import SpriteKit
import Darwin

final class GameScene: SKScene {
    private var world: LivingWorld!
    private var simulation: JourneySimulation!
    private var actors: [SKSpriteNode] = []
    private var actorRoots: [SKNode] = []
    private var actorLabels: [SKNode] = []
    private var frames: [[[SKTexture]]] = []
    private var walks = [WalkCycle(), WalkCycle(), WalkCycle()]
    private var discoveryNodes: [SKNode] = []
    private var discovered = Set<Int>()
    private var pendingDiscovery: Int?
    private var lastTime: TimeInterval = 0
    private var environmentTime: TimeInterval = 0
    private var frameWindowStart: TimeInterval = 0
    private var frameCounter = 0
    private var measuredFPS: Double = 0
    private var metricSamples: [[String: Any]] = []
    private var baseScale: CGFloat = 1
    private var cameraCenter = CGPoint(x: 640, y: 360)
    private var demoPhase = 0
    private(set) var zoom: CGFloat = 1
    var isRunning: Bool { simulation?.isPlaying ?? false }
    var shadowReady = false
    var shadowFrames = 0
    var startupMetrics: [String: Double] = [:]
    var onForegroundReady: (() -> Void)?
    private var initialFrames = 0
    var onWorldReady: ((LivingWorld) -> Void)?
    var onRenderGround: ((LivingWorld, MeadowViewport, TimeInterval, [MeadowHeroCaster]) -> Void)?
    var onPlaybackChanged: ((Bool) -> Void)?
    var onSelectionChanged: ((String) -> Void)?
    var onDiagnostics: ((String) -> Void)?
    var onMetrics: ((String) -> Void)?
    var onDiscovery: ((String) -> Void)?
    private let selectionRing = SKShapeNode(ellipseOf: CGSize(width: 30, height: 12))
    private let destinationRing = SKShapeNode(ellipseOf: CGSize(width: 25, height: 10))
    private let reviewMode = ProcessInfo.processInfo.arguments.contains("-visualReview")
    private let demoMode = ProcessInfo.processInfo.arguments.contains("-visualDemo")

    func prepare(_ prepared: PreparedMeadow, progress: @escaping (Double) -> Void, completion: @escaping () -> Void) {
        let staged = LivingWorld(definition: prepared.definition, roadMask: prepared.roadMask,
            props: prepared.props, textures: prepared.textures, effects: prepared.effects,
            deferProps: true, renderTerrain: prepared.renderer == nil)
        staged.populate(prepared.props, progress: progress) { [weak self] in
            self?.installWorld(staged, heroes: prepared.heroes)
            completion()
        }
    }

    func refreshDiagnostics() { publishDiagnostics() }

    private func installWorld(_ prepared: LivingWorld, heroes: [[[SKTexture]]]? = nil) {
        world = prepared
        if let heroes { frames = heroes }
        addChild(world)
        simulation = JourneySimulation(network: world.network)
        buildMarkers(); buildActors(); reset()
    }

    override func didMove(to view: SKView) {
        backgroundColor = SKColor(red: 0.31, green: 0.38, blue: 0.15, alpha: 1)
        if world == nil { installWorld(LivingWorld(definition: .load())) }
        layoutWorld()
        onWorldReady?(world)
        if ProcessInfo.processInfo.arguments.contains("-alignmentReview") {
            world.children.forEach { $0.isHidden = true }
            for point in [CGPoint(x: 540, y: 300), CGPoint(x: 740, y: 300), CGPoint(x: 640, y: 440)] {
                let marker = SKShapeNode(circleOfRadius: 3)
                marker.fillColor = .red; marker.strokeColor = .clear
                marker.position = LivingWorld.position(point); marker.zPosition = 100000
                world.addChild(marker)
            }
        }
        if demoMode { togglePlayback() }
    }

