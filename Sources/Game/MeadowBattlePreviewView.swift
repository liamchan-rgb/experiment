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
        landscape.accessibilityLabel = "Meadow Journey 营地林地场景，显示一名冒险者与一只史莱姆美术样例；尚未接入真实战斗。"
        addSubview(landscape)
        stageTitle.text = "Meadow Journey · 营地林地"
        stageTitle.textAlignment = .center
        stageTitle.backgroundColor = MeadowPreviewPalette.panel.withAlphaComponent(0.88)
        stageTitle.layer.cornerRadius = 8
        stageTitle.clipsToBounds = true
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
        subtitle.text = mode == .exploration ? "布局演示 · 地图查看" : "布局演示 · 已暂停 · 人物与敌方美术样例"
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
        stageTitle.frame = CGRect(x: 16, y: 12, width: min(246, max(1, landscape.bounds.width - 32)), height: 26)
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

struct MeadowBattleCanvasGeometry {
    static let sourceCanvas = CGSize(width: 1309, height: 1201)
    static let sceneLayerOrder = ["MeadowCampFarForest", "MeadowCampGround", "MeadowCampMidground", "MeadowCampForeground"]
    static let heroVisibleHeight: CGFloat = 0.24
    static let slimeVisibleHeight: CGFloat = 0.17

    static func fittedCanvas(in bounds: CGRect) -> CGRect {
        let scale = min(bounds.width / sourceCanvas.width, bounds.height / sourceCanvas.height)
        let size = CGSize(width: sourceCanvas.width * scale, height: sourceCanvas.height * scale)
        return CGRect(x: bounds.midX - size.width / 2, y: bounds.midY - size.height / 2,
                      width: size.width, height: size.height)
    }

    static func registeredSpriteFrame(imageSize: CGSize, alphaBounds: CGRect, foot: CGPoint,
                                      visibleHeight: CGFloat, canvas: CGRect) -> CGRect {
        let scale = canvas.height * visibleHeight / alphaBounds.height
        let footPoint = CGPoint(x: canvas.minX + canvas.width * foot.x,
                                y: canvas.minY + canvas.height * foot.y)
        return CGRect(x: footPoint.x - (alphaBounds.midX * scale),
                      y: footPoint.y - (alphaBounds.maxY * scale),
                      width: imageSize.width * scale, height: imageSize.height * scale)
    }
}

final class MeadowBattleLandscapeView: UIView {
    private let canvas = UIView()
    private let farForest = UIImageView(image: UIImage(named: "MeadowCampFarForest"))
    private let ground = UIImageView(image: UIImage(named: "MeadowCampGround"))
    private let midground = UIImageView(image: UIImage(named: "MeadowCampMidground"))
    private let foreground = UIImageView(image: UIImage(named: "MeadowCampForeground"))
    private let hero = UIImageView()
    private let slime = UIImageView(image: UIImage(named: "MeadowBattleSlime"))
    private let heroShadow = UIView()
    private let slimeShadow = UIView()
    private var sceneLayers: [UIImageView] { [farForest, ground, midground, foreground] }

    var sceneLayerOrder: [String] { sceneLayers.compactMap(\.accessibilityIdentifier) }
    var sceneLayerFrames: [CGRect] { sceneLayers.map(\.frame) }
    var sceneCanvasFrame: CGRect { canvas.frame }
    var sceneCanvasSubviewOrder: [String] { canvas.subviews.compactMap(\.accessibilityIdentifier) }
    var heroViewFrame: CGRect { hero.frame }
    var slimeViewFrame: CGRect { slime.frame }
    var slimeFacesLeft: Bool { slime.transform.a < 0 }

