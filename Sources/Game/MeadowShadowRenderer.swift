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
    }
    static let units: Float = 32
    let device: MTLDevice
    let shadowSize = 2048
    private let queue: MTLCommandQueue
    private let depthTexture: MTLTexture
    private let depthPipeline: MTLRenderPipelineState
    private let receiverPipeline: MTLRenderPipelineState
    private let depthState: MTLDepthStencilState
    private let receiver: MTLBuffer
    private var staticDraws: [Draw] = []
    private var textures: [String: MTLTexture] = [:]
    private var atlases: [String: CGImage] = [:]
    private let inFlight = DispatchSemaphore(value: 2)
    private(set) var casterCount = 0
    private(set) var submittedFrames = 0
    private var lastRenderTime: TimeInterval = -.infinity
    private var lastCenter = CGPoint.zero
    private var lastScale: CGFloat = 0
    private var lastViewport = CGSize.zero
    private var lastPoses: [Int] = []

    init(device: MTLDevice, world: LivingWorld) throws {
        self.device = device
        guard let queue = device.makeCommandQueue(), let library = device.makeDefaultLibrary() else { throw ShadowLabError.setup("地图 Metal 初始化失败") }
        self.queue = queue
        let descriptor = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .depth32Float, width: shadowSize, height: shadowSize, mipmapped: false)
        descriptor.storageMode = .private; descriptor.usage = [.renderTarget, .shaderRead]
        guard let depth = device.makeTexture(descriptor: descriptor) else { throw ShadowLabError.setup("地图深度贴图分配失败") }
        depthTexture = depth
        let pipeline = MTLRenderPipelineDescriptor()
        pipeline.vertexFunction = library.makeFunction(name: "labCutoutShadowVertex")
        pipeline.fragmentFunction = library.makeFunction(name: "meadowCutoutShadowFragment")
        pipeline.depthAttachmentPixelFormat = .depth32Float
        depthPipeline = try device.makeRenderPipelineState(descriptor: pipeline)
        let color = MTLRenderPipelineDescriptor()
        color.vertexFunction = library.makeFunction(name: "labColorVertex")
        color.fragmentFunction = library.makeFunction(name: "meadowGroundFragment")
        color.colorAttachments[0].pixelFormat = .bgra8Unorm
        let attachment = color.colorAttachments[0]!
        attachment.isBlendingEnabled = false
        attachment.sourceRGBBlendFactor = .one; attachment.destinationRGBBlendFactor = .oneMinusSourceAlpha
        attachment.sourceAlphaBlendFactor = .one; attachment.destinationAlphaBlendFactor = .oneMinusSourceAlpha
        receiverPipeline = try device.makeRenderPipelineState(descriptor: color)
        let state = MTLDepthStencilDescriptor(); state.depthCompareFunction = .lessEqual; state.isDepthWriteEnabled = true
        guard let depthState = device.makeDepthStencilState(descriptor: state) else { throw ShadowLabError.setup("地图深度状态失败") }
        self.depthState = depthState
        var mesh = ShadowLabMesh()
        let b = LivingWorld.bounds
        let a = Self.root(CGPoint(x: b.minX, y: b.minY)), c = Self.root(CGPoint(x: b.maxX, y: b.maxY))
        mesh.triangle(a, SIMD3(c.x, a.y, 0), c); mesh.triangle(a, c, SIMD3(a.x, c.y, 0))
        guard let buffer = device.makeBuffer(bytes: mesh.vertices, length: mesh.vertices.count * MemoryLayout<ShadowLabVertex>.stride) else { throw ShadowLabError.setup("地图接收网格失败") }
        receiver = buffer
        // Group static instances by their original art; the depth pass needs one draw per asset.
        var groups: [String: ShadowLabMesh] = [:]
        for prop in world.casterProps {
            guard let asset = ShadowLabAsset(rawValue: prop.asset), let image = UIImage(named: prop.asset)?.cgImage else { throw ShadowLabError.setup("未配置投影素材：\(prop.asset)") }
            var mesh = groups[prop.asset] ?? ShadowLabMesh()
            let instance = ShadowLabInstance(asset: asset, root: Self.root(CGPoint(x: prop.x, y: prop.y)), width: Float(prop.width) / Self.units,
                                             aspect: Float(image.height) / Float(image.width), anchor: SIMD2(0.5, asset.anchorY))
            let start = mesh.vertices.count
            mesh.imageCaster(instance, mirrored: prop.mirror && asset == .flowers)
            for i in start..<mesh.vertices.count {
                mesh.vertices[i].uvWind.z = prop.wind
                mesh.vertices[i].uvWind.w = Float(prop.x * 0.03 + prop.y * 0.017)
            }
            groups[prop.asset] = mesh
            casterCount += 1
        }
        // The pole and cloth also cast through their own transparent artwork.
        for prop in world.casterProps where prop.asset == "WatchTower" {
            guard let image = UIImage(named: "Banner")?.cgImage, let tower = UIImage(named: "WatchTower")?.cgImage else { throw ShadowLabError.setup("旗帜投影素材缺失") }
            let height = Float(prop.width) * Float(tower.height) / Float(tower.width)
            let root = Self.root(CGPoint(x: prop.x, y: prop.y)) + SIMD3<Float>(0, 0, height * (Float(LivingWorld.towerBannerRoofAnchorY) - ShadowLabAsset.tower.anchorY) / Self.units / ShadowLabMath.cameraUp.z)
            let width = min(34, max(22, Float(prop.width) * 0.40)) / Self.units
            let instance = ShadowLabInstance(asset: .banner, root: root, width: width, aspect: Float(image.height) / Float(image.width), anchor: SIMD2(0.035, 0.04))
            var mesh = groups["Banner"] ?? ShadowLabMesh()
            let start = mesh.vertices.count; mesh.imageCaster(instance)
            for i in start..<mesh.vertices.count { mesh.vertices[i].uvWind.z = 2; mesh.vertices[i].uvWind.w = Float(prop.x * 0.03) }
            groups["Banner"] = mesh; casterCount += 1
        }
        for (name, mesh) in groups {
            let image = UIImage(named: name)!.cgImage!
            let texture = try upload(image)
            textures[name] = texture
            staticDraws.append(try draw(mesh, texture: texture, kind: ShadowLabAsset(rawValue: name)!.casterKind))
        }
        guard let grass = UIImage(named: "MeadowGround")?.cgImage else { throw ShadowLabError.setup("地表素材缺失") }
        textures["MeadowGround"] = try upload(grass)
        textures["RoadMask"] = try upload(world.roadMask)
        world.terrain.removeFromParent()
    }

    static func root(_ point: CGPoint) -> SIMD3<Float> {
        SIMD3((Float(point.x) - 640) / units, (360 - Float(point.y)) / (units * ShadowLabMath.cameraUp.y), 0)
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
        return texture
    }

    private func heroTexture(_ hero: MeadowHeroCaster) throws -> MTLTexture {
        let suffix = hero.facing < 4 ? "Directions" : "Diagonals"
        let name = "Hero\(hero.index + 1)\(suffix)"
        let key = "\(name)-\(hero.facing)-\(hero.frame)"
        if let texture = textures[key] { return texture }
        guard let atlas = atlases[name] ?? UIImage(named: name)?.cgImage else { throw ShadowLabError.setup("人物投影素材缺失") }
        atlases[name] = atlas
        let cell = atlas.width / 4
        guard let image = atlas.cropping(to: CGRect(x: hero.frame * cell, y: (hero.facing % 4) * cell, width: cell, height: cell)) else { throw ShadowLabError.setup("人物投影帧裁切失败") }
        let texture = try upload(image); textures[key] = texture; return texture
    }

    private func encode(command: MTLCommandBuffer, target: MTLRenderPassDescriptor, viewport: CGSize, center: CGPoint,
                        scale: CGFloat, time: TimeInterval, sunCast: CGVector, heroes: [MeadowHeroCaster], shadows: Bool = true, roads: Bool = true) throws {
        var draws = staticDraws
        for hero in heroes {
            let texture = try heroTexture(hero)
            var mesh = ShadowLabMesh()
            let instance = ShadowLabInstance(asset: .hero, root: Self.root(hero.foot), width: 64 / Self.units, aspect: 1, anchor: SIMD2(0.5, 0.125))
            mesh.imageCaster(instance)
            draws.append(try draw(mesh, texture: texture, kind: 2))
        }
        let up = ShadowLabMath.cameraUp
        let sx = Float(2 * scale / max(1, viewport.width)), sy = Float(2 * scale / max(1, viewport.height))
        let camera = simd_float4x4(columns: (SIMD4(Self.units * sx, 0, 0, 0), SIMD4(0, Self.units * up.y * sy, 0, 0),
                                            SIMD4(0, Self.units * up.z * sy, 0, 0), SIMD4((640 - Float(center.x)) * sx, (Float(center.y) - 360) * sy, 0.5, 1)))
        let sun = simd_normalize(SIMD3(-Float(sunCast.dx) * up.z, Float(sunCast.dy) * up.z / up.y, 1))
        let light = ShadowLabMath.orthographic(halfWidth: 46, halfHeight: 46, near: 0.1, far: 180)
            * ShadowLabMath.lookAt(eye: sun * 85, target: .zero, up: SIMD3(0, 0, 1))
        var u = ShadowLabUniforms(camera: camera, light: light, sunTime: SIMD4(sun, Float(time)), options: SIMD4(shadows ? 1 : 0, 1 / Float(shadowSize), 1, 1))
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
            depth.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: item.count)
        }
        depth.endEncoding()
        target.colorAttachments[0].loadAction = .clear; target.colorAttachments[0].storeAction = .store
        target.colorAttachments[0].clearColor = MTLClearColor(red: 0.15, green: 0.20, blue: 0.08, alpha: 1)
        guard let color = command.makeRenderCommandEncoder(descriptor: target) else { throw ShadowLabError.setup("地图接收通道失败") }
        color.label = "Opaque grass + road material + PCF reception"
        color.setRenderPipelineState(receiverPipeline); color.setCullMode(.none)
        color.setVertexBuffer(receiver, offset: 0, index: 0)
        color.setVertexBytes(&u, length: MemoryLayout<ShadowLabUniforms>.stride, index: 1)
        color.setFragmentBytes(&u, length: MemoryLayout<ShadowLabUniforms>.stride, index: 1)
        color.setFragmentTexture(textures["MeadowGround"], index: 0)
        color.setFragmentTexture(depthTexture, index: 1)
        color.setFragmentTexture(textures["RoadMask"], index: 2)
        var settings = SIMD4<Float>(roads ? 1 : 0, 0, 0, 0)
        color.setFragmentBytes(&settings, length: MemoryLayout<SIMD4<Float>>.stride, index: 2)
        color.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 6); color.endEncoding()
    }

    func render(in view: MTKView, world: LivingWorld, center: CGPoint, scale: CGFloat, time: TimeInterval, heroes: [MeadowHeroCaster]) throws {
        let poses = heroes.map { $0.facing * 4 + $0.frame }
        let changed = center != lastCenter || scale != lastScale || view.bounds.size != lastViewport || poses != lastPoses
        guard changed || time - lastRenderTime >= 1.0 / 30 else { return }
        guard inFlight.wait(timeout: .now()) == .success else { return }
        // The paused MTKView has no second display link. Explicitly relinquish
        // its cached drawable after encoding/presenting, including error paths.
        // The committed command buffer retains its GPU resources until completion.
        defer { view.releaseDrawables() }
        guard let pass = view.currentRenderPassDescriptor, let drawable = view.currentDrawable, let command = queue.makeCommandBuffer() else { inFlight.signal(); return }
        do {
            let size = view.bounds.size
            try encode(command: command, target: pass, viewport: size, center: center, scale: scale, time: time, sunCast: world.effects.currentCast, heroes: heroes)
            let semaphore = inFlight; command.addCompletedHandler { _ in semaphore.signal() }
            command.present(drawable); command.commit(); submittedFrames += 1
            lastRenderTime = time; lastCenter = center; lastScale = scale
            lastViewport = view.bounds.size; lastPoses = poses
        } catch { inFlight.signal(); throw error }
    }

    func groundSnapshot(world: LivingWorld, width: Int = 768, height: Int = 432, roads: Bool = true, shadows: Bool = true) throws -> (image: UIImage, bgra: [UInt8]) {
        let d = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm, width: width, height: height, mipmapped: false)
        d.storageMode = .shared; d.usage = .renderTarget
        guard let target = device.makeTexture(descriptor: d), let command = queue.makeCommandBuffer() else { throw ShadowLabError.setup("地面检查缓冲区失败") }
        let pass = MTLRenderPassDescriptor(); pass.colorAttachments[0].texture = target
        try encode(command: command, target: pass, viewport: CGSize(width: width, height: height), center: CGPoint(x: 640, y: 360), scale: CGFloat(width) / 1280, time: 1, sunCast: world.effects.currentCast, heroes: [], shadows: shadows, roads: roads)
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
        try encode(command: command, target: pass, viewport: CGSize(width: 128, height: 72), center: CGPoint(x: 640, y: 360), scale: 0.1, time: 1, sunCast: world.effects.currentCast, heroes: heroes)
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
}
