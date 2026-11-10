import UIKit
import ClassroomGameCore

/// The turn order of a party battle, made to be read at a glance (it replaces the plain row of dots with a line through them):
///
/// * a banner on the left says whose turn it is, in words and in colour (gold = your side, red = the enemy), with the round number;
/// * the unit acting now is first in the row, larger, with a glowing gold ring and a "行动中" tag;
/// * the unit after it carries a "下一位" tag; the rest wait in order; units that already acted are dimmed and ticked; fallen units are grey;
/// * every unit shows its own face, a green / amber / red health bar and a thin shield line, so this row doubles as the team roster;
/// * tapping a unit selects it as the target (`onSelect`).
///
/// The row re-orders with a short spring when the turn changes, so the eye follows the unit that just acted going to the back.
final class MeadowTurnOrderView: UIView {
    struct Entry {
        let id: String, name: String
        let hp: Int, maxHP: Int, shield: Int
        let enemy: Bool, acted: Bool, down: Bool
    }
    var onSelect: ((String) -> Void)?
    private let banner = UILabel()
    private var tokens: [String: MeadowTurnOrderToken] = [:]
    private var order: [String] = []
    private var currentID: String?
    private var selected: Set<String> = []
    private var chevrons: [UILabel] = []
    private let shine = CAGradientLayer()

