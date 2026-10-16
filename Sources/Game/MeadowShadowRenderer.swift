import MetalKit
import SpriteKit
import simd

/// Native opaque terrain and image-alpha shadows share one Metal command buffer.
/// SpriteKit's interactive foreground stays above this surface; no GPU pixels cross the CPU.
final class MeadowShadowRenderer {
    private struct Draw {
        let buffer: MTLBuffer
        let count: Int
        let texture: MTLTexture
        let kind: Float
        var uvRect = SIMD4<Float>(0, 0, 1, 1)
    }
    static let units: Float = 32
    let device: MTLDevice
    private(set) var shadowSize = 2048
    private(set) var shadowsEnabled = true
    private let queue: MTLCommandQueue
    private var depthTexture: MTLTexture
    private let depthPipeline: MTLRenderPipelineState
    private let receiverPipeline: MTLRenderPipelineState
    private let depthState: MTLDepthStencilState
    private let receiver: MTLBuffer
    private var staticDraws: [Draw] = []
    private var textures: [String: MTLTexture] = [:]
    var alignmentReview = false
    var onFirstFrameCompleted: (() -> Void)?
    var onFrameFailed: ((Error) -> Void)?
    // Keep at most one terrain/shadow frame queued on iPad hardware. If the
    // GPU is busy, the next SpriteKit callback simply skips this background frame.
    private let inFlight = DispatchSemaphore(value: 1)
    private(set) var casterCount = 0
    private(set) var submittedFrames = 0
    private(set) var textureUploadCount = 0
    private var lastRenderTime: TimeInterval = -.infinity
    private var lastCamera: MeadowViewport?
    private var lastPoses: [Int] = []
    private var firstFrameReported = false

    convenience init(device: MTLDevice, world: LivingWorld) throws {
        try self.init(device: device, props: world.casterProps, roadMask: world.roadMask)
        world.terrain.removeFromParent()
    }

