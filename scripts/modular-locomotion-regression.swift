import Foundation
#if canImport(CoreGraphics)
import CoreGraphics
#endif

// Pure production controller check: no SpriteKit, app, device or simulator.
enum HeroFrames {
    static let walkFrameCount = 24
    static let reviewSpeed: CGFloat = 25
}
struct MapPoint: Decodable {
    let x: CGFloat; let y: CGFloat
    var point: CGPoint { CGPoint(x:x,y:y) }
}
enum SceneDefinition {
    struct Road: Decodable { let from: Int; let to: Int; let width: CGFloat; let points: [MapPoint] }
}
private struct MapFile: Decodable { let roads: [SceneDefinition.Road] }

@main
struct ModularLocomotionRegression {
    static func require(_ condition: @autoclosure () -> Bool, _ message: String) {
        guard condition() else { fputs("FAIL: \(message)\n", stderr); exit(1) }
    }
    static let directions: [CGPoint] = [
        CGPoint(x:0,y:1),CGPoint(x:-1,y:0),CGPoint(x:0,y:-1),CGPoint(x:1,y:0),
        CGPoint(x:1,y:1),CGPoint(x:-1,y:1),CGPoint(x:-1,y:-1),CGPoint(x:1,y:-1)
    ]
    static func column(_ frame: Int) -> Int { frame == 0 ? 0 : frame <= 24 ? 1+(frame-1)*8/24 : frame-24+8 }

