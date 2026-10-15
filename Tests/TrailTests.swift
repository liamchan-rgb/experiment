import XCTest
import UIKit
import SpriteKit
@testable import MeadowJourney

final class TrailTests: XCTestCase {
    private let trail = Trail(points: [CGPoint(x: 0, y: 0), CGPoint(x: 30, y: 0), CGPoint(x: 30, y: 40)])

    func testArcLengthInterpolationAndClamping() {
        XCTAssertEqual(trail.length, 70, accuracy: 0.001)
        XCTAssertEqual(trail.point(at: -10), CGPoint(x: 0, y: 0))
        XCTAssertEqual(trail.point(at: 50), CGPoint(x: 30, y: 20))
        XCTAssertEqual(trail.point(at: 100), CGPoint(x: 30, y: 40))
    }

    func testTapProjectsOntoNearestRoadSegment() {
        XCTAssertEqual(trail.distance(nearestTo: CGPoint(x: 12, y: -8)), 12, accuracy: 0.001)
        XCTAssertEqual(trail.distance(nearestTo: CGPoint(x: 38, y: 25)), 55, accuracy: 0.001)
    }

    func testRepeatedPointsDoNotProduceNaN() {
        let repeated = Trail(points: [.zero, .zero, CGPoint(x: 10, y: 0)])
        XCTAssertEqual(repeated.point(at: 5), CGPoint(x: 5, y: 0))
        XCTAssertEqual(repeated.distance(nearestTo: CGPoint(x: 5, y: 9)), 5, accuracy: 0.001)
    }

    func testMovementUsesDistanceAndReflectsAtEndpoint() {
        var hero = Traveler(distance: 65, direction: 1, speed: 10)
        hero.advance(by: 1, on: trail)
        XCTAssertEqual(hero.distance, 65, accuracy: 0.001)
        XCTAssertEqual(hero.direction, -1)
        hero.advance(by: 30, on: trail)
        XCTAssertEqual(hero.distance, 45, accuracy: 0.001)
        XCTAssertEqual(hero.direction, -1)
    }

    func testDestinationStopsWithoutOvershootingOrResuming() {
        var hero = Traveler(distance: 50, direction: 1, destination: 22, speed: 40)
        hero.advance(by: 1, on: trail)
        XCTAssertEqual(hero.distance, 22, accuracy: 0.001)
        XCTAssertTrue(hero.isWaiting)
        hero.advance(by: 1, on: trail)
        XCTAssertEqual(hero.distance, 22, accuracy: 0.001)
    }

    func testReferencePositionsAreOnTheRoad() {
        for point in [CGPoint(x: 440, y: 444), CGPoint(x: 555, y: 441), CGPoint(x: 744, y: 209)] {
            let projected = Trail.meadow.point(at: Trail.meadow.distance(nearestTo: point))
            XCTAssertEqual(projected.x, point.x, accuracy: 0.001)
            XCTAssertEqual(projected.y, point.y, accuracy: 0.001)
        }
    }

    func testBranchToBranchRoutePassesThroughSharedJunction() {
        let network = TrailNetwork(roads: SceneDefinition.load().roads)
        let route = network.route(from: CGPoint(x: 982, y: 430), to: CGPoint(x: 735, y: 578))
        XCTAssertEqual(route.points.first!, CGPoint(x: 982, y: 430))
        XCTAssertEqual(route.points.last!, CGPoint(x: 735, y: 578))
        XCTAssertTrue(route.points.contains(CGPoint(x: 555, y: 441)))
        for point in route.points { XCTAssertLessThan(network.project(point).error, 0.01) }
    }

    func testSameRoadDestinationDoesNotDetourToAnEndpoint() {
        let network = TrailNetwork(roads: SceneDefinition.load().roads)
        let start = CGPoint(x: 383, y: 448)
        let end = CGPoint(x: 503, y: 445)
        let edge = network.edges[0].trail
        let expected = abs(edge.distance(nearestTo: end) - edge.distance(nearestTo: start))
        XCTAssertEqual(network.route(from: start, to: end).length, expected, accuracy: 0.01)
    }

