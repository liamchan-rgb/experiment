"""Side-view rune sleeves fitted to the approved per-pose arm and hand art.

Only the rune armor's left/right sleeve layers change.  The parent surface
still supplies the torso, hem, all other directions, and moving pauldrons.
"""
from pathlib import Path
import importlib.util
import json

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("armor_surface_r4", ROOT / "scripts/armor-shared-surface-r4.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


class ArmorSurface(previous.ArmorSurface):
    def __init__(self, root):
        super().__init__(root)
        self.reference = self.root / "Art/Parts/P1-v1/eight-way-v1/forester"
        data = json.loads((self.reference / "asset.json").read_text())
        self.sleeve_bindings = {
            (b["direction"], b["clip"], b["frame"]): b["layers"]
            for b in data["bindings"]
        }

    def profile_sleeve(self, frame, side):
        key = (frame["direction"], frame["clip"], frame["frame"])
        slot = "outfit.sleeve." + side.lower()
        # These are the already-authored sleeve silhouettes for this exact
        # pose, including their original outline and hand-over-sleeve order.
        source = Image.open(self.reference / self.sleeve_bindings[key][slot]).convert("RGBA")
        original = np.asarray(source, dtype=float)
        cloth = original.copy()
        red, green, blue = original[:, :, 0], original[:, :, 1], original[:, :, 2]
        luminance = 0.299 * red + 0.587 * green + 0.114 * blue
        gold = (red > green * 1.12) & (red > blue * 1.35) & (red > 75)
        interior = (luminance > 20) & (original[:, :, 3] > 16)
        cloth[:, :, 0] = np.clip(3 + luminance * 0.22, 0, 255)
        cloth[:, :, 1] = np.clip(9 + luminance * 0.68, 0, 255)
        cloth[:, :, 2] = np.clip(19 + luminance * 1.35, 0, 255)

        # The bracer follows the actual hand silhouette. Its border is drawn
        # on the arm side; the original hand remains on top.
        hand_path = self.body[key]["body.hand." + side.lower()]
        hand = np.asarray(Image.open(self.base / hand_path).convert("RGBA"))[:, :, 3] > 64
        distance = distance_transform_edt(~hand)
        cloth[:, :, :3][gold] = original[:, :, :3][gold]
        near = (frame["direction"] == "left" and side == "Left") or (
            frame["direction"] == "right" and side == "Right"
        )
        if not near:
            cloth[:, :, :3] *= 0.78

        # Fill the exact anatomical arm below the old sleeve silhouette.
        # The original shirt's far sleeve starts partway down the arm because
        # its old torso hid the upper section; the narrower armor exposes it.
        # The near arm is also filled to avoid small holes in bent poses.
        arm_path = self.body[key]["body.arm." + side.lower()]
        arm = np.asarray(Image.open(self.base / arm_path).convert("RGBA"))[:, :, 3]
        depth = distance_transform_edt(arm > 20)
        fill = np.zeros((256, 256, 4), dtype=np.uint8)
        fill[:, :, 0] = np.where(depth > 1, 7, 4)
        fill[:, :, 1] = np.where(depth > 1, 29, 14)
        fill[:, :, 2] = np.where(depth > 1, 54, 25)
        fill[:, :, 3] = arm
        under = Image.fromarray(fill)
        under.alpha_composite(Image.fromarray(np.clip(np.rint(cloth), 0, 255).astype("uint8")))

        # Shade the *connected silhouette*, not the old shirt's brightness
        # pattern: a dark fold in the old shirt otherwise broke the silver
        # plate into flashing fragments in some walking frames.
        pixels = np.asarray(under).copy()
        silhouette = pixels[:, :, 3] > 32
        inside = distance_transform_edt(silhouette) > 1
        plate = silhouette & inside & (distance <= 7.0)
        trim = silhouette & inside & (distance > 7.0) & (distance <= 8.5)
        shade = np.clip((luminance - 15) / 52, 0, 1)
        factor = 1.0 if near else 0.78
        for channel, base, amount in ((0, 174, 49), (1, 176, 46), (2, 182, 40)):
            pixels[:, :, channel][plate] = np.rint((base + amount * shade[plate]) * factor)
        for channel, base, amount in ((0, 160, 70), (1, 103, 65), (2, 22, 48)):
            pixels[:, :, channel][trim] = np.rint((base + amount * shade[trim]) * factor)
        under = Image.fromarray(pixels)

        # Retain the r4 pauldron, its highlights and its separately bounded
        # follow-through.  The sleeve beneath it uses the authored pose.
        rest = self.joints(self.rests[frame["direction"]])
        shoulder = np.asarray(rest["shoulder" + side])
        elbow = np.asarray(rest["elbow" + side])
        y, x = np.mgrid[:256, :256]
        axis = (elbow - shoulder) / np.linalg.norm(elbow - shoulder)
        along = (np.stack([x, y], -1) - shoulder) @ axis
        cap = np.asarray(self.fit("runeArmor", frame["direction"])[slot]).copy()
        cap[along > 7] = 0
        cap = previous.warp(
            Image.fromarray(cap), self.grid,
            self.pauldron_field(frame, side, self.grid), linear=False
        )
        under.alpha_composite(cap)
        result = np.asarray(under).copy()
        result[result[:, :, 3] == 0, :3] = 0
        return Image.fromarray(result)

    def render(self, item, frame):
        result = super().render(item, frame)
        if item == "runeArmor" and frame["direction"] in ("left", "right"):
            for side in ("Left", "Right"):
                result["outfit.sleeve." + side.lower()] = self.profile_sleeve(frame, side)
        return result
