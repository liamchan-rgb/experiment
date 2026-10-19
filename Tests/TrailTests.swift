import XCTest
import UIKit
import SpriteKit
import MetalKit
@testable import MeadowJourney

final class TrailTests: XCTestCase {
    private let trail = Trail(points: [CGPoint(x: 0, y: 0), CGPoint(x: 30, y: 0), CGPoint(x: 30, y: 40)])

    func testCapturedViewportKeepsGroundAndArtworkAlignedThroughZoomAndPan() {
        var maximumError: CGFloat = 0
        for size in [CGSize(width: 1190, height: 892), CGSize(width: 844, height: 390)] {
            let view = SKView(frame: CGRect(origin: .zero, size: size))
            let scene = SKScene(size: size); scene.scaleMode = .resizeFill
            let world = SKNode(); scene.addChild(world); view.presentScene(scene)
            for zoom in [CGFloat(1), 1.25, 1.5, 1.8, 1] {
                let scale = min(size.width / 1280, size.height / 720) * zoom
                world.setScale(scale)
                world.position = CGPoint(x: size.width / 2 - 700 * scale, y: size.height / 2 + 430 * scale)
                let camera = MeadowViewport(world: world, scene: scene, view: view)
                let external = MeadowViewport(world: world, scene: scene, viewSize: size)
                for point in [CGPoint.zero, CGPoint(x: 640, y: 360), CGPoint(x: 500, y: 405), CGPoint(x: 1300, y: 800)] {
                    let root = MeadowShadowRenderer.root(point)
                    let clip = camera.matrix * SIMD4(root, 1)
                    let metal = CGPoint(x: CGFloat(clip.x + 1) * size.width / 2, y: CGFloat(1 - clip.y) * size.height / 2)
                    let artwork = scene.convertPoint(toView: world.convert(LivingWorld.position(point), to: scene))
                    maximumError = max(maximumError, hypot(metal.x - artwork.x, metal.y - artwork.y))
                    let sharedClip = external.matrix * SIMD4(root, 1)
                    let sharedPoint = CGPoint(x: CGFloat(sharedClip.x + 1) * size.width / 2, y: CGFloat(1 - sharedClip.y) * size.height / 2)
                    maximumError = max(maximumError, hypot(sharedPoint.x - artwork.x, sharedPoint.y - artwork.y))
                }
            }
        }
        XCTAssertLessThan(maximumError, 0.25)
    }

    func testHeroShadowAtlasChangesFramesWithoutLiveTextureUploads() throws {
        let world = LivingWorld(definition: .load(), props: [])
        let renderer = try MeadowShadowRenderer(device: XCTUnwrap(MTLCreateSystemDefaultDevice()), world: world)
        let uploads = renderer.textureUploadCount
        let foot = CGPoint(x: 640, y: 360)
        let a = try renderer.groundSnapshot(world: world, heroes: [MeadowHeroCaster(index: 0, foot: foot, facing: 1, frame: 1)])
        let b = try renderer.groundSnapshot(world: world, heroes: [MeadowHeroCaster(index: 0, foot: foot, facing: 1, frame: 3)])
        XCTAssertGreaterThan(pixelDifference(a.bgra, b.bgra), 0.0001)
        for facing in 0..<8 {
            try renderer.validateSubmission(world: world, heroes: [MeadowHeroCaster(index: 2, foot: foot, facing: facing, frame: facing % 4)])
        }
        XCTAssertEqual(renderer.textureUploadCount, uploads, "Walking must not decode or upload textures on a live frame")
    }

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