    override init(frame: CGRect) {
        super.init(frame: frame); MeadowPreviewPalette.stylePanel(self)
        banner.numberOfLines = 2; banner.textAlignment = .center; banner.layer.cornerRadius = 10; banner.layer.borderWidth = 2; banner.clipsToBounds = true
        addSubview(banner)
        clipsToBounds = true
        shine.colors = [UIColor.clear.cgColor, MeadowPreviewPalette.gold.withAlphaComponent(0.28).cgColor, UIColor.clear.cgColor]
        shine.startPoint = CGPoint(x: 0, y: 0.5); shine.endPoint = CGPoint(x: 1, y: 0.5); shine.opacity = 0; layer.addSublayer(shine)
        accessibilityIdentifier = "meadowTurnOrder"
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    /// `entries` in the battle's queue order. `current` is the unit acting (or about to act); `selected` the units picked as targets.
    func show(entries: [Entry], current: String?, round: Int, selected: Set<String>, finished: String? = nil) {
        let by = Dictionary(uniqueKeysWithValues: entries.map { ($0.id, $0) })
        var ordered: [String] = []
        if let current, by[current] != nil { ordered.append(current) }
        ordered += entries.filter { $0.id != current && !$0.acted && !$0.down }.map(\.id)
        ordered += entries.filter { $0.id != current && $0.acted && !$0.down }.map(\.id)
        ordered += entries.filter { $0.id != current && $0.down }.map(\.id)
        let next = ordered.dropFirst().first { by[$0].map { !$0.acted && !$0.down } ?? false }
        for id in tokens.keys where by[id] == nil { tokens.removeValue(forKey: id)?.removeFromSuperview() }
        for entry in entries where tokens[entry.id] == nil {
            let token = MeadowTurnOrderToken(id: entry.id)
            token.onTap = { [weak self] id in self?.onSelect?(id) }
            tokens[entry.id] = token; addSubview(token)
        }
        for entry in entries {
            let status: MeadowTurnOrderToken.Status = entry.down ? .down : entry.id == current ? .current : entry.id == next ? .next : entry.acted ? .done : .waiting
            tokens[entry.id]?.update(entry, status: status, targeted: selected.contains(entry.id))
        }
        let turnChanged = current != currentID
        let changed = ordered != order || turnChanged
        order = ordered; currentID = current; self.selected = selected
        // The banner: who is acting, which side.
        let enemyTurn = current.flatMap { by[$0]?.enemy } ?? false
        let who = current.flatMap { by[$0]?.name } ?? "—"
        let text: String, color: UIColor
        if let finished { text = finished; color = MeadowPreviewPalette.gold }
        else if enemyTurn { text = "敌方行动\n\(who) · 第\(round)轮"; color = UIColor(red: 0.93, green: 0.40, blue: 0.34, alpha: 1) }
        else { text = "轮到 \(who)\n我方行动 · 第\(round)轮"; color = MeadowPreviewPalette.gold }
        let lines = text.components(separatedBy: "\n")
        let attributed = NSMutableAttributedString(string: lines[0], attributes: [.font: MeadowPreviewPalette.font(19, .heavy), .foregroundColor: color])
        if lines.count > 1 { attributed.append(NSAttributedString(string: "\n" + lines[1], attributes: [.font: MeadowPreviewPalette.font(12, .semibold), .foregroundColor: MeadowPreviewPalette.ink.withAlphaComponent(0.85)])) }
        banner.attributedText = attributed
        banner.layer.borderColor = color.cgColor
        banner.backgroundColor = enemyTurn ? UIColor(red: 0.28, green: 0.09, blue: 0.08, alpha: 1) : UIColor(red: 0.23, green: 0.19, blue: 0.07, alpha: 1)
        banner.accessibilityLabel = text.replacingOccurrences(of: "\n", with: "，")
        if changed, window != nil {
            // The row re-orders on a spring; the banner flips over to the new name; the unit whose turn starts pops.
            UIView.animate(withDuration: 0.5, delay: 0, usingSpringWithDamping: 0.78, initialSpringVelocity: 0.5, options: [.allowUserInteraction, .beginFromCurrentState]) { self.layoutNow() }
            if turnChanged {
                UIView.transition(with: banner, duration: 0.35, options: [.transitionFlipFromTop, .allowUserInteraction], animations: nil)
                if let current { tokens[current]?.pop() }
                sweep()
            }
        } else { layoutNow() }
    }

    private func layoutNow() { setNeedsLayout(); layoutIfNeeded() }

    /// A band of light runs along the row when the turn passes on.
    private func sweep() {
        shine.frame = CGRect(x: 0, y: 0, width: 180, height: bounds.height); shine.opacity = 1
        let run = CABasicAnimation(keyPath: "position.x"); run.fromValue = -90; run.toValue = bounds.width + 90
        let fade = CABasicAnimation(keyPath: "opacity"); fade.fromValue = 1; fade.toValue = 0
        let group = CAAnimationGroup(); group.animations = [run, fade]; group.duration = 0.7; group.timingFunction = CAMediaTimingFunction(name: .easeOut)
        shine.opacity = 0; shine.add(group, forKey: "sweep")
    }

    /// The row always fills the bar, from 1v1 (two wide cards) to 7v3 (ten narrow ones); the acting unit's card is 1.35x as wide.
    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.width > 0, bounds.height > 0 else { return }
        let inset: CGFloat = 8, bannerWidth = min(190, max(120, bounds.width * 0.17))
        banner.frame = CGRect(x: inset, y: 6, width: bannerWidth, height: bounds.height - 12)
        let left = banner.frame.maxX + 10, available = bounds.width - left - inset
        let n = CGFloat(max(1, order.count)), gap: CGFloat = order.count > 7 ? 10 : 16
        let unit = (available - gap * (n - 1)) / (n + 0.35)
        while chevrons.count < max(0, order.count - 1) {
            let mark = UILabel(); mark.text = "›"; mark.textAlignment = .center; mark.font = .systemFont(ofSize: 18, weight: .heavy); mark.textColor = MeadowPreviewPalette.gold.withAlphaComponent(0.7)
            chevrons.append(mark); insertSubview(mark, at: 0)
        }
        var x = left
        let full = bounds.height - 8
        for (i, id) in order.enumerated() {
            guard let token = tokens[id] else { continue }
            let isCurrent = id == currentID && i == 0
            let width = isCurrent ? unit * 1.35 : unit, height = isCurrent ? full : full - 6
            token.frame = CGRect(x: x, y: 4 + (full - height) / 2, width: width, height: height)
            x += width + gap
            if i < chevrons.count { chevrons[i].isHidden = i >= order.count - 1; chevrons[i].frame = CGRect(x: x - gap, y: 0, width: gap, height: bounds.height) }
        }
        for (i, mark) in chevrons.enumerated() where i >= order.count - 1 { mark.isHidden = true }
    }
}