    private func buildMarkers() {
        let start = SKShapeNode(circleOfRadius: 10)
        start.position = LivingWorld.position(CGPoint(x: 285, y: 442))
        start.fillColor = SKColor(red: 0.96, green: 0.85, blue: 0.52, alpha: 1)
        start.strokeColor = SKColor(red: 0.40, green: 0.24, blue: 0.11, alpha: 1)
        start.lineWidth = 2.5
        start.zPosition = 65
        world.addChild(start)
        for (index, discovery) in world.definition.discoveries.enumerated() {
            let root = SKNode()
            root.position = LivingWorld.position(CGPoint(x: discovery.x + 28, y: discovery.y - 40))
            root.zPosition = 22500
            root.name = "discovery-\(index)"
            let diamond = SKShapeNode(circleOfRadius: 13)
            diamond.fillColor = SKColor(red: 0.25, green: 0.27, blue: 0.23, alpha: 0.9)
            diamond.strokeColor = SKColor(red: 0.87, green: 0.73, blue: 0.46, alpha: 1)
            diamond.lineWidth = 1.5
            diamond.name = root.name
            root.addChild(diamond)
            let label = SKLabelNode(fontNamed: "Georgia-Bold")
            label.text = "?"
            label.fontSize = 20
            label.fontColor = SKColor(red: 1, green: 0.95, blue: 0.81, alpha: 1)
            label.verticalAlignmentMode = .center
            label.name = root.name
            root.addChild(label)
            world.addChild(root)
            discoveryNodes.append(root)
            let footprint = SKShapeNode(ellipseOf: CGSize(width: 18, height: 8))
            footprint.position = LivingWorld.position(CGPoint(x: discovery.x, y: discovery.y))
            footprint.fillColor = .clear
            footprint.strokeColor = SKColor(red: 0.87, green: 0.73, blue: 0.46, alpha: 0.55)
            footprint.lineWidth = 1
            footprint.zPosition = 65
            world.addChild(footprint)
        }
        selectionRing.fillColor = .clear
        selectionRing.strokeColor = SKColor(red: 1, green: 0.89, blue: 0.56, alpha: 0.9)
        selectionRing.lineWidth = 1.5
        selectionRing.zPosition = 66
        selectionRing.isHidden = true
        world.addChild(selectionRing)
        destinationRing.strokeColor = selectionRing.strokeColor
        destinationRing.fillColor = .clear
        destinationRing.lineWidth = 2
        destinationRing.zPosition = 67
        destinationRing.isHidden = true
        world.addChild(destinationRing)
    }

    private func buildActors() {
        for index in 0..<3 {
            if frames.count <= index { frames.append(HeroFrames.load(index + 1)) }
            let directions = frames[index]
            let root = SKNode()
            root.name = "hero-\(index)"
            let sprite = SKSpriteNode(texture: directions[0][0], size: CGSize(width: 64, height: 64))
            sprite.anchorPoint = CGPoint(x: 0.5, y: 0.125)
            sprite.name = root.name
            sprite.zPosition = 1
            root.addChild(sprite)
            world.addChild(root)
            actorRoots.append(root)
            actors.append(sprite)
            let plate = SKShapeNode(rectOf: CGSize(width: 23, height: 14), cornerRadius: 3)
            plate.fillColor = .init(red: 0.18, green: 0.23, blue: 0.25, alpha: 0.9)
            plate.strokeColor = SKColor(red: 0.78, green: 0.70, blue: 0.46, alpha: 0.25)
            plate.lineWidth = 0.6
            plate.name = root.name
            let label = SKLabelNode(fontNamed: "HelveticaNeue-Medium")
            label.text = "P\(index + 1)"
            label.fontSize = 10
            label.verticalAlignmentMode = .center
            label.fontColor = .white
            label.name = root.name
            plate.addChild(label)
            plate.zPosition = 23000
            world.addChild(plate)
            actorLabels.append(plate)
        }
    }

    override func didChangeSize(_ oldSize: CGSize) { layoutWorld() }

