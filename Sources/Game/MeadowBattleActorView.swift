import UIKit

/// Per-layer transform in registered 256 px artwork coordinates. Every part
/// uses the same canvas and pivots, so appearance assets can use this rig too.
struct MeadowBattleLayerPose {
    var offset: CGPoint = .zero
    var pivot: CGPoint = CGPoint(x: 128, y: 160)
    var rotation: CGFloat = 0
    var scale: CGFloat = 1
}

/// A sampled battle pose. `rootOffset` is deliberately separate from the
/// registered art: the battlefield owns lunge/knockback travel and can keep
/// the planted-foot shadow aligned. Contacts are in canvas pixels.
struct MeadowBattlePoseSample {
    var clip: String
    var progress: CGFloat
    var rootOffset: CGPoint
    var footAnchorPx: CGPoint
    var contacts: [CGPoint]
    var layers: [String: MeadowBattleLayerPose]
    var hitFlash: CGFloat
    var recoil: CGFloat
}

private struct MeadowBattleAnimationKey: Decodable {
    let t: CGFloat
    let root: [CGFloat]
    let lean: CGFloat
    let crouch: CGFloat
    let shoulder: CGFloat
    let elbow: CGFloat
    let wrist: CGFloat
    let nearHip: CGFloat
    let nearKnee: CGFloat
    let farHip: CGFloat
    let farKnee: CGFloat
    let flash: CGFloat
    let recoil: CGFloat
    var rootPoint: CGPoint { CGPoint(x: root[0], y: root[1]) }
}

private struct MeadowBattleAnimationClip: Decodable {
    let durationMs: Int
    let loop: Bool
    let keys: [MeadowBattleAnimationKey]
}

private struct MeadowBattleAnimationLibrary: Decodable {
    let schemaVersion: Int
    let frameDurationMs: Int
    let silhouetteBuckets: Int
    let clips: [String: MeadowBattleAnimationClip]
}

/// Runtime and review renderers share this JSON clip library.
enum MeadowBattleAnimation {
    private static let library: MeadowBattleAnimationLibrary = {
        guard let data = NSDataAsset(name: "MeadowBattleHeroAnimationV2")?.data,
              let decoded = try? JSONDecoder().decode(MeadowBattleAnimationLibrary.self, from: data) else {
            fatalError("Missing or invalid MeadowBattleHeroAnimationV2 asset")
        }
        return decoded
    }()
    static let clips = ["idle", "attack", "guard", "hit", "victory", "defeat"]
    static let frameDurationMs = library.frameDurationMs
    static let silhouetteBuckets = library.silhouetteBuckets
    static func durationMs(for clip: String) -> Int { library.clips[clip]?.durationMs ?? 2400 }
    static func loops(_ clip: String) -> Bool { library.clips[clip]?.loop ?? false }

