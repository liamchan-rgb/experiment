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

    override init(frame: CGRect) {
        super.init(frame: frame); MeadowPreviewPalette.stylePanel(self)
        banner.numberOfLines = 2; banner.textAlignment = .center; banner.layer.cornerRadius = 10; banner.layer.borderWidth = 2; banner.clipsToBounds = true
        addSubview(banner)
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
        let changed = ordered != order || current != currentID
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
            UIView.animate(withDuration: 0.42, delay: 0, usingSpringWithDamping: 0.82, initialSpringVelocity: 0.4, options: [.allowUserInteraction, .beginFromCurrentState]) { self.layoutNow() }
        } else { layoutNow() }
    }

    private func layoutNow() { setNeedsLayout(); layoutIfNeeded() }

    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.width > 0, bounds.height > 0 else { return }
        let inset: CGFloat = 8, bannerWidth = min(170, bounds.width * 0.2)
        banner.frame = CGRect(x: inset, y: 6, width: bannerWidth, height: bounds.height - 12)
        let left = banner.frame.maxX + 10, available = bounds.width - left - inset
        let n = CGFloat(max(1, order.count)), gap: CGFloat = 4
        // The acting unit is 1.4x as wide as the rest.
        let unit = min(92, (available - gap * (n - 1)) / (n + 0.4))
        var x = left
        let full = bounds.height - 6
        for (i, id) in order.enumerated() {
            guard let token = tokens[id] else { continue }
            let isCurrent = id == currentID && i == 0
            let width = isCurrent ? unit * 1.4 : unit, height = isCurrent ? full : full * 0.86
            token.frame = CGRect(x: x, y: 3 + (full - height) / 2, width: width, height: height)
            x += width + gap
        }
    }
}

