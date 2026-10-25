import Foundation
import MeadowBattleSupport
import ClassroomGameCore

@main struct Export {
    static func main() throws {
        let out=URL(fileURLWithPath:CommandLine.arguments[1]);try FileManager.default.createDirectory(at:out,withIntermediateDirectories:true)
        var rows:[[String:Any]]=[],requests:[[String:Any]]=[]
        for scenario in ["support","rally","items","revive"] {
            let model=try PartyEncounter(seed:17,sessionID:"review-"+scenario)
            if scenario=="rally" { let i=model.prepare(.support,target:"p1")!;_ = try model.commit(i.id) }
            if scenario=="revive" { try model.engine.apply(.editResources(unit:"p1",value:ResourcePatch(health:0))) }
            let count=scenario=="items" ? 270:scenario=="revive" ? 180:160
            var current:PartyIntent?,start=0.0,fired=false
            var births:[String:Double]=[:],heals:[String:Double]=[:],forms:[String:Double]=[:]
            var messages:[[String:Any]]=[]
            for frame in 0..<count {
                let time=Double(frame)*0.02
                if frame==20 || (scenario=="items" && frame==140) {
                    let action:PartyAction=scenario=="support" ? .support:scenario=="rally" ? .rally:scenario=="revive" ? .revivalStone:frame==20 ? .largePotion:.shieldPotion
                    let target=scenario=="items" && frame==20 ? "p2":"p1"
                    current=model.prepare(action,target:target)!;start=time;fired=false
                    let offset=max(0,action.impact-0.46)
                    for id in current!.targets {
                        if ["support","heal","revive"].contains(action.visual) { heals[id]=time+offset }
                        if ["support","guard"].contains(action.visual) { forms[id]=time+offset }
                    }
                }
                var receipt:OperationReceipt?
                let age=time-start
                if let intent=current,!fired,age+1e-9>=intent.action.impact {
                    fired=true;receipt=try model.commit(intent.id)
                    if let receipt {
                        for id in ["p1","p2"] {
                            let before=receipt.before.units[id]!,after=receipt.after.units[id]!
                            if after.shield>before.shield { births[id]=time }
                            if after.health>before.health { messages.append(["id":id,"text":"＋\(after.health-before.health)","at":time,"kind":"heal"]) }
                            if after.shield>before.shield { messages.append(["id":id,"text":"盾 ＋\(after.shield-before.shield)","at":time,"kind":"shield"]) }
                            if after.damageBuff != before.damageBuff { messages.append(["id":id,"text":"伤害 ＋2","at":time,"kind":"buff"]) }
                        }
                    }
                }
                if let intent=current,age>=intent.action.duration { current=nil }
                var units:[[String:Any]]=[]
                for id in ["p1","p2","m1","m2"] {
                    let u=model.state.units[id]!,pose=PartyVisual.pose(unit:u,intent:current,age:age,time:time)
                    units.append(["id":id,"name":u.name,"hp":u.health,"maxHP":u.baseAttributes.maximumHealth,"shield":u.shield,"ap":u.ap,"buff":u.damageBuff?.amount ?? 0,"buffRounds":u.damageBuff?.roundsLeft ?? 0,"clip":pose.clip,"progress":pose.progress])
                    if id.hasPrefix("p") {
                        var r:[String:Any]=["kind":scenario+"-"+id,"frame":frame,"time":time,"shield":u.shield,"emitters":[]]
                        if let at=heals[id],u.isAlive { r["recoveryAge"]=time-at }
                        if let at=forms[id],u.shield==0,time-at<1 { r["formation"]=time-at }
                        if let at=births[id] { r["birth"]=time-at }
                        requests.append(r)
                    }
                }
                var action:[String:Any]=[:]
                if let i=current { action=["actor":i.actor,"target":i.target,"targets":i.targets,"action":i.action.rawValue,"visual":i.action.visual,"age":age] }
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
        print("Exported \(rows.count) actual GameCore support/item frames and \(requests.count) attachment samples")
    }
}