    func testPauseResumePreservesOrderedDestinationAndOtherTravelers() {
        var simulation = JourneySimulation(network: TrailNetwork(roads: SceneDefinition.load().roads))
        simulation.orderSelected(to: CGPoint(x: 982, y: 430))
        simulation.advance(1)
        let destination = simulation.travelers[0].destination
        let point = simulation.point(for: 0)
        simulation.togglePlayback()
        simulation.advance(5)
        XCTAssertEqual(simulation.point(for: 0), point)
        simulation.togglePlayback()
        XCTAssertEqual(simulation.travelers[0].destination, destination)
        XCTAssertTrue(simulation.travelers[1].isWaiting)
        XCTAssertTrue(simulation.travelers[2].isWaiting)
        simulation.advance(1)
        XCTAssertNotEqual(simulation.point(for: 0), point)
    }

    func testNewOrderWhileExplicitlyPausedWaitsForResume() {
        var simulation = JourneySimulation(network: TrailNetwork(roads: SceneDefinition.load().roads))
        simulation.togglePlayback()
        simulation.togglePlayback()
        simulation.orderSelected(to: CGPoint(x: 735, y: 578))
        XCTAssertFalse(simulation.isPlaying)
        XCTAssertNotNil(simulation.travelers[0].destination)
        simulation.togglePlayback()
        XCTAssertTrue(simulation.isPlaying)
        XCTAssertEqual(simulation.mode, .destination)
    }

    func testDiscoveryRouteStopsExactlyAtTheDestination() {
        var simulation = JourneySimulation(network: TrailNetwork(roads: SceneDefinition.load().roads))
        simulation.selected = 2
        simulation.orderSelected(to: CGPoint(x: 735, y: 578))
        simulation.advance(100)
        XCTAssertEqual(simulation.point(for: 2), CGPoint(x: 735, y: 578))
        XCTAssertFalse(simulation.isPlaying)
    }

    func testIndependentRetinaAssetsAreBundledWithoutFlattenedMap() {
        XCTAssertNil(UIImage(named: "MapBackground"))
        for name in ["Hero1Directions", "Hero2Directions", "Hero3Directions"] {
            XCTAssertEqual(UIImage(named: name)?.cgImage?.width, 1536)
            XCTAssertEqual(UIImage(named: name)?.cgImage?.height, 1536)
        }
        for name in ["OakA", "OakB", "WatchTower", "CampTent", "MeadowGround", "Banner"] {
            XCTAssertNotNil(UIImage(named: name))
        }
    }

    func testOnlyTheTowerGetsAnAdditionalBanner() {
        let world = LivingWorld(definition: SceneDefinition.load())
        let camps = world.children.filter { $0.name == "CampTent" }
        let towers = world.children.filter { $0.name == "WatchTower" }
        XCTAssertEqual(camps.count, 1)
        XCTAssertTrue(camps.allSatisfy { $0.childNode(withName: "banner") == nil })
        XCTAssertEqual(towers.count, 2)
        XCTAssertTrue(towers.allSatisfy { $0.childNode(withName: "banner") != nil })
    }

    func testWalkCadenceRetainsItsPhaseAcrossAStop() {
        var walk = WalkCycle()
        walk.advance(from: .zero, to: CGPoint(x: 13, y: 0))
        XCTAssertEqual(walk.frame, 3)
        XCTAssertEqual(walk.facing, 3)
        walk.advance(from: CGPoint(x: 13, y: 0), to: CGPoint(x: 13, y: 0))
        XCTAssertEqual(walk.frame, 0)
        XCTAssertEqual(walk.distance, 13)
        walk.advance(from: CGPoint(x: 13, y: 0), to: CGPoint(x: 14, y: 0))
        XCTAssertEqual(walk.frame, 3)
    }

    func testDiagonalHeadingUsesANarrowStableHysteresisBand() {
        var walk = WalkCycle()
        walk.advance(from: .zero, to: CGPoint(x: 10, y: 0))
        walk.advance(from: .zero, to: CGPoint(x: 10, y: 8))
        XCTAssertEqual(walk.facing, 3)
        walk.advance(from: .zero, to: CGPoint(x: 10, y: 10.9))
        XCTAssertEqual(walk.facing, 0)
        walk.advance(from: .zero, to: CGPoint(x: 10, y: 10))
        XCTAssertEqual(walk.facing, 0)
    }

