#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
check_dir="$(mktemp -d)"
trap 'rm -rf "$check_dir"' EXIT
swiftc "$repo_root/Sources/Game/MeadowBattleEncounter.swift" "$repo_root/scripts/battle-effects-regression.swift" -o "$check_dir/check"
"$check_dir/check" "${1:-$check_dir/trace.json}"