    static func sample(clip: String, progress raw: CGFloat) -> MeadowBattlePoseSample {
        let name = library.clips[clip] == nil ? "idle" : clip
        let progress = min(1, max(0, raw))
        let sequence = library.clips[name]!.keys
        let upper = sequence.firstIndex(where: { $0.t >= progress }) ?? sequence.count - 1
        let a = sequence[max(0, upper - 1)], b = sequence[upper]
        let f = b.t == a.t ? 0 : (progress - a.t) / (b.t - a.t)
        func mix(_ x: CGFloat, _ y: CGFloat) -> CGFloat { x + (y - x) * f }
        func mixPoint(_ x: CGPoint, _ y: CGPoint) -> CGPoint { CGPoint(x: mix(x.x, y.x), y: mix(x.y, y.y)) }
        let root = mixPoint(a.rootPoint, b.rootPoint)
        let lean = mix(a.lean, b.lean), crouch = mix(a.crouch, b.crouch)
        func bodyPoint(_ point: CGPoint) -> CGPoint {
            let dx = point.x - 132, dy = point.y - 167
            let c = cos(lean), s = sin(lean)
            return CGPoint(x: 132 + dx * c - dy * s,
                           y: 167 + dx * s + dy * c + crouch)
        }
        func rotate(_ point: CGPoint, around pivot: CGPoint, by angle: CGFloat) -> CGPoint {
            let x = point.x - pivot.x, y = point.y - pivot.y
            let c = cos(angle), s = sin(angle)
            return CGPoint(x: pivot.x + x * c - y * s, y: pivot.y + x * s + y * c)
        }
        func layerPose(pivot: CGPoint, movedPivot: CGPoint, rotation: CGFloat) -> MeadowBattleLayerPose {
            .init(offset: CGPoint(x: movedPivot.x - pivot.x, y: movedPivot.y - pivot.y),
                  pivot: pivot, rotation: rotation)
        }

        let shoulderPivot = CGPoint(x: 117, y: 141), elbowPivot = CGPoint(x: 128, y: 158)
        let gripPivot = CGPoint(x: 145.6, y: 163.7)
        let shoulderAngle = mix(a.shoulder, b.shoulder)
        let elbowAngle = mix(a.elbow, b.elbow)
        let wristAngle = mix(a.wrist, b.wrist)
        let movedShoulder = bodyPoint(shoulderPivot)
        let movedElbow = bodyPoint(rotate(elbowPivot, around: shoulderPivot, by: shoulderAngle))
        let movedGrip = bodyPoint(rotate(rotate(gripPivot, around: elbowPivot, by: elbowAngle),
                                         around: shoulderPivot, by: shoulderAngle))
        let torsoPose = MeadowBattleLayerPose(offset: CGPoint(x: 0, y: crouch),
                                              pivot: CGPoint(x: 132, y: 167), rotation: lean)

        let nearHip = CGPoint(x: 134, y: 175), nearKnee = CGPoint(x: 141, y: 187)
        let farHip = CGPoint(x: 115, y: 176), farKnee = CGPoint(x: 104, y: 192)
        let nearHipAngle = mix(a.nearHip, b.nearHip), nearKneeAngle = mix(a.nearKnee, b.nearKnee)
        let farHipAngle = mix(a.farHip, b.farHip), farKneeAngle = mix(a.farKnee, b.farKnee)
        let movedNearHip = bodyPoint(nearHip)
        let movedNearKnee = bodyPoint(rotate(nearKnee, around: nearHip, by: nearHipAngle))
        let movedFarHip = bodyPoint(farHip)
        let movedFarKnee = bodyPoint(rotate(farKnee, around: farHip, by: farHipAngle))
        func legPoint(_ point: CGPoint, hip: CGPoint, knee: CGPoint, hipAngle: CGFloat, kneeAngle: CGFloat) -> CGPoint {
            bodyPoint(rotate(rotate(point, around: knee, by: kneeAngle), around: hip, by: hipAngle))
        }
        // Sample several points along each boot's registered sole. Screen y
        // grows downward, so the lowest transformed point is the support plane.
        let farSoles = [90, 98, 105].map {
            legPoint(CGPoint(x: CGFloat($0), y: 214), hip: farHip, knee: farKnee,
                     hipAngle: farHipAngle, kneeAngle: farKneeAngle)
        }
        let nearSoles = [145, 150, 156].map {
            legPoint(CGPoint(x: CGFloat($0), y: 214), hip: nearHip, knee: nearKnee,
                     hipAngle: nearHipAngle, kneeAngle: nearKneeAngle)
        }
        let upperArm = layerPose(pivot: shoulderPivot, movedPivot: movedShoulder,
                                 rotation: lean + shoulderAngle)
        let forearm = layerPose(pivot: elbowPivot, movedPivot: movedElbow,
                                rotation: lean + shoulderAngle + elbowAngle)
        let nearThigh = layerPose(pivot: nearHip, movedPivot: movedNearHip,
                                  rotation: lean + nearHipAngle)
        let nearShin = layerPose(pivot: nearKnee, movedPivot: movedNearKnee,
                                 rotation: lean + nearHipAngle + nearKneeAngle)
        let farThigh = layerPose(pivot: farHip, movedPivot: movedFarHip,
                                 rotation: lean + farHipAngle)
        let farShin = layerPose(pivot: farKnee, movedPivot: movedFarKnee,
                                rotation: lean + farHipAngle + farKneeAngle)
        let handPose = layerPose(pivot: gripPivot, movedPivot: movedGrip,
                                 rotation: lean + shoulderAngle + elbowAngle + wristAngle)
        let swordPose = layerPose(pivot: gripPivot, movedPivot: movedGrip,
                                  rotation: lean + shoulderAngle + elbowAngle + wristAngle)
        let layers: [String: MeadowBattleLayerPose] = [
            "MeadowBattleHeroBodyCore": torsoPose,
            "MeadowBattleHeroWardrobeCore": torsoPose,
            "MeadowBattleHeroJointUnderlay": torsoPose,
            "MeadowBattleHeroHair": torsoPose,
            "MeadowBattleHeroFace": torsoPose,
            "MeadowBattleHeroLegNearThighBody": nearThigh,
            "MeadowBattleHeroLegNearThighWardrobe": nearThigh,
            "MeadowBattleHeroLegNearShinBody": nearShin,
            "MeadowBattleHeroLegNearShinWardrobe": nearShin,
            "MeadowBattleHeroLegFarThighBody": farThigh,
            "MeadowBattleHeroLegFarThighWardrobe": farThigh,
            "MeadowBattleHeroLegFarShinBody": farShin,
            "MeadowBattleHeroLegFarShinWardrobe": farShin,
            "MeadowBattleHeroArmNearUpperBody": upperArm,
            "MeadowBattleHeroArmNearUpperWardrobe": upperArm,
            "MeadowBattleHeroArmNearForearmBody": forearm,
            "MeadowBattleHeroArmNearForearmWardrobe": forearm,
            "MeadowBattleHeroNearHand": handPose,
            "MeadowBattleHeroFarHand": torsoPose,
            "MeadowBattleHeroWeapon": swordPose
        ]
        // Keep the support sole at the registered 214 px ground line. Contacts
        // include planted soles only; a lifted boot must not cast a full-strength
        // contact shadow. These local points are transformed with the actor.
        let allSoles = farSoles + nearSoles
        let groundY = allSoles.map(\.y).max() ?? 214
        let rootOffset = CGPoint(x: root.x, y: root.y + 214 - groundY)
        func plantedBootContact(_ soles: [CGPoint]) -> CGPoint? {
            let planted = soles.filter { groundY - $0.y <= 1 }
            guard !planted.isEmpty else { return nil }
            return CGPoint(x: planted.map(\.x).reduce(0, +) / CGFloat(planted.count),
                           y: planted.map(\.y).reduce(0, +) / CGFloat(planted.count))
        }
        let contacts = [plantedBootContact(farSoles), plantedBootContact(nearSoles)].compactMap { $0 }
        let anchorX = contacts.isEmpty ? 123 : contacts.map(\.x).reduce(0, +) / CGFloat(contacts.count)
        return MeadowBattlePoseSample(clip: name, progress: progress, rootOffset: rootOffset,
                                      footAnchorPx: CGPoint(x: anchorX, y: groundY),
                                      contacts: contacts, layers: layers,
                                      hitFlash: mix(a.flash, b.flash), recoil: mix(a.recoil, b.recoil))
    }
}

