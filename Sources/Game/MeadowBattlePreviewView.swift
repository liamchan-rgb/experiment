import UIKit

/// Side-view environment study that keeps the Meadow Journey art vocabulary:
/// the ground, trees, stones, flowers and atmosphere all come from the map.
/// The contact pose is shown as a candidate so this screen does not imply art approval.
final class MeadowBattlePreviewView: UIView {
    var onClose: (() -> Void)?

    private let title = UILabel()
    private let detail = UILabel()
    private let closeButton = UIButton(type: .system)
    private let landscape = MeadowBattleLandscapeView()
    private let notes = UILabel()
    private let footer = UIView()

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = UIColor(red: 0.09, green: 0.13, blue: 0.12, alpha: 1)
        accessibilityIdentifier = "meadowBattlePreview"

        title.text = "战斗场景试验"
        title.font = .systemFont(ofSize: 24, weight: .bold)
        title.textColor = UIColor(red: 0.98, green: 0.92, blue: 0.75, alpha: 1)
        title.adjustsFontSizeToFitWidth = true
        title.minimumScaleFactor = 0.8
        addSubview(title)

        detail.text = "Meadow Journey 林地资源 · 横向战斗镜头"
        detail.font = .systemFont(ofSize: 15, weight: .medium)
        detail.textColor = UIColor(red: 0.72, green: 0.78, blue: 0.68, alpha: 1)
        detail.adjustsFontSizeToFitWidth = true
        detail.minimumScaleFactor = 0.75
        addSubview(detail)

        var closeStyle = UIButton.Configuration.filled()
        closeStyle.title = "返回地图"
        closeStyle.baseBackgroundColor = UIColor(red: 0.89, green: 0.78, blue: 0.55, alpha: 1)
        closeStyle.baseForegroundColor = UIColor(red: 0.20, green: 0.24, blue: 0.17, alpha: 1)
        closeStyle.contentInsets = NSDirectionalEdgeInsets(top: 6, leading: 12, bottom: 6, trailing: 12)
        closeButton.configuration = closeStyle
        closeButton.accessibilityIdentifier = "closeBattlePreview"
        closeButton.addAction(UIAction { [weak self] _ in self?.onClose?() }, for: .touchUpInside)
        addSubview(closeButton)

        landscape.accessibilityIdentifier = "battleLandscape"
        landscape.isAccessibilityElement = true
        landscape.accessibilityLabel = "Meadow Journey 林地横版战斗场景预览。沿用地图草地、松树、阔叶树、岩石、花丛与暖色日光、空气雾和微粒。人物为待审核的单帧侧视候选；敌方位置为占位标记。"
        addSubview(landscape)

        footer.backgroundColor = UIColor(red: 0.14, green: 0.20, blue: 0.17, alpha: 0.96)
        footer.layer.cornerRadius = 14
        footer.layer.borderWidth = 1
        footer.layer.borderColor = UIColor(red: 0.71, green: 0.61, blue: 0.40, alpha: 0.34).cgColor
        addSubview(footer)

        notes.text = "本轮只检查战场环境与镜头：地图原有地表和植被资源，配合 MeadowJourney 的暖光、雾层、微粒与接地阴影。人物单帧仍是候选，敌方素材、完整动作和规则演出尚未接入。"
        notes.font = .systemFont(ofSize: 15, weight: .medium)
        notes.textColor = UIColor(red: 0.89, green: 0.89, blue: 0.79, alpha: 1)
        notes.numberOfLines = 0
        notes.adjustsFontSizeToFitWidth = true
        notes.minimumScaleFactor = 0.78
        footer.addSubview(notes)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func layoutSubviews() {
        super.layoutSubviews()
        let inset: CGFloat = 18
        let buttonWidth: CGFloat = 106
        title.frame = CGRect(x: inset, y: 18, width: max(140, bounds.width - inset * 3 - buttonWidth), height: 32)
        detail.frame = CGRect(x: inset, y: title.frame.maxY + 2, width: max(140, bounds.width - inset * 3 - buttonWidth), height: 24)
        closeButton.frame = CGRect(x: bounds.width - inset - buttonWidth, y: 20, width: buttonWidth, height: 38)

        let stageWidth = max(1, bounds.width - inset * 2)
        let stageHeight = min(stageWidth * 9 / 16, bounds.height * 0.58)
        landscape.frame = CGRect(x: inset, y: detail.frame.maxY + 18, width: stageWidth, height: stageHeight)
        let notesY = landscape.frame.maxY + 16
        footer.frame = CGRect(x: inset, y: notesY, width: stageWidth,
                              height: max(96, bounds.height - notesY - 20))
        notes.frame = footer.bounds.insetBy(dx: 14, dy: 12)
    }
}

