import SpriteKit

/// Only launched by CI's -gaitReview argument; uses the production shaders,
/// textures and distance-to-pose mapping at a size suitable for visual checking.
final class GaitReviewScene: SKScene {
    private let effects = EnvironmentShaders()
    private var frames: [[[SKTexture]]] = []
    private var actors: [SKSpriteNode] = []
    private var shadows: [ProjectedShadow] = []
    private var feet: [CGPoint] = []
    private let heading = SKLabelNode(fontNamed: "HelveticaNeue-Medium")
    private var began: TimeInterval?

    override func didMove(to view: SKView) {
        guard actors.isEmpty else { return }
        let scale = min(size.width / 1280, size.height / 720)
        let ground = SKSpriteNode(texture: SKTexture(imageNamed: "MeadowGround"), size: size)
        ground.position = CGPoint(x: size.width / 2, y: size.height / 2)
        ground.shader = effects.ground
        addChild(ground)
        let road = SKShapeNode(rect: CGRect(x: -10, y: size.height * 0.36 - 14 * scale, width: size.width + 20, height: 35 * scale))
        road.fillColor = .white
        road.strokeColor = .clear
        road.fillTexture = SKTexture(imageNamed: "MeadowGround")
        road.fillShader = effects.soil
        road.attributeValues = ["a_origin": SKAttributeValue(vectorFloat2: SIMD2(640, 442)),
                                "a_extent": SKAttributeValue(vectorFloat2: SIMD2(1280, 35))]
        road.zPosition = 10
        addChild(road)
        for index in 0..<3 {
            let atlas = SKTexture(imageNamed: "Hero\(index + 1)Directions")
            let directions = (0..<4).map { row in
                (0..<4).map { column -> SKTexture in
                    let frame = SKTexture(rect: CGRect(x: CGFloat(column) / 4, y: CGFloat(3-row) / 4, width: 0.25, height: 0.25), in: atlas)
                    frame.filteringMode = .nearest
                    return frame
                }
            }
            frames.append(directions)
            let sprite = SKSpriteNode(texture: directions[0][0], size: CGSize(width: 192 * scale, height: 192 * scale))
            sprite.anchorPoint = CGPoint(x: 0.5, y: 0.125)
            let foot = CGPoint(x: size.width * CGFloat(index + 1) / 4, y: size.height * 0.36)
            feet.append(foot)
            sprite.position = foot
            sprite.zPosition = 100
            addChild(sprite)
            actors.append(sprite)
            let shadow = ProjectedShadow(texture: directions[0][0], body: sprite.size, anchorY: sprite.anchorPoint.y,
                                         ratio: 0.82, softness: 2.0, opacity: 0.52, shader: effects.shadow)
            addChild(shadow)
            shadows.append(shadow)
            let contact = SKSpriteNode(color: .white, size: CGSize(width: 44 * scale, height: 13 * scale))
            contact.position = foot
            contact.shader = effects.contact
            contact.zPosition = 45
            addChild(contact)
            let label = SKLabelNode(fontNamed: "HelveticaNeue-Medium")
            label.text = "P\(index + 1)"
            label.position = CGPoint(x: foot.x, y: foot.y - 58 * scale)
            label.fontSize = 22 * scale
            label.fontColor = SKColor(red: 1, green: 0.96, blue: 0.80, alpha: 1)
            label.zPosition = 200
            addChild(label)
        }
        heading.position = CGPoint(x: size.width / 2, y: size.height * 0.78)
        heading.fontSize = 30 * scale
        heading.fontColor = SKColor(red: 1, green: 0.96, blue: 0.80, alpha: 1)
        heading.zPosition = 200
        addChild(heading)
    }

    override func update(_ currentTime: TimeInterval) {
        if began == nil { began = currentTime }
        let elapsed = currentTime - (began ?? currentTime)
        effects.update(time: elapsed)
        let direction = Int(elapsed / 3) % 4
        let frame = WalkCycle.frame(at: CGFloat(elapsed) * 42)
        heading.text = "四方向步态 · " + ["正面", "向左", "背面", "向右"][direction]
        for index in actors.indices {
            let texture = frames[index][direction][frame]
            actors[index].texture = texture
            let gait = SIMD2(Float(direction), Float(frame))
            effects.apply(effects.vegetation, to: actors[index], origin: CGPoint(x: feet[index].x, y: -feet[index].y - 50),
                          extent: actors[index].size, gait: gait)
            shadows[index].update(foot: feet[index], texture: texture, gait: gait)
        }
    }
}
