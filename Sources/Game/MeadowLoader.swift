import MetalKit
import SpriteKit

struct PreparedMeadow {
    let definition: SceneDefinition
    let roadMask: CGImage
    let props: [SceneDefinition.Prop]
    let textures: [String: SKTexture]
    let heroes: [[[SKTexture]]]
    let effects: EnvironmentShaders
    let renderer: MeadowShadowRenderer?
}

enum MeadowLoader {
    private static let queue = DispatchQueue(label: "meadow.loading", qos: .userInitiated)

    static func load(device: MTLDevice?, progress: @escaping (Float, String) -> Void,
                     completion: @escaping (Result<PreparedMeadow, Error>) -> Void) {
        func report(_ value: Double, _ text: String) {
            DispatchQueue.main.async { progress(Float(value), text) }
        }
        queue.async {
            do {
                report(0.02, "读取地图")
                let definition = SceneDefinition.load()
                let network = TrailNetwork(roads: definition.roads)
                let mask = MeadowRoadMask.make(network: network, bounds: LivingWorld.bounds) {
                    report(0.05 + $0 * 0.22, "准备道路")
                }
                let props = definition.props + LivingWorld.meadowDetails(definition: definition, network: network)
                    + LivingWorld.roadsideGrass(network: network)
                var images: [String: CGImage] = [:]
                var textures: [String: SKTexture] = [:]
                let names = Set(props.map(\.asset) + ["MeadowGround", "Banner"]
                    + (1...3).flatMap { ["Hero\($0)Directions", "Hero\($0)Diagonals"] }).sorted()
                for (index, name) in names.enumerated() {
                    guard let image = UIImage(named: name)?.cgImage else { throw ShadowLabError.setup("素材缺失：\(name)") }
                    images[name] = image
                    if !name.hasPrefix("Hero") {
                        let texture = SKTexture(cgImage: image); texture.filteringMode = .linear
                        textures[name] = texture
                    }
                    report(0.28 + Double(index + 1) / Double(names.count) * 0.13, "准备场景素材")
                }
                var heroes: [[[SKTexture]]] = []
                for index in 1...3 {
                    heroes.append(HeroFrames.load(index))
                    report(0.41 + Double(index) * 0.03, "准备旅人")
                }
                let renderer: MeadowShadowRenderer?
                if let device {
                    renderer = try MeadowShadowRenderer(device: device, props: props, roadMask: mask, images: images) {
                        report(0.50 + $0 * 0.33, "准备实时投影")
                    }
                } else { renderer = nil }
                let effects = EnvironmentShaders()
                let prepared = PreparedMeadow(definition: definition, roadMask: mask, props: props,
                                             textures: textures, heroes: heroes, effects: effects, renderer: renderer)
                report(0.84, "上传场景纹理")
                SKTexture.preload(Array(textures.values) + heroes.flatMap { $0.flatMap { $0 } }) {
                    DispatchQueue.main.async { completion(.success(prepared)) }
                }
            } catch { DispatchQueue.main.async { completion(.failure(error)) } }
        }
    }

}

/// Warm the actual SKView renderer one pipeline at a time, with complete view
/// frames between stages. Match textured/untextured and additive variants;
/// offscreen textured sprites do not warm every real foreground pipeline.
final class MeadowWarmupScene: SKScene {
    private let prepared: PreparedMeadow
    private let progress: (Double) -> Void
    private var completion: (([String: Double]) -> Void)?
    private var stage = 0
    private var frames = 0
    private var advancing = false
    private var stageBegan: TimeInterval = 0
    private var timings: [String: Double] = [:]

    init(size: CGSize, prepared: PreparedMeadow, progress: @escaping (Double) -> Void,
         completion: @escaping ([String: Double]) -> Void) {
        self.prepared = prepared; self.progress = progress; self.completion = completion
        super.init(size: size)
        scaleMode = .resizeFill; backgroundColor = .clear
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func didMove(to view: SKView) { advance() }

    override func didFinishUpdate() {
        guard !advancing, completion != nil else { return }
        frames += 1
        if frames >= 3 {
            advancing = true
            DispatchQueue.main.async { [weak self] in
                guard let self else { return }
                guard !self.isPaused else { self.advancing = false; self.frames = 0; return }
                self.timings["warmStage\(self.stage - 1)"] = ProcessInfo.processInfo.systemUptime - self.stageBegan
                self.advance()
            }
        }
    }

    private func advance() {
        removeAllChildren()
        progress(Double(stage) / 10)
        guard stage < 10 else {
            let finished = completion; completion = nil
            finished?(timings)
            return
        }
        stageBegan = ProcessInfo.processInfo.systemUptime
        let node: SKNode
        if stage < 6 {
            let effects = prepared.effects
            let shaders = [effects.vegetation, effects.meadowPlants, effects.contact,
                           effects.backMist, effects.sunlight, effects.frontMist]
            let sprite: SKSpriteNode
            if stage < 2 {
                sprite = SKSpriteNode(texture: prepared.textures[stage == 0 ? "OakA" : "Flowers"],
                                      size: CGSize(width: 64, height: 64))
            } else { sprite = SKSpriteNode(color: .white, size: CGSize(width: 64, height: 64)) }
            if stage == 4 { sprite.blendMode = .add }
            effects.apply(shaders[stage], to: sprite, origin: .zero, extent: sprite.size)
            node = sprite
        } else if stage < 8 {
            let label = SKLabelNode(fontNamed: stage == 6 ? "Georgia-Bold" : "HelveticaNeue-Medium")
            label.text = "? ✓ P1 P2 P3"; label.fontSize = stage == 6 ? 20 : 10
            node = label
        } else if stage == 8 {
            let shape = SKShapeNode(ellipseOf: CGSize(width: 24, height: 12))
            shape.fillColor = .white; shape.strokeColor = .gray
            node = shape
        } else {
            let emitter = SKEmitterNode()
            emitter.particleTexture = prepared.textures["Flowers"]
            emitter.particleBirthRate = 4; emitter.particleLifetime = 2
            emitter.particleScale = 0.01
            emitter.particleBlendMode = .add
            emitter.advanceSimulationTime(1)
            node = emitter
        }
        node.position = CGPoint(x: size.width / 2, y: size.height / 2)
        addChild(node)
        stage += 1; frames = 0; advancing = false
    }
}
