import UIKit
import ClassroomGameCore
import MeadowBattleSupport

final class MeadowPartyStageView:UIView {
    var onChoose:((String)->Void)?
    var onPresentationChanged:(()->Void)?
    private let world=UIView(),dim=UIView(),wash=UIView()
    private let clock=MeadowBattleSceneClock()
    private let fx=MeadowPartyEffectsView()
    private var monsterIDs=["m1","m2"]
    private var renderIDs:[String] {["p1","p2"]+monsterIDs}
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
    private var recoveryTier:[String:HealingEffectTier]=[:]
    private var fallen:[String:Double]=[:]
    private var victoryAt:Double?
    private var poseKeys:[String:String]=[:]
    private var messages:[MeadowPartyMessage]=[]
    /// Presentation-only hit feel (see MeadowBattleHitFeel): per struck monster, and the latest blow for the camera.
    private var hitFeel:[String:MeadowPartyHitEvent]=[:]
    private var kickFeel:(at:Double,tier:MeadowBattleHitTier,direction:Double)?
    private var emissions:[MeadowBattleLightEmission]=[]
    private var skillVFX:[MeadowPartySkillVFXEvent]=[]
    private var procVFX:[MeadowPartyProcEvent]=[]
    /// Where every unit is drawn right now (after travel and knock-back); effects follow these.
    private var liveFeet:[String:PartyPoint]=[:]
    private var washBase=UIColor.clear
    private struct PendingStatusCue {
        let unitID:String,heal:Int,shieldGain:Int
        let at:Double,point:CGPoint,supportUnit:Bool
    }
    private var pendingStatusCues:[PendingStatusCue]=[]
    private var statusSnapshots:[String:(health:Int,shield:Int)]=[:]
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
        // Pane-wide colour wash for skill light and screen flashes: same coverage as `dim`, so neither has an edge at the world rectangle.
        wash.backgroundColor = .clear;wash.frame=dim.frame;wash.layer.zPosition=999;wash.isUserInteractionEnabled=false;world.addSubview(wash)
        for id in renderIDs { installUnit(id) }
        diceView.layer.zPosition=1200;world.addSubview(diceView)
        for ghost in afterimages { ghost.isHidden=true;ghost.isUserInteractionEnabled=false;ghost.layer.magnificationFilter = .nearest;world.addSubview(ghost) }
        fx.frame=world.bounds;fx.layer.zPosition=1000;world.addSubview(fx)
        fx.onFlash={ [weak self] flash in guard let self else { return };self.wash.backgroundColor=flash ?? self.washBase }
        clock.onTick={ [weak self] delta in self?.advance(delta) }
    }
    private func installUnit(_ id:String) {
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
            let skills=MeadowBattleAttachedSkillsView(frame:.zero);attached[id]=skills;world.addSubview(skills)
            world.addSubview(view);view.accessibilityIdentifier=id;view.addGestureRecognizer(UITapGestureRecognizer(target:self,action:#selector(tapped(_:))))
            let wind=UIImageView();wind.layer.magnificationFilter = .nearest;wind.layer.zPosition=950;winds[id]=wind;world.addSubview(wind)
            shadow=MeadowBattleGroundingView(image:image,soleY:240,contacts:[.init(point:CGPoint(x:84,y:240),radius:15),.init(point:CGPoint(x:172,y:240),radius:15),.init(point:CGPoint(x:230,y:240),radius:15),.init(point:CGPoint(x:314,y:240),radius:15)])
        }
        shadows[id]=shadow;shadow.layer.zPosition=200;shadow.frame=world.bounds;world.addSubview(shadow)
        let label=MeadowBattleVitalsView();label.layer.zPosition=1100;labels[id]=label;world.addSubview(label)
    
    }
    func configureMonsters(_ ids:[String]) {
        guard ids != monsterIDs else{return}
        for id in monsterIDs {
            monsters.removeValue(forKey:id)?.removeFromSuperview();winds.removeValue(forKey:id)?.removeFromSuperview()
            attached.removeValue(forKey:id)?.removeFromSuperview();monsterFlash.removeValue(forKey:id)?.removeFromSuperview();shadows.removeValue(forKey:id)?.removeFromSuperview();labels.removeValue(forKey:id)?.removeFromSuperview()
        }
        monsterIDs=ids;for id in ids {installUnit(id)}
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    @objc private func tapped(_ r:UITapGestureRecognizer) { if !isPlaying,let id=r.view?.accessibilityIdentifier { onChoose?(id) } }
    func start() { MeadowBattleVFXAssets.prewarm();victoryAt=nil;sceneTime=0;recovery=[:];recoveryTier=[:];formation=[:];birth=[:];contact=[:];broken=[:];deaths=[:];hurt=[:];hitFeel=[:];kickFeel=nil;messages=[];emissions=[];skillVFX=[];procVFX=[];pendingStatusCues=[];statusSnapshots=[:];poseKeys=[:];fallen=[:];diceAction=nil;diceConfirmedAt=nil;diceView.confirmationAge=nil;diceView.dice=[];diceSettledAt=nil;diceExitAt=nil;dimFrom=0;dimTarget=0;clock.start() }
    func stop() { MeadowMonsterFrames.retain([]);clock.stop();intent=nil;impact=nil;completion=nil;focus=nil;skillVFX=[];procVFX=[];pendingStatusCues=[];statusSnapshots=[:] }
    func displayedVitals(for unitID:String,health:Int,shield:Int)->(health:Int,shield:Int) { statusSnapshots[unitID] ?? (health,shield) }
    func show(_ value:GameState,friend:String,foe:String,current:String?,catalog:GameCatalog) {
        state=value;self.current=current;self.catalog=catalog;fx.friend=friend;fx.foe=foe
        MeadowMonsterFrames.retain(Set(value.units.values.filter{$0.kind == .monster && renderIDs.contains($0.id)}.compactMap{MonsterVisualSpec.find($0.templateID)?.id}))
        for id in renderIDs where value.units[id]?.isAlive==false {
            if id.hasPrefix("m"),deaths[id]==nil {deaths[id]=sceneTime-MeadowBattleVisualMotion.deathDuration}
            if id.hasPrefix("p"),fallen[id]==nil {fallen[id]=sceneTime-2}
        }
        for (id,label) in labels {
            guard let u=value.units[id] else { continue }
            let visible=displayedVitals(for:id,health:u.health,shield:u.shield)
            label.show(name:(id==current ? "▶ ":"")+u.name,hp:visible.health,maximum:(try? GameRules.attributes(u,catalog:catalog).maximumHealth) ?? u.baseAttributes.maximumHealth,shield:visible.shield,maximumShield:MonsterVisualSpec.find(u.templateID)?.shieldCapacity(catalog:catalog) ?? 8)
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
        if value.action.isOffensive { MeadowBattleHaptics.prepare() }
        castDim=previewDarkness();dimFrom=0;dimTarget=0;dimChangedAt=sceneTime
        if let actor=before.units[value.actor],let target=before.units[value.target],let catalog {
            if diceAction != value.action || diceActor != value.actor { diceVisibleAt=sceneTime }
            diceAction=value.action;diceActor=value.actor;diceSettledAt=nil;diceExitAt=nil
            diceView.dice=BattleDice.channels(value.action,actor:actor,target:target,catalog:catalog,receipt:confirmed,sourceSkillID:value.sourceSkillID);diceView.locked=confirmed != nil;diceConfirmedAt=confirmed == nil ? nil:sceneTime
        }
        naturalTwenty=confirmed?.dice.contains { $0.naturalTwenty } ?? false
        intent=value;state=before;startAt=sceneTime;self.impact=onImpact;self.completion=completion;fired=false;focus=nil;meetsShield=(before.units[value.target]?.shield ?? 0)>0
        if let proc=MeadowSkillProcedural.info[value.action.rawValue] {
            let templates=before.units.mapValues(\.templateID)
            func target(_ id:String)->MeadowSkillProcedural.Target? {
                guard let foot=PartyVisual.foot(id) else { return nil }
                let chest=PartyVisual.skillEffectCenter(targets:[id],actor:value.actor,templates:templates)
                return .init(chest:.init(chest.x,chest.y),foot:.init(foot.x,foot.y))
            }
            if let casterFoot=PartyVisual.foot(value.actor) {
                let casterChest=PartyVisual.skillEffectCenter(targets:[value.actor],actor:value.actor,templates:templates)
                let list=value.targets.compactMap(target)
                if let first=list.first {
                    let geo=MeadowSkillProcedural.Geometry(caster:.init(casterChest.x,casterChest.y),casterFoot:.init(casterFoot.x,casterFoot.y),targets:list,ground:first.foot.y)
                    // The effect starts early enough that its release lands on the rule's impact moment, inside the existing cast motion.
                    let start=sceneTime+max(0,value.impactAge-proc.release)
                    let ids=value.targets.filter { PartyVisual.foot($0) != nil }
                    procVFX.append(MeadowPartyProcEvent(skill:value.action.rawValue,start:start,direction:first.chest.x>=geo.caster.x ? 1:-1,geo:geo,casterID:value.actor,targetIDs:ids))
                }
            }
        } else if let spec=value.action.skillVFX {
            let hitAge=value.impactAge
            let groundYs=value.targets.compactMap { PartyVisual.foot($0)?.y }
            let groundY=groundYs.isEmpty ? (PartyVisual.foot(value.actor)?.y ?? PartyVisual.height):groundYs.reduce(0,+)/Double(groundYs.count)
            let templates=before.units.mapValues(\.templateID)
            var event=MeadowPartySkillVFXEvent(spec:spec,startedAt:spec.startTime(actionStart:sceneTime,impactAge:hitAge),center:PartyVisual.skillEffectCenter(targets:value.targets,actor:value.actor,templates:templates),groundY:groundY)
            event.actionStart=sceneTime;event.impactAt=sceneTime+hitAge
            if let foot=PartyVisual.foot(value.actor) { event.casterFoot=foot;event.casterChest=PartyPoint(foot.x+5*PartyVisual.heroScale,foot.y-70*PartyVisual.heroScale) }
            event.targets=value.targets.compactMap { id in PartyVisual.foot(id).map { MeadowPartySkillTarget(chest:PartyVisual.skillEffectCenter(targets:[id],actor:value.actor,templates:templates),foot:$0) } }
            skillVFX.append(event)
        }
        let delayed=sceneTime+max(0,value.action.impact-0.46)
        let statusAge=value.action.statusVFXCueAge ?? value.action.impact
        let statusCueIsLate=statusAge>value.action.impact+0.0001
        for id in value.targets {
            guard let unit=before.units[id] else { continue }
            if !statusCueIsLate,["support","guard"].contains(value.action.visual),unit.shield<([PartyAction.shieldPotion].contains(value.action) ? 8:4) { formation[id]=delayed }
        }
        render()
    }
    private func advance(_ delta:Double) {
        guard window != nil,!isHidden else { clock.stop();return }
        sceneTime += delta
        emissions.removeAll { sceneTime-$0.startedAt>3 };messages.removeAll { sceneTime-$0.at>MeadowBattleNumber.life }
        hitFeel=hitFeel.filter { sceneTime-$0.value.at<1.0 }
        if let k=kickFeel,sceneTime-k.at>=1.0 { kickFeel=nil }
        skillVFX.removeAll { sceneTime-$0.startedAt>$0.lifetime }
        procVFX.removeAll { sceneTime-$0.start>($0.info?.duration ?? 0)+0.1 }
        let due=pendingStatusCues.filter { $0.at<=sceneTime+1e-9 }
        if !due.isEmpty {
            pendingStatusCues.removeAll { $0.at<=sceneTime+1e-9 }
            due.forEach(revealStatusCue)
        }
        if let value=intent {
            let age=sceneTime-startAt
            let end=value.visualDuration
            let hit=value.impactAge
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
        if receipt.dice.contains(where: { $0.naturalTwenty }) { let p=PartyVisual.hitPoint(target:intent.target,weaponID:intent.weaponID,templateID:receipt.before.units[intent.target]?.templateID);messages.append(.init(text:"自然20",point:CGPoint(x:p.x,y:p.y-55),at:sceneTime,color:.systemCyan,atImpact:true,kind:.crit,rank:2,follow:intent.target)) }
        if let actor=receipt.before.units[intent.actor],let target=receipt.before.units[intent.target],let catalog {
            diceView.dice=BattleDice.channels(intent.action,actor:actor,target:target,catalog:catalog,receipt:receipt,sourceSkillID:intent.sourceSkillID);diceSettledAt=sceneTime
        }
        let plainAttack = !intent.enemy && intent.action.visual == "attack" && intent.action.skillVFX == nil
        var strongestHit=0,killedAny=false,blockedAny=false,numberOrder=0
        for id in renderIDs {
            guard let before=receipt.before.units[id],let after=receipt.after.units[id],let foot=PartyVisual.foot(id) else { continue }
            let heal=max(0,after.health-before.health),damage=max(0,before.health-after.health),gain=max(0,after.shield-before.shield),absorbed=max(0,before.shield-after.shield)
            let shieldHit=absorbed>0 && id.hasPrefix("p")
            let statusAt=startAt+(intent.action.statusVFXCueAge ?? intent.action.impact)
            let delayStatus=after.isAlive && (heal>0 || gain>0) && statusAt>sceneTime+0.0001
            let showsBesideOwner=intent.action.isRune || intent.action == .dragonFlame || intent.action == .starlightPulse || intent.action.isNodeSupport
            let registered=PartyVisual.hitPoint(target:id,shielded:shieldHit,weaponID:intent.weaponID,templateID:before.templateID)
            let point=["greatSword","legendaryStaff"].contains(intent.weaponID ?? "") && id.hasPrefix("m") ? CGPoint(x:registered.x,y:registered.y):CGPoint(x:foot.x+(shieldHit ? (5+240*0.41)*PartyVisual.heroScale:(id.hasPrefix("m") ? -80:0)),y:foot.y-(id.hasPrefix("p") ? 65:72))
            if delayStatus {
                statusSnapshots[id]=(before.health,before.shield)
                pendingStatusCues.append(.init(unitID:id,heal:heal,shieldGain:gain,at:statusAt,point:point,supportUnit:showsBesideOwner))
            }
            if heal>0 && !delayStatus {
                let shift=intent.actor==id ? PartyVisual.travel(intent,age:sceneTime-startAt):PartyPoint(0,0)
                recovery[id]=sceneTime
                recoveryTier[id]=HealingEffectTier.classify(actualHPGained:heal)
                messages.append(.init(text:"＋\(heal)",point:CGPoint(x:point.x+shift.x,y:point.y+shift.y),at:sceneTime,color:.systemGreen,supportUnit:showsBesideOwner ? id:nil,kind:.heal))
            }
            if gain>0 && !delayStatus { birth[id]=sceneTime;messages.append(.init(text:"盾 ＋\(gain)",point:CGPoint(x:point.x,y:point.y+(intent.action.isRune || intent.action == .dragonFlame || intent.action.isNodeSupport ? 36:24)),at:sceneTime,color:.systemCyan,supportUnit:showsBesideOwner ? id:nil,supportLine:1,kind:.shield)) }
            if after.damageBuff != before.damageBuff,let b=after.damageBuff { messages.append(.init(text:"伤害 ＋\(b.amount)",point:CGPoint(x:point.x,y:point.y-(intent.action.isRune || intent.action == .dragonFlame || intent.action.isNodeSupport ? 36:0)),at:sceneTime,color:MeadowPreviewPalette.gold,supportUnit:showsBesideOwner ? id:nil,supportLine:(heal>0 || gain>0) ? 2:0,kind:.buff)) }
            if damage>0 || absorbed>0 {
                hurt[id]=sceneTime
                let hit=PartyVisual.hitPoint(target:id,shielded:absorbed>0,weaponID:intent.weaponID,templateID:before.templateID)
                let killedHere=before.isAlive && !after.isAlive
                let hitTier=MeadowBattleHitTier.classify(damage:damage,killed:killedHere)
                if damage>0 { strongestHit=max(strongestHit,damage);if killedHere { killedAny=true } } else { blockedAny=true }
                let popsHere=plainAttack && damage>0 && id.hasPrefix("m")
                if popsHere { hitFeel[id]=MeadowPartyHitEvent(at:sceneTime,tier:hitTier,direction:1,point:CGPoint(x:hit.x,y:hit.y),footX:CGFloat(foot.x),floorY:CGFloat(foot.y)) }
                // Several targets: their numbers follow one another by a beat instead of all appearing on the same frame.
                messages.append(.init(text:damage>0 ? "−\(damage)":"格挡",point:CGPoint(x:hit.x,y:hit.y),at:sceneTime+0.07*Double(numberOrder),color:damage>0 ? .white:.systemCyan,atImpact:true,hitTier:popsHere ? hitTier:nil,kind:damage>0 ? .damage:.block,rank:hitTier.rawValue,follow:id));numberOrder += 1
                let p=CGPoint(x:hit.x,y:hit.y)
                if absorbed>0 || (intent.action.skillVFX == nil && MeadowSkillProcedural.info[intent.action.rawValue] == nil) { emissions.append(.init(kind:absorbed>0 ? .shieldContact:.strike,startedAt:sceneTime,x:Double(p.x),y:Double(p.y),groundY:foot.y)) }
            }
            if absorbed>0 { contact[id]=sceneTime;if after.shield==0 { broken[id]=sceneTime;emissions.append(.init(kind:.shieldBreak,startedAt:sceneTime,x:foot.x,y:foot.y-60,groundY:foot.y)) } }
            if before.isAlive && !after.isAlive && after.kind == .monster { deaths[id]=sceneTime;emissions.append(.init(kind:.death,startedAt:sceneTime,x:registered.x,y:registered.y,groundY:foot.y)) }
            if before.isAlive && !after.isAlive && after.kind == .player { recovery[id]=nil;recoveryTier[id]=nil;fallen[id]=sceneTime }
        }
        if strongestHit>0 {
            let tier=MeadowBattleHitTier.classify(damage:strongestHit,killed:killedAny)
            MeadowBattleHaptics.hit(tier,killed:killedAny)
            if MeadowSkillProcedural.info[intent.action.rawValue] != nil {
                // A procedural skill has its own lens work; the real damage decides how hard it shakes after the release.
                for i in procVFX.indices where procVFX[i].casterID == intent.actor && procVFX[i].skill == intent.action.rawValue { procVFX[i].power=tier.intensity*(killedAny ? 1.12:1) }
            } else { kickFeel=(sceneTime,tier,intent.enemy ? -1:1) }
        } else if blockedAny { MeadowBattleHaptics.blocked() }
        onPresentationChanged?()
    }
    private func revealStatusCue(_ cue:PendingStatusCue) {
        statusSnapshots.removeValue(forKey:cue.unitID)
        if cue.heal>0 {
            recovery[cue.unitID]=cue.at
            recoveryTier[cue.unitID]=HealingEffectTier.classify(actualHPGained:cue.heal)
            let shift=intent?.actor==cue.unitID ? PartyVisual.travel(intent,age:sceneTime-startAt):PartyPoint(0,0)
            messages.append(.init(text:"＋\(cue.heal)",point:CGPoint(x:cue.point.x+shift.x,y:cue.point.y+shift.y),at:cue.at,color:.systemGreen,supportUnit:cue.supportUnit ? cue.unitID:nil,kind:.heal))
        }
        if cue.shieldGain>0 {
            birth[cue.unitID]=cue.at
            messages.append(.init(text:"盾 ＋\(cue.shieldGain)",point:CGPoint(x:cue.point.x,y:cue.point.y+36),at:cue.at,color:.systemCyan,supportUnit:cue.supportUnit ? cue.unitID:nil,supportLine:1,kind:.shield))
        }
        onPresentationChanged?()
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
            guard i<trails.count,let intent,let actor=actors[intent.actor],let foot=PartyVisual.foot(intent.actor) else { ghost.isHidden=true;continue }
            let trail=trails[i],pose=MeadowBattleAnimation.sample(clip:"attack",progress:CGFloat(trail.progress)),s=PartyVisual.heroScale
            ghost.image=actor.trailImage(progress:CGFloat(trail.progress));ghost.alpha=trail.alpha;ghost.isHidden=false;ghost.layer.zPosition=foot.y-1
            ghost.frame=CGRect(x:foot.x+trail.offset.x+(Double(pose.rootOffset.x)-123)*s,y:foot.y+trail.offset.y+(Double(pose.rootOffset.y)-214)*s,width:256*s,height:256*s)
        }
        for id in renderIDs {
            guard let unit=state.units[id],let f=PartyVisual.foot(id) else { continue }
            let shownVitals=displayedVitals(for:id,health:unit.health,shield:unit.shield)
            labels[id]?.isHidden=unit.kind == .monster && !unit.isAlive
            let offset=intent?.actor==id ? moving:PartyPoint(0,0)
            let foot=CGPoint(x:f.x+offset.x,y:f.y+offset.y)
            liveFeet[id]=PartyPoint(Double(foot.x),Double(foot.y))
            if let actor=actors[id] {
                let pose=PartyVisual.pose(unit:unit,intent:intent,age:age,time:sceneTime,hurtAge:hurt[id].map { sceneTime-$0 },blocked:shownVitals.shield>0 || (hurt[id] != nil && broken[id]==hurt[id]),downAge:fallen[id].map { sceneTime-$0 },victoryAge:victoryAt.map { sceneTime-$0 })
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
                attached[id]?.update(shield:shownVitals.shield,preview:0,time:sceneTime,formation:shownVitals.shield==0 ? formation[id].flatMap { sceneTime-$0<1.0 ? sceneTime-$0:nil }:nil,formationBase:0,birth:birth[id].map { sceneTime-$0 },contact:contact[id].map { sceneTime-$0 },broken:broken[id].map { sceneTime-$0 },recovery:unit.isAlive ? recovery[id].map { sceneTime-$0 }:nil,recoveryTier:recoveryTier[id])
                shadows[id]?.spriteFrame=actor.frame
                labels[id]?.frame=CGRect(x:f.x-88,y:f.y-170,width:176,height:44)
            } else if let view=monsters[id] {
                let species=MonsterVisualSpec.find(unit.templateID)
                let s=CGFloat(species?.scale ?? PartyVisual.enemyScale)
                view.frame=CGRect(x:foot.x-178.5*s,y:foot.y-240*s,width:384*s,height:256*s);view.layer.zPosition=CGFloat(f.y)
                monsterFlash[id]?.alpha=0
                let baseFrame=view.frame
                if let at=deaths[id] {
                    let d=sceneTime-at
                    if let species {
                        view.image=MeadowMonsterFrames.image(species.id,index:MonsterVisualSpec.deathFrame(d),death:true)
                        view.frame=CGRect(x:foot.x-178.5*s,y:foot.y-272*s,width:512*s,height:320*s)
                        view.isHidden=d>=MonsterVisualSpec.deathDuration;winds[id]?.isHidden=true
                    }else{
                        view.isHidden=d>=MeadowBattleVisualMotion.deathDuration;view.image=MeadowBattleVFXAssets.body[MeadowBattleVisualMotion.bodyFrame(d)]
                        winds[id]?.image=MeadowBattleVFXAssets.wind[MeadowBattleVisualMotion.windFrame(d)]
                        winds[id]?.frame=CGRect(x:CGFloat(f.x)-178.5*s,y:CGFloat(f.y)-272*s,width:448*s,height:320*s)
                        winds[id]?.isHidden=d>=MeadowBattleVisualMotion.deathDuration
                    }
                    shadows[id]?.alpha=CGFloat(1-PartyVisual.smooth(d/0.75))
                } else {
                    view.isHidden=false
                    let attacking=intent?.actor==id && intent?.action.isOffensive==true
                    let casting=intent?.actor==id && intent?.action.isOffensive==false
                    let feelActive=hitFeel[id].map { sceneTime-$0.at<0.9 } ?? false
                    let motion=PartyVisual.monster(time:sceneTime+(PartyVisual.slot(id)=="m2" ? 0.7:0),attackAge:attacking ? age:nil,hurtAge:feelActive ? nil:hurt[id].map { sceneTime-$0 },preparing:current==id && intent==nil)
                    let p=motion.progress
                    if let species {
                        let index=species.frame(time:sceneTime+Double(PartyVisual.slot(id)=="m2" ? 1:0),attackAge:attacking ? age:nil,castAge:casting ? age:nil,hurtAge:hurt[id].map{sceneTime-$0},preparing:current==id && intent==nil)
                        let key="species-\(species.id)-\(index)"
                        if poseKeys[id] != key {
                            view.image=MeadowMonsterFrames.image(species.id,index:index)
                            shadows[id]?.update(image:view.image,soleY:240,contacts:MeadowMonsterFrames.feet(species.id).map{.init(point:$0,radius:species.id=="slime" ? 25:12)})
                            monsterFlash[id]?.image=view.image?.withTintColor(.white,renderingMode:.alwaysOriginal);poseKeys[id]=key
                        }
                    }else{
                        view.frame=CGRect(x:foot.x-178.5*s+motion.recoil,y:foot.y-240*s*motion.scaleY,width:384*s,height:256*s*motion.scaleY)
                        view.image=MeadowBattleEnemyFrames.image(progress:CGFloat(p))
                        let key="monster-\(Int(p*8))"
                        if poseKeys[id] != key { shadows[id]?.update(image:view.image,soleY:240,contacts:MeadowBattleEnemyFrames.feet(progress:CGFloat(p)).map { .init(point:$0,radius:15) });poseKeys[id]=key;monsterFlash[id]?.image=view.image?.withTintColor(.white,renderingMode:.alwaysOriginal) }
                    }
                    winds[id]?.isHidden=true;shadows[id]?.alpha=1
                    monsterFlash[id]?.frame=view.frame;monsterFlash[id]?.alpha=motion.flash;monsterFlash[id]?.layer.zPosition=view.layer.zPosition+1
                }
                var shadowShift:CGFloat=0
                if deaths[id]==nil,let h=hitFeel[id],sceneTime-h.at<0.9 {
                    let a=sceneTime-h.at,sq=MeadowBattleHitFeel.squash(age:a,tier:h.tier)
                    shadowShift=CGFloat(MeadowBattleHitFeel.knockback(age:a,tier:h.tier,canvasWidth:PartyVisual.width))
                    let f=view.frame,footX=f.minX+f.width*178.5/384,footY=f.minY+f.height*240/256
                    let w=f.width*CGFloat(sq.x),hgt=f.height*CGFloat(sq.y)
                    view.frame=CGRect(x:footX-w*178.5/384+shadowShift,y:footY-hgt*240/256,width:w,height:hgt)
                    monsterFlash[id]?.frame=view.frame;monsterFlash[id]?.alpha=CGFloat(0.45*MeadowBattleHitFeel.flash(age:a))
                }
                liveFeet[id]=PartyPoint(Double(foot.x+shadowShift),Double(foot.y))
                attached[id]?.frame=CGRect(x:foot.x-192*s,y:foot.y-321*s,width:384*s,height:384*s)
                attached[id]?.layer.zPosition=view.layer.zPosition+2
                attached[id]?.update(shield:unit.isAlive ? shownVitals.shield:0,preview:0,time:sceneTime,formation:shownVitals.shield==0 ? formation[id].flatMap{sceneTime-$0<1.0 ? sceneTime-$0:nil}:nil,formationBase:0,birth:birth[id].map{sceneTime-$0},contact:contact[id].map{sceneTime-$0},broken:broken[id].map{sceneTime-$0},recovery:nil,recoveryTier:nil)
                shadows[id]?.spriteFrame=species == nil ? view.frame:baseFrame.offsetBy(dx:shadowShift,dy:0)
                labels[id]?.frame=CGRect(x:f.x-84,y:f.y-(species == nil ? 256*Double(s)+34:224*Double(s)+46),width:168,height:44)
            }
        }
        if let value=intent {
            let peak=max(BattleDice.darkness(value.action),value.action.isOffensive ? 0.58:0.32)
            let build=castDim+(peak-castDim)*PartyVisual.smooth(age/0.4)
            dim.alpha=CGFloat((value.action.isRune || value.action == .dragonFlame) ? SpellbladeEffects.darkness(value.action,age:age,from:castDim):build*(1-PartyVisual.smooth((age-1.2)/0.6)))
        } else { dim.alpha=CGFloat(previewDarkness()) }
        // One pane-wide grade for every skill: a dark tint (the dim view) and a faint colour wash. Both overlays cover the whole
        // pane, so the brightness is the same everywhere; nothing is filled only inside the world rectangle any more.
        var grade=0.0,gradeTint=UIColor.black,washColor=UIColor.clear
        for e in procVFX {
            guard let info=e.info else { continue }
            let lit=MeadowSkillProcedural.light(skill:e.skill,t:sceneTime-e.start),a=lit*info.dim*0.55
            if a>grade { grade=a;gradeTint=UIColor(red:CGFloat(info.dimTint.r*0.1),green:CGFloat(info.dimTint.g*0.1),blue:CGFloat(info.dimTint.b*0.12),alpha:1) }
            if lit>0.01 { let tone=MeadowSkillProcedural.tone(e.skill);washColor=UIColor(red:CGFloat(tone.r/255),green:CGFloat(tone.g/255),blue:CGFloat(tone.b/255),alpha:CGFloat(lit*0.035)) }
        }
        for e in skillVFX {
            let age=sceneTime-e.startedAt
            guard age>=0,age<e.spec.duration else { continue }
            let a=MeadowSkillAmbientLight.level(age:age,peak:e.spec.peakTime,duration:e.spec.duration)*0.26
            if a>grade { grade=a;gradeTint=UIColor(red:0.06,green:0.05,blue:0.10,alpha:1) }
        }
        dim.backgroundColor=grade>0.004 ? gradeTint:.black
        dim.alpha=max(dim.alpha,CGFloat(grade))
        washBase=washColor;wash.backgroundColor=washColor
        let anchor=PartyVisual.diceAnchor(actor:diceActor,intent:intent,age:age,shielded:meetsShield,diceCount:diceView.dice.count,monsterTemplateID:state.units[diceActor]?.templateID)
        diceView.frame=CGRect(x:anchor.x-110,y:anchor.y,width:220,height:100)
        diceView.time=sceneTime;diceView.visibleAge=sceneTime-diceVisibleAt
        diceView.confirmationAge=diceConfirmedAt.map { sceneTime-$0 }
        diceView.resolvedAge=diceSettledAt.map { sceneTime-$0 };diceView.exitAge=diceExitAt.map { sceneTime-$0 };diceView.setNeedsDisplay()
        fx.templates=state.units.mapValues(\.templateID);fx.naturalTwenty=naturalTwenty;fx.intent=intent;fx.meetsShield=meetsShield;fx.age=age;fx.time=sceneTime;fx.focus=focus;fx.focusTarget=focusTarget
        fx.messages=messages;fx.skillEffects=skillVFX;fx.particles=emissions.flatMap { e in MeadowBattleLightField.sample(e.kind,age:sceneTime-e.startedAt,originX:e.x,originY:e.y,groundY:e.groundY) }
        fx.recoveryLights=state.units.values.filter{renderIDs.contains($0.id)}.compactMap { unit in
            guard unit.isAlive,let at=recovery[unit.id],let foot=PartyVisual.foot(unit.id) else { return nil }
            let power=recoveryTier[unit.id]?.lightEnvelope(at:sceneTime-at) ?? 0,shift=intent?.actor==unit.id ? moving:PartyPoint(0,0)
            return (PartyPoint(foot.x+shift.x,foot.y+shift.y),power)
        }
        let healTemplates=state.units.mapValues(\.templateID)
        fx.monsterRecoveries=monsterIDs.compactMap {id in
            guard state.units[id]?.isAlive==true,let at=recovery[id],let tier=recoveryTier[id],let foot=liveFeet[id] ?? PartyVisual.foot(id) else{return nil}
            let baseFoot=PartyVisual.foot(id) ?? foot,baseChest=PartyVisual.skillEffectCenter(targets:[id],actor:id,templates:healTemplates)
            return (foot:foot,chest:PartyPoint(foot.x+(baseChest.x-baseFoot.x),foot.y+(baseChest.y-baseFoot.y)),tier:tier,age:sceneTime-at)
        }
        fx.allyRecoveries=state.units.values.filter{renderIDs.contains($0.id) && $0.kind != .monster}.compactMap { unit in
            guard unit.isAlive,let at=recovery[unit.id],let tier=recoveryTier[unit.id],let foot=PartyVisual.foot(unit.id) else { return nil }
            let base=liveFeet[unit.id] ?? foot
            return (foot:base,chest:PartyPoint(base.x+5*PartyVisual.heroScale,base.y-70*PartyVisual.heroScale),tier:tier,age:sceneTime-at)
        }
        fx.procEffects=procVFX;fx.liveFeet=liveFeet
        if let intent,(intent.action.isRune || intent.action == .dragonFlame),let catalog,MeadowSkillProcedural.info[intent.action.rawValue] == nil {
            fx.runes=SpellbladeEffects.sample(action:intent.action,age:age,actor:intent.actor,target:intent.target,recipients:SpellbladeEffects.recipients(intent,catalog:catalog),weaponID:intent.weaponID,targets:intent.targets,templates:state.units.mapValues(\.templateID))
        } else { fx.runes=nil }
        fx.hits=Array(hitFeel.values)
        var kick=MeadowBattleHitFeel.Camera.zero
        if let k=kickFeel,sceneTime-k.at<0.9,!UIAccessibility.isReduceMotionEnabled { kick=MeadowBattleHitFeel.camera(age:sceneTime-k.at,tier:k.tier,direction:k.direction) }
        if !UIAccessibility.isReduceMotionEnabled {
            for e in procVFX {
                let t=sceneTime-e.start
                let c=MeadowSkillProcedural.scaled(MeadowSkillProcedural.camera(skill:e.skill,t:t,direction:e.direction),skill:e.skill,t:t,power:e.power)
                kick.dx+=c.dx;kick.dy+=c.dy;kick.zoom+=c.zoom;kick.rotation+=c.rotation
            }
        }
        // Director shot: close-up on whoever casts, a swing to the targets on release, a slow pull back.
        var shot=MeadowSkillProcedural.Shot.idle
        if !UIAccessibility.isReduceMotionEnabled {
            for e in procVFX {
                let s=MeadowSkillProcedural.shot(skill:e.skill,t:sceneTime-e.start,geo:e.geometry(live:liveFeet))
                if s.weight>shot.weight { shot=s }
            }
        }
        let worldScale=bounds.width/1000,layoutUnit=bounds.width/760
        let totalZoom=CGFloat(kick.zoom+shot.zoom),sceneScale=worldScale*(1+totalZoom)
        var shotX=CGFloat(0),shotY=CGFloat(0)
        if shot.weight>0 {
            // Slide toward the focus.
            shotX=CGFloat(-(shot.focusX-500)*0.9*shot.weight)*sceneScale
            shotY=CGFloat(-(shot.focusY-300)*0.6*shot.weight)*sceneScale
        }
        // The whole slide (shot + lens kick) is kept inside what the plates can cover, so the world edge never shows:
        // the world is 1000 wide and the plates run y -159...758; a zoom of z lets the frame slide 500*z units sideways, less what rotation uses up (a few units of floor keep the small shakes alive at no zoom).
        let kickX=CGFloat(kick.dx)*layoutUnit+shotX,kickY=CGFloat(kick.dy)*layoutUnit+shotY
        let maxSlideX=max(5*layoutUnit,bounds.width/2*totalZoom-abs(CGFloat(kick.rotation))*bounds.width/2)
        let maxSlideY=max(5*layoutUnit,(459*sceneScale-bounds.height/2)-abs(CGFloat(kick.rotation))*bounds.width/2)
        var worldTransform=CGAffineTransform(translationX:min(maxSlideX,max(-maxSlideX,kickX)),y:min(maxSlideY,max(-maxSlideY,kickY)))
        worldTransform=worldTransform.rotated(by:CGFloat(kick.rotation)).scaledBy(x:sceneScale,y:sceneScale)
        world.transform=worldTransform
        fx.setNeedsDisplay()
    }
    override func layoutSubviews() { super.layoutSubviews();let scale=bounds.width/1000;world.center=CGPoint(x:bounds.midX,y:bounds.midY);world.transform=CGAffineTransform(scaleX:scale,y:scale) }
}
struct MeadowPartyMessage {
    let text:String;let point:CGPoint;let at:Double;let color:UIColor;var atImpact=false;var supportUnit:String?=nil;var supportLine=0;var hitTier:MeadowBattleHitTier?=nil
    /// Look of the number (`MeadowBattleNumber`), the hit tier (0 light ... 2 heavy) for damage, and the unit it is stuck to (it moves with that unit's knock-back).
    var kind:MeadowBattleNumber.Kind = .heal;var rank=1;var follow:String?=nil
}
/// One player blow on a monster, for the shared hit-feel graphics (world coordinates).
struct MeadowPartyHitEvent { let at:Double;let tier:MeadowBattleHitTier;let direction:Double;let point:CGPoint;let footX:CGFloat;let floorY:CGFloat }
/// A procedural skill on stage (`MeadowSkillProcedural`): its own start, and where everything is.
struct MeadowPartyProcEvent {
    let skill:String,start:Double,direction:Double
    /// The geometry at cast time, plus who is who, so the effect can follow each unit's live position every frame.
    let geo:MeadowSkillProcedural.Geometry,casterID:String,targetIDs:[String]
    /// How hard the blow really was (1 medium, 0.7 light, 1.45 heavy); set when the rules report the damage. Scales the lens shake after the release.
    var power=1.0
    var info:MeadowSkillProcedural.Info? { MeadowSkillProcedural.info[skill] }
    /// Geometry with every foot replaced by the unit's current on-screen foot (travel, knock-back); chests keep their offset from the foot.
    func geometry(live:[String:PartyPoint])->MeadowSkillProcedural.Geometry {
        func move(_ foot:MeadowSkillProcedural.Pt,_ chest:MeadowSkillProcedural.Pt,_ id:String)->(foot:MeadowSkillProcedural.Pt,chest:MeadowSkillProcedural.Pt) {
            guard let p=live[id] else { return (foot,chest) }
            return (.init(p.x,p.y),.init(p.x+(chest.x-foot.x),p.y+(chest.y-foot.y)))
        }
        let c=move(geo.casterFoot,geo.caster,casterID)
        var targets:[MeadowSkillProcedural.Target]=[]
        for (i,t) in geo.targets.enumerated() where i<targetIDs.count { let m=move(t.foot,t.chest,targetIDs[i]);targets.append(.init(chest:m.chest,foot:m.foot)) }
        return .init(caster:c.chest,casterFoot:c.foot,targets:targets.isEmpty ? geo.targets:targets,ground:targets.first?.foot.y ?? geo.ground)
    }
}
enum MeadowSkillProceduralDrawing {
    static func heal(_ tier:HealingEffectTier)->String { switch tier { case .micro:return "healMicro";case .standard:return "healStandard";case .strong:return "healStrong" } }
    static func active(_ tier:HealingEffectTier,age:Double)->Bool { guard let info=MeadowSkillProcedural.info[heal(tier)] else { return false };return age>=0 && age<info.duration }
    static func drawHeal(_ tier:HealingEffectTier,age:Double,foot:PartyPoint,chest:PartyPoint,in ctx:CGContext,bounds:CGRect) {
        let id=heal(tier)
        guard let info=MeadowSkillProcedural.info[id],age>=0,age<info.duration else { return }
        let geo=MeadowSkillProcedural.Geometry(caster:.init(chest.x,chest.y),casterFoot:.init(foot.x,foot.y),targets:[.init(chest:.init(chest.x,chest.y),foot:.init(foot.x,foot.y))],ground:foot.y)
        MeadowSkillProceduralPainter.draw(MeadowSkillProcedural.primitives(skill:id,t:age,geo:geo),in:ctx,bounds:bounds)
        MeadowSkillProceduralPainter.drawAmbient(skill:id,t:age,in:ctx,bounds:bounds,target:CGPoint(x:chest.x,y:chest.y),floorY:CGFloat(foot.y),rx:70)
    }
}
struct MeadowPartySkillTarget { let chest:PartyPoint;let foot:PartyPoint }
/// A skill on stage: the sprite (`startedAt`), plus what surrounds it - the charge-up on the caster inside the cast motion
/// (`actionStart` ... `startedAt`), the reaction of each target from `impactAt`, and the afterglow once the sprite ends.
struct MeadowPartySkillVFXEvent {
    let spec:PartySkillVFXSpec;let startedAt:Double;let center:PartyPoint;let groundY:Double
    var actionStart=0.0,impactAt=0.0
    var casterChest:PartyPoint?,casterFoot:PartyPoint?
    var targets:[MeadowPartySkillTarget]=[]
    /// Seconds after `startedAt` when nothing of this skill is left to draw.
    var lifetime:Double { max(spec.duration+MeadowSkillAmbientLight.afterglowLife,(impactAt-startedAt)+MeadowSkillAmbientLight.wardReactionLife)+0.05 }
}

private final class MeadowPartyEffectsView:UIView {
    var templates:[String:String]=[:]
    private func hitPoint(_ id:String,shielded:Bool=false,weaponID:String?=nil)->PartyPoint {PartyVisual.hitPoint(target:id,shielded:shielded,weaponID:weaponID,templateID:templates[id])}
    var intent:PartyIntent?,focus:PartyAction?
    var friend="p1",foe="m1",focusTarget="p1"
    var meetsShield=false
    var age=0.0,time=0.0
    var messages:[MeadowPartyMessage]=[]
    var naturalTwenty=false
    var runes:RuneEffectSample?
    var particles:[MeadowBattleLightParticle]=[]
    var hits:[MeadowPartyHitEvent]=[]
    var skillEffects:[MeadowPartySkillVFXEvent]=[]
    static let pixelSkillIDs:Set<String>=["rally","sweep"]
    var recoveryLights:[(PartyPoint,Double)]=[]
    var monsterRecoveries:[(foot:PartyPoint,chest:PartyPoint,tier:HealingEffectTier,age:Double)]=[]
    var allyRecoveries:[(foot:PartyPoint,chest:PartyPoint,tier:HealingEffectTier,age:Double)]=[]
    var procEffects:[MeadowPartyProcEvent]=[]
    var liveFeet:[String:PartyPoint]=[:]
    /// Reports the strongest full-screen flash of this frame (or nil) to the stage, which shows it on a pane-wide overlay.
    var onFlash:((UIColor?)->Void)?
    override init(frame:CGRect) { super.init(frame:frame);isOpaque=false;isUserInteractionEnabled=false }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    /// A floating number: springs in, floats up and fades late (`MeadowBattleNumber`). It stays stuck to its unit as the unit is knocked back.
    private func drawNumber(_ m:MeadowPartyMessage,in ctx:CGContext) {
        let age=time-m.at,alpha=MeadowBattleNumber.alpha(age:age),scale=CGFloat(MeadowBattleNumber.scale(age:age,kind:m.kind,rank:m.rank))
        guard alpha>0.003,scale>0.01 else { return }
        let size=MeadowBattleNumber.fontSize(kind:m.kind,rank:m.rank),a=CGFloat(alpha)
        let fill:UIColor = m.kind == .damage ? (m.rank >= 2 ? UIColor(red:1,green:0.886,blue:0.51,alpha:1):.white):m.color
        let attrs:[NSAttributedString.Key:Any]=[.font:UIFont.systemFont(ofSize:CGFloat(size),weight:.heavy),.foregroundColor:fill.withAlphaComponent(a),.strokeColor:UIColor(red:0.10,green:0.07,blue:0.04,alpha:a),.strokeWidth:-4]
        let label=NSAttributedString(string:m.text,attributes:attrs),box=label.size()
        let rise=CGFloat(MeadowBattleNumber.rise(age:age,kind:m.kind)),sway=CGFloat(MeadowBattleNumber.sway(age:age,seed:abs(Int(m.point.x))))
        var cx:CGFloat,cy:CGFloat
        if let id=m.supportUnit,let base=PartyVisual.foot(id) {
            // Beside the owner, under every HP header; stacked lines are spaced by the font size.
            let live=liveFeet[id].map { CGPoint(x:$0.x,y:$0.y) } ?? CGPoint(x:base.x,y:base.y)
            let line=CGFloat(MeadowBattleNumber.lineHeight(kind:m.kind,rank:m.rank))*CGFloat(m.supportLine)
            cx=max(4,live.x-14-box.width)+box.width/2;cy=live.y-86+line-rise+box.height/2
        } else if m.atImpact {
            var p=m.point
            if let id=m.follow,let base=PartyVisual.foot(id),let live=liveFeet[id] { p.x += CGFloat(live.x-base.x);p.y += CGFloat(live.y-base.y) }
            cx=p.x+sway;cy=p.y-rise-6
        } else {
            cx=m.point.x+60+box.width/2+sway;cy=m.point.y-55-rise+box.height/2
        }
        let half=box.width*scale/2
        cx=min(996-half,max(4+half,cx))
        ctx.saveGState();ctx.setBlendMode(.normal)
        ctx.setShadow(offset:.zero,blur:CGFloat(size)*0.4,color:fill.withAlphaComponent(a*0.55).cgColor)
        ctx.translateBy(x:cx,y:cy);ctx.scaleBy(x:scale,y:scale)
        label.draw(at:CGPoint(x:-box.width/2,y:-box.height/2))
        ctx.restoreGState()
    }
    override func draw(_ rect:CGRect) {
        guard let ctx=UIGraphicsGetCurrentContext() else { return }
        func sprite(_ im:UIImage,_ p:PartyPoint,_ w:Double,_ h:Double,_ alpha:Double) { guard alpha>0 else { return };im.draw(in:CGRect(x:p.x-w/2,y:p.y-h/2,width:w,height:h),blendMode:.plusLighter,alpha:CGFloat(alpha)) }
        func glow(_ p:PartyPoint,_ rx:Double,_ ry:Double,_ alpha:Double,_ color:UIColor) { guard alpha>0 else { return };MeadowBattleGlowCache.image(color).draw(in:CGRect(x:p.x-rx,y:p.y-ry,width:rx*2,height:ry*2),blendMode:.plusLighter,alpha:CGFloat(alpha)) }
        for (foot,power) in recoveryLights { glow(foot,105,27,power*0.65,.systemGreen);glow(PartyPoint(foot.x,foot.y-70),42,85,power*0.12,.systemGreen) }
        for r in monsterRecoveries+allyRecoveries { MeadowSkillProceduralDrawing.drawHeal(r.tier,age:r.age,foot:r.foot,chest:r.chest,in:ctx,bounds:bounds) }
        if intent==nil {
            for (id,color) in [(friend,UIColor.systemGreen),(foe,MeadowPreviewPalette.gold)] {
                if let p=PartyVisual.foot(id) { ctx.setStrokeColor(color.withAlphaComponent(0.65).cgColor);ctx.setLineWidth(2);ctx.strokeEllipse(in:CGRect(x:p.x-36,y:p.y-7,width:72,height:14)) }
            }
        }
        if let intent {
            let visual=intent.action.visual
            if intent.action == .support {
                let from=PartyVisual.chest(intent.actor),to=PartyVisual.chest(intent.target)
                let alpha=PartyVisual.pulse(age,0.05,0.36,1.12)
                let path=UIBezierPath();path.move(to:CGPoint(x:from.x,y:from.y));path.addQuadCurve(to:CGPoint(x:to.x,y:to.y),controlPoint:CGPoint(x:(from.x+to.x)/2,y:min(from.y,to.y)-90))
                ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setShadow(offset:.zero,blur:14,color:UIColor.systemGreen.cgColor)
                UIColor.systemGreen.withAlphaComponent(CGFloat(alpha*0.25)).setStroke();path.lineWidth=8;path.stroke();MeadowPreviewPalette.gold.withAlphaComponent(CGFloat(alpha*0.8)).setStroke();path.lineWidth=2;path.stroke();ctx.restoreGState()
                for p in PartyVisual.trail(age:age,from:from,to:to) { sprite(MeadowBattleVFXAssets.healStar,PartyPoint(p.x,p.y),p.size,p.size,p.alpha) }
                let power=PartyVisual.pulse(age,0,0.56,1.5)
                if let foot=PartyVisual.foot(intent.target) { glow(foot,110,26,power*0.5,.systemGreen) }
            }
            if intent.action.isItem,age<intent.action.impact,let foot=PartyVisual.foot(intent.target) {
                let name="MeadowParty"+intent.action.rawValue.prefix(1).uppercased()+intent.action.rawValue.dropFirst()
                if let image=UIImage(named:name) { sprite(image,PartyPoint(foot.x,foot.y-130-age*15),38,38,PartyVisual.pulse(age,0,0.25,0.85)) }
            }
            if intent.ranged,let foot=PartyVisual.foot(intent.actor) {
                let tip=BowRig.releaseArrowTip
                let from=PartyPoint(foot.x+(tip.x-123)*PartyVisual.heroScale,foot.y+(tip.y-214)*PartyVisual.heroScale)
                let to=hitPoint(intent.target,shielded:meetsShield)
                let projectile=intent.enemy ? MonsterVisualSpec.find(intent.monsterTemplateID)?.projectile(age:age,foot:foot,target:to):BowRig.projectile(age:age,from:from,to:to,impact:intent.action.impact,scale:PartyVisual.heroScale)
                if let arrow=projectile {
                    let a=arrow.tail,b=arrow.tip
                    ctx.saveGState();ctx.setLineCap(.round)
                    let missileColor=intent.monsterTemplateID=="ruinDragon" ? UIColor.systemCyan:MeadowPreviewPalette.gold
                    ctx.setShadow(offset:.zero,blur:8,color:missileColor.cgColor)
                    ctx.setStrokeColor(missileColor.withAlphaComponent(0.5).cgColor);ctx.setLineWidth(5)
                    ctx.move(to:CGPoint(x:a.x,y:a.y));ctx.addLine(to:CGPoint(x:b.x,y:b.y));ctx.strokePath()
                    ctx.setStrokeColor(MeadowPreviewPalette.ink.cgColor);ctx.setLineWidth(2)
                    ctx.move(to:CGPoint(x:a.x,y:a.y));ctx.addLine(to:CGPoint(x:b.x,y:b.y));ctx.strokePath();ctx.restoreGState()
                }
            }
            if intent.weaponID=="greatSword",!intent.enemy,visual=="attack",let from=PartyVisual.foot(intent.actor) {
                let points=GreatSwordRig.trail(age:age,from:from,to:hitPoint(intent.target,shielded:meetsShield,weaponID:intent.weaponID),scale:PartyVisual.heroScale)
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
            if intent.magical,let foot=PartyVisual.foot(intent.actor),let targetFoot=PartyVisual.foot(intent.target) {
                let sample=LegendaryStaffRig.effect(age:age,foot:foot,target:hitPoint(intent.target,shielded:meetsShield,weaponID:intent.weaponID),groundY:targetFoot.y,scale:PartyVisual.heroScale,naturalTwenty:naturalTwenty)
                MeadowStaffEffectPainter.draw(sample,in:ctx)
            }
            if visual=="attack",intent.action.skillVFX == nil,!intent.magical,let foot=PartyVisual.foot(intent.target) {
                let a=age-(intent.enemy ? 0.46:1.048),p=hitPoint(intent.target,shielded:meetsShield,weaponID:intent.weaponID)
                let power=PartyVisual.pulse(a,-0.035,0.035,0.52)
                if !intent.enemy && !hits.isEmpty {
                    // Player blows use the sharp contact flare below; only a faint floor glow and the sweep arc stay.
                    glow(foot,110,24,power*0.30,.orange)
                    if a>=0,a<0.7,!intent.ranged { sprite(MeadowBattleVFXAssets.heavyArc,p,170+a*220,170+a*220,power*0.55) }
                } else {
                    glow(p,140,140,power*0.48,.orange);glow(foot,170,30,power*0.65,.orange)
                    if a>=0,a<0.7 {
                        sprite(MeadowBattleVFXAssets.burst,p,150+a*140,150+a*140,power)
                        if !intent.enemy && !intent.ranged { sprite(MeadowBattleVFXAssets.heavyArc,p,210+a*240,210+a*240,power*0.9) }
                    }
                }
            }
            if visual=="ambush",let foot=PartyVisual.foot(intent.target) {
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
        for event in skillEffects {
            let age=time-event.startedAt
            guard age>=0,age<event.spec.duration,let frames=MeadowBattleVFXAssets.skillFrames(for:event.spec.id),frames.count==event.spec.frameCount else { continue }
            let position=age*event.spec.framesPerSecond
            let lower=min(event.spec.frameCount-1,max(0,Int(position)))
            let upper=min(event.spec.frameCount-1,lower+1)
            // The five hand-built pixel sheets (scripts/battle-vfx) hold each frame and are scaled without smoothing, so the
            // pixels stay crisp and nothing swims between frames; any other sheet keeps the soft cross-fade.
            let pixelArt=Self.pixelSkillIDs.contains(event.spec.id)
            let mix=pixelArt ? 0 : PartyVisual.smooth(position-Double(lower))
            let rect=CGRect(x:event.center.x-event.spec.anchorX,y:event.center.y-event.spec.anchorY,width:Double(event.spec.frameWidth),height:Double(event.spec.frameHeight))
            let light=PartyVisual.pulse(age,0,event.spec.peakTime,event.spec.duration)
            let color:UIColor
            switch event.spec.id {
            case "starlightPulse":color=UIColor(red:0.36,green:0.31,blue:1,alpha:1)
            case "rally":color=MeadowPreviewPalette.gold
            case "sweep":color=UIColor(red:0.42,green:0.78,blue:1,alpha:1)
            case "dragonSoulWard":color=UIColor(red:0.29,green:0.67,blue:1,alpha:1)
            default:color=UIColor(red:1,green:0.55,blue:0.18,alpha:1)
            }
            glow(event.center,Double(event.spec.frameWidth)*0.34,Double(event.spec.frameHeight)*0.29,light*0.13,color)
            // Ambient light (MeadowSkillAmbientLight): a faint wash over the whole stage, a wide pool of light on the floor
            // with a rim, and (below) a squashed reflection and glowing motes that drift over the characters.
            let lit=MeadowSkillAmbientLight.level(age:age,peak:event.spec.peakTime,duration:event.spec.duration)
            let floorWidth=Double(event.spec.frameWidth)
            if lit>0 {
                // The flat dim and tint for this light are applied by the stage on pane-wide overlays (see `render()`), not here.
                glow(event.center,max(Double(bounds.width),floorWidth)*0.62,max(Double(bounds.height),floorWidth)*0.52,lit*0.16,color)
                glow(PartyPoint(event.center.x,event.groundY-2),floorWidth*0.62,28,lit*0.34,color)
                ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setStrokeColor(color.withAlphaComponent(CGFloat(lit*0.32)).cgColor);ctx.setLineWidth(1.5)
                ctx.strokeEllipse(in:CGRect(x:event.center.x-floorWidth*0.36,y:event.groundY-9,width:floorWidth*0.72,height:18));ctx.restoreGState()
            }
            ctx.saveGState();ctx.interpolationQuality = pixelArt ? .none : .default
            frames[lower].draw(in:rect,blendMode:.plusLighter,alpha:CGFloat(1-mix))
            if upper != lower,mix>0 { frames[upper].draw(in:rect,blendMode:.plusLighter,alpha:CGFloat(mix)) }
            ctx.restoreGState()
            if lit>0 {
                // Squashed reflection on the floor, only below the ground line.
                ctx.saveGState();ctx.interpolationQuality = pixelArt ? .none : .default
                ctx.clip(to:CGRect(x:rect.minX-20,y:event.groundY,width:rect.width+40,height:90))
                ctx.translateBy(x:0,y:event.groundY);ctx.scaleBy(x:1,y:-0.30);ctx.translateBy(x:0,y:-event.groundY)
                frames[lower].draw(in:rect,blendMode:.plusLighter,alpha:CGFloat(0.16*(1-mix)*lit))
                if upper != lower,mix>0 { frames[upper].draw(in:rect,blendMode:.plusLighter,alpha:CGFloat(0.16*mix*lit)) }
                ctx.restoreGState()
            }
            if !UIAccessibility.isReduceMotionEnabled {
                let hot=UIColor(red:1,green:0.96,blue:0.86,alpha:1)
                for m in MeadowSkillAmbientLight.motes(skill:event.spec.id,age:age,duration:event.spec.duration,spread:floorWidth*0.36) {
                    let p=PartyPoint(event.center.x+m.dx,event.center.y+m.dy)
                    glow(p,m.radius*1.5,m.radius*1.5,m.alpha*0.8,color)
                    ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setFillColor((m.hot ? hot : color).withAlphaComponent(CGFloat(m.alpha)).cgColor)
                    ctx.fill(CGRect(x:p.x-m.core/2,y:p.y-m.core/2,width:m.core,height:m.core));ctx.restoreGState()
                }
            }
        }
        // Stagecraft around the five pixel skills (MeadowSkillAmbientLight): charge-up, target reaction, afterglow.
        for event in skillEffects where Self.pixelSkillIDs.contains(event.spec.id) {
            let id=event.spec.id,tone=MeadowSkillAmbientLight.tone(for:id)
            let color=UIColor(red:CGFloat(tone.r),green:CGFloat(tone.g),blue:CGFloat(tone.b),alpha:1),hot=UIColor(red:1,green:0.96,blue:0.86,alpha:1)
            let calm=UIAccessibility.isReduceMotionEnabled
            func specks(_ motes:[MeadowSkillAmbientLight.Mote],_ o:PartyPoint,_ strength:Double) {
                guard !calm else { return }
                for m in motes where m.alpha>0.01 {
                    let p=PartyPoint(o.x+m.dx,o.y+m.dy)
                    glow(p,m.radius*1.4,m.radius*1.4,m.alpha*strength,color)
                    ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setFillColor((m.hot ? hot:color).withAlphaComponent(CGFloat(m.alpha)).cgColor)
                    ctx.fill(CGRect(x:p.x-m.core/2,y:p.y-m.core/2,width:m.core,height:m.core));ctx.restoreGState()
                }
            }
            func rim(_ c:PartyPoint,_ rx:Double,_ ry:Double,_ alpha:Double) {
                guard alpha>0.01 else { return }
                ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setStrokeColor(color.withAlphaComponent(CGFloat(min(1,alpha))).cgColor);ctx.setLineWidth(1.5)
                ctx.strokeEllipse(in:CGRect(x:c.x-rx,y:c.y-ry,width:rx*2,height:ry*2));ctx.restoreGState()
            }
            // 1. Charge-up on the caster, in the last half second before the sprite starts (inside the existing cast motion).
            let chargeStart=max(event.actionStart,event.startedAt-MeadowSkillAmbientLight.chargeWindow)
            if let chest=event.casterChest,let foot=event.casterFoot,event.startedAt-chargeStart>0.12,time>=chargeStart,time<event.startedAt,
               let c=MeadowSkillAmbientLight.charge(skill:id,progress:(time-chargeStart)/(event.startedAt-chargeStart)) {
                glow(chest,52,52,c.level*0.5,color)
                rim(foot,c.ringRadius,c.ringRadius*0.3,c.ringAlpha*0.7)
                specks(c.motes,chest,0.75)
            }
            // 3. Target reactions from the impact.
            for target in event.targets {
                guard let r=MeadowSkillAmbientLight.reaction(skill:id,age:time-event.impactAt) else { continue }
                glow(target.chest,46,66,r.glow*0.45,color)
                if r.aura>0.01 {
                    glow(target.chest,34,62,r.aura*0.16,color)
                    rim(target.foot,40,12,r.aura*0.5)
                    if !calm { for k in 0..<4 {
                        let th=r.spin+Double(k)*Double.pi/2,p=PartyPoint(target.foot.x+cos(th)*40,target.foot.y+sin(th)*12)
                        ctx.saveGState();ctx.setBlendMode(.plusLighter);ctx.setFillColor(hot.withAlphaComponent(CGFloat(r.aura)).cgColor);ctx.fill(CGRect(x:p.x-1.5,y:p.y-1.5,width:3,height:3));ctx.restoreGState()
                    } }
                }
                specks(r.motes,target.chest,0.6)
            }
            // 4. Afterglow: a fading pool of light and a few embers once the sprite has ended.
            if let g=MeadowSkillAmbientLight.afterglow(skill:id,age:time-(event.startedAt+event.spec.duration),spread:Double(event.spec.frameWidth)*0.3) {
                glow(PartyPoint(event.center.x,event.groundY-2),Double(event.spec.frameWidth)*0.5,22,g.pool,color)
                specks(g.motes,event.center,0.6)
            }
        }
        // Continuous procedural skills (MeadowSkillProcedural): ambient light first, then the effect itself.
        var flashColor:UIColor?=nil,flashAlpha=0.0
        for e in procEffects {
            let t=time-e.start
            guard let info=e.info,t>=0,t<info.duration else { continue }
            let geo=e.geometry(live:liveFeet)
            guard !geo.targets.isEmpty else { continue }
            // The ambient light centres on the whole group of targets and widens with their spread.
            let n=Double(geo.targets.count),mx=geo.targets.reduce(0){$0+$1.chest.x}/n,my=geo.targets.reduce(0){$0+$1.chest.y}/n,fy=geo.targets.reduce(0){$0+$1.foot.y}/n
            let spread=geo.targets.map { abs($0.chest.x-mx) }.max() ?? 0
            MeadowSkillProceduralPainter.drawAmbient(skill:e.skill,t:t,in:ctx,bounds:bounds,target:CGPoint(x:mx,y:my),floorY:CGFloat(fy),rx:90+spread,fillBounds:false)
            MeadowSkillProceduralPainter.draw(MeadowSkillProcedural.primitives(skill:e.skill,t:t,geo:geo),in:ctx,bounds:bounds) { c,a in
                if a>flashAlpha { flashAlpha=a;flashColor=UIColor(red:CGFloat(c.r/255),green:CGFloat(c.g/255),blue:CGFloat(c.b/255),alpha:CGFloat(min(1,a*0.85))) }
            }
        }
        onFlash?(flashColor)
        for h in hits {
            let a=time-h.at
            glow(PartyPoint(Double(h.point.x),Double(h.point.y)),120,120,MeadowBattleHitFeel.flash(age:a)*0.55,UIColor(red:1,green:0.75,blue:0.27,alpha:1))
            MeadowBattleHitFeelPainter.draw(in:ctx,age:a,tier:h.tier,direction:h.direction,impact:h.point,floorY:h.floorY,footX:h.footX,unit:MeadowBattleHitFeelPainter.partyStageUnit)
        }
        if let runes { MeadowRuneEffectPainter.draw(runes,in:ctx) }
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
        for m in messages { drawNumber(m,in:ctx) }
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

/// The offline renderer consumes the exact same points, widths and envelopes.
enum MeadowRuneEffectPainter {
    private static let slashFrames:[UIImage]=((1...8).compactMap { UIImage(named:String(format:"MeadowRuneSlash%02d",$0)) })
    static func color(_ name:String)->UIColor {
        switch name {
        case "violet":return UIColor(red:0.36,green:0.25,blue:1,alpha:1)
        case "cyan":return UIColor(red:0.12,green:0.75,blue:1,alpha:1)
        case "blue":return UIColor(red:0.14,green:0.38,blue:1,alpha:1)
        case "gold":return UIColor(red:0.99,green:0.78,blue:0.27,alpha:1)
        case "fireRed":return UIColor(red:1.00,green:0.18,blue:0.08,alpha:1)
        case "fireOrange":return UIColor(red:1.00,green:0.39,blue:0.10,alpha:1)
        case "fireGold":return UIColor(red:1.00,green:0.73,blue:0.23,alpha:1)
        case "fireWhite":return UIColor(red:1.00,green:0.91,blue:0.61,alpha:1)
        case "green":return UIColor(red:0.16,green:1,blue:0.48,alpha:1)
        default:return UIColor(red:0.96,green:0.98,blue:1,alpha:1)
        }
    }
    static func draw(_ q:RuneEffectSample,in ctx:CGContext) {
        ctx.saveGState();defer { ctx.restoreGState() };ctx.setBlendMode(.plusLighter);ctx.setLineCap(.round);ctx.setLineJoin(.round)
        func glow(_ p:PartyPoint,_ rx:Double,_ ry:Double,_ alpha:Double,_ name:String) {
            guard alpha>0 else{return}
            MeadowBattleGlowCache.image(color(name)).draw(in:CGRect(x:p.x-rx,y:p.y-ry,width:rx*2,height:ry*2),blendMode:.plusLighter,alpha:CGFloat(min(1,alpha)))
        }
        if let index=q.spriteFrame,slashFrames.indices.contains(index),let center=q.spriteCenter {
            let size=q.spriteSize ?? 256,alpha=q.spriteAlpha ?? 1
            for v in q.glows { glow(v.point,v.rx,v.ry,v.alpha,v.color) }
            if alpha>0 {
                ctx.saveGState();ctx.interpolationQuality = .none
                slashFrames[index].draw(in:CGRect(x:center.x-size/2,y:center.y-size/2,width:size,height:size),blendMode:.plusLighter,alpha:CGFloat(alpha))
                ctx.restoreGState()
            }
            return
        }
        for v in q.glows { glow(v.point,v.rx,v.ry,v.alpha,v.color) }
        for layer in q.spriteLayers {
            guard let image=MeadowBattleVFXAssets.effectImage(named:layer.asset),layer.alpha>0 else { continue }
            let size=layer.size,center=layer.center
            ctx.saveGState();ctx.interpolationQuality = .none
            image.draw(in:CGRect(x:center.x-size/2,y:center.y-size/2,width:size,height:size),blendMode:.plusLighter,alpha:CGFloat(layer.alpha*0.92))
            ctx.restoreGState()
        }
        for s in q.strokes where s.points.count>1 {
            ctx.setStrokeColor(color(s.color).withAlphaComponent(CGFloat(s.alpha)).cgColor);ctx.setLineWidth(s.width)
            ctx.beginPath();ctx.move(to:CGPoint(x:s.points[0].x,y:s.points[0].y));for p in s.points.dropFirst() { ctx.addLine(to:CGPoint(x:p.x,y:p.y)) };ctx.strokePath()
        }
        for m in q.motes {
            if m.id%6==0 { glow(m.point,18,14,m.alpha*0.20,m.color) }
            if let age=m.groundAge,age<0.23 {
                let a=m.alpha*(1-age/0.23)
                glow(m.ground,34,9,a*0.72,m.color)
                if m.id%3==0 { MeadowBattleVFXAssets.groundSpark.draw(in:CGRect(x:m.ground.x-23,y:m.ground.y-6,width:46,height:12),blendMode:.plusLighter,alpha:CGFloat(a*0.78)) }
            }
            ctx.saveGState();ctx.translateBy(x:m.point.x,y:m.point.y);ctx.rotate(by:m.angle)
            ctx.setFillColor(color(m.color).withAlphaComponent(CGFloat(m.alpha)).cgColor)
            ctx.move(to:CGPoint(x:0,y:-m.size/2));ctx.addLine(to:CGPoint(x:m.size/3,y:0));ctx.addLine(to:CGPoint(x:0,y:m.size/2));ctx.addLine(to:CGPoint(x:-m.size/3,y:0));ctx.closePath();ctx.fillPath();ctx.restoreGState()
        }
    }
}
