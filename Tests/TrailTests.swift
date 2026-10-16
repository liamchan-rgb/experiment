import XCTest
import UIKit
import SpriteKit
import MetalKit
@testable import MeadowJourney

final class TrailTests: XCTestCase {
    private let trail = Trail(points: [CGPoint(x: 0, y: 0), CGPoint(x: 30, y: 0), CGPoint(x: 30, y: 40)])

    func testMeadowGroundContainsOpaqueGrassRoadsAndShadows() throws {
        let world = LivingWorld(definition: .load())
        let renderer = try MeadowShadowRenderer(device: XCTUnwrap(MTLCreateSystemDefaultDevice()), world: world)
        let ground = try renderer.groundSnapshot(world: world)
        let grass = try renderer.groundSnapshot(world: world, roads: false)
        let lit = try renderer.groundSnapshot(world: world, shadows: false)
        var visible = 0, opaque = 0, minimum = 255, maximum = 0
        for offset in stride(from: 0, to: ground.bgra.count, by: 4) {
            if ground.bgra[offset + 3] == 255 { opaque += 1 }
            let green = Int(ground.bgra[offset + 1])
            minimum = min(minimum, green); maximum = max(maximum, green)
            if max(ground.bgra[offset], max(ground.bgra[offset + 1], ground.bgra[offset + 2])) > 24 { visible += 1 }
        }
        XCTAssertEqual(opaque, ground.bgra.count / 4)
        XCTAssertGreaterThan(Double(visible) / Double(ground.bgra.count / 4), 0.95, "The entire terrain must be visible, including in shade")
        XCTAssertGreaterThan(maximum - minimum, 25, "A flat clear color is not a textured ground")
        XCTAssertGreaterThan(pixelDifference(ground.bgra, grass.bgra), 0.1, "Road coverage must reach the final target")
        XCTAssertGreaterThan(pixelDifference(ground.bgra, lit.bgra), 0.1, "Depth shadows must reach the opaque ground")
        attachLab(ground.image, "main-ground-native-pixels")
    }

    func testShadowLabCutoutPipelineSubmitsContourModes() throws {
        let renderer = try ShadowLabRenderer(device: XCTUnwrap(MTLCreateSystemDefaultDevice()))
        for models in [false, true] {
            try renderer.validateFrameSubmission(frame: ShadowLabFrame(time: 1.1, models: models))
        }
        try renderer.validateFrameSubmission(frame: ShadowLabFrame(time: 12, sunAngle: 0.85, models: true, seed: 8))
    }

    func testMeadowAllAssetsSubmitSharedShadowDepth() throws {
        let world = LivingWorld(definition: .load())
        let renderer = try MeadowShadowRenderer(device: XCTUnwrap(MTLCreateSystemDefaultDevice()), world: world)
        XCTAssertGreaterThan(renderer.casterCount, 200)
        XCTAssertTrue(Set(world.casterProps.map(\.asset)).isSuperset(of: ["OakA", "OakB", "Pines", "WatchTower", "CampTent", "Fence", "RockLow", "RockHigh", "RockSmall", "Flowers", "Shrub"]))
        for facing in 0..<8 {
            let heroes = (0..<3).map { MeadowHeroCaster(index: $0, foot: CGPoint(x: 300 + $0 * 100, y: 442), facing: facing, frame: facing % 4) }
            world.update(time: TimeInterval(facing))
            try renderer.validateSubmission(world: world, heroes: heroes)
        }
    }

