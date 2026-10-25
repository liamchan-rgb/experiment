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
    static let healStar = UIImage(named:"BattleVFXHealStar")!
    static let healWisp = UIImage(named:"BattleVFXHealWisp")!
    static let healShaft = UIImage(named:"BattleVFXHealShaft")!
    static let healWave = UIImage(named:"BattleVFXHealWave")!
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
    var recoveryAge: Double?
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
        let recovery=recoveryAge.map { CGFloat(MeadowBattleRecoveryField.pulse($0)) } ?? 0
        if groundOnly {
            if recovery>0 {
                light(heroFoot,135,42,recovery*0.85,UIColor(red:0.15,green:1,blue:0.52,alpha:1))
                light(CGPoint(x:heroFoot.x,y:heroFoot.y-65*unit),75,110,recovery*0.28,UIColor(red:0.35,green:1,blue:0.60,alpha:1))
            }

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
                sprite(MeadowBattleVFXAssets.spray,CGPoint(x:impact.x+45*unit,y:enemyFoot.y-3*unit),260*spread,22+CGFloat(max(0,age))*70,burst*0.55)
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
        if let age=impactAge, age<0.70 {
            let slash=pulse(age,-0.06,0,0.25)
            let spread=CGFloat(max(0,age))
            sprite(MeadowBattleVFXAssets.slash,impact,225,225,slash)
            ctx.saveGState();ctx.translateBy(x:impact.x,y:impact.y);ctx.rotate(by:-0.65+spread*3.8)
            let arc=(225+spread*300)*unit
            MeadowBattleVFXAssets.heavyArc.draw(in:CGRect(x:-arc/2,y:-arc/2,width:arc,height:arc),blendMode:.plusLighter,alpha:burst*0.9)
            ctx.restoreGState()
            let echo=pulse(age,0.10,0.19,0.65)
            sprite(MeadowBattleVFXAssets.heavyArc,CGPoint(x:impact.x+spread*22*unit,y:impact.y),285+spread*160,225+spread*170,echo*0.38)
            sprite(MeadowBattleVFXAssets.burst,impact,205+spread*145,205+spread*145,burst)
            sprite(MeadowBattleVFXAssets.spray,CGPoint(x:impact.x+(95+spread*75)*unit,y:impact.y-15*unit),250+spread*180,160,burst*0.9)
            for i in 0..<26 {
                let angle=CGFloat(i)*2.399
                let distance=spread*CGFloat(150+(i%5)*38)*unit
                sprite(MeadowBattleVFXAssets.mote,CGPoint(x:impact.x+cos(angle)*distance,y:impact.y+sin(angle)*distance),CGFloat(i%4==0 ? 22 : 10),CGFloat(i%4==0 ? 7 : 10),burst*0.9)
            }
        }
        if let age=shieldContactAge, age<0.4 {
            let size=80+CGFloat(age)*150
            sprite(MeadowBattleVFXAssets.wardHit,CGPoint(x:impact.x+size*0.33*unit,y:impact.y),size,size,wardContact*0.9)
        }
        for p in debris {
            ctx.saveGState()
            ctx.translateBy(x:CGFloat(p.x)*unit,y:CGFloat(p.y)*unit)
            ctx.rotate(by:CGFloat(p.angle + (p.cyan ? Double.pi/4 : -Double.pi*0.75)))
            let size=CGFloat(p.size)*unit
            (p.cyan ? MeadowBattleVFXAssets.shard : MeadowBattleVFXAssets.ember).draw(in:CGRect(x:-size/2,y:-size/3,width:size,height:size*0.67),blendMode:.plusLighter,alpha:CGFloat(p.alpha))
            ctx.restoreGState()
        }
        if let age=messageAge, age < 0.7, !message.isEmpty {
            let center=messageAtHero ? heroFoot : impact
            let attrs:[NSAttributedString.Key:Any]=[.font:UIFont.boldSystemFont(ofSize:max(16,23*unit)),.foregroundColor:messageColor,.strokeColor:UIColor(red:0.15,green:0.1,blue:0.04,alpha:1),.strokeWidth:-3]
            let label=NSAttributedString(string:message,attributes:attrs)
            label.draw(at:CGPoint(x:center.x+20*unit,y:center.y-(40+CGFloat(age)*30)*unit))
        }
    }
}

