#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT

swiftc -O \
  "$repo_root/scripts/road-motion-regression.swift" \
  "$repo_root/Sources/Game/WalkCycle.swift" \
  "$repo_root/Sources/Game/Trail.swift" \
  "$repo_root/Sources/Game/TrailNetwork.swift" \
  "$repo_root/Sources/Game/JourneySimulation.swift" \
  -o "$build_dir/road-motion-regression"

"$build_dir/road-motion-regression" "$repo_root"