    private func layoutWorld() {
        guard world != nil, size.width > 0, size.height > 0 else { return }
        // Preserve the entire reference composition; independent terrain extends beyond it.
        baseScale = min(size.width / 1280, size.height / 720)
        let scale = baseScale * zoom
        let halfWidth = size.width / scale / 2
        let halfHeight = size.height / scale / 2
        let bounds = LivingWorld.bounds
        func clamp(_ value: CGFloat, low: CGFloat, high: CGFloat, fallback: CGFloat) -> CGFloat {
            low <= high ? min(high, max(low, value)) : fallback
        }
        cameraCenter.x = clamp(cameraCenter.x, low: bounds.minX + halfWidth,
                               high: bounds.maxX - halfWidth, fallback: bounds.midX)
        cameraCenter.y = clamp(cameraCenter.y, low: bounds.minY + halfHeight,
                               high: bounds.maxY - halfHeight, fallback: bounds.midY)
        world.setScale(scale)
        world.position = CGPoint(x: size.width / 2 - cameraCenter.x * scale,
                                 y: size.height / 2 + cameraCenter.y * scale)
    }

    func setZoom(_ value: CGFloat, anchorInView: CGPoint? = nil) {
        guard world != nil else { return }
        let anchor = anchorInView.map { CGPoint(x: $0.x, y: size.height - $0.y) }
            ?? CGPoint(x: size.width / 2, y: size.height / 2)
        let previous = world.convert(anchor, from: self)
        zoom = min(1.8, max(1, value))
        let scale = baseScale * zoom
        cameraCenter = CGPoint(x: previous.x - (anchor.x - size.width / 2) / scale,
                               y: -previous.y + (anchor.y - size.height / 2) / scale)
        layoutWorld()
        publishDiagnostics()
    }

    func panBy(_ translation: CGPoint) {
        guard world != nil else { return }
        let scale = baseScale * zoom
        cameraCenter.x -= translation.x / scale
        cameraCenter.y -= translation.y / scale
        layoutWorld()
        publishDiagnostics()
    }

    func togglePlayback() {
        simulation.togglePlayback()
        onPlaybackChanged?(simulation.isPlaying)
        publishDiagnostics()
    }

    func reset() {
        guard world != nil else { return }
        simulation.reset()
        pendingDiscovery = nil
        discovered.removeAll()
        for node in discoveryNodes {
            node.alpha = 1
            node.children.compactMap { $0 as? SKLabelNode }.first?.text = "?"
            node.children.compactMap { $0 as? SKShapeNode }.first?.fillColor = .init(red: 0.25, green: 0.27, blue: 0.23, alpha: 0.9)
        }
        selectionRing.isHidden = true
        destinationRing.isHidden = true
        walks = [WalkCycle(), WalkCycle(), WalkCycle()]
        cameraCenter = CGPoint(x: 640, y: 360)
        zoom = 1
        layoutWorld()
        updateActors(before: nil)
        onPlaybackChanged?(false)
        onSelectionChanged?("P1")
        publishDiagnostics()
    }

    override func update(_ currentTime: TimeInterval) {
        guard world != nil else { return }
        defer { lastTime = currentTime }
        guard lastTime > 0 else {
            frameWindowStart = currentTime
            return
        }
        let rawDelta = max(0, currentTime - lastTime)
        let delta = min(rawDelta, 0.1)
        environmentTime += delta
        world.update(time: environmentTime)
        let previous = actors.indices.map { simulation.point(for: $0) }
        let wasPlaying = simulation.isPlaying
        simulation.advance(delta)
        updateActors(before: previous)
        if wasPlaying != simulation.isPlaying { onPlaybackChanged?(simulation.isPlaying) }
        if let discovery = pendingDiscovery, simulation.travelers[simulation.selected].isWaiting {
            completeDiscovery(discovery)
            pendingDiscovery = nil
        }
        if !simulation.isPlaying && simulation.mode == .destination { destinationRing.isHidden = true }
        if demoMode { updateDemo() }
        frameCounter += 1
        if currentTime - frameWindowStart >= 1 {
            measuredFPS = Double(frameCounter) / (currentTime - frameWindowStart)
            frameCounter = 0
            frameWindowStart = currentTime
            publishDiagnostics(record: true)
        }
    }

    override func didFinishUpdate() {
        guard world != nil, simulation != nil, let view else { return }
        let heroes = actors.indices.map { MeadowHeroCaster(index: $0, foot: simulation.point(for: $0), facing: walks[$0].facing, frame: walks[$0].frame, phase: walks[$0].phase) }
        onRenderGround?(world, MeadowViewport(world: world, scene: self, view: view), environmentTime, heroes)
        initialFrames += 1
        if initialFrames == 1 { DispatchQueue.main.async { [weak self] in self?.onForegroundReady?() } }
    }

