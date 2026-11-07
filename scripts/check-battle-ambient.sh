#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
swiftc -O "$repo_root/scripts/battle-ambient-regression.swift" "$repo_root/Sources/Game/MeadowSkillAmbientLight.swift" -o "$build_dir/battle-ambient"
"$build_dir/battle-ambient"
