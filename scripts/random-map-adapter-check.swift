import Foundation
import MeadowWorldSupport

@main struct RandomMapAdapterCheck {
    static func main() throws {
        let output=URL(fileURLWithPath:CommandLine.arguments[1]);try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
        let encoder=JSONEncoder();encoder.outputFormatting=[.prettyPrinted,.sortedKeys]
        var cases=0
        for n in [4,10,30] { for seed:UInt64 in [1,31827,98765] {
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
            let name="map-\(n)-\(seed)"
            try encoder.encode(generated).write(to:output.appendingPathComponent(name+".json"))
            try encoder.encode(definition).write(to:output.appendingPathComponent(name+"-scene.json"))
            let geometry:[[String:Any]]=network.edges.map { ["from":$0.from,"to":$0.to,"points":$0.trail.points.map{[Double($0.x),Double($0.y)]},"length":Double($0.trail.length)] }
            let data=try JSONSerialization.data(withJSONObject:["roads":geometry,"patrol":network.patrol.points.map{[Double($0.x),Double($0.y)]}],options:[.sortedKeys])
            try data.write(to:output.appendingPathComponent(name+"-geometry.json"));cases+=1
        } }
        print("PASS \(cases) production adapter/smoothed road/patrol/prop-clearance/no-false-crossing cases")
    }
}
