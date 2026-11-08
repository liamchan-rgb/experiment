#!/usr/bin/env python3
"""Emit fixed, visible-pixel ownership for four generated transition poses.

The geometric seed regions are authoring input only. Every visible non-head
source pixel is written into authoring.json as a fixed ownership override;
runtime and downstream export do not run this segmentation.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parent
SLOTS = [
    "body.hand.left", "body.arm.left", "body.hand.right", "body.arm.right",
    "body.leg.left", "body.leg.right", "body.torso", "head.base",
]
DRAW_ORDER = [
    "body.leg.right", "body.leg.left", "body.arm.right", "body.hand.right",
    "body.torso", "head.base", "body.arm.left", "body.hand.left",
]
HEAD = [[0, 0], [255, 0], [255, 128], [0, 128]]
POSES = [
    {
        "id": "start01", "clip": "walk-start", "frame": 1,
        # Foreground/near arm and leg sit screen-right in this almost-idle pose.
        "hand.left": [[132, 161], [147, 161], [147, 175], [132, 175]],
        "arm.left": [[128, 132], [147, 132], [147, 165], [128, 165]],
        "hand.right": [[101, 158], [117, 158], [117, 174], [101, 174]],
        "arm.right": [[99, 132], [120, 132], [120, 167], [99, 167]],
        "leg.left": [[117, 175], [142, 175], [142, 215], [117, 215]],
        "leg.right": [[102, 175], [126, 175], [126, 214], [102, 214]],
        "handPoints": {"left": [138, 169], "right": [109, 166]},
        "elbows": {"left": [137, 151], "right": [110, 151]},
        "supports": "both",
        "legSplit": 120, "leftLegScreenSide": "right",
    },
    {
        "id": "start02", "clip": "walk-start", "frame": 2,
        "hand.left": [[138, 158], [154, 158], [154, 176], [138, 176]],
        "arm.left": [[130, 132], [154, 132], [154, 167], [130, 167]],
        "hand.right": [[94, 155], [110, 155], [110, 174], [94, 174]],
        "arm.right": [[94, 132], [121, 132], [121, 165], [94, 165]],
        "leg.left": [[86, 175], [123, 175], [123, 214], [86, 214]],
        "leg.right": [[117, 175], [148, 175], [148, 214], [117, 214]],
        "handPoints": {"left": [145, 165], "right": [102, 163]},
        "elbows": {"left": [141, 151], "right": [108, 151]},
        "supports": "left-forward-contact-right-trailing",
        "legSplit": 119, "leftLegScreenSide": "left",
    },
    {
        "id": "stop01", "clip": "walk-stop", "frame": 1,
        "hand.left": [[132, 159], [148, 159], [148, 176], [132, 176]],
        "arm.left": [[127, 132], [148, 132], [148, 167], [127, 167]],
        "hand.right": [[99, 157], [117, 157], [117, 174], [99, 174]],
        "arm.right": [[97, 138], [121, 138], [121, 168], [97, 168]],
        "leg.left": [[97, 175], [124, 175], [124, 214], [97, 214]],
        "leg.right": [[117, 175], [148, 175], [148, 214], [117, 214]],
        "handPoints": {"left": [140, 168], "right": [108, 165]},
        "elbows": {"left": [137, 151], "right": [109, 153]},
        "supports": "both-decelerating",
        "legSplit": 119, "leftLegScreenSide": "left",
    },
    {
        "id": "stop02", "clip": "walk-stop", "frame": 2,
        "hand.left": [[128, 163], [143, 163], [143, 178], [128, 178]],
        "arm.left": [[126, 132], [146, 132], [146, 168], [126, 168]],
        "hand.right": [[139, 157], [155, 157], [155, 174], [139, 174]],
        "arm.right": [[137, 132], [156, 132], [156, 170], [137, 170]],
        "leg.left": [[117, 175], [143, 175], [143, 216], [117, 216]],
        "leg.right": [[104, 175], [128, 175], [128, 215], [104, 215]],
        "handPoints": {"left": [137, 170], "right": [146, 165]},
        "elbows": {"left": [136, 151], "right": [147, 151]},
        "supports": "both-settling",
        "legSplit": 122, "leftLegScreenSide": "right",
    },
]


def polygon_mask(points: list[list[int]]) -> np.ndarray:
    mask = Image.new("L", (256, 256))
    ImageDraw.Draw(mask).polygon([tuple(p) for p in points], fill=255)
    return np.asarray(mask) > 0


def centroid(points: np.ndarray) -> list[int]:
    ys, xs = np.where(points)
    return [int(np.rint(xs.mean())), int(np.rint(ys.mean()))]


def sole_marker(mask: np.ndarray) -> list[int]:
    """Choose a real >=128-alpha pixel at the center of the lowest foot run."""
    ys, xs = np.where(mask)
    for y0 in range(int(ys.max()), int(ys.min()) - 1, -1):
        row_xs = np.where(mask[y0])[0]
        if not len(row_xs):
            continue
        runs = np.split(row_xs, np.where(np.diff(row_xs) > 1)[0] + 1)
        run = max(runs, key=lambda xs0: (len(xs0), -int(xs0[0])))
        return [int(run[(len(run) - 1) // 2]), int(y0)]
    raise ValueError("No opaque pixels available for sole marker")


def register(name: str) -> tuple[Image.Image, list[list[int]]]:
    src = Image.open(ROOT / "source" / f"{name}.png").convert("RGBA")
    if src.size != (1254, 1254):
        raise ValueError(f"{name}: expected full 1254x1254 source, got {src.size}")
    art = src.transform(
        (256, 256), Image.Transform.AFFINE,
        (1 / 0.194, 0, -4.72 / 0.194, 0, 1 / 0.194, -6.4 / 0.194),
        Image.Resampling.NEAREST,
    )
    alpha = art.getchannel("A").point(lambda a: 255 if a >= 250 else a)
    art.putalpha(alpha)
    rgba = np.asarray(art).copy()
    # Remove only alpha<=8 registration specks. No visible source pixel is deleted.
    # Raw generated PNGs remain untouched in source/.
    components, count = label(rgba[:, :, 3] > 0, np.ones((3, 3), dtype=np.uint8))
    sizes = np.bincount(components.ravel())
    sizes[0] = 0
    largest = int(np.argmax(sizes))
    discarded: list[list[int]] = []
    for comp in range(1, count + 1):
        if comp == largest:
            continue
        ys, xs = np.where(components == comp)
        if np.all(rgba[ys, xs, 3] <= 8):
            for y, x in zip(ys, xs):
                rgba[y, x, 3] = 0
                discarded.append([int(x), int(y)])
        else:
            raise ValueError(f"{name}: unexpected disconnected source component {len(xs)} pixels at {(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))}")
    art = Image.fromarray(rgba, "RGBA")
    (ROOT / "registered-source").mkdir(exist_ok=True)
    art.save(ROOT / "registered-source" / f"{name}.png")
    return art, discarded


def ownership(art: Image.Image, pose: dict) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    rgba = np.asarray(art).astype(np.int16)
    y, x = np.indices((256, 256))
    alpha = rgba[:, :, 3]
    visible = (alpha > 0) & (y > 128)
    r, g, b = rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2]
    # Clothing colors stay with torso. Limbs use fixed anatomical regions,
    # which is important where the generated near/far skin tones overlap.
    cream = (r > 150) & (g > 130) & (b > 92) & ((r - g) < 38) & ((g - b) < 64)
    gray_spread = np.maximum.reduce([r, g, b]) - np.minimum.reduce([r, g, b])
    charcoal = (y >= 163) & (gray_spread < 38) & (np.maximum.reduce([r, g, b]) < 170) & (np.maximum.reduce([r, g, b]) > 20)
    clothing = visible & (cream | charcoal)
    owners = np.full((256, 256), "body.torso", dtype=object)
    owners[~visible] = "__transparent__"

    # Assign closed fists first, then arm silhouettes around them. Polygons
    # are authored against the actual registered image. Clothing remains with
    # the torso even when it touches a shoulder or wrist.
    for side in ("left", "right"):
        candidate = visible & polygon_mask(pose[f"hand.{side}"]) & ~clothing
        owners[candidate] = f"body.hand.{side}"
    for side in ("right", "left"):
        candidate = visible & polygon_mask(pose[f"arm.{side}"]) & ~clothing
        owners[candidate & (owners == "body.torso")] = f"body.arm.{side}"

    # At the shorts hem, the legs separate along the visible anatomical gap.
    # A per-pose vertical split follows the two foot paths while preserving
    # every original antialias and outline pixel.
    leg_region = polygon_mask(pose["leg.left"]) | polygon_mask(pose["leg.right"])
    leg_candidates = visible & leg_region & (y >= 179) & ~charcoal
    split = pose["legSplit"]
    left_leg_on_right = pose["leftLegScreenSide"] == "right"
    if left_leg_on_right:
        owners[leg_candidates & (x >= split)] = "body.leg.left"
        owners[leg_candidates & (x < split)] = "body.leg.right"
    else:
        owners[leg_candidates & (x < split)] = "body.leg.left"
        owners[leg_candidates & (x >= split)] = "body.leg.right"

    precedence = ["body.hand.left", "body.arm.left", "body.hand.right", "body.arm.right", "body.leg.left", "body.leg.right", "body.torso"]
    slot_ids = {slot: i for i, slot in enumerate(precedence)}
    idx = np.full((256, 256), -1, dtype=np.int8)
    owner_maps = {}
    for slot, slot_idx in slot_ids.items():
        owner_maps[slot] = visible & (owners == slot)
        idx[owner_maps[slot]] = slot_idx
    if np.any(visible & (idx < 0)):
        raise ValueError(f"{pose['id']}: uncovered visible pixels")
    return owners, owner_maps


def main() -> None:
    cfg = json.loads((ROOT / "authoring.json").read_text())
    cfg.update({
        "id": "p1-neutral-left-start-stop-v1",
        "version": "0.2.0",
        "status": "fixed visible-pixel ownership authored and visually self-reviewed; shared-head integration pending",
        "registration": {
            "sourceCanvas": [1254, 1254],
            "sourceScale": 0.194,
            "sourceTranslation": [4.72, 6.4],
            "rule": "Register full source canvas; never fit alpha bounds.",
            "headRule": "Parent integration replaces generated head with approved r2 shared head and applies transition headToCanvas.",
        },
        "compatibility": {"rig": "p1-chibi-v1", "bodyProfile": "p1-standard", "actionSet": "locomotion-v1"},
        "headPartition": HEAD,
        "ownershipPriority": SLOTS[:-2],
        "drawOrder": DRAW_ORDER,
        "frameDurationMs": 120,
    })
    records = []
    for i, pose in enumerate(POSES):
        name = pose["id"]
        art, discarded = register(name)
        _, maps = ownership(art, pose)
        rgba = np.asarray(art).copy()
        head_mask = polygon_mask(HEAD)
        body_visible = (rgba[:, :, 3] > 0) & ~head_mask
        visible = sum(maps.values())
        if not np.array_equal(visible, body_visible):
            raise ValueError(f"{name}: ownership does not cover source body exactly")
        partitions = {f"body.{part}": pose[part].copy() for part in ("hand.left", "arm.left", "hand.right", "arm.right", "leg.left", "leg.right")}
        overrides = []
        counts = {}
        for slot in SLOTS[:-1]:
            mask = maps.get(slot, np.zeros((256,256), dtype=bool))
            ys, xs = np.where(mask)
            counts[slot] = int(len(xs))
            if len(xs):
                overrides.append({"slot": slot, "pixels": [[int(x), int(y)] for y, x in zip(ys, xs)]})
        # Reconcile markers from the actual fixed owner maps, so the hand and
        # sole sockets follow the generated silhouette rather than the guide.
        soles = {}
        for side in ("left", "right"):
            leg = maps[f"body.leg.{side}"] & (rgba[:, :, 3] >= 128)
            soles[side] = sole_marker(leg)
        hand_points = {}
        for side in ("left", "right"):
            hand = maps[f"body.hand.{side}"] & (rgba[:, :, 3] >= 128)
            hand_points[side] = centroid(hand)
        joints = {
            "neck": [125, 132], "shoulderLeft": [129, 138], "shoulderRight": [122, 140],
            "elbowLeft": pose["elbows"]["left"], "elbowRight": pose["elbows"]["right"],
            "hipLeft": [129, 176], "hipRight": [122, 176],
        }
        cfg_pose = {
            "id": name, "clip": pose["clip"], "frame": pose["frame"],
            "source": f"source/{name}.png", "sourceCanvas": [1254,1254],
            "sourceSHA256": hashlib.sha256((ROOT / "source" / f"{name}.png").read_bytes()).hexdigest(),
            "sourceScale": 0.194, "sourceTranslation": [4.72,6.4],
            "partitions": partitions, "ownershipOverrides": overrides,
            "headPartition": HEAD,
            "joints": joints, "soleMarkers": soles, "handMarkers": hand_points,
            "support": pose["supports"], "ownershipPixelCounts": counts,
            "sourceDiscardPixels": discarded,
            "soleMarkerValidation": {
                side: {"sourceAlpha": int(rgba[xy[1], xy[0], 3]), "ownedBy": f"body.leg.{side}", "ownedAlpha": int(rgba[xy[1], xy[0], 3])}
                for side, xy in soles.items()
            },
        }
        records.append(cfg_pose)
    cfg["poses"] = records
    cfg["ownership"] = {
        "slots": DRAW_ORDER,
        "status": "fixed explicit visible-pixel ownership; recomposition and boundary atlases reviewed",
        "rule": "Every alpha-visible non-head source pixel belongs to one semantic slot. OwnershipOverrides are fixed authoring coordinates; no runtime classifier or repaint.",
        "perPoseCounts": {p["id"]: p["ownershipPixelCounts"] for p in records},
    }
    (ROOT / "authoring.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"poses":len(records),"overrides":sum(sum(len(o['pixels']) for o in p['ownershipOverrides']) for p in records),"counts":{p['id']:p['ownershipPixelCounts'] for p in records}},ensure_ascii=False))


if __name__ == "__main__":
    main()
