import UIKit
import ClassroomGameCore
import MeadowBattleSupport

/// The effects review lab: one screen that can call every skill, every weapon blow, every projectile, shield state, monster attack / skill /
/// death, a hero going down and coming back, and the natural 20 - on the real battle stage, with the real motions, camera, numbers and light.
/// It does not touch the rules: actions are played with real intents but no rule receipt, and what the receipt would have caused (the blow,
/// the number, a shield, a death) is played straight on the stage at the rule's impact time.
final class MeadowEffectsLabViewController: UIViewController {
    private let stage = MeadowPartyStageView()
    private var model: PartyEncounter?
    private var base: GameState?
    private let panel = UIScrollView()
    private let column = UIStackView()
    private let status = UILabel()
    private var strength = 1
    private var weapon = "trainingSword"
    private var species = ["slime", "wolf"]
    private var sequence: Timer?

    private static let monsters: [(id: String, name: String)] = [("slime", "史莱姆"), ("wolf", "森林狼"), ("goblinArcher", "哥布林弓手"), ("stoneGuardian", "石像守卫"), ("caveTroll", "洞穴巨魔"), ("ruinDragon", "遗迹魔龙")]
    private static let weapons: [(id: String, name: String)] = [("trainingSword", "短剑"), ("greatSword", "巨剑"), ("huntingBow", "弓"), ("legendaryStaff", "法杖")]

