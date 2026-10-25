#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
swiftc -O "$repo_root/scripts/modular-locomotion-regression.swift" \
  "$repo_root/Sources/Game/WalkCycle.swift" \
  "$repo_root/Sources/Game/Trail.swift" \
  "$repo_root/Sources/Game/TrailNetwork.swift" \
  "$repo_root/Sources/Game/JourneySimulation.swift" -o "$build_dir/modular-locomotion"
"$build_dir/modular-locomotion" "$repo_root" "${1:-$repo_root/build/modular-locomotion-trace.json}"
