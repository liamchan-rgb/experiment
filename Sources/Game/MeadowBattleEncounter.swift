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
    let shieldAbsorbed: Int
    init(cue: MeadowBattleAnimationCue, damage: Int, healed: Int, shieldGained: Int, shieldAbsorbed: Int = 0) {
        self.cue = cue; self.damage = damage; self.healed = healed
        self.shieldGained = shieldGained; self.shieldAbsorbed = shieldAbsorbed
    }
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
        return MeadowBattleActionResult(cue: .enemyStrike, damage: incoming, healed: 0, shieldGained: 0, shieldAbsorbed: absorbed)
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
    static let strikeDuration = 1.70
    static func strikePoseTime(_ elapsed: Double) -> Double {
        let action = max(0, elapsed - anticipation)
        return max(0, action - min(0.10, max(0, action - 0.648)))
    }
}

/// Deterministic, presentation-only light debris. Positive Y points down.
/// Analytic flights keep floor contacts identical at every render cadence.
enum MeadowBattleLightKind: String, CaseIterable {
    case strike, death, shieldContact, shieldBreak
}

struct MeadowBattleLightEmission {
    let kind: MeadowBattleLightKind
    let startedAt: Double
    let x: Double
    let y: Double
    let groundY: Double
}

struct MeadowBattleLightParticle {
    let id: Int
    let x: Double
    let y: Double
    let angle: Double
    let size: Double
    let alpha: Double
    let cyan: Bool
    let groundX: Double
    let groundY: Double
    let groundAge: Double?
    let bounces: Int
}

enum MeadowBattleLightField {
    static func sample(_ kind: MeadowBattleLightKind, age: Double,
                       originX: Double, originY: Double, groundY: Double) -> [MeadowBattleLightParticle] {
        guard age >= 0, age < 3 else { return [] }
        let count: Int
        switch kind {
        case .strike: count = 34
        case .death: count = 52
        case .shieldContact: count = 12
        case .shieldBreak: count = 32
        }
        func fraction(_ i: Int, _ salt: Int) -> Double { Double((i * 73 + salt * 37) % 101) / 100 }
        return (0..<count).compactMap { i in
            let cyan = kind == .shieldContact || kind == .shieldBreak
            let birth = kind == .death && i != 0 ? fraction(i, 2) * 0.65 : 0
            let localAge = age - birth
            let life = (kind == .death ? 1.45 : cyan ? 1.08 : 1.22) + fraction(i, 5) * 0.4
            guard localAge >= 0, localAge < life else { return nil }
            let floor = groundY + Double(i % 5 - 2) * 2.5
            let spread = fraction(i, 3)
            var x = originX, y = originY
            var vx: Double, vy: Double
            if kind == .death {
                x += (spread - 0.25) * 120
                y += (fraction(i, 7) - 0.5) * 105
                vx = 75 + fraction(i, 11) * 105
                vy = -60 - fraction(i, 13) * 120
            } else if kind == .shieldBreak {
                let a = Double(i) * 2.399
                x += cos(a) * 63; y += sin(a) * 63
                vx = cos(a) * (55 + spread * 60)
                vy = sin(a) * 65 - 95
            } else {
                let a = Double(i) * 2.399
                vx = (kind == .shieldContact ? 45 : 20) + cos(a) * (85 + spread * 95)
                vy = -80 - fraction(i, 13) * 170
            }
            y = min(y, floor - 2)
            let gravity = 340.0
            var remaining = localAge, contacts = 0
            var lastContactAge: Double?, lastContactX = x
            // At most two rebounds. After the second landing debris settles.
            for bounce in 0..<3 {
                let flight = (-vy + sqrt(vy * vy + 2 * gravity * (floor - y))) / gravity
                if remaining < flight {
                    x += vx * remaining
                    y += vy * remaining + gravity * remaining * remaining / 2
                    vy += gravity * remaining
                    if let elapsed = lastContactAge { lastContactAge = elapsed + remaining }
                    break
                }
                x += vx * flight; y = floor
                remaining -= flight; contacts += 1
                lastContactX = x; lastContactAge = remaining
                if bounce == 2 { break }
                vx *= 0.62; vy = -(vy + gravity * flight) * 0.32
                // The next arc starts on the plane and rises before falling.
                if remaining == 0 { break }
                lastContactAge = 0
            }
            let fade = pow(max(0, 1 - localAge / life), 0.65)
            return MeadowBattleLightParticle(id: i, x: x, y: min(y, floor),
                angle: atan2(vy, vx) + (cyan ? localAge * (3 + spread * 5) : 0),
                size: (cyan ? 8 : 6) + fraction(i, 17) * (cyan ? 10 : 7),
                alpha: fade, cyan: cyan, groundX: lastContactX, groundY: floor,
                groundAge: contacts > 0 ? lastContactAge : nil, bounces: contacts)
        }
    }
}
