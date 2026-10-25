import Foundation

@main struct BattleEffectsCheck {
    static func main() throws {
        var traces: [[String: Any]] = []
        var shieldTraces: [[String: Any]] = []
        var healTraces: [[String: Any]] = []
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
            let blocked=shield.resolveEnemyImpact()!
            precondition(blocked.damage == 0 && blocked.shieldAbsorbed == 4 && shield.shield == 0)
            var stacked=MeadowBattleEncounter(); stacked.begin()
            _=stacked.perform(.protection); _=stacked.perform(.protection)
            stacked.endPlayerTurn(); _=stacked.beginEnemyAction()
            precondition(stacked.resolveEnemyImpact()?.shieldAbsorbed == 4 && stacked.shield == 4)
            stacked.completeEnemyTurn(); stacked.endPlayerTurn(); _=stacked.beginEnemyAction()
            precondition(stacked.resolveEnemyImpact()?.shieldAbsorbed == 4 && stacked.shield == 0)
            var ward=MeadowBattleEncounter(); ward.begin(); _=ward.beginAction(.protection)
            var spawn=MeadowBattleImpactClock(duration:0.96,impactTime:0.46)
            while spawn.elapsed < spawn.duration {
                var gained=0
                if spawn.advance(1/Double(fps)) { gained=ward.resolveActionImpact()!.shieldGained }
                shieldTraces.append(["fps":fps,"phase":"generate","time":spawn.elapsed,"shield":ward.shield,"hp":ward.playerHP,"gained":gained,"absorbed":0])
            }
            precondition(ward.shield == 4)
            ward.endPlayerTurn(); _=ward.beginEnemyAction()
            var contact=MeadowBattleImpactClock(duration:1.44,impactTime:0.4416)
            while contact.elapsed < contact.duration {
                var absorbed=0
                if contact.advance(1/Double(fps)) {
                    let hit=ward.resolveEnemyImpact()!; absorbed=hit.shieldAbsorbed
                    precondition(absorbed == 4 && hit.damage == 0 && ward.shield == 0)
                    precondition(ward.resolveEnemyImpact() == nil)
                }
                shieldTraces.append(["fps":fps,"phase":"blockBreak","time":2+contact.elapsed,"shield":ward.shield,"hp":ward.playerHP,"gained":0,"absorbed":absorbed])
            }
        }
        for fps in [15,30,60,120] {
            var healed=MeadowBattleEncounter();healed.begin();healed.endPlayerTurn();_=healed.resolveEnemyAction();healed.completeEnemyTurn()
            precondition(healed.playerHP==8)
            _=healed.beginAction(.breathe)
            var clock=MeadowBattleImpactClock(duration:1.20,impactTime:MeadowBattleRecoveryField.impactTime)
            var hits=0
            while clock.elapsed<clock.duration {
                var amount=0
                if clock.advance(1/Double(fps)) { amount=healed.resolveActionImpact()!.healed;hits+=1 }
                healTraces.append(["fps":fps,"elapsed":clock.elapsed,"hp":healed.playerHP,"healed":amount])
                if clock.elapsed<MeadowBattleRecoveryField.impactTime { precondition(healed.playerHP==8) }
            }
            precondition(hits==1 && healed.playerHP==12 && healed.resolveActionImpact()==nil)
        }
        precondition(MeadowBattleRecoveryField.sample(-0.1).isEmpty && MeadowBattleRecoveryField.sample(2).isEmpty)
        for tick in 0..<160 {
            let particles=MeadowBattleRecoveryField.sample(Double(tick)/100)
            for p in particles { precondition(p.x.isFinite && p.y.isFinite && p.alpha>=0 && p.alpha<=1 && p.y<=0) }
        }
        precondition(abs(MeadowBattleImpactClock.strikePoseTime(1.048)-0.648) < 1e-8)
        precondition(abs(MeadowBattleImpactClock.strikePoseTime(1.148)-0.648) < 1e-8)
        precondition(abs(MeadowBattleImpactClock.strikePoseTime(MeadowBattleImpactClock.strikeDuration)-1.2) < 1e-8)
        var particleTraces: [[String: Any]] = []
        for kind in MeadowBattleLightKind.allCases {
            precondition(MeadowBattleLightField.sample(kind,age:-0.01,originX:0,originY:-100,groundY:0).isEmpty)
            precondition(MeadowBattleLightField.sample(kind,age:3,originX:0,originY:-100,groundY:0).isEmpty)
            precondition(!MeadowBattleLightField.sample(kind,age:0,originX:0,originY:-100,groundY:0).isEmpty)
            var sawContact=false, sawRebound=false
            for frame in 0..<75 {
                let particles=MeadowBattleLightField.sample(kind,age:Double(frame)*0.04,originX:0,originY:-100,groundY:0)
                precondition(particles.count <= 52)
                for p in particles {
                    precondition(p.x.isFinite && p.y.isFinite && p.alpha.isFinite)
                    precondition(p.y <= p.groundY + 1e-8 && p.alpha >= 0 && p.alpha <= 1)
                    if p.groundAge != nil { sawContact=true }
                    if p.bounces>0 && p.y < p.groundY-1 { sawRebound=true }
                    particleTraces.append(["kind":kind.rawValue,"frame":frame,"id":p.id,"x":p.x,"y":p.y,"angle":p.angle,"size":p.size,"alpha":p.alpha,"cyan":p.cyan,"groundX":p.groundX,"groundY":p.groundY,"groundAge":p.groundAge as Any? ?? NSNull(),"bounces":p.bounces])
                }
            }
            precondition(sawContact && sawRebound)
            // Exact same sample after different caller cadences: no hidden integrator state.
            let before=MeadowBattleLightField.sample(kind,age:0.8,originX:0,originY:-100,groundY:0)
            for fps in [15,30,60,120] {
                for tick in 0..<fps { _=MeadowBattleLightField.sample(kind,age:Double(tick)/Double(fps),originX:0,originY:-100,groundY:0) }
                let after=MeadowBattleLightField.sample(kind,age:0.8,originX:0,originY:-100,groundY:0)
                precondition(before.map(\.x)==after.map(\.x) && before.map(\.y)==after.map(\.y))
            }
        }
        let out = URL(fileURLWithPath: CommandLine.arguments[1])
        try FileManager.default.createDirectory(at: out.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONSerialization.data(withJSONObject: ["scope":"production model and one-shot impact clock; no UI/device execution", "lastStrike":traces,"shieldSequence":shieldTraces,"lightParticles":particleTraces,"healSequence":healTraces], options:[.prettyPrinted,.sortedKeys]).write(to:out)
        print("Battle VFX checks passed: deferred HP/AP, single impact, lethal same-event transition, nonlethal survival, cancel/retry, shield, contact hold and deterministic ground-bouncing light debris and one-shot recovery at 15/30/60/120Hz.")
    }
}