    static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let data = try Data(contentsOf: root.appendingPathComponent("Sources/Resources/hero-gait.json"))
        let object = try JSONSerialization.jsonObject(with:data) as! [String:Any]
        let encoded = try JSONSerialization.data(withJSONObject:object["modularP1"]!)
        let plan = try JSONDecoder().decode(AuthoredLocomotion.Plan.self,from:encoded)
        var traces: [[String:Any]] = [], stopCases = 0, cadenceCases = 0
        for d in 0..<8 {
            let hint = directions[d]
            func tick(_ actor: inout AuthoredLocomotion, _ requested: Bool, _ seconds: Double = 0.12, travel: Bool = true) {
                let scale = WalkCycle.projectedScale(dx:hint.x,dy:hint.y)
                let length = hypot(hint.x,hint.y)
                let amount = CGFloat(seconds)*plan.finishSpeed*scale/length
                let next = travel && requested && actor.allowsTravel(requested:true)
                    ? CGPoint(x:hint.x*amount,y:hint.y*amount) : .zero
                actor.advance(from:.zero,to:next,seconds:seconds,requested:requested,headingHint:hint)
            }
            func sample(_ actor: AuthoredLocomotion) -> [String:Any] {
                ["facing":actor.facing,"frame":actor.frame,"column":column(actor.frame),"phase":Double(actor.phase),"state":actor.state.rawValue]
            }
            var actor = AuthoredLocomotion(plan:plan)
            // Reach a real standing pose in this direction before recording;
            // a newly constructed actor faces down and is not this idle path.
            tick(&actor,true,0,travel:false);tick(&actor,true);tick(&actor,true);tick(&actor,false,0)
            while actor.state != .idle { tick(&actor,false) }
            var sequence = [sample(actor)]
            tick(&actor,true,0,travel:false);sequence.append(sample(actor))
            require(actor.frame == 25 && actor.facing == d,"direction/start01")
            require(!actor.allowsTravel(requested:true),"start must not slide on the road")
            tick(&actor,true);sequence.append(sample(actor));require(actor.frame == 26,"start02 after120ms")
            tick(&actor,true);require(actor.state == .walking,"start finishes at240ms")
            require(column(actor.frame) == plan.directions[d].entryPhase+1,"native entry phase")
            sequence.append(sample(actor))
            for _ in 0..<15 { tick(&actor,true);sequence.append(sample(actor)) }
            require(column(actor.frame) == plan.directions[d].exitPhase+1,"native exit after16walk poses")
            tick(&actor,false,0);require(actor.state == .settling,"stop waits for designated exit")
            tick(&actor,false);sequence.append(sample(actor));require(actor.frame == 27,"stop01 at native exit boundary")
            tick(&actor,false);sequence.append(sample(actor));require(actor.frame == 28,"stop02 after120ms")
            tick(&actor,false);sequence.append(sample(actor));require(actor.frame == 0 && actor.phase == 0,"idle after stop")
            require(sequence.count == 22,"specified full path22samples")
            traces.append(["direction":d,"specifiedStartStop":sequence])
            // Every command phase is routed THROUGH the authored exit; never
            // claim a new arbitrary-phase stop bridge was generated.
            for phase in 0..<8 {
                var a = AuthoredLocomotion(plan:plan)
                tick(&a,true,0,travel:false);tick(&a,true);tick(&a,true)
                let count = (phase-plan.directions[d].entryPhase+8)%8
                for _ in 0..<count { tick(&a,true) }
                tick(&a,false,0)
                var last = a, waits = 0
                while a.state == .settling && waits < 10 {
                    last = a;tick(&a,false);waits += 1
                }
                require(a.frame == 27,"bounded finish-to-exit")
                require(column(last.frame) == plan.directions[d].exitPhase+1,"stop must follow authored exit pose")
                tick(&a,false);tick(&a,false);require(a.state == .idle,"settle completes")
                stopCases += 1
            }
            // Rendering frequency must not change the two120ms start holds.
            for fps in [30,60,120] {
                var a = AuthoredLocomotion(plan:plan);tick(&a,true,0,travel:false)
                let dt = 1/Double(fps);var time = 0.0
                while time < 0.24-0.000001 {
                    tick(&a,true,dt,travel:false);time += dt
                    if time < 0.12-0.000001 { require(a.frame == 25,"start01 hold") }
                    else if time < 0.24-0.000001 { require(a.frame == 26,"start02 hold") }
                }
                require(a.state == .walking,"entry independent of render FPS");cadenceCases += 1
            }
            // Resume during finishing cancels the pending stop without restarting.
            var resumed = AuthoredLocomotion(plan:plan)
            tick(&resumed,true,0,travel:false);tick(&resumed,true);tick(&resumed,true)
            tick(&resumed,false,0);let before = resumed.distance
            tick(&resumed,true)
            require(resumed.state == .walking && resumed.distance > before,"resume keeps distance phase")
        }
        // At any already-walking phase, a turn must not reset distance.
        var turns = AuthoredLocomotion(plan:plan)
        turns.advance(from:.zero,to:.zero,seconds:0,requested:true,headingHint:directions[0])
        turns.advance(from:.zero,to:.zero,seconds:0.12,requested:true)
        turns.advance(from:.zero,to:.zero,seconds:0.12,requested:true)
        var turnTrace: [[String:Any]] = []
        for direction in [0,4,3,7,2,6,1,5,1,6,2,7,3,4,0,5] {
            let vector = directions[direction], scale = WalkCycle.projectedScale(dx:vector.x,dy:vector.y)
            for _ in 0..<4 {
                let distance = turns.distance, factor = 3*scale/hypot(vector.x,vector.y)
                turns.advance(from:.zero,to:CGPoint(x:vector.x*factor,y:vector.y*factor),seconds:0.12,requested:true)
                require(abs(turns.distance-distance-3)<0.000001,"turn preserves global distance phase")
                require(turns.facing == direction,"turn heading")
                turnTrace.append(["facing":turns.facing,"frame":turns.frame,"column":column(turns.frame),"phase":Double(turns.phase)])
            }
        }
        let map = try JSONDecoder().decode(MapFile.self,from:Data(contentsOf:root.appendingPathComponent("Sources/Resources/SceneMap.json")))
        let network = TrailNetwork(roads:map.roads)
        var simulation = JourneySimulation(network:network), traveller = AuthoredLocomotion(plan:plan)
        simulation.orderSelected(to:network.edges[1].trail.points.last!)
        var mapTrace: [[String:Any]] = []
        for step in 0..<1200 {
            if step == 270 || step == 420 { simulation.togglePlayback() }
            if step == 720 { simulation.orderSelected(to:network.edges[3].trail.points.last!) }
            let before = simulation.point(for:0)
            let requested = simulation.isPlaying && !simulation.travelers[0].isWaiting
            let allowed = traveller.allowsTravel(requested:requested)
            simulation.advance(0.01,p1CanTravel:allowed)
            let after = simulation.point(for:0)
            let nextRequested = simulation.isPlaying && !simulation.travelers[0].isWaiting
            traveller.advance(from:before,to:after,seconds:0.01,requested:nextRequested,headingHint:simulation.heading(for:0))
            if !allowed { require(before == after,"entry/stop gate must hold route position") }
            if step % 12 == 0 {
                mapTrace.append(["time":Double(step)*0.01,"x":Double(after.x),"y":Double(after.y),"facing":traveller.facing,"frame":traveller.frame,"column":column(traveller.frame),"phase":Double(traveller.phase),"state":traveller.state.rawValue])
            }
        }
        require(mapTrace.contains { $0["state"] as? String == "starting" },"real road enters start")
        require(mapTrace.contains { $0["state"] as? String == "stopping" },"real road pause reaches stop")
        require(mapTrace.contains { $0["state"] as? String == "idle" },"real road pause reaches idle")
        let report:[String:Any] = ["status":"pass","specifiedPaths":8,"stopCommandPhases":stopCases,"renderCadenceCases":cadenceCases,"phasePreservingTurns":turnTrace,"directions":traces,"mapTrace":mapTrace,"mapSimulationSteps":1200,"deviceExecuted":false,"simulatorExecuted":false]
        let target = URL(fileURLWithPath:CommandLine.arguments[2]);try FileManager.default.createDirectory(at:target.deletingLastPathComponent(),withIntermediateDirectories:true)
        try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:target)
        print("PASS:8specified paths,\(stopCases)command phases via designated exit,\(cadenceCases)render cadence cases,64phase-preserving turn samples")
    }
}
