#!/usr/bin/env python3
"""Render a 120 ms/frame offline road-motion review from shipped map/art assets.

This uses production SceneMap road controls, Trail.smooth, P1 atlas columns,
WalkCycle distance/frame math, and JourneySimulation's projected travel metric.
The terrain shader, GPU shadow pass, SpriteKit, and device compositor are not
simulated; labels on the output state this limitation.
"""
import json
import math
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = json.loads((ROOT / "Sources/Resources/hero-gait.json").read_text())
SCENE = json.loads((ROOT / "Sources/Resources/SceneMap.json").read_text())
SIMULATION = (ROOT / "Sources/Game/JourneySimulation.swift").read_text()
assert re.search(r"Traveler\([^\n]*speed:\s*HeroFrames\.reviewSpeed\)", SIMULATION), \
    "JourneySimulation P1 speed no longer follows HeroFrames.reviewSpeed"

VIRTUAL_FRAMES = 24
POSES = LAYOUT["authoredFrames"][0]
FRAME_MS = int(LAYOUT["reviewFrameMs"])
SPEED = VIRTUAL_FRAMES / (POSES * FRAME_MS / 1000)


def smooth(controls, steps=8):
    if len(controls) <= 2:
        return controls
    output = []
    for i in range(len(controls) - 1):
        a, b, c, d = controls[max(i - 1, 0)], controls[i], controls[i + 1], controls[min(i + 2, len(controls) - 1)]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            def f(av, bv, cv, dv):
                return 0.5 * ((2 * bv) + (-av + cv) * t + (2 * av - 5 * bv + 4 * cv - dv) * t2
                              + (-av + 3 * bv - 3 * cv + dv) * t3)
            output.append((f(a[0], b[0], c[0], d[0]), f(a[1], b[1], c[1], d[1])))
    output.append(controls[-1])
    return output


def path_length(points):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def point_at(points, distance):
    for a, b in zip(points, points[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        segment = math.hypot(dx, dy)
        if distance <= segment:
            t = distance / segment if segment else 0
            return (a[0] + dx * t, a[1] + dy * t)
        distance -= segment
    return points[-1]


def projected_scale(dx, dy):
    screen = math.hypot(dx, dy)
    return screen / math.hypot(dx, dy * 2) if screen > 0.0001 else 1


def source_frame(gait_distance):
    frame = 1 + int(max(0, gait_distance)) % VIRTUAL_FRAMES
    return 1 + (frame - 1) * POSES // VIRTUAL_FRAMES


def trail_points(edge_index, reverse=False):
    edge = SCENE["roads"][edge_index]
    pts = smooth([(p["x"], p["y"]) for p in edge["points"]])
    return list(reversed(pts)) if reverse else pts


def main():
    width, height = 1280, 720
    ground = Image.open(ROOT / "Sources/Resources/Assets.xcassets/MeadowGround.imageset/MeadowGround.png").convert("RGB")
    canvas = ground.resize((width, height), Image.Resampling.BICUBIC).convert("RGBA")
    road_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    road_draw = ImageDraw.Draw(road_layer)
    paths = []
    for road in SCENE["roads"]:
        pts = smooth([(p["x"], p["y"]) for p in road["points"]])
        paths.append(pts)
        line = [(round(x), round(y)) for x, y in pts]
        radius = round(road["width"] + 18)
        road_draw.line(line, fill=(80, 54, 37, 185), width=radius + 4, joint="curve")
        road_draw.line(line, fill=(151, 111, 70, 220), width=radius, joint="curve")
        road_draw.line(line, fill=(113, 78, 49, 100), width=max(2, round(road["width"] * 0.16)), joint="curve")
    canvas = Image.alpha_composite(canvas, road_layer)

    atlas = Image.open(ROOT / "Sources/Resources/Assets.xcassets/Hero1Diagonals.imageset/Hero1Diagonals.png").convert("RGBA")
    cell = atlas.height // 4
    directions = [
        ("↘ down-right", 3, False, 4, 52),
        ("↙ down-left", 1, True, 5, 48),
        ("↖ up-left", 3, True, 6, 48),
        ("↗ up-right", 1, False, 7, 52),
    ]
    states = []
    for label, edge_index, reverse, facing, start_fraction in directions:
        points = trail_points(edge_index, reverse)
        length = path_length(points)
        states.append({"label": label, "points": points, "distance": min(length - 1, start_fraction),
                       "facing": facing, "gait": 0.0})

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    except OSError:
        font = small = ImageFont.load_default()
    frames = []
    frames_count = 48
    dt = FRAME_MS / 1000
    for tick in range(frames_count):
        image = canvas.copy()
        draw = ImageDraw.Draw(image, "RGBA")
        for state in states:
            points = state["points"]
            here = point_at(points, state["distance"])
            ahead = point_at(points, min(path_length(points), state["distance"] + 1))
            scale = projected_scale(ahead[0] - here[0], ahead[1] - here[1])
            state["distance"] = min(path_length(points), state["distance"] + SPEED * scale * dt)
            foot = point_at(points, state["distance"])
            dx, dy = foot[0] - here[0], foot[1] - here[1]
            state["gait"] += math.hypot(dx, dy) / projected_scale(dx, dy)
            col = source_frame(state["gait"])
            sprite = atlas.crop((col * cell, (state["facing"] - 4) * cell,
                                 (col + 1) * cell, (state["facing"] - 3) * cell))
            sprite = sprite.resize((64, 64), Image.Resampling.NEAREST)
            image.alpha_composite(sprite, (round(foot[0] - 32), round(foot[1] - 56)))
            draw.ellipse((foot[0] - 3, foot[1] - 2, foot[0] + 3, foot[1] + 2),
                         fill=(255, 238, 173, 220), outline=(45, 30, 20, 255))
        # Show the exact speed and limitations on every frame for standalone review.
        draw.rectangle((0, 0, width, 48), fill=(16, 20, 15, 205))
        draw.text((18, 4), f"Offline road motion · P1 {SPEED:.2f}u/s · {FRAME_MS}ms/frame", font=font,
                  fill=(255, 248, 220, 255))
        draw.text((18, 27), "Production route controls + shipped art; terrain/shadows simplified; not a GPU or device capture",
                  font=small, fill=(245, 225, 180, 255))
        # Zoom to the junction and the two actual diagonal branches while
        # retaining the production map's 16:9 camera framing.
        image = image.crop((220, 135, 1020, 585)).convert("RGB")
        image = image.resize((640, 360), Image.Resampling.LANCZOS)
        overlay = ImageDraw.Draw(image, "RGBA")
        overlay.rectangle((0, 0, 640, 43), fill=(16, 20, 15, 220))
        review_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        overlay.text((8, 2), f"OFFLINE · P1 {SPEED:.0f} units/s · {FRAME_MS} ms/frame · no GPU/device capture",
                     font=review_font, fill=(255, 248, 220, 255))
        overlay.text((8, 22), "↘ Down-right   ↙ Down-left   ↖ Up-left   ↗ Up-right · shipped roads + atlas",
                     font=review_font, fill=(245, 225, 180, 255))
        frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE, colors=192))

    output = ROOT / "Artifacts/Diagnostics/road-motion-four-directions-offline.gif"
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=FRAME_MS,
                   loop=0, optimize=False, disposal=2)
    print(f"Wrote {output.relative_to(ROOT)} ({frames_count} frames, {FRAME_MS} ms/frame, {SPEED:.2f} units/s)")


if __name__ == "__main__":
    main()
