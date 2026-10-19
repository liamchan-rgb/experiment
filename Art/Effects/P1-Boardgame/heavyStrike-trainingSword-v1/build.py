#!/usr/bin/env python3
"""Render and package the editable heavy-strike SVG master to the boardgame FX contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "source"
MASTER = SOURCE_DIR / "fx_heavyStrike.svg"
CONCEPT = SOURCE_DIR / "concepts" / "generated-heavy-strike.png"
FRAMES_DIR = ROOT / "frames"
OUTPUTS_DIR = ROOT / "outputs"
SHEET_PATH = OUTPUTS_DIR / "fx_heavyStrike_sheet.png"
REVIEW_PATH = OUTPUTS_DIR / "review.png"
GIF_PATH = OUTPUTS_DIR / "preview-normal.gif"
RENDER_PATH = OUTPUTS_DIR / ".rendered-master.png"

CELL = 256
DURATIONS_MS = [50, 70, 80, 80, 100, 100, 80, 90]
FRAME_NAMES = [
    "glint",
    "slash-enter",
    "slash-full",
    "impact-small",
    "impact-peak",
    "fragments",
    "embers",
    "transparent-end",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checker(size: tuple[int, int], tile: int = 16) -> Image.Image:
    out = Image.new("RGB", size, (32, 39, 51))
    draw = ImageDraw.Draw(out)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle((x, y, min(x + tile - 1, size[0] - 1), min(y + tile - 1, size[1] - 1)), fill=(43, 51, 65))
    return out


def main() -> None:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ["inkscape", str(MASTER), f"--export-filename={RENDER_PATH}", "--export-width=2048", "--export-height=256"],
        check=True,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
    )
    rendered = Image.open(RENDER_PATH).convert("RGBA")
    if rendered.size != (2048, 256):
        raise ValueError(f"unexpected rendered master size: {rendered.size}")

    frames: list[Image.Image] = []
    records: list[dict] = []
    for index, name in enumerate(FRAME_NAMES):
        cell = rendered.crop((index * CELL, 0, (index + 1) * CELL, CELL))
        frame_path = FRAMES_DIR / f"{index:02d}-{name}.png"
        cell.save(frame_path, optimize=False)
        frames.append(cell)
        bounds = cell.getchannel("A").getbbox()
        records.append({
            "index": index,
            "name": name,
            "sourceCellLTRB": [index * CELL, 0, (index + 1) * CELL, CELL],
            "durationMs": DURATIONS_MS[index],
            "sizePx": [CELL, CELL],
            "hitAnchorPx": [CELL // 2, CELL // 2],
            "effectBoundsInCell": list(bounds) if bounds else None,
            "transparent": bounds is None,
            "sha256": sha256(frame_path),
        })

    rendered.save(SHEET_PATH, optimize=False)

    # Review-only contact sheet. The checker and labels are never packed into runtime frames.
    cell_review_height = CELL + 25
    review = Image.new("RGB", (CELL * 4, cell_review_height * 2), (24, 30, 40))
    draw = ImageDraw.Draw(review)
    font = ImageFont.load_default()
    labels = ["01 GLINT", "02 SLASH IN", "03 SLASH", "04 FLASH", "05 IMPACT", "06 FRAGMENTS", "07 EMBERS", "08 CLEAR"]
    for index, frame in enumerate(frames):
        col, row = index % 4, index // 4
        x, y = col * CELL, row * cell_review_height
        tile = checker((CELL, CELL))
        tile.paste(frame, (0, 0), frame)
        review.paste(tile, (x, y))
        draw.rectangle((x, y + CELL, x + CELL - 1, y + cell_review_height - 1), fill=(24, 30, 40))
        draw.text((x + 7, y + CELL + 6), labels[index], font=font, fill=(230, 236, 246))
    review.save(REVIEW_PATH, optimize=False)

    # One-shot normal-speed preview with a checkerboard; only the underlying sheet is transparent.
    gif_frames = []
    for frame in frames:
        canvas = checker((CELL, CELL)).convert("RGBA")
        canvas.alpha_composite(frame)
        gif_frames.append(canvas.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    gif_frames[0].save(
        GIF_PATH,
        save_all=True,
        append_images=gif_frames[1:],
        duration=DURATIONS_MS,
        disposal=2,
        optimize=False,
    )

    manifest = {
        "formatVersion": 1,
        "assetID": "heavyStrike-trainingSword-v1",
        "status": "prototype-awaiting-art-review",
        "skillID": "heavyStrike",
        "equipmentID": "trainingSword",
        "effectID": "heavyStrike",
        "visualRole": "one-shot slash and impact overlay after a committed game result",
        "sourceContract": {
            "repository": "classroom-boardgame",
            "gameContentCommit": "1e9100c4c18364ea64b3ec974fe957ba4ef42f6f",
            "gameContentSHA256": "aaab980fd5f3154ac813a02dc907a835ee0e0181c4149f2b7803d9594795f34a",
            "designArchiveTag": "archive-design-b-art-motion-v1-20261012",
            "designArchiveCommit": "bc2049fb579ef488470a8a2a75a0c078eb492c22",
            "effectTemplate": "impact",
            "effectFrames": 8,
            "frameSizePx": [CELL, CELL],
            "durationMs": sum(DURATIONS_MS),
            "loop": False,
            "playsPerCommittedResult": 1,
            "terminalFrameTransparent": True,
            "reducedMotion": {"frameIndex": 4, "description": "brief static peak glyph, then clear"},
        },
        "sourceImage": {
            "path": "source/fx_heavyStrike.svg",
            "sourceType": "original-editable-vector",
            "sha256": sha256(MASTER),
        },
        "conceptStudy": {
            "path": "source/concepts/generated-heavy-strike.png",
            "sha256": sha256(CONCEPT),
            "use": "initial direction study only; retained for provenance and not used in production outputs",
        },
        "outputs": {
            "spriteSheet": "outputs/fx_heavyStrike_sheet.png",
            "reviewContactSheet": "outputs/review.png",
            "normalSpeedPreview": "outputs/preview-normal.gif",
            "frameDirectory": "frames/",
            "spriteSheetSizePx": [2048, 256],
        },
        "palette": {"impactRed": "#B93838", "ivory": "#FFF3CD", "skyAccent": "#B2DDEF"},
        "limitations": [
            "Effect-only animation; it does not contain the character, arm, hand, weapon, or a frame-by-frame swing pose.",
            "No rules, dice, damage values, game content, or App code were changed.",
            "The equipment ID selects the associated item reference; it does not alter this generic visual effect.",
            "Not yet integrated into the reusable character template or game runtime.",
        ],
        "frames": records,
    }
    (ROOT / "asset-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with Image.open(GIF_PATH) as gif:
        gif_frame_count = gif.n_frames
        gif_durations = []
        for index in range(gif.n_frames):
            gif.seek(index)
            gif_durations.append(gif.info.get("duration", 0))
        has_loop_extension = "loop" in gif.info

    terminal_alpha = np.asarray(frames[-1].getchannel("A"))
    checks = {
        "status": "passed",
        "masterSVG": {"path": "source/fx_heavyStrike.svg", "sha256": sha256(MASTER)},
        "conceptStudySHA256": sha256(CONCEPT),
        "sheetSizePx": list(rendered.size),
        "frameCount": len(frames),
        "frameSizePx": [CELL, CELL],
        "durationMs": sum(DURATIONS_MS),
        "durationSequenceMs": DURATIONS_MS,
        "terminalFrameAlphaPixels": int(np.count_nonzero(terminal_alpha)),
        "gifFrameCount": gif_frame_count,
        "gifDurationsMs": gif_durations,
        "gifLoopExtensionPresent": has_loop_extension,
        "sha256": {
            "spriteSheet": sha256(SHEET_PATH),
            "reviewContactSheet": sha256(REVIEW_PATH),
            "normalSpeedPreview": sha256(GIF_PATH),
        },
    }
    if rendered.size != (2048, 256) or len(frames) != 8 or np.any(terminal_alpha):
        raise AssertionError("sprite-sheet contract failed")
    if gif_frame_count != 8 or gif_durations != DURATIONS_MS or has_loop_extension:
        raise AssertionError("one-shot preview GIF contract failed")
    (ROOT / "validation.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RENDER_PATH.unlink()
    print(json.dumps({
        "sheet": list(rendered.size),
        "frames": len(frames),
        "durationMs": sum(DURATIONS_MS),
        "gifFrames": gif_frame_count,
        "loop": has_loop_extension,
        "sheetSHA256": checks["sha256"]["spriteSheet"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