    override var prefersStatusBarHidden: Bool { true }
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask { .landscape }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red: 0.055, green: 0.09, blue: 0.065, alpha: 1)
        panel.backgroundColor = MeadowPreviewPalette.panel
        column.axis = .vertical; column.spacing = 6; column.alignment = .fill
        panel.addSubview(column)
        status.textColor = MeadowPreviewPalette.ink; status.font = .boldSystemFont(ofSize: 14); status.textAlignment = .center
        status.backgroundColor = UIColor(white: 0, alpha: 0.55); status.text = "特效审核台：点左边的按钮播放（带动作的会先播完再接下一个）"
        view.addSubview(stage); view.addSubview(panel); view.addSubview(status)
        buildPanel()
        loadStage()
    }

    private func loadStage() {
        do {
            let encounter = try PartyEncounter(playerClassID: "adventurer")
            model = encounter; base = encounter.state
            stage.configureMonsters(encounter.monsterIDs)
            stage.start()
            resetScene()
        } catch { status.text = "载入失败：\(error.localizedDescription)" }
    }

    /// Both monsters get the chosen species, P1 the chosen weapon; everyone is alive and unshielded.
    private func resetScene() {
        guard let model, var state = base else { return }
        for (i, id) in ["m1", "m2"].enumerated() where state.units[id] != nil { state.units[id]?.templateID = species[i] }
        for id in state.units.keys { state.units[id]?.shield = 0 }
        state.units["p1"]?.equipment.weapon = weapon
        stage.labReset(state, catalog: model.engine.catalog)
    }

    private func buildPanel() {
        column.addArrangedSubview(action("× 关闭审核台", color: .systemRed) { [weak self] in self?.close() })
        column.addArrangedSubview(heading("设置"))
        column.addArrangedSubview(segmented(["轻击", "中击", "重击"], selected: 1) { [weak self] i in self?.strength = i })
        column.addArrangedSubview(label("P1 武器"))
        column.addArrangedSubview(segmented(Self.weapons.map { $0.name }, selected: 0) { [weak self] i in
            guard let self else { return }
            self.weapon = Self.weapons[i].id; self.stage.labSetWeapon("p1", self.weapon)
        })
        column.addArrangedSubview(label("怪物 1（m1，审核台里的怪物动作都由它来做）"))
        column.addArrangedSubview(segmented(Self.monsters.map { $0.name }, selected: 0) { [weak self] i in self?.species[0] = Self.monsters[i].id; self?.resetScene() })
        column.addArrangedSubview(label("怪物 2（m2）"))
        column.addArrangedSubview(segmented(Self.monsters.map { $0.name }, selected: 1) { [weak self] i in self?.species[1] = Self.monsters[i].id; self?.resetScene() })
        column.addArrangedSubview(action("重置场景", color: .systemTeal) { [weak self] in self?.resetScene(); self?.say("场景重置") })

        column.addArrangedSubview(heading("P1 动作 · 攻击（按上面的武器）"))
        column.addArrangedSubview(action("普通攻击") { [weak self] in self?.attack(.attack, name: "普通攻击") })
        column.addArrangedSubview(action("强击") { [weak self] in self?.attack(.heavyStrike, name: "强击") })
        column.addArrangedSubview(action("突袭") { [weak self] in self?.attack(.ambush, name: "突袭") })
        column.addArrangedSubview(action("自然 20（一击必杀）", color: .systemOrange) { [weak self] in self?.naturalTwenty() })
        column.addArrangedSubview(heading("P1 动作 · 技能打怪物"))
        for (a, name) in [(PartyAction.starlightPulse, "星辉脉冲"), (.runeSlash, "符文斩"), (.dragonFlame, "龙焰"), (.sweep, "横扫")] {
            column.addArrangedSubview(action(name) { [weak self] in self?.offensiveSkill(a, name: name) })
        }
        column.addArrangedSubview(heading("P1 动作 · 增益与护盾"))
        for (a, name, shield, heal, buff) in [(PartyAction.rally, "振奋", 0, 0, 2), (.dragonSoulWard, "龙魂庇护", 10, 10, 3), (.dragonScaleWard, "龙鳞庇护", 10, 12, 2), (.runeWard, "符文庇护", 6, 8, 0), (.battleRune, "战斗符文", 4, 0, 3), (.dragonOrder, "龙之号令", 8, 6, 4)] {
            column.addArrangedSubview(action(name) { [weak self] in self?.supportSkill(a, name: name, targets: ["p1", "p2"], shield: shield, heal: heal, buff: buff) })
        }
        column.addArrangedSubview(action("简易防护") { [weak self] in self?.supportSkill(.simpleGuard, name: "简易防护", targets: ["p1"], shield: 4) })
        column.addArrangedSubview(action("援护（P1 → P2）") { [weak self] in self?.supportSkill(.support, name: "援护", targets: ["p2"], shield: 4, heal: 6) })
        column.addArrangedSubview(action("喘息（自身恢复）") { [weak self] in self?.supportSkill(.breather, name: "喘息", targets: ["p1"], shield: 0, heal: 4) })
        column.addArrangedSubview(heading("P1 动作 · 道具"))
        column.addArrangedSubview(action("小治疗药水") { [weak self] in self?.supportSkill(.smallPotion, name: "小治疗药水", targets: ["p1"], shield: 0, heal: 4) })
        column.addArrangedSubview(action("大治疗药水") { [weak self] in self?.supportSkill(.largePotion, name: "大治疗药水", targets: ["p1"], shield: 0, heal: 12) })
        column.addArrangedSubview(action("护盾药水") { [weak self] in self?.supportSkill(.shieldPotion, name: "护盾药水", targets: ["p1"], shield: 8) })
        column.addArrangedSubview(action("复活石（先让 P2 倒地）") { [weak self] in self?.revivalStone() })

        column.addArrangedSubview(heading("怪物 1 动作"))
        column.addArrangedSubview(action("怪物攻击（按种类）") { [weak self] in self?.monsterAttack() })
        column.addArrangedSubview(action("石肤（护盾）") { [weak self] in self?.monsterSkill(.simpleGuard, name: "石肤", targets: ["m1"], shield: 6) })
        column.addArrangedSubview(action("再生（恢复）") { [weak self] in self?.monsterSkill(.regeneration, name: "再生", targets: ["m1"], heal: 8) })
        column.addArrangedSubview(action("横扫（打两名玩家）") { [weak self] in self?.monsterSkill(.sweep, name: "横扫", targets: ["p1", "p2"], damage: 7) })
        column.addArrangedSubview(action("龙焰（打两名玩家）") { [weak self] in self?.monsterSkill(.dragonFlame, name: "龙焰", targets: ["p1", "p2"], damage: 12) })
        column.addArrangedSubview(action("龙鳞（护盾）") { [weak self] in self?.monsterSkill(.dragonScaleWard, name: "龙鳞", targets: ["m1"], shield: 10) })

        column.addArrangedSubview(heading("单独特效 · 死亡、倒地、复活"))
        column.addArrangedSubview(action("怪物 1 死亡") { [weak self] in self?.stage.labKill("m1", from: "p1"); self?.say("怪物死亡 · " + (self?.species[0] ?? "")) })
        column.addArrangedSubview(action("怪物 2 死亡") { [weak self] in self?.stage.labKill("m2", from: "p1"); self?.say("怪物死亡 · " + (self?.species[1] ?? "")) })
        column.addArrangedSubview(action("P2 倒地") { [weak self] in self?.stage.labDown("p2", from: "m1"); self?.say("P2 倒地：人物隐去，原地留下魂晶标志") })
        column.addArrangedSubview(action("P2 复活（只看特效）") { [weak self] in self?.stage.labRevive("p2"); self?.say("P2 复活") })

        column.addArrangedSubview(heading("单独特效 · 护盾（P1）"))
        column.addArrangedSubview(action("生成 · 展开（护盾 8）") { [weak self] in
            self?.stage.labSetShield("p1", 8); self?.stage.labPlay("shieldDome", actor: "p1", targets: ["p1"], power: 1.0); self?.say("护盾生成")
        })
        column.addArrangedSubview(action("抵挡一击（剩 5）") { [weak self] in self?.stage.labBlock("p1", from: "m1", remaining: 5); self?.say("护盾抵挡") })
        column.addArrangedSubview(action("护盾见底（剩 2：裂纹、闪烁、掉碎片）") { [weak self] in self?.stage.labSetShield("p1", 2); self?.say("护盾见底") })
        column.addArrangedSubview(action("破碎") { [weak self] in self?.stage.labBreak("p1", from: "m1"); self?.say("护盾破碎") })

        column.addArrangedSubview(heading("单独特效 · 增伤持续"))
        for (amount, name) in [(2, "增伤 +2（P1、P2）"), (4, "增伤 +4（P1、P2）"), (0, "清除增伤")] {
            column.addArrangedSubview(action(name) { [weak self] in self?.stage.labSetBuff("p1", amount); self?.stage.labSetBuff("p2", amount); self?.say(name) })
        }
        column.addArrangedSubview(heading("镜头震动"))
        for (i, name) in ["轻震", "中震", "重震"].enumerated() {
            column.addArrangedSubview(action(name) { [weak self] in self?.stage.labShake(MeadowBattleHitTier(rawValue: i) ?? .medium); self?.say(name) })
        }

        column.addArrangedSubview(heading("连播"))
        column.addArrangedSubview(action("依次播放全部动作", color: .systemPurple) { [weak self] in self?.playAll() })
        column.addArrangedSubview(action("停止连播", color: .systemGray) { [weak self] in self?.sequence?.invalidate(); self?.sequence = nil; self?.say("已停止") })
    }

    // MARK: actions with motion

    private var power: Double { [0.7, 1.0, 1.45][strength] }
    private var tier: MeadowBattleHitTier { MeadowBattleHitTier(rawValue: strength) ?? .medium }
    private func say(_ text: String) { status.text = text }
    private func damage(_ base: Int) -> Int { [max(2, base / 2), base, base * 2][strength] }

    /// Plays a real intent (its motion, cast, projectile and skill effects) without a rule receipt. Returns the impact time, or nil if busy.
    @discardableResult
    private func perform(_ act: PartyAction, actor: String, targets: [String], enemy: Bool, name: String) -> Double? {
        guard let state = stage.labState else { return nil }
        if stage.isPlaying { say("还在播放：" + name + " 稍后再点"); return nil }
        let template = state.units[actor]?.templateID
        let ranged = enemy && act == .attack && (template == "goblinArcher" || template == "ruinDragon")
        let intent = PartyIntent(id: UUID().uuidString, action: act, actor: actor, target: targets[0], targets: targets, command: .monsterStep, enemy: enemy,
                                 weaponID: enemy ? nil : weapon, monsterTemplateID: enemy ? template : nil, enemyRanged: ranged)
        stage.play(intent, before: state, confirmed: nil, onImpact: { nil }, completion: { [weak self] in self?.stage.preview(nil, target: targets[0]) })
        say(name + " · " + ["轻击", "中击", "重击"][strength])
        return intent.impactAge
    }

    private func blowID() -> String {
        switch weapon { case "greatSword": return "hitGreat"; case "huntingBow": return "hitBow"; case "legendaryStaff": return "hitStaff"; default: return "hitBlade" }
    }

    private func attack(_ act: PartyAction, name: String) {
        guard let impact = perform(act, actor: "p1", targets: ["m1"], enemy: false, name: name) else { return }
        let scale = act == .heavyStrike ? 1.2 : 1.0
        stage.labPlay(act == .ambush ? "hitAmbush" : blowID(), actor: "p1", targets: ["m1"], power: power * scale, weaponID: weapon, delay: impact)
        stage.labShake(tier, delay: impact)
        stage.labNumber("−\(damage(act == .heavyStrike ? 10 : 8))", target: "m1", kind: .damage, rank: strength, delay: impact)
    }

    private func naturalTwenty() {
        guard let impact = perform(.attack, actor: "p1", targets: ["m1"], enemy: false, name: "自然 20") else { return }
        stage.labPlay("natural20", actor: "p1", targets: ["m1"], power: 1.0, weaponID: weapon, delay: impact)
        stage.labNumber("20!", target: "m1", kind: .crit, rank: 2, delay: impact)
        DispatchQueue.main.asyncAfter(deadline: .now() + impact + 0.25) { [weak self] in self?.stage.labKill("m1", from: "p1") }
    }

    private func offensiveSkill(_ act: PartyAction, name: String) {
        guard let impact = perform(act, actor: "p1", targets: ["m1", "m2"], enemy: false, name: name) else { return }
        for (i, id) in ["m1", "m2"].enumerated() { stage.labNumber("−\(damage(12))", target: id, kind: .damage, rank: strength, delay: impact + 0.07 * Double(i)) }
    }

    private func supportSkill(_ act: PartyAction, name: String, targets: [String], shield: Int, heal: Int = 6, buff: Int = 0) {
        guard let impact = perform(act, actor: "p1", targets: targets, enemy: false, name: name) else { return }
        for id in targets {
            if heal > 0 { stage.labPlay(heal >= 10 ? "healStrong" : heal >= 6 ? "healStandard" : "healMicro", actor: "p1", targets: [id], power: 1.0, delay: impact); stage.labNumber("+\(heal)", target: id, kind: .heal, rank: 1, delay: impact) }
            if shield > 0 { stage.labNumber("+\(shield)", target: id, kind: .shield, rank: 1, delay: impact + 0.1) }
            if buff > 0 { stage.labNumber("↑\(buff)", target: id, kind: .buff, rank: 1, delay: impact + 0.2) }
        }
        if shield > 0 { DispatchQueue.main.asyncAfter(deadline: .now() + impact) { [weak self] in for id in targets { self?.stage.labSetShield(id, shield) } } }
        if buff > 0 { DispatchQueue.main.asyncAfter(deadline: .now() + impact) { [weak self] in for id in targets { self?.stage.labSetBuff(id, buff) } } }
    }

    private func revivalStone() {
        guard let state = stage.labState else { return }
        if state.units["p2"]?.isAlive ?? true { stage.labDown("p2", from: "m1"); say("P2 先倒地，再点一次复活石"); return }
        guard let impact = perform(.revivalStone, actor: "p1", targets: ["p2"], enemy: false, name: "复活石") else { return }
        DispatchQueue.main.asyncAfter(deadline: .now() + impact) { [weak self] in self?.stage.labRevive("p2") }
    }

    /// m1 attacks P1 in the way of its species (the archer and the dragon shoot first: their missile comes from the attack itself).
    private func monsterAttack() {
        let kind = species[0], hit: String
        switch kind {
        case "slime": hit = "hitSlime"; case "wolf": hit = "hitWolf"; case "goblinArcher": hit = "hitArrowM"
        case "stoneGuardian": hit = "hitStone"; case "caveTroll": hit = "hitTroll"; case "ruinDragon": hit = "hitDragon"
        default: hit = "hitClaw"
        }
        guard let impact = perform(.attack, actor: "m1", targets: ["p1"], enemy: true, name: "怪物攻击 · " + kind) else { return }
        stage.labPlay(hit, actor: "m1", targets: ["p1"], power: power, delay: impact)
        stage.labShake(tier, delay: impact)
        stage.labNumber("−\(damage(6))", target: "p1", kind: .damage, rank: strength, delay: impact)
    }

    private func monsterSkill(_ act: PartyAction, name: String, targets: [String], shield: Int = 0, heal: Int = 0, damage dmg: Int = 0) {
        guard let impact = perform(act, actor: "m1", targets: targets, enemy: true, name: name) else { return }
        for (i, id) in targets.enumerated() {
            if dmg > 0 { stage.labNumber("−\(damage(dmg))", target: id, kind: .damage, rank: strength, delay: impact + 0.07 * Double(i)) }
            if heal > 0 { stage.labPlay("healStandard", actor: "m1", targets: [id], power: 1.0, delay: impact); stage.labNumber("+\(heal)", target: id, kind: .heal, rank: 1, delay: impact) }
            if shield > 0 { stage.labNumber("+\(shield)", target: id, kind: .shield, rank: 1, delay: impact) }
        }
        if shield > 0 { DispatchQueue.main.asyncAfter(deadline: .now() + impact) { [weak self] in for id in targets { self?.stage.labSetShield(id, shield) } } }
    }

    /// Every action in turn, waiting for each to finish.
    private func playAll() {
        sequence?.invalidate()
        let steps: [() -> Void] = [
            { [weak self] in self?.attack(.attack, name: "普通攻击") },
            { [weak self] in self?.attack(.heavyStrike, name: "强击") },
            { [weak self] in self?.attack(.ambush, name: "突袭") },
            { [weak self] in self?.offensiveSkill(.starlightPulse, name: "星辉脉冲") },
            { [weak self] in self?.offensiveSkill(.runeSlash, name: "符文斩") },
            { [weak self] in self?.offensiveSkill(.dragonFlame, name: "龙焰") },
            { [weak self] in self?.offensiveSkill(.sweep, name: "横扫") },
            { [weak self] in self?.supportSkill(.rally, name: "振奋", targets: ["p1", "p2"], shield: 0, heal: 0, buff: 2) },
            { [weak self] in self?.supportSkill(.dragonSoulWard, name: "龙魂庇护", targets: ["p1", "p2"], shield: 10) },
            { [weak self] in self?.supportSkill(.dragonScaleWard, name: "龙鳞庇护", targets: ["p1", "p2"], shield: 10) },
            { [weak self] in self?.supportSkill(.runeWard, name: "符文庇护", targets: ["p1", "p2"], shield: 6) },
            { [weak self] in self?.supportSkill(.battleRune, name: "战斗符文", targets: ["p1", "p2"], shield: 4) },
            { [weak self] in self?.supportSkill(.dragonOrder, name: "龙之号令", targets: ["p1", "p2"], shield: 8) },
            { [weak self] in self?.monsterAttack() },
            { [weak self] in self?.monsterSkill(.dragonFlame, name: "龙焰（怪物）", targets: ["p1", "p2"], damage: 12) },
            { [weak self] in self?.naturalTwenty() }
        ]
        var index = 0
        sequence = Timer.scheduledTimer(withTimeInterval: 0.25, repeats: true) { [weak self] timer in
            guard let self else { timer.invalidate(); return }
            if self.stage.isPlaying { return }
            guard index < steps.count else { timer.invalidate(); self.sequence = nil; self.say("连播结束"); return }
            if index > 0 && index % 4 == 0 { self.resetScene() }
            steps[index](); index += 1
        }
    }

    private func close() {
        sequence?.invalidate(); sequence = nil
        stage.stop()
        dismiss(animated: true)
    }

    // MARK: layout

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        let bounds = view.bounds, panelWidth = min(300, bounds.width * 0.34)
        panel.frame = CGRect(x: 0, y: 0, width: panelWidth, height: bounds.height)
        let width = panelWidth - 16
        let height = column.systemLayoutSizeFitting(CGSize(width: width, height: UIView.layoutFittingCompressedSize.height), withHorizontalFittingPriority: .required, verticalFittingPriority: .fittingSizeLevel).height
        column.frame = CGRect(x: 8, y: 8, width: width, height: height)
        panel.contentSize = CGSize(width: panelWidth, height: column.frame.maxY + 24)
        let stageWidth = bounds.width - panelWidth
        stage.frame = CGRect(x: panelWidth, y: 0, width: stageWidth, height: bounds.height)
        status.frame = CGRect(x: panelWidth, y: bounds.height - 30, width: stageWidth, height: 30)
    }

    override func viewDidDisappear(_ animated: Bool) { super.viewDidDisappear(animated); sequence?.invalidate(); sequence = nil }

    // MARK: small builders

    private func heading(_ text: String) -> UILabel {
        let l = UILabel(); l.text = text; l.textColor = MeadowPreviewPalette.gold; l.font = .boldSystemFont(ofSize: 13); l.numberOfLines = 0
        return l
    }
    private func label(_ text: String) -> UILabel {
        let l = UILabel(); l.text = text; l.textColor = MeadowPreviewPalette.muted; l.font = .systemFont(ofSize: 12); l.numberOfLines = 0
        return l
    }
    private func action(_ title: String, color: UIColor = .systemGreen, _ handler: @escaping () -> Void) -> UIButton {
        var config = UIButton.Configuration.filled()
        config.title = title; config.baseBackgroundColor = color.withAlphaComponent(0.85); config.baseForegroundColor = .white
        config.contentInsets = NSDirectionalEdgeInsets(top: 7, leading: 8, bottom: 7, trailing: 8)
        config.titleLineBreakMode = .byWordWrapping
        return UIButton(configuration: config, primaryAction: UIAction { _ in handler() })
    }
    private func segmented(_ items: [String], selected: Int, _ handler: @escaping (Int) -> Void) -> UISegmentedControl {
        let control = UISegmentedControl(items: items)
        control.selectedSegmentIndex = selected
        control.apportionsSegmentWidthsByContent = items.count > 4
        control.addAction(UIAction { [weak control] _ in handler(control?.selectedSegmentIndex ?? 0) }, for: .valueChanged)
        return control
    }
}
