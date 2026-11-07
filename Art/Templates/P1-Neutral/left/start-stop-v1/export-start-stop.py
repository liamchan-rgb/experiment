#!/usr/bin/env python3
"""Export fixed ownership masks and normal-speed transition reviews."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
R2 = ROOT.parent / "walk-r2-head-motion"
ORDER = [
    "body.leg.right", "body.leg.left", "body.arm.right", "body.hand.right",
    "body.torso", "head.base", "body.arm.left", "body.hand.left",
]
COLORS = {
    "body.leg.right": (75, 195, 225), "body.leg.left": (60, 230, 120),
    "body.arm.right": (245, 210, 65), "body.hand.right": (250, 135, 45),
    "body.torso": (220, 90, 120), "head.base": (130, 120, 245),
    "body.arm.left": (70, 170, 255), "body.hand.left": (210, 90, 245),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(image: Image.Image, bg="#17372c") -> Image.Image:
    out = Image.new("RGBA", image.size, bg)
    out.alpha_composite(image.convert("RGBA"))
    return out.convert("RGB")


def save_gif(images: list[Image.Image], path: Path, duration=120) -> None:
    frames = [flatten(im).resize((512, 512), Image.Resampling.NEAREST) for im in images]
    atlas = Image.new("RGB", (frames[0].width * len(frames), frames[0].height))
    for i, frame in enumerate(frames):
        atlas.paste(frame, (i * frame.width, 0))
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(path, save_all=True, append_images=indexed[1:], duration=duration, loop=0, disposal=2)


def mask_from_points(points: list[list[int]]) -> np.ndarray:
    out = np.zeros((256, 256), dtype=bool)
    for x, y in points:
        out[y, x] = True
    return out


def main() -> None:
    cfg = json.loads((ROOT / "authoring.json").read_text())
    for dirname in ("layers", "frames", "editable", "review"):
        (ROOT / dirname).mkdir(exist_ok=True)
    poses = cfg["poses"]
    slots = [slot for slot in ORDER if slot != "head.base"]
    source_art: list[Image.Image] = []
    ownership_maps: list[dict[str, np.ndarray]] = []
    all_frames: list[Image.Image] = []
    per_pose = []
    common = Image.open(ROOT / "registered-source/start01.png").convert("RGBA")
    common_head = Image.new("RGBA", (256, 256))
    common_head.paste(common, (0, 0), common.getchannel("A"))
    hmask = Image.new("L", (256, 256))
    ImageDraw.Draw(hmask).polygon([tuple(p) for p in cfg["headPartition"]], fill=255)
    common_head.putalpha(ImageChops.multiply(common_head.getchannel("A"), hmask))

    for i, pose in enumerate(poses):
        name = pose["id"]
        art = Image.open(ROOT / "registered-source" / f"{name}.png").convert("RGBA")
        rgba = np.asarray(art)
        visible = rgba[:, :, 3] > 0
        owner = {slot: np.zeros((256, 256), dtype=bool) for slot in slots}
        for group in pose["ownershipOverrides"]:
            slot = group["slot"]
            pts = group["pixels"]
            if np.any(owner[slot]):
                pass
            for x, y in pts:
                if owner[slot][y, x]:
                    raise ValueError(f"{name}: duplicate coordinates inside {slot}")
                owner[slot][y, x] = True
        total = np.zeros((256, 256), dtype=np.uint8)
        for slot in slots:
            total += owner[slot].astype(np.uint8)
        head_visible = np.asarray(hmask) > 0
        body_visible = visible & ~head_visible
        missing = body_visible & (total == 0)
        overlap = total > 1
        extra = (total > 0) & ~body_visible
        if np.any(missing) or np.any(overlap) or np.any(extra):
            raise ValueError(f"{name}: missing={int(missing.sum())}, overlap={int(overlap.sum())}, outside-body={int(extra.sum())}")
        ownership_maps.append(owner)
        source_art.append(art)
        parts = {}
        for slot in slots:
            arr = rgba.copy()
            arr[~owner[slot]] = (0, 0, 0, 0)
            part = Image.fromarray(arr, "RGBA")
            parts[slot] = part
        parts["head.base"] = common_head.copy()
        layer_dir = ROOT / "layers" / f"{i:02}"
        layer_dir.mkdir(exist_ok=True)
        for slot in ORDER:
            parts[slot].save(layer_dir / f"{slot}.png")
        frame = Image.new("RGBA", (256, 256))
        for slot in ORDER:
            frame.alpha_composite(parts[slot])
        frame.save(ROOT / "frames" / f"{i:02}.png")
        all_frames.append(frame)

        counts = {slot: int(mask.sum()) for slot, mask in owner.items()}
        nonhead_expected = rgba.copy()
        nonhead_expected[head_visible | (rgba[:, :, 3] == 0)] = (0, 0, 0, 0)
        nonhead_actual = np.zeros((256, 256, 4), dtype=np.uint8)
        for slot in slots:
            nonhead_actual = np.maximum(nonhead_actual, np.asarray(parts[slot]))
        diff = int(np.any(nonhead_actual != nonhead_expected, axis=2).sum())
        if diff:
            raise ValueError(f"{name}: layer pixels differ from source body at {diff} coordinates")
        per_pose.append({
            "pose": name, "clip": pose["clip"], "frame": pose["frame"],
            "sourceSHA256": digest(ROOT / pose["source"]),
            "sourceVisibleBodyPixels": int(body_visible.sum()), "layerPixelCounts": counts,
            "missingPixels": 0, "overlapPixels": 0, "bodyRecompositionDifferencePixels": diff,
            "soleMarkerAlphaChecks": {
                side: {
                    "coordinate": pose["soleMarkers"][side],
                    "layer": f"body.leg.{side}",
                    "alpha": int(np.asarray(parts[f"body.leg.{side}"])[pose["soleMarkers"][side][1], pose["soleMarkers"][side][0], 3]),
                    "passed": int(np.asarray(parts[f"body.leg.{side}"])[pose["soleMarkers"][side][1], pose["soleMarkers"][side][0], 3]) >= 128,
                } for side in ("left", "right")
            },
            "discardedAlpha1RegistrationSpecks": pose["sourceDiscardPixels"],
            "layerSHA256": {slot: digest(layer_dir / f"{slot}.png") for slot in ORDER},
        })
        if not all(c["passed"] for c in per_pose[-1]["soleMarkerAlphaChecks"].values()):
            raise ValueError(f"{name}: at least one sole marker is not an alpha>=128 pixel in its owning leg layer")

    # Slot atlas: every independent authoring layer is visible in its own cell.
    cell = 256
    atlas = Image.new("RGB", (cell * len(ORDER), cell * 4), "#17372c")
    adraw = ImageDraw.Draw(atlas)
    for row in range(4):
        for col, slot in enumerate(ORDER):
            im = Image.open(ROOT / "layers" / f"{row:02}" / f"{slot}.png").convert("RGBA")
            atlas.paste(flatten(im), (col * cell, row * cell))
            adraw.text((col * cell + 3, row * cell + 3), f"{poses[row]['id']} / {slot}", fill="white")
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.Resampling.NEAREST).save(ROOT / "review/layer-atlas-2x.png")

    # Semantic tint overlay is for ownership review only; original pixel art
    # remains intact in layers/ and frames/.
    tint = Image.new("RGB", (512 * 2, 512 * 2), "#17372c")
    draw = ImageDraw.Draw(tint, "RGBA")
    for i, (pose, art, owner) in enumerate(zip(poses, source_art, ownership_maps)):
        x0, y0 = (i % 2) * 512, (i // 2) * 512
        base = flatten(art).resize((512, 512), Image.Resampling.NEAREST).convert("RGBA")
        overlay = Image.new("RGBA", (256, 256))
        px = np.zeros((256,256,4), dtype=np.uint8)
        for slot in slots:
            px[owner[slot]] = (*COLORS[slot], 92)
        overlay = Image.fromarray(px, "RGBA").resize((512,512), Image.Resampling.NEAREST)
        base.alpha_composite(overlay)
        tint.paste(base.convert("RGB"), (x0, y0))
        draw.text((x0 + 5, y0 + 5), pose["id"], fill="white")
    tint.save(ROOT / "review/ownership-tint-2x.png")

    # Tight, nearest-neighbour anatomy audit panel: registered torso and both
    # limb slots, all cropped from shoulder to hand with each slot visible.
    crop_box = (90, 126, 162, 181)
    anatomy_slots = ["body.torso", "body.arm.right", "body.hand.right", "body.arm.left", "body.hand.left"]
    anatomy = Image.new("RGB", (len(anatomy_slots) * 72 * 4, len(poses) * 55 * 4), "#17372c")
    anatomy_draw = ImageDraw.Draw(anatomy)
    for row, pose in enumerate(poses):
        src = Image.open(ROOT / "registered-source" / f"{pose['id']}.png").convert("RGBA")
        for col, slot in enumerate(anatomy_slots):
            im = Image.open(ROOT / "layers" / f"{row:02}" / f"{slot}.png").convert("RGBA")
            crop = flatten(im.crop(crop_box)).resize((72 * 4, 55 * 4), Image.Resampling.NEAREST)
            x0, y0 = col * 72 * 4, row * 55 * 4
            anatomy.paste(crop, (x0, y0))
            anatomy_draw.text((x0 + 2, y0 + 2), f"{pose['id']} {slot}", fill="white")
    anatomy.save(ROOT / "review/arm-hand-boundaries-4x.png")

    refs = {
        "idle00": Image.open(R2 / "frames/00.png").convert("RGBA"),
        "walk01": Image.open(R2 / "frames/01.png").convert("RGBA"),
        "walk08": Image.open(R2 / "frames/08.png").convert("RGBA"),
    }
    ref_dir = ROOT / "review/reference-frames"
    ref_dir.mkdir(exist_ok=True)
    for name, im in refs.items():
        im.save(ref_dir / f"{name}.png")
    start = [refs["idle00"], all_frames[0], all_frames[1], refs["walk01"]]
    stop = [refs["walk08"], all_frames[2], all_frames[3], refs["idle00"]]
    save_gif(start, ROOT / "review/start-transition-120ms.gif", 120)
    save_gif(stop, ROOT / "review/stop-transition-120ms.gif", 120)

    # Full-body start/stop contact sheet at 1x and nearest-neighbor 2x.
    contacts = [refs["idle00"], all_frames[0], all_frames[1], refs["walk01"], refs["walk08"], all_frames[2], all_frames[3], refs["idle00"]]
    contact = Image.new("RGB", (256 * 4, 256 * 2), "#17372c")
    cd = ImageDraw.Draw(contact)
    labels = ["idle00", "start01", "start02", "walk01", "walk08", "stop01", "stop02", "idle00"]
    for i, (label, im) in enumerate(zip(labels, contacts)):
        x0, y0 = (i % 4) * 256, (i // 4) * 256
        contact.paste(flatten(im), (x0, y0))
        cd.text((x0 + 4, y0 + 4), label, fill="white")
    contact.save(ROOT / "review/start-stop-contact-1x.png")
    contact.resize((contact.width * 2, contact.height * 2), Image.Resampling.NEAREST).save(ROOT / "review/start-stop-contact-2x.png")

    audit = {
        "status": "fixed ownership exported; authoring visual self-review complete; shared head still parent integration",
        "artApproval": None, "sourceRegistration": {"scale": 0.194, "translation": [4.72, 6.4], "sourceCanvas": [1254,1254]},
        "sharedHeadPreview": "generated start01 head used consistently as a temporary preview; parent integration replaces it with walk-r2 shared head",
        "durationMs": 120, "checks": per_pose,
        "files": {"startGif": "review/start-transition-120ms.gif", "stopGif": "review/stop-transition-120ms.gif", "contactSheet": "review/start-stop-contact-2x.png", "layerAtlas": "review/layer-atlas-2x.png", "ownershipTint": "review/ownership-tint-2x.png", "armHandBoundaries": "review/arm-hand-boundaries-4x.png"},
        "limits": ["visible ownership only; hidden anatomy not reconstructed", "temporary generated head in preview", "no app/runtime/device integration"],
    }
    (ROOT / "ownership-review.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"poses": len(per_pose), "checkedVisiblePixels": sum(p["sourceVisibleBodyPixels"] for p in per_pose), "diffs": sum(p["bodyRecompositionDifferencePixels"] for p in per_pose), "gifs": audit["files"]}, ensure_ascii=False))


if __name__ == "__main__":
    from PIL import ImageChops
    main()
