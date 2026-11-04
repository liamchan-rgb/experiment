import Foundation
import MeadowWorldSupport

enum HeroFrames {
    static let walkFrameCount = 24
    static let reviewSpeed: CGFloat = 25
}

@main struct RandomMapAdapterCheck {
    static func main() throws {
        let output=URL(fileURLWithPath:CommandLine.arguments[1]);try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
        let encoder=JSONEncoder();encoder.outputFormatting=[.prettyPrinted,.sortedKeys]
        let root=URL(fileURLWithPath:CommandLine.arguments[2])
        let gait=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("Sources/Resources/hero-gait.json"))) as! [String:Any]
        let plan=try JSONDecoder().decode(AuthoredLocomotion.Plan.self,from:JSONSerialization.data(withJSONObject:gait["modularP1"]!))
        var cases=0
        for n in [4,10,30] { for seed:UInt64 in Array(0..<24).map({UInt64($0)}) + [31827,98765] {
            let generated=try MeadowMapGenerator.generate(.suggested(total:n,seed:seed))
            let definition=SceneDefinition.generated(generated)
            let network=TrailNetwork(roads:definition.roads,patrolStart:definition.startNodeID)
            precondition(hypot(network.patrol.points[0].x-generated.spawn.x,network.patrol.points[0].y-generated.spawn.y)<0.000001)
            precondition(network.patrol.points.first==network.patrol.points.last)
            precondition(network.patrol.length>0)
            for road in network.edges {
                precondition(road.trail.length>0 && road.trail.points.allSatisfy{$0.x.isFinite && $0.y.isFinite})
                let a=generated.map.nodes.first{$0.id==road.from}!,b=generated.map.nodes.first{$0.id==road.to}!
                precondition(hypot(road.trail.points[0].x-a.x*1280,road.trail.points[0].y-a.y*720)<0.000001)
                precondition(hypot(road.trail.points.last!.x-b.x*1280,road.trail.points.last!.y-b.y*720)<0.000001)
            }
            for prop in definition.props { precondition(network.project(CGPoint(x:prop.x,y:prop.y)).error>50) }
            func cross(_ a:CGPoint,_ b:CGPoint,_ c:CGPoint)->CGFloat { (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x) }
            for i in network.edges.indices { for j in network.edges.indices where j>i {
                let a=network.edges[i],b=network.edges[j]
                if !Set([a.from,a.to]).isDisjoint(with:[b.from,b.to]) { continue }
                for (p,q) in zip(a.trail.points,a.trail.points.dropFirst()) {
                    for (r,s) in zip(b.trail.points,b.trail.points.dropFirst()) {
                        precondition(!(cross(p,q,r)*cross(p,q,s)<0 && cross(r,s,p)*cross(r,s,q)<0),"False road crossing")
                    }
                }
            } }
            guard [UInt64(1),31827,98765].contains(seed) else { cases+=1;continue }
            let name="map-\(n)-\(seed)"
            try encoder.encode(generated).write(to:output.appendingPathComponent(name+".json"))
            try encoder.encode(definition).write(to:output.appendingPathComponent(name+"-scene.json"))
            let geometry:[[String:Any]]=network.edges.map { ["from":$0.from,"to":$0.to,"points":$0.trail.points.map{[Double($0.x),Double($0.y)]},"length":Double($0.trail.length)] }
            let data=try JSONSerialization.data(withJSONObject:["roads":geometry,"patrol":network.patrol.points.map{[Double($0.x),Double($0.y)]}],options:[.sortedKeys])
            try data.write(to:output.appendingPathComponent(name+"-geometry.json"));cases+=1
            if n==10 && seed==31827 {
                var simulation=JourneySimulation(network:network,spawn:definition.spawn?.point)
                var locomotion=AuthoredLocomotion(plan:plan), walks=[WalkCycle(),WalkCycle(),WalkCycle()]
                simulation.togglePlayback()
                var samples:[[String:Any]]=[]
                for tick in 0..<400 {
                    let previous=(0..<3).map{simulation.point(for:$0)}
                    simulation.advance(0.02,p1CanTravel:locomotion.allowsTravel(requested:simulation.isPlaying && !simulation.travelers[0].isWaiting))
                    for i in 0..<3 { walks[i].advance(from:previous[i],to:simulation.point(for:i)) }
                    locomotion.advance(from:previous[0],to:simulation.point(for:0),seconds:0.02,
                        requested:simulation.isPlaying && !simulation.travelers[0].isWaiting,headingHint:simulation.heading(for:0))
                    let heroes:[[String:Any]]=(0..<3).map { i in
                        let p=simulation.point(for:i)
                        return ["index":i,"x":Double(p.x),"y":Double(p.y),"facing":i==0 ? locomotion.facing : walks[i].facing,
                                "frame":i==0 ? locomotion.frame : walks[i].frame]
                    }
                    samples.append(["time":Double(tick)*0.02,"heroes":heroes])
                }
                try JSONSerialization.data(withJSONObject:samples,options:[.sortedKeys]).write(to:output.appendingPathComponent("walk-samples.json"))
            }
        } }
        print("PASS \(cases) production adapter/smoothed road/patrol/prop-clearance/no-false-crossing cases")
    }
}
