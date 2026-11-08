#!/usr/bin/env bash
set -euo pipefail
campaign_root="$(cd "$(dirname "$0")/.." && pwd)"
campaign_output="${1:-$campaign_root/Art/Review/Map/campaign-v1/data}"
mkdir -p "$campaign_output"
campaign_output="$(cd "$campaign_output" && pwd)"
campaign_swift="${MEADOW_SWIFT:-swift}"
campaign_swiftc="$(dirname "$(command -v "$campaign_swift")")/swiftc"
campaign_build="$(mktemp -d)"
trap 'rm -rf "$campaign_build"' EXIT
"$campaign_swift" build --package-path "$campaign_root/Vendor/ClassroomGameCore" --scratch-path "$campaign_build/package" --target MeadowBattleSupport
"$campaign_swift" build --package-path "$campaign_root/Vendor/ClassroomGameCore" --scratch-path "$campaign_build/package" --target MeadowWorldSupport
campaign_bin="$("$campaign_swift" build --package-path "$campaign_root/Vendor/ClassroomGameCore" --scratch-path "$campaign_build/package" --show-bin-path)"
"$campaign_swiftc" -O -I "$campaign_bin/Modules" \
 "$campaign_root/Sources/Game/Trail.swift" "$campaign_root/Sources/Game/TrailNetwork.swift" \
 "$campaign_root/Sources/Game/SceneDefinition.swift" "$campaign_root/Sources/Game/JourneySimulation.swift" \
 "$campaign_root/Sources/Game/WalkCycle.swift" "$campaign_root/Sources/Game/MeadowBattleEncounter.swift" \
 "$campaign_root/scripts/export-campaign-review.swift" \
 "$campaign_bin/MeadowWorldSupport.build/"*.o "$campaign_bin/MeadowBattleSupport.build/"*.o \
 "$campaign_bin/ClassroomGameCore.build/"*.o -o "$campaign_build/export"
"$campaign_build/export" "$campaign_root" "$campaign_output"
