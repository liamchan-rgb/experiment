#!/usr/bin/env python3
"""Recheck the limited rune-sleeve revision and its actual review atlases."""
from pathlib import Path
import base64
import hashlib
import importlib.util
import json
import re

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, distance_transform_edt

R = Path(__file__).resolve().parents[1]
OLD_PART = R / "Art/Parts/P1-v1/b2-armor-r4/runeArmor"
NEW_PART = R / "Art/Parts/P1-v1/b2-armor-r5/runeArmor"
OLD = R / "Art/Review/Equipment/b2-batch-v4"
NEW = R / "Art/Review/Equipment/b2-batch-v5"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


contract = load("contract", R / "scripts/check-character-part.py")
errors = contract.check_asset(NEW_PART / "asset.json")
assert not errors, errors
asset = json.loads((NEW_PART / "asset.json").read_text())
assert len(asset["bindings"]) == 104
changed, checked, editable = [], 0, 0
for binding in asset["bindings"]:
    for slot, rel in binding["layers"].items():
        path, old_path = NEW_PART / rel, OLD_PART / rel
        current, prior = path.read_bytes(), old_path.read_bytes()
        if current != prior:
            assert binding["direction"] in ("left", "right") and slot.startswith("outfit.sleeve.")
            changed.append(rel)
        array = np.asarray(Image.open(path).convert("RGBA"))
        assert not np.any(array[array[:, :, 3] == 0, :3]), rel
        svg = NEW_PART / "editable" / (
            f'{binding["direction"]}-{binding["clip"]}-{binding["frame"]:02}-{slot}.svg'
        )
        data = re.search(r'data:image/png;base64,([^"]+)', svg.read_text()).group(1)
        assert base64.b64decode(data) == current, str(svg)
        editable += 1
        checked += 1
assert checked == editable == 416 and len(changed) == 52

surface = load("surface", R / "scripts/armor-profile-wrist-r5.py").ArmorSurface(R)
contacts = []
for frame in surface.motion["frames"]:
    if frame["direction"] not in ("left", "right"):
        continue
    key = frame["direction"], frame["clip"], frame["frame"]
    for side in ("Left", "Right"):
        name = side.lower()
        hand = np.asarray(Image.open(surface.base / surface.body[key]["body.hand." + name]).convert("RGBA"))[:, :, 3] > 64
        arm = np.asarray(Image.open(surface.base / surface.body[key]["body.arm." + name]).convert("RGBA"))[:, :, 3]
        sleeve = np.asarray(Image.open(
            NEW_PART / f'png/{frame["direction"]}/{frame["clip"]}/{frame["frame"]:02}/outfit.sleeve.{name}.png'
        ).convert("RGBA"))
        assert np.all(sleeve[:, :, 3] >= arm), key
        assert np.any(binary_dilation(hand, iterations=1) & (sleeve[:, :, 3] > 64)), (key, side)
        distance = distance_transform_edt(~hand)
        # Both sides must retain visible near-wrist silver, but this geometry
        # check is only a supplement to inspection of the assembled frames.
        light = ((sleeve[:, :, :3].min(axis=2) > 120)
                 & (sleeve[:, :, :3].max(axis=2) - sleeve[:, :, :3].min(axis=2) < 60)
                 & (sleeve[:, :, 3] > 64) & (distance > 0) & (distance <= 7.0))
        assert light.any(), (key, side)
        contacts.append({"direction": key[0], "clip": key[1], "frame": key[2], "side": side,
                         "silverPixelsNearHand": int(light.sum())})
assert len(contacts) == 52

comp = load("compositor", R / "scripts/compose-character-parts.py").Compositor(
    R, R / "Art/Integration/Equipment-b2-batch-v5/catalog.json",
    R / "Art/Integration/P1-modular-eight-way-v1/motion.json",
)
selection = json.loads((R / "Art/Integration/P1-modular-demo-v1/selection.json").read_text())
manifest = json.loads((NEW / "manifest.json").read_text())
recomposed = unaffected = 0
for preset in selection["loadouts"]:
    assets = [a for a in preset["assets"] if a not in ("p1-eight-way-forester-v1", "p1-eight-way-wayfarer-v1")]
    assets.append("p1-b2-runearmor-r5")
    atlas = Image.open(NEW / "runeArmor" / (preset["id"] + "-walk.png")).convert("RGBA")
    prior = Image.open(OLD / "runeArmor" / (preset["id"] + "-walk.png")).convert("RGBA")
    for row, direction in enumerate(manifest["directions"]):
        for col, pose in enumerate(manifest["columns"]):
            box = (col * 256, row * 256, (col + 1) * 256, (row + 1) * 256)
            cell = atlas.crop(box)
            if direction in ("left", "right"):
                expected = comp.render(selection["base"], assets, direction, pose["clip"], pose["frame"])
                assert cell.tobytes() == expected.tobytes(), (preset["id"], direction, pose)
                recomposed += 1
            else:
                assert cell.tobytes() == prior.crop(box).tobytes(), (preset["id"], direction, pose)
                unaffected += 1
assert recomposed == 52 and unaffected == 156
for path in (OLD / "leatherArmor").rglob("*"):
    if path.is_file():
        assert (NEW / path.relative_to(OLD)).read_bytes() == path.read_bytes(), path
for path in (OLD / "runeArmor").glob("battle-*"):
    assert (NEW / path.relative_to(OLD)).read_bytes() == path.read_bytes(), path
for rel, digest in json.loads((NEW / "files.json").read_text()).items():
    assert sha(NEW / rel) == digest, rel
assert sha(NEW / "files.json") == manifest["resourceRevisionSHA256"]
assert set(manifest["carriedApprovals"]) == {"greatSword", "legendaryStaff", "powerBadge", "actionRing"}
for direction in ("left", "right"):
    for suffix, total in (("walk-normal.gif", 960), ("start-stop-normal.gif", 3360)):
        im = Image.open(NEW / f"rune-{direction}-{suffix}")
        durations = []
        for n in range(im.n_frames):
            im.seek(n)
            durations.append(im.info["duration"])
        assert sum(durations) == total and im.info["loop"] == 0
        assert im.n_frames == (8 if total == 960 else 22)
result = {
    "partContract": "passed", "bindings": len(asset["bindings"]),
    "checkedPngLayers": checked, "modifiedProfileSleeves": len(changed),
    "editablePngMatches": editable, "armCoverageAndCuffContact": contacts,
    "wholeBodyRecompositions": recomposed, "otherDirectionCellsUnchanged": unaffected,
    "leatherAndRuneBattleBytesUnchanged": True, "fourPriorApprovalsCarried": True,
    "walkGifFramesAndDuration": "8 x 120 ms, loop",
    "transitionGifFramesAndDuration": "22 stages, 3360 ms, loop",
    "artApproval": None, "appSimulatorOrDeviceRun": False,
    "note": "Geometry checks supplement full-body frame inspection; they do not constitute user art approval.",
}
(NEW / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: result[k] for k in (
    "bindings", "checkedPngLayers", "modifiedProfileSleeves", "editablePngMatches",
    "wholeBodyRecompositions", "otherDirectionCellsUnchanged", "leatherAndRuneBattleBytesUnchanged"
)}))
