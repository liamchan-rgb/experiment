import Foundation
import ClassroomGameCore

public struct MeadowCampaignTravel: Codable, Equatable {
    public let id:String
    public let actors:[String]
    public let path:[Int]
    public var leg:Int=0
    public var distance:Double=0
    public var paused=false
}
public struct MeadowCampaignCamera:Codable,Equatable {
    public var x:Double,y:Double,zoom:Double
    public init(x:Double,y:Double,zoom:Double=1){self.x=x;self.y=y;self.zoom=zoom}
}
public struct MeadowCampaignSave:Codable,Equatable {
    public var formatVersion=1
    public let layout:GeneratedMeadowMap
    public var archive:GameArchive
    public var travel:MeadowCampaignTravel?
    public var camera:MeadowCampaignCamera?
    public let appearanceID:String
    public func validate() throws {
        try archive.validate();try layout.configuration.validate();try layout.map.validate()
        guard formatVersion==1,layout.generatorVersion==3,["forester","wayfarer"].contains(appearanceID),
              layout.coordinateHeight.isFinite,layout.coordinateHeight>0,
              [.exploration,.pve].contains(archive.state.phase),archive.state.battle == nil || archive.state.battle?.kind == .pve,
              Set(archive.state.players.map(\.id))==Set(["p1","p2"]),archive.catalog == (try MeadowCampaignSession.catalog()),
              archive.state.map.nodes.map(\.id)==layout.map.nodes.map(\.id),archive.state.map.roads==layout.map.roads else {throw GameError("探索存档与当前地图或规则不匹配。")}
        let ids=Set(layout.map.nodes.map(\.id))
        let assets=Set(["CampTent","NodeCombatOutpost","NodeBossSanctum","NodeRewardCache","NodeWaystone","OakA","OakB","Pines","RockLow","RockHigh","RockSmall","Shrub","Flowers"])
        guard layout.props.allSatisfy({assets.contains($0.asset)}),archive.state.units.values.filter({$0.kind == .monster}).allSatisfy({u in
            ["meadowStag","meadowElderStag"].contains(u.templateID) && (u.id=="m-\(u.nodeID)-1" || u.id=="m-\(u.nodeID)-2")
        }) else {throw GameError("探索资源或怪物数据不受支持。")}
        guard Set(layout.props.compactMap(\.nodeID))==ids,layout.props.allSatisfy({$0.x.isFinite && $0.y.isFinite && $0.width.isFinite && $0.width>0}),
              layout.roads.count==layout.map.roads.count,layout.roads.allSatisfy({$0.points.count>=2 && $0.points.allSatisfy{$0.x.isFinite && $0.y.isFinite}}) else {throw GameError("探索布局数据无效。")}
        for node in archive.state.map.nodes {
            guard let original=layout.map.nodes.first(where:{$0.id==node.id}),node.x==original.x,node.y==original.y,node.kind==original.kind,
                  layout.props.filter({$0.nodeID==node.id}).count==1 else {throw GameError("探索节点不匹配。")}
        }
        if let camera {guard camera.x.isFinite,camera.y.isFinite,camera.zoom.isFinite,(1...3).contains(camera.zoom) else {throw GameError("镜头数据无效。")}}
        if let t=travel {
            guard archive.state.battle==nil,!t.id.isEmpty,!t.actors.isEmpty,Set(t.actors).count==t.actors.count,
                  t.path.count>=2,t.leg>=0,t.leg<t.path.count-1,t.distance.isFinite,t.distance>=0,
                  t.actors.allSatisfy({archive.state.units[$0]?.isAlive==true && archive.state.units[$0]?.kind == .player && archive.state.units[$0]?.nodeID==t.path[t.leg]}),
                  (1..<t.path.count).allSatisfy({archive.state.map.neighbors(t.path[$0-1]).contains(t.path[$0])}),
                  let points=Self.road(layout,from:t.path[t.leg],to:t.path[t.leg+1]),t.distance<Self.length(points)+0.000001 else {throw GameError("存档中的移动游标无效。")}
        }
    }
    public func encoded()throws->Data {try validate();let e=JSONEncoder();e.outputFormatting=[.sortedKeys];return try e.encode(self)}
    public static func decoded(_ bytes:Data)throws->Self {let s=try JSONDecoder().decode(Self.self,from:bytes);try s.validate();return s}
    static func road(_ layout:GeneratedMeadowMap,from:Int,to:Int)->[MeadowWorldPoint]? {
        guard let r=layout.roads.first(where:{($0.from==from && $0.to==to)||($0.to==from && $0.from==to)}) else{return nil}
        return r.from==from ? r.points:Array(r.points.reversed())
    }
    static func length(_ p:[MeadowWorldPoint])->Double {zip(p,p.dropFirst()).map{hypot($0.1.x-$0.0.x,$0.1.y-$0.0.y)}.reduce(0,+)}
}
public final class MeadowCampaignStore {
    public let url:URL
    public init(url:URL){self.url=url}
    public func read()throws->MeadowCampaignSave? {FileManager.default.fileExists(atPath:url.path) ? try .decoded(Data(contentsOf:url)):nil}
    public func write(_ data:Data)throws {try FileManager.default.createDirectory(at:url.deletingLastPathComponent(),withIntermediateDirectories:true);try data.write(to:url,options:.atomic)}
}
private final class CampaignWriter {
    var snapshot:MeadowCampaignSave
    let persist:((Data)throws->Void)?
    init(_ snapshot:MeadowCampaignSave,persist:((Data)throws->Void)?){self.snapshot=snapshot;self.persist=persist}
    func write(_ next:MeadowCampaignSave)throws {if let persist {try persist(next.encoded())};snapshot=next}
}
/// Owns one persistent tabletop engine. Rendering advances a saved road cursor;
/// rules, AP, reveal, loot and encounters commit only at actual node arrival.
public final class MeadowCampaignSession {
    public let engine:GameEngine
    private let writer:CampaignWriter
    public var snapshot:MeadowCampaignSave {var s=writer.snapshot;s.archive=engine.archive;return s}
    public var travel:MeadowCampaignTravel? {writer.snapshot.travel}
    public var isMoving:Bool {travel.map{!$0.paused} ?? false}
    public var playerIDs:[String] {engine.state.players.map(\.id)}
    public var cleared:Bool {!engine.state.units.values.contains{$0.kind == .monster && $0.isAlive}}
    public static func catalog()throws->GameCatalog {
        var c=try GameCatalog.initial()
        // Explicit local skins. All source monster stats/AI/drops and original
        // six definitions remain unchanged; only ID/name match the existing art.
        var stag=try c.monster("wolf");stag.id="meadowStag";stag.name="林地鹿灵"
        var elder=try c.monster("caveTroll");elder.id="meadowElderStag";elder.name="古树鹿王"
        c.monsters += [stag,elder];try c.validate();return c
    }
    public static func new(layout:GeneratedMeadowMap,appearanceID:String="forester",loadouts:[String:GameUnit]?=nil,persist:((Data)throws->Void)?=nil)throws->MeadowCampaignSession {
        let catalog=try self.catalog(),start=layout.map.nodes.first{$0.kind == .start}!.id
        var units=[String:GameUnit]()
        for (id,classID) in [("p1","spellblade"),("p2","ranger")] {
            var u=try GameFactory.player(id:id,name:id.uppercased()+" · "+catalog.playerClass(classID).name,classID:classID,teamID:"party",nodeID:start,catalog:catalog)
            u.inventory=["smallPotion":2,"largePotion":1,"shieldPotion":1,"revivalStone":1]
            if let source=loadouts?[id] {u.equipment=source.equipment;for item in source.equipment.itemIDs {u.inventory[item]=max(1,source.inventory[item] ?? 1)}}
            u.health=try GameRules.attributes(u,catalog:catalog).maximumHealth;try GameRules.refill(&u,catalog:catalog);units[id]=u
        }
        for node in layout.map.nodes where node.kind == .combat || node.kind == .boss {
            let count=node.kind == .boss ? 1:(node.id%3==0 ? 2:1)
            for index in 1...count {
                let id="m-\(node.id)-\(index)"
                units[id]=try GameFactory.monster(id:id,templateID:node.kind == .boss ? "meadowElderStag":"meadowStag",nodeID:node.id,catalog:catalog)
            }
        }
        var state=GameState(units:units,teams:[GameTeam(id:"party",name:"林间小队")],map:layout.map,random:RandomState(seed:layout.configuration.seed ^ 0x43414d504149474e))
        state.pauseReasons=[]
        let save=MeadowCampaignSave(layout:layout,archive:GameArchive(catalog:catalog,state:state,history:[]),appearanceID:appearanceID)
        let session=try MeadowCampaignSession(save:save,persist:persist);try session.checkpoint();return session
    }
    public init(save:MeadowCampaignSave,persist:((Data)throws->Void)?=nil)throws {
        try save.validate()
        var restored=save;restored.travel?.paused=true
        restored.archive.state.pauseReasons.remove(.background)
        let writer=CampaignWriter(restored,persist:persist);self.writer=writer
        engine=try GameEngine(catalog:restored.archive.catalog,state:restored.archive.state,history:restored.archive.history,persist:{archive in
            var next=writer.snapshot;next.archive=archive;try writer.write(next)
        })
    }
    public func point(at nodeID:Int)->MeadowWorldPoint {let n=writer.snapshot.layout.map.nodes.first{$0.id==nodeID}!;return .init(n.x*1280,n.y*writer.snapshot.layout.coordinateHeight)}
    public func position(of id:String)->MeadowWorldPoint {
        guard let u=engine.state.units[id] else{return writer.snapshot.layout.spawn}
        guard let t=travel,t.actors.contains(id),let p=MeadowCampaignSave.road(writer.snapshot.layout,from:t.path[t.leg],to:t.path[t.leg+1]) else{return point(at:u.nodeID)}
        var d=t.distance
        for (a,b) in zip(p,p.dropFirst()) {let l=hypot(b.x-a.x,b.y-a.y);if d<=l,l>0{return .init(a.x+(b.x-a.x)*d/l,a.y+(b.y-a.y)*d/l)};d-=l}
        return p.last!
    }
    public var heading:MeadowWorldPoint {
        guard let t=travel,let p=MeadowCampaignSave.road(writer.snapshot.layout,from:t.path[t.leg],to:t.path[t.leg+1]) else{return .init(0,0)}
        var d=t.distance
        for (a,b) in zip(p,p.dropFirst()) {let l=hypot(b.x-a.x,b.y-a.y);if d<=l{return .init(b.x-a.x,b.y-a.y)};d-=l}
        return .init(0,0)
    }
    public func preview(to node:Int,actor:String="p1")->ActionPreview {
        guard travel==nil,engine.state.battle==nil,let unit=engine.state.units[actor],unit.isAlive,
              let path=engine.state.map.shortestPath(from:unit.nodeID,to:node) else{return .init(allowed:false,message:"请先完成当前移动或战斗。")}
        let actors=engine.state.players.filter{$0.isAlive && $0.nodeID==unit.nodeID}.map(\.id)
        return engine.preview(.move(actors:actors,path:path))
    }
    @discardableResult public func beginTravel(to node:Int,actor:String="p1")throws->ActionPreview {
        let result=preview(to:node,actor:actor);guard result.allowed else{throw GameError(result.message)}
        let origin=result.path[0],actors=engine.state.players.filter{$0.isAlive && $0.nodeID==origin}.map(\.id)
        var next=snapshot;next.travel=MeadowCampaignTravel(id:UUID().uuidString,actors:actors,path:result.path)
        try writer.write(next);return result
    }
    /// distance is actual screen-plane road distance, supplied by the unchanged
    /// projection metric and the app's single movement-speed multiplier.
    @discardableResult public func advanceTravel(distance:Double)throws->[OperationReceipt] {
        guard distance.isFinite,distance>=0 else{throw GameError("移动距离无效。")}
        var remainder=distance,receipts=[OperationReceipt]()
        while remainder>0,let t=travel,!t.paused {
            guard let p=MeadowCampaignSave.road(writer.snapshot.layout,from:t.path[t.leg],to:t.path[t.leg+1]) else{throw GameError("道路不存在。")}
            let needed=max(0,MeadowCampaignSave.length(p)-t.distance)
            if remainder+0.00000001<needed {writer.snapshot.travel?.distance+=remainder;break}
            let before=writer.snapshot,nextLeg=t.leg+1
            if nextLeg==t.path.count-1 {writer.snapshot.travel=nil}
            else {writer.snapshot.travel?.leg=nextLeg;writer.snapshot.travel?.distance=0}
            do {
                let receipt=try engine.apply(.move(actors:t.actors,path:[t.path[t.leg],t.path[nextLeg]]),id:t.id+"/"+String(nextLeg))
                receipts.append(receipt);remainder=max(0,remainder-needed)
            } catch {writer.snapshot=before;writer.snapshot.travel?.paused=true;throw error}
        }
        return receipts
    }
    public func setPaused(_ paused:Bool)throws {var next=snapshot;next.travel?.paused=paused;try writer.write(next)}
    public func pauseAfterFailure(){writer.snapshot.travel?.paused=true}
    public func checkpoint(camera:MeadowCampaignCamera?=nil)throws {var next=snapshot;if let camera{next.camera=camera};try writer.write(next)}
    @discardableResult public func refillExploration()throws->OperationReceipt {
        guard travel==nil else{throw GameError("移动中不能补足行动点。")};return try engine.apply(.refillExploration)
    }
}
