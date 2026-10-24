import Foundation

enum MeadowBattleAnimationCue: Equatable {
    case strike
    case guardPose
    case heal
    case enemyStrike
    case victory
    case defeat
}

enum MeadowBattlePhase: Equatable {
    case exploration
    case playerTurn
    case enemyPreparing
    case enemyTurn
    case victory
    case defeat
}

enum MeadowBattleAction {
    case strike
    case breathe
    case protection
}

struct MeadowBattleActionResult: Equatable {
    let cue: MeadowBattleAnimationCue
    let damage: Int
    let healed: Int
    let shieldGained: Int
}

/// Small, deterministic encounter used by the preview. This models only P1 and
/// one Forest Warden; it does not claim to implement the tabletop rules.
struct MeadowBattleEncounter {
    private(set) var phase: MeadowBattlePhase = .exploration
    private(set) var round = 0
    private(set) var playerHP = 12
    let playerMaxHP = 12
    private(set) var enemyHP = 18
    let enemyMaxHP = 18
    private(set) var shield = 0
    private(set) var actionPoints = 0
    private(set) var breathUses = 2
    private(set) var guardUses = 2
    private(set) var enemySelected = false

    mutating func begin() {
        guard phase == .exploration else { return }
        round = 1
        playerHP = playerMaxHP
        enemyHP = enemyMaxHP
        shield = 0
        actionPoints = 3
        breathUses = 2
        guardUses = 2
        enemySelected = false
        phase = .playerTurn
    }

    mutating func selectEnemy() {
        guard phase == .playerTurn else { return }
        enemySelected.toggle()
    }

    mutating func perform(_ action: MeadowBattleAction) -> MeadowBattleActionResult? {
        guard phase == .playerTurn, actionPoints > 0 else { return nil }
        switch action {
        case .strike:
            guard enemySelected, enemyHP > 0 else { return nil }
            actionPoints -= 1
            // A fixed five damage keeps this small demo deterministic; the result
            // reports actual HP removed when the target has fewer than five left.
            let damage = min(5, enemyHP)
            enemyHP -= damage
            if enemyHP == 0 { phase = .victory }
            return MeadowBattleActionResult(cue: .strike, damage: damage, healed: 0, shieldGained: 0)
        case .breathe:
            guard breathUses > 0, playerHP < playerMaxHP else { return nil }
            actionPoints -= 1
            breathUses -= 1
            let amount = min(4, playerMaxHP - playerHP)
            playerHP += amount
            return MeadowBattleActionResult(cue: .heal, damage: 0, healed: amount, shieldGained: 0)
        case .protection:
            guard guardUses > 0 else { return nil }
            actionPoints -= 1
            guardUses -= 1
            shield += 4
            return MeadowBattleActionResult(cue: .guardPose, damage: 0, healed: 0, shieldGained: 4)
        }
    }

    mutating func endPlayerTurn() {
        guard phase == .playerTurn else { return }
        enemySelected = false
        phase = .enemyPreparing
    }

    /// Applies the enemy's fixed demo hit after the visible wind-up delay.
    mutating func resolveEnemyAction() -> MeadowBattleActionResult? {
        guard phase == .enemyPreparing else { return nil }
        phase = .enemyTurn
        var incoming = 4
        let absorbed = min(shield, incoming)
        shield -= absorbed
        incoming -= absorbed
        playerHP = max(0, playerHP - incoming)
        if playerHP == 0 { phase = .defeat }
        return MeadowBattleActionResult(cue: .enemyStrike, damage: incoming, healed: 0, shieldGained: 0)
    }

    mutating func completeEnemyTurn() {
        guard phase == .enemyTurn else { return }
        round += 1
        actionPoints = 3
        phase = .playerTurn
    }

    mutating func returnToMap() {
        phase = .exploration
        round = 0
        playerHP = playerMaxHP
        enemyHP = enemyMaxHP
        shield = 0
        actionPoints = 0
        breathUses = 2
        guardUses = 2
        enemySelected = false
    }

    mutating func retry() { returnToMap(); begin() }

    var isEncounterActive: Bool { phase != .exploration }
    var isPlayerActionEnabled: Bool { phase == .playerTurn && actionPoints > 0 }
}
