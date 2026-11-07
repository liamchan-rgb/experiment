#!/usr/bin/env python3
"""Verify the delivered Dragon Flame frames, transparent sheet, and app catalog copies."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Art/Parts/BattleVFX/dragon-flame-v2"
ASSETS = ROOT / "Sources/Resources/Assets.xcassets"
SHEET_PATH = SOURCE / "dragon_flame_spritesheet.png"
SHEET = Image.open(SHEET_PATH).convert("RGBA")
assert SHEET.size == (1400, 1120), f"unexpected sheet size: {SHEET.size}"
manifest = json.loads((SOURCE / "frame-manifest.json").read_text())
assert manifest["grid"] == [5, 4] and manifest["frameCount"] == 20
assert manifest["spriteSheetSize"] == [1400, 1120]

rows = []
for index in range(20):
    filename = f"dragon_flame_{index + 1:02}.png"
    source_path = SOURCE / "frames" / filename
    delivered = Image.open(source_path)
    assert delivered.mode == "RGBA" and delivered.size == (280, 280), (filename, delivered.mode, delivered.size)
    col, row = index % 5, index // 5
    crop = SHEET.crop((col * 280, row * 280, (col + 1) * 280, (row + 1) * 280))
    assert crop.tobytes() == delivered.tobytes(), f"spritesheet cell mismatch: {filename}"
    image_name = f"MeadowDragonFlame{index + 1:02}"
    image_set = ASSETS / f"{image_name}.imageset"
    contents = json.loads((image_set / "Contents.json").read_text())
    assert contents["images"][0]["filename"] == f"{image_name}.png"
    app_image = Image.open(image_set / f"{image_name}.png").convert("RGBA")
    assert app_image.size == (280, 280) and app_image.tobytes() == delivered.tobytes(), f"asset catalog differs: {image_name}"
    sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    declared = manifest["frames"][index]
    assert declared["frame"] == index + 1 and declared["size"] == [280, 280]
    assert declared["sourceSheetCellMatches"] is True and declared["sha256"] == sha
    assert list(delivered.getchannel("A").getbbox() or ()) == declared["alphaBounds"]
    rows.append({"frame": index + 1, "sha256": sha, "alphaBounds": declared["alphaBounds"], "asset": image_name})

assert SHEET.getchannel("A").getbbox() is not None
print(json.dumps({"status": "ok", "source": str(SOURCE.relative_to(ROOT)), "sheet": [1400, 1120], "frameCount": 20, "frameSize": [280, 280], "rgba": True, "sourceAndAppFramesPixelIdentical": True, "frames": rows}, ensure_ascii=False, indent=2))
