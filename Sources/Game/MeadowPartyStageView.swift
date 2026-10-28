import UIKit
import ClassroomGameCore
import MeadowBattleSupport

final class MeadowPartyStageView:UIView {
    var onChoose:((String)->Void)?
    private let world=UIView(),dim=UIView()
    private let clock=MeadowBattleSceneClock()
    private let fx=MeadowPartyEffectsView()
    private var actors:[String:MeadowBattleActorView]=[:]
    private let afterimages=(0..<3).map { _ in UIImageView() }
    private var monsters:[String:UIImageView]=[:],winds:[String:UIImageView]=[:]
    private var shadows:[String:MeadowBattleGroundingView]=[:]
    private var attached:[String:MeadowBattleAttachedSkillsView]=[:]
    private var labels:[String:MeadowBattleVitalsView]=[:]
    private var monsterFlash:[String:UIImageView]=[:]
    private let diceView=MeadowBattleDiceView()
    private var catalog=try? GameCatalog.initial()
    private var current:String?
    private var diceActor="p1",diceAction:PartyAction?,diceVisibleAt=0.0,diceSettledAt:Double?,diceExitAt:Double?,diceConfirmedAt:Double?
    private var dimFrom=0.0,dimTarget=0.0,dimChangedAt=0.0,castDim=0.0
    private var state:GameState?
    private var sceneTime=0.0,startAt=0.0
    private var intent:PartyIntent?
    private var impact:(()->OperationReceipt?)?
    private var completion:(()->Void)?
    private var naturalTwenty=false
    private var fired=false,meetsShield=false
    var actorInAction:String? { intent?.actor }
    private var focus:PartyAction?,focusTarget="p1",focusAt=0.0
    private var recovery:[String:Double]=[:],formation:[String:Double]=[:],birth:[String:Double]=[:],contact:[String:Double]=[:],broken:[String:Double]=[:],deaths:[String:Double]=[:],hurt:[String:Double]=[:]
    private var fallen:[String:Double]=[:]
    private var victoryAt:Double?
    private var poseKeys:[String:String]=[:]
    private var messages:[MeadowPartyMessage]=[]
    private var emissions:[MeadowBattleLightEmission]=[]
    var isPlaying:Bool { intent != nil }
    override init(frame:CGRect) {
        super.init(frame:frame);backgroundColor=MeadowPreviewPalette.panel;clipsToBounds=true;layer.cornerRadius=12
        addSubview(world);world.bounds=CGRect(x:0,y:0,width:1000,height:600);world.clipsToBounds=false
        for (i,name) in MeadowBattleCanvasGeometry.sceneLayerOrder.enumerated() {
            let image=MeadowBattlePlateProcessor.image(named:name,role:[.farForest,.ground,.midground,.foreground][i])
            let view=UIImageView(image:image);view.frame=CGRect(x:0,y:-159,width:1000,height:1000*1201/1309)
            view.layer.zPosition=i==3 ? 900:CGFloat(-100+i);world.addSubview(view)
        }
        dim.backgroundColor = .black;dim.frame=CGRect(x:0,y:-500,width:1000,height:1600);dim.layer.zPosition=100;dim.isUserInteractionEnabled=false;world.addSubview(dim)
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
                let flash=UIImageView();flash.isUserInteractionEnabled=false;flash.layer.magnificationFilter = .nearest;monsterFlash[id]=flash;world.addSubview(flash)
                world.addSubview(view);view.accessibilityIdentifier=id;view.addGestureRecognizer(UITapGestureRecognizer(target:self,action:#selector(tapped(_:))))
                let wind=UIImageView();wind.layer.magnificationFilter = .nearest;wind.layer.zPosition=950;winds[id]=wind;world.addSubview(wind)
                shadow=MeadowBattleGroundingView(image:image,soleY:240,contacts:[.init(point:CGPoint(x:84,y:240),radius:15),.init(point:CGPoint(x:172,y:240),radius:15),.init(point:CGPoint(x:230,y:240),radius:15),.init(point:CGPoint(x:314,y:240),radius:15)])
            }
            shadows[id]=shadow;shadow.layer.zPosition=200;shadow.frame=world.bounds;world.addSubview(shadow)
            let label=MeadowBattleVitalsView();label.layer.zPosition=1100;labels[id]=label;world.addSubview(label)
        }
        diceView.layer.zPosition=1200;world.addSubview(diceView)
        for ghost in afterimages { ghost.isHidden=true;ghost.isUserInteractionEnabled=false;ghost.layer.magnificationFilter = .nearest;world.addSubview(ghost) }
        fx.frame=world.bounds;fx.layer.zPosition=1000;world.addSubview(fx)
        clock.onTick={ [weak self] delta in self?.advance(delta) }
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    @objc private func tapped(_ r:UITapGestureRecognizer) { if !isPlaying,let id=r.view?.accessibilityIdentifier { onChoose?(id) } }
    func start() { victoryAt=nil;sceneTime=0;recovery=[:];formation=[:];birth=[:];contact=[:];broken=[:];deaths=[:];hurt=[:];messages=[];emissions=[];poseKeys=[:];fallen=[:];diceAction=nil;diceConfirmedAt=nil;diceView.confirmationAge=nil;diceView.dice=[];diceSettledAt=nil;diceExitAt=nil;dimFrom=0;dimTarget=0;clock.start() }
    func stop() { clock.stop();intent=nil;impact=nil;completion=nil;focus=nil }
    func show(_ value:GameState,friend:String,foe:String,current:String?,catalog:GameCatalog) {
        state=value;self.current=current;self.catalog=catalog;fx.friend=friend;fx.foe=foe
        for (id,label) in labels {
            guard let u=value.units[id] else { continue }
            label.show(name:(id==current ? "▶ ":"")+u.name,hp:u.health,maximum:(try? GameRules.attributes(u,catalog:catalog).maximumHealth) ?? u.baseAttributes.maximumHealth,shield:u.shield)
        }
        render()
    }
    private func maximumHealth(_ unit:GameUnit)->Int {
        guard let catalog else { return unit.baseAttributes.maximumHealth };return (try? GameRules.attributes(unit,catalog:catalog).maximumHealth) ?? unit.baseAttributes.maximumHealth
    }
    private func previewDarkness()->Double { dimFrom+(dimTarget-dimFrom)*PartyVisual.smooth((sceneTime-dimChangedAt)/0.28) }
    func preview(_ action:PartyAction?,target:String) {
        guard !isPlaying,action != focus || target != focusTarget else { return }
        dimFrom=previewDarkness();dimTarget=action.map(BattleDice.darkness) ?? 0;dimChangedAt=sceneTime
        focus=action;focusTarget=target;focusAt=sceneTime
        if let action,let state,let actorID=current,let actor=state.units[actorID],let targetUnit=state.units[target],let catalog {
            diceActor=actorID;diceAction=action;diceVisibleAt=sceneTime;diceSettledAt=nil;diceExitAt=nil
            diceView.locked=false;diceConfirmedAt=nil
            diceView.dice=BattleDice.channels(action,actor:actor,target:targetUnit,catalog:catalog)
        } else { diceExitAt=sceneTime }
    }
    func play(_ value:PartyIntent,before:GameState,confirmed:OperationReceipt?,onImpact:@escaping ()->OperationReceipt?,completion:@escaping ()->Void) {
        castDim=previewDarkness();dimFrom=0;dimTarget=0;dimChangedAt=sceneTime
        if let actor=before.units[value.actor],let target=before.units[value.target],let catalog {
            if diceAction != value.action || diceActor != value.actor { diceVisibleAt=sceneTime }
            diceAction=value.action;diceActor=value.actor;diceSettledAt=nil;diceExitAt=nil
            diceView.dice=BattleDice.channels(value.action,actor:actor,target:target,catalog:catalog,receipt:confirmed);diceView.locked=confirmed != nil;diceConfirmedAt=confirmed == nil ? nil:sceneTime
        }
        naturalTwenty=confirmed?.dice.contains { $0.naturalTwenty } ?? false
        intent=value;state=before;startAt=sceneTime;self.impact=onImpact;self.completion=completion;fired=false;focus=nil;meetsShield=(before.units[value.target]?.shield ?? 0)>0
        let delayed=sceneTime+max(0,value.action.impact-0.46)
        for id in value.targets {
            guard let unit=before.units[id] else { continue }
            if ["support","heal","revive"].contains(value.action.visual),unit.health<maximumHealth(unit) { recovery[id]=delayed }
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
        if receipt.dice.contains(where: { $0.naturalTwenty }) { let p=PartyVisual.hitPoint(target:intent.target,weaponID:intent.weaponID);messages.append(.init(text:"自然20",point:CGPoint(x:p.x,y:p.y-55),at:sceneTime,color:.systemCyan,atImpact:true)) }
        if let actor=receipt.before.units[intent.actor],let target=receipt.before.units[intent.target],let catalog {
            diceView.dice=BattleDice.channels(intent.action,actor:actor,target:target,catalog:catalog,receipt:receipt);diceSettledAt=sceneTime
        }
        for id in ["p1","p2","m1","m2"] {
            guard let before=receipt.before.units[id],let after=receipt.after.units[id],let foot=PartyVisual.feet[id] else { continue }
            let heal=max(0,after.health-before.health),damage=max(0,before.health-after.health),gain=max(0,after.shield-before.shield),absorbed=max(0,before.shield-after.shield)
            let shieldHit=absorbed>0 && id.hasPrefix("p")
            let registered=PartyVisual.hitPoint(target:id,shielded:shieldHit,weaponID:intent.weaponID)
            let point=["greatSword","legendaryStaff"].contains(intent.weaponID ?? "") && id.hasPrefix("m") ? CGPoint(x:registered.x,y:registered.y):CGPoint(x:foot.x+(shieldHit ? (5+240*0.41)*PartyVisual.heroScale:(id.hasPrefix("m") ? -80:0)),y:foot.y-(id.hasPrefix("p") ? 65:72))
            if heal>0 {
                let shift=intent.actor==id ? PartyVisual.travel(intent,age:sceneTime-startAt):PartyPoint(0,0)
                if intent.action == .ambush { recovery[id]=sceneTime }
                messages.append(.init(text:"＋\(heal)",point:CGPoint(x:point.x+shift.x,y:point.y+shift.y),at:sceneTime,color:.systemGreen))
            }
            if gain>0 { birth[id]=sceneTime;messages.append(.init(text:"盾 ＋\(gain)",point:CGPoint(x:point.x,y:point.y+24),at:sceneTime,color:.systemCyan)) }
            if after.damageBuff != before.damageBuff,let b=after.damageBuff { messages.append(.init(text:"伤害 ＋\(b.amount)",point:point,at:sceneTime,color:MeadowPreviewPalette.gold)) }
            if damage>0 || absorbed>0 {
                hurt[id]=sceneTime
                let hit=PartyVisual.hitPoint(target:id,shielded:absorbed>0,weaponID:intent.weaponID)
                messages.append(.init(text:damage>0 ? "−\(damage)":"格挡",point:CGPoint(x:hit.x,y:hit.y),at:sceneTime,color:damage>0 ? .white:.systemCyan,atImpact:true))
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
        let defeated=state.units.values.filter { $0.kind == .monster }
        let won = !defeated.isEmpty && defeated.allSatisfy { !$0.isAlive } && state.players.contains { $0.isAlive }
        if won && intent == nil { if victoryAt == nil { victoryAt=sceneTime } }
        else if !won { victoryAt=nil }
        CATransaction.begin();CATransaction.setDisableActions(true);defer { CATransaction.commit() }
        let age=sceneTime-startAt;let moving=PartyVisual.travel(intent,age:age,shielded:meetsShield)
        let trails=PartyVisual.afterimages(intent,age:age)
        for (i,ghost) in afterimages.enumerated() {
            guard i<trails.count,let intent,let actor=actors[intent.actor],let foot=PartyVisual.feet[intent.actor] else { ghost.isHidden=true;continue }
            let trail=trails[i],pose=MeadowBattleAnimation.sample(clip:"attack",progress:CGFloat(trail.progress)),s=PartyVisual.heroScale
            ghost.image=actor.trailImage(progress:CGFloat(trail.progress));ghost.alpha=trail.alpha;ghost.isHidden=false;ghost.layer.zPosition=foot.y-1
            ghost.frame=CGRect(x:foot.x+trail.offset.x+(Double(pose.rootOffset.x)-123)*s,y:foot.y+trail.offset.y+(Double(pose.rootOffset.y)-214)*s,width:256*s,height:256*s)
        }
        for id in ["p1","p2","m1","m2"] {
            guard let unit=state.units[id],let f=PartyVisual.feet[id] else { continue }
            labels[id]?.isHidden=unit.kind == .monster && !unit.isAlive
            let offset=intent?.actor==id ? moving:PartyPoint(0,0)
            let foot=CGPoint(x:f.x+offset.x,y:f.y+offset.y)
            if let actor=actors[id] {
                let pose=PartyVisual.pose(unit:unit,intent:intent,age:age,time:sceneTime,hurtAge:hurt[id].map { sceneTime-$0 },blocked:unit.shield>0 || (hurt[id] != nil && broken[id]==hurt[id]),downAge:fallen[id].map { sceneTime-$0 },victoryAge:victoryAt.map { sceneTime-$0 })
                actor.setWeaponAsset(HeroFrames.weaponVisual(unit.equipment.weapon)?.battleAsset)
                actor.setArmor(unit.equipment.armor)
                let clip=pose.clip,progress=pose.progress
                actor.setPose(clip:clip,progress:CGFloat(progress))
                let s=CGFloat(PartyVisual.heroScale),root=actor.poseRootOffset
                actor.frame=CGRect(x:foot.x-123*s+root.x*s,y:foot.y-214*s+root.y*s,width:256*s,height:256*s)
                actor.layer.zPosition=CGFloat(f.y)
                let key="\(clip)-\(Int((progress*24).rounded()))-\(unit.equipment.weapon ?? "none")-\(unit.equipment.armor ?? "none")"
                if key != poseKeys[id] { shadows[id]?.update(image:actor.poseSilhouette,soleY:actor.poseFootAnchorPx.y,contacts:actor.poseContacts.map { .init(point:$0,radius:12) });poseKeys[id]=key }
                attached[id]?.frame=actor.bounds
                attached[id]?.update(shield:unit.shield,preview:0,time:sceneTime,formation:unit.shield==0 ? formation[id].flatMap { sceneTime-$0<1.0 ? sceneTime-$0:nil }:nil,formationBase:0,birth:birth[id].map { sceneTime-$0 },contact:contact[id].map { sceneTime-$0 },broken:broken[id].map { sceneTime-$0 },recovery:unit.isAlive ? recovery[id].map { sceneTime-$0 }:nil)
                shadows[id]?.spriteFrame=actor.frame
                labels[id]?.frame=CGRect(x:f.x-88,y:f.y-170,width:176,height:44)
            } else if let view=monsters[id] {
                let s=CGFloat(PartyVisual.enemyScale)
                view.frame=CGRect(x:foot.x-178.5*s,y:foot.y-240*s,width:384*s,height:256*s);view.layer.zPosition=CGFloat(f.y)
                monsterFlash[id]?.alpha=0
                if let at=deaths[id] {
                    let d=sceneTime-at;view.image=MeadowBattleVFXAssets.body[MeadowBattleVisualMotion.bodyFrame(d)]
                    winds[id]?.image=MeadowBattleVFXAssets.wind[MeadowBattleVisualMotion.windFrame(d)]
                    winds[id]?.frame=CGRect(x:CGFloat(f.x)-178.5*s,y:CGFloat(f.y)-272*s,width:448*s,height:320*s)
                    winds[id]?.isHidden=d>=MeadowBattleVisualMotion.deathDuration
                    shadows[id]?.alpha=CGFloat(1-PartyVisual.smooth(d/0.75))
                } else {
                    let motion=PartyVisual.monster(time:sceneTime+(id=="m2" ? 0.7:0),attackAge:intent?.actor==id ? age:nil,hurtAge:hurt[id].map { sceneTime-$0 },preparing:current==id && intent==nil)
                    let p=motion.progress
                    view.frame=CGRect(x:foot.x-178.5*s+motion.recoil,y:foot.y-240*s*motion.scaleY,width:384*s,height:256*s*motion.scaleY)
                    view.image=MeadowBattleEnemyFrames.image(progress:CGFloat(p));winds[id]?.isHidden=true;shadows[id]?.alpha=1
                    let key="monster-\(Int(p*8))"
                    if poseKeys[id] != key { shadows[id]?.update(image:view.image,soleY:240,contacts:MeadowBattleEnemyFrames.feet(progress:CGFloat(p)).map { .init(point:$0,radius:15) });poseKeys[id]=key;monsterFlash[id]?.image=view.image?.withTintColor(.white,renderingMode:.alwaysOriginal) }
                    monsterFlash[id]?.frame=view.frame;monsterFlash[id]?.alpha=motion.flash;monsterFlash[id]?.layer.zPosition=view.layer.zPosition+1
                }
                shadows[id]?.spriteFrame=view.frame
                labels[id]?.frame=CGRect(x:f.x-84,y:f.y-242,width:168,height:44)
            }
        }
        if let value=intent {
            let peak=max(BattleDice.darkness(value.action),value.action.isOffensive ? 0.58:0.32)
            let build=castDim+(peak-castDim)*PartyVisual.smooth(age/0.4)
            dim.alpha=CGFloat(build*(1-PartyVisual.smooth((age-1.2)/0.6)))
        } else { dim.alpha=CGFloat(previewDarkness()) }
        let anchor=PartyVisual.diceAnchor(actor:diceActor,intent:intent,age:age,shielded:meetsShield,diceCount:diceView.dice.count)
        diceView.frame=CGRect(x:anchor.x-110,y:anchor.y,width:220,height:100)
        diceView.time=sceneTime;diceView.visibleAge=sceneTime-diceVisibleAt
        diceView.confirmationAge=diceConfirmedAt.map { sceneTime-$0 }
        diceView.resolvedAge=diceSettledAt.map { sceneTime-$0 };diceView.exitAge=diceExitAt.map { sceneTime-$0 };diceView.setNeedsDisplay()
        fx.naturalTwenty=naturalTwenty;fx.intent=intent;fx.meetsShield=meetsShield;fx.age=age;fx.time=sceneTime;fx.focus=focus;fx.focusTarget=focusTarget
        fx.messages=messages;fx.particles=emissions.flatMap { e in MeadowBattleLightField.sample(e.kind,age:sceneTime-e.startedAt,originX:e.x,originY:e.y,groundY:e.groundY) }
        fx.recoveryLights=state.players.compactMap { unit in
            guard unit.isAlive,let at=recovery[unit.id],let foot=PartyVisual.feet[unit.id] else { return nil }
            let power=MeadowBattleRecoveryField.pulse(sceneTime-at),shift=intent?.actor==unit.id ? moving:PartyPoint(0,0)
            return (PartyPoint(foot.x+shift.x,foot.y+shift.y),power)
        }
        fx.setNeedsDisplay()
    }
    override func layoutSubviews() { super.layoutSubviews();let scale=bounds.width/1000;world.center=CGPoint(x:bounds.midX,y:bounds.midY);world.transform=CGAffineTransform(scaleX:scale,y:scale) }
}
struct MeadowPartyMessage { let text:String;let point:CGPoint;let at:Double;let color:UIColor;var atImpact=false }

private final class MeadowPartyEffectsView:UIView {
    var intent:PartyIntent?,focus:PartyAction?
    var friend="p1",foe="m1",focusTarget="p1"
    var meetsShield=false
    var age=0.0,time=0.0
    var messages:[MeadowPartyMessage]=[]
    var naturalTwenty=false
    var particles:[MeadowBattleLightParticle]=[]
    var recoveryLights:[(PartyPoint,Double)]=[]
    override init(frame:CGRect) { super.init(frame:frame);isOpaque=false;isUserInteractionEnabled=false }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func draw(_ rect:CGRect) {
        guard let ctx=UIGraphicsGetCurrentContext() else { return }
        func sprite(_ im:UIImage,_ p:PartyPoint,_ w:Double,_ h:Double,_ alpha:Double) { guard alpha>0 else { return };im.draw(in:CGRect(x:p.x-w/2,y:p.y-h/2,width:w,height:h),blendMode:.plusLighter,alpha:CGFloat(alpha)) }
        func glow(_ p:PartyPoint,_ rx:Double,_ ry:Double,_ alpha:Double,_ color:UIColor) { guard alpha>0 else { return };MeadowBattleGlowCache.image(color).draw(in:CGRect(x:p.x-rx,y:p.y-ry,width:rx*2,height:ry*2),blendMode:.plusLighter,alpha:CGFloat(alpha)) }
        for (foot,power) in recoveryLights { glow(foot,105,27,power*0.65,.systemGreen);glow(PartyPoint(foot.x,foot.y-70),42,85,power*0.12,.systemGreen) }
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
            if intent.ranged,let foot=PartyVisual.feet[intent.actor] {
                let tip=BowRig.releaseArrowTip
                let from=PartyPoint(foot.x+(tip.x-123)*PartyVisual.heroScale,foot.y+(tip.y-214)*PartyVisual.heroScale)
                let to=PartyVisual.hitPoint(target:intent.target,shielded:meetsShield)
                if let arrow=BowRig.projectile(age:age,from:from,to:to,impact:intent.action.impact,scale:PartyVisual.heroScale) {
                    let a=arrow.tail,b=arrow.tip
                    ctx.saveGState();ctx.setLineCap(.round)
                    ctx.setShadow(offset:.zero,blur:8,color:MeadowPreviewPalette.gold.cgColor)
                    ctx.setStrokeColor(MeadowPreviewPalette.gold.withAlphaComponent(0.5).cgColor);ctx.setLineWidth(5)
                    ctx.move(to:CGPoint(x:a.x,y:a.y));ctx.addLine(to:CGPoint(x:b.x,y:b.y));ctx.strokePath()
                    ctx.setStrokeColor(MeadowPreviewPalette.ink.cgColor);ctx.setLineWidth(2)
                    ctx.move(to:CGPoint(x:a.x,y:a.y));ctx.addLine(to:CGPoint(x:b.x,y:b.y));ctx.strokePath();ctx.restoreGState()
                }
            }
            if intent.weaponID=="greatSword",!intent.enemy,visual=="attack",let from=PartyVisual.feet[intent.actor] {
                let points=GreatSwordRig.trail(age:age,from:from,to:PartyVisual.hitPoint(target:intent.target,shielded:meetsShield,weaponID:intent.weaponID),scale:PartyVisual.heroScale)
                if points.count>1 {
                    let power=PartyVisual.pulse(GreatSwordRig.artTime(age:age),0.86,1.0275,1.20)
                    ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setLineCap(.round)
                    ctx.setShadow(offset:.zero,blur:7,color:MeadowPreviewPalette.gold.cgColor)
                    for (width,alpha) in [(10.0,0.22),(4.0,0.70),(1.5,0.95)] {
                        ctx.setLineWidth(width);ctx.setStrokeColor(MeadowPreviewPalette.ink.withAlphaComponent(CGFloat(power*alpha)).cgColor)
                        ctx.beginPath();ctx.move(to:CGPoint(x:points[0].x,y:points[0].y));for p in points.dropFirst() { ctx.addLine(to:CGPoint(x:p.x,y:p.y)) };ctx.strokePath()
                    };ctx.restoreGState()
                }
            }
            if intent.magical,let foot=PartyVisual.feet[intent.actor],let targetFoot=PartyVisual.feet[intent.target] {
                let sample=LegendaryStaffRig.effect(age:age,foot:foot,target:PartyVisual.hitPoint(target:intent.target,shielded:meetsShield,weaponID:intent.weaponID),groundY:targetFoot.y,scale:PartyVisual.heroScale,naturalTwenty:naturalTwenty)
                MeadowStaffEffectPainter.draw(sample,in:ctx)
            }
            if visual=="attack",!intent.magical,let foot=PartyVisual.feet[intent.target] {
                let a=age-(intent.enemy ? 0.46:1.048),p=PartyVisual.hitPoint(target:intent.target,shielded:meetsShield,weaponID:intent.weaponID)
                let power=PartyVisual.pulse(a,-0.035,0.035,0.52)
                glow(p,140,140,power*0.48,.orange);glow(foot,170,30,power*0.65,.orange)
                if a>=0,a<0.7 {
                    sprite(MeadowBattleVFXAssets.burst,p,150+a*140,150+a*140,power)
                    if !intent.enemy && !intent.ranged { sprite(MeadowBattleVFXAssets.heavyArc,p,210+a*240,210+a*240,power*0.9) }
                }
            }
            if visual=="ambush",let foot=PartyVisual.feet[intent.target] {
                let at=PartyPoint(foot.x-80,foot.y-72),power=PartyVisual.pulse(age,0.72,0.755,1.14)
                glow(at,128,115,power*0.52,.systemYellow);glow(foot,170,27,power*0.70,.systemGreen)
                sprite(MeadowBattleVFXAssets.burst,at,130,130,power*0.72)
                sprite(MeadowBattleVFXAssets.groundSpark,PartyPoint(foot.x-40,foot.y-3),170,22,power*0.70)
                for slash in PartyVisual.ambushSlashes(age:age,at:at) {
                    let path=UIBezierPath();for (j,p) in slash.points.enumerated() { if j==0 { path.move(to:CGPoint(x:p.x,y:p.y)) } else { path.addLine(to:CGPoint(x:p.x,y:p.y)) } }
                    ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setLineCap(.round)
                    UIColor.systemGreen.withAlphaComponent(slash.alpha*0.35).setStroke();path.lineWidth=12;path.stroke()
                    MeadowPreviewPalette.ink.withAlphaComponent(slash.alpha).setStroke();path.lineWidth=3;path.stroke();ctx.restoreGState()
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
            let label=NSAttributedString(string:m.text,attributes:attrs),size=label.size()
            let p=m.atImpact ? PartyVisual.damageLabelOrigin(at:PartyPoint(m.point.x,m.point.y),width:size.width,height:size.height,age:age):PartyPoint(m.point.x+90,m.point.y-55-age*26)
            label.draw(at:CGPoint(x:p.x,y:p.y))
        }
    }
}

/// Both battle layouts draw the same continuously sampled staff geometry.
enum MeadowStaffEffectPainter {
    static func draw(_ q:StaffEffectSample,in ctx:CGContext) {
        func glow(_ p:PartyPoint,_ rx:Double,_ ry:Double,_ alpha:Double) {
            guard alpha>0 else { return }
            MeadowBattleGlowCache.image(.systemCyan).draw(in:CGRect(x:p.x-rx,y:p.y-ry,width:rx*2,height:ry*2),blendMode:.plusLighter,alpha:CGFloat(min(1,alpha)))
        }
        let s=q.scale,p=q.impactPower
        ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setLineCap(.round)
        glow(q.gem,48*s,40*s,q.charge*0.36)
        if let head=q.head {
            glow(head,40*s,30*s,0.45)
            for (w,a) in [(13.0,0.41),(5.0,0.73),(2.0,0.98)] {
                ctx.setStrokeColor((w==2 ? UIColor.white:UIColor.systemCyan).withAlphaComponent(a).cgColor);ctx.setLineWidth(w*s)
                ctx.beginPath();for (i,p) in q.trail.enumerated() { if i==0 { ctx.move(to:CGPoint(x:p.x,y:p.y)) } else { ctx.addLine(to:CGPoint(x:p.x,y:p.y)) } };ctx.strokePath()
            }
            ctx.setFillColor(UIColor.white.withAlphaComponent(0.94).cgColor);ctx.fillEllipse(in:CGRect(x:head.x-5*s,y:head.y-5*s,width:10*s,height:10*s))
        }
        glow(q.impact,108*s,100*s,p*0.58);glow(q.ground,112*s,22*s,p*0.52)
        if p>0 {
            let r=q.burstRadius,x=q.impact.x,y=q.impact.y
            let path=UIBezierPath();let pts=[CGPoint(x:x,y:y-r*1.4),CGPoint(x:x+r*0.23,y:y-r*0.2),CGPoint(x:x+r,y:y),CGPoint(x:x+r*0.23,y:y+r*0.2),CGPoint(x:x,y:y+r*1.4),CGPoint(x:x-r*0.23,y:y+r*0.2),CGPoint(x:x-r,y:y),CGPoint(x:x-r*0.23,y:y-r*0.2)]
            path.move(to:pts[0]);for v in pts.dropFirst() { path.addLine(to:v) };path.close();UIColor.systemCyan.withAlphaComponent(min(0.8,p*0.78)).setFill();path.fill()
            ctx.setFillColor(UIColor.white.withAlphaComponent(min(1,p)).cgColor);ctx.fillEllipse(in:CGRect(x:x-r*0.18,y:y-r*0.18,width:r*0.36,height:r*0.36))
        }
        for ray in q.rays {
            ctx.setStrokeColor(UIColor.systemCyan.withAlphaComponent(ray.alpha).cgColor);ctx.setLineWidth(2*s);ctx.beginPath()
            for (i,p) in ray.points.enumerated() { if i==0 { ctx.move(to:CGPoint(x:p.x,y:p.y)) } else { ctx.addLine(to:CGPoint(x:p.x,y:p.y)) } };ctx.strokePath()
        }
        for mote in q.motes {
            let p=PartyPoint(mote.x,mote.y)
            if mote.id%6==0 { glow(p,18*s,14*s,mote.alpha*0.2) }
            ctx.setFillColor((mote.id%3==0 ? UIColor.white:UIColor.systemCyan).withAlphaComponent(mote.alpha).cgColor);ctx.fillEllipse(in:CGRect(x:p.x-mote.size/2,y:p.y-mote.size/2,width:mote.size,height:mote.size))
            if abs(p.y-q.ground.y)<5*s { glow(p,24*s,6*s,mote.alpha*0.25) }
        }
        ctx.restoreGState()
    }
}
final class MeadowStaffEffectsView:UIView {
    var sample:StaffEffectSample?
    override init(frame:CGRect) { super.init(frame:frame);isOpaque=false;isUserInteractionEnabled=false }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func draw(_ rect:CGRect) { if let q=sample,let ctx=UIGraphicsGetCurrentContext() { MeadowStaffEffectPainter.draw(q,in:ctx) } }
}
