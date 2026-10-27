import Foundation
import MeadowBattleSupport
import ClassroomGameCore

@main struct Export {
    static func main() throws {
        let out=URL(fileURLWithPath:CommandLine.arguments[1]);try FileManager.default.createDirectory(at:out,withIntermediateDirectories:true)
        if CommandLine.arguments.contains("--bow-only") { try exportBow(out:out);return }
        var rows:[[String:Any]]=[],requests:[[String:Any]]=[]
        for scenario in ["support","rally","items","revive","combat"] {
            let model=try PartyEncounter(seed:17,sessionID:"review-"+scenario)
            if scenario=="rally" { let i=model.prepare(.support,target:"p1")!;_ = try model.commit(i.id) }
            if scenario=="revive" { try model.engine.apply(.editResources(unit:"p1",value:ResourcePatch(health:0))) }
            if scenario=="combat" {
                let i=model.prepare(.rally,target:"p1")!;_ = try model.commit(i.id)
                try model.engine.apply(.endTurn(actor:"p2",timedOut:false))
                let guardIntent=model.prepare(.simpleGuard,target:"p1")!;_ = try model.commit(guardIntent.id)
                try model.engine.apply(.editResources(unit:"m1",value:ResourcePatch(health:3)))
            }
            let count=scenario=="combat" ? 320:scenario=="items" ? 370:scenario=="revive" ? 180:160
            var current:PartyIntent?,start=0.0,fired=false
            var births:[String:Double]=[:],heals:[String:Double]=[:],forms:[String:Double]=[:]
            var messages:[[String:Any]]=[]
            var death:[String:Double]=[:],hurt:[String:Double]=[:]
            var emitters:[[String:Any]]=[];var shielded=false
            for frame in 0..<count {
                let time=Double(frame)*0.02
                if frame==20 || (scenario=="items" && (frame==140 || frame==260)) || (scenario=="combat" && frame==140) {
                    let action:PartyAction=scenario=="combat" ? .attack:["support","unarmed"].contains(scenario) ? .support:scenario=="rally" ? .rally:scenario=="revive" ? .revivalStone:frame==20 ? .smallPotion:frame==140 ? .largePotion:.shieldPotion
                    if scenario=="combat" && frame==140 { try model.engine.apply(.endTurn(actor:"p1",timedOut:false)) }
                    let target=scenario=="combat" && frame==20 ? "m1":scenario=="items" && frame==140 ? "p2":"p1"
                    shielded=(model.state.units[target]?.shield ?? 0)>0
                    current=model.prepare(action,target:target)!;start=time;fired=false
                    let offset=max(0,action.impact-0.46)
                    for id in current!.targets {
                        if ["support","heal","revive"].contains(action.visual) { heals[id]=time+offset }
                        if ["support","guard"].contains(action.visual) { forms[id]=time+offset }
                    }
                }
                var receipt:OperationReceipt?
                let age=time-start
                if let intent=current,!fired,age+1e-9>=(intent.enemy ? 0.46:intent.action.impact) {
                    fired=true;receipt=try model.commit(intent.id)
                    if let receipt {
                        for id in ["p1","p2","m1","m2"] {
                            let before=receipt.before.units[id]!,after=receipt.after.units[id]!
                            let foot=PartyVisual.feet[id]!
                            let damage=max(0,before.health-after.health),absorbed=max(0,before.shield-after.shield)
                            if damage>0 || absorbed>0 {
                                hurt[id]=time
                                let x=foot.x+(absorbed>0 ? (5+240*0.41)*PartyVisual.heroScale:(id.hasPrefix("m") ? -80:0))
                                let y=foot.y-(id.hasPrefix("p") ? 65:72)
                                emitters.append(["kind":absorbed>0 ? "shieldContact":"strike","at":time,"x":x,"y":y,"floor":foot.y])
                                if absorbed>0 && after.shield==0 { emitters.append(["kind":"shieldBreak","at":time,"x":foot.x,"y":foot.y-60,"floor":foot.y]) }
                                messages.append(["id":id,"text":damage>0 ? "−\(damage)":"格挡","at":time,"kind":"damage"])
                            }
                            if before.isAlive && !after.isAlive && after.kind == .monster {
                                death[id]=time;emitters.append(["kind":"death","at":time,"x":foot.x-80,"y":foot.y-72,"floor":foot.y])
                            }
                            if after.shield>before.shield { births[id]=time }
                            if after.health>before.health { messages.append(["id":id,"text":"＋\(after.health-before.health)","at":time,"kind":"heal"]) }
                            if after.shield>before.shield { messages.append(["id":id,"text":"盾 ＋\(after.shield-before.shield)","at":time,"kind":"shield"]) }
                            if after.damageBuff != before.damageBuff { messages.append(["id":id,"text":"伤害 ＋2","at":time,"kind":"buff"]) }
                        }
                    }
                }
                if let intent=current,age>=(intent.enemy ? 1.10:intent.action.duration) { current=nil }
                var units:[[String:Any]]=[]
                for id in ["p1","p2","m1","m2"] {
                    let u=model.state.units[id]!,pose=PartyVisual.pose(unit:u,intent:current,age:age,time:time,hurtAge:hurt[id].map { time-$0 },blocked:id=="p1" && shielded && hurt[id] != nil)
                    units.append(["id":id,"name":u.name,"weaponID":u.equipment.weapon as Any? ?? NSNull(),"vitalsVisible":u.kind != .monster || u.isAlive,"hp":u.health,"maxHP":u.baseAttributes.maximumHealth,"shield":u.shield,"ap":u.ap,"buff":u.damageBuff?.amount ?? 0,"buffRounds":u.damageBuff?.roundsLeft ?? 0,"clip":pose.clip,"progress":pose.progress,"deathAge":death[id].map { time-$0 } as Any? ?? NSNull()])
                    if id.hasPrefix("p") {
                        var r:[String:Any]=["kind":scenario+"-"+id,"frame":frame,"time":time,"shield":u.shield,"emitters":[]]
                        if let at=heals[id],u.isAlive { r["recoveryAge"]=time-at }
                        if let at=forms[id],u.shield==0,time-at<1 { r["formation"]=time-at }
                        if let at=births[id] { r["birth"]=time-at }
                        requests.append(r)
                    }
                }
                let activeEmitters=emitters.compactMap { e -> [String:Any]? in
                    let age=time-(e["at"] as! Double);guard age<3 else { return nil }
                    return ["kind":e["kind"]!,"age":age,"x":e["x"]!,"y":e["y"]!,"floor":e["floor"]!]
                }
                requests.append(["kind":scenario+"-fx","frame":frame,"time":time,"emitters":activeEmitters,"shield":0])
                var action:[String:Any]=[:]
                if let i=current { action=["actor":i.actor,"target":i.target,"targets":i.targets,"action":i.action.rawValue,"visual":i.action.visual,"age":age,"enemy":i.enemy,"shielded":shielded,"travel":try JSONSerialization.jsonObject(with:JSONEncoder().encode(PartyVisual.travel(i,age:age,shielded:shielded)))] }
                let from=current.map { PartyVisual.chest($0.actor) } ?? PartyPoint(0,0),to=current.map { PartyVisual.chest($0.target) } ?? PartyPoint(0,0)
                let trail=PartyVisual.trail(age:age,from:from,to:to)
                let rally=["p1","p2"].map { id -> [String:Any] in
                    let data=try! JSONEncoder().encode(PartyVisual.rally(age:age,at:PartyVisual.chest(id)))
                    return ["id":id,"particles":try! JSONSerialization.jsonObject(with:data)]
                }
                rows.append(["scenario":scenario,"frame":frame,"time":time,"current":model.current as Any? ?? NSNull(),"units":units,"action":action,"trail":try JSONSerialization.jsonObject(with:JSONEncoder().encode(trail)),"rally":rally,"messages":messages.filter { time-($0["at"] as! Double)<1 },"committed":receipt != nil])
            }
        }
        try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]).write(to:out.appendingPathComponent("party-frames.json"))
        try JSONSerialization.data(withJSONObject:requests,options:[.sortedKeys]).write(to:out.appendingPathComponent("legacy-light-requests.json"))
        try exportDice(out:out)
        try exportPoly(out:out)
        try exportBow(out:out)
        print("Exported \(rows.count) actual GameCore support/item frames and \(requests.count) attachment samples")
    }
}

