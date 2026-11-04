import Foundation
import ClassroomGameCore
import MeadowBattleSupport
import MeadowWorldSupport

enum HeroFrames {static let walkFrameCount=24;static let reviewSpeed:CGFloat=25}
@main struct ExportCampaign {
    static func main()throws {
        let root=URL(fileURLWithPath:CommandLine.arguments[1]),out=URL(fileURLWithPath:CommandLine.arguments[2])
        try FileManager.default.createDirectory(at:out,withIntermediateDirectories:true)
        let encoder=JSONEncoder();encoder.outputFormatting=[.sortedKeys]
        func json<T:Encodable>(_ value:T)throws->Any {try JSONSerialization.jsonObject(with:encoder.encode(value))}
        func write(_ value:Any,_ name:String)throws {try JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]).write(to:out.appendingPathComponent(name))}
        let generated=try MeadowMapGenerator.generate(.suggested(total:10,seed:31827))
        let definition=SceneDefinition.generated(generated),network=TrailNetwork(roads:definition.roads,patrolStart:definition.startNodeID)
        try encoder.encode(generated).write(to:out.appendingPathComponent("map-10-31827.json"))
        let roads:[[String:Any]]=network.edges.map{["from":$0.from,"to":$0.to,"points":$0.trail.points.map{[Double($0.x),Double($0.y)]}]}
        let badges:[[String:Any]]=definition.props.filter{$0.nodeID != nil}.map{let p=definition.landmarkBadgePoint(nodeID:$0.nodeID)!;return ["nodeID":$0.nodeID!,"x":Double(p.x),"y":Double(p.y)]}
        try write(["roads":roads,"landmarkBadges":badges],"map-10-31827-geometry.json")
        let session=try MeadowCampaignSession.new(layout:generated),start=session.engine.state.units["p1"]!.nodeID
        try encoder.encode(generated).write(to:out.appendingPathComponent("layout.json"))
        let gait=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("Sources/Resources/hero-gait.json"))) as! [String:Any]
        let plan=try JSONDecoder().decode(AuthoredLocomotion.Plan.self,from:JSONSerialization.data(withJSONObject:gait["modularP1"]!))
        var pose=AuthoredLocomotion(plan:plan),walk=WalkCycle()
        let goal=generated.map.nodes.filter{$0.kind == .combat}.min{generated.map.distance(from:start,to:$0.id)!<generated.map.distance(from:start,to:$1.id)!}!.id
        let preview=try session.beginTravel(to:goal);var rows=[[String:Any]](),settled=0
        for tick in 0..<1200 {
            let before=session.playerIDs.map{session.position(of:$0)}
            let requested=session.isMoving,h=session.heading,scale=WalkCycle.projectedScale(dx:CGFloat(h.x),dy:CGFloat(h.y))
            if pose.allowsTravel(requested:requested) {try session.advanceTravel(distance:0.02*Double(JourneySimulation.speed(for:0)*scale))}
            let positions=session.playerIDs.map{session.position(of:$0)}
            pose.advance(from:CGPoint(x:before[0].x,y:before[0].y),to:CGPoint(x:positions[0].x,y:positions[0].y),seconds:0.02,requested:session.isMoving,headingHint:CGPoint(x:session.heading.x,y:session.heading.y))
            walk.advance(from:CGPoint(x:before[1].x,y:before[1].y),to:CGPoint(x:positions[1].x,y:positions[1].y))
            var heroes=[[String:Any]]()
            for (i,id) in session.playerIDs.enumerated() {
                let unit=session.engine.state.units[id]!,p=positions[i]
                heroes.append(["index":i,"x":p.x+Double(i==0 ? -10:10),"y":p.y,"facing":i==0 ? pose.facing:walk.facing,"frame":i==0 ? pose.frame:walk.frame,"hp":unit.health,"maxHP":try GameRules.attributes(unit,catalog:session.engine.catalog).maximumHealth,"ap":unit.ap])
            }
            rows.append(["time":Double(tick)*0.02,"heroes":heroes,"revealed":session.engine.state.map.revealed.sorted(),"battle":session.engine.state.battle != nil,"coins":session.engine.state.players.map(\.coins).reduce(0,+),"history":session.engine.history.count])
            if tick==80 {
                let bytes=try session.snapshot.encoded();try bytes.write(to:out.appendingPathComponent("mid-road-save.json"))
                let resumed=try MeadowCampaignSession(save:.decoded(bytes));precondition(!resumed.isMoving && resumed.position(of:"p1")==session.position(of:"p1"))
            }
            if !session.isMoving {settled+=1;if settled>=90 {break}}
        }
        try write(rows,"walking.json")
        guard session.engine.state.battle != nil else{throw GameError("Review did not reach an encounter")}
        try session.snapshot.encoded().write(to:out.appendingPathComponent("battle-save.json"))
        let battle=try PartyEncounter(engine:session.engine,sessionID:"campaign-review"),ids=session.playerIDs+battle.monsterIDs
        var frames=[[String:Any]](),time=0.0,hurt=[String:Double](),death=[String:Double](),emissions=[(MeadowBattleLightKind,Double,PartyPoint,Double)](),messages=[[String:Any]]()
        var victory:Double?
        var shownReceipt:OperationReceipt?
        func alias(_ id:String)->String {PartyVisual.slot(id)}
        func frame(_ intent:PartyIntent?,age:Double)throws {
            var units=[[String:Any]]()
            for id in ids {
                let u=session.engine.state.units[id]!,p=PartyVisual.pose(unit:u,intent:intent,age:age,time:time,hurtAge:hurt[id].map{time-$0},blocked:false,downAge:u.isAlive ? nil:2,victoryAge:victory.map{time-$0})
                let motion=PartyVisual.monster(time:time+(alias(id)=="m2" ? 0.7:0),attackAge:intent?.actor==id && intent?.action.isOffensive==true ? age:nil,hurtAge:hurt[id].map{time-$0},preparing:battle.current==id && intent==nil)
                units.append(["id":alias(id),"sourceID":id,"name":u.name,"hp":u.health,"maxHP":try GameRules.attributes(u,catalog:session.engine.catalog).maximumHealth,"ap":u.ap,"shield":u.shield,"buff":u.damageBuff?.amount ?? 0,"clip":p.clip,"progress":p.progress,"deathAge":death[id].map{time-$0} as Any? ?? NSNull(),"monster":try json(motion),"diceAnchor":try json(PartyVisual.diceAnchor(actor:id,intent:intent,age:age))])
            }
            var action=[String:Any]()
            if let i=intent {action=["actor":alias(i.actor),"target":alias(i.target),"targets":i.targets.map(alias),"action":i.action.rawValue,"visual":i.action.visual,"age":age,"enemy":i.enemy,"impact":i.enemy ? 0.46:i.action.impact,"travel":try json(PartyVisual.travel(i,age:age))]}
            if let i=intent,let receipt=shownReceipt,let actor=receipt.before.units[i.actor],let target=receipt.before.units[i.target] {
                let dice=BattleDice.channels(i.action,actor:actor,target:target,catalog:session.engine.catalog,receipt:receipt)
                let anchor=PartyVisual.diceAnchor(actor:i.actor,intent:i,age:age,shielded:target.shield>0,diceCount:dice.count)
                let hit=i.enemy ? 0.46:i.action.impact
                let poly=dice.enumerated().map { index,die in PolyhedralDice.sample(die:die,time:time,index:index,count:dice.count,resolvedAge:age>=hit ? age-hit:nil,visibleAge:age,locked:true,confirmationAge:age) }
                action["dice"]=try json(dice);action["poly"]=try json(poly);action["diceAnchor"]=try json(anchor)
            }
            let particles=emissions.flatMap{kind,at,p,floor in MeadowBattleLightField.sample(kind,age:time-at,originX:p.x,originY:p.y,groundY:floor)}
            let values:[[String:Any]]=particles.map{["id":$0.id,"x":$0.x,"y":$0.y,"angle":$0.angle,"size":$0.size,"alpha":$0.alpha,"cyan":$0.cyan,"groundX":$0.groundX,"groundY":$0.groundY,"groundAge":$0.groundAge as Any? ?? NSNull()]}
            frames.append(["time":time,"frame":frames.count,"units":units,"action":action,"particles":values,"messages":messages.filter{time-($0["at"] as! Double)<1},"current":battle.current.map(alias) as Any? ?? NSNull(),"round":battle.round,"terminal":battle.terminal,"coins":session.engine.state.players.map(\.coins).reduce(0,+)])
        }
        for _ in 0..<60 {try frame(nil,age:0);time+=0.02}
        for _ in 0..<50 {
            if battle.terminal {break}
            let actor=battle.current!,enemy=session.engine.state.units[actor]!.kind == .monster
            let intent:PartyIntent?
            if enemy {intent=battle.prepareMonsterStep()}
            else {let foe=battle.monsterIDs.first{session.engine.state.units[$0]!.isAlive}!;intent=battle.prepare(.attack,target:foe) ?? battle.prepare(.endTurn,target:actor)}
            guard let i=intent else{throw GameError("No review intent")}
            shownReceipt=battle.confirmedReceipt
            let duration=enemy ? 1.10:i.action.duration,hit=enemy ? 0.46:i.action.impact
            var fired=false
            for step in 0...Int(ceil(duration/0.02)) {
                let age=Double(step)*0.02
                if !fired && age>=hit {
                    fired=true
                    let receipt=try battle.commit(i.id)!
                    for id in ids {
                        let before=receipt.before.units[id]!,after=receipt.after.units[id]!
                        if after.health<before.health {
                            hurt[id]=time;let p=PartyVisual.hitPoint(target:id)
                            emissions.append((.strike,time,p,PartyVisual.foot(id)!.y))
                            messages.append(["id":alias(id),"at":time,"text":"−\(before.health-after.health)","x":p.x,"y":p.y])
                        }
                        if before.isAlive && !after.isAlive && after.kind == .monster {
                            death[id]=time;let p=PartyVisual.hitPoint(target:id);emissions.append((.death,time,p,PartyVisual.foot(id)!.y))
                        }
                    }
                    if receipt.after.battle==nil {victory=time}
                }
                try frame(i,age:age);time+=0.02
            }
            for _ in 0..<33 {try frame(nil,age:0);time+=0.02}
        }
        for _ in 0..<115 {try frame(nil,age:0);time+=0.02}
        try write(frames,"battle-frames.json")
        try session.snapshot.encoded().write(to:out.appendingPathComponent("after-battle-save.json"))
        let resumed=try MeadowCampaignSession(save:.decoded(session.snapshot.encoded()));precondition(resumed.engine.archive==session.engine.archive)
        try write(["movementMultiplier":3,"demoSpeeds":[75,114,135],"groupSpeed":75,"previewPath":preview.path,"previewCost":preview.cost,"walkingFrames":rows.count,"battleFrames":frames.count,"outcome":battle.terminal,"battleWon":session.engine.state.battle==nil,"history":session.engine.history.count,"resumeArchiveExact":true,"appOrSimulatorRun":false],"review-trace.json")
        print("Exported actual campaign movement/encounter/receipts/death/particles/resume; frames",rows.count,frames.count)
    }
}
