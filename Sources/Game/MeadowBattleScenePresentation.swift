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
        value.preferredFramesPerSecond = 60
        value.preferredFrameRateRange = CAFrameRateRange(minimum:60,maximum:60,preferred:60)
        value.add(to: .main, forMode: .common); link = value
    }
    func stop() { link?.invalidate(); link = nil; previous = 0; MeadowBattleFrameTiming.flush() }
    fileprivate func tick(_ link: CADisplayLink) {
        defer { previous = link.timestamp }
        guard previous > 0, UIApplication.shared.applicationState == .active else { return }
        let delta=max(0,link.timestamp-previous)
        let begin=CACurrentMediaTime()
        onTick?(min(0.25,delta))
        MeadowBattleFrameTiming.record(interval:delta,cpu:CACurrentMediaTime()-begin)
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
    static let body = frames("BattleVFXDeathBody60", width: 384, height: 256,count:48)
    static let wind = frames("BattleVFXDeathWind60", width: 448, height: 320,count:116)
    private static func frames(_ name: String, width: Int, height: Int, count: Int) -> [UIImage] {
        guard let sheet = UIImage(named: name)?.preparingForDisplay()?.cgImage else { fatalError("Missing battle VFX atlas") }
        return (0..<count).map { i in
            UIImage(cgImage: sheet.cropping(to: CGRect(x: (i % 8) * width, y: (i / 8) * height, width: width, height: height))!)
        }
    }
    static func prewarm() { DispatchQueue.global(qos:.userInitiated).async { _ = body; _ = wind } }
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
    var particles: [MeadowBattleLightParticle] = []
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
            let glow=MeadowBattleGlowCache.image(color)
            glow.draw(in:CGRect(x:center.x-rx*unit,y:center.y-ry*unit,width:rx*unit*2,height:ry*unit*2),blendMode:.plusLighter,alpha:alpha)
        }
        let burst = impactAge.map { pulse($0, -0.035, 0.035, 0.52) } ?? 0
        let wardSpawn=shieldBirthAge.map { pulse($0,0,0.10,0.45) } ?? 0
        let wardContact=shieldContactAge.map { pulse($0,-0.02,0.025,0.38) } ?? 0
        let debris = particles
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
            label.draw(at:messageAtHero ? CGPoint(x:center.x+20*unit,y:center.y-(40+CGFloat(age)*30)*unit):CGPoint(x:center.x-label.size().width/2,y:center.y-label.size().height/2-CGFloat(age)*30*unit))
        }
    }
}

