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
enum MeadowBattleVFXAssets {
    static let heavyArc = UIImage(named: "BattleVFXHeavyArc")!
    static let spray = UIImage(named: "BattleVFXHeavySpray")!
    static let barrier = UIImage(named: "BattleVFXRoundBarrier")!
    static let shard = UIImage(named: "BattleVFXCyanShard")!
    static let ember = UIImage(named: "BattleVFXGoldEmber")!
    static let groundSpark = UIImage(named: "BattleVFXGroundSpark")!
    static let wardHit = UIImage(named: "BattleVFXWardHit")!
    static let slash = UIImage(named: "BattleVFXSlash")!
    static let burst = UIImage(named: "BattleVFXBurst")!
    static let ring = UIImage(named: "BattleVFXRing")!
    static let mote = UIImage(named: "BattleVFXMote")!
    static let body = frames("BattleVFXDeathBody", width: 384, height: 256)
    static let wind = frames("BattleVFXDeathWindHeavy", width: 640, height: 320)
    private static func frames(_ name: String, width: Int, height: Int) -> [UIImage] {
        guard let sheet = UIImage(named: name)?.cgImage else { fatalError("Missing battle VFX atlas") }
        return (0..<48).map { i in
            UIImage(cgImage: sheet.cropping(to: CGRect(x: (i % 8) * width, y: (i / 8) * height, width: width, height: height))!)
        }
    }
    static func deathFrame(_ age: Double) -> Int { min(47, max(0, Int(age / 0.04))) }
}

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
    var previewPower: CGFloat = 0
    var previewEnvelope: CGFloat = 0
    var ringAlpha: CGFloat = 0
    var impactAge: Double?
    var messageAge: Double?
    var messageAtHero = false
    var time: Double = 0
    var groundOnly = false
    var shieldPreview = false
    var shieldBirthAge: Double?
    var shieldContactAge: Double?
    var shieldBreakAge: Double?
    var deathAge: Double?
    var lightEmissions: [MeadowBattleLightEmission] = []
    override init(frame: CGRect) { super.init(frame: frame); isOpaque = false; isUserInteractionEnabled = false }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func draw(_ rect: CGRect) {
        guard let ctx = UIGraphicsGetCurrentContext() else { return }
        let unit = bounds.width / 760
        func smooth(_ x: CGFloat) -> CGFloat { let t = min(1, max(0, x)); return t*t*(3-2*t) }
        func pulse(_ age: Double, _ start: Double, _ peak: Double, _ end: Double) -> CGFloat {
            age <= peak ? smooth(CGFloat((age-start)/(peak-start))) : 1-smooth(CGFloat((age-peak)/(end-peak)))
        }
        func sprite(_ image: UIImage, _ center: CGPoint, _ width: CGFloat, _ height: CGFloat, _ alpha: CGFloat) {
            guard alpha > 0 else { return }
            image.draw(in: CGRect(x: center.x-width*unit/2, y: center.y-height*unit/2, width: width*unit, height: height*unit), blendMode: .plusLighter, alpha: alpha)
        }
        func light(_ center: CGPoint, _ rx: CGFloat, _ ry: CGFloat, _ alpha: CGFloat, _ color: UIColor = UIColor(red:1,green:0.75,blue:0.27,alpha:1)) {
            guard alpha > 0 else { return }
            ctx.saveGState(); ctx.translateBy(x: center.x, y: center.y); ctx.scaleBy(x: rx*unit, y: ry*unit)
            let colors = [color.withAlphaComponent(alpha).cgColor, UIColor.clear.cgColor] as CFArray
            let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(), colors: colors, locations: [0, 1])!
            ctx.setBlendMode(.plusLighter); ctx.drawRadialGradient(gradient, startCenter: .zero, startRadius: 0, endCenter: .zero, endRadius: 1, options: [])
            ctx.restoreGState()
        }
        let burst = impactAge.map { pulse($0, -0.035, 0.035, 0.52) } ?? 0
        let wardSpawn=shieldBirthAge.map { pulse($0,0,0.10,0.45) } ?? 0
        let wardContact=shieldContactAge.map { pulse($0,-0.02,0.025,0.38) } ?? 0
        let debris = lightEmissions.flatMap { e in
            MeadowBattleLightField.sample(e.kind,age:time-e.startedAt,originX:e.x,originY:e.y,groundY:e.groundY)
        }
        if groundOnly {
            let cyan = UIColor(red:0.05,green:0.55,blue:1,alpha:1)
            var pools = 0
            for p in debris {
                if p.id % 6 == 0 { light(CGPoint(x:p.x*Double(unit),y:p.y*Double(unit)),24,20,CGFloat(p.alpha)*0.25,p.cyan ? cyan : .orange) }
                if let age=p.groundAge, age<0.24, pools<12 {
                    let center=CGPoint(x:p.groundX*Double(unit),y:p.groundY*Double(unit))
                    let fade=CGFloat(1-age/0.24)*CGFloat(p.alpha)
                    light(center,36,10,fade*0.65,p.cyan ? cyan : .orange)
                    sprite(p.cyan ? MeadowBattleVFXAssets.wardHit : MeadowBattleVFXAssets.groundSpark,center,30,12,fade*0.9)
                    pools += 1
                }
            }
            if let age=deathAge,age<1.4 {
                light(CGPoint(x:impact.x+CGFloat(age)*95*unit,y:enemyFoot.y),180,42,0.38*(1-smooth(CGFloat(age/1.4))))
                light(CGPoint(x:impact.x+CGFloat(age)*90*unit,y:impact.y),115,95,0.18*(1-smooth(CGFloat(age/1.4))))
            }

            light(CGPoint(x: impact.x+20*unit, y: enemyFoot.y), 235, 55, burst*0.76)
            light(impact, 195, 190, burst*0.48)
            light(heroFoot,95,32,(wardSpawn*0.28+wardContact*0.38),.cyan)
            if let age=impactAge, age<0.5 {
                let spread=1+CGFloat(max(0,age))*2
                sprite(MeadowBattleVFXAssets.spray,CGPoint(x:impact.x+45*unit,y:enemyFoot.y-3*unit),260*spread,35,burst*0.55)
            }
            light(heroFoot, 90, 26, previewPower*previewEnvelope*0.16)
            return
        }
        if selected, cue == nil {
            UIColor(red: 1, green: 0.84, blue: 0.35, alpha: 0.65).setStroke()
            let p=UIBezierPath(ovalIn: CGRect(x: enemyFoot.x-48*unit,y:enemyFoot.y-10*unit,width:96*unit,height:20*unit));p.lineWidth=1.5;p.stroke()
        }
        sprite(MeadowBattleVFXAssets.ring, heroFoot, 110, 46, ringAlpha)
        if previewPower > 0 {
            for i in 0..<(previewPower > 0.5 ? 7 : 3) {
                let angle=CGFloat(i)*2.399+CGFloat(time)*1.7
                sprite(MeadowBattleVFXAssets.mote, CGPoint(x: heroFoot.x+cos(angle)*(18+previewPower*15)*unit,y:heroFoot.y-58*unit+sin(angle)*24*unit),12,12,previewPower*previewEnvelope*0.9)
            }
        }
        if let age=impactAge, burst > 0 {
            let slash=pulse(age,-0.06,0,0.25)
            let spread=CGFloat(max(0,age))
            sprite(MeadowBattleVFXAssets.slash,impact,225,225,slash)
            sprite(MeadowBattleVFXAssets.heavyArc,impact,245+spread*220,245+spread*220,burst*0.95)
            sprite(MeadowBattleVFXAssets.burst,impact,205+spread*145,205+spread*145,burst)
            sprite(MeadowBattleVFXAssets.spray,CGPoint(x:impact.x+(95+spread*75)*unit,y:impact.y-15*unit),250+spread*180,160,burst*0.9)
            for i in 0..<26 {
                let angle=CGFloat(i)*2.399
                let distance=spread*CGFloat(150+(i%5)*38)*unit
                sprite(MeadowBattleVFXAssets.mote,CGPoint(x:impact.x+cos(angle)*distance,y:impact.y+sin(angle)*distance),CGFloat(i%4==0 ? 22 : 10),CGFloat(i%4==0 ? 7 : 10),burst*0.9)
            }
        }
        let wardCenter=CGPoint(x:heroFoot.x+6*unit,y:heroFoot.y-66*unit)
        let wardScale=shieldBirthAge.map { 0.68+0.32*smooth(CGFloat($0/0.28)) } ?? 1
        var wardAlpha: CGFloat = shield > 0 ? 0.60+wardSpawn*0.4+wardContact*0.4 : 0
        if shieldPreview { wardAlpha=max(wardAlpha,previewEnvelope*0.12) }
        if let age=shieldBreakAge, age<0.25 { wardAlpha=max(wardAlpha,0.95*(1-smooth(CGFloat(age/0.25)))) }
        sprite(MeadowBattleVFXAssets.barrier,wardCenter,132*wardScale,132*wardScale,wardAlpha)
        if let age=shieldContactAge, age<0.4 {
            let contact=CGPoint(x:heroFoot.x+65*unit,y:heroFoot.y-66*unit)
            let size=80+CGFloat(age)*150
            sprite(MeadowBattleVFXAssets.wardHit,CGPoint(x:contact.x+size*0.33*unit,y:contact.y),size,size,wardContact*0.9)
        }
        for p in debris {
            ctx.saveGState()
            ctx.translateBy(x:CGFloat(p.x)*unit,y:CGFloat(p.y)*unit)
            ctx.rotate(by:CGFloat(p.angle + (p.cyan ? Double.pi/4 : -Double.pi*0.75)))
            let size=CGFloat(p.size)*unit
            (p.cyan ? MeadowBattleVFXAssets.shard : MeadowBattleVFXAssets.ember).draw(in:CGRect(x:-size/2,y:-size/3,width:size,height:size*0.67),blendMode:.plusLighter,alpha:CGFloat(p.alpha))
            ctx.restoreGState()
        }
        if cue == .heal {
            for i in 0..<5 {
                let center=CGPoint(x:heroFoot.x+CGFloat(i-2)*10*unit,y:heroFoot.y-(18+progress*72)*unit)
                UIColor.green.withAlphaComponent(sin(progress * .pi)).setFill()
                UIBezierPath(ovalIn:CGRect(x:center.x,y:center.y,width:3*unit,height:8*unit)).fill()
            }
        }
        if let age=messageAge, age < 0.7, !message.isEmpty {
            let center=messageAtHero ? heroFoot : impact
            let attrs:[NSAttributedString.Key:Any]=[.font:UIFont.boldSystemFont(ofSize:max(16,23*unit)),.foregroundColor:messageColor,.strokeColor:UIColor(red:0.15,green:0.1,blue:0.04,alpha:1),.strokeWidth:-3]
            let label=NSAttributedString(string:message,attributes:attrs)
            label.draw(at:CGPoint(x:center.x+20*unit,y:center.y-(40+CGFloat(age)*30)*unit))
        }
    }
}

final class MeadowBattleEnemyTargetView: UIImageView {
    var onActivate: (() -> Void)?
    override func accessibilityActivate() -> Bool { onActivate?(); return onActivate != nil }
}