    init(device: MTLDevice, props: [SceneDefinition.Prop], roadMask: CGImage,
         images: [String: CGImage] = [:], progress: ((Double, String) -> Void)? = nil) throws {
        self.device = device
        progress?(0.02, "准备投影队列")
        guard let queue = device.makeCommandQueue(), let library = device.makeDefaultLibrary() else { throw ShadowLabError.setup("地图 Metal 初始化失败") }
        self.queue = queue
        progress?(0.06, "分配阴影深度图")
        guard let depth = Self.makeDepthTexture(device: device, size: shadowSize) else { throw ShadowLabError.setup("地图深度贴图分配失败") }
        depthTexture = depth
        progress?(0.10, "编译阴影着色器")
        let pipeline = MTLRenderPipelineDescriptor()
        pipeline.vertexFunction = library.makeFunction(name: "labCutoutShadowVertex")
        pipeline.fragmentFunction = library.makeFunction(name: "meadowCutoutShadowFragment")
        pipeline.depthAttachmentPixelFormat = .depth32Float
        depthPipeline = try device.makeRenderPipelineState(descriptor: pipeline)
        progress?(0.20, "编译地面着色器")
        let color = MTLRenderPipelineDescriptor()
        color.vertexFunction = library.makeFunction(name: "labColorVertex")
        color.fragmentFunction = library.makeFunction(name: "meadowGroundFragment")
        color.colorAttachments[0].pixelFormat = .bgra8Unorm
        let attachment = color.colorAttachments[0]!
        attachment.isBlendingEnabled = false
        attachment.sourceRGBBlendFactor = .one; attachment.destinationRGBBlendFactor = .oneMinusSourceAlpha
        attachment.sourceAlphaBlendFactor = .one; attachment.destinationAlphaBlendFactor = .oneMinusSourceAlpha
        receiverPipeline = try device.makeRenderPipelineState(descriptor: color)
        progress?(0.27, "准备地面深度状态")
        let state = MTLDepthStencilDescriptor(); state.depthCompareFunction = .lessEqual; state.isDepthWriteEnabled = true
        guard let depthState = device.makeDepthStencilState(descriptor: state) else { throw ShadowLabError.setup("地图深度状态失败") }
        self.depthState = depthState
        var mesh = ShadowLabMesh()
        let b = LivingWorld.bounds
        let a = Self.root(CGPoint(x: b.minX, y: b.minY)), c = Self.root(CGPoint(x: b.maxX, y: b.maxY))
        mesh.triangle(a, SIMD3(c.x, a.y, 0), c); mesh.triangle(a, c, SIMD3(a.x, c.y, 0))
        guard let buffer = device.makeBuffer(bytes: mesh.vertices, length: mesh.vertices.count * MemoryLayout<ShadowLabVertex>.stride) else { throw ShadowLabError.setup("地图接收网格失败") }
        receiver = buffer
        progress?(0.32, "生成物件投影网格")
        // Group static instances by their original art; the depth pass needs one draw per asset.
        var groups: [String: ShadowLabMesh] = [:]
        var art = images
        func assetImage(_ name: String) -> CGImage? {
            if let cached = art[name] { return cached }
            let loaded = UIImage(named: name)?.cgImage; art[name] = loaded; return loaded
        }
        for (index, prop) in props.enumerated() {
            guard let asset = ShadowLabAsset(rawValue: prop.asset), let image = assetImage(prop.asset) else { throw ShadowLabError.setup("未配置投影素材：\(prop.asset)") }
            let instance = ShadowLabInstance(asset: asset, root: Self.root(CGPoint(x: prop.x, y: prop.y)), width: Float(prop.width) / Self.units,
                                             aspect: Float(image.height) / Float(image.width), anchor: SIMD2(0.5, asset.anchorY))
            // Mutate the grouped value in place: extracting a mesh from the
            // dictionary then appending copied all preceding vertices per prop.
            groups[prop.asset, default: ShadowLabMesh()].meadowCaster(instance,
                mirrored: prop.mirror && asset == .flowers, wind: prop.wind, phase: Float(prop.x * 0.03 + prop.y * 0.017))
            progress?(0.32 + 0.40 * Double(index + 1) / Double(max(1, props.count)), "生成物件投影网格")
            casterCount += 1
        }
        // The pole and cloth also cast through their own transparent artwork.
        for prop in props where prop.asset == "WatchTower" {
            guard let image = assetImage("Banner"), let tower = assetImage("WatchTower") else { throw ShadowLabError.setup("旗帜投影素材缺失") }
            let height = Float(prop.width) * Float(tower.height) / Float(tower.width)
            let root = Self.root(CGPoint(x: prop.x, y: prop.y)) + SIMD3<Float>(0, 0, height * (Float(LivingWorld.towerBannerRoofAnchorY) - ShadowLabAsset.tower.anchorY) / Self.units / ShadowLabMath.cameraUp.z)
            let width = min(34, max(22, Float(prop.width) * 0.40)) / Self.units
            let instance = ShadowLabInstance(asset: .banner, root: root, width: width, aspect: Float(image.height) / Float(image.width), anchor: SIMD2(0.035, 0.04))
            groups["Banner", default: ShadowLabMesh()].meadowCaster(instance, wind: 2, phase: Float(prop.x * 0.03))
            casterCount += 1
        }
        for (index, group) in groups.sorted(by: { $0.key < $1.key }).enumerated() {
            let (name, mesh) = group
            let texture = try upload(assetImage(name)!)
            textures[name] = texture
            staticDraws.append(try draw(mesh, texture: texture, kind: ShadowLabAsset(rawValue: name)!.casterKind))
            progress?(0.72 + 0.13 * Double(index + 1) / Double(max(1, groups.count)), "上传环境投影素材")
        }
        // Upload each hero atlas once during loading. Changing a walk frame
        // only changes UV bounds; it never decodes/crops/uploads on a live frame.
        for hero in 1...3 { for suffix in ["Directions", "Diagonals"] {
            let name = "Hero\(hero)\(suffix)"
            guard let atlas = assetImage(name) else { throw ShadowLabError.setup("人物投影素材缺失") }
            textures[name] = try upload(atlas)
            progress?(0.85 + Double((hero - 1) * 2 + (suffix == "Directions" ? 1 : 2)) / 6 * 0.13, "上传人物投影图集")
        } }
        guard let grass = assetImage("MeadowGround") else { throw ShadowLabError.setup("地表素材缺失") }
        textures["MeadowGround"] = try upload(grass)
        textures["RoadMask"] = try upload(roadMask)
        progress?(1, "完成地表投影")
    }

    static func root(_ point: CGPoint) -> SIMD3<Float> {
        SIMD3((Float(point.x) - 640) / units, (360 - Float(point.y)) / (units * ShadowLabMath.cameraUp.y), 0)
    }

