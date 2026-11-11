"""Offline preview of the three generic skill layers (charge-up on the caster inside the cast motion, target reaction, afterglow)
on top of the sprite and the ambient light. Left: previous build. Right: with the three layers. Approximation of the UIKit drawing."""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'scripts/review-skill-ambient-v1.py').read_text()
head = src.split('\nDIM = ')[0].replace('if t < dur:', 'if 0 <= t < dur:')
head = head.replace("ROOT = Path(__file__).resolve().parents[1]", f"ROOT = Path({str(ROOT)!r})", 1).replace("sys.path.insert(0, str(ROOT / 'scripts/battle-vfx'))", f"sys.path.insert(0, {str(ROOT / 'scripts/battle-vfx')!r})")
env = {'__file__': str(ROOT / 'scripts/review-skill-ambient-v1.py'), '__name__': 'preview', 'DIM': 0.26}
sys.argv = [sys.argv[0], sys.argv[1]] + sys.argv[2:]
env['DIM'] = 0.26
exec(compile(head, 'ambient', 'exec'), env)
globals().update({k: env[k] for k in ['W', 'H', 'SPECS', 'TONE', 'PEAK', 'frame', 'glow', 'hx', 'hy', 'hs', 'ex', 'ey', 'es', 'frac', 'smooth', 'OUT', 'level']})
SKILLS = {'starlightPulse': dict(caster='hero', targets=['enemy'], impact=1.0, support=False), 'rally': dict(caster='hero', targets=['hero'], impact=0.9, support=True)}
WARD = {'rally', 'dragonSoulWard', 'dragonScaleWard'}


def ease_out(x): t = min(1, max(0, x)); return 1 - (1 - t) ** 3


def charge(p):
    if not 0 < p <= 1: return None
    ms = []
    for i in range(12):
        a0 = frac(i, 3) * 2 * math.pi; start = 70 + 50 * frac(i, 4); t = min(1, max(0, (p - .35 * frac(i, 1)) / (1 - .35 * frac(i, 1))))
        r = start * (1 - ease_out(t)); sw = a0 + t * 2.4
        al = min(1, p * 3) * (.5 + .5 * frac(i, 2)) * (1 - smooth((t - .9) / .1))
        ms.append((math.cos(sw) * r, math.sin(sw) * r * .7, 14 + 10 * frac(i, 5), 1.5 + 1.5 * frac(i, 9), al, frac(i, 10) > .55))
    return smooth(p) * .9, 12 + 58 * (1 - ease_out(p)), min(1, p * 2.5) * (1 - .4 * p), ms


def reaction(sid, age):
    ward = sid in WARD
    if not 0 <= age < (1.7 if ward else .6): return None
    ms = []
    if ward:
        for i in range(8):
            th = frac(i, 3) * 2 * math.pi + age * (2.2 + frac(i, 4)); rise = frac(i, 5) * 30 - 14 + math.sin(age * 3 + i) * 5
            ms.append((math.cos(th) * 34, math.sin(th) * 12 + rise, 14, 1.8 + frac(i, 9), min(1, age / .25) * (1 - smooth((age - 1.1) / .6)), frac(i, 10) > .6))
        return (1 - smooth(age / .4)) * .8, smooth(age / .2) * (1 - smooth((age - 1.1) / .6)), age * 2.2, ms
    for i in range(9):
        life = .3 + .3 * frac(i, 2); t = age / life
        if t >= 1: continue
        a = frac(i, 3) * 2 * math.pi; d = (14 + 40 * frac(i, 4)) * ease_out(t)
        ms.append((math.cos(a) * d, math.sin(a) * d * .8 - 6 * t, 12 + 8 * frac(i, 5), 1.6 + 1.4 * frac(i, 9), (1 - t) ** .8, frac(i, 10) > .5))
    return (1 - age / .6) ** 2 * .9, 0, 0, ms


def afterglow(age, spread):
    if not 0 <= age < .9: return None
    t = age / .9; ms = []
    for i in range(10):
        a0 = frac(i, 3) * 2 * math.pi; r = spread * (.2 + .8 * frac(i, 4))
        ms.append((math.cos(a0) * r + math.sin(age * 2 + i) * 4, math.sin(a0) * r * .5 - age * (14 + 22 * frac(i, 6)), 12 + 8 * frac(i, 5), 1.4 + 1.2 * frac(i, 9), (1 - t) * (.4 + .6 * frac(i, 2)), False))
    return (1 - t) ** 1.5 * .5, ms


