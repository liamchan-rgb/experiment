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

enum MeadowBattleAction: Equatable {
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
    private(set) var pendingAction: MeadowBattleAction?
    private(set) var enemyImpactPending = false

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
        guard phase == .playerTurn, pendingAction == nil else { return }
        enemySelected.toggle()
    }

    mutating func perform(_ action: MeadowBattleAction) -> MeadowBattleActionResult? {
        guard beginAction(action) != nil else { return nil }
        return resolveActionImpact()
    }

    /// Reserve an action, but keep HP unchanged until the animation's contact.
    mutating func beginAction(_ action: MeadowBattleAction) -> MeadowBattleAnimationCue? {
        guard phase == .playerTurn, actionPoints > 0, pendingAction == nil else { return nil }
        let cue: MeadowBattleAnimationCue
        switch action {
        case .strike: guard enemySelected, enemyHP > 0 else { return nil }; cue = .strike
        case .breathe: guard breathUses > 0, playerHP < playerMaxHP else { return nil }; cue = .heal
        case .protection: guard guardUses > 0 else { return nil }; cue = .guardPose
        }
        pendingAction = action; actionPoints -= 1
        return cue
    }

    mutating func resolveActionImpact() -> MeadowBattleActionResult? {
        guard phase == .playerTurn, let action = pendingAction else { return nil }
        pendingAction = nil
        // AP was already reserved. Effects and HP resolve exactly once here.
        switch action {
        case .strike:
            guard enemySelected, enemyHP > 0 else { return nil }
            // A fixed five damage keeps this small demo deterministic; the result
            // reports actual HP removed when the target has fewer than five left.
            let damage = min(5, enemyHP)
            enemyHP -= damage
            if enemyHP == 0 { phase = .victory }
            return MeadowBattleActionResult(cue: .strike, damage: damage, healed: 0, shieldGained: 0)
        case .breathe:
            guard breathUses > 0, playerHP < playerMaxHP else { return nil }
            breathUses -= 1
            let amount = min(4, playerMaxHP - playerHP)
            playerHP += amount
            return MeadowBattleActionResult(cue: .heal, damage: 0, healed: amount, shieldGained: 0)
        case .protection:
            guard guardUses > 0 else { return nil }
            guardUses -= 1
            shield += 4
            return MeadowBattleActionResult(cue: .guardPose, damage: 0, healed: 0, shieldGained: 4)
        }
    }

    mutating func endPlayerTurn() {
        guard phase == .playerTurn, pendingAction == nil else { return }
        enemySelected = false
        phase = .enemyPreparing
    }

    /// Applies the enemy's fixed demo hit after the visible wind-up delay.
    mutating func resolveEnemyAction() -> MeadowBattleActionResult? {
        guard beginEnemyAction() else { return nil }
        return resolveEnemyImpact()
    }

    mutating func beginEnemyAction() -> Bool {
        guard phase == .enemyPreparing else { return false }
        phase = .enemyTurn
        enemyImpactPending = true
        return true
    }

    mutating func resolveEnemyImpact() -> MeadowBattleActionResult? {
        guard phase == .enemyTurn, enemyImpactPending else { return nil }
        enemyImpactPending = false
        var incoming = 4
        let absorbed = min(shield, incoming)
        shield -= absorbed
        incoming -= absorbed
        playerHP = max(0, playerHP - incoming)
        if playerHP == 0 { phase = .defeat }
        return MeadowBattleActionResult(cue: .enemyStrike, damage: incoming, healed: 0, shieldGained: 0)
    }

    mutating func completeEnemyTurn() {
        guard phase == .enemyTurn, !enemyImpactPending else { return }
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
        pendingAction = nil
        enemyImpactPending = false
    }

    mutating func retry() { returnToMap(); begin() }

    var isEncounterActive: Bool { phase != .exploration }
    var isPlayerActionEnabled: Bool { phase == .playerTurn && actionPoints > 0 && pendingAction == nil }
}

/// The production display loop and pure Swift checks use the same one-shot gate.
struct MeadowBattleImpactClock {
    var elapsed: Double = 0
    let duration: Double
    let impactTime: Double?
    private(set) var fired = false
    mutating func advance(_ delta: Double) -> Bool {
        elapsed = min(duration, elapsed + max(0, delta))
        guard !fired, let impactTime, elapsed + 1e-9 >= impactTime else { return false }
        fired = true
        return true
    }
    static let anticipation = 0.4
    static let strikeContact = 1.048
    static let strikeDuration = 1.68
    static func strikePoseTime(_ elapsed: Double) -> Double {
        let action = max(0, elapsed - anticipation)
        return max(0, action - min(0.08, max(0, action - 0.648)))
    }
}