final class MeadowBattleAttachedSkillsView: UIView {
    private let rim=UIImageView(image:MeadowBattleVFXAssets.barrier)
    private let orbiters=(0..<6).map { _ in UIImageView(image:MeadowBattleVFXAssets.mote.withTintColor(.systemCyan,renderingMode:.alwaysOriginal)) }
    private let core=UIImageView(image:MeadowBattleVFXAssets.burst.withTintColor(UIColor(red:0.82,green:1,blue:0.85,alpha:1),renderingMode:.alwaysOriginal))
    private let shaft=UIImageView(image:MeadowBattleVFXAssets.healShaft)
    private let wave=UIImageView(image:MeadowBattleVFXAssets.healWave)
    private let wisps=(0..<2).map { _ in UIImageView(image:MeadowBattleVFXAssets.healWisp) }
    private let stars=(0..<26).map { _ in UIImageView(image:MeadowBattleVFXAssets.healStar) }
    override init(frame:CGRect) {
        super.init(frame:frame);isUserInteractionEnabled=false;clipsToBounds=false
        ([shaft,wave,core]+wisps+stars+[rim]+orbiters).forEach { $0.contentMode = .scaleToFill;addSubview($0) }
        layer.zPosition=100
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    func update(shield:Int,preview:Bool,time:Double,birth:Double?,contact:Double?,broken:Double?,recovery:Double?) {
        let unit=bounds.width/256
        func smooth(_ x:Double)->CGFloat { CGFloat(MeadowBattleRecoveryField.smooth(x)) }
        UIView.performWithoutAnimation {
            CATransaction.begin();CATransaction.setDisableActions(true)
            defer { CATransaction.commit() }
            let center=CGPoint(x:MeadowBattleShieldGeometry.centerX*Double(unit),y:MeadowBattleShieldGeometry.centerY*Double(unit))
            let spawn=birth.map { 1-smooth($0/0.45) } ?? 0
            let hit=contact.map { 1-smooth($0/0.32) } ?? 0
            var alpha:CGFloat=shield>0 ? 0.68+spawn*0.25+hit*0.25+sin(CGFloat(time)*3)*0.035 : 0
            if preview { alpha=max(alpha,0.18) }
            if let broken,broken<0.25 { alpha=max(alpha,0.95*(1-smooth(broken/0.25))) }
            let size=CGFloat(MeadowBattleShieldGeometry.diameter)*unit
            rim.frame=CGRect(x:center.x-size/2,y:center.y-size/2,width:size,height:size)
            rim.alpha=alpha
            for (i,orb) in orbiters.enumerated() {
                let angle=CGFloat(time)*1.25+CGFloat(i)*2.399
                let radius=size*0.41
                let s=(i%2==0 ? CGFloat(9) : 6)*unit
                orb.frame=CGRect(x:center.x+cos(angle)*radius-s/2,y:center.y+sin(angle)*radius-s/2,width:s,height:s)
                orb.alpha=alpha*0.65
            }
            let age=recovery ?? -1
            let power=CGFloat(MeadowBattleRecoveryField.pulse(age))
            let active=age>=0 && age<MeadowBattleRecoveryField.duration
            let foot=CGPoint(x:128*unit,y:214*unit)
            shaft.isHidden = !active;wave.isHidden = !active
            shaft.frame=CGRect(x:foot.x-55*unit,y:foot.y-175*unit,width:110*unit,height:185*unit)
            shaft.alpha=power*0.50
            core.isHidden = !active
            let coreSize:CGFloat=110*unit
            core.frame=CGRect(x:foot.x-coreSize/2,y:foot.y-64*unit-coreSize/2,width:coreSize,height:coreSize)
            let corePulse:CGFloat=age<0.47 ? smooth((age-0.34)/0.13) : 1-smooth((age-0.47)/0.23)
            core.alpha=corePulse*0.70
            let expansion=CGFloat(0.65+0.65*MeadowBattleRecoveryField.smooth(age/1.1))
            wave.frame=CGRect(x:foot.x-82*unit*expansion,y:foot.y-12*unit,width:164*unit*expansion,height:28*unit)
            wave.alpha=power*0.8
            for (i,wisp) in wisps.enumerated() {
                wisp.isHidden = !active
                let turn=CGFloat(age)*4+CGFloat(i) * .pi
                wisp.bounds=CGRect(x:0,y:0,width:85*unit,height:180*unit)
                wisp.center=CGPoint(x:foot.x+(CGFloat(i==0 ? -26 : 26)+sin(turn)*12)*unit,y:foot.y-(76+CGFloat(age)*15)*unit)
                wisp.transform=CGAffineTransform(rotationAngle:sin(turn)*0.22).scaledBy(x:cos(turn)>=0 ? 1 : -1,y:1)
                wisp.alpha=power*(i==0 ? 0.85 : 0.65)
            }
            let motes=MeadowBattleRecoveryField.sample(age)
            for (i,star) in stars.enumerated() {
                guard i<motes.count else { star.isHidden=true;continue }
                let p=motes[i];star.isHidden=false
                star.frame=CGRect(x:foot.x+CGFloat(p.x-p.size/2)*unit,y:foot.y+CGFloat(p.y-p.size/2)*unit,width:CGFloat(p.size)*unit,height:CGFloat(p.size)*unit)
                star.alpha=CGFloat(p.alpha)
            }
        }
    }
}

final class MeadowBattleEnemyTargetView: UIImageView {
    var onActivate: (() -> Void)?
    override func accessibilityActivate() -> Bool { onActivate?(); return onActivate != nil }
}
