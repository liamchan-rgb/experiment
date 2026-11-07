#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
swiftc -O "$repo_root/scripts/battle-hitfeel-regression.swift" "$repo_root/Sources/Game/MeadowBattleHitFeel.swift" -o "$build_dir/battle-hitfeel"
"$build_dir/battle-hitfeel" "$repo_root/scripts/battle-hitfeel/golden.json"
