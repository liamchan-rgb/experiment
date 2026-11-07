"""Continuous procedural skill effects: the way the dragon-flame demo gets its smoothness.

Every effect is a closed-form function of time that returns a list of primitives (soft glows, small hard blocks, rings,
segments). Trails are the same path sampled at delayed times, so motion is continuous at any frame rate; every element
carries a soft additive glow, and a bloom pass (or its stacked-glow approximation in the game) removes the pixel edges.

Primitives (stage points, y grows downward):
  ('g', x, y, rx, ry, rgb, alpha)            soft radial glow
  ('b', x, y, size, rgb, alpha)              small hard square (accent)
  ('r', x, y, rx, ry, width, rgb, alpha[, rot])  ring on an ellipse (optionally rotated by rot)
  ('s', x1, y1, x2, y2, width, rgb, alpha)   segment (glow along it + bright core)
  ('d', x, y, rx, ry, rgb, alpha)            hard diamond (scale plates)
  ('k', pts, widths, rgb, alpha, mode, soft)  smooth tapered ribbon along a curve; mode 'add' (light) or 'mix' (solid, normal blend); soft = edge softness in points
  ('e', x, y, rx, ry, angle, rgb, alpha)      elongated soft glow rotated by `angle` (rays, glints, spark streaks)
  ('a', x, y, rx, ry, a0, a1, width, rgb, alpha)  arc of an ellipse
  ('p', [(x, y), ...], rgb, alpha)           solid polygon, normal blending (heads, fins)
  ('c', x, y, r, rgb, alpha)                 solid disc with normal blending (keeps dark, saturated colour; body of the dragon)
Geometry `geo`: dict(caster=(x,y chest), casterFoot=(x,y), targets=[(chest, foot), ...], center=(x,y), ground=y).
`t` is seconds since the skill started; `impact` is when it lands (peak), `duration` the total length.
"""
import math

SPEC = {  # id: (duration, impact, support)
    'starlightPulse': (1.6, 0.75, False),
    'rally': (1.67, 0.0, True),
    'sweep': (1.0, 0.45, False),
    'dragonSoulWard': (2.0, 0.0, True),
    'dragonScaleWard': (1.0, 0.0, True),
}
TONE = {
    'starlightPulse': [(255, 255, 255), (222, 212, 255), (160, 136, 255), (96, 70, 235), (44, 26, 150)],
    'rally': [(255, 250, 215), (255, 213, 96), (240, 150, 30), (170, 84, 12)],
    'sweep': [(255, 255, 255), (190, 232, 255), (92, 170, 255), (36, 86, 200)],
    'dragonSoulWard': [(235, 250, 255), (130, 210, 255), (56, 140, 255), (24, 70, 190)],
    'dragonScaleWard': [(255, 246, 205), (255, 190, 90), (240, 120, 36), (160, 60, 18)],
}


def frac(i, salt): return ((i * 73 + salt * 37 + (i * i) * 11) % 101) / 100.0
def clamp01(x): return min(1.0, max(0.0, x))
def smooth(x): t = clamp01(x); return t * t * (3 - 2 * t)
def ease_out(x): t = clamp01(x); return 1 - (1 - t) ** 3
def ease_in(x): t = clamp01(x); return t * t
def lerp(a, b, t): return a + (b - a) * t
def lerp2(a, b, t): return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


def glint(out, x, y, long, thick, col, a, rot=0.0):
    """Thin four-point glint: tapered segments plus a core glow."""
    for k in range(4):
        ang = rot + k * math.pi / 2
        L = long * (1.0 if k % 2 == 0 else 0.62)
        out.append(('s', x, y, x + math.cos(ang) * L, y + math.sin(ang) * L, thick, col, a))
    out.append(('g', x, y, long * .35, long * .35, col, a * .8))


# how far the stage is dimmed while the skill is on, and the tint of the dimming: (amount, rgb multiplier)
DIM = {'starlightPulse': (.34, (.80, .76, 1.0)), 'rally': (.24, (1.0, .94, .8)), 'sweep': (.26, (.82, .9, 1.0)),
       'dragonSoulWard': (.32, (.74, .88, 1.0)), 'dragonScaleWard': (.26, (1.0, .9, .76))}
MAG, CYAN, GOLD = (255, 128, 226), (130, 224, 255), (255, 232, 160)


def ell(cx, cy, rx, ry, a): return cx + math.cos(a) * rx, cy + math.sin(a) * ry


def sigil(out, cx, cy, R, ratio, t, env, cols, glyphs=12, spin=1.0):
    """Rotating floor sigil: double ring, ticks, a hexagram, glyph dots and a soft disc (projected onto the floor)."""
    if env <= .01: return
    c1, c2, c3 = cols
    out.append(('g', cx, cy, R * 1.12, R * 1.12 * ratio, c2, .30 * env))
    out.append(('r', cx, cy, R, R * ratio, 2.4, c1, .85 * env))
    out.append(('r', cx, cy, R * .9, R * .9 * ratio, 1.2, c2, .6 * env))
    out.append(('r', cx, cy, R * .58, R * .58 * ratio, 1.5, c1, .7 * env))
    for k in range(glyphs):
        a = spin * t * .6 + k * 2 * math.pi / glyphs
        x1, y1 = ell(cx, cy, R * .9, R * .9 * ratio, a); x2, y2 = ell(cx, cy, R * 1.0, R * ratio, a)
        out.append(('s', x1, y1, x2, y2, 1.6, c1, .8 * env))
        if k % 2 == 0:
            gx, gy = ell(cx, cy, R * .79, R * .79 * ratio, a + math.pi / glyphs)
            out.append(('b', gx, gy, 3.2, c3, .9 * env))
    for tri in (0, 1):
        base = -spin * t * .45 + tri * math.pi / 3
        pts = [ell(cx, cy, R * .86, R * .86 * ratio, base + j * 2 * math.pi / 3) for j in range(3)]
        for j in range(3):
            (xa, ya), (xb, yb) = pts[j], pts[(j + 1) % 3]
            out.append(('s', xa, ya, xb, yb, 1.4, c2, .65 * env))
    out.append(('g', cx, cy, R * .3, R * .3 * ratio, c3, .35 * env))


def tone_at(skill, u):
    """u in 0..1 from hot core to cool tail."""
    T = TONE[skill]
    return T[min(len(T) - 1, int(u * (len(T) - 0.01)))]


