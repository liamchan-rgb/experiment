#!/usr/bin/env python3
"""Offline review: P1 walk with uniform vs foot-locked pose timing, plus idle breathing.

Mirrors GaitTiming.footLocked / frame(at:) and HeroBreathing from Sources/Game.
Ground scrolls at the real campaign speed (reviewSpeed 25 x3, projected metric),
so sole slipping shows against the ground. Offline composite, not a device capture.
Usage: python3 -I scripts/review-gait-timing.py <out-dir>
"""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'Art/Review/P1/gait-timing-v1')
gait = json.loads((ROOT / 'Sources/Resources/hero-gait.json').read_text())
atlas = Image.open(ROOT / 'Sources/Resources/Assets.xcassets/Hero1Directions.imageset/Hero1Directions.png').convert('RGBA')
DIRS = [(0, 1), (-1, 0), (0, -1), (1, 0), (1, 1), (-1, 1), (-1, -1), (1, -1)]
SPEED = 25 * 3            # HeroFrames.reviewSpeed x JourneySimulation.movementSpeedMultiplier
SCALE = 2                 # review pixels per world point (sprite 64pt -> 128px)
FPS = 50

def foot_locked(min_stride=12, strength=0.6):
    rows = []
    for d in range(8):
        soles = [[(f[0] * 64, f[1] * 64) for f in gait['heroes'][0][d][1 + 3 * p]['feet'][:2]] for p in range(8)]
        vx, vy = DIRS[d]; n = math.hypot(vx, vy); ux, uy = vx / n, vy / n; metric = math.hypot(ux, 2 * uy)
        planted = []
        for p in range(8):
            a, b = soles[p], soles[(p + 1) % 8]
            planted.append(max(0, max(-((b[i][0] - a[i][0]) * ux + (b[i][1] - a[i][1]) * uy) for i in range(2))) * metric)
        total = sum(planted)
        if total < min_stride: rows.append([3.0] * 8); continue
        avg = total / 8; c = [min(max(x, avg * .45), avg * 1.8) for x in planted]
        sc = [x * 24 / sum(c) for x in c]; bl = [3 + (x - 3) * strength for x in sc]; s = sum(bl)
        rows.append([x * 24 / s for x in bl])
    return rows

def pose_at(distance, row):
    local = math.fmod(distance, 24) + 1e-9
    for p in range(8):
        if local < row[p] or p == 7: return p
        local -= row[p]

def cell(facing, column):
    r = facing % 4
    return atlas.crop((column * 256, r * 256, column * 256 + 256, r * 256 + 256)).resize((128, 128), Image.NEAREST)

def ground(w, h, ox, oy):
    g = Image.new('RGBA', (w, h), (122, 140, 72, 255)); d = ImageDraw.Draw(g)
    step = 8 * SCALE
    for x in range(-step, w + step, step):
        xx = int(x - ox % step); d.line([(xx, 0), (xx, h)], fill=(104, 122, 60, 255), width=1)
    for y in range(-step, h + step, step):
        yy = int(y - oy % step); d.line([(0, yy), (w, yy)], fill=(104, 122, 60, 255), width=1)
    return g

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    locked = foot_locked(); uniform = [[3.0] * 8 for _ in range(8)]
    facings = [(1, '左 left'), (0, '下 down'), (3, '右 right')]
    W, H = 168, 150; seconds = 3.2
    font = ImageFont.load_default()
    for candidate in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                      '/System/Library/Fonts/PingFang.ttc']:
        try: font = ImageFont.truetype(candidate, 13); break
        except OSError: pass
    frames = []
    for i in range(int(seconds * FPS)):
        t = i / FPS
        canvas = Image.new('RGBA', (W * 2 + 24 + W, H * 3 + 26), (28, 34, 30, 255)); dr = ImageDraw.Draw(canvas)
        dr.text((10, 4), '旧：均匀时序', fill=(230, 220, 190), font=font)
        dr.text((W + 18, 4), '新：按脚底重分配', fill=(230, 220, 190), font=font)
        dr.text((2 * W + 30, 4), '待机呼吸 ×2', fill=(230, 220, 190), font=font)
        for row, (facing, label) in enumerate(facings):
            vx, vy = DIRS[facing]; scale = math.hypot(vx, vy) / math.hypot(vx, 2 * vy)
            screen = SPEED * scale * t                 # world points travelled on screen
            distance = SPEED * t                       # projected-metric walk distance
            ux, uy = vx / math.hypot(vx, vy), vy / math.hypot(vx, vy)
            for colIndex, rows in enumerate([uniform, locked]):
                g = ground(W, H, screen * ux * SCALE, screen * uy * SCALE)
                pose = pose_at(distance, rows[facing])
                g.alpha_composite(cell(facing, 1 + pose), (W // 2 - 64, H - 128 - 6))
                canvas.alpha_composite(g, (6 + colIndex * (W + 12), 22 + row * H))
            dr.text((10, 26 + row * H), label, fill=(255, 255, 255), font=font)
        # Idle breathing at 2x review scale (amplitude 1.2%, period 3.4 s), anchored at y=0.125.
        breath = 0.5 - 0.5 * math.cos(t / 3.4 * 2 * math.pi)
        ys = 1 + 0.012 * breath
        idle = atlas.crop((0, 0, 256, 256))
        h = round(256 * ys); scaled = idle.resize((256, h), Image.NEAREST)
        box = Image.new('RGBA', (W, H * 3), (122, 140, 72, 255))
        anchor = H * 3 - 40                            # anchor line (y = 0.125 of the cell)
        box.alpha_composite(scaled, (W // 2 - 128, anchor - round(h * 0.875)))
        ImageDraw.Draw(box).line([(0, anchor - 22), (W, anchor - 22)], fill=(255, 230, 160, 120))
        canvas.alpha_composite(box, (2 * W + 24, 22))
        frames.append(canvas.convert('RGB'))
    frames[0].save(OUT / 'gait-timing-normal.gif', save_all=True, append_images=frames[1:], duration=1000 // FPS, loop=0, optimize=True)
    frames[0].save(OUT / 'gait-timing-still.png')
    (OUT / 'timing.json').write_text(json.dumps({'footLockedWindows': locked, 'speed': SPEED, 'fps': FPS,
        'note': 'offline composite of Hero1Directions cells; not a device capture'}, indent=2) + '\n')
    print('wrote', OUT)

if __name__ == '__main__':
    main()