/// A single registered pose assembled from data. Appearance layers never alter
/// the pose, source canvas or foot anchor, and add no appearance-ID branches.
struct MeadowBattleActorConfiguration: Decodable {
    let canvasPx: [CGFloat]
    let footAnchorPx: [CGFloat]
    let referenceHeightPx: CGFloat
    let layers: [String]

    static func load() -> MeadowBattleActorConfiguration? {
        guard let data = NSDataAsset(name: "MeadowBattleHeroConfigurationV2")?.data else { return nil }
        guard let configuration = try? JSONDecoder().decode(Self.self, from: data),
              configuration.canvasPx.count == 2, configuration.footAnchorPx.count == 2,
              configuration.canvasPx.allSatisfy({ $0 > 0 }),
              configuration.referenceHeightPx > 0, !configuration.layers.isEmpty else { return nil }
        return configuration
    }

    var canvasSize: CGSize { CGSize(width: canvasPx[0], height: canvasPx[1]) }
    var footAnchor: CGPoint { CGPoint(x: footAnchorPx[0], y: footAnchorPx[1]) }
}

final class MeadowBattleActorView: UIView {
    let configuration: MeadowBattleActorConfiguration?
    private let images: [UIImageView]
    var layerNames: [String] { configuration?.layers ?? [] }
    let silhouette: UIImage?
    private(set) var currentPose = MeadowBattleAnimation.sample(clip: "idle", progress: 0)
    private let silhouetteCache = NSCache<NSString, UIImage>()
    var poseRootOffset: CGPoint { currentPose.rootOffset }
    var poseFootAnchorPx: CGPoint { currentPose.footAnchorPx }
    var poseContacts: [CGPoint] { currentPose.contacts }
    var poseSilhouette: UIImage { silhouette(for: currentPose) }

