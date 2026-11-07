"""Healing sheets drawn from scratch (no reference to the old sheets): a sprout and fireflies, a rune circle with a leaf
helix, and a full life-bloom. Same pipeline as skills.py: hard masks, small palettes, closed-form motion, fixed particle ids.

Layout facts (see HealingEffectTier.canvasGroundAnchorY): the cell is registered on the receiver's feet, so the ground
line is at 100% (micro), 90% (standard) and 66% (strong) of the cell height; everything else rises above it.
"""
import math
import numpy as np
from pixelvfx import Grid, hx, smooth, clamp01, lerp, ease_out, ease_in, frac

# (id, asset, frames, fps, cell w, cell h, columns, grid scale) - cells match the size the sheets are drawn at on the party stage
SPECS = {
    'healMicro': ('BattleVFXHealingMicroSheet', 20, 20, 320, 320, 5, 2),
    'healStandard': ('BattleVFXHealingStandardSheet', 20, 20, 320, 268, 5, 2),
    'healStrong': ('BattleVFXHealingStrongSheet', 20, 20, 320, 320, 5, 2),
}
SIZES = {'healMicro': (160, 160), 'healStandard': (160, 134), 'healStrong': (160, 160)}

GR = [hx('#052b1a'), hx('#0b6a38'), hx('#17a455'), hx('#55dc86'), hx('#b4ffc8'), (255, 255, 255)]
LF = [hx('#1f7a2c'), hx('#4fb83a'), hx('#9be04a'), hx('#d6f78a')]          # leaf tones: shade, body, lit, rim


def tone(i, dim=0):
    return GR[max(0, min(5, i - dim))]


def leaf(g, x, y, length, width, ang, lit=2, dim=0):
    """Pointed leaf from its base (x, y) towards `ang`: dark outline, body, lit half and a mid rib."""
    c, s = math.cos(ang), math.sin(ang)

    def P(u, v): return (x + c * u - s * v, y + s * u + c * v)
    outline = g.poly([P(-0.8, 0), P(length * .28, -width / 2 - .9), P(length * .72, -width * .42 - .9), P(length + 1.2, 0), P(length * .72, width * .42 + .9), P(length * .28, width / 2 + .9)])
    body = g.poly([P(0, 0), P(length * .28, -width / 2), P(length * .72, -width * .42), P(length, 0), P(length * .72, width * .42), P(length * .28, width / 2)])
    upper = g.poly([P(0, 0), P(length * .28, -width / 2), P(length * .72, -width * .42), P(length, 0)])
    g.fill(outline, LF[0] if lit < 1 else GR[0])
    g.fill(body, LF[max(0, min(3, 1 - dim))])
    g.fill(upper, LF[max(0, min(3, 2 - dim))])
    g.fill(g.segment(P(1, 0), P(length * .85, 0), 1.0, 0.6), LF[3] if dim == 0 else LF[1])


def star(g, cx, cy, long, short, color, core=None):
    """Thin four-point glint: tapered spikes (long horizontal, shorter vertical) and a small bright core."""
    w = max(1.4, short * .9)
    for (dx, dy, L) in [(1, 0, long), (-1, 0, long), (0, 1, long * .72), (0, -1, long * .72)]:
        g.fill(g.segment((cx, cy), (cx + dx * L, cy + dy * L), w, 0.5), color)
    if core is not None: g.fill(g.disc(cx, cy, max(1.0, short * .8)), core)


def mote(g, x, y, size, col, hot=False):
    g.fill(g.diamond(x, y, size + .8, size + .8), col)
    if hot: g.fill(g.disc(x, y, max(.7, size * .45)), GR[5])


# ---------------------------------------------------------------- micro: sprout + fireflies + a chest sparkle
def micro(f, n=20):
    g = Grid(*SIZES['healMicro'])
    cx, gy = 80.0, 152.0
    fade = 1 - ease_in((f - 14) / 6.0)                       # everything thins out over the last frames
    dim = 0 if fade > .66 else 1 if fade > .33 else 2
    # ripple on the ground
    if 0 <= f <= 12:
        t = f / 12.0
        r = 6 + 30 * ease_out(t)
        m = g.ring(cx, gy, r - 1.6, r, 0.28)
        if t > .45: m &= g.dither(1 - (t - .45) / .55)
        g.fill(m, tone(3, dim))
        g.fill(g.ellipse(cx, gy, 7 * (1 - t) + 2, 2.2) & (t < .5), tone(4))
    # sprout: two leaves unfurl from the ground
    if 1 <= f <= 17:
        grow = ease_out((f - 1) / 6.0) * (1 - ease_in((f - 11) / 6.0))
        if grow > 0.05:
            g.fill(g.segment((cx, gy), (cx, gy - 16 * grow), 2.0, 1.4), LF[1])
            leaf(g, cx, gy - 12 * grow, 14 * grow, 7 * grow + 1, math.radians(-150), 2)
            leaf(g, cx, gy - 12 * grow, 14 * grow, 7 * grow + 1, math.radians(-30), 2)
    # fireflies rising out of the ground
    for i in range(8):
        born = 1 + int(frac(i, 1) * 7)
        age = f - born
        if 0 <= age < 11:
            t = age / 10.0
            x = cx + (frac(i, 2) - .5) * 52 + math.sin(t * 5 + i) * 5
            y = gy - 6 - ease_out(t) * (46 + 56 * frac(i, 3))
            size = (1.8 + 1.2 * frac(i, 4)) * (1 - .5 * ease_in(t))
            mote(g, x, y, size, tone(4 if t < .7 else 3, dim), hot=t < .5 and frac(i, 5) > .4)
    # sparkle at chest height
    if 3 <= f <= 17:
        k = smooth((f - 3) / 4.0) * (1 - smooth((f - 12) / 5.0))
        if k > .02:
            star(g, cx, 82, 12 * k + 2, 1.8 * k + .6, tone(4, dim), tone(5))
            g.fill(g.diamond(cx - 13 * k, 82 - 7 * k, 1.5, 1.5), tone(5))
            g.fill(g.diamond(cx + 12 * k, 82 + 8 * k, 1.3, 1.3), tone(4))
    return g


