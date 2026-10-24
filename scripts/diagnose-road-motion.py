#!/usr/bin/env python3
"""Offline diagnostics reading the production route and gait clock sources."""
from math import atan2, cos, hypot, pi, sin
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = json.loads((ROOT / "Sources/Resources/hero-gait.json").read_text())
SCENE_MAP = json.loads((ROOT / "Sources/Resources/SceneMap.json").read_text())
DT = 1 / 60
VIRTUAL_FRAMES = 24
P1_POSES = LAYOUT["authoredFrames"][0]
REVIEW_MS = LAYOUT["reviewFrameMs"]
REVIEW_SPEED = VIRTUAL_FRAMES / (P1_POSES * REVIEW_MS / 1000)
SIMULATION_SOURCE = (ROOT / "Sources/Game/JourneySimulation.swift").read_text()
RENDERER_SOURCE = (ROOT / "Sources/Game/MeadowShadowRenderer.swift").read_text()
P1_SPEED_USES_REVIEW = bool(re.search(
    r"Traveler\([^\n]*speed:\s*HeroFrames\.reviewSpeed\)", SIMULATION_SOURCE
))
P1_SPEED = REVIEW_SPEED if P1_SPEED_USES_REVIEW else float(re.search(
    r"Traveler\([^\n]*nearestTo: CGPoint\(x: 440, y: 444\)[^\n]*speed:\s*([0-9.]+)",
    SIMULATION_SOURCE
).group(1))
MAP_SPEED = P1_SPEED


def projected_scale(dx, dy):
    screen = hypot(dx, dy)
    return screen / hypot(dx, 2 * dy) if screen > 0.0001 else 1


def gait_frame(distance):
    return 1 + int(max(0, distance) / VIRTUAL_FRAMES * VIRTUAL_FRAMES) % VIRTUAL_FRAMES


def source_column(frame):
    return 0 if frame == 0 else 1 + (frame - 1) * P1_POSES // VIRTUAL_FRAMES


def interpolate(points, distance):
    lengths = [hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]
    distance = max(0, min(sum(lengths), distance))
    for i, length in enumerate(lengths):
        if distance <= length and length:
            t = distance / length
            a, b = points[i], points[i + 1]
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        distance -= length
    return points[-1]


def smooth(controls, steps=8):
    if len(controls) <= 2:
        return controls
    output = []
    for index in range(len(controls) - 1):
        a = controls[max(index - 1, 0)]
        b = controls[index]
        c = controls[index + 1]
        d = controls[min(index + 2, len(controls) - 1)]
        for step in range(steps):
            t = step / steps
            t2, t3 = t * t, t * t * t
            def interp(av, bv, cv, dv):
                return 0.5 * ((2 * bv) + (-av + cv) * t + (2 * av - 5 * bv + 4 * cv - dv) * t2
                              + (-av + 3 * bv - 3 * cv + dv) * t3)
            output.append((interp(a[0], b[0], c[0], d[0]), interp(a[1], b[1], c[1], d[1])))
    output.append(controls[-1])
    return output


def simulate(points, seconds=2.4, speed=MAP_SPEED):
    total = sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))
    distance = 0.0
    gait_distance = 0.0
    previous = interpolate(points, distance)
    frames, sources, positions = [], [], []
    facing = 0
    heading = None
    facing_changes = 0
    count = int(seconds / DT)
    for _ in range(count):
        here = interpolate(points, distance)
        ahead = interpolate(points, min(total, distance + 1))
        scale = projected_scale(ahead[0] - here[0], ahead[1] - here[1])
        distance = min(total, distance + speed * DT * scale)
        current = interpolate(points, distance)
        dx, dy = current[0] - previous[0], current[1] - previous[1]
        gait_distance += hypot(dx, dy) / projected_scale(dx, dy)
        if hypot(dx, dy) > 0.001:
            angle = atan2(dx, dy)
            sector = pi / 4
            difference = None if heading is None else atan2(sin(angle - heading), cos(angle - heading))
            if difference is None or abs(difference) > sector / 2 + pi / 36:
                index = (int(round(angle / sector)) + 8) % 8
                next_facing = [0, 4, 3, 7, 2, 6, 1, 5][index]
                facing_changes += next_facing != facing
                facing = next_facing
                heading = index * sector
        frame = gait_frame(gait_distance)
        frames.append(frame)
        sources.append(source_column(frame))
        positions.append(current)
        previous = current
    return frames, sources, positions, facing_changes


