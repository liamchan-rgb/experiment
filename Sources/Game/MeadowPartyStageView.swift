import UIKit
import ClassroomGameCore
import MeadowBattleSupport

final class MeadowPartyStageView:UIView {
    var onChoose:((String)->Void)?
    private let world=UIView(),dim=UIView()
    private let clock=MeadowBattleSceneClock()
    private let fx=MeadowPartyEffectsView()
    private var actors:[String:MeadowBattleActorView]=[:]
    private var monsters:[String:UIImageView]=[:],winds:[String:UIImageView]=[:]
    private var shadows:[String:MeadowBattleGroundingView]=[:]
    private var attached:[String:MeadowBattleAttachedSkillsView]=[:]
    private var labels:[String:UILabel]=[:]
    private var state:GameState?
    private var sceneTime=0.0,startAt=0.0
    private var intent:PartyIntent?
    private var impact:(()->OperationReceipt?)?
    private var completion:(()->Void)?
    private var fired=false
    private var focus:PartyAction?,focusTarget="p1",focusAt=0.0
    private var recovery:[String:Double]=[:],formation:[String:Double]=[:],birth:[String:Double]=[:],contact:[String:Double]=[:],broken:[String:Double]=[:],deaths:[String:Double]=[:],hurt:[String:Double]=[:]
    private var fallen:[String:Double]=[:]
    private var poseKeys:[String:String]=[:]
    private var messages:[MeadowPartyMessage]=[]
    private var emissions:[MeadowBattleLightEmission]=[]
    var isPlaying:Bool { intent != nil }
    override init(frame:CGRect) {
        super.init(frame:frame);backgroundColor=MeadowPreviewPalette.panel;clipsToBounds=true;layer.cornerRadius=12
        addSubview(world);world.bounds=CGRect(x:0,y:0,width:1000,height:600);world.clipsToBounds=true
        for (i,name) in MeadowBattleCanvasGeometry.sceneLayerOrder.enumerated() {
            let image=MeadowBattlePlateProcessor.image(named:name,role:[.farForest,.ground,.midground,.foreground][i])
            let view=UIImageView(image:image);view.frame=CGRect(x:0,y:-200,width:1000,height:1000*1201/1309)
            view.layer.zPosition=i==3 ? 900:CGFloat(-100+i);world.addSubview(view)
        }
        dim.backgroundColor = .black;dim.frame=world.bounds;dim.layer.zPosition=100;dim.isUserInteractionEnabled=false;world.addSubview(dim)
        for id in ["p1","p2","m1","m2"] {
            let shadow:MeadowBattleGroundingView
            if id.hasPrefix("p") {
                let actor=MeadowBattleActorView(frame:.zero);actors[id]=actor;world.addSubview(actor)
                let skills=MeadowBattleAttachedSkillsView(frame:.zero);actor.addSubview(skills);attached[id]=skills
                shadow=MeadowBattleGroundingView(image:actor.silhouette,soleY:214,contacts:[])
                actor.addGestureRecognizer(UITapGestureRecognizer(target:self,action:#selector(tapped(_:))));actor.accessibilityIdentifier=id
            } else {
                let image=UIImage(named:"MeadowBattleForestWarden")
                let view=UIImageView(image:image);monsters[id]=view;view.isUserInteractionEnabled=true;view.layer.magnificationFilter = .nearest
                world.addSubview(view);view.accessibilityIdentifier=id;view.addGestureRecognizer(UITapGestureRecognizer(target:self,action:#selector(tapped(_:))))
                let wind=UIImageView();wind.layer.magnificationFilter = .nearest;wind.layer.zPosition=950;winds[id]=wind;world.addSubview(wind)
                shadow=MeadowBattleGroundingView(image:image,soleY:240,contacts:[.init(point:CGPoint(x:84,y:240),radius:15),.init(point:CGPoint(x:172,y:240),radius:15),.init(point:CGPoint(x:230,y:240),radius:15),.init(point:CGPoint(x:314,y:240),radius:15)])
            }
            shadows[id]=shadow;shadow.layer.zPosition=200;shadow.frame=world.bounds;world.addSubview(shadow)
            let label=UILabel();label.font=MeadowPreviewPalette.font(18);label.textColor=MeadowPreviewPalette.ink;label.textAlignment = .center;label.backgroundColor=MeadowPreviewPalette.panel.withAlphaComponent(0.85);label.layer.cornerRadius=4;label.clipsToBounds=true;label.layer.zPosition=1100;labels[id]=label;world.addSubview(label)
        }
        fx.frame=world.bounds;fx.layer.zPosition=1000;world.addSubview(fx)
        clock.onTick={ [weak self] delta in self?.advance(delta) }
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    @objc private func tapped(_ r:UITapGestureRecognizer) { if !isPlaying,let id=r.view?.accessibilityIdentifier { onChoose?(id) } }
    func start() { sceneTime=0;recovery=[:];formation=[:];birth=[:];contact=[:];broken=[:];deaths=[:];hurt=[:];messages=[];emissions=[];poseKeys=[:];fallen=[:];clock.start() }
    func stop() { clock.stop();intent=nil;impact=nil;completion=nil;focus=nil }
    func show(_ value:GameState,friend:String,foe:String,current:String?) {
        state=value;fx.friend=friend;fx.foe=foe
        for (id,label) in labels { label.text=(id==current ? "▶ ":"")+(value.units[id]?.name ?? id) }
        render()
    }
    func preview(_ action:PartyAction?,target:String) { guard !isPlaying else { return };focus=action;focusTarget=target;focusAt=sceneTime }
    func play(_ value:PartyIntent,before:GameState,onImpact:@escaping ()->OperationReceipt?,completion:@escaping ()->Void) {
        intent=value;state=before;startAt=sceneTime;self.impact=onImpact;self.completion=completion;fired=false;focus=nil
        let delayed=sceneTime+max(0,value.action.impact-0.46)
        for id in value.targets {
            guard let unit=before.units[id] else { continue }
            if ["support","heal","revive"].contains(value.action.visual),unit.health<unit.baseAttributes.maximumHealth { recovery[id]=delayed }
            if ["support","guard"].contains(value.action.visual),unit.shield<([PartyAction.shieldPotion].contains(value.action) ? 8:4) { formation[id]=delayed }
        }
        render()
    }
    private func advance(_ delta:Double) {
        guard window != nil,!isHidden else { clock.stop();return }
        sceneTime += delta
        emissions.removeAll { sceneTime-$0.startedAt>3 };messages.removeAll { sceneTime-$0.at>1.0 }
        if let value=intent {
            let age=sceneTime-startAt
            let end=value.enemy ? 1.10:value.action.duration
            let hit=value.enemy ? 0.46:value.action.impact
            if !fired,age>=hit {
                fired=true;let callback=impact;impact=nil
                if let receipt=callback?() { apply(receipt,intent:value) }
            }
            render()
            if age>=end { intent=nil;impact=nil;let finished=completion;completion=nil;MeadowBattleFrameTiming.flush();finished?() }
        } else { render() }
    }
    private func apply(_ receipt:OperationReceipt,intent:PartyIntent) {
        state=receipt.after
        for id in ["p1","p2","m1","m2"] {
            guard let before=receipt.before.units[id],let after=receipt.after.units[id],let foot=PartyVisual.feet[id] else { continue }
            let heal=max(0,after.health-before.health),damage=max(0,before.health-after.health),gain=max(0,after.shield-before.shield),absorbed=max(0,before.shield-after.shield)
            let point=CGPoint(x:foot.x,y:foot.y-(id.hasPrefix("p") ? 65:90))
            if heal>0 { messages.append(.init(text:"＋\(heal)",point:point,at:sceneTime,color:.systemGreen)) }
            if gain>0 { birth[id]=sceneTime;messages.append(.init(text:"盾 ＋\(gain)",point:CGPoint(x:point.x,y:point.y+24),at:sceneTime,color:.systemCyan)) }
            if after.damageBuff != before.damageBuff,let b=after.damageBuff { messages.append(.init(text:"伤害 ＋\(b.amount)",point:point,at:sceneTime,color:MeadowPreviewPalette.gold)) }
            if damage>0 || absorbed>0 {
                hurt[id]=sceneTime
                messages.append(.init(text:damage>0 ? "−\(damage)":"格挡",point:point,at:sceneTime,color:damage>0 ? .white:.systemCyan))
                let p=CGPoint(x:point.x,y:point.y)
                emissions.append(.init(kind:absorbed>0 ? .shieldContact:.strike,startedAt:sceneTime,x:Double(p.x),y:Double(p.y),groundY:foot.y))
            }
            if absorbed>0 { contact[id]=sceneTime;if after.shield==0 { broken[id]=sceneTime;emissions.append(.init(kind:.shieldBreak,startedAt:sceneTime,x:foot.x,y:foot.y-60,groundY:foot.y)) } }
            if before.isAlive && !after.isAlive && after.kind == .monster { deaths[id]=sceneTime;emissions.append(.init(kind:.death,startedAt:sceneTime,x:Double(point.x),y:Double(point.y),groundY:foot.y)) }
            if before.isAlive && !after.isAlive && after.kind == .player { recovery[id]=nil;fallen[id]=sceneTime }
        }
    }
    private func render() {
        guard let state else { return }
        CATransaction.begin();CATransaction.setDisableActions(true);defer { CATransaction.commit() }
        let age=sceneTime-startAt;let moving=PartyVisual.travel(intent,age:age)
        for id in ["p1","p2","m1","m2"] {
            guard let unit=state.units[id],let f=PartyVisual.feet[id] else { continue }
            let offset=intent?.actor==id ? moving:PartyPoint(0,0)
            let foot=CGPoint(x:f.x+offset.x,y:f.y+offset.y)
            if let actor=actors[id] {
                let pose=PartyVisual.pose(unit:unit,intent:intent,age:age,time:sceneTime,hurtAge:hurt[id].map { sceneTime-$0 },blocked:unit.shield>0 || (hurt[id] != nil && broken[id]==hurt[id]),downAge:fallen[id].map { sceneTime-$0 })
                let clip=pose.clip,progress=pose.progress
                actor.setPose(clip:clip,progress:CGFloat(progress))
                let s=CGFloat(PartyVisual.heroScale),root=actor.poseRootOffset
                actor.frame=CGRect(x:foot.x-123*s+root.x*s,y:foot.y-214*s+root.y*s,width:256*s,height:256*s)
                actor.layer.zPosition=CGFloat(f.y)
                let key="\(clip)-\(Int((progress*24).rounded()))"
                if key != poseKeys[id] { shadows[id]?.update(image:actor.poseSilhouette,soleY:actor.poseFootAnchorPx.y,contacts:actor.poseContacts.map { .init(point:$0,radius:12) });poseKeys[id]=key }
                attached[id]?.frame=actor.bounds
                attached[id]?.update(shield:unit.shield,preview:0,time:sceneTime,formation:unit.shield==0 ? formation[id].flatMap { sceneTime-$0<1.0 ? sceneTime-$0:nil }:nil,formationBase:0,birth:birth[id].map { sceneTime-$0 },contact:contact[id].map { sceneTime-$0 },broken:broken[id].map { sceneTime-$0 },recovery:unit.isAlive ? recovery[id].map { sceneTime-$0 }:nil)
                shadows[id]?.spriteFrame=actor.frame
                labels[id]?.frame=CGRect(x:f.x-78,y:f.y-140,width:156,height:26)
            } else if let view=monsters[id] {
                let s=CGFloat(PartyVisual.enemyScale)
                view.frame=CGRect(x:foot.x-178.5*s,y:foot.y-240*s,width:384*s,height:256*s);view.layer.zPosition=CGFloat(f.y)
                if let at=deaths[id] {
                    let d=sceneTime-at;view.image=MeadowBattleVFXAssets.body[MeadowBattleVisualMotion.bodyFrame(d)]
                    winds[id]?.image=MeadowBattleVFXAssets.wind[MeadowBattleVisualMotion.windFrame(d)]
                    winds[id]?.frame=CGRect(x:CGFloat(f.x)-178.5*s,y:CGFloat(f.y)-272*s,width:448*s,height:320*s)
                    winds[id]?.isHidden=d>=MeadowBattleVisualMotion.deathDuration
                    shadows[id]?.alpha=CGFloat(1-PartyVisual.smooth(d/0.75))
                } else {
                    let p=intent?.actor==id ? min(1,age/0.96):0
                    view.image=MeadowBattleEnemyFrames.image(progress:CGFloat(p));winds[id]?.isHidden=true;shadows[id]?.alpha=1
                    let key="monster-\(Int(p*8))"
                    if poseKeys[id] != key { shadows[id]?.update(image:view.image,soleY:240,contacts:MeadowBattleEnemyFrames.feet(progress:CGFloat(p)).map { .init(point:$0,radius:15) });poseKeys[id]=key }
                }
                shadows[id]?.spriteFrame=view.frame
                labels[id]?.frame=CGRect(x:f.x-72,y:f.y-218,width:144,height:26)
            }
        }
        let envelope=PartyVisual.pulse(age,0,0.4,1.8)
        dim.alpha=intent == nil ? (focus==nil ? 0:CGFloat(0.2*PartyVisual.smooth((sceneTime-focusAt)/0.25))) : CGFloat(envelope*(intent?.action.visual=="attack" ? 0.58:0.32))
        fx.intent=intent;fx.age=age;fx.time=sceneTime;fx.focus=focus;fx.focusTarget=focusTarget
        fx.messages=messages;fx.particles=emissions.flatMap { e in MeadowBattleLightField.sample(e.kind,age:sceneTime-e.startedAt,originX:e.x,originY:e.y,groundY:e.groundY) }
        fx.setNeedsDisplay()
    }
    override func layoutSubviews() { super.layoutSubviews();let scale=min(bounds.width/1000,bounds.height/600);world.center=CGPoint(x:bounds.midX,y:bounds.midY);world.transform=CGAffineTransform(scaleX:scale,y:scale) }
}
struct MeadowPartyMessage { let text:String;let point:CGPoint;let at:Double;let color:UIColor }

private final class MeadowPartyEffectsView:UIView {
    var intent:PartyIntent?,focus:PartyAction?
    var friend="p1",foe="m1",focusTarget="p1"
    var age=0.0,time=0.0
    var messages:[MeadowPartyMessage]=[]
    var particles:[MeadowBattleLightParticle]=[]
    override init(frame:CGRect) { super.init(frame:frame);isOpaque=false;isUserInteractionEnabled=false }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func draw(_ rect:CGRect) {
        guard let ctx=UIGraphicsGetCurrentContext() else { return }
        func sprite(_ im:UIImage,_ p:PartyPoint,_ w:Double,_ h:Double,_ alpha:Double) { guard alpha>0 else { return };im.draw(in:CGRect(x:p.x-w/2,y:p.y-h/2,width:w,height:h),blendMode:.plusLighter,alpha:CGFloat(alpha)) }
        func glow(_ p:PartyPoint,_ rx:Double,_ ry:Double,_ alpha:Double,_ color:UIColor) { guard alpha>0 else { return };MeadowBattleGlowCache.image(color).draw(in:CGRect(x:p.x-rx,y:p.y-ry,width:rx*2,height:ry*2),blendMode:.plusLighter,alpha:CGFloat(alpha)) }
        if intent==nil {
            for (id,color) in [(friend,UIColor.systemGreen),(foe,MeadowPreviewPalette.gold)] {
                if let p=PartyVisual.feet[id] { ctx.setStrokeColor(color.withAlphaComponent(0.65).cgColor);ctx.setLineWidth(2);ctx.strokeEllipse(in:CGRect(x:p.x-36,y:p.y-7,width:72,height:14)) }
            }
        }
        if let intent {
            let visual=intent.action.visual
            if visual=="support" {
                let from=PartyVisual.chest(intent.actor),to=PartyVisual.chest(intent.target)
                let alpha=PartyVisual.pulse(age,0.05,0.36,1.12)
                let path=UIBezierPath();path.move(to:CGPoint(x:from.x,y:from.y));path.addQuadCurve(to:CGPoint(x:to.x,y:to.y),controlPoint:CGPoint(x:(from.x+to.x)/2,y:min(from.y,to.y)-90))
                ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setShadow(offset:.zero,blur:14,color:UIColor.systemGreen.cgColor)
                UIColor.systemGreen.withAlphaComponent(CGFloat(alpha*0.25)).setStroke();path.lineWidth=8;path.stroke();MeadowPreviewPalette.gold.withAlphaComponent(CGFloat(alpha*0.8)).setStroke();path.lineWidth=2;path.stroke();ctx.restoreGState()
                for p in PartyVisual.trail(age:age,from:from,to:to) { sprite(MeadowBattleVFXAssets.healStar,PartyPoint(p.x,p.y),p.size,p.size,p.alpha) }
                let power=PartyVisual.pulse(age,0,0.56,1.5)
                if let foot=PartyVisual.feet[intent.target] { glow(foot,110,26,power*0.5,.systemGreen) }
            }
            if visual=="rally" {
                for id in intent.targets {
                    let p=PartyVisual.chest(id),power=PartyVisual.pulse(age,0.05,0.46,1.5)
                    glow(p,48,85,power*0.25,.orange)
                    for mote in PartyVisual.rally(age:age,at:p) { sprite(MeadowBattleVFXAssets.ember,PartyPoint(mote.x,mote.y),mote.size*0.5,mote.size*2,mote.alpha) }
                    for i in 0..<3 {
                        let local=age-Double(i)*0.10,a=PartyVisual.pulse(local,0,0.28,0.85)
                        guard a>0 else { continue }
                        let y=p.y+10-local*75
                        let path=UIBezierPath();path.move(to:CGPoint(x:p.x-14,y:y+10));path.addLine(to:CGPoint(x:p.x,y:y));path.addLine(to:CGPoint(x:p.x+14,y:y+10))
                        MeadowPreviewPalette.gold.withAlphaComponent(CGFloat(a)).setStroke();path.lineWidth=3;path.stroke()
                    }
                }
            }
            if intent.action.isItem,let foot=PartyVisual.feet[intent.target] {
                let name="MeadowParty"+intent.action.rawValue.prefix(1).uppercased()+intent.action.rawValue.dropFirst()
                if let image=UIImage(named:name) { sprite(image,PartyPoint(foot.x,foot.y-130-age*15),38,38,PartyVisual.pulse(age,0,0.25,0.85)) }
            }
            if visual=="revive",let foot=PartyVisual.feet[intent.target] {
                let a=PartyVisual.pulse(age,0,0.72,1.9)
                sprite(MeadowBattleVFXAssets.healShaft,PartyPoint(foot.x,foot.y-80),120,220,a)
                for p in PartyVisual.rally(age:age,at:PartyPoint(foot.x,foot.y-60)) { sprite(MeadowBattleVFXAssets.healStar,PartyPoint(p.x,p.y),p.size,p.size,p.alpha) }
            }
            if visual=="attack",let foot=PartyVisual.feet[intent.target] {
                let a=age-(intent.enemy ? 0.46:1.048),p=PartyPoint(foot.x-(intent.enemy ? -10:80),foot.y-(intent.enemy ? 65:72))
                let power=PartyVisual.pulse(a,-0.035,0.035,0.52)
                glow(p,140,140,power*0.48,.orange);glow(foot,170,30,power*0.65,.orange)
                if a>=0,a<0.7 {
                    sprite(MeadowBattleVFXAssets.burst,p,150+a*140,150+a*140,power)
                    if !intent.enemy { sprite(MeadowBattleVFXAssets.heavyArc,p,210+a*240,210+a*240,power*0.9) }
                }
            }
        }
        var pools=0
        for p in particles {
            let at=PartyPoint(p.x,p.y)
            if p.id%6==0 { glow(at,22,20,p.alpha*0.2,p.cyan ? .cyan:.orange) }
            if let age=p.groundAge,age<0.24,pools<12 {
                let point=PartyPoint(p.groundX,p.groundY),a=(1-age/0.24)*p.alpha
                glow(point,34,10,a*0.6,p.cyan ? .cyan:.orange);sprite(p.cyan ? MeadowBattleVFXAssets.wardHit:MeadowBattleVFXAssets.groundSpark,point,30,12,a);pools += 1
            }
            ctx.saveGState();ctx.translateBy(x:p.x,y:p.y);ctx.rotate(by:p.angle)
            let image=p.cyan ? MeadowBattleVFXAssets.shard:MeadowBattleVFXAssets.ember
            image.draw(in:CGRect(x:-p.size/2,y:-p.size/3,width:p.size,height:p.size*0.67),blendMode:.plusLighter,alpha:CGFloat(p.alpha));ctx.restoreGState()
        }
        for m in messages {
            let age=time-m.at,alpha=1-PartyVisual.smooth((age-0.65)/0.35)
            let attrs:[NSAttributedString.Key:Any]=[.font:MeadowPreviewPalette.font(24,.heavy),.foregroundColor:m.color.withAlphaComponent(CGFloat(alpha)),.strokeColor:UIColor.black.withAlphaComponent(CGFloat(alpha)),.strokeWidth:-3]
            NSAttributedString(string:m.text,attributes:attrs).draw(at:CGPoint(x:m.point.x+90,y:m.point.y-55-age*26))
        }
    }
}
