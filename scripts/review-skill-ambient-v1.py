"""Offline preview of the skill ambient light (Sources/Game/MeadowSkillAmbientLight.swift) on the review battle scene.
Left: sprite only (previous build). Right: with stage wash, floor pool + rim, reflection and glowing motes. Approximation of the UIKit drawing."""
import math, sys, io
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/battle-vfx'))
from skills import SPECS
base = ROOT / 'scripts/review-battle-effects-demo.py'
env = {'__file__': str(base)}
src = base.read_text().replace("'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',", "'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',")
exec(compile(src.split('\nframes=[]; traces=[]')[0], str(base), 'exec'), env)
W, H = env['W'], env['H']
plate, foreground, render, shadow = env['plate'], env['foreground'], env['render'], env['shadow']
hs, es, hx, hy, ex, ey, enemy = [env[k] for k in ['hs', 'es', 'hx', 'hy', 'ex', 'ey', 'enemy']]
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SHEETS = {k: Image.open(ROOT / f'Sources/Resources/Assets.xcassets/{v[0]}.imageset/{v[0]}.png').convert('RGBA') for k, v in SPECS.items()}
TONE = {'starlightPulse': (.46, .40, 1), 'rally': (1, .76, .30), 'sweep': (.42, .78, 1), 'dragonSoulWard': (.29, .67, 1), 'dragonScaleWard': (1, .55, .18)}
PEAK = {'starlightPulse': 12, 'rally': 14, 'sweep': 9, 'dragonSoulWard': 12, 'dragonScaleWard': 12}


def smooth(x): t = min(1, max(0, x)); return t * t * (3 - 2 * t)
def frac(i, s): return ((i * 73 + s * 37 + i * i * 11) % 101) / 100.0


def level(age, peak, dur):
    if age < 0 or age >= dur: return 0.0
    rise = smooth(age / max(.05, peak * .9)); fall = 1 - smooth((age - peak - .08) / max(.05, dur - peak - .08))
    return min(1, max(0, rise * (1 if age <= peak else fall)))


def motes(sid, age, dur, spread):
    out = []
    for i in range(16 if sid == "sweep" else 22):
        born = frac(i, 1) * dur * .55; life = .45 + .5 * frac(i, 2); t = (age - born) / life
        if not (0 <= t < 1): continue
        a0 = frac(i, 3) * 2 * math.pi; r0 = spread * (.15 + .85 * frac(i, 4)); x, y = math.cos(a0) * r0, math.sin(a0) * r0 * .6; size = 22 + 20 * frac(i, 5)
        if sid == 'starlightPulse': x *= 1 + .35 * t; y = y * (1 + .35 * t) - 8 * t
        elif sid in ('rally', 'dragonScaleWard'): y -= 46 * t * (.6 + frac(i, 6)); x += math.sin(t * 6 + i) * 6
        elif sid == 'sweep': x = spread * (.2 + t) * (1 if frac(i, 7) > .5 else .7); y = (frac(i, 8) - .5) * spread * 1.1 + 14 * t * t
        else: th = a0 + t * 3.2; x = math.cos(th) * r0; y = math.sin(th) * r0 * .5 - 40 * t
        if sid == 'starlightPulse': size *= .8
        al = math.sin(math.pi * t) ** .8
        if sid == 'starlightPulse': al *= .55 + .45 * math.sin(age * 22 + i * 2)
        out.append((x, y, size, 1.5 + 1.5 * frac(i, 9), min(1, max(0, al)), frac(i, 10) > .6))
    return out


def glow(buf, cx, cy, rx, ry, alpha, col):
    if alpha <= 0: return
    x0, x1 = int(max(0, cx - rx)), int(min(W, cx + rx + 1)); y0, y1 = int(max(0, cy - ry)), int(min(H, cy + ry + 1))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt(((xx + .5 - cx) / rx) ** 2 + ((yy + .5 - cy) / ry) ** 2)
    a = np.clip(1 - d, 0, 1) * min(1, alpha)
    buf[y0:y1, x0:x1] += a[..., None] * (np.array(col) * 255)