    func testWalkLiftPeaksBetweenAlternatingContactPoses() {
        var walk = WalkCycle()
        walk.advance(from: .zero, to: CGPoint(x: 6, y: 0))
        XCTAssertEqual(walk.frame, 2)
        XCTAssertEqual(walk.lift, 1.35, accuracy: 0.001)
        walk.advance(from: CGPoint(x: 6, y: 0), to: CGPoint(x: 12, y: 0))
        XCTAssertEqual(walk.frame, 3)
        XCTAssertEqual(walk.lift, 0, accuracy: 0.001)
    }

    func testGroundProjectionKeepsTheFeetFixedAndCastsAwayFromSun() {
        let projection = ShadowProjection(body: CGSize(width: 60, height: 100), anchorY: 0.02, ratio: 0.9, softness: 2)
        XCTAssertEqual(projection.point(x: 0, height: 0), .zero)
        let crown = projection.point(x: 0, height: 80)
        XCTAssertGreaterThan(crown.x, 0)
        XCTAssertLessThan(crown.y, 0)
        XCTAssertEqual(crown.x / -crown.y, MeadowSun.cast.dx / MeadowSun.cast.dy, accuracy: 0.001)
        XCTAssertGreaterThan(projection.size.width, 60 + crown.x)
    }

    func testLiveShadowDirectionTracksTheMovingSunAndKeepsItsGroundAnchor() {
        let firstSun = MeadowSun.cast(at: 0)
        let laterSun = MeadowSun.cast(at: 32)
        let first = ShadowProjection(body: CGSize(width: 60, height: 100), anchorY: 0.02,
                                     ratio: 0.9, softness: 2, sun: firstSun)
        let later = ShadowProjection(body: CGSize(width: 60, height: 100), anchorY: 0.02,
                                     ratio: 0.9, softness: 2, sun: laterSun)
        XCTAssertEqual(first.point(x: 0, height: 0), .zero)
        XCTAssertEqual(later.point(x: 0, height: 0), .zero)
        XCTAssertNotEqual(first.point(x: 0, height: 80), later.point(x: 0, height: 80))
        XCTAssertEqual(later.point(x: 0, height: 80).x / -later.point(x: 0, height: 80).y,
                       laterSun.dx / laterSun.dy, accuracy: 0.001)
    }

