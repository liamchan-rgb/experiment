#!/usr/bin/env python3
"""Export only the side-view rune-sleeve correction and its review atlases."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil

from PIL import Image, ImageDraw, ImageFont
from armor_editable_sync import sync_editable_pngs

ROOT = Path(__file__).resolve().parents[1]
PREV_PART = ROOT / "Art/Parts/P1-v1/b2-armor-r4/runeArmor"
PART = ROOT / "Art/Parts/P1-v1/b2-armor-r5/runeArmor"
OLD = ROOT / "Art/Review/Equipment/b2-batch-v4"
OUT = ROOT / "Art/Review/Equipment/b2-batch-v5"
INTEGRATION = ROOT / "Art/Integration/Equipment-b2-batch-v5"
MOTION = ROOT / "Art/Integration/P1-modular-eight-way-v1/motion.json"


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    INTEGRATION.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PREV_PART, PART, dirs_exist_ok=True)
    surface = load("rune_wrist_r5", ROOT / "scripts/armor-profile-wrist-r5.py").ArmorSurface(ROOT)
    asset = json.loads((PART / "asset.json").read_text())
    asset["id"] = "p1-b2-runearmor-r5"
    frames = [f for f in surface.motion["frames"] if f["direction"] in ("left", "right")]
    assert len(frames) == 26
    for frame in frames:
        for side in ("Left", "Right"):
            slot = "outfit.sleeve." + side.lower()
            rel = f'png/{frame["direction"]}/{frame["clip"]}/{frame["frame"]:02}/{slot}.png'
            surface.profile_sleeve(frame, side).save(PART / rel)
    write(PART / "asset.json", asset)
    authoring = json.loads((PART / "authoring.json").read_text())
    authoring.update({
        "exporter": "scripts/build-b2-rune-wrist-r5.py",
        "surface": "scripts/armor-profile-wrist-r5.py",
        "method": "r4 preserved except side-view rune sleeves; original approved pose sleeve contour and actual hand silhouette locate wrist armor",
        "profileReference": "Art/Parts/P1-v1/eight-way-v1/forester/asset.json",
        "farArm": "paint exact body arm silhouette beneath the far sleeve and torso",
        "artApproval": None,
    })
    write(PART / "authoring.json", authoring)
    sync_editable_pngs(PART)

    catalog = json.loads((ROOT / "Art/Integration/Equipment-b2-batch-v4/catalog.json").read_text())
    catalog["assets"].append({"id": asset["id"], "manifest": str((PART / "asset.json").relative_to(ROOT))})
    write(INTEGRATION / "catalog.json", catalog)
    comp = load("compositor", ROOT / "scripts/compose-character-parts.py").Compositor(
        ROOT, INTEGRATION / "catalog.json", MOTION
    )
    selection = json.loads((ROOT / "Art/Integration/P1-modular-demo-v1/selection.json").read_text())
    manifest = json.loads((OLD / "manifest.json").read_text())
    manifest.update({
        "id": "b2-batch-v5",
        "title": "B2 符文甲侧向袖口返修 · 第五轮",
        "previousBatch": "b2-batch-v4",
        "previousResourceRevisionSHA256": manifest["resourceRevisionSHA256"],
    })
    for item in ("leatherArmor", "runeArmor"):
        shutil.copytree(OLD / item, OUT / item, dirs_exist_ok=True)
    entry = next(x for x in manifest["items"] if x["id"] == "runeArmor")
    entry.update({
        "revision": "b2-armor-r5",
        "artApproval": None,
        "scope": "正左、正右袖形及腕甲按原动作袖口与手部逐帧贴合；远侧袖面补齐，护肩保留随动",
    })
    columns, directions = manifest["columns"], manifest["directions"]
    for preset in selection["loadouts"]:
        selected = [
            a for a in preset["assets"]
            if a not in ("p1-eight-way-forester-v1", "p1-eight-way-wayfarer-v1")
        ] + [asset["id"]]
        path = OUT / "runeArmor" / (preset["id"] + "-walk.png")
        atlas = Image.open(path).convert("RGBA")
        for direction in ("left", "right"):
            row = directions.index(direction)
            for col, pose in enumerate(columns):
                image = comp.render(selection["base"], selected, direction, pose["clip"], pose["frame"])
                atlas.paste(image, (col * 256, row * 256))
        atlas.save(path)
    atlas = Image.open(OUT / "runeArmor/forester-walk.png").convert("RGBA")
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", 14)
    walk = []
    for col in range(9):
        board = Image.new("RGB", (1024, 560), "#20372a")
        draw = ImageDraw.Draw(board)
        for row, label in enumerate(manifest["directionLabels"]):
            cell = atlas.crop((col * 256, row * 256, (col + 1) * 256, (row + 1) * 256))
            x, y = row % 4 * 256, row // 4 * 280
            board.paste(cell, (x, y), cell)
            draw.text((x + 7, y + 256), entry["name"] + " · " + label, font=font, fill="#ffedc7")
        if col == 0:
            board.save(OUT / "runeArmor/standing.png")
        else:
            walk.append(board)
    walk[0].save(OUT / "runeArmor/walk-normal.gif", save_all=True, append_images=walk[1:],
                 duration=120, loop=0, disposal=2, optimize=True)
    files = {
        str(path.relative_to(OUT)): sha(path)
        for path in OUT.rglob("*")
        if path.is_file() and path.relative_to(OUT).parts[0] in ("leatherArmor", "runeArmor")
        and path.suffix in (".png", ".gif")
    }
    write(OUT / "files.json", files)
    manifest["resourceRevisionSHA256"] = sha(OUT / "files.json")
    write(OUT / "manifest.json", manifest)
    print(json.dumps({"revision": manifest["resourceRevisionSHA256"], "modifiedSleeves": 52,
                      "poses": 26, "artApproval": None}))


if __name__ == "__main__":
    main()
