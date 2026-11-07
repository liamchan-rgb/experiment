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
    struct Road: Decodable { let from: Int; let to: Int; let width: CGFloat; let points: [MapPoint]; var sampled: Bool? = nil }
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
        var traces: [[String:Any]] = [], stopCases = 0, cadenceCases = 0, wideTurnCases = 0
        let poseDistance: CGFloat = 3, hold = AuthoredLocomotion.stopHold
        // Distance stepping keeps every sample off the exact 3/6-unit start boundaries.
        let stepSeconds = 0.05
        for d in 0..<8 {
            let hint = directions[d]
            func tick(_ actor: inout AuthoredLocomotion, _ requested: Bool, _ seconds: Double = 0.05, travel: Bool = true) {
                require(actor.allowsTravel(requested:requested),"animation never holds route travel")
                let scale = WalkCycle.projectedScale(dx:hint.x,dy:hint.y)
                let length = hypot(hint.x,hint.y)
                let amount = CGFloat(seconds)*plan.finishSpeed*scale/length
                let next = travel && requested ? CGPoint(x:hint.x*amount,y:hint.y*amount) : .zero
                actor.advance(from:.zero,to:next,seconds:seconds,requested:requested,headingHint:hint)
            }
            func sample(_ actor: AuthoredLocomotion) -> [String:Any] {
                ["facing":actor.facing,"frame":actor.frame,"column":column(actor.frame),"phase":Double(actor.phase),"state":actor.state.rawValue]
            }
            func stand(_ actor: inout AuthoredLocomotion) {
                var guardSteps = 0
                while (actor.facing != d || actor.state != .walking) && guardSteps < 40 { tick(&actor,true);guardSteps += 1 }
                tick(&actor,false,0)
                while actor.state != .idle && guardSteps < 80 { tick(&actor,false);guardSteps += 1 }
                require(actor.state == .idle && actor.facing == d,"reach a standing pose in this direction")
            }
            var actor = AuthoredLocomotion(plan:plan)
            stand(&actor)
            var sequence = [sample(actor)]
            // Start: route travel begins at once; start poses follow distance, not a timer.
            tick(&actor,true,0,travel:false);sequence.append(sample(actor))
            require(actor.state == .starting && actor.frame == 25 && actor.facing == d,"direction/start01 on order")
            var travelled: CGFloat = 0
            while actor.state == .starting {
                tick(&actor,true);travelled += CGFloat(stepSeconds)*plan.finishSpeed;sequence.append(sample(actor))
                if actor.state == .starting { require(actor.frame == (travelled < poseDistance ? 25 : 26),"start pose by travelled distance") }
                require(travelled < poseDistance*2+1,"start lasts two pose-distances")
            }
            require(actor.state == .walking && column(actor.frame) == plan.directions[d].entryPhase+1,"native entry phase")
            // Walk: poses advance in order, never skipped or reversed.
            var previousPose = (actor.frame-1)/3
            for _ in 0..<40 {
                let before = actor.distance
                tick(&actor,true);sequence.append(sample(actor))
                require(abs(actor.distance-before-CGFloat(stepSeconds)*plan.finishSpeed)<0.000001,"distance follows travel")
                let pose = (actor.frame-1)/3
                require(pose == previousPose || pose == (previousPose+1)%8,"walk pose order");previousPose = pose
            }
            // Arrival: stop poses at once, idle after two short holds, no stepping in place.
            let arrival = actor.distance
            tick(&actor,false,0);sequence.append(sample(actor))
            require(actor.state == .stopping && actor.frame == 27 && actor.distance == arrival,"stop01 on arrival")
            tick(&actor,false,hold*0.5);require(actor.frame == 27,"stop01 hold")
            tick(&actor,false,hold*0.75);sequence.append(sample(actor));require(actor.frame == 28 && actor.distance == arrival,"stop02")
            tick(&actor,false,hold*0.75);sequence.append(sample(actor));require(actor.state == .idle && actor.frame == 0 && actor.phase == 0,"idle within two holds")
            require(actor.facing == d,"stand facing the travel direction")
            traces.append(["direction":d,"specifiedStartStop":sequence])
            // A stop at any walk phase is immediate and bounded.
            for phase in 0..<8 {
                var a = AuthoredLocomotion(plan:plan)
                stand(&a);tick(&a,true,0,travel:false)
                var guardSteps = 0
                while (a.state != .walking || (a.frame-1)/3 != phase) && guardSteps < 400 { tick(&a,true,0.01);guardSteps += 1 }
                require(a.state == .walking && (a.frame-1)/3 == phase,"reach walk phase")
                tick(&a,false,0);require(a.state == .stopping && a.frame == 27,"stop from any phase at once")
                var waited = 0.0
                while a.state != .idle && waited < 1 { tick(&a,false,1.0/60);waited += 1.0/60 }
                require(a.state == .idle && waited <= hold*2+1.0/60+0.000001,"stop settles within two holds")
                stopCases += 1
            }
            // Rendering frequency changes neither when start ends nor the entry pose.
            for fps in [30,60,120] {
                var a = AuthoredLocomotion(plan:plan);stand(&a);tick(&a,true,0,travel:false)
                let dt = 1/Double(fps);var time = 0.0
                while a.state == .starting && time < 1 { tick(&a,true,dt);time += dt }
                let startTime = Double(poseDistance*2/plan.finishSpeed)
                require(a.state == .walking && time >= startTime-0.000001 && time < startTime+dt+0.000001,"entry independent of render FPS")
                require((a.frame-1)/3 == plan.directions[d].entryPhase,"entry pose independent of render FPS")
                cadenceCases += 1
            }
            // Re-ordering during the stop keeps the stride: no second start.
            var resumed = AuthoredLocomotion(plan:plan)
            stand(&resumed);for _ in 0..<12 { tick(&resumed,true) }
            tick(&resumed,false,0);let before = resumed.distance
            tick(&resumed,true)
            require(resumed.state == .walking && resumed.distance > before,"resume keeps distance phase")
        }
        // Wide turns step through every intermediate sector (180° via screen-down)
        // and finish within three turn steps, standing or walking.
        let sectorOfRow = AuthoredLocomotion.sectorOfRow
        var wideTurnTrace: [[String:Any]] = []
        for from in 0..<8 {
            for offset in 2...4 {
                for walking in [false,true] {
                    let to = AuthoredLocomotion.rowOfSector[(sectorOfRow[from]+offset)%8]
                    var a = AuthoredLocomotion(plan:plan)
                    let u = directions[from], v = directions[to]
                    for _ in 0..<40 { a.advance(from:.zero,to:CGPoint(x:u.x,y:u.y),seconds:0.05,requested:true) }
                    if !walking {
                        a.advance(from:.zero,to:.zero,seconds:0,requested:false)
                        while a.state != .idle { a.advance(from:.zero,to:.zero,seconds:0.05,requested:false) }
                    }
                    require(a.facing == from,"turn starts from the old facing")
                    var facings = [a.facing], time = 0.0
                    while a.facing != to && time < 1 {
                        a.advance(from:.zero,to:CGPoint(x:v.x,y:v.y),seconds:1.0/60,requested:true);time += 1.0/60
                        if a.facing != facings.last! { facings.append(a.facing) }
                    }
                    require(a.facing == to && time <= AuthoredLocomotion.turnStep*Double(offset-2)+2.0/60+0.001,"wide turn completes quickly")
                    require(facings.count == offset+1,"wide turn passes each intermediate sector")
                    for (x,y) in zip(facings,facings.dropFirst()) {
                        let step = (sectorOfRow[y]-sectorOfRow[x]+8)%8
                        require(step == 1 || step == 7,"turn moves one sector at a time")
                    }
                    if offset == 4 && (from == 1 || from == 3) { require(facings.contains(0),"left/right reversal turns through screen-down") }
                    wideTurnTrace.append(["from":from,"to":to,"walking":walking,"facings":facings,"seconds":time])
                    wideTurnCases += 1
                }
            }
        }
        // Adjacent turns while walking switch at once and keep the distance phase.
        var turns = AuthoredLocomotion(plan:plan)
        for _ in 0..<10 { turns.advance(from:.zero,to:CGPoint(x:0,y:1),seconds:0.05,requested:true) }
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
        var mapTrace: [[String:Any]] = [], mapStates = Set<String>()
        for step in 0..<1200 {
            if step == 270 || step == 420 { simulation.togglePlayback() }
            if step == 720 { simulation.orderSelected(to:network.edges[3].trail.points.last!) }
            let before = simulation.point(for:0)
            let requested = simulation.isPlaying && !simulation.travelers[0].isWaiting
            simulation.advance(0.01,p1CanTravel:traveller.allowsTravel(requested:requested))
            let after = simulation.point(for:0)
            let nextRequested = simulation.isPlaying && !simulation.travelers[0].isWaiting
            traveller.advance(from:before,to:after,seconds:0.01,requested:nextRequested,headingHint:simulation.heading(for:0))
            if !nextRequested && before == after {
                require(traveller.state == .stopping || traveller.state == .idle,"no stepping in place once the route stops")
            }
            mapStates.insert(traveller.state.rawValue)
            if step % 12 == 0 {
                mapTrace.append(["time":Double(step)*0.01,"x":Double(after.x),"y":Double(after.y),"facing":traveller.facing,"frame":traveller.frame,"column":column(traveller.frame),"phase":Double(traveller.phase),"state":traveller.state.rawValue])
            }
        }
        require(mapStates.contains("starting"),"real road enters start")
        require(mapStates.contains("stopping"),"real road pause reaches stop")
        require(mapStates.contains("idle"),"real road pause reaches idle")
        // Foot-locked pose timing derived from the same hero-gait.json soles.
        guard let soles = GaitTiming.p1Soles(rigJSON:data) else { require(false,"P1 soles in hero-gait.json");return }
        let timing = GaitTiming.footLocked(soles:soles)
        var timingReport: [[String:Any]] = [], footLockedCases = 0
        for d in 0..<8 {
            let row = timing.windows[d]
            require(abs(row.reduce(0,+)-24)<0.000001 && row.allSatisfy { $0 > 0.5 },"windows cover one24-unit cycle")
            // Planted-sole travel per pose in the projected metric (as in GaitTiming).
            let v = directions[d], n = hypot(v.x,v.y), u = CGPoint(x:v.x/n,y:v.y/n), metric = hypot(u.x,u.y*2)
            let planted = (0..<8).map { pose -> CGFloat in
                let a = soles[d][pose], b = soles[d][(pose+1)%8]
                return max(0,(0..<2).map { -((b[$0].x-a[$0].x)*u.x+(b[$0].y-a[$0].y)*u.y) }.max()!)*metric
            }
            let uniformSlip = planted.map { abs($0-3) }.reduce(0,+)/8
            let lockedSlip = zip(planted,row).map { abs($0-$1) }.reduce(0,+)/8
            let isUniform = row.allSatisfy { $0 == 3 }
            if planted.reduce(0,+) < 12 { require(isUniform,"short art stride keeps uniform timing") }
            require(isUniform || lockedSlip < uniformSlip,"foot-locked timing only where it reduces sole slip")
            // Frame space: poses in order, one authored pose per window, same 24-tick clock.
            var previous = -1
            for step in 0..<2400 {
                let frame = timing.frame(at:CGFloat(step)*0.01,facing:d)
                require((1...24).contains(frame),"walk frame stays in the shared24-tick space")
                let pose = (frame-1)/3
                if previous >= 0 && pose != previous { require(pose == (previous+1)%8,"no skipped or reversed pose") }
                previous = pose
            }
            // Start still enters on the authored pose; a stop at any phase is immediate.
            for phase in 0..<8 {
                var a = AuthoredLocomotion(plan:plan,timing:timing)
                let hint = directions[d], scale = WalkCycle.projectedScale(dx:hint.x,dy:hint.y)
                func step(_ requested: Bool, _ seconds: Double) {
                    let amount = CGFloat(seconds)*plan.finishSpeed*scale/hypot(hint.x,hint.y)
                    let next = requested ? CGPoint(x:hint.x*amount,y:hint.y*amount) : .zero
                    a.advance(from:.zero,to:next,seconds:seconds,requested:requested,headingHint:hint)
                }
                var guardSteps = 0
                step(true,0)
                while a.state == .starting && guardSteps < 4000 { step(true,0.001);guardSteps += 1 }
                require(a.state == .walking && column(a.frame) == plan.directions[d].entryPhase+1,"foot-locked entry pose")
                let target = timing.poseStart(facing:d,pose:phase)+0.05
                while (a.distance.truncatingRemainder(dividingBy:24)-target+24).truncatingRemainder(dividingBy:24) > 0.03 && guardSteps < 8000 {
                    step(true,0.001);guardSteps += 1
                }
                require(column(a.frame) == phase+1,"foot-locked walk phase reached")
                let arrival = a.distance
                step(false,0)
                require(a.state == .stopping && a.frame == 27 && a.distance == arrival,"foot-locked stop at once")
                var waited = 0.0
                while a.state != .idle && waited < 1 { step(false,0.005);waited += 0.005 }
                require(a.state == .idle && waited <= AuthoredLocomotion.stopHold*2+0.006,"foot-locked stop settles within two holds")
                footLockedCases += 1
            }
            timingReport.append(["direction":d,"windows":row.map { Double($0) },"plantedTravel":planted.map { Double($0) },
                                 "meanSlipUniform":Double(uniformSlip),"meanSlipFootLocked":Double(lockedSlip),"uniform":isUniform])
        }
        let report:[String:Any] = ["status":"pass","specifiedPaths":8,"stopCommandPhases":stopCases,"wideTurns":wideTurnTrace,"wideTurnCases":wideTurnCases,"renderCadenceCases":cadenceCases,"phasePreservingTurns":turnTrace,"directions":traces,"mapTrace":mapTrace,"mapSimulationSteps":1200,"footLockedTiming":timingReport,"footLockedStopCases":footLockedCases,"deviceExecuted":false,"simulatorExecuted":false]
        let target = URL(fileURLWithPath:CommandLine.arguments[2]);try FileManager.default.createDirectory(at:target.deletingLastPathComponent(),withIntermediateDirectories:true)
        try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:target)
        print("PASS:8 responsive start/stop paths,\(stopCases) immediate stops,\(cadenceCases) render cadence cases,\(wideTurnCases) stepped wide turns,64 phase-preserving turn samples,\(footLockedCases) foot-locked stop cases")
    }
}