private final class MeadowTurnOrderToken: UIView {
    enum Status { case current, next, waiting, done, down }
    var onTap: ((String) -> Void)?
    private let id: String
    private let name = UILabel(), circle = UIView(), portrait = UIImageView(), pill = UILabel(), hpTrack = UIView(), hpFill = UIView(), shieldFill = UIView()
    private var status = Status.waiting, hpRatio: CGFloat = 1, shieldRatio: CGFloat = 0, enemy = false, targeted = false
    private static let portraits: [UIImage?] = (1...3).map { index in
        guard let atlas = UIImage(named: "Hero\(index)Directions")?.cgImage else { return nil }
        let cell = atlas.height / HeroFrames.atlasRows
        return atlas.cropping(to: CGRect(x: 0, y: 0, width: cell, height: cell)).map { UIImage(cgImage: $0) }
    }
    init(id: String) {
        self.id = id
        super.init(frame: .zero); isAccessibilityElement = true; accessibilityIdentifier = "previewQueue\(id)"
        name.font = MeadowPreviewPalette.font(11, .bold); name.textColor = MeadowPreviewPalette.ink; name.textAlignment = .center; name.adjustsFontSizeToFitWidth = true; name.minimumScaleFactor = 0.7
        circle.backgroundColor = MeadowPreviewPalette.card; circle.clipsToBounds = false
        portrait.contentMode = .scaleAspectFit; portrait.layer.magnificationFilter = .nearest
        pill.font = MeadowPreviewPalette.font(10, .heavy); pill.textAlignment = .center; pill.layer.cornerRadius = 6.5; pill.clipsToBounds = true
        hpTrack.backgroundColor = UIColor.black.withAlphaComponent(0.7); hpTrack.layer.cornerRadius = 2; hpTrack.clipsToBounds = true
        hpFill.layer.cornerRadius = 2; shieldFill.backgroundColor = .systemCyan
        [circle, portrait, name, hpTrack, pill].forEach(addSubview)
        hpTrack.addSubview(hpFill); hpTrack.addSubview(shieldFill)
        addGestureRecognizer(UITapGestureRecognizer(target: self, action: #selector(tapped)))
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    @objc private func tapped() { onTap?(id) }

    func update(_ entry: MeadowTurnOrderView.Entry, status: Status, targeted: Bool) {
        self.status = status; self.targeted = targeted; enemy = entry.enemy
        name.text = entry.name
        hpRatio = entry.maxHP > 0 ? CGFloat(max(0, min(entry.maxHP, entry.hp))) / CGFloat(entry.maxHP) : 0
        shieldRatio = entry.maxHP > 0 ? CGFloat(min(entry.maxHP, entry.shield)) / CGFloat(entry.maxHP) : 0
        hpFill.backgroundColor = hpRatio > 0.5 ? .systemGreen : hpRatio > 0.25 ? .systemOrange : .systemRed
        if entry.id.hasPrefix("p"), let number = Int(entry.id.dropFirst()) { portrait.image = Self.portraits[(number - 1) % Self.portraits.count]; portrait.tintColor = nil }
        else { portrait.image = UIImage(systemName: "pawprint.fill"); portrait.tintColor = UIColor(red: 0.93, green: 0.45, blue: 0.38, alpha: 1) }
        let ring: UIColor = status == .current ? MeadowPreviewPalette.gold : enemy ? UIColor(red: 0.9, green: 0.38, blue: 0.33, alpha: 1) : UIColor(red: 0.45, green: 0.82, blue: 0.58, alpha: 1)
        circle.layer.borderColor = (targeted ? UIColor.white : ring).cgColor
        circle.layer.borderWidth = status == .current ? 4 : targeted ? 3 : 2
        circle.layer.shadowColor = MeadowPreviewPalette.gold.cgColor; circle.layer.shadowOffset = .zero; circle.layer.shadowRadius = 9
        circle.layer.shadowOpacity = status == .current ? 0.95 : status == .next ? 0.35 : 0
        circle.layer.removeAnimation(forKey: "glow")
        if status == .current {
            let pulse = CABasicAnimation(keyPath: "shadowOpacity"); pulse.fromValue = 0.35; pulse.toValue = 1; pulse.duration = 0.7; pulse.autoreverses = true; pulse.repeatCount = .infinity
            circle.layer.add(pulse, forKey: "glow")
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
        let dim: CGFloat = status == .done ? 0.5 : status == .down ? 0.4 : 1
        circle.alpha = dim; portrait.alpha = status == .down ? 0.3 : dim; name.alpha = max(0.6, dim); hpTrack.alpha = dim
        accessibilityLabel = entry.name
        accessibilityValue = (status == .current ? "当前行动" : status == .next ? "下一位" : status == .done ? "已行动" : status == .down ? "倒地" : "等待") + "，生命\(entry.hp)/\(entry.maxHP)"
        setNeedsLayout()
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.width > 0, bounds.height > 30 else { return }
        let nameH: CGFloat = 13, barH: CGFloat = 5
        name.frame = CGRect(x: 0, y: 0, width: bounds.width, height: nameH)
        let side = max(16, min(bounds.width - 6, bounds.height - nameH - barH - 4))
        circle.frame = CGRect(x: (bounds.width - side) / 2, y: nameH + 1, width: side, height: side)
        circle.layer.cornerRadius = side / 2; portrait.frame = circle.frame.insetBy(dx: side * 0.1, dy: side * 0.07)
        hpTrack.frame = CGRect(x: circle.frame.minX, y: circle.frame.maxY + 3, width: side, height: barH)
        hpFill.frame = CGRect(x: 0, y: 0, width: side * hpRatio, height: barH)
        shieldFill.frame = CGRect(x: 0, y: 0, width: side * shieldRatio, height: 2)
        let pillWidth = min(bounds.width, max(40, side))
        pill.frame = CGRect(x: (bounds.width - pillWidth) / 2, y: circle.frame.maxY - 11, width: pillWidth, height: 13)
    }
}
