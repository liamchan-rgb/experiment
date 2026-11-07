"""Hand-built pixel-art frames for the party skill effects (see pixelvfx.py).

Frame counts, fps, cell sizes and anchors are the game's existing PartySkillVFXSpec values, so only the sheet PNGs change.
"""
import math
import numpy as np
from pixelvfx import Grid, hx, smooth, clamp01, lerp, ease_out, ease_in, frac

# (id, asset, frames, fps, cell_w, cell_h, columns, grid scale)
SPECS = {
    'starlightPulse': ('MeadowBattleVFXStarlightPulse', 20, 16, 344, 344, 5, 2),
    'rally': ('MeadowBattleVFXRally', 20, 12, 256, 256, 5, 2),
    'sweep': ('MeadowBattleVFXSweep', 20, 20, 339, 287, 5, 2),
    'dragonSoulWard': ('MeadowBattleVFXDragonSoulWard', 20, 12, 256, 256, 5, 2),
    'dragonScaleWard': ('MeadowBattleVFXDragonScaleWard', 20, 20, 256, 256, 4, 2),
}

# ---------------------------------------------------------------- starlight pulse
V = [hx('#140d40'), hx('#2c21a0'), hx('#5d4be6'), hx('#9185ff'), hx('#cbc4ff'), (255, 255, 255)]


