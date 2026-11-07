#!/usr/bin/env python3
"""Verify the user healing deliveries, sprite atlases and app asset catalogs."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageChops
import json

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "Art/Parts/BattleVFX/healing-v1/source-packs"
CATALOG = ROOT / "Sources/Resources/Assets.xcassets"
SPECS = [
    ("3-healing_micro_delivery.zip", "healing_micro", "healing_micro_spritesheet_5x4.png", "BattleVFXHealingMicroSheet", 280, None),
    ("1-healing_standard_pack.zip", "healing_standard", "healing_standard_spritesheet.png", "BattleVFXHealingStandardSheet", 614, 512),
    ("2-healing_strong_assets.zip", "healing_strong", "healing_strong_sheet_5x4.png", "BattleVFXHealingStrongSheet", 512, None),
]


def rgba(image, where):
    assert image.mode == "RGBA", f"{where}: expected RGBA, got {image.mode}"
    return image


def same_pixels(a, b, where):
    assert a.size == b.size and a.mode == b.mode, f"{where}: size/mode mismatch {a.size}/{a.mode} != {b.size}/{b.mode}"
    assert ImageChops.difference(a, b).getbbox() is None, f"{where}: pixel mismatch"


# The catalog sheets are now hand-built pixel art (scripts/battle-vfx/heal.py), no longer the delivered packs: check their
# structure (size, 20 frames, a visible effect in the middle, a faint ending) instead of comparing with the packs.
PIXEL_ART = {"BattleVFXHealingMicroSheet": (320, 320), "BattleVFXHealingStandardSheet": (320, 268), "BattleVFXHealingStrongSheet": (320, 320)}


def verify_pixel_art(asset_name, cell_w, cell_h):
    path = CATALOG / f"{asset_name}.imageset" / f"{asset_name}.png"
    sheet = rgba(Image.open(path), str(path))
    assert sheet.size == (cell_w * 5, cell_h * 4), f"{asset_name}: unexpected atlas size {sheet.size}"
    covered = []
    for index in range(20):
        x, y = (index % 5) * cell_w, (index // 5) * cell_h
        alpha = sheet.crop((x, y, x + cell_w, y + cell_h)).getchannel("A")
        covered.append(sum(1 for v in alpha.tobytes() if v > 0))
    assert max(covered) > 1500, f"{asset_name}: effect is not visible in any frame"
    assert covered[19] < max(covered) * 0.25, f"{asset_name}: ending frame should be faint"
    print(f"PASS {asset_name}: hand-built pixel art, 20 frames of {cell_w}x{cell_h}, 5x4 atlas, peak coverage {max(covered)} px, ending {covered[19]} px")


def main():
    for zip_name, prefix, sheet_name, asset_name, cell_w, cell_h in SPECS:
        if asset_name in PIXEL_ART:
            verify_pixel_art(asset_name, *PIXEL_ART[asset_name])
            continue
        archive = PACKS / zip_name
        assert archive.is_file(), f"missing source pack: {archive}"
        with ZipFile(archive) as z:
            bad = z.testzip()
            assert bad is None, f"{zip_name}: corrupt entry {bad}"
            names = set(z.namelist())
            sheet = rgba(Image.open(z.open(sheet_name)), f"{zip_name}:{sheet_name}")
            if prefix == "healing_standard":
                meta = json.loads(z.read("manifest.json"))
                assert meta["frame_count"] == 20 and meta["frame_size"] == {"width": 614, "height": 512}
                assert meta["spritesheet"]["order"] == "row-major"
                rows, cols, cell_h = 4, 5, 512
            elif prefix == "healing_strong":
                meta = json.loads(z.read("manifest.json"))
                assert meta["frame_count"] == 20 and meta["frame_width"] == 512 and meta["frame_height"] == 512
                assert meta["spritesheet"]["order"].startswith("row-major")
                rows, cols, cell_h = 4, 5, 512
            else:
                rows, cols, cell_h = 4, 5, 280
            assert sheet.size == (cell_w * cols, cell_h * rows), f"{zip_name}: unexpected atlas size {sheet.size}"
            app_path = CATALOG / f"{asset_name}.imageset" / f"{asset_name}.png"
            app_sheet = rgba(Image.open(app_path), str(app_path))
            same_pixels(sheet, app_sheet, f"{zip_name} -> {app_path}")
            for index in range(20):
                frame_name = f"frames/{prefix}_{index+1:02}.png"
                assert frame_name in names, f"{zip_name}: missing {frame_name}"
                frame = rgba(Image.open(z.open(frame_name)), frame_name)
                assert frame.size == (cell_w, cell_h), f"{frame_name}: unexpected size {frame.size}"
                x, y = (index % cols) * cell_w, (index // cols) * cell_h
                same_pixels(frame, sheet.crop((x, y, x + cell_w, y + cell_h)), frame_name)
            last = rgba(Image.open(z.open(f"frames/{prefix}_20.png")), f"{prefix} frame20")
            assert last.getchannel("A").getextrema()[1] <= (1 if prefix == "healing_strong" else 0), f"{prefix}: ending frame should be transparent/faint"
            print(f"PASS {prefix}: 20 RGBA frames, {cell_w}x{cell_h}, 5x4 atlas, app pixels match source; ending alpha <= {last.getchannel('A').getextrema()[1]}")


if __name__ == "__main__":
    main()