    func testHeroWarpMatchesCasterProjectionAcrossContactPhases() {
        var maximumError: Float = 0
        for hero in 0..<3 { for facing in 0..<8 { for phase in [CGFloat(0), 0.125, 0.25, 0.5, 0.625, 0.75] {
            let pose = HeroPose(heroIndex: hero, facing: facing, frame: WalkCycle.frame(at: phase * 24), phase: phase)
            let instance = ShadowLabInstance(asset: .hero, root: .zero, width: 2, aspect: 1, anchor: SIMD2(0.5, 0.125))
            var mesh = ShadowLabMesh(); mesh.imageCaster(instance, mirrored: facing == 3, pose: pose)
            let source = pose.sourcePositions, destination = pose.destinationPositions()
            for vertex in mesh.vertices {
                let point = SIMD2(vertex.uvWind.x, 1 - vertex.uvWind.y)
                guard let index = source.firstIndex(where: { abs($0.x - point.x) + abs($0.y - point.y) < 0.00001 }) else { return XCTFail("Caster changed the source texture coordinates") }
                let position = vertex.position
                let projected = SIMD2(position.x / 2 + 0.5,
                                      (position.y * ShadowLabMath.cameraUp.y + position.z * ShadowLabMath.cameraUp.z) / 2 + 0.125)
                let expectedX = facing == 3 ? 1 - destination[index].x : destination[index].x
                maximumError = max(maximumError, abs(projected.x - expectedX) + abs(projected.y - destination[index].y))
            }
        } } }
        XCTAssertLessThan(maximumError, 0.0001, "The visible actor and depth caster must use identical warped landmarks")
    }

    func testReliefPreservesArtCoordinatesForEveryAsset() {
        let assets: [ShadowLabAsset] = [.tree, .oakB, .pines, .tower, .hero, .tent, .fence, .rockLow, .rockHigh, .rockSmall, .shrub, .flowers]
        for asset in assets {
            let instance = ShadowLabInstance(asset: asset, root: SIMD3(3, 4, 0), width: 3, aspect: 1.2, anchor: SIMD2(0.5, asset.anchorY))
            var mesh = ShadowLabMesh(); mesh.imageCaster(instance)
            for vertex in mesh.vertices {
                let p = SIMD3(vertex.position.x, vertex.position.y, vertex.position.z) - instance.root
                XCTAssertEqual(p.x, (vertex.uvWind.x - 0.5) * instance.width, accuracy: 0.0001)
                let projected = p.y * ShadowLabMath.cameraUp.y + p.z * ShadowLabMath.cameraUp.z
                XCTAssertEqual(projected, (1 - vertex.uvWind.y - instance.anchor.y) * instance.screenHeight, accuracy: 0.0001)
                XCTAssertGreaterThanOrEqual(p.z, 0)
            }
        }
    }

    func testRoadMaskUsesOneUnionAtJunctions() throws {
        let roads = SceneDefinition.load().roads
        let bounds = LivingWorld.bounds
        let image = MeadowRoadMask.make(network: TrailNetwork(roads: roads), bounds: bounds)
        let reversed = MeadowRoadMask.make(network: TrailNetwork(roads: Array(roads.reversed())), bounds: bounds)
        XCTAssertEqual(image.width, 1600); XCTAssertEqual(image.height, 1160)
        let first = try XCTUnwrap(image.dataProvider?.data) as Data
        let second = try XCTUnwrap(reversed.dataProvider?.data) as Data
        XCTAssertEqual(first, second, "Road overlap must be independent of drawing order")
        XCTAssertGreaterThan(first.filter { $0 > 0 && $0 < 255 }.count, 10000, "Edges need a continuous distance mask")
    }

    func testShadowLabUsesActualDepthForImageContours() throws {
        let device = try XCTUnwrap(MTLCreateSystemDefaultDevice())
        let renderer = try ShadowLabRenderer(device: device)
        var frame = ShadowLabFrame(time: 0, wind: false, artwork: false, heroFrame: 1)
        let shaded = try renderer.snapshot(frame: frame)
        frame.shadows = false
        let lit = try renderer.snapshot(frame: frame)
        XCTAssertGreaterThan(shaded.depthTexels, 1000, "The shadow texture must contain rasterized 3D geometry")
        XCTAssertGreaterThan(shaded.minimumDepth, 0)
        XCTAssertLessThan(shaded.minimumDepth, 0.9)
        XCTAssertGreaterThan(pixelDifference(shaded.bgra, lit.bgra), 0.1)
        attachLab(shaded.image, "shadow-lab-ground-receiver")
        attachLab(try renderer.snapshot(frame: ShadowLabFrame(time: 0, wind: false)).image, "shadow-lab-artwork")
        attachLab(try renderer.snapshot(frame: ShadowLabFrame(time: 0, wind: false, models: true)).image, "shadow-lab-proxy-alignment")
    }

