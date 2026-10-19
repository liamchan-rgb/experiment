import UIKit

private enum MeadowPreviewPalette {
    static let panel = UIColor(red: 0.10, green: 0.17, blue: 0.13, alpha: 0.97)
    static let card = UIColor(red: 0.17, green: 0.25, blue: 0.19, alpha: 1)
    static let ink = UIColor(red: 0.98, green: 0.93, blue: 0.77, alpha: 1)
    static let muted = UIColor(red: 0.72, green: 0.79, blue: 0.66, alpha: 1)
    static let gold = UIColor(red: 0.92, green: 0.77, blue: 0.42, alpha: 1)
    static let border = UIColor(red: 0.60, green: 0.57, blue: 0.34, alpha: 0.65)
    static func stylePanel(_ view: UIView) {
        view.backgroundColor = panel
        view.layer.cornerRadius = 14
        view.layer.borderWidth = 1
        view.layer.borderColor = border.cgColor
    }
    static func label(_ text: String, size: CGFloat, weight: UIFont.Weight = .medium) -> UILabel {
        let label = UILabel(); label.text = text
        label.font = .systemFont(ofSize: size, weight: weight)
        label.textColor = ink; label.adjustsFontSizeToFitWidth = true; label.minimumScaleFactor = 0.85
        return label
    }
}

