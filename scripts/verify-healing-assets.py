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


def main():
    for zip_name, prefix, sheet_name, asset_name, cell_w, cell_h in SPECS:
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