def sprite(buf, sid, f, rect, alpha, flip_ground=None):
    asset, n, fps, cw, ch, cols, _ = SPECS[sid]
    cell = SHEETS[sid].crop(((f % cols) * cw, (f // cols) * ch, (f % cols) * cw + cw, (f // cols) * ch + ch))
    a = np.asarray(cell).astype(float)
    layer = a[..., :3] * a[..., 3:] / 255 * alpha
    x0, y0 = rect
    if flip_ground is None:
        ys = slice(max(0, y0), min(H, y0 + ch)); xs = slice(max(0, x0), min(W, x0 + cw))
        buf[ys, xs] += layer[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
    else:
        g = flip_ground
        for row in range(ch):
            y = y0 + row
            if y >= g: continue
            yd = int(round(g + .30 * (g - y)))
            if 0 <= yd < H and yd < g + 90:
                xs = slice(max(0, x0), min(W, x0 + cw))
                buf[yd, xs] += layer[row, xs.start - x0:xs.stop - x0]


def scene(e, hero_clip='idle'):
    s = plate.copy()
    hero = render('idle', (e % 2.4) / 2.4)
    shadow(s, enemy, ex, ey, es); shadow(s, hero, hx, hy, hs)
    s.alpha_composite(hero.resize((round(256 * hs), round(256 * hs)), Image.Resampling.NEAREST), (round(hx), round(hy)))
    s.alpha_composite(enemy.resize((round(enemy.width * es), round(enemy.height * es)), Image.Resampling.NEAREST), (round(ex), round(ey)))
    s.alpha_composite(foreground)
    return np.asarray(s.convert('RGB')).astype(float)


def frame(sid, t, center, ground, ambient):
    asset, n, fps, cw, ch, cols, _ = SPECS[sid]
    dur = n / fps; buf = scene(t)
    col = TONE[sid]; f = min(n - 1, int(t * fps))
    lit = level(t, PEAK[sid] / fps, dur)
    anchor = (cw / 2, ch / 2); rect = (round(center[0] - anchor[0]), round(center[1] - anchor[1]))
    if ambient and lit > 0:
        buf *= 1 - lit * DIM * np.array([1.0, .96, .84])          # dim the stage so the light reads
        buf += lit * .03 * np.array(col) * 255
        glow(buf, center[0], center[1], max(W, cw) * .62, max(H, cw) * .52, lit * .16, col)
        glow(buf, center[0], ground - 2, cw * .62, 28, lit * .34, col)
    if t < dur:
        sprite(buf, sid, f, rect, 1.0)
        if ambient and lit > 0:
            sprite(buf, sid, f, rect, .16 * lit, flip_ground=ground)
            for (x, y, size, core, al, hot) in motes(sid, t, dur, cw * .36):
                px, py = center[0] + x, center[1] + y
                glow(buf, px, py, size * 1.5, size * 1.5, al * .8, col)
                c = (1, .96, .86) if hot else col
                buf[int(py - core / 2):int(py + core / 2 + 1), int(px - core / 2):int(px + core / 2 + 1)] += al * np.array(c) * 255
    return Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8))


DIM = float(sys.argv[2]) if len(sys.argv) > 2 else .26
CROP = (100, 120, 740, 600)
jobs = [('rally', (hx + 128 * hs, hy + 130 * hs), hy + 240 * hs), ('starlightPulse', (ex + 178 * es, ey + 140 * es), ey + 240 * es)]
for sid, center, ground in jobs:
    asset, n, fps = SPECS[sid][:3]
    frames = []
    for k in range(int((n / fps + .25) * 25)):
        t = k / 25.0
        a = frame(sid, t, center, ground, False).crop(CROP); b = frame(sid, t, center, ground, True).crop(CROP)
        c = Image.new('RGB', (a.width * 2 + 6, a.height)); c.paste(a, (0, 0)); c.paste(b, (a.width + 6, 0)); frames.append(c.resize((c.width * 3 // 4, c.height * 3 // 4)))
    frames[0].save(OUT / f'{sid}-ambient-before-after.gif', save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
    frames[min(len(frames) - 1, int(PEAK[sid] / fps * 25) + 1)].save(OUT / f'{sid}-ambient-peak.png')
    print(sid, len(frames))
