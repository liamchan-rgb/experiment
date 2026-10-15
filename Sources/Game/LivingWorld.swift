import SpriteKit

final class LivingWorld: SKNode {
    static let bounds = CGRect(x: -160, y: -220, width: 1600, height: 1160)
    static let towerBannerRoofAnchorY: CGFloat = 0.91
    let definition: SceneDefinition
    let network: TrailNetwork
    let effects = EnvironmentShaders()
    private var textures: [String: SKTexture] = [:]
    private var propShadows: [(node: ProjectedShadow, foot: CGPoint)] = []
    private(set) var shadowCount = 0
    private(set) var objectCount = 0

    init(definition: SceneDefinition) {
        self.definition = definition
        network = TrailNetwork(roads: definition.roads)
        super.init()
        buildGround()
        buildRoads()
        for prop in definition.props { addProp(prop) }
        buildMeadowDetails()
        buildRoadsideGrass()
        addOverlay(shader: effects.backMist, depth: 95)
        addOverlay(shader: effects.sunlight, depth: 20000, additive: true)
        addOverlay(shader: effects.frontMist, depth: 21000)
        buildMotes()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func texture(_ name: String) -> SKTexture {
        if let texture = textures[name] { return texture }
        let texture = SKTexture(imageNamed: name)
        texture.filteringMode = .linear
        textures[name] = texture
        return texture
    }

    static func position(_ point: CGPoint) -> CGPoint { CGPoint(x: point.x, y: -point.y) }

    private func buildGround() {
        let node = SKSpriteNode(texture: texture("MeadowGround"), size: Self.bounds.size)
        node.position = Self.position(CGPoint(x: Self.bounds.midX, y: Self.bounds.midY))
        node.shader = effects.ground
        node.zPosition = 0
        addChild(node)
    }

    private func roadPolygon(_ trail: Trail, width: CGFloat) -> CGPath {
        var left: [CGPoint] = [], right: [CGPoint] = []
        for index in trail.points.indices {
            let before = trail.points[max(0, index - 1)]
            let after = trail.points[min(trail.points.count - 1, index + 1)]
            let dx = after.x - before.x
            let dy = after.y - before.y
            let length = max(0.1, (dx * dx + dy * dy).squareRoot())
            let half = width / 2 * (1 + sin(CGFloat(index) * 0.85) * 0.10)
            let offset = CGPoint(x: -dy / length * half, y: dx / length * half)
            let p = trail.points[index]
            left.append(Self.position(CGPoint(x: p.x + offset.x, y: p.y + offset.y)))
            right.append(Self.position(CGPoint(x: p.x - offset.x, y: p.y - offset.y)))
        }
        let path = CGMutablePath()
        path.addLines(between: left + Array(right.reversed()))
        path.closeSubpath()
        return path
    }

    private func buildRoads() {
        for edge in network.edges {
            let border = SKShapeNode(path: roadPolygon(edge.trail, width: edge.width + 9))
            border.fillColor = SKColor(red: 0.44, green: 0.38, blue: 0.18, alpha: 0.20)
            border.strokeColor = .clear
            border.zPosition = 10
            addChild(border)
            let road = SKShapeNode(path: roadPolygon(edge.trail, width: edge.width))
            road.fillColor = SKColor(red: 0.89, green: 0.72, blue: 0.44, alpha: 1)
            road.strokeColor = .clear
            road.fillTexture = texture("MeadowGround")
            road.fillShader = effects.soil
            let bounds = road.path!.boundingBoxOfPath
            road.attributeValues = [
                "a_origin": SKAttributeValue(vectorFloat2: SIMD2(Float(bounds.midX), Float(-bounds.midY))),
                "a_extent": SKAttributeValue(vectorFloat2: SIMD2(Float(bounds.width), Float(bounds.height)))
            ]
            road.zPosition = 11
            addChild(road)
        }
        buildRoadDetails()
    }

    private func buildRoadDetails() {
        var random = MeadowRandom(seed: 9182)
        for edge in network.edges {
            var distance: CGFloat = 5
            while distance < edge.trail.length - 5 {
                let point = edge.trail.point(at: distance)
                let next = edge.trail.point(at: distance + 1)
                let dx = next.x - point.x, dy = next.y - point.y
                let length = max(0.1, hypot(dx, dy))
                let side = random.value(-edge.width * 0.40, edge.width * 0.40)
                let width = random.value(1.2, 3.5)
                let stone = SKShapeNode(ellipseOf: CGSize(width: width, height: width * 0.65))
                stone.position = Self.position(CGPoint(x: point.x - dy / length * side, y: point.y + dx / length * side))
                let tone = random.value(0.52, 0.78)
                stone.fillColor = SKColor(red: tone, green: tone * 0.94, blue: tone * 0.78, alpha: 0.85)
                stone.strokeColor = SKColor(red: 0.28, green: 0.24, blue: 0.15, alpha: 0.25)
                stone.lineWidth = 0.4
                stone.zPosition = 12
                addChild(stone)
                distance += random.value(7, 17)
            }
        }
    }

    func makeContact(foot: CGPoint, width: CGFloat, depth: CGFloat) -> SKSpriteNode {
        let node = SKSpriteNode(color: .white, size: CGSize(width: width, height: depth))
        node.position = foot
        node.shader = effects.contact
        node.zPosition = 45
        addChild(node)
        return node
    }

    private func addProp(_ prop: SceneDefinition.Prop) {
        let propTexture = texture(prop.asset)
        let height = prop.width * propTexture.size().height / propTexture.size().width
        let node = SKSpriteNode(texture: propTexture, size: CGSize(width: prop.width, height: height))
        node.name = prop.asset
        node.anchorPoint = CGPoint(x: 0.5, y: 0.02)
        node.position = Self.position(CGPoint(x: prop.x, y: prop.y))
        node.zPosition = 10000 + prop.y
        // Preserve upper-left painted highlights on solid objects.
        node.xScale = prop.mirror && prop.asset == "Flowers" ? -1 : 1
        let vegetationShader = prop.asset == "Flowers" || prop.asset == "Shrub" ? effects.meadowPlants : effects.vegetation
        effects.apply(vegetationShader, to: node,
                      origin: CGPoint(x: prop.x, y: prop.y - height * 0.48),
                      extent: CGSize(width: prop.width * node.xScale, height: height),
                      wind: prop.wind, phase: Float(prop.x * 0.03 + prop.y * 0.017))
        addChild(node)
        objectCount += 1
        if prop.asset != "Flowers" {
            let tree = ["OakA", "OakB", "Pines"].contains(prop.asset)
            let ratio: CGFloat = tree || prop.asset == "WatchTower" ? 0.90 : 0.53
            let shadow = ProjectedShadow(texture: propTexture, body: node.size, anchorY: node.anchorPoint.y,
                                         ratio: ratio, softness: tree ? 2.6 : 1.5, opacity: tree ? 0.48 : 0.53,
                                         foliage: tree, phase: Float(prop.x * 0.03 + prop.y * 0.017), wind: prop.wind, shader: effects.shadow)
            shadow.update(foot: node.position)
            addChild(shadow)
            propShadows.append((shadow, node.position))
            shadowCount += 1
            let contactWidth = prop.width * (tree ? 0.27 : 0.70)
            _ = makeContact(foot: node.position, width: contactWidth, depth: max(4, contactWidth * 0.23))
        }
        // CampTent already contains its stitched banner. The tower needs a
        // separate flag, anchored at the roof peak instead of the image top.
        if prop.asset == "WatchTower" {
            let bannerTexture = texture("Banner")
            let width = min(34, max(22, prop.width * 0.40))
            let banner = SKSpriteNode(texture: bannerTexture,
                                      size: CGSize(width: width, height: width * bannerTexture.size().height / bannerTexture.size().width))
            banner.name = "banner"
            banner.anchorPoint = CGPoint(x: 0.035, y: 0.04)
            banner.position = CGPoint(x: 0, y: height * Self.towerBannerRoofAnchorY)
            banner.zPosition = 1
            effects.apply(effects.vegetation, to: banner,
                          origin: CGPoint(x: prop.x + width * 0.465,
                                          y: prop.y - height * Self.towerBannerRoofAnchorY - banner.size.height * 0.46),
                          extent: banner.size, wind: 2, phase: Float(prop.x * 0.03))
            node.addChild(banner)
        }
    }

    private func buildMeadowDetails() {
        var random = MeadowRandom(seed: definition.seed)
        for index in 0..<110 {
            let point = CGPoint(x: random.value(Self.bounds.minX, Self.bounds.maxX),
                                y: random.value(Self.bounds.minY, Self.bounds.maxY))
            if network.project(point).error < 38 { continue }
            if CGRect(x: 215, y: 275, width: 360, height: 160).contains(point) { continue }
            if definition.props.contains(where: { hypot($0.x - point.x, $0.y - point.y) < 23 }) { continue }
            let name = index % 9 == 0 ? "Shrub" : "Flowers"
            let width = name == "Shrub" ? random.value(23, 34) : random.value(12, 23)
            addProp(SceneDefinition.Prop(asset: name, x: point.x, y: point.y, width: width,
                                         mirror: random.next() > 0.5, wind: 1.15))
        }
    }

    private func addOverlay(shader: SKShader, depth: CGFloat, additive: Bool = false) {
        let node = SKSpriteNode(color: .white, size: Self.bounds.size)
        node.position = Self.position(CGPoint(x: Self.bounds.midX, y: Self.bounds.midY))
        node.shader = shader
        node.zPosition = depth
        if additive { node.blendMode = .add }
        addChild(node)
    }

    private func buildRoadsideGrass() {
        var random = MeadowRandom(seed: 39281)
        for edge in network.edges {
            var distance: CGFloat = 12
            while distance < edge.trail.length - 12 {
                let point = edge.trail.point(at: distance)
                let ahead = edge.trail.point(at: distance + 1)
                let dx = ahead.x - point.x
                let dy = ahead.y - point.y
                let length = max(0.1, (dx * dx + dy * dy).squareRoot())
                let side: CGFloat = random.next() > 0.5 ? 1 : -1
                let offset = edge.width / 2 + random.value(0, 3)
                addProp(SceneDefinition.Prop(asset: "Flowers", x: point.x - dy / length * offset * side,
                                             y: point.y + dx / length * offset * side,
                                             width: random.value(7, 14), mirror: random.next() > 0.5, wind: 1.2))
                distance += random.value(10, 20)
            }
        }
    }

    private func buildMotes() {
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: 16, height: 16))
        let dot = renderer.image { context in
            UIColor.white.setFill()
            context.cgContext.fillEllipse(in: CGRect(x: 4, y: 4, width: 8, height: 8))
        }
        let emitter = SKEmitterNode()
        emitter.particleTexture = SKTexture(image: dot)
        emitter.particleBirthRate = 4
        emitter.particleLifetime = 16
        emitter.particleLifetimeRange = 5
        emitter.particlePositionRange = CGVector(dx: 1400, dy: 920)
        emitter.position = CGPoint(x: 620, y: -380)
        emitter.particleSpeed = 5
        emitter.particleSpeedRange = 4
        emitter.emissionAngle = 0.35
        emitter.emissionAngleRange = 0.6
        emitter.particleAlpha = 0.40
        emitter.particleAlphaRange = 0.15
        emitter.particleAlphaSpeed = -0.02
        emitter.particleScale = 0.20
        emitter.particleScaleRange = 0.10
        emitter.particleColor = SKColor(red: 1, green: 0.88, blue: 0.50, alpha: 1)
        emitter.particleColorBlendFactor = 1
        emitter.particleBlendMode = .add
        emitter.zPosition = 20500
        emitter.advanceSimulationTime(10)
        addChild(emitter)
    }

    func update(time: TimeInterval) {
        effects.update(time: time)
        for shadow in propShadows {
            shadow.node.update(foot: shadow.foot, sun: effects.currentCast)
        }
    }
}
