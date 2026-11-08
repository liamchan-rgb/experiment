#!/usr/bin/env python3
"""Verify preserved deliveries, exact frame extraction and Xcode runtime sheets."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Art/Parts/BattleVFX/skill-effects-v1/manifest.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    total = 0
    for spec in manifest["sourceArchives"]:
        assert 0 <= spec["peak_frame"] < spec["count"], f"Bad peak frame: {spec['skill']}"
        assert 0 <= spec["anchor_x"] <= spec["width"] and 0 <= spec["anchor_y"] <= spec["height"], f"Bad pivot: {spec['skill']}"
        assert spec["fps"] > 0, f"Bad playback rate: {spec['skill']}"
        art = ROOT / "Art/Parts/BattleVFX" / spec["directory"]
        source = art / "source-packs" / spec["zip"]
        sheet = art / spec["sheet"]
        assert sha(source) == spec["archive_sha256"], f"Source archive changed: {source}"
        assert sha(sheet) == spec["runtime_sha256"], f"Art sheet changed: {sheet}"
        runtime = ROOT / "Sources/Resources/Assets.xcassets" / f"{spec['asset']}.imageset"
        runtime_png = runtime / f"{spec['asset']}.png"
        assert sha(runtime_png) == spec["runtime_sha256"], f"Runtime sheet differs: {runtime_png}"
        assert (runtime / "Contents.json").is_file(), f"Missing image catalog: {runtime}"

        image = Image.open(sheet).convert("RGBA")
        assert image.size == (spec["width"] * spec["columns"], spec["height"] * spec["rows"]), spec["directory"]
        assert len(spec["frame_sha256"]) == spec["count"]
        with zipfile.ZipFile(source) as archive:
            for index in range(spec["count"]):
                n = index + 1 if spec["directory"] == "dragon-scale-ward-v1" else index
                pattern = spec["frame_pattern"]
                member = f"{spec['pack_root'] + '/' if spec['pack_root'] else ''}{pattern.format(n)}"
                frame_bytes = archive.read(member)
                archived_hash = hashlib.sha256(frame_bytes).hexdigest()
                assert archived_hash == spec["frame_sha256"][index], f"Source frame hash changed: {member}"
                copied = art / "frames" / PurePosixPath(member).name
                assert copied.read_bytes() == frame_bytes, f"Copied frame differs: {copied}"
                frame = Image.open(copied).convert("RGBA")
                assert frame.size == (spec["width"], spec["height"]), f"Wrong frame size: {copied}"
                x = (index % spec["columns"]) * spec["width"]
                y = (index // spec["columns"]) * spec["height"]
                crop = image.crop((x, y, x + spec["width"], y + spec["height"]))
                assert crop.getchannel("A").tobytes() == frame.getchannel("A").tobytes(), f"Sprite-sheet alpha differs at {member}"
                # Some transparent cells intentionally retain arbitrary hidden RGB.
                # Compare visible RGBA exactly while ignoring only RGB where alpha is zero.
                mask = crop.getchannel("A").point(lambda a: 255 if a else 0)
                empty = Image.new("RGBA", crop.size, (0, 0, 0, 0))
                visible_crop = Image.composite(crop, empty, mask)
                visible_frame = Image.composite(frame, empty, mask)
                assert visible_crop.tobytes() == visible_frame.tobytes(), f"Sprite-sheet pixels differ at {member}"
        total += spec["count"]
        print(f"PASS {spec['skill']}: {spec['count']} {spec['width']}x{spec['height']} RGBA frames, {spec['fps']} FPS")
    assert total == 100
    assert manifest["authoredMotionAdded"] is False
    assert "support effects begin on the receipt" in manifest["trigger"]
    print(f"PASS {len(manifest['sourceArchives'])} preserved packs, {total} exact runtime frames")


if __name__ == "__main__":
    main()
