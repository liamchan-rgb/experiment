#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
swiftc -O "$repo_root/scripts/battle-procedural-regression.swift" "$repo_root/Sources/Game/MeadowSkillProcedural.swift" -o "$build_dir/battle-procedural"
"$build_dir/battle-procedural" "$repo_root/scripts/battle-vfx/procedural-golden.json"
swiftc -O "$repo_root/scripts/battle-number-regression.swift" "$repo_root/Sources/Game/MeadowBattleNumber.swift" -o "$build_dir/battle-number"
"$build_dir/battle-number"
