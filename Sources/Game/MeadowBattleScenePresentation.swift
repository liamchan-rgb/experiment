import UIKit

/// A weak display-link target avoids retaining the battle view after it closes.
private final class MeadowBattleClockTarget: NSObject {
    weak var clock: MeadowBattleSceneClock?
    @objc func tick(_ link: CADisplayLink) { clock?.tick(link) }
}

final class MeadowBattleSceneClock {
    var onTick: ((TimeInterval) -> Void)?
    private let target = MeadowBattleClockTarget()
    private var link: CADisplayLink?
    private var previous: TimeInterval = 0
    func start() {
        guard link == nil else { return }
        previous = 0; target.clock = self
        let value = CADisplayLink(target: target, selector: #selector(MeadowBattleClockTarget.tick(_:)))
        value.preferredFramesPerSecond = 30
        value.add(to: .main, forMode: .common); link = value
    }
    func stop() { link?.invalidate(); link = nil; previous = 0 }
    fileprivate func tick(_ link: CADisplayLink) {
        defer { previous = link.timestamp }
        guard previous > 0, UIApplication.shared.applicationState == .active else { return }
        onTick?(min(1.0 / 15, max(0, link.timestamp - previous)))
    }
    deinit { stop() }
}

/// Authored animation sheet is cropped once, never during the display loop.
enum MeadowBattleEnemyFrames {
    private static let sheet = UIImage(named: "MeadowBattleWardenAttackSheet")?.cgImage
    static let attack: [UIImage] = {
        guard let sheet, sheet.width % 8 == 0 else { return [] }
        let cell = sheet.width / 8
        return (0..<8).compactMap { index in
            sheet.cropping(to: CGRect(x: index * cell, y: 0, width: cell, height: sheet.height)).map { UIImage(cgImage: $0) }
        }
    }()
    static func image(progress: CGFloat) -> UIImage? {
        guard !attack.isEmpty else { return UIImage(named: "MeadowBattleForestWarden") }
        return attack[min(attack.count - 1, max(0, Int(progress * CGFloat(attack.count))))]
    }
    static let contacts: [[CGPoint]] = {
        guard let data = NSDataAsset(name: "MeadowBattleWardenMotion")?.data,
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let values = json["contacts"] as? [[[NSNumber]]] else { return [] }
        return values.map { $0.compactMap { $0.count == 2 ? CGPoint(x: CGFloat(truncating: $0[0]), y: CGFloat(truncating: $0[1])) : nil } }
    }()
    static func feet(progress: CGFloat) -> [CGPoint] {
        guard !contacts.isEmpty else { return [CGPoint(x: 84, y: 240), CGPoint(x: 172, y: 240), CGPoint(x: 230, y: 240), CGPoint(x: 314, y: 240)] }
        return contacts[min(contacts.count - 1, max(0, Int(progress * CGFloat(contacts.count))))]
    }
}

/// Vector combat feedback is registered to the same battlefield canvas as the
/// sprites: target ring, short impact arc, ward and healing motes.
final class MeadowBattleEffectsView: UIView {
    var heroFoot = CGPoint.zero
    var enemyFoot = CGPoint.zero
    var impact = CGPoint.zero
    var selected = false
    var cue: MeadowBattleAnimationCue?
    var progress: CGFloat = 0
    var shield = 0
    var message = ""
    var messageColor = UIColor.white
    override init(frame: CGRect) { super.init(frame: frame); isOpaque = false; isUserInteractionEnabled = false }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func draw(_ rect: CGRect) {
        guard let ctx = UIGraphicsGetCurrentContext() else { return }
        let unit = bounds.width / 700
        let gold = UIColor(red: 1, green: 0.84, blue: 0.35, alpha: 1)
        func ellipse(_ point: CGPoint, radius: CGFloat, color: UIColor) {
            color.setStroke(); let path = UIBezierPath(ovalIn: CGRect(x: point.x - radius, y: point.y - radius * 0.25,
                width: radius * 2, height: radius * 0.5)); path.lineWidth = max(1.5, 2 * unit); path.stroke()
        }
        if selected { ellipse(enemyFoot, radius: 51 * unit, color: gold) }
        if shield > 0 {
            let path = UIBezierPath(arcCenter: CGPoint(x: heroFoot.x, y: heroFoot.y - 34 * unit), radius: 43 * unit,
                                    startAngle: -.pi * 0.60, endAngle: .pi * 0.60, clockwise: true)
            UIColor(red: 0.35, green: 0.85, blue: 1, alpha: 0.75).setStroke(); path.lineWidth = 3 * unit; path.stroke()
        }
        if let cue {
            switch cue {
            case .strike, .enemyStrike:
                let intensity = max(0, 1 - abs(progress - 0.52) / 0.12)
                if intensity > 0 {
                    ctx.saveGState(); ctx.setAlpha(intensity)
                    let arc = UIBezierPath()
                    arc.move(to: CGPoint(x: impact.x - 28 * unit, y: impact.y - 35 * unit))
                    arc.addQuadCurve(to: CGPoint(x: impact.x + 22 * unit, y: impact.y + 24 * unit),
                                     controlPoint: CGPoint(x: impact.x + 35 * unit, y: impact.y - 25 * unit))
                    gold.setStroke(); arc.lineWidth = 8 * unit; arc.stroke()
                    UIColor.white.setStroke(); arc.lineWidth = 3 * unit; arc.stroke()
                    for index in 0..<6 {
                        let angle = CGFloat(index) * .pi / 3
                        let ray = UIBezierPath(); let start: CGFloat = 10 * unit, end: CGFloat = 23 * unit
                        ray.move(to: CGPoint(x: impact.x + cos(angle) * start, y: impact.y + sin(angle) * start))
                        ray.addLine(to: CGPoint(x: impact.x + cos(angle) * end, y: impact.y + sin(angle) * end))
                        ray.lineWidth = 2 * unit; ray.stroke()
                    }
                    ctx.restoreGState()
                }
            case .heal:
                for index in 0..<5 {
                    let x = heroFoot.x + CGFloat(index - 2) * 10 * unit
                    let y = heroFoot.y - (18 + progress * 72 + CGFloat(index % 2) * 8) * unit
                    let opacity = sin(progress * .pi)
                    UIColor(red: 0.45, green: 1, blue: 0.60, alpha: opacity).setFill()
                    UIBezierPath(roundedRect: CGRect(x: x, y: y, width: 3 * unit, height: 10 * unit), cornerRadius: unit).fill()
                }
            case .guardPose:
                ellipse(heroFoot, radius: (25 + 18 * sin(progress * .pi)) * unit,
                        color: UIColor(red: 0.4, green: 0.85, blue: 1, alpha: sin(progress * .pi)))
            case .victory, .defeat: break
            }
        }
        if !message.isEmpty, progress > 0.46, progress < 0.95 {
            let center = (cue == .enemyStrike || cue == .heal || cue == .guardPose) ? heroFoot : enemyFoot
            let font = UIFont.boldSystemFont(ofSize: max(17, 24 * unit))
            let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: messageColor,
                .strokeColor: UIColor(red: 0.12, green: 0.15, blue: 0.10, alpha: 1), .strokeWidth: -3]
            let label = NSAttributedString(string: message, attributes: attrs)
            let size = label.size()
            label.draw(at: CGPoint(x: center.x - size.width / 2, y: center.y - (95 + 30 * (progress - 0.46)) * unit))
        }
    }
}

final class MeadowBattleEnemyTargetView: UIImageView {
    var onActivate: (() -> Void)?
    override func accessibilityActivate() -> Bool { onActivate?(); return onActivate != nil }
}
