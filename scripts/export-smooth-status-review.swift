import Foundation
@main struct SkillFlowExport {
    static func main() throws {
        let requests=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))) as! [[String:Any]]
        let frames=requests.map { r -> [String:Any] in
            let particles=(r["emitters"] as! [[String:Any]]).flatMap { e -> [[String:Any]] in
                MeadowBattleLightField.sample(MeadowBattleLightKind(rawValue:e["kind"] as! String)!,age:e["age"] as! Double,originX:e["x"] as! Double,originY:e["y"] as! Double,groundY:e["floor"] as! Double).map { p in
                    ["id":p.id,"x":p.x,"y":p.y,"angle":p.angle,"size":p.size,"alpha":p.alpha,"cyan":p.cyan,"groundX":p.groundX,"groundY":p.groundY,"groundAge":p.groundAge as Any? ?? NSNull(),"bounces":p.bounces]
                }
            }
            let age=r["recoveryAge"] as? Double ?? -1
            let motes=MeadowBattleRecoveryField.sample(age).map { ["id":Double($0.id),"x":$0.x,"y":$0.y,"size":$0.size,"alpha":$0.alpha] }
            let time=r["time"] as? Double ?? 0
            let alpha=MeadowBattleVisualMotion.shieldOpacity(shield:r["shield"] as? Int ?? 0,time:time,formation:r["formation"] as? Double,birth:r["birth"] as? Double,contact:r["contact"] as? Double,broken:r["broken"] as? Double)
            let wisps=(0..<2).map { i -> [String:Double] in
                let p=MeadowBattleVisualMotion.wisp(age,index:i)
                return ["x":p.x,"y":p.y,"rotation":p.rotation,"scaleX":p.scaleX,"alpha":p.alpha]
            }
            return ["shieldOpacity":alpha,"wisps":wisps,"kind":r["kind"]!,"frame":r["frame"]!,"particles":particles,"recovery":motes,"recoveryPower":MeadowBattleRecoveryField.pulse(age)]
        }
        let geometry:[String:Any]=["centerX":MeadowBattleShieldGeometry.centerX,"centerY":MeadowBattleShieldGeometry.centerY,"diameter":MeadowBattleShieldGeometry.diameter,"contactX":MeadowBattleShieldGeometry.contactX,"contactY":MeadowBattleShieldGeometry.contactY]
        try JSONSerialization.data(withJSONObject:["geometry":geometry,"frames":frames,"scope":"actual production Swift fields for offline composition; not UIKit/device"],options:[.sortedKeys]).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
        print("Exported production particles, recovery and shield geometry for \(frames.count) frames")
    }
}
