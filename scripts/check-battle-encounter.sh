#!/bin/sh
set -eu
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
cat > "$tmp_dir/BattleEncounterCheck.swift" <<'SWIFT'
import Foundation

@main
struct BattleEncounterCheck {
    static func main() {
        var encounter = MeadowBattleEncounter()
        precondition(encounter.phase == .exploration)
        encounter.begin()
        precondition(encounter.phase == .playerTurn && encounter.round == 1 && encounter.actionPoints == 3)
        precondition(encounter.perform(.strike) == nil) // A target must be selected.
        encounter.selectEnemy()
        for _ in 0..<3 { precondition(encounter.perform(.strike) != nil) }
        precondition(encounter.enemyHP == 3 && encounter.phase == .playerTurn && encounter.actionPoints == 0)
        precondition(encounter.perform(.strike) == nil) // No fourth action with zero AP.
        encounter.endPlayerTurn()
        precondition(!encounter.enemySelected)
        encounter.selectEnemy()
        precondition(!encounter.enemySelected) // Target cannot be changed in enemy preparation.
        precondition(encounter.resolveEnemyAction()?.damage == 4)
        let hpAfterEnemyAction = encounter.playerHP
        precondition(encounter.resolveEnemyAction() == nil)
        precondition(encounter.playerHP == hpAfterEnemyAction) // Resolution cannot hit twice.
        precondition(encounter.playerHP == 8 && encounter.phase == .enemyTurn)
        encounter.completeEnemyTurn()
        precondition(encounter.round == 2 && encounter.actionPoints == 3)
        encounter.selectEnemy()
        precondition(encounter.perform(.strike)?.damage == 3)
        precondition(encounter.enemyHP == 0 && encounter.phase == .victory)
        let victoryAP = encounter.actionPoints
        precondition(encounter.perform(.strike) == nil)
        precondition(encounter.actionPoints == victoryAP) // Victory rejects further actions.
        encounter.selectEnemy()
        precondition(encounter.enemySelected) // Target cannot be changed after victory.
        encounter.retry()
        precondition(encounter.phase == .playerTurn && encounter.playerHP == 12 && encounter.enemyHP == 18)

        var armored=MeadowBattleEncounter(maximumHealth:20)
        armored.begin();precondition(armored.playerMaxHP==20 && armored.playerHP==20)
        armored.endPlayerTurn();_ = armored.resolveEnemyAction();armored.completeEnemyTurn()
        precondition(armored.playerHP==16 && armored.perform(.breathe)?.healed==4 && armored.playerHP==20)
        armored.retry();precondition(armored.playerHP==20 && armored.playerMaxHP==20)
        var healing = MeadowBattleEncounter()
        healing.begin()
        let fullHealthAP = healing.actionPoints
        precondition(healing.perform(.breathe) == nil)
        precondition(healing.actionPoints == fullHealthAP && healing.breathUses == 2)

        var defense = MeadowBattleEncounter()
        defense.begin()
        defense.selectEnemy()
        precondition(defense.enemySelected) // Target selection is allowed during the player turn.
        precondition(defense.perform(.protection)?.shieldGained == 4)
        precondition(defense.perform(.protection)?.shieldGained == 4)
        precondition(defense.guardUses == 0 && defense.shield == 8)
        defense.endPlayerTurn()
        defense.selectEnemy()
        precondition(!defense.enemySelected) // Selection is locked during enemy turn.
        precondition(defense.resolveEnemyAction()?.damage == 0)
        defense.selectEnemy()
        precondition(!defense.enemySelected) // Selection remains locked during enemy action.
        precondition(defense.shield == 4 && defense.playerHP == 12)
        defense.completeEnemyTurn()
        defense.endPlayerTurn()
        precondition(defense.resolveEnemyAction()?.damage == 0)
        precondition(defense.shield == 0 && defense.playerHP == 12)
        defense.completeEnemyTurn()
        defense.endPlayerTurn()
        precondition(defense.resolveEnemyAction()?.damage == 4)
        precondition(defense.playerHP == 8)
        defense.completeEnemyTurn()
        precondition(defense.perform(.breathe)?.healed == 4)
        precondition(defense.playerHP == 12 && defense.breathUses == 1)
        let apAfterHeal = defense.actionPoints
        precondition(defense.perform(.breathe) == nil)
        precondition(defense.actionPoints == apAfterHeal && defense.breathUses == 1)

        var defeat = MeadowBattleEncounter()
        defeat.begin()
        for _ in 0..<3 {
            defeat.endPlayerTurn()
            _ = defeat.resolveEnemyAction()
            if defeat.phase == .defeat { break }
            defeat.completeEnemyTurn()
        }
        precondition(defeat.phase == .defeat && defeat.playerHP == 0)
        defeat.returnToMap()
        precondition(defeat.phase == .exploration && defeat.round == 0 && defeat.actionPoints == 0)
        print("MeadowBattleEncounter checks passed: target/AP, victory across rounds, shield/heal uses, defeat, retry and map return.")
    }
}
SWIFT
swiftc "$repo_root/Sources/Game/MeadowBattleEncounter.swift" "$tmp_dir/BattleEncounterCheck.swift" -o "$tmp_dir/check-battle-encounter"
"$tmp_dir/check-battle-encounter"