extension Export {
    static func exportDice(out:URL) throws {
        var rows:[[String:Any]]=[]
        for scenario in ["attack-buff","support","shield","heal","lethal","ambush","ambush-last","unarmed","bow","bow-heavy","bow-lethal"] {
            let gear=try TrainingLoadout()
            if scenario=="unarmed" { try gear.equip(nil) };if scenario.hasPrefix("bow") { try gear.equip("huntingBow") }
            let p=try PartyEncounter(seed:47,sessionID:"dice-review-"+scenario,loadouts:scenario=="unarmed" || scenario.hasPrefix("bow") ? gear.units:nil)
            let action:PartyAction=scenario=="bow-heavy" ? .heavyStrike:scenario.hasPrefix("ambush") ? .ambush:["support","unarmed"].contains(scenario) ? .support:scenario=="shield" ? .simpleGuard:scenario=="heal" ? .largePotion:.attack
            if scenario=="attack-buff" || scenario=="lethal" || scenario=="ambush-last" {
                let rally=p.prepare(.rally,target:"p1")!;_ = try p.commit(rally.id)
            }
            if scenario != "support" && scenario != "unarmed" && scenario != "heal" && !scenario.hasPrefix("ambush") { try p.engine.apply(.endTurn(actor:"p2",timedOut:false)) }
            if scenario=="lethal" || scenario=="bow-lethal" { try p.engine.apply(.editResources(unit:"m1",value:ResourcePatch(health:3))) }
            if scenario=="ambush-last" {
                try p.engine.apply(.editResources(unit:"m2",value:ResourcePatch(health:0)))
                try p.engine.apply(.editResources(unit:"m1",value:ResourcePatch(health:3)))
            }
            let target=action.isOffensive ? "m1":"p1"
            var intent:PartyIntent?,receipt:OperationReceipt?,activeAction=action,start=1.0,hitAt:Double?,fired=false
            var dieActor=p.current!,dieTarget=target,dieActorUnit=p.state.units[p.current!]!,dieTargetUnit=p.state.units[target]!
            var hurt:[String:Double]=[:],death:[String:Double]=scenario=="ambush-last" ? ["m2":-3.0]:[:]
            var damageLabels:[[String:Any]]=[]
            var dice=BattleDice.channels(action,actor:dieActorUnit,target:dieTargetUnit,catalog:p.engine.catalog)
            let count=scenario=="attack-buff" ? 300:scenario.hasPrefix("ambush") ? 220:190
            for frame in 0..<count {
                let time=Double(frame)*0.02
                if frame==50 || scenario=="attack-buff" && frame==190 {
                    if frame==190 {
                        try p.engine.apply(.endTurn(actor:"p1",timedOut:false));activeAction = .attack
                        dieActor=p.current!;dieTarget="p1";dieActorUnit=p.state.units[dieActor]!;dieTargetUnit=p.state.units[dieTarget]!
                        dice=BattleDice.channels(activeAction,actor:dieActorUnit,target:dieTargetUnit,catalog:p.engine.catalog)
                    }
                    intent=p.prepare(activeAction,target:dieTarget)!;start=time;fired=false;hitAt=nil;receipt=nil
                    dice=BattleDice.channels(activeAction,actor:dieActorUnit,target:dieTargetUnit,catalog:p.engine.catalog,receipt:p.confirmedReceipt)
                }
                let age=time-start
                if let i=intent,!fired,age+1e-8 >= (i.enemy ? 0.46:i.action.impact) {
                    receipt=try p.commit(i.id);fired=true;hitAt=time
                    if let r=receipt {
                        dice=BattleDice.channels(activeAction,actor:dieActorUnit,target:dieTargetUnit,catalog:p.engine.catalog,receipt:r)
                        for id in ["p1","p2","m1","m2"] {
                            let damage=max(0,r.before.units[id]!.health-r.after.units[id]!.health),absorbed=max(0,r.before.units[id]!.shield-r.after.units[id]!.shield)
                            if damage>0 || absorbed>0 {
                                hurt[id]=time;let point=PartyVisual.hitPoint(target:id,shielded:absorbed>0)
                                damageLabels.append(["text":damage>0 ? "−\(damage)":"格挡","x":point.x,"y":point.y,"at":time])
                            }
                            if r.before.units[id]!.isAlive && !r.after.units[id]!.isAlive { death[id]=time }
                        }
                    }
                }
                let showing=intent.flatMap { age<($0.enemy ? 1.10:$0.action.duration) ? $0:nil }
                let travel=PartyVisual.travel(showing,age:age,shielded:dieTargetUnit.shield>0)
                var units:[[String:Any]]=[]
                for id in ["p1","p2","m1","m2"] {
                    let u=p.state.units[id]!,pose=PartyVisual.pose(unit:u,intent:showing,age:age,time:time,hurtAge:hurt[id].map { time-$0 },blocked:u.shield>0)
                    let monster=PartyVisual.monster(time:time+(id=="m2" ? 0.7:0),attackAge:showing?.actor==id ? age:nil,hurtAge:hurt[id].map { time-$0 },preparing:p.current==id && showing==nil)
                    units.append(["id":id,"weaponID":u.equipment.weapon as Any? ?? NSNull(),"vitalsVisible":u.kind != .monster || u.isAlive,"hp":u.health,"maxHP":u.baseAttributes.maximumHealth,"shield":u.shield,"ap":u.ap,"buff":u.damageBuff?.amount ?? 0,"clip":pose.clip,"progress":pose.progress,"monster":try JSONSerialization.jsonObject(with:JSONEncoder().encode(monster)),"deathAge":death[id].map { time-$0 } as Any? ?? NSNull()])
                }
                let bowProjectile=showing.flatMap { i -> BowProjectile? in
                    guard i.ranged,let f=PartyVisual.feet[i.actor] else { return nil }
                    let tip=BowRig.releaseArrowTip
                    return BowRig.projectile(age:age,from:PartyPoint(f.x+(tip.x-123)*PartyVisual.heroScale,f.y+(tip.y-214)*PartyVisual.heroScale),to:PartyVisual.hitPoint(target:i.target,shielded:dieTargetUnit.shield>0),impact:i.action.impact)
                }
                let diePose=dice.indices.map { index in BattleDice.pose(time:time,index:index,resolvedAge:hitAt.map { time-$0 },visibleAge:frame>=190 && scenario=="attack-buff" ? time-3.8:time) }
                let hover=time<1
                let initial=BattleDice.darkness(action)
                let dim=hover ? initial*PartyVisual.smooth(time/0.28):showing != nil ? (initial+(max(initial,activeAction.isOffensive ? 0.58:0.32)-initial)*PartyVisual.smooth(age/0.4))*(1-PartyVisual.smooth((age-1.2)/0.6)):0
                rows.append(["scenario":scenario,"frame":frame,"time":time,"damageLabels":damageLabels.filter { time-($0["at"] as! Double)<1 },"ranged":showing?.ranged ?? false,"projectile":bowProjectile.map { try! JSONSerialization.jsonObject(with:JSONEncoder().encode($0)) } as Any? ?? NSNull(),"locked":!hover,"confirmationAge":hover ? NSNull():age,"hover":hover,"darkness":dim,"actor":dieActor,"target":dieTarget,"action":activeAction.rawValue,"age":age,"playing":showing != nil,"enemy":showing?.enemy ?? false,"impact":hitAt as Any? ?? NSNull(),"afterimages":try JSONSerialization.jsonObject(with:JSONEncoder().encode(PartyVisual.afterimages(showing,age:age))),"ambushSlashes":try JSONSerialization.jsonObject(with:JSONEncoder().encode(activeAction == .ambush ? PartyVisual.ambushSlashes(age:age,at:PartyPoint(PartyVisual.feet[dieTarget]!.x-80,PartyVisual.feet[dieTarget]!.y-72)):[])),"receiptDice":try JSONSerialization.jsonObject(with:JSONEncoder().encode(receipt?.dice ?? [])),"dice":try JSONSerialization.jsonObject(with:JSONEncoder().encode(dice)),"diceAnchor":try JSONSerialization.jsonObject(with:JSONEncoder().encode(PartyVisual.diceAnchor(actor:dieActor,intent:showing,age:age,shielded:dieTargetUnit.shield>0,diceCount:dice.count))),"poly":try JSONSerialization.jsonObject(with:JSONEncoder().encode(dice.enumerated().map { index,die in PolyhedralDice.sample(die:die,time:time,index:index,count:dice.count,resolvedAge:hitAt.map { time-$0 },visibleAge:frame>=190 && scenario=="attack-buff" ? time-3.8:time,locked:!hover,confirmationAge:hover ? nil:age) })),"dicePose":try JSONSerialization.jsonObject(with:JSONEncoder().encode(diePose)),"travel":try JSONSerialization.jsonObject(with:JSONEncoder().encode(travel)),"current":(showing?.actor ?? p.current) as Any? ?? NSNull(),"acted":Array(p.state.battle?.acted ?? []),"units":units])
            }
        }
        try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]).write(to:out.appendingPathComponent("dice-frames.json"))
        print("Exported \(rows.count) receipt-bound dice / monster / queue frames")
    }
}