    override init(frame: CGRect) {
        let atlas = UIImage(named: "Hero1Directions")?.cgImage
        let cellSize = 256
        let rightIdle = atlas?.cropping(to: CGRect(x: 0, y: cellSize * 3,
                                                   width: cellSize, height: cellSize))
        super.init(frame: frame)
        if let rightIdle { hero.image = UIImage(cgImage: rightIdle) }
        clipsToBounds = true
        layer.cornerRadius = 14
        layer.borderWidth = 1
        layer.borderColor = UIColor(red: 0.91, green: 0.81, blue: 0.58, alpha: 0.7).cgColor

        canvas.clipsToBounds = true
        canvas.accessibilityIdentifier = "meadowBattleSceneCanvas"
        addSubview(canvas)
        for (index, imageView) in sceneLayers.enumerated() {
            imageView.accessibilityIdentifier = MeadowBattleCanvasGeometry.sceneLayerOrder[index]
            imageView.contentMode = .scaleToFill
            imageView.isAccessibilityElement = false
            imageView.layer.minificationFilter = .linear
            imageView.layer.magnificationFilter = .linear
            canvas.addSubview(imageView)
        }
        configureShadow(heroShadow, identifier: "meadowBattleHeroShadow")
        configureShadow(slimeShadow, identifier: "meadowBattleSlimeShadow")
        canvas.addSubview(heroShadow)
        canvas.addSubview(slimeShadow)

        hero.accessibilityIdentifier = "meadowBattleHero"
        hero.isAccessibilityElement = true
        hero.accessibilityLabel = "Meadow Journey 冒险者，向右待机姿态"
        hero.contentMode = .scaleToFill
        hero.layer.minificationFilter = .nearest
        hero.layer.magnificationFilter = .nearest
        canvas.addSubview(hero)

        slime.accessibilityIdentifier = "meadowBattleSlime"
        slime.isAccessibilityElement = true
        slime.accessibilityLabel = "史莱姆敌方单位示意"
        slime.contentMode = .scaleToFill
        slime.transform = CGAffineTransform(scaleX: -1, y: 1)
        slime.layer.minificationFilter = .nearest
        slime.layer.magnificationFilter = .nearest
        canvas.addSubview(slime)

        canvas.addSubview(foreground)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private func configureShadow(_ shadow: UIView, identifier: String) {
        shadow.accessibilityIdentifier = identifier
        shadow.isUserInteractionEnabled = false
        shadow.backgroundColor = UIColor(red: 0.08, green: 0.10, blue: 0.07, alpha: 0.42)
        shadow.layer.cornerRadius = 100
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.width > 0, bounds.height > 0 else { return }
        let fitted = MeadowBattleCanvasGeometry.fittedCanvas(in: bounds)
        canvas.frame = fitted
        let canvasBounds = canvas.bounds
        sceneLayers.forEach { $0.frame = canvasBounds }

        let heroFrame = MeadowBattleCanvasGeometry.registeredSpriteFrame(
            imageSize: CGSize(width: 256, height: 256),
            alphaBounds: CGRect(x: 87, y: 68, width: 83, height: 156),
            foot: CGPoint(x: 0.30, y: 0.69), visibleHeight: MeadowBattleCanvasGeometry.heroVisibleHeight,
            canvas: canvasBounds)
        hero.frame = heroFrame
        let slimeFrame = MeadowBattleCanvasGeometry.registeredSpriteFrame(
            imageSize: slime.image.map { CGSize(width: $0.size.width, height: $0.size.height) } ?? CGSize(width: 1024, height: 1024),
            alphaBounds: CGRect(x: 179, y: 207, width: 642, height: 648),
            foot: CGPoint(x: 0.76, y: 0.685), visibleHeight: MeadowBattleCanvasGeometry.slimeVisibleHeight,
            canvas: canvasBounds)
        slime.frame = slimeFrame

        let heroFoot = CGPoint(x: canvasBounds.width * 0.30, y: canvasBounds.height * 0.69)
        let slimeFoot = CGPoint(x: canvasBounds.width * 0.76, y: canvasBounds.height * 0.685)
        heroShadow.frame = CGRect(x: heroFoot.x - heroFrame.width * 0.21,
                                  y: heroFoot.y - max(2, canvasBounds.height * 0.006),
                                  width: heroFrame.width * 0.42, height: max(4, canvasBounds.height * 0.012))
        slimeShadow.frame = CGRect(x: slimeFoot.x - slimeFrame.width * 0.22,
                                   y: slimeFoot.y - max(2, canvasBounds.height * 0.006),
                                   width: slimeFrame.width * 0.44, height: max(4, canvasBounds.height * 0.012))
    }
}