private final class MeadowBattleLandscapeView: UIView {
    private struct Prop {
        let view: UIImageView
        let rect: CGRect
        let alpha: CGFloat
    }

    private let sky = CAGradientLayer()
    private let ground = UIImageView(image: UIImage(named: "MeadowGround"))
    private let groundMask = CAGradientLayer()
    private let sunGlow = UIImageView(image: Self.makeSunGlow())
    private let sunWash = CAGradientLayer()
    private let pathFill = CAShapeLayer()
    private let pathEdge = CAShapeLayer()
    private let pebblesLight = CAShapeLayer()
    private let pebblesDark = CAShapeLayer()
    private let contactShadow = CAShapeLayer()
    private let targetGlow = CAShapeLayer()
    private let targetRing = CAShapeLayer()
    private let targetCross = CAShapeLayer()
    private let hero = UIImageView(image: UIImage(named: "BattleHeroContactCandidate"))
    private let backHaze = CAGradientLayer()
    private let frontHaze = CAGradientLayer()
    private let motes = CAEmitterLayer()
    private let propViews: [Prop]

    override init(frame: CGRect) {
        let pineFar = UIImageView(image: UIImage(named: "Pines"))
        let oakFar = UIImageView(image: UIImage(named: "OakA"))
        let pineRight = UIImageView(image: UIImage(named: "Pines"))
        let oakRight = UIImageView(image: UIImage(named: "OakB"))
        let rockLeft = UIImageView(image: UIImage(named: "RockLow"))
        let rockRight = UIImageView(image: UIImage(named: "RockHigh"))
        let flowersLeft = UIImageView(image: UIImage(named: "Flowers"))
        let flowersRight = UIImageView(image: UIImage(named: "Shrub"))
        propViews = [
            Prop(view: pineFar, rect: CGRect(x: -0.02, y: 0.16, width: 0.24, height: 0.64), alpha: 0.50),
            Prop(view: oakFar, rect: CGRect(x: 0.16, y: 0.28, width: 0.22, height: 0.47), alpha: 0.46),
            Prop(view: pineRight, rect: CGRect(x: 0.66, y: 0.18, width: 0.22, height: 0.60), alpha: 0.50),
            Prop(view: oakRight, rect: CGRect(x: 0.80, y: 0.25, width: 0.23, height: 0.52), alpha: 0.56),
            Prop(view: rockLeft, rect: CGRect(x: -0.02, y: 0.62, width: 0.20, height: 0.28), alpha: 0.94),
            Prop(view: rockRight, rect: CGRect(x: 0.82, y: 0.59, width: 0.20, height: 0.30), alpha: 0.94),
            Prop(view: flowersLeft, rect: CGRect(x: 0.04, y: 0.70, width: 0.17, height: 0.24), alpha: 0.95),
            Prop(view: flowersRight, rect: CGRect(x: 0.80, y: 0.71, width: 0.16, height: 0.22), alpha: 0.94)
        ]
        super.init(frame: frame)
        clipsToBounds = true
        layer.cornerRadius = 14
        layer.borderWidth = 1
        layer.borderColor = UIColor(red: 0.91, green: 0.81, blue: 0.58, alpha: 0.7).cgColor

        sky.colors = [
            UIColor(red: 0.15, green: 0.25, blue: 0.29, alpha: 1).cgColor,
            UIColor(red: 0.39, green: 0.49, blue: 0.40, alpha: 1).cgColor,
            UIColor(red: 0.70, green: 0.60, blue: 0.37, alpha: 1).cgColor
        ]
        sky.locations = [0, 0.53, 1]
        sky.startPoint = CGPoint(x: 0.4, y: 0)
        sky.endPoint = CGPoint(x: 0.62, y: 1)
        layer.addSublayer(sky)

        ground.contentMode = .scaleAspectFill
        ground.layer.magnificationFilter = .linear
        groundMask.startPoint = CGPoint(x: 0.5, y: 0)
        groundMask.endPoint = CGPoint(x: 0.5, y: 1)
        groundMask.colors = [UIColor.clear.cgColor, UIColor.white.withAlphaComponent(0.55).cgColor, UIColor.white.cgColor]
        groundMask.locations = [0, 0.43, 0.70]
        ground.layer.mask = groundMask
        addSubview(ground)

        sunGlow.contentMode = .scaleToFill
        sunGlow.alpha = 0.72
        sunGlow.layer.compositingFilter = "screenBlendMode"
        addSubview(sunGlow)

        sunWash.colors = [
            UIColor(red: 1, green: 0.89, blue: 0.61, alpha: 0.22).cgColor,
            UIColor(red: 1, green: 0.86, blue: 0.56, alpha: 0.08).cgColor,
            UIColor.clear.cgColor
        ]
        sunWash.startPoint = CGPoint(x: 0, y: 0)
        sunWash.endPoint = CGPoint(x: 1, y: 1)
        layer.addSublayer(sunWash)

        for prop in propViews {
            prop.view.contentMode = .scaleAspectFit
            prop.view.alpha = prop.alpha
            prop.view.isAccessibilityElement = false
            prop.view.layer.minificationFilter = .linear
            addSubview(prop.view)
        }

        pathFill.fillColor = UIColor(red: 0.39, green: 0.31, blue: 0.18, alpha: 0.74).cgColor
        pathEdge.fillColor = UIColor.clear.cgColor
        pathEdge.strokeColor = UIColor(red: 0.74, green: 0.60, blue: 0.35, alpha: 0.35).cgColor
        pathEdge.lineWidth = 2
        pebblesLight.fillColor = UIColor(red: 0.91, green: 0.77, blue: 0.48, alpha: 0.36).cgColor
        pebblesDark.fillColor = UIColor(red: 0.25, green: 0.23, blue: 0.14, alpha: 0.32).cgColor
        for shape in [pathFill, pathEdge, pebblesDark, pebblesLight] { layer.addSublayer(shape) }

        contactShadow.fillColor = UIColor(red: 0.05, green: 0.08, blue: 0.07, alpha: 0.52).cgColor
        contactShadow.strokeColor = UIColor.clear.cgColor
        contactShadow.shadowColor = UIColor.black.cgColor
        contactShadow.shadowOpacity = 0.28
        contactShadow.shadowRadius = 9
        contactShadow.shadowOffset = CGSize(width: 0, height: 3)
        layer.addSublayer(contactShadow)

        hero.contentMode = .scaleAspectFit
        hero.isAccessibilityElement = false
        hero.layer.minificationFilter = .linear
        hero.layer.magnificationFilter = .nearest
        addSubview(hero)

        targetGlow.fillColor = UIColor(red: 1, green: 0.82, blue: 0.39, alpha: 0.13).cgColor
        targetRing.fillColor = UIColor.clear.cgColor
        targetRing.strokeColor = UIColor(red: 1, green: 0.88, blue: 0.59, alpha: 0.90).cgColor
        targetRing.lineWidth = 2
        targetCross.fillColor = UIColor.clear.cgColor
        targetCross.strokeColor = UIColor(red: 1, green: 0.88, blue: 0.59, alpha: 0.70).cgColor
        targetCross.lineWidth = 1
        for shape in [targetGlow, targetRing, targetCross] { layer.addSublayer(shape) }

        backHaze.colors = [
            UIColor(red: 0.66, green: 0.79, blue: 0.77, alpha: 0).cgColor,
            UIColor(red: 0.69, green: 0.80, blue: 0.78, alpha: 0.22).cgColor,
            UIColor(red: 0.78, green: 0.83, blue: 0.72, alpha: 0).cgColor
        ]
        backHaze.startPoint = CGPoint(x: 0, y: 0.5)
        backHaze.endPoint = CGPoint(x: 1, y: 0.5)
        layer.addSublayer(backHaze)
        let drift = CABasicAnimation(keyPath: "transform.translation.x")
        drift.fromValue = -22
        drift.toValue = 22
        drift.duration = 12
        drift.autoreverses = true
        drift.repeatCount = .infinity
        backHaze.add(drift, forKey: "meadow-mist-drift")

        frontHaze.colors = [
            UIColor(red: 0.88, green: 0.81, blue: 0.61, alpha: 0).cgColor,
            UIColor(red: 0.88, green: 0.81, blue: 0.61, alpha: 0.18).cgColor,
            UIColor(red: 0.88, green: 0.81, blue: 0.61, alpha: 0.02).cgColor
        ]
        frontHaze.startPoint = CGPoint(x: 0.5, y: 0)
        frontHaze.endPoint = CGPoint(x: 0.5, y: 1)
        layer.addSublayer(frontHaze)

        let particle = Self.makeSunGlow().cgImage
        let cell = CAEmitterCell()
        cell.contents = particle
        cell.contentsScale = UIScreen.main.scale
        cell.birthRate = 2
        cell.lifetime = 8
        cell.lifetimeRange = 2
        cell.velocity = 7
        cell.velocityRange = 5
        cell.emissionLongitude = -.pi / 2
        cell.emissionRange = .pi / 3
        cell.alphaSpeed = -0.035
        cell.scale = 0.035
        cell.scaleRange = 0.025
        cell.color = UIColor(red: 1, green: 0.86, blue: 0.52, alpha: 0.64).cgColor
        motes.emitterShape = .rectangle
        motes.emitterMode = .surface
        motes.renderMode = .additive
        motes.emitterCells = [cell]
        layer.addSublayer(motes)

        let tag = UILabel()
        tag.text = "姿势候选 · 单帧"
        tag.font = .systemFont(ofSize: 12, weight: .bold)
        tag.textColor = UIColor(red: 0.18, green: 0.23, blue: 0.16, alpha: 1)
        tag.textAlignment = .center
        tag.backgroundColor = UIColor(red: 0.97, green: 0.90, blue: 0.70, alpha: 0.94)
        tag.layer.cornerRadius = 9
        tag.clipsToBounds = true
        tag.accessibilityElementsHidden = true
        addSubview(tag)
        self.heroTag = tag

        let targetLabel = UILabel()
        targetLabel.text = "目标位置占位"
        targetLabel.font = .systemFont(ofSize: 11, weight: .semibold)
        targetLabel.textColor = UIColor(red: 0.21, green: 0.25, blue: 0.18, alpha: 1)
        targetLabel.textAlignment = .center
        targetLabel.backgroundColor = UIColor(red: 0.97, green: 0.90, blue: 0.70, alpha: 0.86)
        targetLabel.layer.cornerRadius = 8
        targetLabel.clipsToBounds = true
        targetLabel.accessibilityElementsHidden = true
        addSubview(targetLabel)
        self.targetTag = targetLabel
    }