    func testGPUReportKeepsFirstFailureAcrossReload() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let url = directory.appendingPathComponent("report.json")
        let diagnostics = MeadowGPUDiagnostics(url: url)
        diagnostics.begin(device: nil, size: CGSize(width: 1024, height: 768), scale: 2)
        diagnostics.beginStage("A02 ground", kind: "native Metal")
        XCTAssertTrue(MeadowGPUDiagnostics(url: url).savedFailureOrInterruption?.contains("中断") == true)
        diagnostics.failed(NSError(domain: "GPU", code: 2, userInfo: [NSLocalizedDescriptionKey: "first timeout"]), stage: "A02 ground")
        diagnostics.failed(NSError(domain: "GPU", code: 4, userInfo: [NSLocalizedDescriptionKey: "later ignored"]), stage: "A03 depth")
        let reloaded = MeadowGPUDiagnostics(url: url)
        let data = try XCTUnwrap(reloaded.json.data(using: .utf8))
        let report = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
        let failure = try XCTUnwrap(report["firstError"] as? [String: Any])
        XCTAssertEqual(failure["stage"] as? String, "A02 ground")
        XCTAssertEqual(failure["code"] as? Int, 2)
        XCTAssertTrue(reloaded.savedFailureOrInterruption?.contains("first timeout") == true)
    }

    func testNativeDiagnosticSubmitsFourSeparatePasses() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let diagnostics = MeadowGPUDiagnostics(url: directory.appendingPathComponent("report.json"))
        let world = LivingWorld(definition: .load())
        let renderer = try MeadowShadowRenderer(device: XCTUnwrap(MTLCreateSystemDefaultDevice()), world: world)
        diagnostics.begin(device: renderer.device, size: CGSize(width: 256, height: 192), scale: 1)
        try renderer.diagnoseStartup(size: CGSize(width: 256, height: 192), diagnostics: diagnostics)
        let data = try XCTUnwrap(diagnostics.json.data(using: .utf8))
        let report = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
        let events = try XCTUnwrap(report["events"] as? [[String: Any]])
        XCTAssertEqual(events.filter { $0["state"] as? String == "gpuCompleted" }.count, 4)
        XCTAssertNil(report["firstError"])
    }

    func testSingleSurfaceCompositeReusesResourcesAcrossFramesAndZoom() throws {
        let device = try XCTUnwrap(MTLCreateSystemDefaultDevice())
        let queue = try XCTUnwrap(device.makeCommandQueue())
        let size = CGSize(width: 256, height: 192)
        let world = LivingWorld(definition: .load(), renderTerrain: false)
        let native = try MeadowShadowRenderer(device: device, world: world)
        let uploads = native.textureUploadCount
        let scene = SKScene(size: size); scene.backgroundColor = .clear
        scene.addChild(world)
        world.attachSunlight(to: scene)
        let foreground = SKRenderer(device: device); foreground.scene = scene
        let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm, width: 512, height: 384, mipmapped: false)
        descriptor.storageMode = .private; descriptor.usage = .renderTarget
        let target = try XCTUnwrap(device.makeTexture(descriptor: descriptor))
        for index in 0..<4 {
            let scale = CGFloat(0.2 + Double(index) * 0.025)
            world.setScale(scale)
            world.position = CGPoint(x: size.width / 2 - 640 * scale, y: size.height / 2 + 360 * scale)
            let time = Double(index) / 60
            world.update(time: time); foreground.update(atTime: time)
            let camera = MeadowViewport(world: world, scene: scene, viewSize: size)
            let frame = MeadowFrameState(world: world, camera: camera, time: time, heroes: [])
            let command = try MeadowGPUDiagnostics.command(queue: queue, label: "Unit repeated composite \(index)")
            let pass = MTLRenderPassDescriptor(); pass.colorAttachments[0].texture = target
            try native.encodeComposite(command: command, target: pass, frame: frame, foreground: foreground, forceBackground: true)
            command.commit(); command.waitUntilCompleted()
            XCTAssertNil(command.error)
            XCTAssertEqual(command.status, .completed)
        }
        XCTAssertEqual(native.textureUploadCount, uploads)
    }

    func testSunlightSourceAndCoverageStayFixedWhileTheMapZoomsAndPans() throws {
        let size = CGSize(width: 1366, height: 1024)
        let scene = SKScene(size: size)
        let world = LivingWorld(definition: .load(), props: [], renderTerrain: false)
        scene.addChild(world); world.attachSunlight(to: scene)
        let light = try XCTUnwrap(world.sunlightOverlay)
        let sourceInLight = CGPoint(x: -size.width * 0.535, y: size.height * 0.555)
        let expectedSource = CGPoint(x: -size.width * 0.035, y: size.height * 1.055)
        for scale in [CGFloat(0.6), 1, 1.25, 1.5, 1.8] {
            world.setScale(scale)
            world.position = CGPoint(x: 177 - 700 * scale, y: 320 + 430 * scale)
            world.attachSunlight(to: scene)
            XCTAssertTrue(light.parent === scene)
            let source = light.convert(sourceInLight, to: scene)
            XCTAssertEqual(source.x, expectedSource.x, accuracy: 0.0001)
            XCTAssertEqual(source.y, expectedSource.y, accuracy: 0.0001)
            XCTAssertEqual(light.calculateAccumulatedFrame(), CGRect(origin: .zero, size: size))
        }
    }

    func testHeroWarpMatchesCasterProjectionAcrossContactPhases() {
        var maximumError: Float = 0
        var maximumSoleHeight: Float = 0
        var soleVertices = 0
        for hero in 0..<3 { for facing in 0..<8 { for phase in [CGFloat(0), 0.125, 0.25, 0.5, 0.625, 0.75] {
            let pose = HeroPose(heroIndex: hero, facing: facing, frame: WalkCycle.frame(at: phase * 24), phase: phase)
            let instance = ShadowLabInstance(asset: .hero, root: .zero, width: 2, aspect: 1, anchor: SIMD2(0.5, 0.125))
            var mesh = ShadowLabMesh(); mesh.imageCaster(instance, mirrored: HeroFrames.isMirrored(facing), pose: pose)
            let source = pose.sourcePositions, destination = pose.destinationPositions()
            for vertex in mesh.vertices {
                let point = SIMD2(vertex.uvWind.x, 1 - vertex.uvWind.y)
                guard let index = source.firstIndex(where: { abs($0.x - point.x) + abs($0.y - point.y) < 0.00001 }) else { return XCTFail("Caster changed the source texture coordinates") }
                let position = vertex.position
                if abs(point.y - 0.125) < 0.00001 {
                    maximumSoleHeight = max(maximumSoleHeight, abs(position.z))
                    soleVertices += 1
                }
                let projected = SIMD2(position.x / 2 + 0.5,
                                      (position.y * ShadowLabMath.cameraUp.y + position.z * ShadowLabMath.cameraUp.z) / 2 + 0.125)
                let expectedX = HeroFrames.isMirrored(facing) ? 1 - destination[index].x : destination[index].x
                maximumError = max(maximumError, abs(projected.x - expectedX) + abs(projected.y - destination[index].y))
            }
        } } }
        XCTAssertLessThan(maximumError, 0.0001, "The visible actor and depth caster must use identical warped landmarks")
        XCTAssertGreaterThan(soleVertices, 0, "The mesh needs a row at the exact sole anchor")
        XCTAssertTrue(maximumSoleHeight.isFinite, "Footprint depth must remain finite")
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

    func testFencePostsAllTouchTheReceiverAlongTheirPaintedGroundLine() throws {
        let instance = ShadowLabInstance(asset: .fence, root: SIMD3(3, 4, 0), width: 3,
                                         aspect: 295.0 / 471, anchor: SIMD2(0.5, 0.08))
        var mesh = ShadowLabMesh(); mesh.imageCaster(instance)
        // Independent landmarks from the original Fence.png, in top-origin UV.
        for base in [SIMD2<Float>(0.17, 0.50), SIMD2(0.50, 0.68), SIMD2(0.83, 0.86)] {
            let foot = try XCTUnwrap(mesh.vertices.first {
                abs($0.uvWind.x - base.x) < 0.0001 && abs($0.uvWind.y - base.y) < 0.0001
            })
            XCTAssertEqual(foot.position.z, 0, accuracy: 0.0001, "Every post must meet the receiver")
            let screenUp = (foot.position.y - instance.root.y) * ShadowLabMath.cameraUp.y
            XCTAssertEqual(screenUp, (1 - base.y - instance.anchor.y) * instance.screenHeight, accuracy: 0.0001)
        }
        for vertex in mesh.vertices where vertex.uvWind.y > ShadowLabAsset.fenceGroundV(at: vertex.uvWind.x) {
            XCTAssertEqual(vertex.position.z, 0, accuracy: 0.0001, "The painted grass below the posts must not cast a raised shadow")
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
            XCTAssertEqual(UIImage(named: name)?.cgImage?.width, 6400)
            XCTAssertEqual(UIImage(named: name)?.cgImage?.height, 1024)
        }
        for name in ["Hero1Diagonals", "Hero2Diagonals", "Hero3Diagonals"] {
            XCTAssertEqual(UIImage(named: name)?.cgImage?.width, 6400)
            XCTAssertEqual(UIImage(named: name)?.cgImage?.height, 1024)
        }
        for name in ["OakA", "OakB", "WatchTower", "CampTent", "MeadowGround", "Banner"] {
            XCTAssertNotNil(UIImage(named: name))
        }
    }

    func testMeadowBattleUsesRegisteredCampLayersAndOneVisibleSlime() throws {
        for name in ["MeadowCampFarForest", "MeadowCampGround", "MeadowCampMidground", "MeadowCampForeground"] {
            let image = try XCTUnwrap(UIImage(named: name), "Missing approved Meadow battle layer: \(name)")
            XCTAssertEqual(image.cgImage?.width, 1309)
            XCTAssertEqual(image.cgImage?.height, 1201)
        }
        XCTAssertNotNil(UIImage(named: "MeadowBattleSlime"))

        let view = MeadowBattleLandscapeView(frame: CGRect(x: 0, y: 0, width: 900, height: 500))
        view.layoutIfNeeded()
        XCTAssertEqual(view.sceneLayerOrder, MeadowBattleCanvasGeometry.sceneLayerOrder)

        let expectedCanvas = CGRect(x: 177.518734388, y: 0, width: 544.962531224, height: 500)
        XCTAssertEqual(view.sceneCanvasFrame.minX, expectedCanvas.minX, accuracy: 0.001)
        XCTAssertEqual(view.sceneCanvasFrame.minY, expectedCanvas.minY, accuracy: 0.001)
        XCTAssertEqual(view.sceneCanvasFrame.width, expectedCanvas.width, accuracy: 0.001)
        XCTAssertEqual(view.sceneCanvasFrame.height, expectedCanvas.height, accuracy: 0.001)
        for layerFrame in view.sceneLayerFrames {
            XCTAssertEqual(layerFrame.minX, 0, accuracy: 0.01)
            XCTAssertEqual(layerFrame.minY, 0, accuracy: 0.01)
            XCTAssertEqual(layerFrame.width, expectedCanvas.width, accuracy: 0.01,
                           "Every environment plate must use the same full-canvas width")
            XCTAssertEqual(layerFrame.height, expectedCanvas.height, accuracy: 0.01,
                           "Every environment plate must use the same full-canvas height")
        }
        let heroFoot = CGPoint(x: view.heroViewFrame.minX + 128.5 / 256.0 * view.heroViewFrame.width,
                               y: view.heroViewFrame.minY + 224.0 / 256.0 * view.heroViewFrame.height)
        let slimeFoot = CGPoint(x: view.slimeViewFrame.minX + 500.0 / 1024.0 * view.slimeViewFrame.width,
                                y: view.slimeViewFrame.minY + 855.0 / 1024.0 * view.slimeViewFrame.height)
        XCTAssertEqual(heroFoot.x, expectedCanvas.width * 0.30, accuracy: 0.01)
        XCTAssertEqual(heroFoot.y, expectedCanvas.height * 0.69, accuracy: 0.01)
        XCTAssertEqual(slimeFoot.x, expectedCanvas.width * 0.76, accuracy: 0.01)
        XCTAssertEqual(slimeFoot.y, expectedCanvas.height * 0.685, accuracy: 0.01)
        XCTAssertEqual(view.slimeViewFrame.height * (648.0 / 1024.0),
                       expectedCanvas.height * MeadowBattleCanvasGeometry.slimeVisibleHeight, accuracy: 0.01,
                       "The enemy needs enough visual weight to read clearly in the battle pane")
        XCTAssertTrue(view.slimeFacesLeft, "The enemy should face the approaching right-facing traveller")

        let subviewOrder = view.sceneCanvasSubviewOrder
        XCTAssertEqual(subviewOrder, [
            "MeadowCampFarForest", "MeadowCampGround", "MeadowCampMidground",
            "meadowBattleHeroShadow", "meadowBattleSlimeShadow", "meadowBattleHero",
            "meadowBattleSlime", "MeadowCampForeground"
        ], "Scene layers, actor shadows, units and foreground must retain their fixed composite order")
        let heroIndex = try XCTUnwrap(subviewOrder.firstIndex(of: "meadowBattleHero"))
        let slimeIndex = try XCTUnwrap(subviewOrder.firstIndex(of: "meadowBattleSlime"))
        let foregroundIndex = try XCTUnwrap(subviewOrder.firstIndex(of: "MeadowCampForeground"))
        XCTAssertLessThan(subviewOrder.firstIndex(of: "MeadowCampMidground")!, heroIndex)
        XCTAssertLessThan(heroIndex, foregroundIndex)
        XCTAssertLessThan(slimeIndex, foregroundIndex)
        XCTAssertEqual(subviewOrder.filter { $0 == "meadowBattleSlime" }.count, 1,
                       "The approved scene sample should show one distinct enemy")
        XCTAssertTrue(subviewOrder.contains("meadowBattleHeroShadow"))
        XCTAssertTrue(subviewOrder.contains("meadowBattleSlimeShadow"))
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
        XCTAssertEqual(walk.frame, 14)
        XCTAssertEqual(walk.facing, 3)
        walk.advance(from: CGPoint(x: 13, y: 0), to: CGPoint(x: 13, y: 0))
        XCTAssertEqual(walk.frame, 0)
        XCTAssertEqual(walk.distance, 13)
        walk.advance(from: CGPoint(x: 13, y: 0), to: CGPoint(x: 14, y: 0))
        XCTAssertEqual(walk.frame, 15)
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
        XCTAssertEqual(walk.frame, 7)
        XCTAssertEqual(walk.lift, 0, accuracy: 0.001)
        walk.advance(from: CGPoint(x: 6, y: 0), to: CGPoint(x: 12, y: 0))
        XCTAssertEqual(walk.frame, 13)
        XCTAssertEqual(walk.lift, 0, accuracy: 0.001)
        walk.advance(from: CGPoint(x: 12, y: 0), to: CGPoint(x: 12, y: 0))
        XCTAssertEqual(walk.frame, 0)
        XCTAssertEqual(walk.lift, 0, accuracy: 0.001)
    }

    func testAuthoredWalkUses24WholeFramesAndNoLegWarp() {
        XCTAssertEqual(HeroFrames.walkFrameCount, 24)
        for hero in 0..<3 { for facing in 0..<8 { for frame in 0...24 {
            let pose = HeroPose(heroIndex: hero, facing: facing, frame: frame, phase: CGFloat(frame) / 24)
            XCTAssertEqual(pose.frame, frame)
            XCTAssertEqual(pose.sourcePositions, pose.destinationPositions())
            XCTAssertEqual(pose.bodyOffset(), .zero)
            let rect = HeroFrames.atlasRect(facing: facing, frame: frame)
            XCTAssertEqual(rect.x + rect.z / 2, (Float(frame) + 0.5) / 25, accuracy: 0.00001)
            XCTAssertLessThanOrEqual(rect.x + rect.z, 1.00001)
        } } }
    }

    func testHeroCasterAnchorsEachPlantedFootAndTracksLift() {
        for hero in 0..<3 { for facing in 0..<8 { for frame in 0...24 {
            let pose = HeroPose(heroIndex: hero, facing: facing, frame: frame, phase: CGFloat(frame) / 24)
            let instance = ShadowLabInstance(asset: .hero, root: .zero, width: 2, aspect: 1, anchor: SIMD2(0.5, 0.125))
            var mesh = ShadowLabMesh(); mesh.imageCaster(instance, pose: pose)
            for foot in pose.footLandmarks {
                let vertex = mesh.vertices.first { abs($0.uvWind.x - foot.x) < 0.00001 && abs(1 - $0.uvWind.y - foot.y) < 0.00001 }
                guard let vertex else { return XCTFail("The depth mesh omitted a foot landmark") }
                let expectedHeight = foot.z * 2 / ShadowLabMath.cameraUp.z
                XCTAssertEqual(vertex.position.z, expectedHeight, accuracy: 0.0001,
                               "Planted and swinging soles must share the artwork's exact depth, hero \(hero), facing \(facing), frame \(frame)")
            }
        } } }
    }

    func testFootprintGroundLineFollowsAlternatingFeet() {
        for hero in 0..<3 { for facing in [0, 2, 4, 5, 6, 7] {
            let a = HeroPose(heroIndex: hero, facing: facing, frame: 1, phase: 0)
            let b = HeroPose(heroIndex: hero, facing: facing, frame: 13, phase: 0.5)
            for leg in 0..<2 {
                let af = a.footLandmarks[leg], bf = b.footLandmarks[leg]
                let change = abs(a.groundLine(at: SIMD2(af.x, af.y)) - b.groundLine(at: SIMD2(bf.x, bf.y)))
                XCTAssertGreaterThan(change, 0.02, "Each anatomical boot must exchange ground depth, hero \(hero), facing \(facing), leg \(leg)")
            }
        } }
    }

    func testGaitTestCoversEightRoadIndependentHeadingsAndSupportsStepping() {
        for facing in GaitTest.menuOrder {
            var test = GaitTest(); test.select(facing)
            let previous = test.point(for: 0)
            test.advance(0.1)
            var walk = WalkCycle(); walk.advance(from: previous, to: test.point(for: 0))
            XCTAssertEqual(walk.facing, facing)
            test.paused = true
            let frozen = test.point(for: 0); test.advance(10)
            XCTAssertEqual(test.point(for: 0), frozen)
            let phase = test.phase; test.step()
            XCTAssertEqual(test.phase - phase, 1.0 / 24, accuracy: 0.0001)
            XCTAssertEqual(test.point(for: 1).x - test.point(for: 0).x, 110, accuracy: 0.0001)
        }
    }

    func testNorthwestLegMeshNeverFoldsAcrossTheCycle() {
        func area(_ a: SIMD2<Float>, _ b: SIMD2<Float>, _ c: SIMD2<Float>) -> Float {
            (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
        }
        var minimumRatio: Float = 1
        for hero in 0..<3 { for sample in 0..<128 {
            let phase = CGFloat(sample) / 128
            let pose = HeroPose(heroIndex: hero, facing: 6, frame: WalkCycle.frame(at: phase * 24), phase: phase)
            let source = pose.sourcePositions, destination = pose.destinationPositions()
            for row in 0..<8 { for column in 0..<8 {
                let a = row * 9 + column, b = a + 9, c = b + 1, d = a + 1
                for indices in [[a, b, c], [a, c, d]] {
                    let original = area(source[indices[0]], source[indices[1]], source[indices[2]])
                    let warped = area(destination[indices[0]], destination[indices[1]], destination[indices[2]])
                    minimumRatio = min(minimumRatio, warped / original)
                }
            } }
        } }
        XCTAssertGreaterThan(minimumRatio, 0.15, "Boot exchange must not invert or collapse the connecting mesh")
    }

    func testBattleLayoutKeepsSharedRowsAndExpandsForExplorationAndMonsterTurns() {
        for size in [CGSize(width: 1366, height: 1024), CGSize(width: 1920, height: 1080),
                     CGSize(width: 1190, height: 820)] {
            let player = MeadowBattleLayout(size: size, safeArea: .zero, mode: .playerTurn)
            let monster = MeadowBattleLayout(size: size, safeArea: .zero, mode: .monsterTurn)
            let explore = MeadowBattleLayout(size: size, safeArea: .zero, mode: .exploration)
            let canvas = CGRect(origin: .zero, size: size)
            for rect in [player.header, player.map, player.battlefield, player.track, player.details,
                         monster.map, monster.battlefield, monster.track, explore.map] {
                XCTAssertTrue(canvas.contains(rect))
            }
            XCTAssertEqual(player.map.minY, player.battlefield.minY)
            XCTAssertEqual(player.map.height, player.battlefield.height)
            XCTAssertGreaterThan(player.map.height, size.height * 0.45)
            XCTAssertLessThan(player.details.height, size.height * 0.17)
            XCTAssertGreaterThan(player.track.minY, player.map.maxY)
            XCTAssertGreaterThan(player.details.minY, player.track.maxY)
            XCTAssertEqual(player.track.minX, player.map.minX)
            XCTAssertEqual(player.track.maxX, player.battlefield.maxX, accuracy: 0.001)
            XCTAssertEqual(player.details.width, player.track.width)
            XCTAssertEqual(monster.details, .zero)
            XCTAssertGreaterThan(monster.map.height, player.map.height)
            XCTAssertEqual(monster.map.height, monster.battlefield.height)
            XCTAssertEqual(explore.track, .zero)
            XCTAssertEqual(explore.battlefield, .zero)
            XCTAssertGreaterThan(explore.map.width, player.map.width * 1.9)
        }
    }

    func testBattlePreviewCropsAroundTravellerAndKeepsTerrainAcrossViewport() throws {
        let fullSize = CGSize(width: 1366, height: 1024)
        let scene = GameScene(size: fullSize)
        scene.activateForMetalRenderer()
        scene.resizeMapViewport(to: fullSize, referenceSize: fullSize)
        scene.setZoom(1.25)
        scene.panBy(CGPoint(x: -85, y: 40))
        let original = try XCTUnwrap(scene.metalFrame(viewSize: fullSize))
        for reference in [fullSize, CGSize(width: 1190, height: 892)] {
            scene.beginBattlePreviewCamera()
            let pane = CGSize(width: reference.width / 2, height: reference.height)
            scene.resizeMapViewport(to: pane, referenceSize: reference)
            let frame = try XCTUnwrap(scene.metalFrame(viewSize: pane))
            XCTAssertEqual(frame.camera.xAxis.dx,
                           min(reference.width / 1280, reference.height / 720) * 1.25, accuracy: 0.001)
            let traveller = frame.camera.project(frame.heroes[0].foot)
            XCTAssertTrue(CGRect(origin: .zero, size: pane).insetBy(dx: 80, dy: 80).contains(traveller))
            // Panning into any world edge must still leave terrain across the viewport.
            for translation in [CGPoint(x: -10000, y: -10000), CGPoint(x: 20000, y: 20000)] {
                scene.panBy(translation)
                let camera = try XCTUnwrap(scene.metalFrame(viewSize: pane)).camera
                let topLeft = camera.project(LivingWorld.bounds.origin)
                let bottomRight = camera.project(CGPoint(x: LivingWorld.bounds.maxX, y: LivingWorld.bounds.maxY))
                XCTAssertLessThanOrEqual(topLeft.x, 0.01)
                XCTAssertLessThanOrEqual(topLeft.y, 0.01)
                XCTAssertGreaterThanOrEqual(bottomRight.x, pane.width - 0.01)
                XCTAssertGreaterThanOrEqual(bottomRight.y, pane.height - 0.01)
            }
            scene.resizeMapViewport(to: fullSize, referenceSize: fullSize)
            scene.endBattlePreviewCamera()
            let restored = try XCTUnwrap(scene.metalFrame(viewSize: fullSize))
            XCTAssertEqual(restored.camera, original.camera)
            XCTAssertEqual(restored.heroes.map(\.foot), original.heroes.map(\.foot))
        }
    }

    func testGaitTestReturnsToTheSameMapCameraAndActorPositions() throws {
        let scene = GameScene(size: CGSize(width: 1366, height: 1024))
        scene.activateForMetalRenderer()
        scene.setZoom(1.5)
        let original = try XCTUnwrap(scene.metalFrame(viewSize: scene.size))
        scene.toggleGaitTest()
        let test = try XCTUnwrap(scene.metalFrame(viewSize: scene.size))
        XCTAssertFalse(test.includeEnvironment)
        XCTAssertTrue(test.heroes.allSatisfy { $0.facing == 6 })
        scene.setGaitDirection(7); scene.stepGait()
        scene.toggleGaitTest()
        let restored = try XCTUnwrap(scene.metalFrame(viewSize: scene.size))
        XCTAssertTrue(restored.includeEnvironment)
        XCTAssertEqual(restored.camera, original.camera)
        XCTAssertEqual(restored.heroes.map(\.foot), original.heroes.map(\.foot))
    }

    func testWalkCycleVisitsEveryFrameAndWrapsWithoutRepeatingPassingArt() {
        let frames = (0..<24).map { WalkCycle.frame(at: CGFloat($0) + 0.01) }
        XCTAssertEqual(frames, Array(1...24))
        XCTAssertEqual(WalkCycle.frame(at: 24), 1)
        XCTAssertEqual(WalkCycle.frame(at: 23.99), 24)
        for facing in 0..<8 {
            var walk = WalkCycle()
            let d = [CGPoint(x: 0, y: 1), CGPoint(x: -1, y: 0), CGPoint(x: 0, y: -1), CGPoint(x: 1, y: 0),
                     CGPoint(x: 1, y: 1), CGPoint(x: -1, y: 1), CGPoint(x: -1, y: -1), CGPoint(x: 1, y: -1)][facing]
            let scale = WalkCycle.projectedScale(dx: d.x, dy: d.y)
            let length = hypot(d.x, d.y)
            walk.advance(from: .zero, to: CGPoint(x: d.x / length * scale * 6, y: d.y / length * scale * 6))
            XCTAssertEqual(walk.distance, 6, accuracy: 0.0001)
        }
    }

    func testHeroFramesBundlesAllDirectionsAndWholeMirroredRightProfile() {
        XCTAssertEqual(HeroFrames.sourceFacing(3), 3)
        XCTAssertFalse(HeroFrames.isMirrored(3), "Right art is mirrored once during packing, including its footprint data")
        for hero in 1...3 {
            let poses = HeroFrames.load(hero)
            XCTAssertEqual(poses.count, 8)
            XCTAssertTrue(poses.allSatisfy { $0.count == 25 })
            for facing in 0..<8 {
                let hashes = Set((1...24).map { frame -> Data in
                    let image = poses[facing][frame].cgImage()
                    return UIImage(cgImage: image).pngData()!
                })
                XCTAssertEqual(hashes.count, 24, "Every walk pose must contain a distinct rasterized limb pose")
            }
        }
    }

    func testHeroPoseSpriteKitRenderingKeepsAllHeroContoursConnected() throws {
        let view = SKView(frame: CGRect(x: 0, y: 0, width: 384, height: 384))
        let headings = [0, 2, 3, 4, 5, 6, 7]
        let headingNames = ["front", "back", "right", "SE", "SW", "NW", "NE"]
        let framesForPhase = [1, 7, 13, 19]
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
                    sprite.warpGeometry = nil
                    let canvas = SKNode()
                    // Inspect complete rendered poses with a transparent surrounding gutter.
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
