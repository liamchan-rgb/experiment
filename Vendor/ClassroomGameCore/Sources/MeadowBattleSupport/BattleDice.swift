import Foundation
import ClassroomGameCore

public struct BattleDie:Codable,Equatable {
    public let color:String
    public let sides:Int
    public let value:Int?
    public let label:String
    public init(_ color:String,sides:Int=0,value:Int?=nil,label:String="定值") { self.color=color;self.sides=sides;self.value=value;self.label=label }
}
public struct BattleDiePose:Codable {
    public let angle:Double,offsetY:Double,scale:Double,resultMix:Double,alpha:Double
    public let face:Int
}
public enum BattleDice {
    /// No RNG is used here: only the engine receipt may supply a rolled result.
    public static func channels(_ action:PartyAction,actor:GameUnit,target:GameUnit,catalog:GameCatalog,receipt:OperationReceipt?=nil)->[BattleDie] {
        if action == .endTurn { return [] }
        var result:[BattleDie]=[]
        if action.visual=="attack" {
            let dice=receipt?.dice.first(where: { $0.source=="damage" })
            result.append(BattleDie("red",sides:dice?.formula.sides ?? 6,value:dice?.values.first,label:action == .heavyStrike ? "D6＋2":"D6"))
            if let buff=actor.damageBuff,buff.amount>0 { result.append(BattleDie("yellow",value:receipt == nil ? nil:buff.amount,label:"增伤")) }
        } else if action == .rally {
            result=[BattleDie("yellow",value:receipt == nil ? nil:2,label:"增伤")]
        } else {
            let skill=try? catalog.skill(action.rawValue)
            let item=try? catalog.item(action.rawValue)
            let effects=skill?.effects ?? []
            for effect in effects {
                if effect.kind == .heal || effect.kind == .shield {
                    let color=effect.kind == .heal ? "green":"blue"
                    result.append(BattleDie(color,value:receipt == nil ? nil:effect.amount,label:effect.kind == .heal ? "恢复":"授盾"))
                }
            }
            if let item {
                if item.heal>0 { result.append(BattleDie("green",value:receipt == nil ? nil:item.heal,label:"恢复")) }
                if item.shield>0 { result.append(BattleDie("blue",value:receipt == nil ? nil:item.shield,label:"授盾")) }
            }
            if action == .revivalStone { result=[BattleDie("green",value:receipt == nil ? nil:(target.baseAttributes.maximumHealth+1)/2,label:"复活")] }
        }
        return result
    }
    public static func pose(time:Double,index:Int,resolvedAge:Double?,visibleAge:Double,exitAge:Double?=nil)->BattleDiePose {
        let settle=resolvedAge.map { PartyVisual.smooth($0/0.36) } ?? 0
        let moving=1-settle,t=time*13+Double(index)*2.1
        let fade=exitAge.map { 1-PartyVisual.smooth($0/0.22) } ?? (resolvedAge.map { 1-PartyVisual.smooth(($0-0.85)/0.3) } ?? 1)
        return BattleDiePose(angle:(sin(t)*0.21+sin(t*0.47)*0.09)*moving,offsetY:(sin(t*0.79)*4)*moving,scale:1+sin(t*0.69)*0.035*moving,resultMix:settle,alpha:PartyVisual.smooth(visibleAge/0.18)*fade,face:Int(floor(max(0,time)*11+Double(index)*1.7)).quotientAndRemainder(dividingBy:6).remainder+1)
    }
    public static func darkness(_ action:PartyAction)->Double {
        switch action { case .heavyStrike:return 0.46;case .attack:return 0.24;case .support:return 0.32;case .rally:return 0.36;case .largePotion,.revivalStone:return 0.34;case .simpleGuard,.shieldPotion:return 0.25;case .endTurn:return 0;default:return 0.22 }
    }
}

public struct PartyMonsterPose:Codable {
    public let progress:Double,scaleY:Double,recoil:Double,flash:Double
}
extension PartyVisual {
    /// Existing attack artwork plus subtle registered idle/preparation/hit/recovery.
    public static func monster(time:Double,attackAge:Double?,hurtAge:Double?=nil,preparing:Bool=false)->PartyMonsterPose {
        let p=attackAge.map { min(1,max(0,$0/0.96)) } ?? 0
        let breathing=sin(time*2.4)*0.007
        let hit=hurtAge.map { pulse($0,0,0.055,0.42) } ?? 0
        let prepare=preparing ? 0.012*(0.5+0.5*sin(time*6)):0
        return PartyMonsterPose(progress:p,scaleY:1+breathing-prepare-hit*0.012,recoil:hit*14,flash:hit*0.65)
    }
}

extension PartyVisual {
    public static func diceAnchor(actor:String,intent:PartyIntent?,age:Double,shielded:Bool=false)->PartyPoint {
        let foot=feet[actor]!,moving=intent?.actor==actor ? travel(intent,age:age,shielded:shielded):PartyPoint(0,0)
        var inset=0.0
        if let intent,!intent.enemy,intent.action.visual=="attack",intent.actor==actor,let to=feet[intent.target] {
            inset=18*min(1,abs(moving.x)/max(1,abs(to.x-140-foot.x)))
        }
        return PartyPoint(foot.x+moving.x-inset,foot.y+moving.y-(actor.hasPrefix("m") ? 337:267))
    }
}