# ---------------------------------------------------------------- standard: rune circle + leaf helix + light column + bloom
def standard(f, n=20):
    g = Grid(*SIZES['healStandard'])
    cx, gy = 80.0, 120.0
    rise = ease_out(clamp01(f / 9.0))
    fade = 1 - ease_in((f - 12.5) / 6.5)
    dim = 0 if fade > .66 else 1 if fade > .33 else 2
    ringr = 52 * ease_out(clamp01(f / 5.0)) * (1 if f < 14 else 1 - ease_in((f - 14) / 5.0))
    # light column behind everything
    if f >= 2 and fade > 0:
        top = gy - 100 * rise
        col = g.ellipse(cx, (top + gy) / 2, 15, (gy - top) / 2 + 2) & (g.y < gy - 2)
        g.fill(col & g.dither(.09 * fade + .02), tone(2, dim))
        g.fill(g.ellipse(cx, (top + gy) / 2, 8, (gy - top) / 2) & (g.y < gy - 2) & g.dither(.20 * fade), tone(3, dim))
    # ground circle
    if ringr > 2:
        g.fill(g.ellipse(cx, gy, ringr, ringr * .28) & g.dither(.22 * max(.3, fade)), tone(1, dim))
        g.fill(g.ring(cx, gy, ringr - 1.8, ringr, 0.28), tone(3, dim))
        g.fill(g.ring(cx, gy, ringr * .62 - 1.2, ringr * .62, 0.28) & g.dither(.55), tone(2, dim))
        spin = f * 0.16
        for k in range(6):
            a = spin + k * math.pi / 3
            px, py = cx + math.cos(a) * ringr * .81, gy + math.sin(a) * ringr * .81 * .28
            g.fill(g.diamond(px, py, 2.6, 2.6), tone(4, dim))
    # vines (back half first so the front half overlaps the column)
    def vine(front):
        for k in range(2):
            phase = k * math.pi + f * 0.22
            smax = rise if f >= 2 else 0.0
            smin = ease_in((f - 13) / 7.0)
            if smax <= smin + 0.02: continue
            steps = 40
            pts = []
            for j in range(steps + 1):
                s = smin + (smax - smin) * j / steps
                if s < 0 or s > 1: continue
                depth = math.sin(phase + s * 6.2)
                x = cx + math.cos(phase + s * 6.2) * (21 - 8 * s)
                y = gy - 4 - s * 92
                pts.append((s, depth, x, y))
            for (s, d, x, y), (s2, d2, x2, y2) in zip(pts, pts[1:]):
                if (d >= 0) != front: continue
                g.fill(g.segment((x, y), (x2, y2), 2.6 - 1.0 * s, 2.4 - 1.0 * s2), LF[1 if front else 0])
            for j, (s, d, x, y) in enumerate(pts):
                if j % 5 != 2 or (d >= 0) != front: continue
                out = 0.0 if math.cos(phase + s * 6.2) >= 0 else math.pi
                ang = out + (-0.6 if out == 0.0 else 0.6) - 0.35 * (1 - s)
                size = (11 - 5 * s) * (1 if front else .85)
                leaf(g, x, y, size, size * .55, ang, 2 if front else 1, dim=0 if fade > .5 else 1)
    vine(False)
    vine(True)
    # bloom at the top of the column
    if f >= 7:
        k = smooth((f - 7) / 4.0) * (1 - smooth((f - 14) / 5.0))
        if k > .02:
            bx, by = cx, gy - 98 * rise + 4
            for j in range(5):
                a = -math.pi / 2 + (j - 2) * 0.62
                leaf(g, bx, by + 5, 17 * k, 8 * k + 1, a, 3)
            star(g, bx, by, 11 * k + 2, 1.7 * k + .6, tone(4, dim), tone(5))
    # rising motes
    for i in range(14):
        born = 3 + int(frac(i, 1) * 8)
        age = f - born
        if 0 <= age < 9:
            t = age / 8.0
            a = frac(i, 2) * 6.283
            x = cx + math.cos(a + t * 2.2) * (10 + 26 * frac(i, 3))
            y = gy - 8 - ease_out(t) * (30 + 70 * frac(i, 4))
            mote(g, x, y, (1.6 + 1.2 * frac(i, 5)) * (1 - .5 * t), tone(4 if t < .65 else 3, dim), hot=t < .4)
    return g


