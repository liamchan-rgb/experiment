#!/usr/bin/env python3
"""Import the five supplied battle-skill VFX packs without altering their pixels."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
ATTACHMENTS = Path("/tmp/codex-remote-attachments/01a159c6-55ea-7311-9c81-a1f0cbd4b088/E9C1A059-C4BD-4BEB-B2D3-84DE14B58879")

PACKS = [
    {
        "zip": "1-starlight_pulse_delivery.zip", "directory": "starlight-pulse-v1",
        "pack_root": "starlight_pulse_delivery", "asset": "MeadowBattleVFXStarlightPulse",
        "sheet": "starlight_pulse_spritesheet.png", "frame_pattern": "frames/starlight_pulse_{:02d}.png",
        "count": 20, "columns": 5, "rows": 4, "width": 344, "height": 344,
        "archive_sheet": "starlight_pulse_spritesheet.png", "fps": 16,
        "anchor_x": 172, "anchor_y": 172, "peak_frame": 12,
        "skill": "starlightPulse", "motion": "ranged attack",
    },
    {
        "zip": "2-rally_delivery.zip", "directory": "rally-v1",
        "pack_root": "rally_delivery", "asset": "MeadowBattleVFXRally",
        "sheet": "rally_spritesheet.png", "frame_pattern": "frames/rally_{:03d}.png",
        "count": 20, "columns": 5, "rows": 4, "width": 256, "height": 256,
        "archive_sheet": "rally_spritesheet.png", "fps": 12,
        "anchor_x": 128, "anchor_y": 128, "peak_frame": 14,
        "skill": "rally", "motion": "existing support / guard",
    },
    {
        "zip": "3-sweep_delivery_bundle.zip", "directory": "sweep-v1",
        "pack_root": "sweep_delivery", "asset": "MeadowBattleVFXSweep",
        "sheet": "sweep_spritesheet.png", "frame_pattern": "frames/sweep_{:03d}.png",
        "count": 20, "columns": 5, "rows": 4, "width": 339, "height": 287,
        "archive_sheet": "sweep_spritesheet.png", "fps": 20,
        "anchor_x": 169.5, "anchor_y": 143.5, "peak_frame": 9,
        "skill": "sweep", "motion": "existing melee attack",
    },
    {
        "zip": "4-dragon_soul_ward_asset_pack.zip", "directory": "dragon-soul-ward-v1",
        "pack_root": "dragon_soul_ward_asset_pack", "asset": "MeadowBattleVFXDragonSoulWard",
        "sheet": "dragon_soul_ward_spritesheet.png", "frame_pattern": "frames/dragon_soul_ward_{:03d}.png",
        "count": 20, "columns": 5, "rows": 4, "width": 256, "height": 256,
        "archive_sheet": "dragon_soul_ward_spritesheet.png", "fps": 12,
        "anchor_x": 133, "anchor_y": 154, "peak_frame": 12,
        "skill": "dragonSoulWard", "motion": "existing support / guard",
    },
    {
        "zip": "5-dragon_scale_ward_delivery.zip", "directory": "dragon-scale-ward-v1",
        "pack_root": "", "asset": "MeadowBattleVFXDragonScaleWard",
        "sheet": "dragon_scale_ward_spritesheet.png", "frame_pattern": "dragon_scale_ward_{:02d}.png",
        "count": 20, "columns": 4, "rows": 5, "width": 256, "height": 256,
        "archive_sheet": "dragon_scale_ward_spritesheet.png", "fps": 20,
        "anchor_x": 128, "anchor_y": 128, "peak_frame": 12,
        "skill": "dragonScaleWard", "motion": "existing support / guard",
    },
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_member(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive member: {name}")


def main() -> None:
    for spec in PACKS:
        archive = ATTACHMENTS / spec["zip"]
        if not archive.is_file():
            raise FileNotFoundError(archive)
        target = ROOT / "Art/Parts/BattleVFX" / spec["directory"]
        source_dir = target / "source-packs"
        extracted = target / "delivery"
        source_dir.mkdir(parents=True, exist_ok=True)
        extracted.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archive, source_dir / archive.name)

        with zipfile.ZipFile(archive) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            for name in names:
                safe_member(name)
                member = PurePosixPath(name)
                if spec["pack_root"]:
                    prefix = spec["pack_root"] + "/"
                    if not name.startswith(prefix):
                        raise ValueError(f"Unexpected pack path {name} in {archive.name}")
                    relative = Path(*member.parts[1:])
                else:
                    relative = Path(*member.parts)
                destination = extracted / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(zf.read(name))

            sheet_source = f"{spec['pack_root'] + '/' if spec['pack_root'] else ''}{spec['archive_sheet']}"
            frames = []
            for i in range(spec["count"]):
                index = i + 1 if spec["directory"] == "dragon-scale-ward-v1" else i
                member = f"{spec['pack_root'] + '/' if spec['pack_root'] else ''}{spec['frame_pattern'].format(index)}"
                frames.append((member, zf.read(member)))
            sheet_bytes = zf.read(sheet_source)
            image_spec = spec["directory"]
            frame_dir = target / "frames"
            frame_dir.mkdir(exist_ok=True)
            for member, content in frames:
                relative = PurePosixPath(member)
                frame_dir.joinpath(relative.name).write_bytes(content)

        sheet_copy = target / spec["sheet"]
        sheet_copy.write_bytes(sheet_bytes)
        contents = {
            "images": [{"filename": f"{spec['asset']}.png", "idiom": "universal"}],
            "info": {"author": "xcode", "version": 1},
        }
        imageset = ROOT / "Sources/Resources/Assets.xcassets" / f"{spec['asset']}.imageset"
        imageset.mkdir(parents=True, exist_ok=True)
        (imageset / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")
        (imageset / f"{spec['asset']}.png").write_bytes(sheet_bytes)

        input_docs = sorted(p.name for p in (extracted).glob("*.md"))
        readme = [
            f"# {spec['skill']} VFX",
            "",
            f"Supplied archive: `{spec['zip']}` (SHA-256 `{digest(archive.read_bytes())}`).",
            f"Runtime source sheet: `{spec['sheet']}`; {spec['count']} frames at {spec['width']}×{spec['height']} px, {spec['columns']}×{spec['rows']} grid, {spec['fps']} FPS, one-shot.",
            f"Skill ID: `{spec['skill']}`. Existing action motion: {spec['motion']}; no new body animation is included.",
            "The original ZIP and unpacked delivery are preserved. Runtime sheets and individual frames are copied byte-for-byte.",
            "",
            "## Delivery notes",
            "",
        ] + [f"- `{name}`" for name in input_docs] + [
            "",
            "The app uses the corresponding sheet in `Sources/Resources/Assets.xcassets`; frame slicing and pixel identity are checked by `scripts/verify-skill-vfx-assets.py`.",
        ]
        (target / "README.md").write_text("\n".join(readme) + "\n")
        spec["archive_sha256"] = digest(archive.read_bytes())
        spec["runtime_sha256"] = digest(sheet_bytes)
        spec["frame_sha256"] = [digest(data) for _, data in frames]

    manifest = {
        "schemaVersion": 1,
        "sourceArchives": [
            {k: spec[k] for k in ("zip", "directory", "pack_root", "asset", "sheet", "frame_pattern", "skill", "count", "columns", "rows", "width", "height", "fps", "anchor_x", "anchor_y", "peak_frame", "motion", "archive_sha256", "runtime_sha256", "frame_sha256")}
            for spec in PACKS
        ],
        "trigger": "play once from the skill action clock; attack effects are staged to peak on the existing hit receipt, support effects begin on the receipt; gameplay motion reuses the existing attack or guard clip",
        "authoredMotionAdded": False,
    }
    path = ROOT / "Art/Parts/BattleVFX/skill-effects-v1/manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"packs": len(PACKS), "frames": sum(p["count"] for p in PACKS), "manifest": str(path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