    func testRenderedShadowMovesWithTheLiveSunDirection() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 384, height: 256))
        let scene = SKScene(size: CGSize(width: 384, height: 256))
        scene.backgroundColor = .clear
        let shadow = ProjectedShadow(texture: HeroFrames.load(1)[0][1], body: CGSize(width: 192, height: 192),
                                     anchorY: 0.125, ratio: 0.82, softness: 1.2, opacity: 0.52, shader: effects.shadow)
        scene.addChild(shadow)
        let foot = CGPoint(x: 192, y: 160)
        shadow.update(foot: foot, sun: MeadowSun.cast(at: 0))
        let morning = try renderedPixels(scene, in: view)
        shadow.update(foot: foot, sun: MeadowSun.cast(at: 32))
        let later = try renderedPixels(scene, in: view)
        XCTAssertGreaterThan(pixelDifference(morning, later), 0.05,
                             "The rendered silhouette should follow the current directional light")
    }

    func testAtmosphereActuallyChangesRenderedPixels() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 256, height: 256))
        let node = SKSpriteNode(color: .white, size: CGSize(width: 256, height: 256))
        for shader in [effects.frontMist, effects.sunlight] {
            node.shader = shader
            effects.update(time: 0)
            let before = try renderedPixels(node, in: view)
            effects.update(time: 8)
            let after = try renderedPixels(node, in: view)
            XCTAssertGreaterThan(pixelDifference(before, after), 0.4, "Atmosphere must visibly change with a fixed camera")
        }
    }

    func testFrontBackLegRigChangesTheContactPoseWithoutAtlasCoordinates() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 192, height: 192))
        let frames = HeroFrames.load(1)
        let node = SKSpriteNode(texture: frames[0][1], size: CGSize(width: 192, height: 192))
        for direction in [0, 2] {
            node.texture = frames[direction][1]
            effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size, gait: SIMD2(Float(direction), 1))
            let left = try renderedPixels(node, in: view)
            effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size, gait: SIMD2(Float(direction), 3))
            let right = try renderedPixels(node, in: view)
            XCTAssertGreaterThan(pixelDifference(left, right), 0.5, "Opposite leg contact cannot render the same pose")
            XCTAssertLessThanOrEqual(widestOpaqueRow(right), widestOpaqueRow(left) + 2,
                                     "The hem must not stretch into the transparent frame gutters")
        }
    }

    func testProjectedShadowActuallyRendersTheCurrentLegPose() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 384, height: 192))
        let shadow = ProjectedShadow(texture: HeroFrames.load(1)[0][1], body: CGSize(width: 192, height: 192),
                                     anchorY: 0.125, ratio: 0.82, softness: 1.2, opacity: 0.52, shader: effects.shadow)
        shadow.update(foot: .zero, gait: SIMD2(0, 1))
        let left = try renderedPixels(shadow, in: view)
        shadow.update(foot: .zero, gait: SIMD2(0, 3))
        let right = try renderedPixels(shadow, in: view)
        XCTAssertGreaterThan(pixelDifference(left, right), 0.05, "The ground projection must follow the rendered leg pose")
    }

    func testMeadowPlantShaderSoftensThePaintedGrassBase() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 192, height: 192))
        let node = SKSpriteNode(texture: SKTexture(imageNamed: "Flowers"), size: CGSize(width: 192, height: 192))
        effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size)
        let crispBase = try renderedPixels(node, in: view)
        effects.apply(effects.meadowPlants, to: node, origin: .zero, extent: node.size)
        let blendedBase = try renderedPixels(node, in: view)
        let width = 192
        let rows = 24
        func difference(in range: Range<Int>) -> Int {
            range.reduce(0) { total, y in
                total + (0..<width).reduce(0) { rowTotal, x in
                    let offset = (y * width + x) * 4 + 3
                    return rowTotal + abs(Int(crispBase[offset]) - Int(blendedBase[offset]))
                }
            }
        }
        let edgeChange = difference(in: 0..<(rows * 2)) + difference(in: (width - rows * 2)..<width)
        let interiorChange = difference(in: (rows * 2)..<(width - rows * 2))
        XCTAssertGreaterThan(edgeChange, 10_000, "The painted sod edge should blend into the meadow")
        XCTAssertLessThan(interiorChange, edgeChange, "The blend should preserve the flower heads and upper foliage")
    }

    private func renderedPixels(_ node: SKNode, in view: SKView) throws -> [UInt8] {
        let texture = try XCTUnwrap(view.texture(from: node))
        let image = texture.cgImage()
        var bytes = [UInt8](repeating: 0, count: image.width * image.height * 4)
        let drew = bytes.withUnsafeMutableBytes { buffer -> Bool in
            guard let context = CGContext(data: buffer.baseAddress, width: image.width, height: image.height,
                                          bitsPerComponent: 8, bytesPerRow: image.width * 4, space: CGColorSpaceCreateDeviceRGB(),
                                          bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return false }
            context.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
            return true
        }
        XCTAssertTrue(drew)
        return bytes
    }

    private func pixelDifference(_ first: [UInt8], _ second: [UInt8]) -> Double {
        guard first.count == second.count, !first.isEmpty else { return 0 }
        return Double(zip(first, second).reduce(0) { $0 + abs(Int($1.0) - Int($1.1)) }) / Double(first.count)
    }

    private func widestOpaqueRow(_ pixels: [UInt8]) -> Int {
        let width = Int(Double(pixels.count / 4).squareRoot())
        guard width > 0 else { return 0 }
        return (0..<width).map { y in
            let covered = (0..<width).filter { pixels[(y * width + $0) * 4 + 3] > 32 }
            return covered.isEmpty ? 0 : covered.last! - covered.first! + 1
        }.max() ?? 0
    }
}