extension Export {
    static func exportPoly(out:URL) throws {
        var rows:[[String:Any]]=[]
        for group in ["types","bonus"] {
            let p=try PartyEncounter(seed:48,sessionID:"poly-review-"+group)
            var sources:[(GameEngine,GameCommand,String)]=[]
            if group=="types" {
                for sides in [4,6,8,12,20,10] {
                    var catalog=p.engine.catalog,state=p.state
                    var weapon=try catalog.item("trainingSword")
                    let id=[6:"trainingSword",8:"huntingBow",12:"greatSword",20:"legendaryStaff"][sides]
                    if let id { weapon=try catalog.item(id) }
                    else { weapon.id="offlineReviewD\(sides)";weapon.name="离线骰型D\(sides)";weapon.attack?.dice=DiceFormula(sides:sides);catalog.items.append(weapon) }
                    state.units["p1"]?.equipment.weapon=weapon.id;state.battle?.queue=["p1","p2","m1","m2"];state.battle?.current="p1"
                    sources.append((try GameEngine(catalog:catalog,state:state),.attack(actor:"p1",target:"m1"),"D\(sides)"))
                }
            } else {
                let rally=p.prepare(.rally,target:"p1")!;_ = try p.commit(rally.id)
                sources.append((p.engine,.cast(actor:"p2",skill:"ambush",target:.unit("m1")),"突袭 · 2D8＋2 / 增伤＋2"))
                var state=p.state;var actor=try GameFactory.player(id:"p1",name:"符文公式审核",classID:"spellblade",teamID:"party",nodeID:1,catalog:p.engine.catalog)
                actor.health=6;actor.damageBuff=state.units["p1"]?.damageBuff;state.units["p1"]=actor;state.battle?.queue=["p1","p2","m1","m2"];state.battle?.current="p1"
                sources.append((try GameEngine(catalog:p.engine.catalog,state:state),.cast(actor:"p1",skill:"runeSlash",target:.unit("m1")),"符文斩 · 2D12＋2 / 增伤＋2"))
            }
            var receipts:[OperationReceipt]=[]
            for (engine,command,_) in sources { receipts.append(try engine.apply(command)) }
            for frame in 0..<180 {
                let time=Double(frame)*0.02,at=1.2,resolved=time>=at
                var entries:[[String:Any]]=[]
                for (i,source) in sources.enumerated() {
                    let receipt=receipts[i],actorID=group=="bonus" && i==0 ? "p2":"p1",actor=receipt.before.units[actorID]!,target=receipt.before.units["m1"]!
                    let dice=group=="types" ? BattleDice.channels(.attack,actor:actor,target:target,catalog:source.0.catalog,receipt:resolved ? receipt:nil):BattleDice.skillChannels(i==0 ? "ambush":"runeSlash",actor:actor,catalog:source.0.catalog,receipt:resolved ? receipt:nil)
                    let samples=dice.enumerated().map { index,die in PolyhedralDice.sample(die:die,time:time,index:index+i*3,count:dice.count,resolvedAge:resolved ? time-at:nil,visibleAge:time) }
                    entries.append(["title":source.2,"dice":try JSONSerialization.jsonObject(with:JSONEncoder().encode(dice)),"samples":try JSONSerialization.jsonObject(with:JSONEncoder().encode(samples)),"receiptDice":try JSONSerialization.jsonObject(with:JSONEncoder().encode(resolved ? receipt.dice:[]))])
                }
                rows.append(["group":group,"frame":frame,"time":time,"entries":entries])
            }
        }
        try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]).write(to:out.appendingPathComponent("poly-frames.json"))
        print("Exported \(rows.count) polyhedron gallery and source-formula bonus frames")
    }
}

