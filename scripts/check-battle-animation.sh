#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
check_dir="$(mktemp -d)"
trap 'rm -rf "$check_dir"' EXIT
# Compile the production pose sampler, with only the UIKit data-asset loader
# replaced by a Foundation filesystem adapter. No app or simulator is started.
python3 - "$repo_root" "$check_dir" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]);out=Path(sys.argv[2]);source=(root/'Sources/Game/MeadowBattleActorView.swift').read_text()
source=source[:source.index('/// A single registered pose')].replace('import UIKit','import Foundation\nimport CoreGraphics',1)
adapter='''
final class NSDataAsset {
    let data: Data
    init?(name: String) {
        let base = URL(fileURLWithPath: CommandLine.arguments[1])
            .appendingPathComponent("Sources/Resources/Assets.xcassets/\\(name).dataset")
        guard let manifest = try? Data(contentsOf: base.appendingPathComponent("Contents.json")),
              let json = try? JSONSerialization.jsonObject(with: manifest) as? [String: Any],
              let entries = json["data"] as? [[String: Any]],
              let filename = entries.first?["filename"] as? String,
              let bytes = try? Data(contentsOf: base.appendingPathComponent(filename)) else { return nil }
        data = bytes
    }
}
'''
(out/'ProductionPose.swift').write_text(source+'\n'+adapter)
PY
cat > "$check_dir/PoseCheck.swift" <<'SWIFT'
import Foundation
import CoreGraphics
@main
struct PoseCheck {
    static func main() {
        func same(_ a: MeadowBattleLayerPose, _ b: MeadowBattleLayerPose) -> Bool {
            a.offset == b.offset && a.pivot == b.pivot && a.rotation == b.rotation && a.scale == b.scale
        }
        for clip in MeadowBattleAnimation.clips {
            precondition(MeadowBattleAnimation.durationMs(for: clip) > 0)
            for index in 0...120 {
                let pose = MeadowBattleAnimation.sample(clip: clip, progress: CGFloat(index) / 120)
                precondition(pose.rootOffset.x.isFinite && pose.rootOffset.y.isFinite)
                precondition(pose.contacts.count > 0 && pose.contacts.count <= 2)
                precondition(pose.contacts.allSatisfy { abs($0.y - pose.footAnchorPx.y) <= 1.01 })
                precondition(abs(pose.footAnchorPx.y + pose.rootOffset.y - 214) <= 6.01)
                precondition(same(pose.layers["MeadowBattleHeroHair"]!, pose.layers["MeadowBattleHeroFace"]!))
                precondition(same(pose.layers["MeadowBattleHeroHair"]!, pose.layers["MeadowBattleHeroBodyCore"]!))
                precondition(same(pose.layers["MeadowBattleHeroWeapon"]!, pose.layers["MeadowBattleHeroNearHand"]!))
            }
        }
        precondition(MeadowBattleAnimation.sample(clip: "attack", progress: -1).progress == 0)
        precondition(MeadowBattleAnimation.sample(clip: "attack", progress: 2).progress == 1)
        print("Battle pose checks passed: real JSON sampler, support plane, at most two planted contacts, head/face registration and weapon grip across six clips.")
    }
}
SWIFT
swiftc "$check_dir/ProductionPose.swift" "$check_dir/PoseCheck.swift" -o "$check_dir/pose-check"
"$check_dir/pose-check" "$repo_root"