    func testShadowLabDepthShadowsRespondToSunWindAndLegPose() throws {
        let renderer = try ShadowLabRenderer(device: XCTUnwrap(MTLCreateSystemDefaultDevice()))
        var frame = ShadowLabFrame(time: 1.1, wind: false, artwork: false, heroFrame: 1)
        let original = try renderer.snapshot(frame: frame)
        frame.sunAngle = 0.85
        let changedSun = try renderer.snapshot(frame: frame)
        XCTAssertGreaterThan(pixelDifference(original.bgra, changedSun.bgra), 0.5)
        frame.sunAngle = -0.65; frame.wind = true
        let changedWind = try renderer.snapshot(frame: frame)
        XCTAssertGreaterThan(pixelDifference(original.bgra, changedWind.bgra), 0.02)
        frame.wind = false; frame.heroFrame = 3
        let changedLegs = try renderer.snapshot(frame: frame)
        XCTAssertGreaterThan(pixelDifference(original.bgra, changedLegs.bgra), 0.001)
        attachLab(changedSun.image, "shadow-lab-opposite-sun")
    }

    private func attachLab(_ image: UIImage, _ name: String) {
        let attachment = XCTAttachment(image: image)
        attachment.name = name; attachment.lifetime = .keepAlways
        add(attachment)
    }

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
        for name in ["Hero1Diagonals", "Hero2Diagonals", "Hero3Diagonals"] {
            XCTAssertEqual(UIImage(named: name)?.cgImage?.width, 1024)
            XCTAssertEqual(UIImage(named: name)?.cgImage?.height, 1024)
        }
        for name in ["OakA", "OakB", "WatchTower", "CampTent", "MeadowGround", "Banner"] {
            XCTAssertNotNil(UIImage(named: name))
        }
    }

    func testOnlyTheTowerGetsAnAdditionalBanner() throws {
        let world = LivingWorld(definition: SceneDefinition.load())
        let camps = world.children.filter { $0.name == "CampTent" }
        let towers = world.children.filter { $0.name == "WatchTower" }
        XCTAssertEqual(camps.count, 1)
        XCTAssertTrue(camps.allSatisfy { $0.childNode(withName: "banner") == nil })
        XCTAssertEqual(towers.count, 2)
        for tower in towers {
            let sprite = try XCTUnwrap(tower as? SKSpriteNode)
            let banner = try XCTUnwrap(tower.childNode(withName: "banner") as? SKSpriteNode)
            XCTAssertEqual(banner.position.x, 0, accuracy: 0.001)
            XCTAssertEqual(banner.position.y, sprite.size.height * (LivingWorld.towerBannerRoofAnchorY - sprite.anchorPoint.y), accuracy: 0.001)
            XCTAssertLessThan(banner.zPosition, 0, "The tower roof must occlude the lower pole")
        }
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
        walk.advance(from: .zero, to: CGPoint(x: 10, y: 4.5))
        XCTAssertEqual(walk.facing, 3)
        walk.advance(from: .zero, to: CGPoint(x: 10, y: 6))
        XCTAssertEqual(walk.facing, 4)
        walk.advance(from: .zero, to: CGPoint(x: 10, y: 4))
        XCTAssertEqual(walk.facing, 4)
        walk.advance(from: .zero, to: CGPoint(x: 10, y: 3))
        XCTAssertEqual(walk.facing, 3)
        for (point, row) in [(CGPoint(x: 10, y: 10), 4), (CGPoint(x: -10, y: 10), 5),
                             (CGPoint(x: -10, y: -10), 6), (CGPoint(x: 10, y: -10), 7)] {
            var diagonal = WalkCycle()
            diagonal.advance(from: .zero, to: point)
            XCTAssertEqual(diagonal.facing, row)
        }
    }

    func testWalkCycleDoesNotLiftAuthoredContactSoles() {
        var walk = WalkCycle()
        walk.advance(from: .zero, to: CGPoint(x: 6, y: 0))
        XCTAssertEqual(walk.frame, 2)
        XCTAssertEqual(walk.lift, 0, accuracy: 0.001)
        walk.advance(from: CGPoint(x: 6, y: 0), to: CGPoint(x: 12, y: 0))
        XCTAssertEqual(walk.frame, 3)
        XCTAssertEqual(walk.lift, 0, accuracy: 0.001)
        walk.advance(from: CGPoint(x: 12, y: 0), to: CGPoint(x: 12, y: 0))
        XCTAssertEqual(walk.frame, 0)
        XCTAssertEqual(walk.lift, 0, accuracy: 0.001)
    }

    func testHeroPoseAlternatesWholeLegReachAcrossAllHeadings() {
        let bottomLeftLeg = 3 // bottom row, x=0.40 in the 8x8 grid
        for facing in 0..<8 {
            let first = HeroPose(heroIndex: 0, facing: facing, frame: 1, phase: 0)
            let second = HeroPose(heroIndex: 0, facing: facing, frame: 3, phase: 0.5)
            XCTAssertEqual(first.legDrive, 1, accuracy: 0.001)
            XCTAssertEqual(second.legDrive, -1, accuracy: 0.001)
            XCTAssertEqual(first.sourcePositions.count, 81)
            XCTAssertEqual(first.destinationPositions().count, 81)

            let source = first.sourcePositions[bottomLeftLeg]
            let a = first.destinationPositions()[bottomLeftLeg] - source
            let b = second.destinationPositions()[bottomLeftLeg] - source
            let direction = [SIMD2<Float>(0, -1), SIMD2(-1, 0), SIMD2(0, 1), SIMD2(-1, 0),
                             SIMD2(0.70710677, -0.70710677), SIMD2(-0.70710677, -0.70710677),
                             SIMD2(-0.70710677, 0.70710677), SIMD2(0.70710677, 0.70710677)][facing]
            let firstReach = a.x * direction.x + a.y * direction.y
            let secondReach = b.x * direction.x + b.y * direction.y
            if first.legReachPoints > 0.1 {
                XCTAssertGreaterThan(firstReach, 0)
                XCTAssertLessThan(secondReach, 0)
            } else {
                XCTAssertEqual(firstReach, 0, accuracy: 0.001, "Profile strides already match their contact spacing")
                XCTAssertEqual(secondReach, 0, accuracy: 0.001)
            }
            XCTAssertEqual(first.warpGeometry().numberOfColumns, HeroPose.gridColumns)
            XCTAssertEqual(first.warpGeometry().numberOfRows, HeroPose.gridRows)
            XCTAssertEqual(first.bodyOffset(), .zero)
            XCTAssertEqual(second.bodyOffset(), .zero)
        }
    }

    func testHeroPosePassesContinuouslyBetweenRepeatedPassingFrames() {
        let before = HeroPose(heroIndex: 0, facing: 0, frame: 2, phase: 0.499)
        let after = HeroPose(heroIndex: 0, facing: 0, frame: 3, phase: 0.501)
        let beforeGrid = before.destinationPositions()
        let afterGrid = after.destinationPositions()
        XCTAssertEqual(beforeGrid.count, afterGrid.count)
        let largestStep = zip(beforeGrid, afterGrid).map { lhs, rhs in
            let dx = lhs.x - rhs.x, dy = lhs.y - rhs.y
            return (dx * dx + dy * dy).squareRoot()
        }.max() ?? 0
        XCTAssertLessThan(largestStep, 0.001,
                          "The lower-leg warp must remain continuous as frame 2 becomes contact B")

        let idle = HeroPose(heroIndex: 0, facing: 0, frame: 0, phase: 0.73)
        XCTAssertEqual(idle.legReachPoints, 0)
        XCTAssertEqual(idle.bodyOffset(), .zero)
        XCTAssertEqual(idle.destinationPositions(), idle.sourcePositions)
        XCTAssertEqual(HeroPose(heroIndex: 0, facing: 0, frame: 2, phase: 0.25).legDrive, 0, accuracy: 0.001)
        XCTAssertEqual(HeroPose(heroIndex: 0, facing: 0, frame: 2, phase: 0.75).legDrive, 0, accuracy: 0.001)
    }

    func testHeroFramesUsesWholeMirroredProfileForRightFacing() {
        XCTAssertEqual(HeroFrames.sourceFacing(3), 1)
        XCTAssertTrue(HeroFrames.isMirrored(3))
        XCTAssertEqual(HeroFrames.sourceFacing(1), 1)
        XCTAssertFalse(HeroFrames.isMirrored(1))
        for hero in 0..<3 {
            let poses = HeroFrames.load(hero + 1)
            for frame in 0..<4 {
                XCTAssertTrue(poses[3][frame] === poses[1][frame],
                              "Right-facing animation should reuse the intact left-profile frame")
            }
            XCTAssertEqual(HeroPose(heroIndex: hero, facing: 1, frame: 1, phase: 0).legReachPoints, 0)
            XCTAssertEqual(HeroPose(heroIndex: hero, facing: 3, frame: 1, phase: 0).legReachPoints, 0)
        }
    }

    func testHeroPoseSpriteKitRenderingKeepsAllHeroContoursConnected() throws {
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 384, height: 384))
        let headings = [0, 2, 3, 4, 5, 6, 7]
        let headingNames = ["front", "back", "right", "SE", "SW", "NW", "NE"]
        let framesForPhase = [1, 2, 3, 2]
        let phases: [CGFloat] = [0, 0.25, 0.5, 0.75]
        let phaseNames = ["contact A", "passing", "contact B", "passing"]
        let cell = CGSize(width: 104, height: 104)

        for hero in 0..<3 {
            let source = HeroFrames.load(hero + 1)
            var renderedPoses: [[UIImage]] = []
            for row in phases.indices {
                var rowImages: [UIImage] = []
                for column in headings.indices {
                    let facing = headings[column]
                    let frame = framesForPhase[row]
                    let phase = phases[row]
                    let sprite = SKSpriteNode(texture: source[facing][frame],
                                              size: CGSize(width: 192, height: 192))
                    sprite.anchorPoint = CGPoint(x: 0.5, y: 0.125)
                    sprite.xScale = HeroFrames.isMirrored(facing) ? -1 : 1
                    sprite.warpGeometry = HeroPose(heroIndex: hero, facing: facing,
                                                   frame: frame, phase: phase).warpGeometry()
                    let canvas = SKNode()
                    // Give the warp room to move the soles past the source quad.
                    let bounds = SKSpriteNode(color: .clear, size: CGSize(width: 384, height: 384))
                    canvas.addChild(bounds)
                    canvas.addChild(sprite)
                    let rendered = try XCTUnwrap(view.texture(from: canvas)).cgImage()
                    let components = alphaComponentCount(rendered)
                    XCTAssertEqual(components, 1,
                                   "Hero \(hero + 1), facing \(facing), frame \(frame), phase \(phase) split into \(components) alpha components")
                    let crop = try XCTUnwrap(croppedCharacter(rendered))
                    rowImages.append(UIImage(cgImage: crop))
                }
                renderedPoses.append(rowImages)
            }
            let sheetSize = CGSize(width: cell.width * CGFloat(headings.count + 1),
                                   height: cell.height * CGFloat(phases.count + 1))
            let format = UIGraphicsImageRendererFormat()
            format.scale = 1
            format.opaque = false
            let renderer = UIGraphicsImageRenderer(size: sheetSize, format: format)
            let sheet = renderer.image { context in
                UIColor(red: 0.10, green: 0.14, blue: 0.11, alpha: 1).setFill()
                context.cgContext.fill(CGRect(origin: .zero, size: sheetSize))
                let headerAttributes: [NSAttributedString.Key: Any] = [
                    .font: UIFont.systemFont(ofSize: 8, weight: .medium),
                    .foregroundColor: UIColor.white
                ]
                for column in headings.indices {
                    (headingNames[column] as NSString).draw(
                        at: CGPoint(x: cell.width * CGFloat(column + 1) + 3, y: 3),
                        withAttributes: headerAttributes)
                }
                for row in phases.indices {
                    (phaseNames[row] as NSString).draw(
                        at: CGPoint(x: 2, y: cell.height * CGFloat(row + 1) + 3),
                        withAttributes: headerAttributes)
                }
                for row in phases.indices {
                    for column in headings.indices {
                        let target = CGRect(origin: .zero, size: cell).insetBy(dx: 8, dy: 10).offsetBy(
                            dx: cell.width * CGFloat(column + 1), dy: cell.height * CGFloat(row + 1))
                        let fitted = aspectFit(renderedPoses[row][column].size, in: target)
                        renderedPoses[row][column].draw(in: fitted)
                    }
                }
            }
            attachLab(sheet, "gait-hero-\(hero + 1)-front-back-diagonals")
        }
    }

    func testGroundProjectionKeepsTheFeetFixedAndCastsAwayFromSun() {
        let projection = ShadowProjection(body: CGSize(width: 60, height: 100), anchorY: 0.02, ratio: 0.9, softness: 2)
        XCTAssertEqual(projection.point(x: 0, height: 0), .zero)
        let crown = projection.point(x: 0, height: 80)
        XCTAssertGreaterThan(crown.x, 0)
        XCTAssertLessThan(crown.y, 0)
        XCTAssertEqual(crown.x / -crown.y, MeadowSun.cast.dx / MeadowSun.cast.dy, accuracy: 0.001)
        XCTAssertGreaterThan(projection.size.width, 60 + crown.x)
        let fullProjection = projection.point(x: 0, height: 98)
        XCTAssertEqual(projection.offset.x, fullProjection.x / 2, accuracy: 0.001)
        XCTAssertEqual(projection.offset.y, fullProjection.y / 2, accuracy: 0.001)
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

    func testAuthoredGaitFramesDoNotGetShaderLegAlphaTears() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 192, height: 192))
        for hero in 1...3 {
            let frames = HeroFrames.load(hero)
            let node = SKSpriteNode(texture: frames[0][1], size: CGSize(width: 192, height: 192))
            for direction in 0..<8 {
                node.texture = frames[direction][1]
                effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size,
                              gait: SIMD2(Float(direction), 1))
                let contactA = try renderedPixels(node, in: view)

                // Changing the contact phase without changing its texture may
                // alter no alpha pixels: the shader must not splice a boot from
                // the other side of the image around the knees.
                effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size,
                              gait: SIMD2(Float(direction), 3))
                let sameFrameOtherPhase = try renderedPixels(node, in: view)
                XCTAssertLessThan(alphaDifference(contactA, sameFrameOtherPhase), 0.25,
                                  "Gait attributes must not cut or replace the authored leg silhouette")

                // The paired pose comes from the real atlas column instead.
                node.texture = frames[direction][3]
                let contactB = try renderedPixels(node, in: view)
                XCTAssertGreaterThan(pixelDifference(contactA, contactB), 0.5,
                                     "Contact A/B must use the two authored full-frame poses")
            }
        }
    }

    func testDiagonalContactsAndPassingFramesRenderDistinctPoses() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 192, height: 192))
        for hero in 1...3 {
            let frames = HeroFrames.load(hero)
            XCTAssertEqual(frames.count, 8)
            let node = SKSpriteNode(color: .white, size: CGSize(width: 192, height: 192))
            for direction in 4...7 {
                effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size, gait: SIMD2(Float(direction), 1))
                node.texture = frames[direction][1]
                let left = try renderedPixels(node, in: view)
                effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size, gait: SIMD2(Float(direction), 2))
                node.texture = frames[direction][2]
                let passing = try renderedPixels(node, in: view)
                effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size, gait: SIMD2(Float(direction), 3))
                node.texture = frames[direction][3]
                let right = try renderedPixels(node, in: view)
                XCTAssertGreaterThan(pixelDifference(left, right), 0.5)
                XCTAssertGreaterThan(pixelDifference(left, passing), 0.5)
                XCTAssertGreaterThan(largestOpaqueComponentRatio(right), 0.80,
                                     "The complete authored leg frame should remain connected (hero \(hero), direction \(direction))")
            }
        }
    }

    func testFullViewTreeWindChangesTheRenderedSilhouette() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 96, height: 96))
        let node = SKSpriteNode(texture: SKTexture(imageNamed: "OakA"), size: CGSize(width: 60, height: 80))
        effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size, wind: 1, phase: 0.4)
        effects.update(time: 0)
        let first = try renderedPixels(node, in: view)
        effects.update(time: 2)
        let later = try renderedPixels(node, in: view)
        let alphaChange = stride(from: 3, to: first.count, by: 4).reduce(0) {
            $0 + abs(Int(first[$1]) - Int(later[$1]))
        }
        XCTAssertGreaterThan(Double(alphaChange) / Double(first.count / 4), 0.8,
                             "Tree motion must deform its silhouette at the full-view size, independently of lighting")
    }

    func testProjectedShadowActuallyRendersTheCurrentLegPose() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 384, height: 192))
        let contacts = HeroFrames.load(1)[0]
        let shadow = ProjectedShadow(texture: contacts[1], body: CGSize(width: 192, height: 192),
                                     anchorY: 0.125, ratio: 0.82, softness: 1.2, opacity: 0.52, shader: effects.shadow)
        shadow.update(foot: .zero, texture: contacts[1], gait: SIMD2(0, 1))
        let left = try renderedPixels(shadow, in: view)
        shadow.update(foot: .zero, texture: contacts[3], gait: SIMD2(0, 3))
        let right = try renderedPixels(shadow, in: view)
        XCTAssertGreaterThan(pixelDifference(left, right), 0.05,
                             "The ground projection must use the currently selected full animation frame")
    }

    func testMeadowPlantShaderSoftensThePaintedGrassBase() throws {
        let effects = EnvironmentShaders()
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 192, height: 192))
        let node = SKSpriteNode(texture: SKTexture(imageNamed: "Flowers"), size: CGSize(width: 192, height: 192))
        effects.apply(effects.vegetation, to: node, origin: .zero, extent: node.size)
        let crispBase = try renderedPixels(node, in: view)
        effects.apply(effects.meadowPlants, to: node, origin: .zero, extent: node.size)
        let blendedBase = try renderedPixels(node, in: view)
        XCTAssertEqual(crispBase.count, blendedBase.count)
        let width = Int(Double(crispBase.count / 4).squareRoot())
        let rows = max(1, width / 4)
        func difference(in range: Range<Int>) -> Int {
            range.reduce(0) { total, y in
                total + (0..<width).reduce(0) { rowTotal, x in
                    let offset = (y * width + x) * 4 + 3
                    return rowTotal + abs(Int(crispBase[offset]) - Int(blendedBase[offset]))
                }
            }
        }
        let edgeChange = difference(in: 0..<rows) + difference(in: (width - rows)..<width)
        let interiorChange = difference(in: rows..<(width - rows))
        let overallChange = pixelDifference(crispBase, blendedBase)
        XCTAssertGreaterThan(overallChange, 0.05,
                             "The plant shader must alter rendered pixels (texture side: \(width))")
        XCTAssertGreaterThan(edgeChange, 10_000, "The painted sod edge should blend into the meadow")
        XCTAssertLessThan(interiorChange, edgeChange, "The blend should preserve the flower heads and upper foliage")
    }

    private func alphaComponentCount(_ image: CGImage) -> Int {
        let pixels = rgbaPixels(image)
        let width = image.width, height = image.height
        guard pixels.count == width * height * 4 else { return 0 }
        var occupied = (0..<(width * height)).map { pixels[$0 * 4 + 3] > 32 }
        var components = 0
        for start in occupied.indices where occupied[start] {
            components += 1
            var queue = [start]
            occupied[start] = false
            var cursor = 0
            while cursor < queue.count {
                let index = queue[cursor]
                cursor += 1
                let x = index % width, y = index / width
                for dy in -1...1 {
                    for dx in -1...1 where dx != 0 || dy != 0 {
                        let nx = x + dx, ny = y + dy
                        guard nx >= 0, nx < width, ny >= 0, ny < height else { continue }
                        let neighbor = ny * width + nx
                        if occupied[neighbor] {
                            occupied[neighbor] = false
                            queue.append(neighbor)
                        }
                    }
                }
            }
        }
        return components
    }

    private func croppedCharacter(_ image: CGImage) -> CGImage? {
        let pixels = rgbaPixels(image)
        let width = image.width, height = image.height
        guard pixels.count == width * height * 4 else { return nil }
        var minX = width, minY = height, maxX = -1, maxY = -1
        for y in 0..<height {
            for x in 0..<width where pixels[(y * width + x) * 4 + 3] > 32 {
                minX = min(minX, x); minY = min(minY, y)
                maxX = max(maxX, x); maxY = max(maxY, y)
            }
        }
        guard maxX >= minX, maxY >= minY else { return nil }
        let pad = max(4, max(maxX - minX, maxY - minY) / 16)
        let crop = CGRect(x: CGFloat(max(0, minX - pad)), y: CGFloat(max(0, minY - pad)),
                          width: CGFloat(min(width, maxX + pad + 1) - max(0, minX - pad)),
                          height: CGFloat(min(height, maxY + pad + 1) - max(0, minY - pad))).integral
        return image.cropping(to: crop)
    }

    private func rgbaPixels(_ image: CGImage) -> [UInt8] {
        var pixels = [UInt8](repeating: 0, count: image.width * image.height * 4)
        let drew = pixels.withUnsafeMutableBytes { buffer -> Bool in
            guard let context = CGContext(data: buffer.baseAddress, width: image.width, height: image.height,
                                          bitsPerComponent: 8, bytesPerRow: image.width * 4,
                                          space: CGColorSpaceCreateDeviceRGB(),
                                          bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return false }
            context.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
            return true
        }
        return drew ? pixels : []
    }

    private func aspectFit(_ size: CGSize, in rect: CGRect) -> CGRect {
        guard size.width > 0, size.height > 0 else { return rect }
        let scale = min(rect.width / size.width, rect.height / size.height)
        let fitted = CGSize(width: size.width * scale, height: size.height * scale)
        return CGRect(x: rect.midX - fitted.width / 2, y: rect.midY - fitted.height / 2,
                      width: fitted.width, height: fitted.height)
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

    private func alphaDifference(_ first: [UInt8], _ second: [UInt8]) -> Double {
        guard first.count == second.count, first.count >= 4 else { return .infinity }
        var total = 0
        for index in stride(from: 3, to: first.count, by: 4) {
            total += abs(Int(first[index]) - Int(second[index]))
        }
        return Double(total) / Double(first.count / 4)
    }

    private func largestOpaqueComponentRatio(_ pixels: [UInt8]) -> Double {
        let width = Int(Double(pixels.count / 4).squareRoot())
        var occupied = (0..<(width * width)).map { pixels[$0 * 4 + 3] > 32 }
        let total = occupied.filter { $0 }.count
        guard total > 0 else { return 0 }
        var largest = 0
        for start in occupied.indices where occupied[start] {
            var queue = [start]
            occupied[start] = false
            var cursor = 0
            while cursor < queue.count {
                let index = queue[cursor]
                cursor += 1
                let x = index % width, y = index / width
                for dy in -1...1 {
                    for dx in -1...1 where dx != 0 || dy != 0 {
                        let nx = x + dx, ny = y + dy
                        guard nx >= 0, nx < width, ny >= 0, ny < width else { continue }
                        let neighbor = ny * width + nx
                        if occupied[neighbor] {
                            occupied[neighbor] = false
                            queue.append(neighbor)
                        }
                    }
                }
            }
            largest = max(largest, queue.count)
        }
        return Double(largest) / Double(total)
    }
}