extension Export {
    static func exportBow(out:URL) throws {
        let root=URL(fileURLWithPath:#filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        let data=try Data(contentsOf:root.appendingPathComponent("Sources/Resources/Assets.xcassets/MeadowBattleHeroAnimationV2.dataset/animation.json"))
        let json=try JSONSerialization.jsonObject(with:data) as! [String:Any],clips=json["clips"] as! [String:[String:Any]]
        var rows:[[String:Any]]=[]
        for clip in ["idle","attack","guard","hit","victory","defeat"] {
            let keys=clips[clip]!["keys"] as! [[String:Any]]
            for i in 0...600 {
                let p=Double(i)/600,u=keys.firstIndex { ($0["t"] as! Double)>=p } ?? keys.count-1,a=keys[max(0,u-1)],b=keys[u]
                let at=a["t"] as! Double,bt=b["t"] as! Double,f=bt==at ? 0:(p-at)/(bt-at)
                func value(_ key:String)->Double { let x=a[key] as! Double,y=b[key] as! Double;return x+(y-x)*f }
                let sample=BowRig.sample(clip:clip,progress:p,lean:clip=="attack" ? 0:value("lean"),crouch:clip=="attack" ? 0:value("crouch"))
                rows.append(["clip":clip,"progress":p,"sample":try JSONSerialization.jsonObject(with:JSONEncoder().encode(sample))])
            }
        }
        try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]).write(to:out.appendingPathComponent("bow-poses.json"))
        print("Exported \(rows.count) shared bow/arm/string poses")
    }
}