    private var heroTag: UILabel!
    private var targetTag: UILabel!

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func layoutSubviews() {
        super.layoutSubviews()
        let w = bounds.width
        let h = bounds.height
        sky.frame = bounds
        ground.frame = bounds
        groundMask.frame = bounds
        sunWash.frame = bounds
        sunGlow.frame = CGRect(x: -w * 0.10, y: -h * 0.38, width: w * 0.70, height: h * 1.18)
        for prop in propViews {
            prop.view.frame = CGRect(x: prop.rect.minX * w, y: prop.rect.minY * h,
                                     width: prop.rect.width * w, height: prop.rect.height * h)
        }

        let road = UIBezierPath()
        road.move(to: CGPoint(x: 0, y: h * 0.76))
        road.addCurve(to: CGPoint(x: w, y: h * 0.74),
                      controlPoint1: CGPoint(x: w * 0.28, y: h * 0.70),
                      controlPoint2: CGPoint(x: w * 0.70, y: h * 0.82))
        road.addLine(to: CGPoint(x: w, y: h))
        road.addLine(to: CGPoint(x: 0, y: h))
        road.close()
        pathFill.path = road.cgPath

        let crest = UIBezierPath()
        crest.move(to: CGPoint(x: 0, y: h * 0.76))
        crest.addCurve(to: CGPoint(x: w, y: h * 0.74),
                       controlPoint1: CGPoint(x: w * 0.28, y: h * 0.70),
                       controlPoint2: CGPoint(x: w * 0.70, y: h * 0.82))
        pathEdge.path = crest.cgPath

        let lightPebbles = UIBezierPath()
        let darkPebbles = UIBezierPath()
        for index in 0..<54 {
            let x = CGFloat((index * 37 + 11) % 97) / 97 * w
            let y = h * (0.79 + CGFloat((index * 19 + 5) % 20) / 100)
            let radius = CGFloat(1 + (index % 3))
            let pebble = UIBezierPath(ovalIn: CGRect(x: x, y: y, width: radius * 2, height: radius))
            (index % 3 == 0 ? darkPebbles : lightPebbles).append(pebble)
        }
        pebblesLight.path = lightPebbles.cgPath
        pebblesDark.path = darkPebbles.cgPath

        let actorGroundY = h * 0.79
        contactShadow.path = UIBezierPath(ovalIn: CGRect(x: w * 0.20, y: actorGroundY - h * 0.018,
                                                         width: w * 0.30, height: h * 0.045)).cgPath
        hero.frame = CGRect(x: w * 0.105, y: h * 0.075, width: w * 0.44, height: h * 0.80)

        let targetCenter = CGPoint(x: w * 0.61, y: actorGroundY - h * 0.075)
        let radius = w * 0.035
        targetGlow.path = UIBezierPath(ovalIn: CGRect(x: targetCenter.x - radius * 1.55,
                                                     y: targetCenter.y - radius * 1.55,
                                                     width: radius * 3.1, height: radius * 3.1)).cgPath
        targetRing.path = UIBezierPath(ovalIn: CGRect(x: targetCenter.x - radius,
                                                     y: targetCenter.y - radius,
                                                     width: radius * 2, height: radius * 2)).cgPath
        let cross = UIBezierPath()
        cross.move(to: CGPoint(x: targetCenter.x - radius * 1.3, y: targetCenter.y))
        cross.addLine(to: CGPoint(x: targetCenter.x + radius * 1.3, y: targetCenter.y))
        cross.move(to: CGPoint(x: targetCenter.x, y: targetCenter.y - radius * 1.3))
        cross.addLine(to: CGPoint(x: targetCenter.x, y: targetCenter.y + radius * 1.3))
        targetCross.path = cross.cgPath

        backHaze.frame = CGRect(x: -w * 0.12, y: h * 0.34, width: w * 1.24, height: h * 0.30)
        frontHaze.frame = CGRect(x: 0, y: h * 0.73, width: w, height: h * 0.27)
        motes.frame = bounds
        motes.emitterPosition = CGPoint(x: w * 0.5, y: h * 0.52)
        motes.emitterSize = CGSize(width: w * 0.92, height: h * 0.62)
        heroTag.frame = CGRect(x: w * 0.14, y: h * 0.08, width: w * 0.25, height: 22)
        targetTag.frame = CGRect(x: w * 0.51, y: h * 0.82, width: w * 0.20, height: 20)
    }

    private static func makeSunGlow() -> UIImage {
        let size = CGSize(width: 256, height: 256)
        let renderer = UIGraphicsImageRenderer(size: size)
        return renderer.image { context in
            let center = CGPoint(x: size.width / 2, y: size.height / 2)
            let colors = [
                UIColor(red: 1, green: 0.91, blue: 0.64, alpha: 0.72).cgColor,
                UIColor(red: 1, green: 0.86, blue: 0.58, alpha: 0.30).cgColor,
                UIColor(red: 1, green: 0.83, blue: 0.49, alpha: 0).cgColor
            ] as CFArray
            let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(), colors: colors,
                                      locations: [0, 0.42, 1])!
            context.cgContext.drawRadialGradient(gradient, startCenter: center, startRadius: 0,
                                                 endCenter: center, endRadius: size.width * 0.49, options: [])
        }
    }
}
