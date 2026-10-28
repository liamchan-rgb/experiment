import Foundation
import ClassroomGameCore

public enum PartyAction:String,CaseIterable,Codable {
    case attack,heavyStrike,ambush,breather,simpleGuard,support,rally,smallPotion,largePotion,shieldPotion,revivalStone,endTurn
    public var title:String {
        switch self {
        case .attack:return "普通攻击"
        case .heavyStrike:return "强击"
        case .ambush:return "突袭"
        case .breather:return "喘息"
        case .simpleGuard:return "简易防护"
        case .support:return "援护"
        case .rally:return "振奋"
        case .smallPotion:return "小治疗药水"
        case .largePotion:return "大治疗药水"
        case .shieldPotion:return "护盾药水"
        case .revivalStone:return "复活石"
        case .endTurn:return "结束行动"
        }
    }
    public var visual:String {
        switch self {
        case .ambush:return "ambush"
        case .support:return "support"
        case .rally:return "rally"
        case .breather,.smallPotion,.largePotion:return "heal"
        case .simpleGuard,.shieldPotion:return "guard"
        case .revivalStone:return "revive"
        case .endTurn:return "wait"
        default:return "attack"
        }
    }
    public var impact:Double { if self == .endTurn { return 0 };if self == .ambush { return 0.72 };return visual == "attack" ? 1.048 : visual == "support" ? 0.56 : visual == "revive" ? 0.72 : 0.46 }
    public var duration:Double { if self == .endTurn { return 0.25 };if self == .ambush { return 2.10 };return visual == "attack" ? 1.70 : visual == "revive" ? 2.10 : 1.80 }
    public var isOffensive:Bool { [.attack,.heavyStrike,.ambush].contains(self) }
    public var isItem:Bool { [.smallPotion,.largePotion,.shieldPotion,.revivalStone].contains(self) }
}
public struct PartyIntent {
    public let id:String
    public let action:PartyAction
    public let actor:String
    public let target:String
    public let targets:[String]
    public let command:GameCommand
    public let enemy:Bool
    public let weaponID:String?
    public var magical:Bool { weaponID=="legendaryStaff" && !enemy && action.visual=="attack" }
    public var ranged:Bool { weaponID=="huntingBow" && !enemy && action.isOffensive }
}
/// Uses the original atomic rule engine. Pending visual actions do not mutate it.
public final class PartyEncounter {
    public private(set) var engine:GameEngine
    public private(set) var pending:PartyIntent?
    public private(set) var confirmedReceipt:OperationReceipt?
    private var confirmedEngine:GameEngine?
    public let sessionID:String
    private var serial=0
    public var state:GameState { engine.state }
    public var current:String? { state.battle?.current }
    public var round:Int { state.battle?.round ?? 0 }
    public var terminal:Bool { state.battle == nil || state.pauseReasons.contains(.allPlayersDown) }
    public init(seed:UInt64=UInt64.random(in:1...UInt64.max),sessionID:String=UUID().uuidString,loadouts:[String:GameUnit]?=nil) throws {
        self.sessionID=sessionID
        var catalog=try GameCatalog.initial()
        // A local training creature using the existing deer art. The six formal
        // monster definitions and all19 skills/18 items remain unchanged.
        var warden=try catalog.monster("wolf")
        warden.id="meadowTrainingWarden";warden.name="林地鹿灵"
        warden.attributes=Attributes(maximumHealth:18,baseAP:1,maximumAP:8)
        warden.attack=AttackDefinition(dice:DiceFormula(sides:6),range:0)
        warden.skills=[];warden.drops=[];warden.score=0
        catalog.monsters.append(warden);try catalog.validate()
        var units:[String:GameUnit]=[:]
        units["p1"]=try GameFactory.player(id:"p1",name:"P1 · 冒险者",classID:"adventurer",teamID:"party",nodeID:1,catalog:catalog)
        units["p2"]=try GameFactory.player(id:"p2",name:"P2 · 游侠",classID:"ranger",teamID:"party",nodeID:1,catalog:catalog)
        for id in ["p1","p2"] {
            units[id]?.inventory=["smallPotion":2,"largePotion":1,"shieldPotion":1,"revivalStone":1]
            if let source=loadouts?[id] {
                units[id]?.equipment=source.equipment
                for (item,count) in source.inventory where (try? catalog.item(item).slot) != nil { units[id]?.inventory[item]=count }
            }
        }
        units["p1"]?.health=6;units["p2"]?.health=12
        for (i,id) in ["m1","m2"].enumerated() {
            units[id]=try GameFactory.monster(id:id,templateID:warden.id,nodeID:1,catalog:catalog)
            units[id]?.active=true;units[id]?.name="鹿灵\(i==0 ? "甲":"乙")"
        }
        let map=GameMap(nodes:[MapNode(id:0,name:"营地",kind:.start),MapNode(id:1,name:"林地演练",kind:.combat)],roads:[MapRoad(0,1)],revealed:[0,1])
        var state=GameState(gameID:sessionID,units:units,teams:[GameTeam(id:"party",name:"旅人小队")],map:map,random:RandomState(seed:seed))
        state.pauseReasons=[];state.phase = .pve
        state.battle=BattleState(kind:.pve,queue:["p2","p1","m1","m2"],current:"p2")
        self.engine=try GameEngine(catalog:catalog,state:state)
    }
    public func command(_ action:PartyAction,target:String)->GameCommand? {
        guard let actor=current else { return nil }
        switch action {
        case .attack:return .attack(actor:actor,target:target)
        case .endTurn:return .endTurn(actor:actor,timedOut:false)
        case .revivalStone:return .rescue(actor:actor,target:target)
        case .smallPotion,.largePotion,.shieldPotion:return .useItem(actor:actor,item:action.rawValue,target:target)
        case .rally:return .cast(actor:actor,skill:action.rawValue,target:.node(state.units[target]?.nodeID ?? 1))
        case .breather,.simpleGuard:return .cast(actor:actor,skill:action.rawValue,target:.unit(actor))
        default:return .cast(actor:actor,skill:action.rawValue,target:.unit(target))
        }
    }
    public func preview(_ action:PartyAction,target:String)->ActionPreview {
        guard pending==nil,let command=command(action,target:target),!terminal else { return ActionPreview(allowed:false,message:"等待当前动作完成") }
        return engine.preview(command)
    }
    @discardableResult public func prepare(_ action:PartyAction,target:String)->PartyIntent? {
        guard pending==nil,preview(action,target:target).allowed,let actor=current,let command=command(action,target:target) else { return nil }
        serial += 1
        let targets:[String]
        if action == .rally { targets=state.players.filter { $0.isAlive && $0.nodeID==state.units[target]?.nodeID }.map(\.id) }
        else if action == .breather || action == .simpleGuard { targets=[actor] }
        else { targets=[target] }
        let intent=PartyIntent(id:sessionID+"/"+String(serial),action:action,actor:actor,target:target,targets:targets,command:command,enemy:state.units[actor]?.kind == .monster,weaponID:state.units[actor]?.equipment.weapon)
        // Resolve once in an isolated transaction at confirmation. Live HP/AP,
        // RNG and history remain unchanged until the visible impact commits it.
        guard let staged=try? GameEngine(catalog:engine.catalog,state:state,history:engine.history),
              let receipt=try? staged.apply(command,id:intent.id) else { return nil }
        confirmedEngine=staged;confirmedReceipt=receipt;pending=intent;return intent
    }
    /// Exactly one atomic result at the visible contact; no duplicate effects on replay.
    public func commit(_ id:String) throws -> OperationReceipt? {
        guard let intent=pending,intent.id==id else { return nil }
        guard let staged=confirmedEngine,let receipt=confirmedReceipt else { return nil }
        defer { cancel() }
        guard state==receipt.before else { throw GameError("动作确认后状态已变化，请重新选择。") }
        engine=staged;return receipt
    }
    public func cancel() { pending=nil;confirmedEngine=nil;confirmedReceipt=nil }
    public func playerActions()->[PartyAction] {
        guard let current, state.units[current]?.kind == .player else { return [] }
        return current=="p2" ? [.attack,.ambush,.support,.rally] : [.attack,.heavyStrike,.breather,.simpleGuard]
    }
    public func cost(_ action:PartyAction)->Int {
        if action == .endTurn { return 0 };if action == .revivalStone { return 2 }
        return (try? engine.catalog.skill(action.rawValue).cost) ?? 1
    }
    public func nextEnemyTarget()->String? { state.players.filter(\.isAlive).min { a,b in Double(a.health)/Double(a.baseAttributes.maximumHealth)<Double(b.health)/Double(b.baseAttributes.maximumHealth) }?.id }
}
