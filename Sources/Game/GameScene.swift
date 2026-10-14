import SpriteKit

final class GameScene: SKScene {
    private let world = SKNode()
    private let trail = Trail.meadow
    private var heroes: [SKNode] = []
    private var sprites: [SKSpriteNode] = []
    private var frames: [[SKTexture]] = []
    private var travelers: [Traveler] = []
    private var selection = 0
    private var lastTime: TimeInterval = 0
    private var animationTime: TimeInterval = 0
    private var baseScale: CGFloat = 1
    private(set) var zoom: CGFloat = 1
    private var pan = CGPoint.zero
    private(set) var isRunning = false
    var onPlaybackChanged: ((Bool) -> Void)?
    var onSelectionChanged: ((String) -> Void)?
    private let selectionRing = SKShapeNode(ellipseOf: CGSize(width: 32, height: 13))
    private let destinationRing = SKShapeNode(ellipseOf: CGSize(width: 25, height: 10))

    override func didMove(to view: SKView) {
        guard world.parent == nil else { return }
        backgroundColor = SKColor(red: 0.25, green: 0.32, blue: 0.15, alpha: 1)
        addChild(world)
        let background = SKSpriteNode(texture: SKTexture(imageNamed: "MapBackground"))
        background.anchorPoint = .zero
        background.size = CGSize(width: 1280, height: 720)
        background.zPosition = -1000
        world.addChild(background)
        buildTrailMarkers()
        buildHeroes()
        layoutWorld()
        reset()
    }

    private func position(_ point: CGPoint) -> CGPoint {
        CGPoint(x: point.x, y: 720 - point.y)
    }

    private func buildTrailMarkers() {
        let start = SKShapeNode(circleOfRadius: 11)
        start.position = position(CGPoint(x: 285, y: 442))
        start.fillColor = SKColor(red: 0.96, green: 0.85, blue: 0.52, alpha: 1)
        start.strokeColor = SKColor(red: 0.40, green: 0.24, blue: 0.11, alpha: 1)
        start.lineWidth = 3
        start.zPosition = 1
        world.addChild(start)
        for location in [CGPoint(x: 982, y: 430), CGPoint(x: 735, y: 578)] {
            let marker = SKShapeNode(circleOfRadius: 17)
            marker.position = position(location)
            marker.fillColor = SKColor(red: 0.22, green: 0.25, blue: 0.24, alpha: 0.92)
            marker.strokeColor = SKColor(red: 0.86, green: 0.73, blue: 0.49, alpha: 1)
            marker.lineWidth = 2
            marker.name = "discovery"
            marker.zPosition = 15
            let label = SKLabelNode(fontNamed: "Georgia-Bold")
            label.text = "?"
            label.fontSize = 21
            label.fontColor = .init(white: 0.96, alpha: 1)
            label.verticalAlignmentMode = .center
            label.name = "discovery"
            marker.addChild(label)
            world.addChild(marker)
        }
        selectionRing.fillColor = .clear
        selectionRing.strokeColor = SKColor(red: 1, green: 0.87, blue: 0.55, alpha: 0.85)
        selectionRing.lineWidth = 1.5
        selectionRing.zPosition = 2
        selectionRing.isHidden = true
        world.addChild(selectionRing)
        destinationRing.strokeColor = SKColor(red: 1, green: 0.87, blue: 0.55, alpha: 1)
        destinationRing.fillColor = .clear
        destinationRing.lineWidth = 2
        destinationRing.zPosition = 3
        destinationRing.isHidden = true
        world.addChild(destinationRing)
    }

    private func buildHeroes() {
        let sheet = SKTexture(imageNamed: "Heroes")
        sheet.filteringMode = .nearest
        for index in 0..<3 {
            let row = (0..<4).map { column -> SKTexture in
                let texture = SKTexture(rect: CGRect(x: CGFloat(column) / 4,
                                                    y: CGFloat(2 - index) / 3,
                                                    width: 0.25, height: 1.0 / 3.0), in: sheet)
                texture.filteringMode = .nearest
                return texture
            }
            frames.append(row)
            let hero = SKNode()
            hero.name = "hero-\(index)"
            let shadow = SKShapeNode(ellipseOf: CGSize(width: 22, height: 7))
            shadow.fillColor = .init(white: 0.10, alpha: 0.3)
            shadow.strokeColor = .clear
            shadow.position.y = 1
            hero.addChild(shadow)
            let sprite = SKSpriteNode(texture: row[0], size: CGSize(width: 64, height: 64))
            sprite.anchorPoint = CGPoint(x: 0.5, y: 0.125)
            sprite.position.y = 1
            sprite.name = hero.name
            hero.addChild(sprite)
            let plate = SKShapeNode(rectOf: CGSize(width: 26, height: 17), cornerRadius: 3)
            plate.position.y = -14
            plate.fillColor = .init(red: 0.18, green: 0.23, blue: 0.25, alpha: 0.9)
            plate.strokeColor = .clear
            plate.name = hero.name
            let label = SKLabelNode(fontNamed: "HelveticaNeue-Medium")
            label.text = "P\(index + 1)"
            label.fontSize = 12
            label.verticalAlignmentMode = .center
            label.fontColor = .white
            label.name = hero.name
            plate.addChild(label)
            hero.addChild(plate)
            world.addChild(hero)
            heroes.append(hero)
            sprites.append(sprite)
        }
    }

