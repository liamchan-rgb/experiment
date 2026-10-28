import Foundation
import ClassroomGameCore

/// Exploration-only equipment staging for the controlled Meadow encounter.
/// Inventory transfers and legality are always performed by the original engine.
public final class TrainingLoadout {
    public private(set) var engine:GameEngine
    public var units:[String:GameUnit] { engine.state.units }
    public init(seed:UInt64=52) throws {
        let catalog=try GameCatalog.initial()
        var p1=try GameFactory.player(id:"p1",name:"P1",classID:"adventurer",teamID:"party",nodeID:0,catalog:catalog)
        let p2=try GameFactory.player(id:"p2",name:"P2",classID:"ranger",teamID:"party",nodeID:0,catalog:catalog)
        let map=GameMap(nodes:[MapNode(id:0,name:"营地",kind:.start)],roads:[],revealed:[0])
        // Demo loan weapons in the camp inventory; catalog and prices stay original.
        p1.inventory["huntingBow"]=1
        p1.inventory["greatSword"]=1
        p1.inventory["legendaryStaff"]=1
        p1.inventory["leatherArmor"]=1
        p1.inventory["runeArmor"]=1
        var state=GameState(units:["p1":p1,"p2":p2],teams:[GameTeam(id:"party",name:"旅人小队")],map:map,random:RandomState(seed:seed))
        state.pauseReasons=[]
        engine=try GameEngine(catalog:catalog,state:state)
    }
    @discardableResult public func equipArmor(_ item:String?,actor:String="p1") throws -> OperationReceipt {
        try engine.apply(.equip(unit:actor,slot:.armor,item:item))
    }
    @discardableResult public func equip(_ item:String?,actor:String="p1") throws -> OperationReceipt {
        try engine.apply(.equip(unit:actor,slot:.weapon,item:item))
    }
}

/// A data binding, not a weapon-specific branch in the renderer or body rig.
public struct EquipmentVisualBinding:Codable {
    public let itemID:String,walkingAsset:String,battleAsset:String,iconAsset:String
}