    private func updateActors(before: [CGPoint]?) {
        for index in actors.indices {
            let point = simulation.point(for: index)
            if let before {
                walks[index].advance(from: before[index], to: point)
            }
            let walk = walks[index]
            let gait = SIMD2(Float(walk.facing), Float(walk.frame))
            let texture = frames[index][walk.facing][walk.frame]
            actors[index].texture = texture
            actors[index].xScale = HeroFrames.isMirrored(walk.facing) ? -1 : 1
            let pose = HeroPose(heroIndex: index, facing: walk.facing, frame: walk.frame, phase: walk.phase)
            // An idle/profile pose is the identity: avoid rebuilding GPU warp
            // geometry every frame for three stationary actors.
            if pose.legReachPoints > 0 { actors[index].warpGeometry = pose.warpGeometry() }
            else if actors[index].warpGeometry != nil { actors[index].warpGeometry = nil }
            actors[index].position = pose.bodyOffset(size: actors[index].size)
            actorRoots[index].position = LivingWorld.position(point)
            actorRoots[index].zPosition = 10000 + point.y
            actorLabels[index].position = actorRoots[index].position + CGPoint(x: 0, y: -13)
            world.effects.apply(world.effects.vegetation, to: actors[index],
                                origin: CGPoint(x: point.x, y: point.y - 24), extent: actors[index].size, gait: gait)
        }
        selectionRing.position = actorRoots[simulation.selected].position
    }

    private func order(to point: CGPoint, discovery: Int? = nil) {
        simulation.orderSelected(to: point)
        pendingDiscovery = discovery
        selectionRing.isHidden = false
        let goal = simulation.routes[simulation.selected].points.last!
        destinationRing.position = LivingWorld.position(goal)
        destinationRing.isHidden = false
        onPlaybackChanged?(simulation.isPlaying)
        publishDiagnostics()
    }

    private func completeDiscovery(_ index: Int) {
        guard !discovered.contains(index) else { return }
        discovered.insert(index)
        let marker = discoveryNodes[index]
        marker.children.compactMap { $0 as? SKLabelNode }.first?.text = "✓"
        marker.children.compactMap { $0 as? SKShapeNode }.first?.fillColor = .init(red: 0.62, green: 0.45, blue: 0.19, alpha: 0.95)
        for particle in 0..<24 {
            let dot = SKShapeNode(circleOfRadius: 1.4)
            dot.fillColor = SKColor(red: 1, green: 0.9, blue: 0.6, alpha: 1)
            dot.strokeColor = .clear
            dot.position = marker.position
            dot.zPosition = 23100
            world.addChild(dot)
            let angle = CGFloat(particle) * .pi / 12
            dot.run(.sequence([.group([
                .moveBy(x: cos(angle) * 35, y: sin(angle) * 20 + 16, duration: 1.6),
                .fadeOut(withDuration: 1.6)
            ]), .removeFromParent()]))
        }
        onDiscovery?("发现 · " + world.definition.discoveries[index].title)
        publishDiagnostics()
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let touch = touches.first, world != nil else { return }
        let location = touch.location(in: world)
        if let index = actorRoots.indices.min(by: {
            hypot(actorRoots[$0].position.x - location.x, actorRoots[$0].position.y + 17 - location.y) <
            hypot(actorRoots[$1].position.x - location.x, actorRoots[$1].position.y + 17 - location.y)
        }), hypot(actorRoots[index].position.x - location.x, actorRoots[index].position.y + 17 - location.y) < 30 {
            simulation.selected = index
            selectionRing.isHidden = false
            selectionRing.position = actorRoots[index].position
            onSelectionChanged?("P\(index + 1)")
            publishDiagnostics()
            return
        }
        for index in discoveryNodes.indices where hypot(discoveryNodes[index].position.x - location.x,
                                                        discoveryNodes[index].position.y - location.y) < 25 {
            let item = world.definition.discoveries[index]
            order(to: CGPoint(x: item.x, y: item.y), discovery: index)
            return
        }
        let point = CGPoint(x: location.x, y: -location.y)
        let projection = world.network.project(point)
        if projection.error <= 24 { order(to: projection.point) }
    }