/// One unit in the turn order: a card with its face, name, health (bar and numbers), shield and a status tag. Wide cards lay this out in
/// a row (face left, text right); narrow ones (many units, small screens) stack it.
private final class MeadowTurnOrderToken: UIView {
    enum Status { case current, next, waiting, done, down }
    var onTap: ((String) -> Void)?
    private let id: String
    private let card = UIView(), name = UILabel(), circle = UIView(), portrait = UIImageView(), pill = UILabel(), numbers = UILabel()
    private let hpTrack = UIView(), hpFill = UIView(), shieldFill = UIView(), flash = UIView()
    private var status = Status.waiting, hpRatio: CGFloat = 1, shieldRatio: CGFloat = 0, enemy = false, targeted = false
    private var lastHP: Int?
    private static let portraits: [UIImage?] = (1...3).map { index in
        guard let atlas = UIImage(named: "Hero\(index)Directions")?.cgImage else { return nil }
        let cell = atlas.height / HeroFrames.atlasRows
        return atlas.cropping(to: CGRect(x: 0, y: 0, width: cell, height: cell)).map { UIImage(cgImage: $0) }
    }
    init(id: String) {
        self.id = id
        super.init(frame: .zero); isAccessibilityElement = true; accessibilityIdentifier = "previewQueue\(id)"
        card.layer.cornerRadius = 10; card.layer.borderWidth = 1.5; card.isUserInteractionEnabled = false
        flash.layer.cornerRadius = 10; flash.alpha = 0; flash.isUserInteractionEnabled = false
        name.font = MeadowPreviewPalette.font(13, .bold); name.textColor = MeadowPreviewPalette.ink; name.adjustsFontSizeToFitWidth = true; name.minimumScaleFactor = 0.65
        numbers.font = .monospacedDigitSystemFont(ofSize: 11, weight: .bold); numbers.textColor = MeadowPreviewPalette.ink
        circle.backgroundColor = MeadowPreviewPalette.panel
        portrait.contentMode = .scaleAspectFit; portrait.layer.magnificationFilter = .nearest
        pill.font = MeadowPreviewPalette.font(10, .heavy); pill.textAlignment = .center; pill.layer.cornerRadius = 7; pill.clipsToBounds = true
        hpTrack.backgroundColor = UIColor.black.withAlphaComponent(0.7); hpTrack.layer.cornerRadius = 3; hpTrack.clipsToBounds = true
        shieldFill.backgroundColor = .systemCyan
        [card, circle, portrait, name, hpTrack, numbers, pill, flash].forEach(addSubview)
        hpTrack.addSubview(hpFill); hpTrack.addSubview(shieldFill)
        addGestureRecognizer(UITapGestureRecognizer(target: self, action: #selector(tapped)))
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    @objc private func tapped() {
        onTap?(id)
        UIView.animate(withDuration: 0.08, animations: { self.transform = CGAffineTransform(scaleX: 0.94, y: 0.94) }) { _ in
            UIView.animate(withDuration: 0.3, delay: 0, usingSpringWithDamping: 0.5, initialSpringVelocity: 0.8, options: .allowUserInteraction) { self.transform = .identity }
        }
    }
    /// The turn just came to this unit.
    func pop() {
        transform = CGAffineTransform(scaleX: 1.16, y: 1.16)
        UIView.animate(withDuration: 0.55, delay: 0.05, usingSpringWithDamping: 0.45, initialSpringVelocity: 0.9, options: .allowUserInteraction) { self.transform = .identity }
    }

    func update(_ entry: MeadowTurnOrderView.Entry, status: Status, targeted: Bool) {
        self.status = status; self.targeted = targeted; enemy = entry.enemy
        name.text = entry.name
        numbers.text = "\(max(0, entry.hp))/\(entry.maxHP)" + (entry.shield > 0 ? "  盾\(entry.shield)" : "")
        let ratio = entry.maxHP > 0 ? CGFloat(max(0, min(entry.maxHP, entry.hp))) / CGFloat(entry.maxHP) : 0
        let ward = entry.maxHP > 0 ? CGFloat(min(entry.maxHP, entry.shield)) / CGFloat(entry.maxHP) : 0
        let barsChanged = ratio != hpRatio || ward != shieldRatio
        hpRatio = ratio; shieldRatio = ward
        hpFill.backgroundColor = hpRatio > 0.5 ? .systemGreen : hpRatio > 0.25 ? .systemOrange : .systemRed
        // Hurt: the card flashes red and shakes; healed: it flashes green. The bar slides to its new length.
        if let old = lastHP, old != entry.hp, window != nil {
            flash.backgroundColor = entry.hp < old ? .systemRed : .systemGreen; flash.alpha = 0.7
            UIView.animate(withDuration: 0.5) { self.flash.alpha = 0 }
            if entry.hp < old {
                let shake = CAKeyframeAnimation(keyPath: "transform.translation.x"); shake.values = [0, -6, 5, -4, 3, 0]; shake.duration = 0.32
                layer.add(shake, forKey: "shake")
            }
        }
        lastHP = entry.hp
        if entry.id.hasPrefix("p"), let number = Int(entry.id.dropFirst()) { portrait.image = Self.portraits[(number - 1) % Self.portraits.count]; portrait.tintColor = nil }
        else { portrait.image = UIImage(systemName: "pawprint.fill"); portrait.tintColor = UIColor(red: 0.93, green: 0.45, blue: 0.38, alpha: 1) }
        let side: UIColor = enemy ? UIColor(red: 0.9, green: 0.38, blue: 0.33, alpha: 1) : UIColor(red: 0.45, green: 0.82, blue: 0.58, alpha: 1)
        let ring: UIColor = status == .current ? MeadowPreviewPalette.gold : side
        circle.layer.borderColor = ring.cgColor; circle.layer.borderWidth = status == .current ? 3 : 2
        card.backgroundColor = status == .current ? UIColor(red: 0.30, green: 0.25, blue: 0.09, alpha: 1) : enemy ? UIColor(red: 0.24, green: 0.12, blue: 0.11, alpha: 1) : UIColor(red: 0.13, green: 0.24, blue: 0.17, alpha: 1)
        card.layer.borderColor = (targeted && status != .current ? UIColor.white : status == .current ? MeadowPreviewPalette.gold : side.withAlphaComponent(0.55)).cgColor
        card.layer.borderWidth = status == .current ? 2.5 : targeted ? 2.5 : 1.5
        card.layer.shadowColor = MeadowPreviewPalette.gold.cgColor; card.layer.shadowOffset = .zero; card.layer.shadowRadius = 10
        card.layer.shadowOpacity = status == .current ? 0.9 : 0
        card.layer.removeAnimation(forKey: "glow"); circle.layer.removeAnimation(forKey: "breathe")
        if status == .current {
            let pulse = CABasicAnimation(keyPath: "shadowOpacity"); pulse.fromValue = 0.3; pulse.toValue = 1; pulse.duration = 0.75; pulse.autoreverses = true; pulse.repeatCount = .infinity
            card.layer.add(pulse, forKey: "glow")
            let breathe = CABasicAnimation(keyPath: "transform.scale"); breathe.fromValue = 1; breathe.toValue = 1.07; breathe.duration = 0.75; breathe.autoreverses = true; breathe.repeatCount = .infinity
            circle.layer.add(breathe, forKey: "breathe")
        }
        let pillText: String?, pillColor: UIColor, pillInk: UIColor
        switch status {
        case .current: pillText = "行动中"; pillColor = MeadowPreviewPalette.gold; pillInk = UIColor(red: 0.12, green: 0.1, blue: 0.04, alpha: 1)
        case .next: pillText = "下一位"; pillColor = UIColor(white: 0.93, alpha: 1); pillInk = UIColor(red: 0.12, green: 0.1, blue: 0.04, alpha: 1)
        case .done: pillText = "✓ 已行动"; pillColor = UIColor(white: 0.35, alpha: 0.95); pillInk = .white
        case .down: pillText = "倒地"; pillColor = UIColor(red: 0.62, green: 0.14, blue: 0.12, alpha: 1); pillInk = .white
        case .waiting: pillText = nil; pillColor = .clear; pillInk = .white
        }
        pill.text = pillText; pill.isHidden = pillText == nil; pill.backgroundColor = pillColor; pill.textColor = pillInk
        alpha = status == .done ? 0.6 : status == .down ? 0.45 : 1
        accessibilityLabel = entry.name
        accessibilityValue = (status == .current ? "当前行动" : status == .next ? "下一位" : status == .done ? "已行动" : status == .down ? "倒地" : "等待") + "，生命\(entry.hp)/\(entry.maxHP)"
        if barsChanged, window != nil, hpTrack.bounds.width > 0 { UIView.animate(withDuration: 0.4, delay: 0, options: [.curveEaseOut, .beginFromCurrentState]) { self.layoutBars() } }
        setNeedsLayout()
    }

    private func layoutBars() {
        let w = hpTrack.bounds.width, h = hpTrack.bounds.height
        hpFill.frame = CGRect(x: 0, y: 0, width: w * hpRatio, height: h)
        shieldFill.frame = CGRect(x: 0, y: 0, width: w * shieldRatio, height: max(2, h * 0.35))
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        let w = bounds.width, h = bounds.height
        guard w > 0, h > 24 else { return }
        card.frame = bounds; flash.frame = bounds
        card.layer.shadowPath = UIBezierPath(roundedRect: bounds, cornerRadius: 10).cgPath
        if w >= 118 {
            // Row: face on the left; name and tag, the health bar, the numbers on the right.
            let side = min(h - 10, 48)
            circle.bounds = CGRect(x: 0, y: 0, width: side, height: side); circle.center = CGPoint(x: 6 + side / 2, y: h / 2)
            let x0 = circle.frame.maxX + 8, tw = w - x0 - 8, pillW: CGFloat = pill.isHidden ? 0 : min(58, tw * 0.45)
            let block: CGFloat = 16 + 4 + 8 + 3 + 13, top = max(2, (h - block) / 2)
            name.textAlignment = .left; name.frame = CGRect(x: x0, y: top, width: tw - pillW - (pillW > 0 ? 4 : 0), height: 16)
            pill.frame = CGRect(x: x0 + tw - pillW, y: top + 1, width: pillW, height: 14)
            hpTrack.frame = CGRect(x: x0, y: top + 20, width: tw, height: 8)
            numbers.isHidden = false; numbers.textAlignment = .left; numbers.frame = CGRect(x: x0, y: top + 31, width: tw, height: 13)
        } else {
            // Stack: name, face (the tag across its foot), health bar.
            let side = max(16, min(w - 10, h - 13 - 5 - 9))
            name.textAlignment = .center; name.frame = CGRect(x: 2, y: 2, width: w - 4, height: 13)
            circle.bounds = CGRect(x: 0, y: 0, width: side, height: side); circle.center = CGPoint(x: w / 2, y: 16 + side / 2)
            hpTrack.frame = CGRect(x: 6, y: h - 9, width: w - 12, height: 5)
            numbers.isHidden = true
            let pillW = min(w - 4, 54)
            pill.frame = CGRect(x: (w - pillW) / 2, y: circle.frame.maxY - 12, width: pillW, height: 14)
        }
        circle.layer.cornerRadius = circle.bounds.width / 2
        portrait.bounds = circle.bounds.insetBy(dx: circle.bounds.width * 0.1, dy: circle.bounds.width * 0.07); portrait.center = circle.center
        layoutBars()
    }
}