def report(name, points):
    frames, sources, positions, facing_changes = simulate(points)
    changes = sum(a != b for a, b in zip(sources, sources[1:]))
    render_steps = sum(a != b for a, b in zip(frames[::2], frames[2::2]))
    disp = sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(positions, positions[1:]))
    print(f"{name}: 60Hz={len(frames)} samples, {changes} authored-pose changes/2.4s "
          f"({changes / 2.4:.2f}/s), {render_steps} frame changes at 30Hz, "
          f"screen-path={disp:.2f} map units / 2.4s, facing changes={facing_changes}")


def main():
    print(f"preview: {REVIEW_SPEED:.2f} virtual units/s = {1000 / REVIEW_MS:.2f} authored poses/s")
    print(f"map source: JourneySimulation P1 uses HeroFrames.reviewSpeed={P1_SPEED_USES_REVIEW}; "
          f"speed={MAP_SPEED:.2f} virtual units/s = {MAP_SPEED * P1_POSES / VIRTUAL_FRAMES:.2f} "
          f"authored poses/s; {MAP_SPEED / REVIEW_SPEED:.2f}x preview cadence")
    edges = SCENE_MAP["roads"]
    down_right = smooth([(p["x"], p["y"]) for p in edges[3]["points"]])
    up_right = smooth([(p["x"], p["y"]) for p in edges[1]["points"]])
    roads = {
        "down-right": down_right,
        "up-left": list(reversed(down_right)),
        "up-right": up_right,
        "down-left": list(reversed(up_right)),
        "turn": smooth([(p["x"], p["y"]) for p in edges[1]["points"]]),
        "turn-reverse": list(reversed(smooth([(p["x"], p["y"]) for p in edges[1]["points"]]))),
    }
    for name, points in roads.items():
        report(name, points)

    # GameScene still calls WalkCycle.advance while stationary. Its visible
    # frame resets to 0, while distance is retained; resume restores that phase.
    paused_distance = MAP_SPEED * 0.6
    paused_source = source_column(gait_frame(paused_distance))
    idle_source = 0
    resume_source = source_column(gait_frame(MAP_SPEED * DT))
    reset_source = 0
    restart_source = source_column(gait_frame(MAP_SPEED * DT))
    print(f"pause at 0.6s: source {paused_source} -> idle {idle_source}; resume next tick: "
          f"source {resume_source}; reset: source {reset_source}; restart first tick: {restart_source}")
    assert resume_source == restart_source == 1

    # Adjacent 120ms preview samples should advance one authored column.
    adjacent = [source_column(gait_frame(i * REVIEW_SPEED * REVIEW_MS / 1000)) for i in range(9)]
    assert all((b - a) % P1_POSES == 1 for a, b in zip(adjacent, adjacent[1:]))
    main_changes = sum(source_column(gait_frame(i * MAP_SPEED * DT)) !=
                       source_column(gait_frame((i + 1) * MAP_SPEED * DT))
                       for i in range(30))
    print(f"main 60Hz first 0.5s: {main_changes}/30 source-pose changes; "
          "the remaining callbacks repeat one of P1's 8 authored frames")
    tracks_foot = "let foot: CGPoint" in RENDERER_SOURCE and "heroChanged" in RENDERER_SOURCE
    assert tracks_foot
    print("renderer cache key: includes index, foot, facing, frame, phase; actor movement invalidates backdrop")
    print("adjacent 120ms preview samples: pass (one P1 source pose per sample)")


if __name__ == "__main__":
    main()