    private static func makeDepthTexture(device: MTLDevice, size: Int) -> MTLTexture? {
        let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .depth32Float, width: size, height: size, mipmapped: false)
        descriptor.storageMode = .private
        descriptor.usage = [.renderTarget, .shaderRead]
        return device.makeTexture(descriptor: descriptor)
    }

    /// Step down after a command-buffer GPU timeout. The caller also reduces
    /// the drawable size so the next submitted frame has a smaller workload.
    @discardableResult
    func reduceQualityAfterGPUFailure() -> String? {
        if shadowSize > 1024, let smaller = Self.makeDepthTexture(device: device, size: 1024) {
            depthTexture = smaller
            shadowSize = 1024
            resetRenderCache()
            return "实时阴影图降至 1024"
        }
        if shadowsEnabled {
            shadowsEnabled = false
            resetRenderCache()
            return "关闭实时阴影"
        }
        return nil
    }

    private func resetRenderCache() {
        lastRenderTime = -.infinity
        lastCamera = nil
        lastPoses = []
    }

    private func draw(_ mesh: ShadowLabMesh, texture: MTLTexture, kind: Float) throws -> Draw {
        guard let buffer = device.makeBuffer(bytes: mesh.vertices, length: mesh.vertices.count * MemoryLayout<ShadowLabVertex>.stride) else { throw ShadowLabError.setup("地图投影网格上传失败") }
        return Draw(buffer: buffer, count: mesh.vertices.count, texture: texture, kind: kind)
    }

    private func upload(_ image: CGImage) throws -> MTLTexture {
        // The same premultiplied decode and top-origin UV convention as the approved lab.
        let w = image.width, h = image.height
        var rgba = [UInt8](repeating: 0, count: w * h * 4)
        let ok = rgba.withUnsafeMutableBytes { raw -> Bool in
            guard let c = CGContext(data: raw.baseAddress, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGBitmapInfo.byteOrder32Big.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue) else { return false }
            c.draw(image, in: CGRect(x: 0, y: 0, width: w, height: h)); return true
        }
        let d = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .rgba8Unorm, width: w, height: h, mipmapped: false)
        d.storageMode = .shared; d.usage = .shaderRead
        guard ok, let texture = device.makeTexture(descriptor: d) else { throw ShadowLabError.setup("地图素材上传失败") }
        rgba.withUnsafeBytes { texture.replace(region: MTLRegionMake2D(0, 0, w, h), mipmapLevel: 0, withBytes: $0.baseAddress!, bytesPerRow: w * 4) }
        textureUploadCount += 1
        return texture
    }

    private func heroTexture(_ hero: MeadowHeroCaster) throws -> MTLTexture {
        let suffix = hero.facing < 4 ? "Directions" : "Diagonals"
        let name = "Hero\(hero.index + 1)\(suffix)"
        guard let texture = textures[name] else { throw ShadowLabError.setup("人物投影图集未加载") }
        return texture
    }

    private func encode(command: MTLCommandBuffer, target: MTLRenderPassDescriptor, camera: MeadowViewport,
                        time: TimeInterval, sunCast: CGVector, heroes: [MeadowHeroCaster], shadows: Bool = true, roads: Bool = true, alignment: Bool = false) throws {
        let renderShadows = shadows && shadowsEnabled
        if renderShadows {
            var draws = staticDraws
            for hero in heroes {
                let texture = try heroTexture(hero)
                var mesh = ShadowLabMesh()
                let pose = HeroPose(heroIndex: hero.index, facing: hero.facing, frame: hero.frame, phase: hero.phase)
                let offset = pose.bodyOffset()
                let foot = CGPoint(x: hero.foot.x + offset.x, y: hero.foot.y - offset.y)
                let instance = ShadowLabInstance(asset: .hero, root: Self.root(foot), width: 64 / Self.units, aspect: 1, anchor: SIMD2(0.5, 0.125))
                mesh.imageCaster(instance, mirrored: HeroFrames.isMirrored(hero.facing), pose: pose)
                var item = try draw(mesh, texture: texture, kind: 2)
                item.uvRect = SIMD4(Float(hero.frame) / 4, Float(HeroFrames.sourceFacing(hero.facing) % 4) / 4, 0.25, 0.25)
                draws.append(item)
            }
            try encodeShadowDepth(command: command, draws: draws, camera: camera, time: time, sunCast: sunCast)
        }

        var u = makeUniforms(camera: camera, time: time, sunCast: sunCast, shadows: renderShadows)
        target.colorAttachments[0].loadAction = .clear; target.colorAttachments[0].storeAction = .store
        target.colorAttachments[0].clearColor = MTLClearColor(red: 0.15, green: 0.20, blue: 0.08, alpha: 1)
        guard let color = command.makeRenderCommandEncoder(descriptor: target) else { throw ShadowLabError.setup("地图接收通道失败") }
        color.label = renderShadows ? "Opaque grass + road material + PCF reception" : "Opaque grass + road material (GPU fallback)"
        color.setRenderPipelineState(receiverPipeline); color.setCullMode(.none)
        color.setVertexBuffer(receiver, offset: 0, index: 0)
        color.setVertexBytes(&u, length: MemoryLayout<ShadowLabUniforms>.stride, index: 1)
        color.setFragmentBytes(&u, length: MemoryLayout<ShadowLabUniforms>.stride, index: 1)
        color.setFragmentTexture(textures["MeadowGround"], index: 0)
        color.setFragmentTexture(depthTexture, index: 1)
        color.setFragmentTexture(textures["RoadMask"], index: 2)
        var settings = SIMD4<Float>(roads ? 1 : 0, alignment ? 1 : 0, 0, 0)
        color.setFragmentBytes(&settings, length: MemoryLayout<SIMD4<Float>>.stride, index: 2)
        color.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 6); color.endEncoding()
    }

    private func makeUniforms(camera: MeadowViewport, time: TimeInterval, sunCast: CGVector, shadows: Bool) -> ShadowLabUniforms {
        let up = ShadowLabMath.cameraUp
        let sun = simd_normalize(SIMD3(-Float(sunCast.dx) * up.z, Float(sunCast.dy) * up.z / up.y, 1))
        let light = ShadowLabMath.orthographic(halfWidth: 46, halfHeight: 46, near: 0.1, far: 180)
            * ShadowLabMath.lookAt(eye: sun * 85, target: .zero, up: SIMD3(0, 0, 1))
        return ShadowLabUniforms(camera: camera.matrix, light: light, sunTime: SIMD4(sun, Float(time)), options: SIMD4(shadows ? 1 : 0, 1 / Float(shadowSize), 1, 1))
    }

    private func encodeShadowDepth(command: MTLCommandBuffer, draws: [Draw], camera: MeadowViewport,
                                   time: TimeInterval, sunCast: CGVector) throws {
        var u = makeUniforms(camera: camera, time: time, sunCast: sunCast, shadows: true)
        let pass = MTLRenderPassDescriptor(); pass.depthAttachment.texture = depthTexture
        pass.depthAttachment.loadAction = .clear; pass.depthAttachment.storeAction = .store; pass.depthAttachment.clearDepth = 1
        guard let depth = command.makeRenderCommandEncoder(descriptor: pass) else { throw ShadowLabError.setup("地图深度通道失败") }
        depth.label = "All meadow assets: alpha relief depth"
        depth.setRenderPipelineState(depthPipeline); depth.setDepthStencilState(depthState); depth.setCullMode(.none)
        depth.setVertexBytes(&u, length: MemoryLayout<ShadowLabUniforms>.stride, index: 1)
        depth.setFragmentBytes(&u, length: MemoryLayout<ShadowLabUniforms>.stride, index: 1)
        for item in draws {
            var settings = SIMD4<Float>(item.kind, 0.32, 0, 0)
            depth.setVertexBuffer(item.buffer, offset: 0, index: 0); depth.setFragmentTexture(item.texture, index: 0)
            depth.setFragmentBytes(&settings, length: MemoryLayout<SIMD4<Float>>.stride, index: 2)
            var uvRect = item.uvRect
            depth.setFragmentBytes(&uvRect, length: MemoryLayout<SIMD4<Float>>.stride, index: 3)
            depth.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: item.count)
        }
        depth.endEncoding()
    }

    func render(in view: MTKView, world: LivingWorld, camera: MeadowViewport, time: TimeInterval, heroes: [MeadowHeroCaster]) throws {
        let poses = heroes.map { $0.facing * 4 + $0.frame }
        let changed = camera != lastCamera || poses != lastPoses
        guard changed || time - lastRenderTime >= 1.0 / 30 else { return }
        guard inFlight.wait(timeout: .now()) == .success else { return }
        // The paused MTKView has no second display link. Explicitly relinquish
        // its cached drawable after encoding/presenting, including error paths.
        // The committed command buffer retains its GPU resources until completion.
        defer { view.releaseDrawables() }
        guard let pass = view.currentRenderPassDescriptor, let drawable = view.currentDrawable, let command = queue.makeCommandBuffer() else { inFlight.signal(); return }
        do {
            try encode(command: command, target: pass, camera: camera, time: time, sunCast: world.effects.currentCast, heroes: heroes, alignment: alignmentReview)
            let semaphore = inFlight
            command.addCompletedHandler { [weak self] buffer in
                if let error = buffer.error {
                    // Apply the fallback before allowing another frame to enter the queue.
                    DispatchQueue.main.async {
                        self?.onFrameFailed?(error)
                        semaphore.signal()
                    }
                    return
                }
                semaphore.signal()
                guard buffer.status == .completed else { return }
                DispatchQueue.main.async {
                    guard let self, !self.firstFrameReported else { return }
                    self.firstFrameReported = true
                    self.onFirstFrameCompleted?()
                }
            }
            command.present(drawable); command.commit(); submittedFrames += 1
            lastRenderTime = time; lastCamera = camera; lastPoses = poses
        } catch { inFlight.signal(); throw error }
    }

    func groundSnapshot(world: LivingWorld, width: Int = 768, height: Int = 432, roads: Bool = true, shadows: Bool = true, camera: MeadowViewport? = nil, alignment: Bool = false, heroes: [MeadowHeroCaster] = []) throws -> (image: UIImage, bgra: [UInt8]) {
        let d = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm, width: width, height: height, mipmapped: false)
        d.storageMode = .shared; d.usage = .renderTarget
        guard let target = device.makeTexture(descriptor: d), let command = queue.makeCommandBuffer() else { throw ShadowLabError.setup("地面检查缓冲区失败") }
        let pass = MTLRenderPassDescriptor(); pass.colorAttachments[0].texture = target
        try encode(command: command, target: pass, camera: camera ?? MeadowViewport(size: CGSize(width: width, height: height), center: CGPoint(x: 640, y: 360), scale: CGFloat(width) / 1280), time: 1, sunCast: world.effects.currentCast, heroes: heroes, shadows: shadows, roads: roads, alignment: alignment)
        command.commit(); command.waitUntilCompleted()
        if let error = command.error { throw error }
        var bytes = [UInt8](repeating: 0, count: width * height * 4)
        bytes.withUnsafeMutableBytes { target.getBytes($0.baseAddress!, bytesPerRow: width * 4, from: MTLRegionMake2D(0, 0, width, height), mipmapLevel: 0) }
        guard let provider = CGDataProvider(data: Data(bytes) as CFData), let image = CGImage(width: width, height: height, bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: width * 4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGBitmapInfo.byteOrder32Little.union(CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedFirst.rawValue)), provider: provider, decode: nil, shouldInterpolate: false, intent: .defaultIntent) else { throw ShadowLabError.setup("地面检查图像失败") }
        return (UIImage(cgImage: image), bytes)
    }

    /// Native pipeline execution check: no image readback or effect inspection.
    func validateSubmission(world: LivingWorld, heroes: [MeadowHeroCaster]) throws {
        let d = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm, width: 128, height: 72, mipmapped: false)
        d.storageMode = .private; d.usage = .renderTarget
        guard let texture = device.makeTexture(descriptor: d), let command = queue.makeCommandBuffer() else { throw ShadowLabError.setup("地图运行检查分配失败") }
        let pass = MTLRenderPassDescriptor(); pass.colorAttachments[0].texture = texture
        try encode(command: command, target: pass, camera: MeadowViewport(size: CGSize(width: 128, height: 72), center: CGPoint(x: 640, y: 360), scale: 0.1), time: 1, sunCast: world.effects.currentCast, heroes: heroes)
        command.commit(); command.waitUntilCompleted()
        if let error = command.error { throw error }
        guard command.status == .completed else { throw ShadowLabError.setup("地图 Metal 检查未完成") }
    }
}

struct MeadowHeroCaster {
    let index: Int
    let foot: CGPoint
    let facing: Int
    let frame: Int
    var phase: CGFloat = 0
}
