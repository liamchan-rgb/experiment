import Foundation
import CoreGraphics

struct MapPoint: Decodable {
    let x: CGFloat
    let y: CGFloat
    var point: CGPoint { CGPoint(x: x, y: y) }
}

enum SceneDefinition {
    struct Road: Decodable {
        let from: Int
        let to: Int
        let width: CGFloat
        let points: [MapPoint]
    }
}

enum HeroFrames {
    static let walkFrameCount = 24
    static var reviewSpeed: CGFloat = 0
    static var authoredFrames = [8, 24, 24]
    static func authoredFrameCount(heroIndex: Int) -> Int { authoredFrames[heroIndex] }
}

private struct Layout: Decodable {
    let authoredFrames: [Int]
    let reviewFrameMs: Double
}

private struct MapFile: Decodable { let roads: [SceneDefinition.Road] }

@main
struct RoadMotionRegression {
    static func require(_ condition: @autoclosure () -> Bool, _ message: String) {
        guard condition() else { fputs("FAIL: \(message)\n", stderr); exit(1) }
    }

    static func main() throws {
        guard CommandLine.arguments.count == 2 else {
            fputs("Usage: check-road-motion.sh <repository-root>\n", stderr); exit(2)
        }
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        func data(_ path: String) throws -> Data { try Data(contentsOf: root.appendingPathComponent(path)) }
        let decoder = JSONDecoder()
        let layout = try decoder.decode(Layout.self, from: data("Sources/Resources/hero-gait.json"))
        HeroFrames.authoredFrames = layout.authoredFrames
        HeroFrames.reviewSpeed = CGFloat(24 / (Double(layout.authoredFrames[0]) * layout.reviewFrameMs / 1000))
        let scene = try decoder.decode(MapFile.self, from: data("Sources/Resources/SceneMap.json"))
        let network = TrailNetwork(roads: scene.roads)
        var simulation = JourneySimulation(network: network)

        require(abs(simulation.travelers[0].speed - HeroFrames.reviewSpeed) < 0.0001,
                "P1 map travel speed must equal the 120ms preview speed")
        require(simulation.travelers[1].speed == 38 && simulation.travelers[2].speed == 45,
                "P2/P3 speeds must remain unchanged")

        let step = HeroFrames.reviewSpeed * CGFloat(layout.reviewFrameMs / 1000)
        require(abs(step - 3) < 0.0001, "P1 preview advances three virtual units per authored pose")
        let adjacentPose = WalkCycle.frame(at: step)
        require(adjacentPose == 4, "The first 120ms sample advances to the next P1 source pose")

        for (vector, expected) in [(CGPoint(x: 3, y: 3), 4), (CGPoint(x: -3, y: -3), 6),
                                   (CGPoint(x: 3, y: -3), 7), (CGPoint(x: -3, y: 3), 5)] {
            var walk = WalkCycle()
            walk.advance(from: .zero, to: vector)
            require(walk.facing == expected, "canonical diagonal must select its authored direction")
        }

        let downRight = network.edges[3].trail
        let upRight = network.edges[1].trail
        for (name, trail, reverse, expectedFacing) in [("down-right", downRight, false, 4), ("up-left", downRight, true, 6),
                                                       ("up-right", upRight, false, 7), ("down-left", upRight, true, 5)] {
            let start = reverse ? trail.length : CGFloat(0)
            let direction: CGFloat = reverse ? -1 : 1
            let p0 = trail.point(at: start)
            let p1 = trail.point(at: max(0, min(trail.length, start + direction * 3)))
            var walk = WalkCycle()
            walk.advance(from: p0, to: p1)
            let facing = walk.facing
            require(walk.frame > 0, "\(name) route must enter a walk pose")
            // A smoothed production road can start/end on a cardinal tangent.
            // Its quadrant is meaningful; assuming every endpoint is 45 degrees is not.
            let quadrants = [4: Set([0, 3, 4]), 6: Set([1, 2, 6]),
                             7: Set([2, 3, 7]), 5: Set([0, 1, 5])]
            require(quadrants[expectedFacing]!.contains(facing), "\(name) route tangent must stay in its travel quadrant")
            print("\(name): facing=\(facing), frame=\(walk.frame), scale=\(WalkCycle.projectedScale(dx: p1.x - p0.x, dy: p1.y - p0.y))")
        }

        var paused = WalkCycle()
        paused.advance(from: .zero, to: CGPoint(x: 10, y: 0))
        paused.advance(from: .zero, to: .zero)
        require(paused.frame == 0 && paused.distance == 0, "stationary pause must clear pose phase")
        paused.advance(from: .zero, to: CGPoint(x: 1, y: 0))
        require(paused.frame == 2, "resume must advance from the first walk pose without stale phase")

        simulation.togglePlayback()
        let beforePlayback = simulation.point(for: 0)
        simulation.advance(0.12)
        require(simulation.point(for: 0) != beforePlayback,
                "P1 route must advance while playback is active")
        let beforeGate = simulation.point(for: 0), otherBefore = simulation.point(for: 1)
        simulation.advance(0.12, p1CanTravel: false)
        require(simulation.point(for: 0) == beforeGate, "authored entry gate holds P1 route")
        require(simulation.point(for: 1) != otherBefore, "P1 entry must not pause P2/P3")
        simulation.togglePlayback()
        let pausedPoint = simulation.point(for: 0)
        simulation.advance(0.12)
        require(simulation.point(for: 0) == pausedPoint, "paused simulation must hold route position")

        let renderer = try String(contentsOf: root.appendingPathComponent("Sources/Game/MeadowShadowRenderer.swift"), encoding: .utf8)
        require(renderer.contains("foot = hero.foot") && renderer.contains("heroChanged"),
                "renderer backdrop invalidation must track hero foot position")
        print("PASS: production WalkCycle, Trail, TrailNetwork, JourneySimulation; P1 speed=\(HeroFrames.reviewSpeed), pause/reset and four road directions")
    }
}