# ---------------------------------------------------------------- strong: rune array + pillar + life bloom + shock ring
def strong(f, n=20):
    g = Grid(*SIZES['healStrong'])
    cx, gy = 80.0, 105.0
    open_ = ease_out(clamp01(f / 6.0))
    fade = 1 - ease_in((f - 12.5) / 6.5)
    dim = 0 if fade > .66 else 1 if fade > .33 else 2
    R = 68 * open_ * (1 if f < 15 else 1 - ease_in((f - 15) / 4.5))
    # pillar of light
    if f >= 3 and fade > 0:
        h = 98 * ease_out(clamp01((f - 3) / 5.0))
        top = gy - h
        for lvl, w, col in [(.07, 22, 1), (.13, 14, 2), (.24, 7, 3)]:
            m = g.ellipse(cx, (top + gy) / 2, w, h / 2 + 1) & (g.y < gy)
            lvl_map = lvl * fade * (0.45 + 0.55 * np.clip((g.y - top) / max(1, h), 0, 1))
            g.fill(m & (g.bayer < lvl_map), tone(col, dim))
    # ground array: two rings, a dithered disc, radial leaf glyphs
    if R > 3:
        g.fill(g.ellipse(cx, gy, R, R * .34) & g.dither(.24 * max(.3, fade)), tone(1, dim))
        g.fill(g.ring(cx, gy, R - 2.2, R, 0.34), tone(3, dim))
        g.fill(g.ring(cx, gy, R * .72 - 1.4, R * .72, 0.34), tone(2, dim))
        g.fill(g.ring(cx, gy, R * .38 - 1.2, R * .38, 0.34), tone(3, dim))
        spin = f * 0.13
        for k in range(8):
            a = spin + k * math.pi / 4
            c, s = math.cos(a), math.sin(a)
            g.fill(g.diamond(cx + c * R * .86, gy + s * R * .86 * .34, 3.2, 2.2), tone(4, dim))
            g.fill(g.segment((cx + c * R * .42, gy + s * R * .42 * .34), (cx + c * R * .70, gy + s * R * .70 * .34), 2.0, 1.0), tone(2, dim))
    # shock ring racing outwards
    if 5 <= f <= 14:
        t = (f - 5) / 9.0
        r = 16 + 76 * ease_out(t)
        m = g.ring(cx, gy, r - 2.0, r, 0.34)
        if t > .4: m &= g.dither(1 - (t - .4) / .6)
        g.fill(m, tone(5 if t < .35 else 4, dim))
    # life bloom: a fan of leaves opening from the orb above the pillar
    if f >= 5:
        k = ease_out(clamp01((f - 5) / 5.0)) * (1 - ease_in((f - 13) / 7.0))
        if k > .02:
            ox, oy = cx, gy - 52
            for j in range(13):
                a = -math.pi / 2 + (j - 6) * 0.30
                L = (30 if j % 2 == 0 else 22) * k
                leaf(g, ox, oy, L, L * .42, a, 3 if j % 2 == 0 else 2, dim=0 if fade > .5 else 1)
            for j in range(4):
                a = math.radians(205 + j * 43) + (math.pi if j >= 2 else 0) * 0
                leaf(g, ox, oy + 4, 18 * k, 8 * k, math.radians([-20, 200, 8, 172][j]), 2)
            g.fill(g.disc(ox, oy, 8 * k + 2) & g.dither(.5), tone(2, dim))
            g.fill(g.disc(ox, oy, 5 * k + 1.2), tone(4))
            star(g, ox, oy, 20 * k + 3, 2.0 * k + .6, tone(5), tone(5))
    # leaf motes circling up the pillar
    for i in range(26):
        born = 3 + int(frac(i, 1) * 9)
        age = f - born
        if 0 <= age < 10:
            t = age / 9.0
            a = frac(i, 2) * 6.283 + t * 3.0
            rr = 12 + 34 * frac(i, 3)
            x = cx + math.cos(a) * rr
            y = gy - 6 - ease_out(t) * (26 + 78 * frac(i, 4)) + math.sin(a) * rr * .2
            if i % 3 == 0:
                leaf(g, x, y, 6.5 * (1 - .4 * t), 3.2, a + 1.2, 2, dim=0 if t < .6 else 1)
            else:
                mote(g, x, y, (1.5 + 1.2 * frac(i, 5)) * (1 - .45 * t), tone(4 if t < .6 else 3, dim), hot=t < .35)
    return g


GENERATORS = {'healMicro': micro, 'healStandard': standard, 'healStrong': strong}
