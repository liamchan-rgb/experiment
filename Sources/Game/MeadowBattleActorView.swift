import UIKit

/// A single registered pose assembled from data. Appearance layers never alter
/// the pose, source canvas or foot anchor, and add no appearance-ID branches.
struct MeadowBattleActorConfiguration: Decodable {
    let canvasPx: [CGFloat]
    let footAnchorPx: [CGFloat]
    let referenceHeightPx: CGFloat
    let layers: [String]

    static func load() -> MeadowBattleActorConfiguration? {
        guard let data = NSDataAsset(name: "MeadowBattleHeroConfiguration")?.data else { return nil }
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
                    UIImage(named: name)?.draw(in: CGRect(origin: .zero, size: configuration.canvasSize))
                }
            }
        } else {
            silhouette = nil
        }
        super.init(frame: frame)
        images.forEach(addSubview)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func layoutSubviews() {
        super.layoutSubviews()
        images.forEach { $0.frame = bounds }
    }
}

/// Low-opacity source-silhouette projection plus small, soft planted-foot
/// contacts. The cast goes down-right, matching the scene's upper-left light.
final class MeadowBattleGroundingView: UIView {
    struct Contact {
        let point: CGPoint
        let radius: CGFloat
    }
    var spriteFrame: CGRect = .zero { didSet { setNeedsDisplay() } }
    private let source: UIImage?
    private let soleY: CGFloat
    private let contacts: [Contact]

    init(image: UIImage?, soleY: CGFloat, contacts: [Contact]) {
        source = image?.withTintColor(UIColor(red: 0.07, green: 0.10, blue: 0.07, alpha: 0.16), renderingMode: .alwaysOriginal)
        self.soleY = soleY
        self.contacts = contacts
        super.init(frame: .zero)
        isOpaque = false
        isUserInteractionEnabled = false
        contentMode = .redraw
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func draw(_ rect: CGRect) {
        guard let source, let context = UIGraphicsGetCurrentContext(), spriteFrame.width > 0 else { return }
        context.saveGState()
        context.translateBy(x: spriteFrame.minX, y: spriteFrame.minY)
        context.scaleBy(x: spriteFrame.width / source.size.width, y: spriteFrame.height / source.size.height)
        context.saveGState()
        context.concatenate(CGAffineTransform(a: 1, b: 0, c: -0.38, d: -0.15,
                                              tx: soleY * 0.38, ty: soleY * 1.15))
        context.interpolationQuality = .high
        context.setShadow(offset: .zero, blur: 2, color: UIColor.black.withAlphaComponent(0.10).cgColor)
        source.draw(at: .zero)
        context.restoreGState()
        let colors = [UIColor(red: 0.05, green: 0.08, blue: 0.04, alpha: 0.42).cgColor,
                      UIColor.black.withAlphaComponent(0).cgColor] as CFArray
        if let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(), colors: colors, locations: [0, 1]) {
            for contact in contacts {
                context.saveGState()
                context.translateBy(x: contact.point.x, y: contact.point.y)
                context.scaleBy(x: 1, y: 0.25)
                context.drawRadialGradient(gradient, startCenter: .zero, startRadius: 0,
                                           endCenter: .zero, endRadius: contact.radius, options: [])
                context.restoreGState()
            }
        }
        context.restoreGState()
    }
}
