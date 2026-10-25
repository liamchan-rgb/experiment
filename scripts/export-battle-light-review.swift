import Foundation

@main struct BattleLightReviewExport {
    static func main() throws {
        let input=URL(fileURLWithPath:CommandLine.arguments[1])
        let requests=try JSONSerialization.jsonObject(with:Data(contentsOf:input)) as! [[String:Any]]
        var frames:[[String:Any]]=[]
        for request in requests {
            let emitters=request["emitters"] as! [[String:Any]]
            let values=emitters.flatMap { e -> [[String:Any]] in
                let kind=MeadowBattleLightKind(rawValue:e["kind"] as! String)!
                return MeadowBattleLightField.sample(kind,age:e["age"] as! Double,originX:e["x"] as! Double,originY:e["y"] as! Double,groundY:e["floor"] as! Double).map { p in
                    ["id":p.id,"x":p.x,"y":p.y,"angle":p.angle,"size":p.size,"alpha":p.alpha,"cyan":p.cyan,"groundX":p.groundX,"groundY":p.groundY,"groundAge":p.groundAge as Any? ?? NSNull(),"bounces":p.bounces]
                }
            }
            frames.append(["kind":request["kind"]!,"frame":request["frame"]!,"particles":values])
        }
        try JSONSerialization.data(withJSONObject:frames,options:[.sortedKeys]).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
        print("Exported production light trajectories for \(frames.count) offline review frames; no UI execution")
    }
}