    override init(frame: CGRect) {
        let configuration = MeadowBattleActorConfiguration.load()
        self.configuration = configuration
        images = (configuration?.layers ?? []).map { name in
            let view = UIImageView(image: UIImage(named: name))
            view.accessibilityIdentifier = name
            view.layer.minificationFilter = .nearest
            view.layer.magnificationFilter = .nearest
            view.contentMode = .scaleToFill
            return view
        }
        if let configuration {
            let format = UIGraphicsImageRendererFormat(); format.scale = 1
            silhouette = UIGraphicsImageRenderer(size: configuration.canvasSize, format: format).image { _ in
                for name in configuration.layers {
                    if name == "MeadowBattleHeroJointUnderlay" { continue }
                    UIImage(named: name)?.draw(in: CGRect(origin: .zero, size: configuration.canvasSize))
                }
            }
        } else {
            silhouette = nil
        }
        super.init(frame: frame)
        silhouetteCache.countLimit = 96
        silhouetteCache.totalCostLimit = 24*1024*1024
        images.forEach(addSubview)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func layoutSubviews() {
        super.layoutSubviews()
        images.forEach {
            $0.layer.anchorPoint = .zero
            $0.bounds = CGRect(origin: .zero, size: bounds.size)
            $0.layer.position = bounds.origin
        }
        applyPose(currentPose)
    }

    /// Apply one deterministic pose sample without starting a timer. The scene
    /// can use the same sample to move the actor and shadow on its own clock.
    func setPose(clip: String, progress: CGFloat) {
        let pose = MeadowBattleAnimation.sample(clip: clip, progress: progress)
        currentPose = pose
        applyPose(pose)
    }

    private func applyPose(_ pose: MeadowBattlePoseSample) {
        guard !images.isEmpty else { return }
        let orderedNames = orderedLayerNames(for: pose.clip)
        let depth = Dictionary(uniqueKeysWithValues: orderedNames.enumerated().map { ($0.element, CGFloat($0.offset)) })
        UIView.performWithoutAnimation {
            for (index, image) in images.enumerated() {
                let name = configuration?.layers[index] ?? ""
                image.layer.zPosition = depth[name] ?? CGFloat(index)
                image.alpha = (name == "MeadowBattleHeroJointUnderlay" && pose.clip == "idle") ? 0 : 1
                guard let part = pose.layers[name] else { image.transform = .identity; continue }
                let sx = bounds.width / (configuration?.canvasSize.width ?? 256)
                let sy = bounds.height / (configuration?.canvasSize.height ?? 256)
                let px = part.pivot.x * sx, py = part.pivot.y * sy
                let ox = part.offset.x * sx, oy = part.offset.y * sy
                let c = cos(part.rotation) * part.scale, s = sin(part.rotation) * part.scale
                let transform = CGAffineTransform(a: c, b: s, c: -s, d: c,
                                                  tx: px + ox - c * px + s * py,
                                                  ty: py + oy - s * px - c * py)
                image.layer.setAffineTransform(transform)
            }
        }
    }

    /// Keep the approved idle stack exactly as imported (weapon behind the
    /// character). During authored clips, bring the independently moving blade
    /// in front of the torso and sleeves while retaining head/hand foreground.
    private func orderedLayerNames(for clip: String) -> [String] {
        let names = configuration?.layers ?? []
        guard clip != "idle" else { return names }
        let animated = [
            "MeadowBattleHeroJointUnderlay", "MeadowBattleHeroBodyCore",
            "MeadowBattleHeroLegFarThighBody", "MeadowBattleHeroLegFarShinBody",
            "MeadowBattleHeroLegNearThighBody", "MeadowBattleHeroLegNearShinBody",
            "MeadowBattleHeroArmNearUpperBody", "MeadowBattleHeroArmNearForearmBody",
            "MeadowBattleHeroWardrobeCore", "MeadowBattleHeroLegFarThighWardrobe",
            "MeadowBattleHeroLegFarShinWardrobe", "MeadowBattleHeroLegNearThighWardrobe",
            "MeadowBattleHeroLegNearShinWardrobe", "MeadowBattleHeroArmNearUpperWardrobe",
            "MeadowBattleHeroArmNearForearmWardrobe", "MeadowBattleHeroWeapon",
            "MeadowBattleHeroHair", "MeadowBattleHeroFace", "MeadowBattleHeroNearHand",
            "MeadowBattleHeroFarHand"
        ]
        return animated.filter { names.contains($0) }
    }

    private func silhouette(for pose: MeadowBattlePoseSample) -> UIImage {
        let bucket = Int((pose.progress * CGFloat(MeadowBattleAnimation.silhouetteBuckets)).rounded())
        let key = "\(pose.clip)-\(bucket)" as NSString
        if let cached = silhouetteCache.object(forKey: key) { return cached }
        let renderPose = MeadowBattleAnimation.sample(clip: pose.clip,
                                                      progress: CGFloat(bucket) / CGFloat(MeadowBattleAnimation.silhouetteBuckets))
        let size = configuration?.canvasSize ?? CGSize(width: 256, height: 256)
        let format = UIGraphicsImageRendererFormat(); format.scale = 1
        let rendered = UIGraphicsImageRenderer(size: size, format: format).image { renderer in
            for name in orderedLayerNames(for: pose.clip) {
                if name == "MeadowBattleHeroJointUnderlay" && pose.clip == "idle" { continue }
                guard let image = UIImage(named: name) else { continue }
                let part = renderPose.layers[name] ?? MeadowBattleLayerPose()
                let sx = size.width / 256, sy = size.height / 256
                let px = part.pivot.x * sx, py = part.pivot.y * sy
                let ox = part.offset.x * sx, oy = part.offset.y * sy
                let c = cos(part.rotation) * part.scale, s = sin(part.rotation) * part.scale
                let transform = CGAffineTransform(a: c, b: s, c: -s, d: c,
                                                  tx: px + ox - c * px + s * py,
                                                  ty: py + oy - s * px - c * py)
                renderer.cgContext.saveGState()
                renderer.cgContext.concatenate(transform)
                image.draw(in: CGRect(origin: .zero, size: size))
                renderer.cgContext.restoreGState()
            }
        }
        silhouetteCache.setObject(rendered, forKey: key,cost:256*256*4)
        return rendered
    }
}

/// Low-opacity source-silhouette projection plus small, soft planted-foot
/// contacts. The cast goes down-right, matching the scene's upper-left light.
final class MeadowBattleGroundingView: UIView {
    struct Contact {
        let point: CGPoint
        let radius: CGFloat
    }
    var spriteFrame: CGRect = .zero { didSet { if oldValue != spriteFrame { setNeedsDisplay() } } }
    private final class CachedTile: NSObject { let source:UIImage;let image:UIImage;init(source:UIImage,image:UIImage) { self.source=source;self.image=image } }
    private static let cache: NSCache<NSString,CachedTile> = { let c=NSCache<NSString,CachedTile>();c.totalCostLimit=8*1024*1024;return c }()
    private var tile:UIImage?
    private var sourceSize=CGSize(width:256,height:256)
    private var tileOrigin=CGPoint.zero
    private static let contactMask:UIImage = {
        let f=UIGraphicsImageRendererFormat();f.scale=1
        return UIGraphicsImageRenderer(size:CGSize(width:64,height:64),format:f).image { ctx in
            let colors=[UIColor(red:0.025,green:0.035,blue:0.018,alpha:0.68).cgColor,UIColor.clear.cgColor] as CFArray
            let g=CGGradient(colorsSpace:CGColorSpaceCreateDeviceRGB(),colors:colors,locations:[0,1])!
            ctx.cgContext.drawRadialGradient(g,startCenter:CGPoint(x:32,y:32),startRadius:0,endCenter:CGPoint(x:32,y:32),endRadius:32,options:[])
        }
    }()
    private var soleY: CGFloat
    private var contacts: [Contact]