final class MeadowBattleAttachedSkillsView: UIView {
    private let rim=UIImageView(image:MeadowBattleVFXAssets.barrier)
    private let orbiters=(0..<6).map { _ in UIImageView(image:MeadowBattleVFXAssets.mote.withTintColor(.systemCyan,renderingMode:.alwaysOriginal)) }
    private let core=UIImageView(image:MeadowBattleVFXAssets.burst.withTintColor(UIColor(red:0.82,green:1,blue:0.85,alpha:1),renderingMode:.alwaysOriginal))
    private let shaft=UIImageView(image:MeadowBattleVFXAssets.healShaft)
    private let wave=UIImageView(image:MeadowBattleVFXAssets.healWave)
    private let ribbon=MeadowBattleRecoveryRibbonView(front:true)
    private let rearRibbon=MeadowBattleRecoveryRibbonView(front:false)
    private let stars=(0..<26).map { _ in UIImageView(image:MeadowBattleVFXAssets.healStar) }
    override init(frame:CGRect) {
        super.init(frame:frame);isUserInteractionEnabled=false;clipsToBounds=false
        ([shaft,wave,core,ribbon]+stars+[rim]+orbiters).forEach { $0.contentMode = .scaleToFill;addSubview($0) }
        layer.zPosition=100
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func didMoveToSuperview() {
        super.didMoveToSuperview()
        rearRibbon.removeFromSuperview()
        if let host=superview { rearRibbon.layer.zPosition = -1;host.addSubview(rearRibbon) }
    }
    func update(shield:Int,preview:Double,time:Double,formation:Double?,formationBase:Double,birth:Double?,contact:Double?,broken:Double?,recovery:Double?) {
        let unit=bounds.width/256
        func smooth(_ x:Double)->CGFloat { CGFloat(MeadowBattleRecoveryField.smooth(x)) }
        UIView.performWithoutAnimation {
            CATransaction.begin();CATransaction.setDisableActions(true)
            defer { CATransaction.commit() }
            let center=CGPoint(x:MeadowBattleShieldGeometry.centerX*Double(unit),y:MeadowBattleShieldGeometry.centerY*Double(unit))
            var alpha=CGFloat(MeadowBattleVisualMotion.shieldOpacity(shield:shield,time:time,formation:formation,birth:birth,contact:contact,broken:broken))
            alpha=max(alpha,CGFloat(preview)*0.18)
            if let formation { alpha=max(alpha,CGFloat(formationBase)*(1-smooth(formation/0.46))) }
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
            shaft.alpha=power*0.10
            core.isHidden = !active
            let coreSize:CGFloat=110*unit
            core.frame=CGRect(x:foot.x-coreSize/2,y:foot.y-64*unit-coreSize/2,width:coreSize,height:coreSize)
            let corePulse:CGFloat=age<0.47 ? smooth((age-0.34)/0.13) : 1-smooth((age-0.47)/0.23)
            core.alpha=corePulse*0.25
            let expansion=CGFloat(0.65+0.65*MeadowBattleRecoveryField.smooth(age/1.1))
            wave.frame=CGRect(x:foot.x-82*unit*expansion,y:foot.y-12*unit,width:164*unit*expansion,height:28*unit)
            wave.alpha=power*0.35
            ribbon.frame=bounds;ribbon.age=age;ribbon.setNeedsDisplay()
            rearRibbon.frame=frame;rearRibbon.age=age;rearRibbon.setNeedsDisplay()
            let motes=Dictionary(uniqueKeysWithValues:MeadowBattleRecoveryField.sample(age).map { ($0.id,$0) })
            for (i,star) in stars.enumerated() {
                guard let p=motes[i] else { star.isHidden=true;continue }
                star.isHidden=false
                star.frame=CGRect(x:foot.x+CGFloat(p.x-p.size/2)*unit,y:foot.y+CGFloat(p.y-p.size/2)*unit,width:CGFloat(p.size)*unit,height:CGFloat(p.size)*unit)
                star.alpha=CGFloat(p.alpha)
            }
        }
    }
}

private final class MeadowBattleRecoveryRibbonView:UIView {
    let front:Bool
    var age = -1.0
    init(front:Bool) { self.front=front;super.init(frame:.zero);isOpaque=false;isUserInteractionEnabled=false }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func draw(_ rect:CGRect) {
        guard let ctx=UIGraphicsGetCurrentContext() else { return }
        let scale=bounds.width/256
        ctx.saveGState();ctx.scaleBy(x:scale,y:scale);ctx.translateBy(x:128,y:214)
        ctx.setBlendMode(.plusLighter);ctx.setLineCap(.round);ctx.setLineJoin(.round)
        for strand in 0..<2 {
            let points=MeadowBattleRecoveryField.ribbon(age,strand:strand)
            for start in stride(from:0,to:max(0,points.count-1),by:3) {
                let end=min(points.count-1,start+3)
                let path=UIBezierPath();var alpha=0.0,count=0
                for j in start..<end {
                    let a=points[j],b=points[j+1]
                    guard ((a.depth+b.depth)/2>=0)==front else { continue }
                    path.move(to:CGPoint(x:a.x,y:a.y));path.addLine(to:CGPoint(x:b.x,y:b.y));alpha += (a.alpha+b.alpha)/2;count += 1
                }
                guard count>0 else { continue };alpha=alpha/Double(count)*(front ? 1:0.58)
                UIColor(red:0.08,green:0.95,blue:0.40,alpha:alpha*0.20).setStroke();path.lineWidth=9;path.stroke()
                UIColor(red:0.40,green:1,blue:0.64,alpha:alpha*0.90).setStroke();path.lineWidth=3.2;path.stroke()
                UIColor(red:0.86,green:1,blue:0.81,alpha:alpha*0.85).setStroke();path.lineWidth=1.1;path.stroke()
            }
        }
        ctx.restoreGState()
    }
}

final class MeadowBattleEnemyTargetView: UIImageView {
    var onActivate: (() -> Void)?
    override func accessibilityActivate() -> Bool { onActivate?(); return onActivate != nil }
}

/// Cached optical masks avoid constructing gradients for every particle every frame.
enum MeadowBattleGlowCache {
    private static var cache: [UIColor:UIImage] = [:]
    static func image(_ color: UIColor) -> UIImage {
        if let found=cache[color] { return found }
        let image=UIGraphicsImageRenderer(size:CGSize(width:96,height:96),format:{ let f=UIGraphicsImageRendererFormat();f.scale=1;return f }()).image { context in
            let colors=[color.cgColor,color.withAlphaComponent(0).cgColor] as CFArray
            let g=CGGradient(colorsSpace:CGColorSpaceCreateDeviceRGB(),colors:colors,locations:[0,1])!
            context.cgContext.drawRadialGradient(g,startCenter:CGPoint(x:48,y:48),startRadius:0,endCenter:CGPoint(x:48,y:48),endRadius:48,options:[])
        }
        cache[color]=image;return image
    }
}

/// Actual display-link intervals and update CPU time, never inferred device FPS.
enum MeadowBattleFrameTiming {
    private static var count=0, over25=0, over50=0
    private static var intervalTotal=0.0, cpuTotal=0.0, maxInterval=0.0, maxCPU=0.0
    private static let queue=DispatchQueue(label:"battle.frame-timing",qos:.utility)
    static func record(interval:Double,cpu:Double) {
        count += 1;intervalTotal += interval;cpuTotal += cpu
        maxInterval=max(maxInterval,interval);maxCPU=max(maxCPU,cpu)
        if interval>0.025 { over25 += 1 };if interval>0.050 { over50 += 1 }
    }
    static func flush() {
        guard count>0 else { return }
        let values:[String:Any]=["build":Bundle.main.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? "unknown","samples":count,"targetHz":60,"meanIntervalMs":intervalTotal/Double(count)*1000,"maxIntervalMs":maxInterval*1000,"meanUpdateCPUMs":cpuTotal/Double(count)*1000,"maxUpdateCPUMs":maxCPU*1000,"intervalsOver25ms":over25,"intervalsOver50ms":over50,"scope":"display-link interval and main-thread update CPU; not GPU timing"]
        queue.async {
            guard let folder=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask).first,
                  let data=try? JSONSerialization.data(withJSONObject:values,options:[.sortedKeys,.prettyPrinted]) else { return }
            try? data.write(to:folder.appendingPathComponent("BattleFrameTiming.json"),options:.atomic)
        }
    }
}