    override func didChangeSize(_ oldSize: CGSize) { layoutWorld() }

    private func layoutWorld() {
        guard size.width > 0, size.height > 0 else { return }
        baseScale = max(size.width / 1280, size.height / 720)
        let scale = baseScale * zoom
        world.setScale(scale)
        let horizontalLimit = max(0, (1280 * scale - size.width) / 2)
        let verticalLimit = max(0, (720 * scale - size.height) / 2)
        pan.x = min(horizontalLimit, max(-horizontalLimit, pan.x))
        pan.y = min(verticalLimit, max(-verticalLimit, pan.y))
        world.position = CGPoint(x: (size.width - 1280 * scale) / 2 + pan.x,
                                 y: (size.height - 720 * scale) / 2 + pan.y)
    }

    func setZoom(_ value: CGFloat) {
        zoom = min(1.7, max(1, value))
        layoutWorld()
    }

    func panBy(_ translation: CGPoint) {
        pan.x += translation.x
        pan.y -= translation.y
        layoutWorld()
    }

    func togglePlayback() {
        isRunning.toggle()
        if isRunning {
            for index in travelers.indices {
                travelers[index].isWaiting = false
                travelers[index].destination = nil
            }
            destinationRing.isHidden = true
        }
        onPlaybackChanged?(isRunning)
    }

    func reset() {
        travelers = [
            Traveler(distance: trail.distance(nearestTo: CGPoint(x: 440, y: 444)), direction: 1, speed: 42),
            Traveler(distance: trail.length, direction: -1, speed: 38),
            Traveler(distance: trail.distance(nearestTo: CGPoint(x: 560, y: 441)), direction: 1, speed: 45)
        ]
        isRunning = false
        selection = 0
        selectionRing.isHidden = true
        destinationRing.isHidden = true
        animationTime = 0
        lastTime = 0
        zoom = 1
        pan = .zero
        layoutWorld()
        updateHeroPositions()
        for index in sprites.indices {
            sprites[index].texture = frames[index][0]
            sprites[index].position.y = 1
        }
        onPlaybackChanged?(false)
        onSelectionChanged?("P1")
    }

    override func update(_ currentTime: TimeInterval) {
        defer { lastTime = currentTime }
        guard lastTime > 0, isRunning else { return }
        // Clamp after foregrounding, so a suspended app never jumps forward.
        let delta = min(max(currentTime - lastTime, 0), 1.0 / 15.0)
        animationTime += delta
        for index in travelers.indices {
            let before = travelers[index].distance
            travelers[index].advance(by: delta, on: trail)
            if abs(travelers[index].distance - before) > 0.001 {
                sprites[index].texture = frames[index][Int(animationTime * 9) % 4]
                sprites[index].position.y = 1 + sin(animationTime * 18) * 0.65
            } else {
                sprites[index].texture = frames[index][0]
                sprites[index].position.y = 1
            }
        }
        updateHeroPositions()
        if travelers.allSatisfy({ $0.isWaiting }) {
            isRunning = false
            destinationRing.isHidden = true
            onPlaybackChanged?(false)
        }
    }

    private func updateHeroPositions() {
        for index in heroes.indices {
            let point = trail.point(at: travelers[index].distance)
            heroes[index].position = position(point)
            // Characters farther down the map render over those farther up.
            heroes[index].zPosition = point.y
            sprites[index].xScale = travelers[index].direction >= 0 ? 1 : -1
        }
        if heroes.indices.contains(selection) {
            selectionRing.position = heroes[selection].position
        }
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let touch = touches.first else { return }
        let location = touch.location(in: world)
        if let index = heroes.indices.min(by: {
            hypot(heroes[$0].position.x - location.x, heroes[$0].position.y + 17 - location.y) <
            hypot(heroes[$1].position.x - location.x, heroes[$1].position.y + 17 - location.y)
        }), hypot(heroes[index].position.x - location.x, heroes[index].position.y + 17 - location.y) < 34 {
            selection = index
            selectionRing.isHidden = false
            selectionRing.position = heroes[index].position
            onSelectionChanged?("P\(index + 1)")
            return
        }
        if world.nodes(at: location).contains(where: { $0.name == "discovery" }) {
            for _ in 0..<18 {
                let sparkle = SKShapeNode(circleOfRadius: CGFloat.random(in: 1...2))
                sparkle.fillColor = SKColor(red: 1, green: 0.88, blue: 0.54, alpha: 1)
                sparkle.strokeColor = .clear
                sparkle.position = location
                sparkle.zPosition = 900
                world.addChild(sparkle)
                sparkle.run(.sequence([
                    .group([.moveBy(x: CGFloat.random(in: -30...30), y: CGFloat.random(in: 8...40), duration: 1.2),
                            .fadeOut(withDuration: 1.2)]), .removeFromParent()
                ]))
            }
            return
        }
        let referencePoint = CGPoint(x: location.x, y: 720 - location.y)
        let distance = trail.distance(nearestTo: referencePoint)
        let projected = trail.point(at: distance)
        guard hypot(projected.x - referencePoint.x, projected.y - referencePoint.y) < 30 else { return }
        for index in travelers.indices { travelers[index].isWaiting = index != selection }
        travelers[selection].destination = distance
        travelers[selection].isWaiting = false
        selectionRing.isHidden = false
        destinationRing.position = position(projected)
        destinationRing.isHidden = false
        isRunning = true
        onPlaybackChanged?(true)
    }
}