    private func updateDemo() {
        if environmentTime > 3, demoPhase == 0 {
            demoPhase = 1
            run(.customAction(withDuration: 1.4) { [weak self] _, elapsed in
                self?.setZoom(1 + CGFloat(elapsed) / 1.4 * 0.35)
            })
        }
        if environmentTime > 6, demoPhase == 1 {
            demoPhase = 2
            simulation.selected = 2
            let target = world.definition.discoveries[1]
            order(to: CGPoint(x: target.x, y: target.y), discovery: 1)
        }
        if environmentTime > 10, demoPhase == 2 {
            demoPhase = 3
            run(.customAction(withDuration: 1.5) { [weak self] _, elapsed in
                self?.setZoom(1.35 - CGFloat(elapsed) / 1.5 * 0.35)
            })
        }
    }

    private func residentMemoryMiB() -> Double {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<natural_t>.size)
        let result = withUnsafeMutablePointer(to: &info) { pointer in
            pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        return result == KERN_SUCCESS ? Double(info.resident_size) / (1024 * 1024) : 0
    }

    private func publishDiagnostics(record: Bool = false) {
        guard world != nil, simulation != nil, size.width > 0, size.height > 0 else { return }
        let heroTargets = actors.indices.map { index -> [String: Double] in
            let local = actorRoots[index].position + CGPoint(x: 0, y: 17)
            let point = world.convert(local, to: self)
            return ["x": Double(point.x / size.width), "y": Double(1 - point.y / size.height)]
        }
        let goal = simulation.routes[simulation.selected].points.last!
        let orderPoint = world.convert(LivingWorld.position(CGPoint(x: 713, y: 252)), to: self)
        let memory = residentMemoryMiB()
        let metrics: [String: Any] = [
            "fps": measuredFPS, "residentMemoryMiB": memory,
            "startup": startupMetrics,
            "textureBudgetMiB": world.definition.textureBudgetMiB,
            "independentProps": world.objectCount, "roads": world.network.edges.count,
            "projectedShadows": world.shadowCount + actors.count, "shadowRenderer": "image-alpha relief Metal depth map", "shadowReady": shadowReady, "shadowFrames": shadowFrames,
            "sunDirection": ["x": Double(world.effects.currentCast.dx), "y": Double(world.effects.currentCast.dy)],
            "environmentTime": environmentTime, "zoom": Double(zoom),
            "selected": simulation.selected, "isPlaying": simulation.isPlaying,
            "mode": simulation.mode == .patrol ? "patrol" : "destination",
            "goal": ["x": Double(goal.x), "y": Double(goal.y)],
            "heroTargets": heroTargets,
            "orderPoint": ["x": Double(orderPoint.x / size.width), "y": Double(1 - orderPoint.y / size.height)],
            "discoveries": discovered.count
        ]
        if let data = try? JSONSerialization.data(withJSONObject: metrics, options: [.sortedKeys]),
           let text = String(data: data, encoding: .utf8) { onDiagnostics?(text) }
        onMetrics?(String(format: "%.0f FPS  ·  %d 物件\n纹理 %.1f MiB  ·  内存 %.0f MiB",
                          measuredFPS, world.objectCount, world.definition.textureBudgetMiB, memory))
        if record && reviewMode {
            metricSamples.append(metrics)
            if metricSamples.count > 30 { metricSamples.removeFirst() }
            if let data = try? JSONSerialization.data(withJSONObject: metricSamples, options: [.sortedKeys]) {
                let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                try? data.write(to: directory.appendingPathComponent("RuntimeMetrics.json"), options: .atomic)
            }
        }
    }
}

private extension CGPoint {
    static func + (lhs: CGPoint, rhs: CGPoint) -> CGPoint { CGPoint(x: lhs.x + rhs.x, y: lhs.y + rhs.y) }
}
