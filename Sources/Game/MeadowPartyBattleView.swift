import UIKit
import ClassroomGameCore
import MeadowBattleSupport

/// A real two-player/two-target training encounter backed by the tabletop engine.
final class MeadowPartyBattleView:UIView {
    var onClose:(()->Void)?
    private var model:PartyEncounter?
    private var active=false
    private var generation=0
    private var scheduled:DispatchWorkItem?
    private var friend="p1",foe="m1"
    private let title=MeadowPreviewPalette.label("小队支援",size:26,weight:.heavy)
    private let hint=MeadowPreviewPalette.label("",size:17,weight:.semibold)
    private let header=UIView(),panel=UIScrollView()
    private let back=MeadowPreviewPalette.button("返回单人")
    private let reset=MeadowPreviewPalette.button("重置演练")
    private let end=MeadowPreviewPalette.button("结束行动")
    private let items=MeadowPreviewPalette.button("道具")
    private let stage=MeadowPartyStageView()
    private var cards:[String:MeadowPartyUnitCard]=[:]
    private var skills:[MeadowPartySkillButton]=[]
    override init(frame:CGRect) {
        super.init(frame:frame);backgroundColor=MeadowPreviewPalette.panel
        MeadowPreviewPalette.stylePanel(header);MeadowPreviewPalette.stylePanel(panel)
        [header,stage,panel].forEach(addSubview)
        [title,hint,back,reset,end].forEach(header.addSubview)
        back.addAction(UIAction { [weak self] _ in self?.setActive(false);self?.onClose?() },for:.touchUpInside)
        reset.addAction(UIAction { [weak self] _ in self?.restart() },for:.touchUpInside)
        end.addAction(UIAction { [weak self] _ in self?.perform(.endTurn) },for:.touchUpInside)
        for id in ["p1","p2","m1","m2"] {
            let card=MeadowPartyUnitCard();card.onChoose={ [weak self] in self?.choose(id) };cards[id]=card;panel.addSubview(card)
        }
        for _ in 0..<4 { let b=MeadowPartySkillButton(type:.system);skills.append(b);panel.addSubview(b) }
        panel.addSubview(items);items.showsMenuAsPrimaryAction=true
        stage.onChoose={ [weak self] id in self?.choose(id) }
        accessibilityIdentifier="meadowPartySupportEncounter"
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    func setActive(_ value:Bool) {
        active=value
        if value { restart() } else {
            generation += 1;scheduled?.cancel();scheduled=nil;model?.cancel();stage.stop()
        }
    }
    private func restart() {
        generation += 1;scheduled?.cancel();scheduled=nil;stage.stop()
        do { model=try PartyEncounter() } catch { hint.text="演练加载失败：\(error.localizedDescription)";return }
        friend="p1";foe="m1";stage.start();refresh()
    }
    private func choose(_ id:String) {
        guard model?.pending==nil else { return }
        if id.hasPrefix("p") { friend=id } else { foe=id };refresh()
    }
    private func target(_ action:PartyAction)->String { [.attack,.heavyStrike].contains(action) ? foe:friend }
    private func perform(_ action:PartyAction) {
        guard active,let model,let intent=model.prepare(action,target:target(action)) else { return }
        let token=generation;refresh()
        stage.play(intent,before:model.state,onImpact:{ [weak self] in
            guard let self,self.active,self.generation==token else { return nil }
            do { let receipt=try model.commit(intent.id);self.refresh();return receipt }
            catch { self.hint.text=error.localizedDescription;return nil }
        },completion:{ [weak self] in
            guard let self,self.active,self.generation==token else { return }
            self.refresh();self.scheduleEnemy()
        })
    }
    private func scheduleEnemy() {
        scheduled?.cancel();scheduled=nil
        guard active,let model,let current=model.current,model.state.units[current]?.kind == .monster,!model.terminal else { return }
        let token=generation
        let task=DispatchWorkItem { [weak self] in
            guard let self,self.active,self.generation==token,let id=model.nextEnemyTarget() else { return }
            self.friend=id;self.performEnemy(target:id)
        }
        scheduled=task;DispatchQueue.main.asyncAfter(deadline:.now()+0.65,execute:task)
    }
    private func performEnemy(target:String) {
        guard let model,let intent=model.prepare(.attack,target:target) else { return }
        let token=generation;refresh()
        stage.play(intent,before:model.state,onImpact:{ [weak self] in
            guard let self,self.active,self.generation==token else { return nil }
            do { let r=try model.commit(intent.id);self.refresh();return r } catch { self.hint.text=error.localizedDescription;return nil }
        },completion:{ [weak self] in guard let self,self.active,self.generation==token else { return };self.refresh();self.scheduleEnemy() })
    }
    private func refresh() {
        guard let model else { return }
        let state=model.state;let current=model.current
        if state.units[foe]?.isAlive != true,let live=["m1","m2"].first(where:{ state.units[$0]?.isAlive==true }) { foe=live }
        let busy=stage.isPlaying || model.pending != nil
        title.text=model.terminal ? (state.players.contains(where: \.isAlive) ? "小队胜利":"小队倒地") : "小队支援 · 第\(model.round)轮"
        let showing=busy ? (stage.actorInAction ?? model.pending?.actor ?? current):current
        let name=showing.flatMap { state.units[$0]?.name } ?? "演练结束"
        hint.text=busy ? "\(name) · 动作进行中" : "\(name)行动 · 友方 \(friend.uppercased()) / 敌方 \(foe=="m1" ? "甲":"乙") · 点角色选目标"
        for (id,card) in cards {
            guard let unit=state.units[id] else { continue }
            card.show(unit:unit,selected:id==friend || id==foe,current:id==current)
        }
        stage.show(state,friend:friend,foe:foe,current:current)
        let actions=model.playerActions()
        for (i,b) in skills.enumerated() {
            b.clearHandlers();b.isHidden=i>=actions.count
            guard i<actions.count else { continue }
            let a=actions[i];let result=model.preview(a,target:target(a))
            b.setTitle(a.title,for:.normal);b.subtitle.text=detail(a,model:model)
            b.isEnabled=active && !busy && result.allowed
            b.onActivate={ [weak self] in self?.perform(a) }
            b.onFocus={ [weak self] focused in self?.stage.preview(focused ? a:nil,target:self?.target(a) ?? "p1") }
            b.accessibilityLabel=a.title+"，"+b.subtitle.text!
            b.accessibilityHint=result.allowed ? "执行技能":result.message
        }
        end.isEnabled=active && !busy && current?.hasPrefix("p")==true && !model.terminal
        var menu:[UIAction]=[]
        for a in [PartyAction.smallPotion,.largePotion,.shieldPotion,.revivalStone] {
            let count=current.flatMap { state.units[$0]?.inventory[a.rawValue] } ?? 0
            let allowed=model.preview(a,target:friend).allowed
            menu.append(UIAction(title:"\(a.title) ×\(count) · \(a == .revivalStone ? 2:1) AP",image:UIImage(named:"MeadowParty"+a.rawValue.prefix(1).uppercased()+a.rawValue.dropFirst()),attributes:allowed && !busy ? []:.disabled,handler:{ [weak self] _ in self?.perform(a) }))
        }
        items.menu=UIMenu(title:"对 \(friend.uppercased()) 使用",children:menu)
        items.isEnabled=active && !busy && current?.hasPrefix("p")==true && !model.terminal
        setNeedsLayout()
    }
    private func detail(_ a:PartyAction,model:PartyEncounter)->String {
        guard a != .attack else { return "1 AP · 1D6＋当前增伤" }
        let uses=model.current.flatMap { model.state.units[$0]?.skillUses[a.rawValue] } ?? 0
        let rest=max(0,2-uses)
        switch a {
        case .support:return "1 AP · 治疗6 / 盾4 · 余\(rest)"
        case .rally:return "1 AP · 节点友方增伤2 / 1轮 · 余\(rest)"
        case .heavyStrike:return "1 AP · 1D6＋2 · 余\(rest)"
        case .breather:return "1 AP · 自身恢复4 · 余\(rest)"
        default:return "1 AP · 自身护盾4 · 余\(rest)"
        }
    }
    override func layoutSubviews() {
        super.layoutSubviews();let inset=safeAreaInsets
        let margin:CGFloat=16;let left=max(margin,inset.left+8),right=max(margin,inset.right+8)
        let top=max(12,inset.top+8),bottom=max(12,inset.bottom+8),w=max(1,bounds.width-left-right)
        let compact=bounds.height<600
        header.frame=CGRect(x:left,y:top,width:w,height:compact ? 72:82)
        if compact {
            let sidebar:CGFloat=min(250,w*0.34)
            panel.frame=CGRect(x:left+w-sidebar,y:header.frame.maxY+8,width:sidebar,height:max(1,bounds.height-bottom-header.frame.maxY-8))
            stage.frame=CGRect(x:left,y:panel.frame.minY,width:w-sidebar-8,height:panel.frame.height)
            panel.isScrollEnabled=true;panel.contentSize=CGSize(width:sidebar,height:820)
            for (i,id) in ["p1","p2","m1","m2"].enumerated() { cards[id]?.frame=CGRect(x:8,y:8+CGFloat(i)*90,width:sidebar-16,height:84) }
            for (i,b) in skills.enumerated() { b.frame=CGRect(x:8,y:378+CGFloat(i)*88,width:sidebar-16,height:80) }
            items.frame=CGRect(x:8,y:736,width:sidebar-16,height:68)
        } else {
            panel.frame=CGRect(x:left,y:bounds.height-bottom-196,width:w,height:196)
            stage.frame=CGRect(x:left,y:header.frame.maxY+10,width:w,height:max(1,panel.frame.minY-header.frame.maxY-20))
            panel.isScrollEnabled=false;panel.contentSize=panel.bounds.size
            let cw=(w-32-24)/4
            for (i,id) in ["p1","p2","m1","m2"].enumerated() { cards[id]?.frame=CGRect(x:16+CGFloat(i)*(cw+8),y:9,width:cw,height:86) }
            let itemWidth:CGFloat=100;let visible=skills.filter { !$0.isHidden };let count=CGFloat(max(1,visible.count))
            let bw=(w-32-itemWidth-10-8*(count-1))/count
            for (i,b) in visible.enumerated() { b.frame=CGRect(x:16+CGFloat(i)*(bw+8),y:108,width:bw,height:76) }
            items.frame=CGRect(x:w-itemWidth-16,y:108,width:itemWidth,height:76)
        }
        back.frame=CGRect(x:w-124,y:10,width:112,height:34);reset.frame=back.frame.offsetBy(dx:-124,dy:0)
        end.frame=CGRect(x:w-248,y:46,width:236,height:26)
        title.frame=CGRect(x:14,y:6,width:max(1,w-276),height:35)
        hint.frame=CGRect(x:14,y:42,width:max(1,w-276),height:28)
    }
}

private final class MeadowPartySkillButton:UIButton {
    let subtitle=UILabel()
    var onActivate:(()->Void)?
    var onFocus:((Bool)->Void)?
    private var hover=false
    override init(frame:CGRect) {
        super.init(frame:frame);backgroundColor=MeadowPreviewPalette.card;layer.cornerRadius=8;layer.borderWidth=1;layer.borderColor=MeadowPreviewPalette.border.cgColor
        titleLabel?.font=MeadowPreviewPalette.font(21,.heavy);setTitleColor(MeadowPreviewPalette.ink,for:.normal)
        subtitle.font=MeadowPreviewPalette.font(15);subtitle.textColor=MeadowPreviewPalette.muted;subtitle.numberOfLines=2;addSubview(subtitle)
        addAction(UIAction { [weak self] _ in self?.onActivate?() },for:.touchUpInside)
        addGestureRecognizer(UIHoverGestureRecognizer(target:self,action:#selector(hovered(_:))));isPointerInteractionEnabled=true
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    func clearHandlers() { onFocus?(false);onActivate=nil;onFocus=nil }
    override var isEnabled:Bool { didSet { alpha=isEnabled ? 1:0.48;if !isEnabled { hover=false };updateFocus() } }
    override var isHighlighted:Bool { didSet { updateFocus() } }
    override func didUpdateFocus(in context:UIFocusUpdateContext,with coordinator:UIFocusAnimationCoordinator) { super.didUpdateFocus(in:context,with:coordinator);updateFocus() }
    @objc private func hovered(_ r:UIHoverGestureRecognizer) { hover=r.state == .began || r.state == .changed;updateFocus() }
    private func updateFocus() { onFocus?(isEnabled && (hover || isHighlighted || isFocused)) }
    override func layoutSubviews() { super.layoutSubviews();titleLabel?.frame=CGRect(x:10,y:5,width:bounds.width-20,height:28);subtitle.frame=CGRect(x:10,y:36,width:bounds.width-20,height:36) }
}
private final class MeadowPartyUnitCard:UIView {
    var onChoose:(()->Void)?
    private let name=UILabel(),hp=MeadowBattleResourceBar(),ward=MeadowBattleResourceBar(),buff=MeadowPartyBuffButton(type:.system),shieldBuff=MeadowPartyBuffButton(type:.system)
    override init(frame:CGRect) {
        super.init(frame:frame);backgroundColor=MeadowPreviewPalette.card;layer.cornerRadius=7;layer.borderWidth=1
        name.font=MeadowPreviewPalette.font(17);name.textColor=MeadowPreviewPalette.ink
        [name,hp,ward,buff,shieldBuff].forEach(addSubview)
        let choose=UITapGestureRecognizer(target:self,action:#selector(chosen));choose.cancelsTouchesInView=false;addGestureRecognizer(choose)
        isAccessibilityElement=false;buff.layer.zPosition=100;shieldBuff.layer.zPosition=100
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    @objc private func chosen() { onChoose?() }
    func show(unit:GameUnit,selected:Bool,current:Bool) {
        name.text=(current ? "▶ ":"")+unit.name+" · \(unit.ap)AP"
        layer.borderColor=(selected ? MeadowPreviewPalette.gold:MeadowPreviewPalette.border).cgColor;layer.borderWidth=selected ? 2:1
        hp.show("HP",value:unit.health,maximum:unit.baseAttributes.maximumHealth,color:.systemGreen)
        ward.show("盾",value:unit.shield,maximum:8,color:.systemCyan)
        if let b=unit.damageBuff { buff.show(title:"振奋 · 增伤＋\(b.amount)",detail:"剩余 \(b.roundsLeft) 轮\n普攻和伤害技能生效\n按回合结算移除",symbol:"arrow.up",color:MeadowPreviewPalette.gold) }
        else { buff.hide() }
        if unit.shield>0 { shieldBuff.show(title:"防护 · 剩余 \(unit.shield) 点",detail:"优先抵挡伤害\n新授盾与旧值取较高者\n耗尽后移除",symbol:"shield.fill",color:.systemCyan) }
        else { shieldBuff.hide() }
        accessibilityLabel="\(unit.name)，生命\(unit.health)/\(unit.baseAttributes.maximumHealth)，盾\(unit.shield)，\(unit.ap)行动点"
    }
    override func layoutSubviews() {
        super.layoutSubviews();name.frame=CGRect(x:9,y:4,width:bounds.width-18,height:22)
        let width=(bounds.width-104)/2
        hp.frame=CGRect(x:9,y:31,width:width,height:44);ward.frame=CGRect(x:18+width,y:31,width:width,height:44)
        buff.frame=CGRect(x:bounds.width-73,y:39,width:30,height:30)
        shieldBuff.frame=CGRect(x:bounds.width-39,y:39,width:30,height:30)
    }
}
private final class MeadowPartyBuffButton:UIButton {
    private let tip=UILabel();private var pinned=false,hover=false
    override init(frame:CGRect) {
        super.init(frame:frame);layer.borderWidth=1.5;layer.cornerRadius=4;backgroundColor=MeadowPreviewPalette.panel
        tip.font=MeadowPreviewPalette.font(17);tip.numberOfLines=0;tip.backgroundColor=MeadowPreviewPalette.panel;tip.textColor=MeadowPreviewPalette.ink;tip.layer.borderWidth=1;tip.layer.borderColor=MeadowPreviewPalette.gold.cgColor;tip.isHidden=true;tip.isUserInteractionEnabled=false
        addSubview(tip);addGestureRecognizer(UIHoverGestureRecognizer(target:self,action:#selector(hovered(_:))))
        addAction(UIAction { [weak self] _ in guard let self else { return };self.pinned.toggle();self.disclose() },for:.touchUpInside);isPointerInteractionEnabled=true
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    func show(title:String,detail:String,symbol:String,color:UIColor) { isHidden=false;setImage(UIImage(systemName:symbol),for:.normal);tintColor=color;layer.borderColor=color.cgColor;tip.text=" \(title)\n \(detail.replacingOccurrences(of:"\n",with:"\n "))";accessibilityLabel=title+"，"+detail;disclose() }
    func hide() { isHidden=true;pinned=false;hover=false;disclose() }
    @objc private func hovered(_ r:UIHoverGestureRecognizer) { hover=r.state == .began || r.state == .changed;disclose() }
    private func disclose() {
        tip.isHidden=isHidden || !(pinned || hover || isFocused)
        guard !tip.isHidden else { return }
        var host=superview
        while host != nil && !(host is MeadowPartyBattleView) { host=host?.superview }
        guard let host else { tip.isHidden=true;return }
        if tip.superview !== host { host.addSubview(tip);tip.layer.zPosition=2000 }
        let rect=convert(bounds,to:host)
        tip.frame=CGRect(x:max(12,min(host.bounds.width-280,rect.maxX-268)),y:max(12,rect.minY-117),width:268,height:108)
    }
    override func didUpdateFocus(in context:UIFocusUpdateContext,with coordinator:UIFocusAnimationCoordinator) { super.didUpdateFocus(in:context,with:coordinator);disclose() }
    override func layoutSubviews() { super.layoutSubviews();if !tip.isHidden { disclose() } }
    override func didMoveToWindow() { super.didMoveToWindow();if window==nil { pinned=false;hover=false;tip.isHidden=true } }
    deinit { tip.removeFromSuperview() }
}
