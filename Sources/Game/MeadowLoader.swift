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
                    queue.async {
                        do {
                            report(0.90, "预热光照与薄雾")
                            if let device { try warmEffects(device: device, textures: textures, effects: effects) }
                            report(0.96, "布置场景")
                            DispatchQueue.main.async { completion(.success(prepared)) }
                        } catch { DispatchQueue.main.async { completion(.failure(error)) } }
                    }
                }
            } catch { DispatchQueue.main.async { completion(.failure(error)) } }
        }
    }

    /// Compile and submit the actual SpriteKit effect sources while the loading
    /// screen remains on the main thread. This scene is owned only by this queue.
    /// UIKit font/shape preparation stays on the actual foreground scene: doing
    /// it inside this offscreen background renderer can stall cold startup.
    private static func warmEffects(device: MTLDevice, textures: [String: SKTexture], effects: EnvironmentShaders) throws {
        guard let queue = device.makeCommandQueue(), let command = queue.makeCommandBuffer() else {
            throw ShadowLabError.setup("光效预热初始化失败")
        }
        let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm, width: 64, height: 64, mipmapped: false)
        descriptor.storageMode = .private; descriptor.usage = [.renderTarget, .shaderRead]
        guard let texture = device.makeTexture(descriptor: descriptor) else { throw ShadowLabError.setup("光效预热缓冲失败") }
        let scene = SKScene(size: CGSize(width: 64, height: 64))
        scene.backgroundColor = .clear
        for (index, shader) in [effects.vegetation, effects.meadowPlants, effects.contact, effects.backMist, effects.sunlight, effects.frontMist].enumerated() {
            let sprite = SKSpriteNode(texture: textures["OakA"], size: CGSize(width: 64, height: 64))
            sprite.position = CGPoint(x: 32, y: 32); sprite.zPosition = CGFloat(index)
            effects.apply(shader, to: sprite, origin: .zero, extent: sprite.size)
            scene.addChild(sprite)
        }
        let renderer = SKRenderer(device: device); renderer.scene = scene
        let pass = MTLRenderPassDescriptor(); pass.colorAttachments[0].texture = texture
        pass.colorAttachments[0].loadAction = .clear; pass.colorAttachments[0].storeAction = .store
        renderer.update(atTime: 0)
        renderer.render(withViewport: CGRect(x: 0, y: 0, width: 64, height: 64), commandBuffer: command, renderPassDescriptor: pass)
        command.commit(); command.waitUntilCompleted()
        if let error = command.error { throw error }
    }
}