/// Presentation-only fixture. It does not drive turns, damage, inventory or map movement.
/// The small header badge distinguishes the layout sample from a real battle.
final class MeadowBattlePreviewView: UIView {
    var onClose: (() -> Void)?
    var onLayoutChanged: (() -> Void)?
    private(set) var mode: MeadowBattlePreviewMode = .playerTurn
    // Query the current mode directly. UIViewController's layout callback may
    // precede this child's layout pass when a footer is hidden or revealed.
    var mapFrame: CGRect {
        MeadowBattleLayout(size: bounds.size, safeArea: safeAreaInsets, mode: mode).map
    }
    private let header = UIView()
    private let actor = MeadowPreviewPalette.label("", size: 23, weight: .bold)
    private let subtitle = MeadowPreviewPalette.label("", size: 13)
    private let modeControl = UISegmentedControl(items: ["探索", "玩家回合", "怪物回合"])
    private let closeButton = UIButton(type: .system)
    private let landscape = MeadowBattleLandscapeView()
    private let mapBorder = UIView()
    private let mapTitle = MeadowPreviewPalette.label("Meadow Journey", size: 15, weight: .semibold)
    private let stageTitle = MeadowPreviewPalette.label("Meadow Journey · 林地", size: 17, weight: .semibold)
    private let track = MeadowTurnTrackView()
    private let details = MeadowPlayerDetailsView()

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .clear
        accessibilityIdentifier = "meadowBattlePreview"
        MeadowPreviewPalette.stylePanel(header)
        header.accessibilityIdentifier = "battlePreviewHeader"
        addSubview(header)
        actor.accessibilityIdentifier = "previewCurrentActor"
        header.addSubview(actor); header.addSubview(subtitle)
        subtitle.textColor = MeadowPreviewPalette.muted
        modeControl.accessibilityIdentifier = "battlePreviewMode"
        modeControl.selectedSegmentIndex = mode.rawValue
        modeControl.selectedSegmentTintColor = MeadowPreviewPalette.gold
        modeControl.setTitleTextAttributes([.foregroundColor: MeadowPreviewPalette.ink], for: .normal)
        modeControl.setTitleTextAttributes([.foregroundColor: MeadowPreviewPalette.panel], for: .selected)
        modeControl.addTarget(self, action: #selector(changeMode), for: .valueChanged)
        header.addSubview(modeControl)
        var style = UIButton.Configuration.filled(); style.title = "返回地图"
        style.baseBackgroundColor = MeadowPreviewPalette.gold
        style.baseForegroundColor = MeadowPreviewPalette.panel
        closeButton.configuration = style
        closeButton.accessibilityIdentifier = "closeBattlePreview"
        closeButton.addAction(UIAction { [weak self] _ in self?.onClose?() }, for: .touchUpInside)
        header.addSubview(closeButton)
        mapBorder.layer.cornerRadius = 14; mapBorder.layer.borderWidth = 1
        mapBorder.layer.borderColor = MeadowPreviewPalette.border.cgColor
        mapBorder.isUserInteractionEnabled = false; addSubview(mapBorder)
        mapTitle.backgroundColor = MeadowPreviewPalette.panel
        mapTitle.textAlignment = .center; mapTitle.layer.cornerRadius = 8; mapTitle.clipsToBounds = true
        mapTitle.isUserInteractionEnabled = false; addSubview(mapTitle)
        landscape.accessibilityIdentifier = "battleLandscape"
        landscape.isAccessibilityElement = true
        landscape.accessibilityLabel = "Meadow Journey 林地横版战场。单帧人物候选与目标占位，尚未接入真实战斗。"
        addSubview(landscape)
        stageTitle.isUserInteractionEnabled = false; landscape.addSubview(stageTitle)
        track.accessibilityIdentifier = "previewTurnTrack"; addSubview(track)
        details.accessibilityIdentifier = "previewPlayerDetails"; addSubview(details)
        updateMode()
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    @objc private func changeMode() {
        mode = MeadowBattlePreviewMode(rawValue: modeControl.selectedSegmentIndex) ?? .playerTurn
        updateMode(); setNeedsLayout(); onLayoutChanged?()
    }
    private func updateMode() {
        actor.text = mode == .exploration ? "探索 · Meadow Journey"
            : mode == .playerTurn ? "第1轮 · 行动中：P1 冒险者" : "第1轮 · 行动中：敌1"
        subtitle.text = mode == .exploration ? "布局演示 · 地图查看" : "布局演示 · 已暂停 · 单帧动作样片"
        landscape.isHidden = !mode.showsBattle
        track.isHidden = !mode.showsBattle
        details.isHidden = !mode.showsDetails
        track.show(monsterTurn: mode == .monsterTurn)
    }
    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.width > 0, bounds.height > 0 else { return }
        let layout = MeadowBattleLayout(size: bounds.size, safeArea: safeAreaInsets, mode: mode)
        header.frame = layout.header
        mapBorder.frame = mapFrame
        mapTitle.frame = CGRect(x: mapFrame.minX + 12, y: mapFrame.minY + 12, width: 154, height: 28)
        landscape.frame = layout.battlefield; track.frame = layout.track; details.frame = layout.details
        stageTitle.frame = CGRect(x: 16, y: 12, width: max(1, landscape.bounds.width - 32), height: 26)
        let buttonWidth: CGFloat = 104
        let selectorWidth = min(292, header.bounds.width * 0.29)
        closeButton.frame = CGRect(x: header.bounds.width - buttonWidth - 12, y: (header.bounds.height - 44) / 2,
                                   width: buttonWidth, height: 44)
        modeControl.frame = CGRect(x: closeButton.frame.minX - selectorWidth - 12, y: closeButton.frame.minY,
                                   width: selectorWidth, height: 44)
        let textWidth = max(1, modeControl.frame.minX - 28)
        actor.frame = CGRect(x: 16, y: 9, width: textWidth, height: 27)
        subtitle.frame = CGRect(x: 16, y: 38, width: textWidth, height: 18)
    }
    override func hitTest(_ point: CGPoint, with event: UIEvent?) -> UIView? {
        // The live map sits below this shell; leave its gestures in the real renderer.
        if mapFrame.contains(point) { return nil }
        return super.hitTest(point, with: event)
    }
}

