import UIKit
import ClassroomGameCore
import MeadowBattleSupport

/// The effects review lab: one screen that can call every skill, every weapon blow, every projectile, shield state, monster attack / death,
/// a hero going down and the natural 20, on the real battle stage and with the real camera, numbers and lighting. It does not touch the
/// rules: effects are played straight on the stage (`MeadowPartyStageView.labPlay`).
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

    override var prefersStatusBarHidden: Bool { true }
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask { .landscape }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red: 0.055, green: 0.09, blue: 0.065, alpha: 1)
        panel.backgroundColor = MeadowPreviewPalette.panel
        panel.showsVerticalScrollIndicator = true
        column.axis = .vertical; column.spacing = 6; column.alignment = .fill
        panel.addSubview(column)
        status.textColor = MeadowPreviewPalette.ink; status.font = .boldSystemFont(ofSize: 14); status.textAlignment = .center
        status.backgroundColor = UIColor(white: 0, alpha: 0.55); status.text = "特效审核台：点左边的按钮播放"
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
            applySpecies()
        } catch { status.text = "载入失败：\(error.localizedDescription)" }
    }

    /// Both monsters get the chosen species; everyone is alive and unshielded.
    private func applySpecies() {
        guard let model, var state = base else { return }
        for (i, id) in ["m1", "m2"].enumerated() where state.units[id] != nil { state.units[id]?.templateID = species[i] }
        for id in state.units.keys { state.units[id]?.shield = 0 }
        stage.labReset(state, catalog: model.engine.catalog)
    }

    private func buildPanel() {
        column.addArrangedSubview(heading("返回"))
        column.addArrangedSubview(action("× 关闭审核台", color: .systemRed) { [weak self] in self?.close() })
        column.addArrangedSubview(heading("设置"))
        column.addArrangedSubview(segmented(["轻击", "中击", "重击"], selected: 1) { [weak self] i in self?.strength = i })
        column.addArrangedSubview(segmented(["短剑", "巨剑", "弓", "法杖"], selected: 0) { [weak self] i in self?.weapon = ["trainingSword", "greatSword", "huntingBow", "legendaryStaff"][i] })
        column.addArrangedSubview(label("怪物 1（m1）"))
        column.addArrangedSubview(segmented(Self.monsters.map { $0.name }, selected: 0) { [weak self] i in self?.species[0] = Self.monsters[i].id; self?.applySpecies() })
        column.addArrangedSubview(label("怪物 2（m2）"))
        column.addArrangedSubview(segmented(Self.monsters.map { $0.name }, selected: 1) { [weak self] i in self?.species[1] = Self.monsters[i].id; self?.applySpecies() })
        column.addArrangedSubview(action("重置场景", color: .systemTeal) { [weak self] in self?.applySpecies() })

        column.addArrangedSubview(heading("玩家技能 · 打怪物"))
        for (id, name) in [("starlightPulse", "星辉脉冲"), ("runeSlash", "符文斩"), ("dragonFlame", "龙焰"), ("sweep", "横扫")] {
            column.addArrangedSubview(action(name) { [weak self] in self?.skill(id, name: name, allies: false) })
        }
        column.addArrangedSubview(heading("玩家技能 · 友军"))
        for (id, name) in [("rally", "振奋"), ("dragonSoulWard", "龙魂庇护"), ("dragonScaleWard", "龙鳞庇护"), ("runeWard", "符文庇护"), ("battleRune", "战斗符文"), ("dragonOrder", "龙之号令"), ("shieldDome", "简易防护 / 护盾药水 / 援护（施放）")] {
            column.addArrangedSubview(action(name) { [weak self] in self?.skill(id, name: name, allies: true) })
        }
        column.addArrangedSubview(action("治疗 · 小") { [weak self] in self?.skill("healMicro", name: "治疗·小", allies: true) })
        column.addArrangedSubview(action("治疗 · 中") { [weak self] in self?.skill("healStandard", name: "治疗·中", allies: true) })
        column.addArrangedSubview(action("治疗 · 大") { [weak self] in self?.skill("healStrong", name: "治疗·大", allies: true) })

        column.addArrangedSubview(heading("普攻 · 强击 · 突袭（P1 → 怪物1，按上面的武器）"))
        column.addArrangedSubview(action("普通攻击（带投射）") { [weak self] in self?.playerAttack(heavy: false) })
        column.addArrangedSubview(action("强击") { [weak self] in self?.playerAttack(heavy: true) })
        column.addArrangedSubview(action("突袭") { [weak self] in self?.play("hitAmbush", actor: "p1", targets: ["m1"], name: "突袭") })
        column.addArrangedSubview(action("自然 20（一击必杀）", color: .systemOrange) { [weak self] in self?.play("natural20", actor: "p1", targets: ["m1"], name: "自然20", weapon: self?.weapon) })

        column.addArrangedSubview(heading("怪物攻击（怪物1 → P1，按怪物1的种类）"))
        column.addArrangedSubview(action("怪物攻击") { [weak self] in self?.monsterAttack() })
        column.addArrangedSubview(action("怪物死亡（怪物1）") { [weak self] in self?.stage.labKill("m1", from: "p1"); self?.say("怪物死亡 · " + (self?.species[0] ?? "")) })
        column.addArrangedSubview(action("怪物死亡（怪物2）") { [weak self] in self?.stage.labKill("m2", from: "p1"); self?.say("怪物死亡 · " + (self?.species[1] ?? "")) })

        column.addArrangedSubview(heading("护盾（P1）"))
        column.addArrangedSubview(action("生成 · 展开（护盾 8）") { [weak self] in
            self?.stage.labSetShield("p1", 8); self?.stage.labPlay("shieldDome", actor: "p1", targets: ["p1"], power: 1.0); self?.say("护盾生成")
        })
        column.addArrangedSubview(action("抵挡一击（剩 5）") { [weak self] in self?.stage.labBlock("p1", from: "m1", remaining: 5); self?.say("护盾抵挡") })
        column.addArrangedSubview(action("护盾见底（剩 2，裂纹）") { [weak self] in self?.stage.labSetShield("p1", 2); self?.say("护盾 2：闪烁与裂纹") })
        column.addArrangedSubview(action("破碎") { [weak self] in self?.stage.labBreak("p1", from: "m1"); self?.say("护盾破碎") })
        column.addArrangedSubview(action("怪物也有盾（怪物1 生成）") { [weak self] in self?.stage.labSetShield("m1", 6); self?.stage.labPlay("shieldDome", actor: "m1", targets: ["m1"], power: 1.0); self?.say("怪物护盾") })

        column.addArrangedSubview(heading("玩家倒地"))
        column.addArrangedSubview(action("P2 倒地") { [weak self] in self?.stage.labDown("p2", from: "m1"); self?.say("P2 倒地：冲击、魂光上升、等待的光柱") })
        column.addArrangedSubview(action("P2 恢复") { [weak self] in self?.applySpecies(); self?.say("场景重置") })

        column.addArrangedSubview(heading("镜头震动"))
        for (i, name) in ["轻震", "中震", "重震"].enumerated() {
            column.addArrangedSubview(action(name) { [weak self] in self?.stage.labShake(MeadowBattleHitTier(rawValue: i) ?? .medium); self?.say(name) })
        }

        column.addArrangedSubview(heading("连播"))
        column.addArrangedSubview(action("依次播放全部技能", color: .systemPurple) { [weak self] in self?.playAll() })
        column.addArrangedSubview(action("停止连播", color: .systemGray) { [weak self] in self?.sequence?.invalidate(); self?.sequence = nil; self?.say("已停止") })
    }

    // MARK: actions

    private var power: Double { [0.7, 1.0, 1.45][strength] }
    private func say(_ text: String) { status.text = text }

    private func skill(_ id: String, name: String, allies: Bool) {
        let targets = allies ? ["p1", "p2"] : ["m1", "m2"]
        play(id, actor: "p1", targets: targets, name: name)
    }

    private func play(_ id: String, actor: String, targets: [String], name: String, weapon: String? = nil, delay: Double = 0) {
        stage.labPlay(id, actor: actor, targets: targets, power: power, weaponID: weapon ?? self.weapon, delay: delay)
        say(name + " · " + ["轻击", "中击", "重击"][strength])
    }

    /// The hero's blow with the chosen weapon, with its projectile when it has one (the blow lands when the projectile arrives).
    private func playerAttack(heavy: Bool) {
        let scale = heavy ? 1.2 : 1.0
        let w = weapon
        switch w {
        case "greatSword": stage.labPlay("hitGreat", actor: "p1", targets: ["m1"], power: power * scale, weaponID: w)
        case "huntingBow":
            stage.labPlay("projBow", actor: "p1", targets: ["m1"], power: power, weaponID: w)
            stage.labPlay("hitBow", actor: "p1", targets: ["m1"], power: power * scale, weaponID: w, delay: 0.19)
        case "legendaryStaff":
            stage.labPlay("projStaff", actor: "p1", targets: ["m1"], power: power, weaponID: w)
            stage.labPlay("hitStaff", actor: "p1", targets: ["m1"], power: power * scale, weaponID: w, delay: 0.70)
        default: stage.labPlay("hitBlade", actor: "p1", targets: ["m1"], power: power * scale, weaponID: w)
        }
        stage.labShake(MeadowBattleHitTier(rawValue: strength) ?? .medium)
        say((heavy ? "强击" : "普通攻击") + " · " + w)
    }

    /// A monster attack in the way of m1's species: a melee blow, or a missile first for the archer and the dragon.
    private func monsterAttack() {
        let kind = species[0]
        let hit: String
        switch kind {
        case "slime": hit = "hitSlime"
        case "wolf": hit = "hitWolf"
        case "goblinArcher": hit = "hitArrowM"
        case "stoneGuardian": hit = "hitStone"
        case "caveTroll": hit = "hitTroll"
        case "ruinDragon": hit = "hitDragon"
        default: hit = "hitClaw"
        }
        if kind == "goblinArcher" || kind == "ruinDragon" {
            stage.labPlay(kind == "ruinDragon" ? "projDragon" : "projArcher", actor: "m1", targets: ["p1"], power: power)
            stage.labPlay(hit, actor: "m1", targets: ["p1"], power: power, delay: 0.22)
        } else { stage.labPlay(hit, actor: "m1", targets: ["p1"], power: power) }
        stage.labShake(MeadowBattleHitTier(rawValue: strength) ?? .medium)
        say("怪物攻击 · " + kind)
    }

    /// Every skill in turn, three seconds apart.
    private func playAll() {
        sequence?.invalidate()
        let steps: [() -> Void] = [
            { [weak self] in self?.skill("starlightPulse", name: "星辉脉冲", allies: false) },
            { [weak self] in self?.skill("runeSlash", name: "符文斩", allies: false) },
            { [weak self] in self?.skill("dragonFlame", name: "龙焰", allies: false) },
            { [weak self] in self?.skill("sweep", name: "横扫", allies: false) },
            { [weak self] in self?.skill("rally", name: "振奋", allies: true) },
            { [weak self] in self?.skill("dragonSoulWard", name: "龙魂庇护", allies: true) },
            { [weak self] in self?.skill("dragonScaleWard", name: "龙鳞庇护", allies: true) },
            { [weak self] in self?.skill("runeWard", name: "符文庇护", allies: true) },
            { [weak self] in self?.skill("battleRune", name: "战斗符文", allies: true) },
            { [weak self] in self?.skill("dragonOrder", name: "龙之号令", allies: true) },
            { [weak self] in self?.playerAttack(heavy: false) },
            { [weak self] in self?.monsterAttack() },
            { [weak self] in self?.play("natural20", actor: "p1", targets: ["m1"], name: "自然20") }
        ]
        var index = 0
        sequence = Timer.scheduledTimer(withTimeInterval: 3.2, repeats: true) { [weak self] timer in
            guard let self, index < steps.count else { timer.invalidate(); self?.sequence = nil; return }
            steps[index](); index += 1
        }
        sequence?.fire()
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
        column.frame = CGRect(x: 8, y: 8, width: width, height: column.systemLayoutSizeFitting(CGSize(width: width, height: UIView.layoutFittingCompressedSize.height), withHorizontalFittingPriority: .required, verticalFittingPriority: .fittingSizeLevel).height)
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
        let l = UILabel(); l.text = text; l.textColor = MeadowPreviewPalette.muted; l.font = .systemFont(ofSize: 12)
        return l
    }
    private func action(_ title: String, color: UIColor = .systemGreen, _ handler: @escaping () -> Void) -> UIButton {
        var config = UIButton.Configuration.filled()
        config.title = title; config.baseBackgroundColor = color.withAlphaComponent(0.85); config.baseForegroundColor = .white
        config.contentInsets = NSDirectionalEdgeInsets(top: 7, leading: 8, bottom: 7, trailing: 8)
        config.titleLineBreakMode = .byWordWrapping
        let button = UIButton(configuration: config, primaryAction: UIAction { _ in handler() })
        return button
    }
    private func segmented(_ items: [String], selected: Int, _ handler: @escaping (Int) -> Void) -> UISegmentedControl {
        let control = UISegmentedControl(items: items)
        control.selectedSegmentIndex = selected
        control.apportionsSegmentWidthsByContent = items.count > 4
        control.addAction(UIAction { [weak control] _ in handler(control?.selectedSegmentIndex ?? 0) }, for: .valueChanged)
        return control
    }
}
