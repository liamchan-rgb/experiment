"""Offline preview of the continuous procedural skills (scripts/battle-vfx/procfx.py) on the review battle scene, 40 fps.
Soft glows + a bloom pass stand in for the game's stacked-glow drawing. Approximation, not a device capture."""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/battle-vfx'))
import procfx
base = ROOT / 'scripts/review-battle-effects-demo.py'
env = {'__file__': str(base)}
src = base.read_text().replace("'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',", "'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',")
exec(compile(src.split('\nframes=[]; traces=[]')[0], str(base), 'exec'), env)
W, H = env['W'], env['H']
plate, foreground, render, shadow = env['plate'], env['foreground'], env['render'], env['shadow']
hs, es, hx, hy, ex, ey, enemy = [env[k] for k in ['hs', 'es', 'hx', 'hy', 'ex', 'ey', 'enemy']]
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
FPS = 40


def scene(t):
    s = plate.copy(); hero = render('idle', (t % 2.4) / 2.4)
    shadow(s, enemy, ex, ey, es); shadow(s, hero, hx, hy, hs)
    s.alpha_composite(hero.resize((round(256 * hs), round(256 * hs)), Image.Resampling.NEAREST), (round(hx), round(hy)))
    s.alpha_composite(enemy.resize((round(enemy.width * es), round(enemy.height * es)), Image.Resampling.NEAREST), (round(ex), round(ey)))
    s.alpha_composite(foreground)
    return np.asarray(s.convert('RGB')).astype(float)


YY, XX = np.mgrid[0:H, 0:W]


def window(cx, cy, rx, ry):
    x0, x1 = int(max(0, cx - rx - 2)), int(min(W, cx + rx + 3)); y0, y1 = int(max(0, cy - ry - 2)), int(min(H, cy + ry + 3))
    return (x0, x1, y0, y1) if x1 > x0 and y1 > y0 else None


def glow(buf, cx, cy, rx, ry, col, a):
    w = window(cx, cy, rx, ry)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    d = np.sqrt(((XX[y0:y1, x0:x1] + .5 - cx) / rx) ** 2 + ((YY[y0:y1, x0:x1] + .5 - cy) / ry) ** 2)
    buf[y0:y1, x0:x1] += (np.clip(1 - d, 0, 1) ** 1.4 * min(1.0, a))[..., None] * np.array(col)


def block(buf, cx, cy, size, col, a):
    w = window(cx, cy, size, size)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    m = (np.abs(XX[y0:y1, x0:x1] + .5 - cx) <= size / 2) & (np.abs(YY[y0:y1, x0:x1] + .5 - cy) <= size / 2)
    buf[y0:y1, x0:x1][m] += np.array(col) * min(1.0, a)


def ring(buf, cx, cy, rx, ry, wd, col, a):
    w = window(cx, cy, rx + wd, ry + wd)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    d = np.sqrt(((XX[y0:y1, x0:x1] + .5 - cx) / rx) ** 2 + ((YY[y0:y1, x0:x1] + .5 - cy) / ry) ** 2)
    band = np.clip(1 - np.abs(d - 1) * min(rx, ry) / max(wd, 1.0), 0, 1)
    buf[y0:y1, x0:x1] += (band * min(1.0, a))[..., None] * np.array(col)


def diamond(buf, cx, cy, rx, ry, col, a):
    w = window(cx, cy, rx, ry)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    m = (np.abs(XX[y0:y1, x0:x1] + .5 - cx) / max(rx, .5) + np.abs(YY[y0:y1, x0:x1] + .5 - cy) / max(ry, .5)) <= 1
    buf[y0:y1, x0:x1][m] += np.array(col) * min(1.0, a)


def disc(buf, cx, cy, r, col, a):
    w = window(cx, cy, r, r)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    d = np.sqrt((XX[y0:y1, x0:x1] + .5 - cx) ** 2 + (YY[y0:y1, x0:x1] + .5 - cy) ** 2)
    m = np.clip(r - d + .5, 0, 1)[..., None] * min(1.0, a)
    buf[y0:y1, x0:x1] = buf[y0:y1, x0:x1] * (1 - m) + np.array(col) * m


