import Foundation

@main struct BattleEffectsCheck {
    static func main() throws {
        var traces: [[String: Any]] = []
        for fps in [15, 30, 60, 120] {
            var battle = MeadowBattleEncounter(); battle.begin(); battle.selectEnemy()
            for attack in 0..<4 {
                if attack == 3 {
                    battle.endPlayerTurn()
                    let hp = battle.playerHP
                    precondition(battle.beginEnemyAction())
                    precondition(battle.playerHP == hp)
                    precondition(battle.resolveEnemyImpact()?.damage == 4)
                    precondition(battle.resolveEnemyImpact() == nil)
                    battle.completeEnemyTurn(); battle.selectEnemy()
                }
                let hpBefore = battle.enemyHP, ap = battle.actionPoints
                precondition(battle.beginAction(.strike) == .strike)
                precondition(battle.enemyHP == hpBefore && battle.actionPoints == ap - 1)
                precondition(battle.beginAction(.strike) == nil)
                battle.selectEnemy(); precondition(battle.enemySelected)
                battle.endPlayerTurn(); precondition(battle.phase == .playerTurn)
                var clock = MeadowBattleImpactClock(duration: MeadowBattleImpactClock.strikeDuration, impactTime: MeadowBattleImpactClock.strikeContact)
                var hits = 0
                while clock.elapsed < clock.duration {
                    var damage = 0
                    if clock.advance(1 / Double(fps)) {
                        let result = battle.resolveActionImpact()!; damage = result.damage; hits += 1
                        precondition(battle.resolveActionImpact() == nil)
                        precondition(clock.elapsed - MeadowBattleImpactClock.strikeContact <= 1 / Double(fps) + 1e-8)
                        precondition(battle.enemyHP == max(0, hpBefore - 5))
                    }
                    if clock.elapsed < MeadowBattleImpactClock.strikeContact { precondition(battle.enemyHP == hpBefore) }
                    if attack == 3 {
                        traces.append(["fps": fps, "elapsed": clock.elapsed, "hp": battle.enemyHP, "damage": damage,
                                       "impact": damage > 0, "defeated": battle.phase == .victory,
                                       "poseProgress": MeadowBattleImpactClock.strikePoseTime(clock.elapsed)/1.2])
                        if damage > 0 { precondition(battle.phase == .victory && battle.enemyHP == 0 && damage == 3) }
                    } else { precondition(battle.phase != .victory) }
                }
                precondition(hits == 1 && !clock.advance(10))
            }
            precondition(battle.phase == .victory)
            battle.retry(); precondition(battle.enemyHP == 18 && battle.pendingAction == nil)
            battle.selectEnemy(); _ = battle.beginAction(.strike); battle.returnToMap()
            precondition(battle.resolveActionImpact() == nil && battle.enemyHP == 18)
            var shield = MeadowBattleEncounter(); shield.begin()
            _ = shield.beginAction(.protection); precondition(shield.shield == 0)
            precondition(shield.resolveActionImpact()?.shieldGained == 4)
            shield.endPlayerTurn(); precondition(shield.beginEnemyAction())
            precondition(shield.playerHP == 12 && shield.shield == 4)
            precondition(shield.resolveEnemyImpact()?.damage == 0 && shield.shield == 0)
        }
        precondition(abs(MeadowBattleImpactClock.strikePoseTime(1.048)-0.648) < 1e-8)
        precondition(abs(MeadowBattleImpactClock.strikePoseTime(1.128)-0.648) < 1e-8)
        let out = URL(fileURLWithPath: CommandLine.arguments[1])
        try FileManager.default.createDirectory(at: out.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONSerialization.data(withJSONObject: ["scope":"production model and one-shot impact clock; no UI/device execution", "lastStrike":traces], options:[.prettyPrinted,.sortedKeys]).write(to:out)
        print("Battle VFX checks passed: deferred HP/AP, single impact, lethal same-event transition, nonlethal survival, cancel/retry, shield, contact hold at 15/30/60/120Hz.")
    }
}