# ------------------------------------------------------------------ starlight pulse: a comet of star dust
def starlight(t, geo):
    out = []; C = geo['caster']; CF = geo['casterFoot']; T, TF = geo['targets'][0]; imp = SPEC['starlightPulse'][1]
    V = TONE['starlightPulse']; helix = [V[1], MAG, CYAN]
    # floor sigil under the caster while the comet is born
    sig = smooth(t / .2) * (1 - smooth((t - .42) / .25))
    sigil(out, CF[0], CF[1] - 2, 66, .3, t, sig, (V[2], V[3], V[1]), 12, 1.2)
    if t < .5:
        for i in range(18):
            ph = frac(i, 1); u = (t * .9 + ph) % 1.0
            x = CF[0] + (frac(i, 2) - .5) * 80; y = CF[1] - 6 - u * 120
            al = sig * math.sin(math.pi * u) ** .7
            out.append(('g', x, y, 7, 7, V[2], .6 * al)); out.append(('b', x, y, 2.2, V[0], al))

    def path(tt):
        s = ease_in(clamp01(tt / imp)) ** .8
        x, y = lerp2(C, T, s)
        return x, y - 70 * math.sin(math.pi * s) * (1 - .3 * s), s

    if t < imp + .02:
        hx, hy, _ = path(t)
        N = 46
        for i in range(N - 1, -1, -1):
            tt = t - i * .013
            if tt < 0: continue
            x, y, s = path(tt); x2, y2, _ = path(tt + .006)
            dx, dy = x2 - x, y2 - y; L = math.hypot(dx, dy) or 1.0; nx, ny = -dy / L, dx / L
            u = i / N; w = (15 * (1 - u) ** .8 + 1.6) * (.45 + .55 * clamp01(tt * 7))
            lat = 4.5 * u * math.sin(tt * 22 + i * .5); cx, cy = x + nx * lat, y + ny * lat
            if i % 3 == 0:
                col = (V[3], MAG, CYAN)[(i // 3) % 3]
                out.append(('g', cx, cy, w * 3.6, w * 3.6, col, .09 * (1 - u)))          # nebula puffs
            out.append(('g', cx, cy, w * 2.1, w * 2.1, V[3], .16 * (1 - .5 * u)))
            out.append(('c', cx, cy, w * 1.02, V[4], .6 * (1 - .4 * u)))
            out.append(('c', cx, cy, w * .7, V[3], .75 * (1 - .3 * u)))
            out.append(('g', cx, cy, w * 1.1, w * 1.1, V[2], .5 * (1 - u)))
            for k in range(3):                                                       # three strands twisting round the core
                ang = tt * 18 + i * .35 + k * 2.094
                off = w * .95 + 2
                px = cx + nx * math.cos(ang) * off; py = cy + ny * math.cos(ang) * off + math.sin(ang) * off * .35
                if math.sin(ang) > -.2:
                    out.append(('g', px, py, 4.2, 4.2, helix[k], .65 * (1 - u)))
                    out.append(('b', px, py, 1.9, V[0], .9 * (1 - u)))
        for i in range(30):                                                          # shed star dust
            tb = frac(i, 1) * imp * .95
            if not 0 <= t - tb < .55: continue
            tt = t - tb; x, y, _ = path(tb); r = tt / .55
            x += (frac(i, 2) - .5) * 40 * r; y += (frac(i, 3) - .3) * 40 * r + 30 * r * r
            col = (V[0], GOLD, MAG, CYAN)[i % 4]; k = 1 - r
            glint(out, x, y, 6 + 5 * frac(i, 4), 1.1, col, .9 * k, tt * 4 + i)
        fade = clamp01((imp - t) / .05)
        out.append(('g', hx, hy, 60, 60, V[3], .34 * fade))
        out.append(('r', hx, hy, 22 + 3 * math.sin(t * 25), 22 + 3 * math.sin(t * 25), 1.6, V[2], .55 * fade))
        out.append(('g', hx, hy, 26, 26, V[2], .6 * fade)); out.append(('c', hx, hy, 9, V[1], .95 * fade))
        out.append(('g', hx, hy, 13, 13, V[0], .95 * fade)); out.append(('b', hx, hy, 5, V[0], fade))
        glint(out, hx, hy, 38 + 4 * math.sin(t * 20), 2.6, V[0], fade, t * 3)
        glint(out, hx, hy, 24, 1.8, V[1], .8 * fade, t * 3 + .785)
        out.append(('s', hx - 70, hy, hx + 70, hy, 1.6, V[1], .35 * fade))
        for k in range(6):
            a = t * 9 + k * math.pi / 3; rr = 22 + 5 * math.sin(t * 6 + k)
            out.append(('b', hx + math.cos(a) * rr, hy + math.sin(a) * rr * .6, 3, V[0], .9 * fade))
    a = t - imp
    if a >= 0:
        cx, cy = T
        if a < .2: out.append(('f', V[2], .14 * math.exp(-a * 18)))
        out.append(('g', cx, cy, 150 * (.5 + ease_out(a / .35)), 150 * (.5 + ease_out(a / .35)), V[3], .4 * (1 - ease_in(a / .7))))
        out.append(('g', cx, cy, 52, 52, V[2], .5 * (1 - ease_in(a / .3)))); out.append(('g', cx, cy, 20, 20, V[1], .6 * (1 - ease_in(a / .2))))
        # radiating light rays
        for k in range(28):
            ang = k * 2 * math.pi / 28 + a * .5
            L = (70 + 80 * frac(k, 2)) * ease_out(a / .14) * (1 - ease_in((a - .08) / .55))
            if L > 2: out.append(('s', cx, cy, cx + math.cos(ang) * L, cy + math.sin(ang) * L, 2.4 * (1 - a / .65), (V[2], MAG, CYAN, V[1])[k % 4], .6 * (1 - a / .65)))
        for j, (d, col) in enumerate(((0, V[2]), (.07, MAG), (.14, CYAN))):
            if a - d >= 0:
                r = 12 + 140 * ease_out((a - d) / .55)
                out.append(('r', cx, cy, r, r * .8, 3.2 * (1 - (a - d) / .6) + .6, col, .9 * (1 - ease_in((a - d) / .6))))
        sg = smooth(a / .08) * (1 - ease_in((a - .2) / .6))
        sigil(out, TF[0], TF[1] - 2, 44 + 62 * ease_out(a / .3), .3, a + imp, sg, (V[2], V[3], V[1]), 12, 1.6)
        for q, (L0, rot, dx, dy) in enumerate(((100, .3, 0, 0), (62, .8, -50, -30), (48, 1.2, 46, 24))):
            k = ease_out(a / .12) * (1 - ease_in((a - .12) / .4))
            if k > .02: glint(out, cx + dx, cy + dy, L0 * k, 3.0, V[1], .8 * k, rot + a * 1.5)
        for i in range(84):                                                          # streaking sparks
            life = .5 + .55 * frac(i, 2); tt = a - .02 * frac(i, 5)
            if not 0 <= tt < life: continue
            ang = frac(i, 3) * 6.283; spd = 160 + 280 * frac(i, 4); tr = tt / life
            d = spd * (1 - math.exp(-tt * 5)) / 5; v = spd * math.exp(-tt * 5)
            x = cx + math.cos(ang) * d; y = cy + math.sin(ang) * d * .8 + 130 * tt * tt * (frac(i, 6) > .5)
            tw = .6 + .4 * math.sin(tt * 40 + i); col = (V[0], GOLD, MAG, CYAN, V[1])[i % 5]
            tx, ty = x - math.cos(ang) * v * .028, y - math.sin(ang) * v * .028 * .8
            out.append(('s', x, y, tx, ty, 2.2 * (1 - .5 * tr), col, (1 - tr) * tw))
            out.append(('g', x, y, 8, 8, col, .45 * (1 - tr) * tw)); out.append(('b', x, y, 2.4, V[0], (1 - tr) * tw))
        for i in range(26):                                                          # slow starfall
            tb = .08 + .5 * frac(i, 1); tt = a - tb
            if not 0 <= tt < .85: continue
            x = cx + (frac(i, 2) - .5) * 190; y = cy - 120 + tt * (70 + 40 * frac(i, 3)); r = tt / .85
            col = (V[0], GOLD, V[1], CYAN)[i % 4]
            glint(out, x, y, 5 + 5 * frac(i, 4), 1.2, col, math.sin(math.pi * r) * (.6 + .4 * math.sin(tt * 30 + i)), tt * 3 + i)
        if a < .6:
            for k in range(6):
                u = a / .6; ang = k * 1.047 + 1.9 * u
                px, py = cx + math.cos(ang) * 60 * ease_out(u), cy + math.sin(ang) * 44 * ease_out(u)
                out.append(('g', px, py, 36, 36, (V[3], MAG, CYAN)[k % 3], .16 * (1 - u)))   # nebula puffs
    return out


# ------------------------------------------------------------------ rally: golden pillars and a rising crest
def rally(t, geo):
    out = []; G = TONE['rally']; gy = geo['ground']
    cen = geo['center']
    if t < .9:
        r = 20 + 220 * ease_out(t / .9)
        out.append(('r', cen[0], gy - 2, r, r * .26, 3 * (1 - t / .9) + .6, G[1], .75 * (1 - ease_in(t / .9))))
    for n, (chest, foot) in enumerate(geo['targets']):
        d = .08 * n; tt = t - d
        if tt < 0: continue
        fx, fy = foot
        env = smooth(tt / .22) * (1 - smooth((tt - .95) / .6))
        r = 12 + 56 * ease_out(tt / .35)
        out.append(('r', fx, fy - 2, r, r * .3, 2.6 * (1 - ease_in(tt / .9)) + .8, G[1], .9 * (1 - ease_in(tt / 1.1))))
        out.append(('g', fx, fy - 2, 62 * env, 20 * env, G[2], .55 * env))
        h = 120 * ease_out(tt / .3)
        for k in range(8):
            yy = fy - h * k / 7
            out.append(('g', fx, yy, 22 + 6 * math.sin(tt * 6 + k), 22, G[1], .22 * env * (1 - .5 * k / 7)))
        for i in range(18):
            ph = frac(i + 40 * n, 1); a0 = ph * 6.283 + tt * (3 + 2 * frac(i, 2))
            life = 1.1; u = ((tt * .9 + ph) % 1.0)
            x = fx + math.cos(a0) * (30 - 12 * u) * 1.0; y = fy - 8 - u * (118 + 20 * frac(i, 3)) + math.sin(a0) * 8
            al = env * math.sin(math.pi * u) ** .7
            out.append(('g', x, y, 8, 8, G[1], .7 * al)); out.append(('b', x, y, 2.4, G[0], al))
        if .12 < tt < .8:
            k = smooth((tt - .12) / .2) * (1 - smooth((tt - .5) / .3))
            glint(out, chest[0], chest[1] - 70, 36 * k + 2, 2.8, G[0], k, 0)
    return out


# ------------------------------------------------------------------ sweep: a bright crescent swung through the target
def sweep(t, geo):
    out = []; W = TONE['sweep']; cx, cy = geo['center']; gy = geo['ground']; imp = SPEC['sweep'][1]
    ecx, ecy, rx, ry = cx - 18, cy, 112.0, 70.0
    a0, a1 = math.radians(-112), math.radians(112)
    def pt(th, k=1.0): return ecx + math.cos(th) * rx * k, ecy + math.sin(th) * ry * k
    head = lerp(a0, a1, ease_out(clamp01(t / .34)) ** .9) if t < .34 else a1
    swing = clamp01(t / .34)
    tail_len = math.radians(150)
    if t < 1.0:
        n = 64; ev = 1 - ease_in((t - .34) / .5)
        for i in range(n + 1):
            th = head - tail_len * i / n
            if th < a0: break
            u = i / n
            if t > .34: th2 = th; vis = ev * (1 - u * .5)
            else: vis = 1 - u
            x, y = pt(th); x2, y2 = pt(th, .88 - .12 * u)
            w = 18 * (1 - u) ** .8 * (.45 + .55 * math.sin(math.pi * clamp01((th - a0) / (a1 - a0)))) + 1.5
            out.append(('g', x, y, w * 1.6, w * 1.6, tone_at('sweep', .35 + u * .6), .3 * vis))
            out.append(('s', x, y, x2, y2, w * .4, W[1] if u < .5 else W[2], .8 * vis))
        hx, hy = pt(head)
        if t <= .5: out.append(('g', hx, hy, 34, 34, W[2], .5)); out.append(('g', hx, hy, 14, 14, W[1], .7))
        for i in range(40):
            tb = .04 + .30 * frac(i, 1); tt = t - tb
            if not 0 <= tt < .5: continue
            th = lerp(a0, a1, ease_out(tb / .34) ** .9); x, y = pt(th)
            nx, ny = math.cos(th), math.sin(th); tx, ty = -math.sin(th), math.cos(th)
            sp = 80 + 120 * frac(i, 2); d = sp * (1 - math.exp(-tt * 4)) / 4
            px = x + (nx * .7 + tx * .5) * d; py = y + (ny * .7 + ty * .5) * d + 140 * tt * tt * frac(i, 3)
            tr = tt / .5
            out.append(('g', px, py, 8, 8, W[2], .55 * (1 - tr))); out.append(('b', px, py, 2.4 * (1 - .5 * tr), W[0], 1 - tr))
    a = t - imp
    if a >= 0:
        if a < .2: out.append(('f', W[2], .12 * math.exp(-a * 18)))
        out.append(('g', cx + 40, cy, 90, 90, W[2], .32 * (1 - ease_in(a / .35))))
        glint(out, cx + 40, cy, 70 * ease_out(a / .1) * (1 - ease_in((a - .1) / .3)), 3.4, W[0], 1 - ease_in(a / .4), .4)
        r = 30 + 150 * ease_out(a / .5)
        out.append(('r', cx, gy - 2, r, r * .28, 3 * (1 - a / .55), W[1], .8 * (1 - ease_in(a / .55))))
    return out


# ------------------------------------------------------------------ dragon soul ward: a dragon coils round the ally, becomes a shell
def soul(t, geo):
    out = []; D = TONE['dragonSoulWard']; (chest, foot) = geo['targets'][0]; fx, fy = foot; gy = geo['ground']
    N = 56; coil = ease_out(clamp01(t / .55)); dissolve = smooth((t - 1.0) / .45)
    shell = smooth((t - .6) / .4) * (1 - smooth((t - 1.55) / .45))
    DEEP, BODY, MID, LIGHT = (10, 30, 96), (34, 98, 220), (70, 150, 255), (170, 225, 255)
    # floor sigil: the dragon seal
    sg = smooth(t / .25) * (1 - smooth((t - 1.5) / .45))
    sigil(out, fx, gy - 2, 70, .28, t, sg, (D[1], D[2], D[0]), 12, 1.0)
    if sg > .01:
        for k in range(12):
            a = -t * .8 + k * math.pi / 6
            x, y = ell(fx, gy - 2, 80, 80 * .28, a); out.append(('b', x, y, 3.0, GOLD, .85 * sg * (.5 + .5 * math.sin(t * 5 + k))))

    def body(tt, i):
        ph = tt * 4.8 - i * .115
        r = lerp(86, 42, coil) * (1 + .05 * math.sin(i * .3 + tt * 3))
        rise = 14 + 126 * (1 - math.exp(-max(0, tt) * 2.0)) - i * .95 + math.sin(ph * .5) * 7
        return fx + math.cos(ph) * r, fy - rise + math.sin(ph) * r * .34, math.sin(ph)
    if t < 1.5:
        env = 1 - dissolve
        pts = [body(t, i) for i in range(N)]

        def size(i, dep): return (20 * (1 - i / N) ** .8 + 5) * (.82 + .18 * dep)
        live = [i for i in range(N) if i <= N * (1 - dissolve)]
        if env > .01:
            for i in range(0, N, 4):                                               # mist puffs along the body
                if i in live:
                    x, y, dep = pts[i]; out.append(('g', x, y, 30, 24, (D[1], D[2], D[0])[(i // 4) % 3], .1 * env))
            for i in reversed(live):                                               # silhouette
                x, y, dep = pts[i]; sz = size(i, dep); al = (1.0 if dep > -.2 else .6) * env
                out.append(('g', x, y, sz * 1.8, sz * 1.8, D[2], .15 * env)); out.append(('c', x, y, sz * .56 + 1.7, DEEP, .95 * al))
            for i in reversed(live):                                               # body, belly and back light
                x, y, dep = pts[i]; sz = size(i, dep); al = (1.0 if dep > -.2 else .6) * env
                out.append(('c', x, y, sz * .56, BODY if i / N > .2 else MID, al))
                out.append(('c', x + sz * .04, y + sz * .2, sz * .34, MID, .85 * al))               # lighter belly
                out.append(('c', x - sz * .1, y - sz * .2, sz * .26, LIGHT, .85 * al))              # back light
                if i % 3 == 0 and dep > -.3:                                                      # dorsal fin
                    out.append(('p', [(x - sz * .22, y - sz * .45), (x + sz * .22, y - sz * .45), (x + sz * .05, y - sz * 1.15)], MID, .9 * env))
                    out.append(('p', [(x - sz * .1, y - sz * .5), (x + sz * .1, y - sz * .5), (x + sz * .03, y - sz * .95)], LIGHT, .9 * env))
                if i % 5 == 2: out.append(('b', x + math.sin(i * 9.1) * sz * .4, y - sz * .1, max(1.8, sz * .16), D[0], .85 * env))
            tx, ty, _ = pts[min(N - 1, int(N * (1 - dissolve)) - 1 if dissolve > 0 else N - 1)]
            for k in range(3):                                                      # tail tuft
                a = k - 1; out.append(('s', tx, ty, tx + 16 * (1 + .3 * math.sin(t * 8 + k)), ty + a * 9 + 4, 2.2, LIGHT, .7 * env))
            hx, hy, hd = pts[0]; nx2, ny2, _ = pts[3]
            ang = math.atan2(hy - ny2, hx - nx2); c, s_ = math.cos(ang), math.sin(ang); sc = 1.6
            def P(u, v): return (hx + (c * u - s_ * v) * sc, hy + (s_ * u + c * v) * sc)
            def poly(pts_l, col, al, grow=1.0): return ('p', [P(u * grow, v * grow) for u, v in pts_l], col, al * env)
            skull = [(-8, -7), (2, -9), (12, -6), (21, -3), (24, 1), (15, 3), (4, 6), (-8, 5)]
            jaw = [(0, 5), (14, 3), (21, 4), (12, 10), (0, 9)]
            out.append(poly(skull, DEEP, .98, 1.14)); out.append(poly(jaw, DEEP, .98, 1.14))
            for hu, hv, hl, hw in ((-6, -6, -20, -16), (-4, -8, -14, -22)):                # horns
                out.append(('p', [P(hu, hv), P(hl, hw), P(hu - 3, hv + 4)], DEEP, .95 * env))
                out.append(('p', [P(hu - .5, hv - .5), P(hl + 1.5, hw + 1.5), P(hu - 2.6, hv + 3.2)], LIGHT, .95 * env))
            for sp in range(3):                                                    # mane spikes
                out.append(('p', [P(-8 - sp * 5, -3 + sp * 2), P(-22 - sp * 5, -9 + sp * 5), P(-9 - sp * 5, 4 + sp * 2)], MID if sp != 1 else BODY, .9 * env))
            out.append(poly(skull, BODY, 1.0)); out.append(poly(jaw, (28, 80, 190), 1.0))
            out.append(poly([(2, -8), (12, -6), (21, -3), (12, -2.2), (3, -4)], LIGHT, .85))  # bridge highlight
            for k in range(3): x, y = P(14 + k * 3, 3.2); out.append(('b', x, y, 1.6, (255, 255, 255), .9 * env))   # teeth
            ex, ey = P(6, -3.2); out.append(('g', ex, ey, 10, 10, (255, 230, 140), .9 * env)); out.append(('b', ex, ey, 3.6, (255, 255, 255), env))
            for sgn in (-1, 1):                                                    # flowing whiskers
                pts_w = [P(20, sgn * 3)]
                for q in range(1, 7):
                    pts_w.append(P(20 - q * 5.5, sgn * (3 + q * 3.2) + math.sin(t * 7 + q * .8 + sgn) * 3.5))
                for q in range(6): out.append(('s', pts_w[q][0], pts_w[q][1], pts_w[q + 1][0], pts_w[q + 1][1], 1.9 - q * .15, LIGHT, .85 * env))
            out.append(('g', hx, hy, 46, 46, D[1], .3 * env))
            if .35 < t < .95:
                k = smooth((t - .35) / .2) * (1 - smooth((t - .75) / .2)); x, y = P(26, 2)
                out.append(('g', x, y, 26 * k + 4, 26 * k + 4, D[0], .8 * k)); out.append(('g', x, y, 50 * k + 4, 50 * k + 4, D[2], .3 * k))
                for q in range(10):
                    a2 = frac(q, 1) * 6.283; r2 = 12 + 40 * k * frac(q, 2); out.append(('b', x + math.cos(a2) * r2, y + math.sin(a2) * r2, 2.2, D[0], .8 * k))
        # the body breaks into light as it dissolves
        if dissolve > 0:
            for i in range(N):
                if i <= N * (1 - dissolve): continue
                x, y, dep = pts[i]
                if frac(i, 1) > .6: continue
                out.append(('g', x, y, 10, 10, (D[0], D[1], GOLD)[i % 3], .6 * (1 - dissolve * .5)))
                out.append(('b', x + (frac(i, 2) - .5) * 24 * dissolve, y - 30 * dissolve * (.5 + frac(i, 3)), 2.4, D[0], .9))
    if shell > .01:
        cy_ = fy - 64; RX, RY = 50, 78; rot = t * 1.1
        out.append(('g', fx, cy_, RX * 1.3, RY * 1.2, D[2], .2 * shell)); out.append(('g', fx, cy_, RX * .9, RY * .9, D[1], .1 * shell))
        for q in range(-3, 4):                                                     # latitude rings of the scale lattice
            yy = cy_ + q * RY * .27; rr = math.sqrt(max(0.0, 1 - (q * .27) ** 2))
            out.append(('r', fx, yy, RX * rr, RX * rr * .26, 1.5, D[1], .45 * shell))
        for k in range(6):                                                         # meridians
            a = rot + k * math.pi / 6; rx_ = abs(math.cos(a)) * RX
            if rx_ > 3: out.append(('r', fx, cy_, rx_, RY, 1.3, D[1], .34 * shell * (.5 + .5 * math.cos(a) ** 2)))
        out.append(('r', fx, cy_, RX, RY, 2.8, LIGHT, .55 * shell)); out.append(('r', fx, cy_, RX * .97, RY * .97, 1.3, D[0], .5 * shell))
        wy = cy_ + RY * (1 - 2 * ((t * .9) % 1.0)); out.append(('g', fx, wy, RX * 1.1, 10, D[0], .4 * shell))        # shimmer sweep
        for i in range(22):                                                        # rising motes inside the shell
            u = ((t * .5 + frac(i, 1)) % 1.0); a = frac(i, 2) * 6.283 + t
            x = fx + math.cos(a) * RX * .8 * frac(i, 3); y = cy_ + RY * (1 - 2 * u) * .9
            out.append(('g', x, y, 7, 7, (D[0], D[1], GOLD)[i % 3], .6 * shell * math.sin(math.pi * u))); out.append(('b', x, y, 2.2, D[0], shell * math.sin(math.pi * u)))
        rp = (t * 1.2) % 1.0
        out.append(('r', fx, cy_ + RY * (rp * 2 - 1) * .9, RX * math.sqrt(max(0.0, 1 - ((rp * 2 - 1) * .9) ** 2)) * 1.02, 10, 1.8, D[0], .5 * shell * (1 - rp)))
    if .55 < t < 1.1:
        k = 1 - abs(t - .8) / .25
        if k > 0: out.append(('f', D[2], .1 * k))
    return out


# ------------------------------------------------------------------ dragon scale ward: plates rise and lock into a shell
def scales(t, geo):
    out = []; S = TONE['dragonScaleWard']; (chest, foot) = geo['targets'][0]; fx, fy = foot; gy = geo['ground']
    cy_ = fy - 62; shell_rx, shell_ry = 46, 72
    fadeout = 1 - smooth((t - .72) / .26)
    r0 = 14 + 58 * ease_out(t / .3)
    out.append(('r', fx, gy - 2, r0, r0 * .3, 2.6 * (1 - ease_in(t / .8)) + .8, S[1], .85 * (1 - ease_in(t / .9))))
    out.append(('g', fx, gy - 2, 70 * smooth(t / .2) * fadeout, 20 * smooth(t / .2) * fadeout, S[2], .5 * fadeout))
    n = 30
    for i in range(n):
        row = i // 6; col = i % 6
        ang = (col / 6 + (row % 2) * .08) * 6.283 + .4
        ty = row / 4.0
        sx = fx + math.cos(ang) * shell_rx * math.sin(math.pi * (ty * .86 + .07)) * 1.04
        sy = cy_ + shell_ry * (ty - .5) * 1.9
        depth = math.sin(ang)
        t0 = .04 + .46 * frac(i, 1); k = clamp01((t - t0) / .34)
        if k <= 0: continue
        sa = frac(i, 2) * 6.283; sr = 52 + 40 * frac(i, 3)
        x0 = fx + math.cos(sa) * sr; y0 = gy + 2
        e = ease_out(k)
        x = lerp(x0, sx, e); y = lerp(y0, sy, e) - 56 * math.sin(math.pi * e) * (1 - e)
        for j in range(1, 5):
            kk = ease_out(clamp01((t - j * .018 - t0) / .34))
            if kk <= 0 or k >= 1: continue
            xx = lerp(x0, sx, kk); yy = lerp(y0, sy, kk) - 56 * math.sin(math.pi * kk) * (1 - kk)
            out.append(('g', xx, yy, 10 - j, 10 - j, S[2], .5 * (1 - j / 5)))
        size = 11 + 3 * (1 - abs(depth)) * .5
        a = (.95 if depth > -.25 else .55) * fadeout
        lock = smooth((k - .85) / .15)
        out.append(('g', x, y, size * 1.8, size * 1.8, S[2], .26 * a))
        out.append(('d', x, y, size * .78, size, S[3] if depth < -.25 else S[2], a))
        out.append(('d', x - size * .12, y - size * .2, size * .46, size * .6, S[1] if lock < .5 else S[0], .95 * a))
        out.append(('b', x - size * .2, y - size * .38, 2.2, S[0], a))
        if k >= 1 and t - t0 - .34 < .22:
            g = 1 - (t - t0 - .34) / .22
            out.append(('g', x, y, 20, 20, S[0], .6 * g))
    sh = smooth((t - .5) / .25) * fadeout
    if sh > .01:
        out.append(('g', fx, cy_, 58, 86, S[2], .22 * sh))
        sweep_y = cy_ + shell_ry * (((t - .55) * 2.2 % 1.0) * 2 - 1)
        out.append(('g', fx, sweep_y, 56, 9, S[0], .45 * sh))
        out.append(('r', fx, cy_, shell_rx, shell_ry, 2.0, S[1], .4 * sh))
    if .18 < t < .45:
        out.append(('f', S[2], .12 * (1 - abs(t - .3) / .15)))
    return out


# ================================================================== v3: smooth, rich, no angular parts
def stack(out, pts, ws, layers, alpha=1.0):
    """Gradient ribbon: several passes, each (width scale, rgb, mode, alpha), outer to inner, so the stroke shades smoothly."""
    for sc, col, mode, a in layers:
        out.append(('k', pts, [w * sc for w in ws], col, a * alpha, mode, max(1.2, 2.4 * sc)))


def sigil2(out, cx, cy, R, ratio, t, env, cols, petals=8, spin=1.0):
    """Floor seal made only of rings, arcs and petals (no straight lines)."""
    if env <= .01: return
    c1, c2, c3 = cols
    out.append(('g', cx, cy, R * 1.18, R * 1.18 * ratio, c2, .30 * env)); out.append(('g', cx, cy, R * .6, R * .6 * ratio, c1, .22 * env))
    out.append(('r', cx, cy, R, R * ratio, 2.6, c1, .85 * env)); out.append(('r', cx, cy, R * .93, R * .93 * ratio, 1.1, c3, .6 * env))
    out.append(('r', cx, cy, R * .62, R * .62 * ratio, 1.6, c1, .7 * env)); out.append(('r', cx, cy, R * .3, R * .3 * ratio, 1.2, c3, .6 * env))
    for k in range(6):
        a0 = spin * t * .7 + k * math.pi / 3
        out.append(('a', cx, cy, R * .8, R * .8 * ratio, a0, a0 + .72, 3.0, c1, .85 * env))
    for k in range(4):
        a0 = -spin * t * 1.1 + k * math.pi / 2
        out.append(('a', cx, cy, R * .46, R * .46 * ratio, a0, a0 + .9, 2.2, c3, .8 * env))
    for k in range(petals):
        a = k * 2 * math.pi / petals - spin * t * .4; d = R * .5
        px, py = cx + math.cos(a) * d, cy + math.sin(a) * d * ratio
        out.append(('r', px, py, R * .3, R * .11 * (1 + 1.2 * (1 - ratio)), 1.2, c2, .5 * env, a))
        out.append(('e', px, py, R * .26, R * .08, a, c1, .16 * env))
    for k in range(16):
        a = k * math.pi / 8 + spin * t * .5
        x, y = cx + math.cos(a) * R * .72, cy + math.sin(a) * R * .72 * ratio
        out.append(('g', x, y, 5, 5, c3, .85 * env * (.55 + .45 * math.sin(t * 5 + k))))


def aurora(out, cx, cy, t, env, cols, spread=150, h=120):
    if env <= .01: return
    for k in range(3):
        pts = []; ws = []
        for j in range(48):
            u = j / 47; x = cx + (u - .5) * spread * 2
            y = cy - h - 26 * k + 22 * math.sin(u * 5 + t * 1.3 + k * 2) + 9 * math.sin(u * 11 - t * 2 + k)
            pts.append((x, y)); ws.append(30 * math.sin(math.pi * u) ** .8 * (1 - .18 * k) + 2)
        out.append(('k', pts, ws, cols[k % len(cols)], .16 * env, 'add', 9))
        out.append(('k', pts, [w * .4 for w in ws], cols[(k + 1) % len(cols)], .12 * env, 'add', 6))


# ------------------------------------------------------------------ starlight pulse v3
def starlight(t, geo):
    out = []; C = geo['caster']; CF = geo['casterFoot']; T, TF = geo['targets'][0]; imp = SPEC['starlightPulse'][1]
    V = TONE['starlightPulse']; DEEP = (40, 24, 140)
    sig = smooth(t / .2) * (1 - smooth((t - .42) / .25))
    sigil2(out, CF[0], CF[1] - 2, 66, .3, t, sig, (V[2], V[3], V[1]), 8, 1.2)
    if t < .55:
        for i in range(22):                                                             # light rising from the seal
            ph = frac(i, 1); u = (t * .9 + ph) % 1.0
            x = CF[0] + math.sin(u * 6 + i) * (24 + 30 * frac(i, 2)); y = CF[1] - 6 - u * 130
            al = sig * math.sin(math.pi * u) ** .7
            out.append(('g', x, y, 8, 8, (V[2], MAG, CYAN)[i % 3], .55 * al)); out.append(('g', x, y, 3, 3, V[0], .9 * al))

    def path(tt):
        s = ease_in(clamp01(tt / imp)) ** .8
        x, y = lerp2(C, T, s)
        return x, y - 70 * math.sin(math.pi * s) * (1 - .3 * s), s

    if t < imp + .02:
        hx, hy, _ = path(t)
        N = 60; pts = []; ws = []; nrm = []
        for i in range(N - 1, -1, -1):
            tt = t - i * .0105
            if tt < 0: continue
            x, y, s = path(tt); x2, y2, _ = path(tt + .006)
            dx, dy = x2 - x, y2 - y; L = math.hypot(dx, dy) or 1.0; nx, ny = -dy / L, dx / L
            u = i / N; lat = 5 * u * math.sin(tt * 22 + i * .45)
            pts.append((x + nx * lat, y + ny * lat)); nrm.append((nx, ny, tt, i))
            ws.append(((17 * (1 - u) ** .85 + 1.2) * (.45 + .55 * clamp01(tt * 7))) * 2)
        if len(pts) > 3:
            for k in range(0, len(pts), 5):                                                 # nebula puffs
                out.append(('g', pts[k][0], pts[k][1], ws[k] * 1.9, ws[k] * 1.9, (V[3], MAG, CYAN)[(k // 5) % 3], .1))
            stack(out, pts, ws, [(1.25, DEEP, 'mix', .5), (1.0, V[4], 'mix', .7), (.72, V[3], 'mix', .85), (.5, V[2], 'add', .55), (.22, V[1], 'add', .85)])
            for k, col in enumerate((MAG, CYAN, V[1])):                                       # three light strands twisting round the core
                sp = []; sw = []
                for (px, py), (nx, ny, tt, i), w in zip(pts, nrm, ws):
                    ang = tt * 18 + i * .3 + k * 2.094; off = w * .62 + 2
                    sp.append((px + nx * math.cos(ang) * off, py + ny * math.cos(ang) * off + math.sin(ang) * off * .3)); sw.append(max(.8, w * .12))
                out.append(('k', sp, sw, col, .8, 'add', 2.0))
        for i in range(34):                                                                   # shed star dust
            tb = frac(i, 1) * imp * .95
            if not 0 <= t - tb < .6: continue
            tt = t - tb; x, y, _ = path(tb); r = tt / .6
            x += (frac(i, 2) - .5) * 44 * r; y += (frac(i, 3) - .3) * 44 * r + 34 * r * r
            col = (V[0], GOLD, MAG, CYAN)[i % 4]; k = (1 - r) * (.6 + .4 * math.sin(tt * 30 + i))
            out.append(('g', x, y, 8, 8, col, .7 * k)); out.append(('e', x, y, 8 + 4 * frac(i, 4), 1.1, tt * 3 + i, V[0], .8 * k)); out.append(('e', x, y, 8 + 4 * frac(i, 4), 1.1, tt * 3 + i + 1.571, V[0], .8 * k))
        fade = clamp01((imp - t) / .05); pulse = 1 + .08 * math.sin(t * 25)
        out.append(('g', hx, hy, 74, 74, V[3], .3 * fade)); out.append(('g', hx, hy, 40, 40, V[2], .42 * fade))
        out.append(('r', hx, hy, 26 * pulse, 26 * pulse, 1.5, V[2], .5 * fade)); out.append(('r', hx, hy, 34, 34, 1.0, MAG, .35 * fade))
        out.append(('g', hx, hy, 24, 24, V[1], .75 * fade)); out.append(('g', hx, hy, 12, 12, V[0], 1.0 * fade))
        out.append(('e', hx, hy, 110, 3.2, 0, V[1], .45 * fade)); out.append(('e', hx, hy, 70, 2.4, 0, V[0], .5 * fade))
        for k in range(4): out.append(('e', hx, hy, 42 - 10 * (k % 2), 2.4, t * 3 + k * .785, V[0], .6 * fade))
        for k in range(7):
            a = t * 9 + k * 2 * math.pi / 7; rr = 24 + 5 * math.sin(t * 6 + k)
            out.append(('g', hx + math.cos(a) * rr, hy + math.sin(a) * rr * .6, 6, 6, (V[0], MAG, CYAN)[k % 3], .8 * fade))
    a = t - imp
    if a >= 0:
        cx, cy = T
        if a < .2: out.append(('f', V[2], .12 * math.exp(-a * 18)))
        out.append(('g', cx, cy, 170 * (.5 + ease_out(a / .35)), 170 * (.5 + ease_out(a / .35)), V[3], .4 * (1 - ease_in(a / .8))))
        out.append(('g', cx, cy, 60, 60, V[2], .5 * (1 - ease_in(a / .35))))
        out.append(('g', cx, cy, 22, 22, V[1], .6 * (1 - ease_in(a / .22)))); out.append(('g', cx, cy, 10, 10, V[0], .9 * (1 - ease_in(a / .16))))
        out.append(('e', cx, cy, 230 * ease_out(a / .2), 4.5, 0, V[1], .55 * (1 - ease_in(a / .45))))          # anamorphic streak
        out.append(('e', cx, cy, 110 * ease_out(a / .2), 3.2, 0, V[0], .55 * (1 - ease_in(a / .35))))
        out.append(('e', cx, cy, 90 * ease_out(a / .2), 3.0, 1.571, V[1], .4 * (1 - ease_in(a / .35))))
        for k in range(40):                                                                   # soft light rays
            ang = k * 2 * math.pi / 40 + a * .4
            L = (60 + 100 * frac(k, 2)) * ease_out(a / .16) * (1 - ease_in((a - .1) / .6))
            if L > 3: out.append(('e', cx + math.cos(ang) * L / 2, cy + math.sin(ang) * L / 2, L / 2, 1.8, ang, (V[2], MAG, CYAN, V[1])[k % 4], .55 * (1 - a / .7)))
        for ring_i, (d, col) in enumerate(((0, V[2]), (.07, MAG), (.14, CYAN), (.22, V[1]))):    # shock rings
            if a - d >= 0:
                r = 12 + 150 * ease_out((a - d) / .6)
                out.append(('r', cx, cy, r, r * .8, 3.0 * (1 - (a - d) / .65) + .6, col, .85 * (1 - ease_in((a - d) / .65))))
        for layer, (n_p, col, rot0, size) in enumerate(((12, V[2], 0.0, 120), (8, MAG, .39, 82), (12, CYAN, .13, 150))):   # blooming light lotus
            k = ease_out((a - layer * .05) / .3) * (1 - ease_in((a - .22 - layer * .05) / .5))
            if k > .02:
                for q in range(n_p):
                    ang = q * 2 * math.pi / n_p + rot0 + a * (.9 - .3 * layer); L = size * k
                    px, py = cx + math.cos(ang) * L * .5, cy + math.sin(ang) * L * .5 * .82
                    out.append(('r', px, py, L * .5, L * .13, 1.4, col, .6 * k, ang)); out.append(('e', px, py, L * .42, L * .1, ang, col, .2 * k))
        sg = smooth(a / .08) * (1 - ease_in((a - .22) / .6))
        sigil2(out, TF[0], TF[1] - 2, 46 + 62 * ease_out(a / .3), .3, a + imp, sg, (V[2], V[3], V[1]), 8, 1.6)
        for q in range(3):                                                                    # rising spiral light
            pts = []; ws = []
            for j in range(40):
                u = j / 39; ang = q * 2.094 + u * 7 + a * 5; rr = 36 + 40 * u
                pts.append((TF[0] + math.cos(ang) * rr, TF[1] - 8 - u * 150 * ease_out(a / .5) + math.sin(ang) * rr * .3)); ws.append(5 * math.sin(math.pi * u) ** .8 + .6)
            out.append(('k', pts, ws, (V[2], MAG, CYAN)[q], .55 * (1 - ease_in((a - .15) / .6)), 'add', 3.0))
        for i in range(90):                                                                   # streaking sparks
            life = .55 + .6 * frac(i, 2); tt = a - .02 * frac(i, 5)
            if not 0 <= tt < life: continue
            ang = frac(i, 3) * 6.283; spd = 160 + 300 * frac(i, 4); tr = tt / life
            d = spd * (1 - math.exp(-tt * 5)) / 5; v = spd * math.exp(-tt * 5)
            x = cx + math.cos(ang) * d; y = cy + math.sin(ang) * d * .8 + 140 * tt * tt * (frac(i, 6) > .5)
            tw = .6 + .4 * math.sin(tt * 40 + i); col = (V[0], GOLD, MAG, CYAN, V[1])[i % 5]
            out.append(('e', x - math.cos(ang) * v * .014, y - math.sin(ang) * v * .014 * .8, max(3.0, v * .03), 1.9 * (1 - .5 * tr), ang, col, .9 * (1 - tr) * tw))
            out.append(('g', x, y, 7, 7, col, .5 * (1 - tr) * tw))
        for i in range(34):                                                                   # slow starfall
            tb = .06 + .55 * frac(i, 1); tt = a - tb
            if not 0 <= tt < .9: continue
            x = cx + (frac(i, 2) - .5) * 210; y = cy - 130 + tt * (70 + 40 * frac(i, 3)); r = tt / .9
            col = (V[0], GOLD, V[1], CYAN)[i % 4]; k = math.sin(math.pi * r) * (.6 + .4 * math.sin(tt * 30 + i))
            sz = 5 + 6 * frac(i, 4)
            out.append(('g', x, y, sz, sz, col, .7 * k)); out.append(('e', x, y, sz * 1.7, 1.1, tt * 2 + i, V[0], .8 * k)); out.append(('e', x, y, sz * 1.7, 1.1, tt * 2 + i + 1.571, V[0], .8 * k))
        aurora(out, cx, cy - 20, a * 1.4, smooth(a / .25) * (1 - smooth((a - .4) / .5)), (V[3], MAG, CYAN), 140, 100)
    return out


# ------------------------------------------------------------------ dragon soul ward v3
def soul(t, geo):
    out = []; D = TONE['dragonSoulWard']; (chest, foot) = geo['targets'][0]; fx, fy = foot; gy = geo['ground']
    N = 90; coil = ease_out(clamp01(t / .55)); dissolve = smooth((t - 1.0) / .45)
    shell = smooth((t - .6) / .4) * (1 - smooth((t - 1.55) / .45))
    DEEP, BODY, MID, LIGHT, BELLY = (10, 30, 96), (34, 98, 220), (70, 150, 255), (170, 225, 255), (150, 215, 255)
    sg = smooth(t / .25) * (1 - smooth((t - 1.5) / .45))
    sigil2(out, fx, gy - 2, 72, .28, t, sg, (D[2], (36, 90, 220), D[1]), 10, 1.0)
    for k in range(14):
        a = -t * .8 + k * math.pi / 7; x, y = ell(fx, gy - 2, 84, 84 * .28, a)
        out.append(('g', x, y, 6, 6, GOLD, .8 * sg * (.5 + .5 * math.sin(t * 5 + k))))

    def body(tt, i):
        ph = tt * 4.8 - i * .067
        r = lerp(88, 42, coil) * (1 + .05 * math.sin(i * .2 + tt * 3))
        rise = 14 + 130 * (1 - math.exp(-max(0, tt) * 2.0)) - i * .55 + math.sin(ph * .5) * 7
        return fx + math.cos(ph) * r, fy - rise + math.sin(ph) * r * .34, math.sin(ph)
    if t < 1.5:
        env = 1 - dissolve; n_live = max(2, int(N * (1 - dissolve)))
        raw = [body(t, i) for i in range(N)]
        pts = [(x, y) for x, y, _ in raw][:n_live]; dep = [d for _, _, d in raw][:n_live]
        ws = [(27 * (1 - i / N) ** .8 + 5) * (.86 + .14 * dep[i]) for i in range(n_live)]
        if env > .01 and n_live > 4:
            for i in range(0, n_live, 6):
                out.append(('g', pts[i][0], pts[i][1], 34, 28, (D[1], D[2], D[0])[(i // 6) % 3], .1 * env))            # mist
            def nrm(i):
                a_, b_ = pts[max(0, i - 1)], pts[min(n_live - 1, i + 1)]; dx, dy = b_[0] - a_[0], b_[1] - a_[1]; L = math.hypot(dx, dy) or 1.0
                return -dy / L, dx / L
            runs = []; cur = [0]
            for i in range(1, n_live):
                if (dep[i] >= -.15) != (dep[cur[-1]] >= -.15): runs.append(cur); cur = [cur[-1], i]
                else: cur.append(i)
            runs.append(cur)
            for run in sorted(runs, key=lambda r_: dep[r_[len(r_) // 2]] >= -.15):      # far runs first
                front = dep[run[len(run) // 2]] >= -.15; fa = (1.0 if front else .62) * env
                rp = [pts[i] for i in run]; rw = [ws[i] for i in run]
                stack(out, rp, rw, [(1.0, DEEP, 'mix', .95), (.84, BODY, 'mix', 1.0)], fa)
                up = []; lo = []
                for i in run: nx, ny = nrm(i); up.append((pts[i][0] + nx * ws[i] * -.2, pts[i][1] + ny * ws[i] * -.2)); lo.append((pts[i][0] + nx * ws[i] * .2, pts[i][1] + ny * ws[i] * .2))
                out.append(('k', lo, [w * .42 for w in rw], BELLY, .8 * fa, 'mix', 2.2))                      # lighter belly
                out.append(('k', up, [w * .3 for w in rw], LIGHT, .85 * fa, 'mix', 2.0))                       # back light
                out.append(('k', rp, [w * .6 for w in rw], MID, .3 * fa, 'add', 4.0))
            for i in range(3, n_live - 4, 5):                                                              # flowing dorsal fins
                if dep[i] < -.3: continue
                nx, ny = nrm(i); fx0, fy0 = pts[i][0] - nx * ws[i] * .4, pts[i][1] - ny * ws[i] * .4
                tx, ty = pts[min(n_live - 1, i + 2)][0] - pts[max(0, i - 2)][0], pts[min(n_live - 1, i + 2)][1] - pts[max(0, i - 2)][1]; tl = math.hypot(tx, ty) or 1.0
                tx, ty = tx / tl, ty / tl; hgt = ws[i] * 1.5; fp = []; fw = []
                for q in range(14):
                    u = q / 13; wob = math.sin(t * 7 + i * .5 + u * 4) * 4 * u
                    fp.append((fx0 - nx * hgt * math.sin(math.pi * u * .8) + tx * u * hgt * 1.3 + nx * wob, fy0 - ny * hgt * math.sin(math.pi * u * .8) + ty * u * hgt * 1.3 + ny * wob)); fw.append(5.5 * (1 - u) ** 1.1 + .3)
                out.append(('k', fp, fw, MID, .85 * env, 'mix', 1.6)); out.append(('k', fp, [w * .5 for w in fw], LIGHT, .8 * env, 'mix', 1.4))
            # head: bulbous skull + snout from one smooth ribbon, jaw, horns, mane and whiskers are all curved ribbons
            hx, hy = pts[0]; nx2, ny2 = pts[min(n_live - 1, 7)]
            ang = math.atan2(hy - ny2, hx - nx2); c, s_ = math.cos(ang), math.sin(ang); sc = 1.3
            def P(u, v): return (hx + (c * u - s_ * v) * sc, hy + (s_ * u + c * v) * sc)
            def curve(ctrl, n=18):
                out_pts = []
                for q in range(n):
                    u = q / (n - 1); i0 = min(len(ctrl) - 2, int(u * (len(ctrl) - 1))); f = u * (len(ctrl) - 1) - i0
                    a_, b_ = ctrl[i0], ctrl[i0 + 1]; out_pts.append((lerp(a_[0], b_[0], f), lerp(a_[1], b_[1], f)))
                return out_pts
            def sm(ctrl, wctrl, n=26):
                pp = []; ww = []
                for q in range(n):
                    u = q / (n - 1) * (len(ctrl) - 1); i0 = min(len(ctrl) - 2, int(u)); f = u - i0; f = f * f * (3 - 2 * f)
                    pp.append((lerp(ctrl[i0][0], ctrl[i0 + 1][0], f), lerp(ctrl[i0][1], ctrl[i0 + 1][1], f))); ww.append(lerp(wctrl[i0], wctrl[i0 + 1], f))
                return pp, ww
            sp, sw = sm([P(-12, 0), P(0, 0), P(12, -1), P(26, 0), P(38, 2)], [16, 24, 21, 12, 5])
            stack(out, sp, sw, [(1.14, DEEP, 'mix', .98), (1.0, BODY, 'mix', 1.0), (.62, MID, 'mix', .55)], env)
            up_ = [(x, y - 3.5) for x, y in sp]
            out.append(('k', [P(-2, -6), P(10, -6), P(24, -4), P(36, -.5)], [4.5, 5, 4, 1.5], LIGHT, .85 * env, 'mix', 2.0))
            jp, jw = sm([P(2, 9), P(14, 10), P(28, 8), P(36, 4)], [8, 9, 6, 2.2])
            stack(out, jp, jw, [(1.15, DEEP, 'mix', .95), (1.0, (28, 80, 190), 'mix', 1.0)], env)
            for hu, hv, hl, hw2 in ((-4, -10, -22, -16), (0, -12, -14, -24)):                              # curved horns
                hp = [P(hu, hv), P(hu - 6, hv - 8), P(hl + 3, hw2 + 5), P(hl, hw2)]
                cp = curve(hp, 18); out.append(('k', cp, [7 * (1 - q / 17) ** .9 + .5 for q in range(18)], DEEP, .95 * env, 'mix', 1.4)); out.append(('k', cp, [4.4 * (1 - q / 17) ** .9 + .2 for q in range(18)], LIGHT, .95 * env, 'mix', 1.2))
            for m in range(3):                                                                             # flowing mane
                mp = []; mw = []
                for q in range(16):
                    u = q / 15; wob = math.sin(t * 6 + m + u * 4) * 5 * u
                    mp.append(P(-8 - u * 26, -4 + m * 4 + wob * .6)); mw.append(5 * (1 - u) ** 1.1 + .3)
                out.append(('k', mp, mw, MID if m % 2 else BODY, .85 * env, 'mix', 1.6)); out.append(('k', mp, [w * .45 for w in mw], LIGHT, .7 * env, 'add', 2.0))
            for sgn in (-1, 1):                                                                            # long flowing whiskers
                wp = []; ww = []
                for q in range(24):
                    u = q / 23; wp.append(P(34 - u * 44, sgn * (3 + u * 12) + math.sin(t * 6 + u * 6 + sgn) * 5 * u)); ww.append(1.8 * (1 - u) ** 1.0 + .22)
                out.append(('k', wp, ww, LIGHT, .9 * env, 'add', 1.4))
            ex, ey = P(10, -6); out.append(('g', ex, ey, 13, 13, (255, 220, 120), .85 * env)); out.append(('g', ex, ey, 5.5, 5.5, (255, 255, 255), 1.0 * env))
            out.append(('g', hx, hy, 60, 60, D[1], .28 * env))
            if .35 < t < .95:
                k = smooth((t - .35) / .2) * (1 - smooth((t - .75) / .2)); x, y = P(42, 2)
                out.append(('g', x, y, 34 * k + 4, 34 * k + 4, D[0], .7 * k)); out.append(('g', x, y, 70 * k + 4, 70 * k + 4, D[2], .3 * k))
                for q in range(12):
                    a2 = frac(q, 1) * 6.283; r2 = 14 + 50 * k * frac(q, 2); out.append(('g', x + math.cos(a2) * r2, y + math.sin(a2) * r2, 6, 6, D[0], .8 * k))
            for k in range(2):                                                                             # spirit scarves
                sp2 = []; sw2 = []
                for q in range(50):
                    u = q / 49; ph = t * 3 + k * 3.14 - u * 5
                    sp2.append((fx + math.cos(ph) * (108 + 6 * math.sin(u * 8)), fy - 30 - 110 * u * (1 - .2 * k) + math.sin(ph) * 36)); sw2.append(5 * math.sin(math.pi * u) ** .8 + .4)
                out.append(('k', sp2, sw2, (D[1], D[0])[k], .2 * env * (1 - dissolve), 'add', 4.0))
        if dissolve > 0:                                                                                    # the body turns into light
            for i in range(n_live, N, 2):
                x, y, _ = raw[i]
                out.append(('g', x + (frac(i, 2) - .5) * 26 * dissolve, y - 34 * dissolve * (.5 + frac(i, 3)), 9, 9, (D[0], D[1], GOLD)[i % 3], .65 * (1 - dissolve * .6)))
    if shell > .01:
        cy_ = fy - 64; RX, RY = 52, 80
        out.append(('g', fx, cy_, RX * 1.35, RY * 1.25, D[2], .2 * shell)); out.append(('g', fx, cy_, RX * .9, RY * .9, D[1], .1 * shell))
        for q in range(3):                                                                                 # bands of light winding round the dome
            pts_ = []; ws_ = []
            for j in range(60):
                u = j / 59; ang = q * 2.094 + u * 9 + t * 1.3
                pts_.append((fx + math.cos(ang) * RX * math.sqrt(max(0, 1 - (2 * u - 1) ** 2)) * 1.0, cy_ + (2 * u - 1) * RY * .96))
                ws_.append(4 * math.sin(math.pi * u) ** .6 + .5)
            out.append(('k', pts_, ws_, (D[1], D[0], GOLD)[q], .5 * shell, 'add', 2.4))
        out.append(('r', fx, cy_, RX, RY, 3.0, LIGHT, .5 * shell)); out.append(('r', fx, cy_, RX * .96, RY * .96, 1.4, D[1], .5 * shell)); out.append(('r', fx, cy_, RX * .86, RY * .88, 1.0, D[2], .3 * shell))
        for k in range(5):
            a0 = t * (1.2 + .3 * k) + k * 1.3; out.append(('a', fx, cy_, RX * (1.0 + .02 * k), RY * (1.0 + .02 * k), a0, a0 + .9, 2.6, D[0], .65 * shell))
        wy = cy_ + RY * (1 - 2 * ((t * .8) % 1.0)); out.append(('e', fx, wy, RX * 1.0, 9, 0, D[0], .4 * shell))
        for i in range(30):
            u = ((t * .45 + frac(i, 1)) % 1.0); a = frac(i, 2) * 6.283 + t
            x = fx + math.cos(a) * RX * .82 * frac(i, 3); y = cy_ + RY * (1 - 2 * u) * .9; k = shell * math.sin(math.pi * u)
            out.append(('g', x, y, 8, 8, (D[0], D[1], GOLD)[i % 3], .65 * k)); out.append(('g', x, y, 3, 3, (255, 255, 255), .9 * k))
        rp = (t * 1.2) % 1.0
        out.append(('r', fx, cy_ + RY * (rp * 2 - 1) * .9, RX * math.sqrt(max(0.0, 1 - ((rp * 2 - 1) * .9) ** 2)) * 1.02, 10, 1.8, D[0], .5 * shell * (1 - rp)))
    if .55 < t < 1.1:
        k = 1 - abs(t - .8) / .25
        if k > 0: out.append(('f', D[2], .1 * k))
    return out


# ------------------------------------------------------------------ dragon soul ward v4: presence and power, nothing literal
def soul(t, geo):
    out = []; D = TONE['dragonSoulWard']; (chest, foot) = geo['targets'][0]; fx, fy = foot; gy = geo['ground']
    cx, cy = chest[0], chest[1]
    DEEP, BODY, MID, LIGHT = (10, 30, 96), (34, 98, 220), (70, 150, 255), (170, 225, 255)
    REL = .38                                           # the moment the power is released
    pre = clamp01(t / REL); post = t - REL
    # 1. the air tightens: light is drawn in, the seal wakes, the world darkens a touch more
    sg = smooth(t / .22) * (1 - smooth((t - 1.55) / .4))
    sigil2(out, fx, gy - 2, 74 - 14 * ease_in(pre) * (post < 0) + 8 * ease_out(post / .3), .28, t, sg, (D[2], (36, 90, 220), D[1]), 10, 1.0 + 3 * ease_in(pre) * (post < 0))
    if t < REL + .05:
        for i in range(34):
            ph = frac(i, 1); tt = clamp01((t - ph * .12) / (REL - ph * .12))
            a = frac(i, 2) * 6.283 + tt * 4.5; r = (120 + 80 * frac(i, 3)) * (1 - ease_in(tt)) ** 1.4
            x = cx + math.cos(a) * r; y = cy + 20 + math.sin(a) * r * .55 - 20 * ease_in(tt)
            k = math.sin(math.pi * min(1, tt * 1.05)) ** .6
            out.append(('e', x, y, 9 + 18 * (1 - tt), 1.8, a + 1.571 + tt * 4.5, (D[0], D[1], GOLD)[i % 3], .8 * k))
            out.append(('g', x, y, 6, 6, D[0], .8 * k))
        k = ease_in(pre) * (post < 0)
        out.append(('g', cx, cy, 70 - 40 * k + 20, 90 - 50 * k + 20, D[3], .22 + .22 * k)); out.append(('g', cx, cy, 20, 26, D[1], .5 * k))
    # 2. release: flash, pressure waves, a column of power
    if post >= 0:
        if post < .22: out.append(('f', D[2], .12 * math.exp(-post * 14)))
        for j, (d, wd) in enumerate(((0, 7.0), (.08, 5.0), (.17, 3.4), (.28, 2.2))):
            if post - d >= 0:
                r = 14 + 190 * ease_out((post - d) / .7)
                out.append(('r', fx, gy - 2, r, r * .27, wd * (1 - (post - d) / .75) + .5, (D[1], D[2], D[2], D[1])[j], .8 * (1 - ease_in((post - d) / .75))))
        for j in range(2):                                                                               # a wave through the air, round the body
            if post - j * .1 >= 0:
                r = 26 + 120 * ease_out((post - j * .1) / .5); out.append(('r', cx, cy, r, r * 1.25, 2.4 * (1 - (post - j * .1) / .55) + .5, D[1], .6 * (1 - ease_in((post - j * .1) / .55))))
        col_env = smooth(post / .12) * (1 - smooth((post - .95) / .55))
        for lyr, (w, c_, a) in enumerate(((84, D[3], .12), (52, BODY, .12), (26, D[2], .12), (9, MID, .3))):         # pillar of power, soft all through
            top = fy - 250 * ease_out(post / .2)
            pts = [(fx + math.sin(u * 7 + t * 4 + lyr) * 3 * (1 - u), fy - u * (fy - top)) for u in [i / 40 for i in range(41)]]
            out.append(('k', pts, [w * (.5 + .5 * math.sin(math.pi * (u * .9 + .1)) ** .5) * (1 + .06 * math.sin(t * 20 + lyr)) for u in [i / 40 for i in range(41)]], c_, a * col_env, 'add', 14 if lyr < 2 else 6))
        for q in range(6):                                                                               # counter-rotating streams of force
            sgn = 1 if q % 2 == 0 else -1; pts = []; ws = []
            head = ease_out(clamp01(post / .5)); tail = ease_in(clamp01((post - .9) / .6))
            for j in range(72):
                u = j / 71
                if u > head or u < tail * .9: continue
                ang = q * 1.047 + sgn * (u * (7 + .7 * q) - post * (4.5 + .4 * q)); rr = 40 + 30 * math.sin(u * 3 + q) + 34 * u * (1 + .15 * q)
                pts.append((fx + math.cos(ang) * rr, fy - 8 - u * 215 + math.sin(ang) * rr * .3)); ws.append((11 * (1 - u) ** .9 + 1.4) * (1 - tail) * (.75 + .25 * math.sin(u * 9 + q)))
            if len(pts) > 3:
                stack(out, pts, ws, [(1.7, D[3], 'add', .30), (1.0, BODY, 'add', .5), (.5, MID, 'add', .7), (.16, LIGHT, 'add', .8)], col_env)
                out.append(('k', pts, [w * 3.0 for w in ws], D[3], .1 * col_env, 'add', 12))
        for i in range(44):                                                                              # sparks blown outward and up
            tb = .02 + .5 * frac(i, 1); tt = post - tb
            if not 0 <= tt < .9: continue
            a = frac(i, 3) * 6.283; r = (60 + 160 * frac(i, 4)) * ease_out(tt / .6)
            x = cx + math.cos(a) * r; y = cy + 40 + math.sin(a) * r * .3 - 70 * tt * (.5 + frac(i, 5)); k = (1 - tt / .9) * (.6 + .4 * math.sin(tt * 30 + i))
            out.append(('e', x, y, 10, 1.7, a, (D[0], GOLD, D[1])[i % 3], .8 * k)); out.append(('g', x, y, 6, 6, D[0], .7 * k))
        for k in range(26):                                                                              # wind raked across the ground
            a = k * 2 * math.pi / 26 + .3 * frac(k, 2); L = (40 + 60 * frac(k, 3)); r = (30 + 160 * ease_out(post / .6)) * (.7 + .5 * frac(k, 4))
            out.append(('e', fx + math.cos(a) * r, gy - 4 + math.sin(a) * r * .27, L, 1.8, a, D[2], .5 * (1 - ease_in(post / .8))))
    # 3. the aura that stays: layered, breathing shells and flames of light rising off the body
    aura = smooth((post - .1) / .4) * (1 - smooth((t - 1.6) / .4)) if post > 0 else 0
    if aura > .01:
        pulse = 1 + .05 * math.sin(t * 6); RX, RY = 56 * pulse, 86 * pulse
        out.append(('g', cx, cy, RX * 1.6, RY * 1.3, D[3], .22 * aura)); out.append(('g', cx, cy, RX * 1.05, RY * 1.0, D[2], .08 * aura))
        for k, (sc, w, c_, al) in enumerate(((1.0, 3.0, D[1], .55), (.94, 1.6, D[2], .5), (1.1, 1.4, D[2], .35))):
            out.append(('r', cx, cy, RX * sc, RY * sc, w, c_, al * aura))
        for k in range(5):
            a0 = t * (1.3 + .35 * k) + k * 1.3; out.append(('a', cx, cy, RX * (1 + .03 * k), RY * (1 + .03 * k), a0, a0 + 1.0, 2.8, D[1], .6 * aura))
        for i in range(16):                                                                              # flames of light off the shoulders and back
            ph = frac(i, 1); u0 = (t * .55 + ph) % 1.0; a = frac(i, 2) * 6.283
            bx = cx + math.cos(a) * RX * .7; by = cy + RY * .75
            pts = []; ws = []
            for j in range(22):
                u = j / 21; y = by - u * (90 + 70 * frac(i, 3)) * (.35 + .65 * u0)
                pts.append((bx + math.sin(u * 5 + t * 3 + i) * 9 * u + (frac(i, 4) - .5) * 20 * u, y)); ws.append(8 * (1 - u) ** 1.1 + .4)
            fade = math.sin(math.pi * u0) ** .8
            out.append(('k', pts, ws, (D[2], D[1], D[2])[i % 3], .4 * aura * fade, 'add', 3.0))
        for i in range(30):
            u = ((t * .4 + frac(i, 1)) % 1.0); a = frac(i, 2) * 6.283 + t * .8
            x = cx + math.cos(a) * RX * .95 * frac(i, 3); y = cy + RY * (1 - 2 * u); k = aura * math.sin(math.pi * u)
            out.append(('g', x, y, 8, 8, (D[0], D[1], GOLD)[i % 3], .65 * k)); out.append(('g', x, y, 3, 3, (255, 255, 255), .9 * k))
        halo = aura * (.7 + .3 * math.sin(t * 5))                                                         # a crown of light above the head
        out.append(('r', cx, cy - RY - 14, 34, 9, 2.2, GOLD, .75 * halo)); out.append(('g', cx, cy - RY - 14, 50, 16, GOLD, .28 * halo))
    return out


GENERATORS = {'starlightPulse': starlight, 'rally': rally, 'sweep': sweep, 'dragonSoulWard': soul, 'dragonScaleWard': scales}