def rim(buf, c, rx, ry, alpha, col):
    if alpha <= .01: return
    ys, xs = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xs + .5 - c[0]) / rx) ** 2 + ((ys + .5 - c[1]) / ry) ** 2)
    m = (np.abs(d - 1) * min(rx, ry) < 1.0)
    buf[m] += min(1, alpha) * np.array(col) * 255


def specks(buf, ms, o, strength, col):
    for (dx, dy, r, core, al, hot) in ms:
        if al <= .01: continue
        px, py = o[0] + dx, o[1] + dy
        glow(buf, px, py, r * 1.4, r * 1.4, al * strength, col)
        c = (1, .96, .86) if hot else col
        y0, x0 = int(py - core / 2), int(px - core / 2)
        if 0 <= y0 < H - 4 and 0 <= x0 < W - 4: buf[y0:y0 + int(core) + 1, x0:x0 + int(core) + 1] += al * np.array(c) * 255


hero_chest = (hx + 128 * hs + 5 * .83, hy + 170 * hs); hero_foot = (hx + 128 * hs, hy + 240 * hs)
enemy_chest = (ex + 178 * es, ey + 140 * es); enemy_foot = (ex + 178 * es, ey + 240 * es)
POINTS = {'hero': (hero_chest, hero_foot), 'enemy': (enemy_chest, enemy_foot)}


def stage_frame(sid, t, layers):
    cfg = SKILLS[sid]; asset, n, fps = SPECS[sid][:3]; dur = n / fps; peak = PEAK[sid] / fps
    started = cfg['impact'] if cfg['support'] else max(0, cfg['impact'] - peak)
    center, ground = (POINTS[cfg['targets'][0]][0], POINTS[cfg['targets'][0]][1][1])
    img = frame(sid, t - started, center, ground, True)
    if not layers: return img
    buf = np.asarray(img).astype(float); col = TONE[sid]
    cstart = max(0, started - .5)
    if started - cstart > .12 and cstart <= t < started:
        c = charge((t - cstart) / (started - cstart))
        if c:
            lvl, rr, ra, ms = c; chest, foot = POINTS[cfg['caster']]
            glow(buf, chest[0], chest[1], 52, 52, lvl * .5, col); rim(buf, foot, rr, rr * .3, ra * .7, col); specks(buf, ms, chest, .75, col)
    impact = cfg['impact']
    for tg in cfg['targets']:
        r = reaction(sid, t - impact)
        if not r: continue
        g, aura, spin, ms = r; chest, foot = POINTS[tg]
        glow(buf, chest[0], chest[1], 46, 66, g * .45, col)
        if aura > .01:
            glow(buf, chest[0], chest[1], 34, 62, aura * .16, col); rim(buf, foot, 40, 12, aura * .5, col)
            for k in range(4):
                th = spin + k * math.pi / 2; px, py = int(foot[0] + math.cos(th) * 40), int(foot[1] + math.sin(th) * 12)
                buf[py - 1:py + 2, px - 1:px + 2] += aura * np.array((1, .96, .86)) * 255
        specks(buf, ms, chest, .6, col)
    ag = afterglow(t - (started + dur), SPECS[sid][3] * .3)
    if ag:
        pool, ms = ag; glow(buf, center[0], ground - 2, SPECS[sid][3] * .5, 22, pool, col); specks(buf, ms, center, .6, col)
    return Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8))


CROP = (100, 120, 740, 600)
for sid in SKILLS:
    cfg = SKILLS[sid]; asset, n, fps = SPECS[sid][:3]; dur = n / fps
    started = cfg['impact'] if cfg['support'] else max(0, cfg['impact'] - PEAK[sid] / fps)
    end = max(started + dur + .9, cfg['impact'] + (1.7 if sid in WARD else .6)) + .1
    fr = []
    for k in range(int(end * 25)):
        t = k / 25.0
        a = stage_frame(sid, t, False).crop(CROP); b = stage_frame(sid, t, True).crop(CROP)
        c = Image.new('RGB', (a.width * 2 + 6, a.height)); c.paste(a, (0, 0)); c.paste(b, (a.width + 6, 0)); fr.append(c.resize((c.width * 3 // 4, c.height * 3 // 4)))
    fr[0].save(OUT / f'{sid}-stagecraft-before-after.gif', save_all=True, append_images=fr[1:], duration=40, loop=0, optimize=True)
    pk = int(cfg['impact'] * 25) + 4
    fr[min(len(fr) - 1, pk)].save(OUT / f'{sid}-stagecraft-impact.png')
    print(sid, len(fr))