def needle(g, cx, cy, length, thick, ang, sy=1.0):
    """Thin pointed spike (a long diamond) along `ang`."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(cx + ca * length, cy + sa * length * sy), (cx - sa * thick, cy + ca * thick * sy),
           (cx - ca * length, cy - sa * length * sy), (cx + sa * thick, cy - ca * thick * sy)]
    return g.poly(pts)


def starlight(f, n=20):
    g = Grid(172, 172)
    cx, cy, sy = 86.0, 86.0, 0.82            # the pulse sits on the enemy node: slightly flattened
    gather = clamp01(f / 10.0)
    b = f - 10
    # 1. a faint three-armed spiral of dust that winds in as the star charges (dotted, brightness by distance)
    if f <= 11:
        arm_fade = 1 - ease_in((f - 7) / 5.0) if f > 7 else 1.0
        for arm in range(3):
            for i in range(26):
                a = arm * 2.094 + i * 0.21 + f * 0.30
                r = (10 + i * 2.7) * (1.0 - 0.45 * ease_in(gather))
                if i / 26 > ease_out(clamp01(f / 4.0)) * 1.05: continue
                px, py = cx + math.cos(a) * r, cy + math.sin(a) * r * sy
                if arm_fade <= 0: continue
                col = V[4] if i < 6 else V[3] if i < 14 else V[2] if i < 21 else V[1]
                g.fill(g.disc(px, py, 1.0 if i % 3 else 1.5), col)
    # 2. star motes spiral in with a three-step trail
    for i in range(16):
        delay = int(frac(i, 1) * 4)
        for step in range(3, -1, -1):
            ff = f - step
            if ff < delay or ff > 11: continue
            u = clamp01((ff - delay) / (11.0 - delay))
            r = (46 + 40 * frac(i, 2)) * (1 - ease_in(u) * 0.97)
            a = i * 2.399 + u * (2.2 + 1.6 * frac(i, 3))
            px, py = cx + math.cos(a) * r, cy + math.sin(a) * r * sy
            size = [1.8, 1.3, 1.0, 0.7][step] * (1.3 if i % 3 == 0 else 1.0)
            if step == 0:
                g.fill(g.diamond(px, py, size * 1.5, size * 1.5), V[5])
            else:
                g.fill(g.disc(px, py, size), [None, V[4], V[3], V[2]][step])
    # 3. burst: two shock rings, tapering rays
    if b >= 0:
        for k, (delay, grow, col) in enumerate([(0, 76, V[3]), (2, 54, V[2])]):
            bb = b - delay
            if bb < 0: continue
            ring_r = 8 + grow * ease_out(bb / 9.0)
            thick = max(1.0, 3.4 * (1 - bb / 10.0))
            fade = 1 - ease_in((bb - 4) / 6.0)
            if fade > 0:
                m = g.ring(cx, cy, ring_r - thick, ring_r, sy)
                if fade < 1: m &= g.dither(fade)
                g.fill(m, col)
        rays = clamp01(b / 3.0) * (1 - ease_in((b - 3) / 6.0))
        if rays > 0:
            for k in range(12):
                a = k * math.pi / 6 + math.pi / 12
                long = (86, 40)[k % 2] if k % 3 else 62
                L = long * rays
                p0 = (cx + math.cos(a) * 8, cy + math.sin(a) * 8 * sy)
                p1 = (cx + math.cos(a) * L, cy + math.sin(a) * L * sy)
                g.fill(g.segment(p0, p1, 3.2, 0.6), V[3])
                g.fill(g.segment(p0, p1, 1.4, 0.3), V[5])
    # 4. the core: stepped glow halo + crossed needles
    if f <= 15:
        core = 2.0 + 9 * smooth(gather) + (9 * math.sin(math.pi * clamp01(b / 5.0)) if b >= 0 else 0)
        g.fill(g.disc(cx, cy, core * 2.1) & g.dither(0.28), V[1])
        g.fill(g.disc(cx, cy, core * 1.5) & g.dither(0.5), V[2])
        g.fill(g.disc(cx, cy, core * 1.05), V[3])
        for ang, ln, th, col in [(0, 3.4, 0.28, V[4]), (math.pi / 2, 3.4, 0.28, V[4]), (math.pi / 4, 1.9, 0.18, V[3]), (3 * math.pi / 4, 1.9, 0.18, V[3])]:
            g.fill(needle(g, cx, cy, core * ln * 1.5, max(1.1, core * th), ang, sy), col)
        g.fill(g.disc(cx, cy, max(1.5, core * 0.62)), V[4])
        g.fill(g.disc(cx, cy, max(1.0, core * 0.34)), V[5])
    # 5. four diagonal shards leave the burst
    if b >= 3:
        s = ease_out((b - 3) / 6.0)
        fade = 1 - ease_in((b - 3) / 7.0)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            r = 18 + 70 * s
            px, py = cx + math.cos(a) * r, cy + math.sin(a) * r * sy
            if fade > 0.12:
                tail = (cx + math.cos(a) * (r - 22 * fade), cy + math.sin(a) * (r - 22 * fade) * sy)
                g.fill(g.segment(tail, (px, py), 3.4 * fade, 0.8), V[3])
                g.fill(g.diamond(px, py, 4.5 * fade, 4.5 * fade), V[5])
    # 6. falling sparkles after the burst
    if b >= 5:
        for i in range(12):
            life = 5 + int(frac(i, 4) * 4)
            age = b - 5 - int(frac(i, 5) * 3)
            if 0 <= age < life:
                a = i * 2.399
                r = 20 + 52 * frac(i, 6)
                px = cx + math.cos(a) * r
                py = cy + math.sin(a) * r * sy + age * 2.2
                bright = age < life - 2
                g.fill(g.disc(px, py, 1.2 if bright else 0.7), V[4] if bright else V[2])
    return g


# ---------------------------------------------------------------- sweep
B = [hx('#0d2478'), hx('#2459d8'), hx('#4f9bff'), hx('#9fd8ff'), hx('#e4f6ff'), (255, 255, 255)]


def shade(i, shift):
    return B[max(0, min(5, i - shift))]


def sweep(f, n=20):
    g = Grid(170, 144)
    cx, cy, rx, ry = 34.0, 72.0, 100.0, 42.0                # the blade runs along this ellipse, bulging toward the target (right)
    a_start, a_end = math.radians(-104), math.radians(100)
    dim = 0 if f < 13 else 1 if f < 16 else 2

    def crescent(scale, width, head_delay, tail_delay, tone):
        head = ease_out(clamp01((f - head_delay) / 7.0))
        tail = ease_in(clamp01((f - 8 - tail_delay) / 9.0))
        if head <= 0 or tail >= head: return
        ang = np.arctan2((g.y - cy) / ry, (g.x - cx) / rx)
        s = ((ang - a_start) % (2 * math.pi)) / (a_end - a_start)
        rn = np.hypot((g.x - cx) / rx, (g.y - cy) / ry)
        px_per = math.sqrt(rx * ry)
        th = (width * np.power(np.sin(np.pi * np.clip(s, 0, 1)), 0.75) + 1.0) / px_per
        outer = scale
        m = (s >= tail) & (s <= head) & (s <= 1.0) & (rn <= outer) & (rn >= outer - th)
        u = np.clip((outer - rn) / np.maximum(th, 1e-6), 0, 1)
        lead = s > head - 0.05
        for lo, hi, idx in [(0.0, 0.16, 5), (0.16, 0.42, 4), (0.42, 0.66, 3), (0.66, 0.86, 2), (0.86, 1.01, 1)]:
            g.fill(m & (u >= lo) & (u < hi), shade(max(1, idx - tone), dim))
        g.fill(m & lead & (u < 0.66), shade(5, dim))

    crescent(1.0, 11.0, 0, 0, 0)
    crescent(0.82, 5.0, 1, 1, 1)
    crescent(0.66, 3.0, 2, 2, 1)
    # impact burst on the leading tip
    tip = (cx + rx * math.cos(a_end), cy + ry * math.sin(a_end))
    k = f - 7
    if 0 <= k <= 6:
        grow = ease_out(k / 3.0) * (1 - ease_in((k - 3) / 4.0))
        for j in range(6):
            a = a_end + (j - 2.5) * 0.5
            L = (20 if j % 2 == 0 else 12) * grow
            g.fill(g.segment(tip, (tip[0] + math.cos(a) * L, tip[1] + math.sin(a) * L), 3.0, 0.5), shade(4, dim))
        g.fill(g.disc(tip[0], tip[1], 5.0 * grow), shade(5, dim))
    # sparks thrown off the blade
    for i in range(14):
        born = 2 + int(frac(i, 1) * 9)
        age = f - born
        if 0 <= age < 6:
            sp = lerp(0.3, 0.98, frac(i, 2))
            ang = a_start + (a_end - a_start) * sp
            ox, oy = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
            nx, ny = math.cos(ang) * 0.8, math.sin(ang) * 0.8
            d = 3 + age * (3.4 + 2.5 * frac(i, 3))
            px, py = ox + nx * d, oy + ny * d + age * age * 0.45
            size = 1.6 - age * 0.18
            g.fill(g.diamond(px, py, size + .6, size + .6) if age < 3 else g.disc(px, py, max(.6, size)), shade(5 if age < 3 else 3, dim))
    return g


# ---------------------------------------------------------------- rally (golden war-cry)
G = [hx('#3a1c00'), hx('#9a5200'), hx('#e08a0a'), hx('#ffc23a'), hx('#fff0a0'), (255, 255, 255)]


def rally(f, n=20):
    g = Grid(128, 128)
    cx, cy = 64.0, 64.0
    b = f - 8
    gather = clamp01(f / 8.0)
    # 1. two counter-rotating rings of motes that tighten
    if f <= 9:
        k = 1 - 0.40 * ease_in(gather)
        vis = clamp01((f + 1) / 3.0) * (1 - ease_in((f - 6) / 4.0))
        if vis > 0:
            for i in range(12):
                a = i * math.pi / 6 + f * 0.13
                r = 52 * k
                px, py = cx + math.cos(a) * r, cy + math.sin(a) * r
                s = (2.0 if i % 3 == 0 else 1.3) * (0.6 + 0.4 * vis)
                g.fill(g.diamond(px, py, s * 1.3, s * 1.3) if i % 3 == 0 else g.disc(px, py, s), G[4] if i % 3 == 0 else G[3])
            for i in range(8):
                a = i * math.pi / 4 - f * 0.19 + 0.4
                r = 26 * k
                g.fill(g.disc(cx + math.cos(a) * r, cy + math.sin(a) * r, 1.4 * (0.6 + 0.4 * vis)), G[2])
            g.fill(g.ring(cx, cy, 40 * k - 0.6, 40 * k + 0.6) & g.dither(0.5 * vis), G[2])
    # 2. starburst: 12 rays, long and short alternating, with a travelling shock ring
    if b >= 0:
        grow = ease_out(b / 3.0)
        life = 1 - ease_in((b - 4) / 6.0)
        if life > 0:
            for k in range(12):
                a = k * math.pi / 6
                long = 60 if k % 2 == 0 else 38
                L = long * grow * (0.55 + 0.45 * life)
                p0 = (cx + math.cos(a) * 7, cy + math.sin(a) * 7)
                p1 = (cx + math.cos(a) * L, cy + math.sin(a) * L)
                g.fill(g.segment(p0, p1, 5.0 if k % 2 == 0 else 3.6, 0.6), G[3] if k % 2 == 0 else G[2])
                g.fill(g.segment(p0, p1, 2.2 if k % 2 == 0 else 1.6, 0.3), G[5] if k % 2 == 0 else G[4])
        rr = 12 + 46 * ease_out(clamp01(b / 8.0))
        fade = 1 - ease_in((b - 3) / 7.0)
        if fade > 0:
            m = g.ring(cx, cy, rr - 2.2, rr)
            if fade < 1: m &= g.dither(fade)
            g.fill(m, G[3])
    # 3. the core: stepped halo + four-point star
    if f <= 16:
        core = 2.0 + 6.5 * smooth(gather) + (6.5 * math.sin(math.pi * clamp01(b / 5.0)) if b >= 0 else 0)
        g.fill(g.disc(cx, cy, core * 2.0) & g.dither(0.3), G[1])
        g.fill(g.disc(cx, cy, core * 1.45) & g.dither(0.55), G[2])
        g.fill(g.disc(cx, cy, core * 1.0), G[3])
        g.fill(g.segment((cx - core * 2.3, cy), (cx + core * 2.3, cy), 1.6, 0.4), G[4])
        g.fill(g.segment((cx, cy - core * 2.3), (cx, cy + core * 2.3), 1.6, 0.4), G[4])
        g.fill(g.disc(cx, cy, max(1.2, core * 0.55)), G[5])
    # 4. the ring re-forms from sparks and drifts out
    if b >= 6:
        k = b - 6
        for i in range(14):
            a = i * math.pi / 7 + 0.2
            r = 30 + k * 3.6 + 8 * frac(i, 1)
            fade = 1 - ease_in(k / 6.0)
            if fade > 0.1:
                g.fill(g.disc(cx + math.cos(a) * r, cy + math.sin(a) * r - k * 0.8, 1.6 * fade + 0.4), G[4] if i % 2 else G[3])
    return g


# ---------------------------------------------------------------- dragon scale ward (golden scales around a rune)
R = [hx('#3a0808'), hx('#8c1a0a'), hx('#d4480f'), hx('#ff8a1e'), hx('#ffc93a'), hx('#fff0a0'), (255, 255, 255)]


def rot_diamond(g, cx, cy, rx, ry, ang):
    """Diamond with half-width rx and half-height ry whose long axis points along `ang`."""
    ca, sa = math.cos(ang), math.sin(ang)
    def P(px, py): return (cx + px * ca - py * sa, cy + px * sa + py * ca)
    return [P(ry, 0), P(0, rx), P(-ry, 0), P(0, -rx)], P


def plate(g, cx, cy, size, ang, tone=0):
    """One scale plate: facets, a dark rim and a highlight pip."""
    if size <= 0.15: return
    pts, P = rot_diamond(g, cx, cy, 7.4 * size, 13.0 * size, ang)
    body = g.poly(pts)
    g.fill(body, R[1])
    half = g.poly([pts[0], pts[1], pts[2], P(0, 0)])                     # lit half
    g.fill(half, R[3 - tone])
    inner, _ = rot_diamond(g, cx, cy, 4.2 * size, 8.2 * size, ang)
    g.fill(g.poly(inner) & body, R[4 - tone])
    ridge = g.segment(P(11 * size, 0), P(-11 * size, 0), 1.4 * size, 0.7 * size)
    g.fill(ridge & body, R[5])
    rim = body & ~g.poly(rot_diamond(g, cx, cy, 6.1 * size, 11.4 * size, ang)[0])
    g.fill(rim, R[0])


def scales(f, n=20):
    g = Grid(128, 128)
    cx, cy = 64.0, 72.0
    pulse = smooth(f / 10.0) * (1 - ease_in((f - 14) / 5.0))
    flash = max(0.0, 1 - abs(f - 12) / 2.2)
    # 1. two crowns of scale plates fan out above the rune (back crown smaller and darker), pointing away from it
    for row, (scale0, dist0, tone, count) in enumerate([(0.86, 44, 1, 9), (1.12, 31, 0, 7)]):
        for k in range(count):
            born = 2 + abs(k - count // 2) + row * 2
            grow = ease_out(clamp01((f - born) / 4.0))
            if f > 13: grow *= 1 - ease_in((f - 13 - abs(k - count // 2) * 0.4) / 5.0)
            if grow <= 0: continue
            phi = math.radians(-100 + k * (200.0 / (count - 1)))           # fan angle, 0 = straight up
            d = dist0 + (3.0 * flash) + (12 * ease_in((f - 13) / 6.0))
            px = cx + math.sin(phi) * d * 1.05
            py = cy - 6 - math.cos(phi) * d * 0.80
            ang = math.atan2(py - (cy - 6), px - cx)
            plate(g, px, py, scale0 * grow * (1.0 + 0.1 * flash), ang, tone)
    # 2. the rune diamond with a glowing glyph
    if f >= 1:
        k = ease_out(clamp01(f / 6.0)) * (1 - ease_in((f - 16) / 3.0))
        if k > 0.1:
            halo = 1.0 + 0.2 * flash
            g.fill(g.disc(cx, cy, 21 * k * halo) & g.dither(0.12 + 0.2 * pulse), R[2])
            g.fill(g.disc(cx, cy, 15 * k * halo) & g.dither(0.25 + 0.3 * pulse), R[3])
            g.fill(g.diamond(cx, cy, 12.5 * k, 18 * k), R[0])
            g.fill(g.diamond(cx, cy, 10.6 * k, 15.8 * k), R[2])
            g.fill(g.diamond(cx, cy, 8.2 * k, 12.2 * k), R[4] if pulse > 0.55 else R[3])
            glyph = R[0]
            g.fill(g.segment((cx, cy - 9 * k), (cx, cy + 9 * k), 1.6, 1.6), glyph)
            g.fill(g.segment((cx - 4.6 * k, cy - 3 * k), (cx, cy + 1 * k), 1.6, 1.6), glyph)
            g.fill(g.segment((cx + 4.6 * k, cy - 3 * k), (cx, cy + 1 * k), 1.6, 1.6), glyph)
            g.fill(g.segment((cx - 3.4 * k, cy + 4.5 * k), (cx, cy + 7.5 * k), 1.6, 1.6), glyph)
            g.fill(g.segment((cx + 3.4 * k, cy + 4.5 * k), (cx, cy + 7.5 * k), 1.6, 1.6), glyph)
            g.fill(g.disc(cx, cy - 6 * k, 1.4 * k), R[6])
    # 3. flash at the peak: rays + ring
    if flash > 0:
        for i in range(8):
            a = i * math.pi / 4 + math.pi / 8
            L = (62 if i % 2 == 0 else 40) * flash
            g.fill(g.segment((cx + math.cos(a) * 14, cy + math.sin(a) * 14), (cx + math.cos(a) * L, cy + math.sin(a) * L), 3.4, 0.6), R[5])
        rr = 18 + 34 * (1 - flash)
        g.fill(g.ring(cx, cy, rr - 2, rr) & g.dither(0.35 + 0.65 * flash), R[4])
    # 4. embers rise from the scales
    for i in range(18):
        born = 5 + int(frac(i, 1) * 8)
        age = f - born
        life = 7
        if 0 <= age < life:
            a = i * 2.399
            r = 18 + 30 * frac(i, 2)
            px = cx + math.cos(a) * r
            py = cy + 12 + math.sin(a) * r * 0.5 - age * (3.0 + frac(i, 3) * 2.0)
            big = age < life - 3
            g.fill(g.diamond(px, py, 2.2 if big else 1.2, 2.8 if big else 1.6), R[5] if age < 2 else R[4] if big else R[2])
    return g


# ---------------------------------------------------------------- dragon soul ward (a spirit dragon coils round its ally)
D = [hx('#0a1450'), hx('#1b3fb8'), hx('#3d7dff'), hx('#7fb8ff'), hx('#c4e6ff'), (255, 255, 255)]


def soul(f, n=20):
    g = Grid(128, 128)
    cx, cy = 66.0, 70.0
    sy = 0.62
    appear = clamp01((f - 1) / 6.0)
    coil = ease_in(clamp01((f - 8) / 4.0))
    b = f - 12
    orb = 2.0 + 5.5 * smooth(f / 10.0) + (6.0 * math.sin(math.pi * clamp01(b / 5.0)) if b >= 0 else 0)

    def draw_core():
        if f > 16: return
        g.fill(g.disc(cx, cy, orb * 2.2) & g.dither(0.22), D[1])
        g.fill(g.disc(cx, cy, orb * 1.6) & g.dither(0.5), D[2])
        g.fill(g.disc(cx, cy, orb * 1.1), D[3])
        g.fill(g.disc(cx, cy, max(1.4, orb * 0.7)), D[4])
        g.fill(g.disc(cx, cy, max(1.0, orb * 0.38)), D[5])

    segs = []
    if 1 <= f <= 14:
        count = 34
        length = int(8 + (count - 8) * appear)
        head_theta = -1.2 + 0.50 * f
        for i in range(length):
            th = head_theta - i * 0.125
            R0 = (56 - 10 * ease_out(clamp01((f - 2) / 10.0)) - 36 * coil) * (1 + 0.08 * math.sin(i * 0.45 + f * 0.3))
            lift = math.sin(th + 0.8) * 7
            x = cx + math.cos(th) * R0
            y = cy + math.sin(th) * R0 * sy + lift * (1 - coil)
            w = 16.0 * (1 - i / (length + 6)) ** 1.1 + 2.0
            segs.append((i, th, x, y, w))
        vanish = ease_in(clamp01((f - 12) / 2.5))
        segs = [s_ for s_ in segs if s_[0] < len(segs) * (1 - vanish) + 0.001]

    def draw_dragon(front):
        for i, th, x, y, w in reversed(segs):
            if (math.sin(th) >= -0.05) != front: continue
            g.fill(g.disc(x, y, w / 2 + 1.0), D[0])
        for i, th, x, y, w in reversed(segs):
            if (math.sin(th) >= -0.05) != front: continue
            g.fill(g.disc(x, y, w / 2), D[1] if i % 5 == 0 else D[2])
            g.fill(g.disc(x - 0.4, y - w * 0.18, max(0.7, w / 2 - 1.6)), D[3])
            if i % 3 == 0:                                                      # belly scales
                g.fill(g.disc(x + 0.3, y + w * 0.22, max(0.5, w / 5)), D[4])
            if i % 2 == 0 and i > 1:                                            # dorsal spines on the outer side
                nx, ny = math.cos(th), math.sin(th) * sy
                g.fill(g.diamond(x + nx * (w / 2 + 1.6), y + ny * (w / 2 + 1.6) - 0.8, 1.5, 2.2), D[4])
        if front and segs and (math.sin(segs[0][1]) >= -0.05):
            i, th, x, y, w = segs[0]
            tx, ty = -math.sin(th), math.cos(th) * sy
            ang = math.atan2(ty, tx)
            ca, sa = math.cos(ang), math.sin(ang)
            def P(a, b): return (x + a * ca - b * sa, y + a * sa + b * ca)
            upper = g.poly([P(13, -1.0), P(6, -6.0), P(-4, -6.2), P(-6, -1.0), P(6, 0.4)])
            lower = g.poly([P(11, 2.6), P(6, 0.8), P(-3, 1.2), P(-3, 4.4), P(4, 5.2)])
            for m_ in (upper, lower): g.fill(m_ & ~m_, D[0])
            g.fill(g.poly([P(14.2, -1.6), P(6, -7.4), P(-5, -7.4), P(-7.4, -1.0), P(6, 1.2)]), D[0])
            g.fill(g.poly([P(12.6, 3.4), P(6, 0.2), P(-4.2, 0.6), P(-4.2, 5.6), P(4, 6.4)]), D[0])
            g.fill(upper, D[2]); g.fill(upper & g.disc(*P(2, -3.6), 3.2), D[3])
            g.fill(lower, D[1])
            g.fill(g.segment(P(-1, -5.0), P(-12, -10.0), 2.4, 0.8), D[4])      # horns
            g.fill(g.segment(P(-3, 3.6), P(-12.0, 7.4), 2.0, 0.7), D[4])
            g.fill(g.diamond(*P(11.8, -2.4), 1.2, 1.2), D[5])                  # nostril glint
            g.fill(g.disc(*P(3.2, -3.2), 1.5), D[5])                           # glowing eye
            g.fill(g.segment(P(6, 0.6), P(12.5, 0.6), 1.0, 1.0), D[0])         # mouth line

    draw_dragon(False)
    draw_core()
    draw_dragon(True)
    if b >= 0:
        grow = ease_out(b / 2.5) * (1 - ease_in((b - 2.5) / 3.5))
        for k in range(10):
            a = k * math.pi / 5 + 0.15
            L = (58 if k % 2 == 0 else 34) * grow
            g.fill(g.segment((cx + math.cos(a) * 9, cy + math.sin(a) * 9), (cx + math.cos(a) * L, cy + math.sin(a) * L), 3.2, 0.5), D[4])
        rr = 10 + 46 * ease_out(b / 7.0)
        fade = 1 - ease_in((b - 2) / 5.0)
        if fade > 0:
            m = g.ring(cx, cy, rr - 2, rr, 0.62)
            if fade < 1: m &= g.dither(fade)
            g.fill(m, D[3])
    if b >= 1:
        for i in range(20):
            age = b - 1 - int(frac(i, 1) * 3)
            life = 6
            if 0 <= age < life:
                a = i * 2.399
                r = 12 + 34 * frac(i, 2)
                px = cx + math.cos(a) * r
                py = cy + math.sin(a) * r * 0.6 - age * (2.6 + frac(i, 3) * 2)
                g.fill(g.disc(px, py, 1.5 if age < life - 2 else 0.8), D[4] if age < life - 2 else D[2])
    return g


GENERATORS = {'starlightPulse': starlight, 'sweep': sweep, 'rally': rally, 'dragonScaleWard': scales, 'dragonSoulWard': soul}
