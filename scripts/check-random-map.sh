#!/usr/bin/env bash
set -euo pipefail
map_root="$(cd "$(dirname "$0")/.." && pwd)"
map_output="${1:-$map_root/Art/Review/Map/random-map-v3/data}"
mkdir -p "$map_output"
map_output="$(cd "$map_output" && pwd)"
map_swift="${MEADOW_SWIFT:-swift}"
map_swiftc="$(dirname "$(command -v "$map_swift")")/swiftc"
map_build="$(mktemp -d)"
trap 'rm -rf "$map_build"' EXIT
"$map_swift" build --package-path "$map_root/Vendor/ClassroomGameCore" --scratch-path "$map_build/package" --product MeadowMapExport
map_bin="$("$map_swift" build --package-path "$map_root/Vendor/ClassroomGameCore" --scratch-path "$map_build/package" --show-bin-path)"
"$map_swiftc" -O -I "$map_bin/Modules" \
  "$map_root/Sources/Game/SceneDefinition.swift" "$map_root/Sources/Game/Trail.swift" \
  "$map_root/Sources/Game/TrailNetwork.swift" "$map_root/Sources/Game/WalkCycle.swift" \
  "$map_root/Sources/Game/JourneySimulation.swift" "$map_root/scripts/random-map-adapter-check.swift" \
  "$map_bin/MeadowWorldSupport.build/"*.o "$map_bin/ClassroomGameCore.build/"*.o \
  -o "$map_build/check"
"$map_build/check" "$map_output" "$map_root"
