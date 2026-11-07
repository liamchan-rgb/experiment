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


def ring(buf, cx, cy, rx, ry, wd, col, a, rot=0.0):
    R_ = max(rx, ry)
    w = window(cx, cy, R_ + wd, R_ + wd) if rot else window(cx, cy, rx + wd, ry + wd)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    dx, dy = XX[y0:y1, x0:x1] + .5 - cx, YY[y0:y1, x0:x1] + .5 - cy
    if rot: dx, dy = dx * math.cos(rot) + dy * math.sin(rot), -dx * math.sin(rot) + dy * math.cos(rot)
    d = np.sqrt((dx / max(rx, .5)) ** 2 + (dy / max(ry, .5)) ** 2)
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


def poly(buf, pts, col, a):
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    w = window((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (max(xs) - min(xs)) / 2 + 1, (max(ys) - min(ys)) / 2 + 1)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    from PIL import ImageDraw
    m = Image.new('L', (x1 - x0, y1 - y0), 0); ImageDraw.Draw(m).polygon([(q[0] - x0, q[1] - y0) for q in pts], fill=255)
    mm = (np.asarray(m).astype(float) / 255)[..., None] * min(1.0, a)
    buf[y0:y1, x0:x1] = buf[y0:y1, x0:x1] * (1 - mm) + np.array(col) * mm


def egl(buf, cx, cy, rx, ry, ang, col, a):
    R_ = max(rx, ry)
    w = window(cx, cy, R_, R_)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    dx, dy = XX[y0:y1, x0:x1] + .5 - cx, YY[y0:y1, x0:x1] + .5 - cy
    u = dx * math.cos(ang) + dy * math.sin(ang); v = -dx * math.sin(ang) + dy * math.cos(ang)
    d = np.sqrt((u / max(rx, .5)) ** 2 + (v / max(ry, .5)) ** 2)
    buf[y0:y1, x0:x1] += (np.clip(1 - d, 0, 1) ** 1.6 * min(1.0, a))[..., None] * np.array(col)


def arc(buf, cx, cy, rx, ry, a0, a1, wd, col, a):
    w = window(cx, cy, rx + wd, ry + wd)
    if not w or a <= 0.003: return
    x0, x1, y0, y1 = w
    X, Y = XX[y0:y1, x0:x1] + .5 - cx, YY[y0:y1, x0:x1] + .5 - cy
    d = np.sqrt((X / rx) ** 2 + (Y / ry) ** 2)
    band = np.clip(1 - np.abs(d - 1) * min(rx, ry) / max(wd, 1.0), 0, 1)
    ang = (np.arctan2(Y / ry, X / rx) - a0) % (2 * math.pi)
    span = a1 - a0; edge = np.clip(np.minimum(ang, span - ang) / .12, 0, 1)
    m = band * np.where(ang <= span, edge, 0)
    buf[y0:y1, x0:x1] += (m * min(1.0, a))[..., None] * np.array(col)


def ribbon(buf, pts, ws, col, a, mode, soft):
    if len(pts) < 2 or a <= 0.003: return
    pad = max(ws) / 2 + soft * 3 + 2
    x0 = int(max(0, min(p[0] for p in pts) - pad)); x1 = int(min(W, max(p[0] for p in pts) + pad + 1))
    y0 = int(max(0, min(p[1] for p in pts) - pad)); y1 = int(min(H, max(p[1] for p in pts) + pad + 1))
    if x1 <= x0 or y1 <= y0: return
    from PIL import ImageDraw
    SS = 2
    m = Image.new('L', ((x1 - x0) * SS, (y1 - y0) * SS), 0); d = ImageDraw.Draw(m)
    for (xa, ya), (xb, yb), wa, wb in zip(pts, pts[1:], ws, ws[1:]):
        n = max(1, int(math.hypot(xb - xa, yb - ya) / 0.8))
        for k in range(n + 1):
            u = k / n; x = (xa + (xb - xa) * u - x0) * SS; y = (ya + (yb - ya) * u - y0) * SS; r = max(.3, (wa + (wb - wa) * u) / 2) * SS
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    m = m.resize((x1 - x0, y1 - y0), Image.LANCZOS).filter(ImageFilter.GaussianBlur(max(.4, soft * .5)))
    mm = (np.asarray(m).astype(float) / 255)[..., None] * min(1.0, a)
    reg = buf[y0:y1, x0:x1]
    if mode == 'add': buf[y0:y1, x0:x1] = reg + mm * np.array(col)
    else: buf[y0:y1, x0:x1] = reg * (1 - mm) + np.array(col) * mm


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
        elif k == 'r': ring(buf, *p[1:])
        elif k == 'e': egl(buf, *p[1:])
        elif k == 'a': arc(buf, *p[1:])
        elif k == 'k': ribbon(buf, *p[1:])
        elif k == 's': seg(buf, *p[1:])
        elif k == 'p': poly(buf, p[1], p[2], p[3])
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
        dm, dt = procfx.DIM[sid]
        buf *= 1 - dm * lit * (1 - np.array(dt) * .0) * np.array(dt)
        draw(buf, procfx.GENERATORS[sid](t, geo))
        buf = bloom(buf)
        frames.append(Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8)).crop(CROP))
    im = [f.resize((f.width * 2 // 3, f.height * 2 // 3), Image.LANCZOS).quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    im[0].save(OUT / f'{sid}-procedural.gif', save_all=True, append_images=im[1:], duration=25, loop=0, optimize=True)
    pk = int(max(procfx.SPEC[sid][1], .5) * FPS) + 3
    frames[min(len(frames) - 1, pk)].save(OUT / f'{sid}-procedural-peak.png')
    print(sid, len(frames))