/// The same bars are used in the action panel and actor status headers.
final class MeadowBattleResourceBar: UIView {
    private let caption=UILabel()
    private let track=UIView()
    private let fill=UIView()
    private var fraction:CGFloat=0
    override init(frame:CGRect) {
        super.init(frame:frame);isAccessibilityElement=true
        caption.font=MeadowPreviewPalette.font(17);caption.textColor=MeadowPreviewPalette.ink
        track.backgroundColor=UIColor(red:0.03,green:0.07,blue:0.05,alpha:0.95)
        track.layer.borderColor=MeadowPreviewPalette.border.cgColor;track.layer.borderWidth=1;track.layer.cornerRadius=3;track.clipsToBounds=true
        addSubview(caption);addSubview(track);track.addSubview(fill)
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    func show(_ name:String,value:Int,maximum:Int,color:UIColor) {
        caption.text="\(name)  \(value)/\(maximum)";fill.backgroundColor=color
        fraction=CGFloat(max(0,min(value,maximum)))/CGFloat(max(1,maximum))
        accessibilityLabel=name;accessibilityValue="\(value)/\(maximum)";setNeedsLayout()
    }
    override func layoutSubviews() {
        super.layoutSubviews();caption.frame=CGRect(x:0,y:0,width:bounds.width,height:23)
        track.frame=CGRect(x:0,y:27,width:bounds.width,height:max(8,bounds.height-29))
        fill.frame=CGRect(x:1,y:1,width:max(0,(track.bounds.width-2)*fraction),height:max(0,track.bounds.height-2))
    }
}

/// Discrete AP uses the same panel slot in solo and party scenes.
final class MeadowBattleActionPointsView:UIView {
    private let caption=UILabel()
    private var remaining=0,maximum=0
    override init(frame:CGRect) {
        super.init(frame:frame);isOpaque=false;isAccessibilityElement=true
        caption.font=MeadowPreviewPalette.font(17);caption.textColor=MeadowPreviewPalette.ink;caption.text="行动"
        addSubview(caption);accessibilityLabel="行动点数"
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    func show(value:Int,maximum:Int) {
        self.maximum=max(0,maximum);remaining=max(0,min(value,self.maximum))
        accessibilityValue="剩余\(remaining)，上限\(self.maximum)";setNeedsDisplay()
    }
    override func layoutSubviews() {
        super.layoutSubviews();caption.frame=CGRect(x:0,y:0,width:bounds.width,height:23);setNeedsDisplay()
    }
    override func draw(_ rect:CGRect) {
        guard maximum>0 else { return }
        let side=min(18,max(1,bounds.height-25),bounds.width/CGFloat(maximum)),gap=min(9,max(0,(bounds.width-side*CGFloat(maximum))/CGFloat(maximum)))
        let cy=CGFloat(26)+side/2
        for i in 0..<maximum {
            let cx=side/2+CGFloat(i)*(side+gap),h=side/2
            let path=UIBezierPath();path.move(to:CGPoint(x:cx,y:cy-h));path.addLine(to:CGPoint(x:cx+h,y:cy));path.addLine(to:CGPoint(x:cx,y:cy+h));path.addLine(to:CGPoint(x:cx-h,y:cy));path.close()
            (i<remaining ? MeadowPreviewPalette.gold:MeadowPreviewPalette.gold.withAlphaComponent(0.10)).setFill();path.fill()
            MeadowPreviewPalette.gold.withAlphaComponent(i<remaining ? 1:0.45).setStroke();path.lineWidth=1.25;path.stroke()
        }
    }
}

final class MeadowBattleVitalsView: UIView {
    private let title=UILabel()
    private let track=UIView(),fill=UIView(),shieldTrack=UIView(),shieldFill=UIView()
    private var hp:CGFloat=1,ward:CGFloat=0
    override init(frame:CGRect) {
        super.init(frame:frame);isUserInteractionEnabled=false;isAccessibilityElement=true
        backgroundColor=MeadowPreviewPalette.panel;layer.cornerRadius=5
        title.font=MeadowPreviewPalette.font(17);title.textColor=MeadowPreviewPalette.ink
        title.textAlignment = .center
        for bar in [track,shieldTrack] { bar.backgroundColor=UIColor.black.withAlphaComponent(0.7);addSubview(bar) }
        fill.backgroundColor = .systemGreen;shieldFill.backgroundColor = .systemCyan
        track.addSubview(fill);shieldTrack.addSubview(shieldFill);addSubview(title)
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    func show(name:String,hp:Int,maximum:Int,shield:Int) {
        title.text="\(name)  \(hp)/\(maximum)";self.hp=CGFloat(hp)/CGFloat(maximum);ward=CGFloat(min(8,shield))/8
        shieldTrack.isHidden=shield==0
        accessibilityLabel=name;accessibilityValue="生命\(hp)/\(maximum)，护盾\(shield)";setNeedsLayout()
    }
    override func layoutSubviews() {
        super.layoutSubviews();title.frame=CGRect(x:3,y:1,width:bounds.width-6,height:23)
        track.frame=CGRect(x:6,y:27,width:bounds.width-12,height:7);fill.frame=CGRect(x:0,y:0,width:track.bounds.width*hp,height:7)
        shieldTrack.frame=CGRect(x:6,y:36,width:bounds.width-12,height:4);shieldFill.frame=CGRect(x:0,y:0,width:shieldTrack.bounds.width*ward,height:4)
    }
}