def seg(buf, x1, y1, x2, y2, wd, col, a):
    L = math.hypot(x2 - x1, y2 - y1); n = max(2, int(L / 3))
    for k in range(n + 1):
        u = k / n; taper = 1 - .5 * u
        x, y = x1 + (x2 - x1) * u, y1 + (y2 - y1) * u
        glow(buf, x, y, wd * 2.2, wd * 2.2, col, a * .35); block(buf, x, y, max(1.2, wd * taper), col, a)


def draw(buf, prims):
    for p in prims:
        k = p[0]
        if k == 'g': glow(buf, p[1], p[2], p[3], p[4], p[5], p[6])
        elif k == 'b': block(buf, p[1], p[2], p[3], p[4], p[5])
        elif k == 'r': ring(buf, *p[1:7], p[7]) if False else ring(buf, p[1], p[2], p[3], p[4], p[5], p[6], p[7])
        elif k == 's': seg(buf, *p[1:])
        elif k == 'c': disc(buf, *p[1:])
        elif k == 'd': diamond(buf, *p[1:])
        elif k == 'f': buf += p[2] * np.array(p[1])


def bloom(buf, strength=.26):
    im = Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8))
    bright = np.clip(buf - 190, 0, 255)
    b = Image.fromarray(bright.astype(np.uint8)).filter(ImageFilter.GaussianBlur(9))
    b2 = Image.fromarray(bright.astype(np.uint8)).filter(ImageFilter.GaussianBlur(22))
    return np.clip(buf + strength * np.asarray(b).astype(float) + strength * .7 * np.asarray(b2).astype(float), 0, 255)


hero_chest = (hx + 128 * hs + 5 * .83, hy + 170 * hs); hero_foot = (hx + 128 * hs, hy + 240 * hs)
enemy_chest = (ex + 178 * es, ey + 140 * es); enemy_foot = (ex + 178 * es, ey + 240 * es)
CASES = {
    'starlightPulse': dict(targets=[(enemy_chest, enemy_foot)], center=enemy_chest, ground=enemy_foot[1]),
    'sweep': dict(targets=[(enemy_chest, enemy_foot)], center=enemy_chest, ground=enemy_foot[1]),
    'rally': dict(targets=[(hero_chest, hero_foot)], center=hero_chest, ground=hero_foot[1]),
    'dragonSoulWard': dict(targets=[(hero_chest, hero_foot)], center=hero_chest, ground=hero_foot[1]),
    'dragonScaleWard': dict(targets=[(hero_chest, hero_foot)], center=hero_chest, ground=hero_foot[1]),
}
for c in CASES.values(): c.update(caster=hero_chest, casterFoot=hero_foot)
CROP = (int(hx - 90), int(hy - 90), int(hx + 560), int(hy + 290))
sel = sys.argv[2].split(',') if len(sys.argv) > 2 else list(CASES)
for sid in sel:
    dur = procfx.SPEC[sid][0]; geo = CASES[sid]; frames = []
    n = int((dur + .15) * FPS)
    for k in range(n):
        t = k / FPS
        buf = scene(t)
        lit = procfx.smooth(t / .15) * (1 - procfx.smooth((t - dur + .25) / .4))
        buf *= 1 - .24 * lit * np.array([1.0, .96, .86])
        draw(buf, procfx.GENERATORS[sid](t, geo))
        buf = bloom(buf)
        frames.append(Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8)).crop(CROP))
    im = [f.resize((f.width * 2 // 3, f.height * 2 // 3), Image.LANCZOS).quantize(96, dither=Image.Dither.NONE) for f in frames]
    im[0].save(OUT / f'{sid}-procedural.gif', save_all=True, append_images=im[1:], duration=25, loop=0, optimize=True)
    pk = int(max(procfx.SPEC[sid][1], .5) * FPS) + 3
    frames[min(len(frames) - 1, pk)].save(OUT / f'{sid}-procedural-peak.png')
    print(sid, len(frames))