    init(image: UIImage?, soleY: CGFloat, contacts: [Contact]) {
        // The original 0.16 tint disappeared against the bright, detailed
        // ground in actual iPad captures. Keep the cast restrained, but dark
        // enough to read at the 1x battle-scene scale.
        self.soleY = soleY
        self.contacts = contacts
        super.init(frame: .zero)
        isOpaque = false
        isUserInteractionEnabled = false
        contentMode = .redraw
        update(image:image,soleY:soleY,contacts:contacts)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    /// Update the projected registered pose. The actor caches silhouettes by
    /// clip and quantized progress, avoiding a render on every display tick.
    func update(image: UIImage?, soleY: CGFloat, contacts: [Contact]) {
        if let image {
            sourceSize=image.size;tileOrigin=CGPoint(x:-8,y:soleY-8)
            let key="\(ObjectIdentifier(image))-\(Int(soleY*10))" as NSString
            if let found=Self.cache.object(forKey:key) { tile=found.image } else {
                let tint=image.withTintColor(UIColor(red:0.035,green:0.045,blue:0.025,alpha:0.34),renderingMode:.alwaysOriginal)
                let size=CGSize(width:image.size.width+ceil(image.size.height*0.38)+16,height:ceil(image.size.height*0.15)+16)
                let format=UIGraphicsImageRendererFormat();format.scale=1
                let rendered=UIGraphicsImageRenderer(size:size,format:format).image { ctx in
                    let c=ctx.cgContext;c.translateBy(x:8,y:8-soleY)
                    c.concatenate(CGAffineTransform(a:1,b:0,c:-0.38,d:-0.15,tx:soleY*0.38,ty:soleY*1.15))
                    c.setShadow(offset:.zero,blur:3.5,color:UIColor.black.withAlphaComponent(0.18).cgColor)
                    tint.draw(at:.zero)
                }
                tile=rendered;Self.cache.setObject(CachedTile(source:image,image:rendered),forKey:key,cost:Int(size.width*size.height)*4)
            }
        } else { tile=nil }
        self.soleY = soleY
        self.contacts = contacts
        setNeedsDisplay()
    }

    override func draw(_ rect: CGRect) {
        guard let tile, let context=UIGraphicsGetCurrentContext(),spriteFrame.width>0 else { return }
        context.saveGState()
        context.translateBy(x:spriteFrame.minX,y:spriteFrame.minY)
        context.scaleBy(x:spriteFrame.width/sourceSize.width,y:spriteFrame.height/sourceSize.height)
        tile.draw(at:tileOrigin)
        for contact in contacts {
            let r=contact.radius
            Self.contactMask.draw(in:CGRect(x:contact.point.x-r,y:contact.point.y-r*0.38,width:r*2,height:r*0.76))
        }
        context.restoreGState()
    }
}