private final class MeadowTurnTrackView: UIView {
    private let line = CAShapeLayer()
    private let completed = CAShapeLayer()
    private let ids = ["P2", "敌2", "P3", "P1", "敌1", "P4", "P5", "P6", "敌3", "P7"]
    private var tokens: [MeadowTurnTokenView] = []
    private var current = 3
    override init(frame: CGRect) {
        super.init(frame: frame); MeadowPreviewPalette.stylePanel(self)
        line.strokeColor = MeadowPreviewPalette.muted.withAlphaComponent(0.35).cgColor; line.lineWidth = 5
        completed.strokeColor = MeadowPreviewPalette.gold.cgColor; completed.lineWidth = 5
        layer.addSublayer(line); layer.addSublayer(completed)
        for id in ids {
            let token = MeadowTurnTokenView(id: id); tokens.append(token); addSubview(token)
        }
        show(monsterTurn: false)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    func show(monsterTurn: Bool) {
        current = monsterTurn ? 4 : 3
        for (index, token) in tokens.enumerated() {
            token.show(current: index == current, done: index < current,
                       badge: ids[index] == "P5" ? "×" : ids[index] == "P6" ? "◷" : "")
        }
        setNeedsLayout()
    }
    override func layoutSubviews() {
        super.layoutSubviews()
        let step = bounds.width / CGFloat(tokens.count)
        guard bounds.width > 0, bounds.height > 0 else { return }
        let y = min(34, bounds.height * 0.46)
        let path = UIBezierPath(); path.move(to: CGPoint(x: step / 2, y: y))
        path.addLine(to: CGPoint(x: bounds.width - step / 2, y: y)); line.path = path.cgPath
        let done = UIBezierPath(); done.move(to: CGPoint(x: step / 2, y: y))
        done.addLine(to: CGPoint(x: step * (CGFloat(current) + 0.5), y: y)); completed.path = done.cgPath
        for (index, token) in tokens.enumerated() {
            token.frame = CGRect(x: CGFloat(index) * step, y: 0, width: step, height: bounds.height)
        }
    }
}

private final class MeadowTurnTokenView: UIView {
    private let circle = UIView()
    private let portrait = UIImageView()
    private let name: UILabel
    private let marker = MeadowPreviewPalette.label("▼", size: 11, weight: .bold)
    private let badge = MeadowPreviewPalette.label("", size: 17, weight: .bold)
    private let id: String
    private static let portraits: [UIImage?] = (1...3).map { index in
        guard let atlas = UIImage(named: "Hero\(index)Directions")?.cgImage else { return nil }
        let cell = atlas.width / HeroFrames.columns
        return atlas.cropping(to: CGRect(x: 0, y: 0, width: cell, height: cell)).map { UIImage(cgImage: $0) }
    }
    init(id: String) {
        self.id = id; name = MeadowPreviewPalette.label(id, size: 12, weight: .semibold)
        super.init(frame: .zero)
        isAccessibilityElement = true; accessibilityIdentifier = "previewQueue\(id)"
        accessibilityLabel = id
        circle.backgroundColor = MeadowPreviewPalette.card; circle.layer.borderWidth = 1.5
        addSubview(circle); addSubview(portrait); addSubview(name); addSubview(marker); addSubview(badge)
        name.textAlignment = .center; marker.textAlignment = .center; badge.textAlignment = .center
        marker.textColor = MeadowPreviewPalette.gold
        portrait.contentMode = .scaleAspectFit; portrait.layer.magnificationFilter = .nearest
        if id.hasPrefix("P"), let number = Int(id.dropFirst()) {
            portrait.image = Self.portraits[(number - 1) % Self.portraits.count]
        } else {
            portrait.image = UIImage(systemName: "pawprint.fill"); portrait.tintColor = MeadowPreviewPalette.gold
        }
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    func show(current: Bool, done: Bool, badge value: String) {
        marker.isHidden = !current
        circle.layer.borderColor = (current || done ? MeadowPreviewPalette.gold : MeadowPreviewPalette.muted).cgColor
        circle.layer.borderWidth = current ? 3 : 1.5
        badge.text = value.isEmpty && done ? "✓" : value
        badge.textColor = value == "×" ? .systemRed : MeadowPreviewPalette.gold
        portrait.alpha = value == "×" ? 0.38 : 1
        accessibilityValue = current ? "当前行动" : value == "×" ? "倒地" : value == "◷" ? "下轮资格" : done ? "已行动" : "待行动"
    }
    override func layoutSubviews() {
        super.layoutSubviews()
        let side = min(44, bounds.height - 25)
        guard bounds.width > 0, bounds.height > 25 else { return }
        circle.frame = CGRect(x: (bounds.width - side) / 2, y: 12, width: side, height: side)
        circle.layer.cornerRadius = side / 2
        portrait.frame = circle.frame.insetBy(dx: 5, dy: 4)
        marker.frame = CGRect(x: circle.frame.midX - 8, y: 0, width: 16, height: 13)
        badge.frame = CGRect(x: circle.frame.maxX - 10, y: 8, width: 20, height: 20)
        name.frame = CGRect(x: 0, y: circle.frame.maxY + 2, width: bounds.width, height: 16)
    }
}

private final class MeadowPlayerDetailsView: UIView {
    private let resources = MeadowPreviewPalette.label("冒险者    生命 12/12    盾 0    金币 0    积分 0    ● 蓝队", size: 16, weight: .semibold)
    private var cards: [UIView] = []
    override init(frame: CGRect) {
        super.init(frame: frame); MeadowPreviewPalette.stylePanel(self)
        resources.accessibilityIdentifier = "previewResourceValues"; addSubview(resources)
        // Read-only catalog fixture, not the map simulation's inventory or skill state.
        for (title, text) in [
            ("强击 · 1 AP", "射程0 · 1D6+2伤害\n余2次 · 可用"),
            ("喘息 · 1 AP", "自身 · 恢复4生命\n余2次 · 可用"),
            ("简易防护 · 1 AP", "自身 · 获得4护盾\n余2次 · 可用"),
            ("个人物品", "空背包\n尚未持有可用道具")
        ] {
            let card = MeadowPreviewCard(title: title, text: text); addSubview(card); cards.append(card)
        }
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.width > 0, bounds.height > 0 else { return }
        resources.frame = CGRect(x: 14, y: 8, width: max(1, bounds.width - 28), height: 23)
        let gap: CGFloat = 8; let width = max(1, (bounds.width - 28 - gap * 3) / 4)
        for (index, card) in cards.enumerated() {
            card.frame = CGRect(x: 14 + CGFloat(index) * (width + gap), y: 37, width: width, height: max(1, bounds.height - 47))
        }
    }
}

private final class MeadowPreviewCard: UIView {
    private let title: UILabel
    private let detail: UILabel
    init(title: String, text: String) {
        self.title = MeadowPreviewPalette.label(title, size: 17, weight: .bold)
        self.detail = MeadowPreviewPalette.label(text, size: 15)
        super.init(frame: .zero); backgroundColor = MeadowPreviewPalette.card
        layer.cornerRadius = 9; detail.numberOfLines = 2
        addSubview(self.title); addSubview(detail)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.width > 0, bounds.height > 0 else { return }
        title.frame = CGRect(x: 10, y: 6, width: max(1, bounds.width - 20), height: 22)
        detail.frame = CGRect(x: 10, y: 30, width: max(1, bounds.width - 20), height: max(1, bounds.height - 35))
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
    private let sunGlow = UIImageView(image: MeadowBattleLandscapeView.makeSunGlow())
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
        guard w > 0, h > 0 else { return }
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
        // Visible boot edge is y1052 on the original 1254px canvas. Alpha=1
        // noise extends to y1236 and must not be mistaken for the foot anchor.
        let actorSize = min(w * 0.48, h * 0.60)
        hero.frame = CGRect(x: w * 0.105, y: actorGroundY - actorSize * 1052 / 1254,
                            width: actorSize, height: actorSize)
        contactShadow.path = UIBezierPath(ovalIn: CGRect(x: hero.frame.minX + actorSize * 0.04,
            y: actorGroundY - 3, width: actorSize * 0.72, height: max(10, actorSize * 0.06))).cgPath

        let targetCenter = CGPoint(x: w * 0.76, y: actorGroundY - actorSize * 0.12)
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
        heroTag.frame = CGRect(x: 16, y: 44, width: min(170, w - 32), height: 22)
        targetTag.frame = CGRect(x: targetCenter.x - 65, y: actorGroundY + 20, width: 130, height: 20)
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
