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
    'starlightPulse': (1.6, 0.75, False, .75),
    'rally': (1.67, 0.0, True),
    'sweep': (1.0, 0.45, False),
    'dragonSoulWard': (2.0, 0.0, True, .38),
    'dragonScaleWard': (1.0, 0.0, True, .56),
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
def starlight(t, geo, ti=0):
    out = []; C = geo['caster']; CF = geo['casterFoot']; T, TF = geo['targets'][ti]; imp = SPEC['starlightPulse'][1]
    V = TONE['starlightPulse']; DEEP = (40, 24, 140)
    sig = smooth(t / .2) * (1 - smooth((t - .42) / .25)) * (1.0 if ti == 0 else 0.0)
    sigil2(out, CF[0], CF[1] - 2, 66, .3, t, sig, (V[2], V[3], V[1]), 8, 1.2)
    if t < .55 and ti == 0:
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
        if a < .2 and ti == 0: out.append(('f', V[2], .12 * math.exp(-a * 18)))
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
def soul(t, geo, ti=0):
    out = []; D = TONE['dragonSoulWard']; (chest, foot) = geo['targets'][ti]; fx, fy = foot; gy = fy
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
        if post < .22 and ti == 0: out.append(('f', D[2], .12 * math.exp(-post * 14)))
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


# ================================================================== v5: the spellblade and dragon knight skills
# Palette: deep, body, mid, light, accent 1, accent 2.
PAL = {
    'rune': dict(deep=(14, 40, 92), body=(40, 150, 235), mid=(90, 215, 255), light=(205, 248, 255), a1=(255, 214, 120), a2=(150, 110, 255)),
    'battle': dict(deep=(110, 40, 10), body=(230, 120, 30), mid=(255, 180, 60), light=(255, 236, 170), a1=(255, 90, 60), a2=(255, 230, 160)),
    'flame': dict(deep=(120, 20, 8), body=(235, 70, 20), mid=(255, 150, 40), light=(255, 225, 140), a1=(255, 250, 220), a2=(255, 90, 40)),
    'scale': dict(deep=(96, 44, 10), body=(214, 120, 28), mid=(255, 180, 70), light=(255, 230, 160), a1=(255, 120, 60), a2=(255, 214, 120)),
    'order': dict(deep=(90, 10, 30), body=(200, 40, 50), mid=(255, 110, 70), light=(255, 210, 150), a1=(255, 220, 120), a2=(255, 150, 90)),
}
SPEC.update({'runeSlash': (2.4, 1.048, False), 'runeWard': (2.4, .72, True), 'battleRune': (2.1, .56, True),
             'dragonFlame': (2.2, .46, False), 'dragonScaleWard': (2.2, .56, True), 'dragonOrder': (2.1, .56, True)})
DIM.update({'runeSlash': (.30, (.8, .92, 1.0)), 'runeWard': (.28, (.8, .92, 1.0)), 'battleRune': (.28, (1.0, .88, .72)),
            'dragonFlame': (.34, (1.0, .78, .62)), 'dragonScaleWard': (.28, (1.0, .88, .7)), 'dragonOrder': (.32, (1.0, .78, .72))})


def compress_in(out, cx, cy, fx, fy, pre, P, n=30):
    """Light drawn into the target in the beat before release."""
    if pre <= 0 or pre >= 1.02: return
    for i in range(n):
        ph = frac(i, 1); tt = clamp01((pre - ph * .3) / (1 - ph * .3))
        a = frac(i, 2) * 6.283 + tt * 4.5; r = (110 + 80 * frac(i, 3)) * (1 - ease_in(tt)) ** 1.4
        x = cx + math.cos(a) * r; y = cy + 20 + math.sin(a) * r * .55 - 20 * ease_in(tt)
        k = math.sin(math.pi * min(1, tt * 1.05)) ** .6
        out.append(('e', x, y, 9 + 16 * (1 - tt), 1.8, a + 1.571 + tt * 4.5, (P['light'], P['mid'], P['a1'])[i % 3], .8 * k)); out.append(('g', x, y, 6, 6, P['light'], .7 * k))
    k = ease_in(clamp01(pre))
    out.append(('g', cx, cy, 90 - 50 * k, 110 - 60 * k, P['body'], .2 + .22 * k)); out.append(('g', cx, cy, 22, 28, P['mid'], .5 * k))


def ground_waves(out, fx, gy, post, P, R=190, n=4, thick=7.0):
    for j in range(n):
        d = j * .09
        if post - d >= 0:
            r = 14 + R * ease_out((post - d) / .7); wd = (thick - j * 1.5)
            out.append(('r', fx, gy - 2, r, r * .27, max(.6, wd * (1 - (post - d) / .75)), (P['mid'], P['body'], P['mid'], P['light'])[j % 4], .8 * (1 - ease_in((post - d) / .75))))


def column(out, fx, fy, post, env, P, h=240, w0=84):
    top = fy - h * ease_out(post / .2); us = [i / 40 for i in range(41)]
    for lyr, (w, c_, a) in enumerate(((w0, P['deep'], .16), (w0 * .62, P['body'], .14), (w0 * .3, P['mid'], .13), (10, P['light'], .3))):
        pts = [(fx + math.sin(u * 7 + post * 4 + lyr) * 3 * (1 - u), fy - u * (fy - top)) for u in us]
        out.append(('k', pts, [w * (.5 + .5 * math.sin(math.pi * (u * .9 + .1)) ** .5) * (1 + .06 * math.sin(post * 20 + lyr)) for u in us], c_, a * env, 'add', 14 if lyr < 2 else 6))


def sparks_out(out, cx, cy, post, P, n=44, spread=160, life0=.9, rise=70):
    for i in range(n):
        tb = .02 + .5 * frac(i, 1); tt = post - tb
        if not 0 <= tt < life0: continue
        a = frac(i, 3) * 6.283; r = (60 + spread * frac(i, 4)) * ease_out(tt / .6)
        x = cx + math.cos(a) * r; y = cy + 40 + math.sin(a) * r * .3 - rise * tt * (.5 + frac(i, 5)); k = (1 - tt / life0) * (.6 + .4 * math.sin(tt * 30 + i))
        out.append(('e', x, y, 10, 1.7, a, (P['light'], P['a1'], P['mid'])[i % 3], .8 * k)); out.append(('g', x, y, 6, 6, P['light'], .7 * k))


def helix_streams(out, fx, fy, post, env, P, n=6, height=215, widest=11.0):
    for q in range(n):
        sgn = 1 if q % 2 == 0 else -1; pts = []; ws = []
        head = ease_out(clamp01(post / .5)); tail = ease_in(clamp01((post - .9) / .6))
        for j in range(72):
            u = j / 71
            if u > head or u < tail * .9: continue
            ang = q * 6.283 / n + sgn * (u * (7 + .7 * q) - post * (4.5 + .4 * q)); rr = 40 + 30 * math.sin(u * 3 + q) + 34 * u * (1 + .15 * q)
            pts.append((fx + math.cos(ang) * rr, fy - 8 - u * height + math.sin(ang) * rr * .3)); ws.append((widest * (1 - u) ** .9 + 1.4) * (1 - tail) * (.75 + .25 * math.sin(u * 9 + q)))
        if len(pts) > 3:
            stack(out, pts, ws, [(1.7, P['deep'], 'add', .3), (1.0, P['body'], 'add', .5), (.5, P['mid'], 'add', .7), (.16, P['light'], 'add', .8)], env)
            out.append(('k', pts, [w * 3.0 for w in ws], P['deep'], .1 * env, 'add', 12))


def aura(out, cx, cy, fx, t, env, P, rx=56, ry=86, flames=14, crown=None):
    if env <= .01: return
    pulse = 1 + .05 * math.sin(t * 6); RX, RY = rx * pulse, ry * pulse
    out.append(('g', cx, cy, RX * 1.6, RY * 1.3, P['deep'], .22 * env)); out.append(('g', cx, cy, RX * 1.05, RY * 1.0, P['body'], .08 * env))
    for sc, w, c_, al in ((1.0, 3.0, P['mid'], .55), (.94, 1.6, P['body'], .5), (1.1, 1.4, P['body'], .35)):
        out.append(('r', cx, cy, RX * sc, RY * sc, w, c_, al * env))
    for k in range(5):
        a0 = t * (1.3 + .35 * k) + k * 1.3; out.append(('a', cx, cy, RX * (1 + .03 * k), RY * (1 + .03 * k), a0, a0 + 1.0, 2.8, P['mid'], .6 * env))
    for i in range(flames):
        ph = frac(i, 1); u0 = (t * .55 + ph) % 1.0; a = frac(i, 2) * 6.283; bx = cx + math.cos(a) * RX * .7; by = cy + RY * .75
        pts = []; ws = []
        for j in range(22):
            u = j / 21; pts.append((bx + math.sin(u * 5 + t * 3 + i) * 9 * u + (frac(i, 4) - .5) * 20 * u, by - u * (90 + 70 * frac(i, 3)) * (.35 + .65 * u0))); ws.append(8 * (1 - u) ** 1.1 + .4)
        out.append(('k', pts, ws, (P['body'], P['mid'], P['a2'])[i % 3], .4 * env * math.sin(math.pi * u0) ** .8, 'add', 3.0))
    for i in range(24):
        u = ((t * .4 + frac(i, 1)) % 1.0); a = frac(i, 2) * 6.283 + t * .8
        x = cx + math.cos(a) * RX * .95 * frac(i, 3); y = cy + RY * (1 - 2 * u); k = env * math.sin(math.pi * u)
        out.append(('g', x, y, 8, 8, (P['light'], P['mid'], P['a1'])[i % 3], .65 * k)); out.append(('g', x, y, 3, 3, (255, 255, 255), .9 * k))
    if crown:
        halo = env * (.7 + .3 * math.sin(t * 5)); out.append(('r', cx, cy - RY - 14, 34, 9, 2.2, crown, .75 * halo)); out.append(('g', cx, cy - RY - 14, 50, 16, crown, .28 * halo))


def burst_at(out, cx, cy, a, P, size=1.0):
    """Common detonation: flash, soft core, streak, rays, rings."""
    if a < 0: return
    if a < .2: out.append(('f', P['mid'], .12 * math.exp(-a * 18)))
    out.append(('g', cx, cy, 170 * size * (.5 + ease_out(a / .35)), 170 * size * (.5 + ease_out(a / .35)), P['deep'], .4 * (1 - ease_in(a / .8))))
    out.append(('g', cx, cy, 60 * size, 60 * size, P['body'], .5 * (1 - ease_in(a / .35))))
    out.append(('g', cx, cy, 22 * size, 22 * size, P['light'], .6 * (1 - ease_in(a / .22)))); out.append(('g', cx, cy, 10 * size, 10 * size, (255, 255, 255), .85 * (1 - ease_in(a / .16))))
    out.append(('e', cx, cy, 230 * size * ease_out(a / .2), 4.5, 0, P['mid'], .5 * (1 - ease_in(a / .45))))
    for k in range(32):
        ang = k * 2 * math.pi / 32 + a * .4; L = (60 + 100 * frac(k, 2)) * size * ease_out(a / .16) * (1 - ease_in((a - .1) / .6))
        if L > 3: out.append(('e', cx + math.cos(ang) * L / 2, cy + math.sin(ang) * L / 2, L / 2, 1.8, ang, (P['body'], P['a1'], P['mid'], P['light'])[k % 4], .55 * (1 - a / .7)))
    for ring_i, (d, col) in enumerate(((0, P['mid']), (.07, P['a1']), (.14, P['body']))):
        if a - d >= 0:
            r = (12 + 150 * ease_out((a - d) / .6)) * size
            out.append(('r', cx, cy, r, r * .8, 3.0 * (1 - (a - d) / .65) + .6, col, .85 * (1 - ease_in((a - d) / .65))))


def rune_cylinder(out, fx, gy, cy, t, env, P, RX=52, RY=84, bands=5):
    """A standing barrier made of rotating arc bands, rings and travelling glints (runes implied, nothing literal)."""
    if env <= .01: return
    out.append(('g', fx, cy, RX * 1.4, RY * 1.25, P['deep'], .2 * env))
    for b in range(bands):
        yy = cy + (b - (bands - 1) / 2) * RY * .42
        for k in range(4):
            a0 = t * (1.0 + .25 * b) * (1 if b % 2 == 0 else -1) + k * 1.571 + b
            out.append(('a', fx, yy, RX * .98, RX * .98 * .28, a0, a0 + .95, 2.6, (P['mid'], P['a1'])[b % 2], .75 * env))
        out.append(('r', fx, yy, RX, RX * .28, 1.2, P['body'], .45 * env))
    out.append(('r', fx, cy, RX, RY, 2.6, P['light'], .45 * env))
    wy = cy + RY * (1 - 2 * ((t * .8) % 1.0)); out.append(('e', fx, wy, RX, 9, 0, P['light'], .4 * env))


# ------------------------------------------------------------------ spellblade: rune slash
def rune_slash(t, geo):
    out = []; P = PAL['rune']; C = geo['caster']; CF = geo['casterFoot']; T, TF = geo['targets'][0]; imp = SPEC['runeSlash'][1]
    pre = clamp01((t - .3) / (imp - .3)); post = t - imp
    sg = smooth((t - .2) / .3) * (1 - smooth((t - imp - .1) / .5))
    sigil2(out, CF[0], CF[1] - 2, 62 - 16 * ease_in(pre), .3, t, sg, (P['mid'], P['body'], P['light']), 8, 1.4 + 2.5 * pre)
    if t < imp: compress_in(out, C[0] + 30, C[1] - 10, CF[0], CF[1], pre, P, 26)
    for q in range(3):                                                                         # rune light runs along the blade while it is held
        if 0 < pre:
            for j in range(10):
                u = j / 9; a = t * 6 + q * 2.1 + u * 3; x = C[0] + 24 + u * 30; y = C[1] - 22 + u * 4
                out.append(('g', x + math.cos(a) * 3, y + math.sin(a) * 4, 6, 6, (P['light'], P['a1'], P['mid'])[q], .55 * pre * math.sin(math.pi * u) ** .5))
    if post >= 0:
        cx, cy = T; swing = clamp01(post / .26)
        for copy in range(4):                                                                  # a slash and three afterimages, each a smooth ribbon
            d = copy * .035; sw = clamp01((post - d) / .26)
            if sw <= 0: continue
            head = lerp(-1.75, 1.85, ease_out(sw) ** .9); tail = head - 2.6 * (1 - .15 * copy)
            pts = []; ws = []
            for j in range(60):
                th = lerp(max(tail, -1.75), head, j / 59); u = j / 59
                pts.append((cx - 24 + math.cos(th) * 128 * (1 + .04 * copy), cy + math.sin(th) * 84 * (1 + .04 * copy) - 6)); ws.append((22 * math.sin(math.pi * clamp01((th + 1.75) / 3.6)) ** .7 + 2) * (u ** 1.1) * (1 - .18 * copy))
            env = (1 - ease_in((post - .3 - d) / .6)) * (1 - .2 * copy)
            if env > .01 and len(pts) > 3:
                stack(out, pts, ws, [(1.7, P['deep'], 'add', .28), (1.0, P['body'], 'add', .55), (.5, P['mid'], 'add', .75), (.18, P['light'], 'add', .95)], env)
        hx = cx - 24 + math.cos(lerp(-1.75, 1.85, ease_out(swing) ** .9)) * 128; hy = cy + math.sin(lerp(-1.75, 1.85, ease_out(swing) ** .9)) * 84 - 6
        if post < .5: out.append(('g', hx, hy, 40, 40, P['mid'], .6 * (1 - post / .5))); out.append(('g', hx, hy, 14, 14, P['light'], .9 * (1 - post / .5)))
        if post > .16: burst_at(out, cx, cy, post - .16, P, 1.05)
        ground_waves(out, TF[0], TF[1], post - .12, P, 200, 4, 7)
        for k in range(9):                                                                     # light run along the ground from the blow
            a = k * 2 * math.pi / 9 + .3 * frac(k, 2); pts = []; ws = []
            for j in range(24):
                u = j / 23; L = (40 + 150 * frac(k, 3)) * ease_out((post - .12) / .5) * u
                pts.append((TF[0] + math.cos(a) * L + math.sin(u * 9 + k) * 4, TF[1] - 4 + math.sin(a) * L * .27)); ws.append(5 * (1 - u) ** 1.2 + .5)
            out.append(('k', pts, ws, (P['mid'], P['a1'], P['light'])[k % 3], .6 * (1 - ease_in((post - .1) / .8)), 'add', 3.0))
        sparks_out(out, cx, cy, post - .1, P, 56, 200)
        sg2 = smooth((post - .1) / .1) * (1 - ease_in((post - .3) / .9)); sigil2(out, TF[0], TF[1] - 2, 50 + 70 * ease_out((post - .1) / .4), .3, post + imp, sg2, (P['mid'], P['body'], P['a1']), 8, 1.6)
    return out


# ------------------------------------------------------------------ spellblade: rune ward
def rune_ward(t, geo):
    out = []; P = PAL['rune']; (chest, foot) = geo['targets'][0]; fx, fy = foot; cx, cy = chest; gy = geo['ground']; imp = SPEC['runeWard'][1]
    pre = clamp01(t / imp); post = t - imp
    sg = smooth(t / .25) * (1 - smooth((t - 2.0) / .35))
    sigil2(out, fx, gy - 2, 72 - 12 * ease_in(pre) * (post < 0) + 8 * ease_out(post / .3), .28, t, sg, (P['mid'], P['body'], P['a1']), 10, 1.0 + 3 * ease_in(pre) * (post < 0))
    if post < .05: compress_in(out, cx, cy, fx, fy, pre, P, 30)
    if post >= 0:
        if post < .2: out.append(('f', P['mid'], .12 * math.exp(-post * 14)))
        ground_waves(out, fx, gy, post, P, 180, 4, 6)
        for k in range(6):                                                                     # rune rings climbing the body
            d = k * .07; tt = post - d
            if 0 <= tt < .9:
                y = fy - 6 - 150 * ease_out(tt / .8); rx_ = 60 - 10 * math.sin(math.pi * tt / .9)
                out.append(('r', fx, y, rx_, rx_ * .28, 3.0 * (1 - tt / .95) + .6, (P['mid'], P['a1'], P['light'])[k % 3], .8 * (1 - ease_in(tt / .95))))
                for m in range(3):
                    a0 = t * 5 + m * 2.094 + k; out.append(('a', fx, y, rx_, rx_ * .28, a0, a0 + .8, 3.0, P['light'], .7 * (1 - ease_in(tt / .95))))
        col_env = smooth(post / .12) * (1 - smooth((post - .9) / .5)); column(out, fx, fy, post, col_env, P, 220, 70)
        sparks_out(out, cx, cy, post, P, 34, 130, .9, 60)
    cyl = smooth((post - .12) / .35) * (1 - smooth((t - 2.0) / .35)) if post > 0 else 0
    rune_cylinder(out, fx, gy, cy, t, cyl, P)
    for i in range(18):
        u = ((t * .45 + frac(i, 1)) % 1.0); a = frac(i, 2) * 6.283 + t; x = fx + math.cos(a) * 46 * frac(i, 3); y = cy + 84 * (1 - 2 * u); k = cyl * math.sin(math.pi * u)
        out.append(('g', x, y, 8, 8, (P['light'], P['mid'], P['a1'])[i % 3], .65 * k)); out.append(('g', x, y, 3, 3, (255, 255, 255), .9 * k))
    return out


# ------------------------------------------------------------------ spellblade: battle rune (a surge of power)
def battle_rune(t, geo):
    out = []; P = PAL['battle']; (chest, foot) = geo['targets'][0]; fx, fy = foot; cx, cy = chest; gy = geo['ground']; imp = SPEC['battleRune'][1]
    pre = clamp01((t - .05) / (imp - .05)); post = t - imp
    sg = smooth(t / .2) * (1 - smooth((t - 1.8) / .3))
    sigil2(out, fx, gy - 2, 70 - 14 * ease_in(pre) * (post < 0) + 10 * ease_out(post / .3), .28, t, sg, (P['mid'], P['body'], P['a2']), 12, 1.0 + 3 * ease_in(pre) * (post < 0))
    if post < .05: compress_in(out, cx, cy, fx, fy, pre, P, 30)
    if post >= 0:
        if post < .22: out.append(('f', P['mid'], .14 * math.exp(-post * 14)))
        ground_waves(out, fx, gy, post, P, 200, 4, 7); column(out, fx, fy, post, smooth(post / .1) * (1 - smooth((post - .8) / .5)), P, 260, 90)
        for q in range(7):                                                                     # tongues of power racing up the body
            pts = []; ws = []; head = ease_out(clamp01((post - q * .02) / .4)); tail = ease_in(clamp01((post - .7) / .6))
            for j in range(40):
                u = j / 39
                if u > head or u < tail * .9: continue
                a = q * .9 + post * 3; x = fx + math.sin(u * 6 + post * 8 + q * 2) * (14 + 10 * u) + (q - 3) * 7
                pts.append((x, fy - 6 - u * (200 + 40 * frac(q, 1)))); ws.append((13 * (1 - u) ** .9 + 1.6) * (1 - tail))
            if len(pts) > 3: stack(out, pts, ws, [(1.7, P['deep'], 'add', .3), (1.0, P['body'], 'add', .55), (.5, P['mid'], 'add', .75), (.18, P['light'], 'add', .9)], 1.0)
        sparks_out(out, cx, cy, post, P, 60, 170, 1.0, 100)
        for k in range(3):                                                                     # the power settles into the shoulders and arms
            a = post - k * .08
            if a >= 0: r = 20 + 110 * ease_out(a / .6); out.append(('r', cx, cy, r, r * 1.2, 2.4 * (1 - a / .65) + .5, (P['light'], P['a1'], P['mid'])[k], .6 * (1 - ease_in(a / .65))))
    aura(out, cx, cy, fx, t, smooth((post - .1) / .4) * (1 - smooth((t - 1.8) / .3)) if post > 0 else 0, P, 58, 88, 18, P['light'])
    return out


# ------------------------------------------------------------------ dragon knight: dragon flame (fire falls on the target and erupts)
def dragon_flame(t, geo):
    out = []; P = PAL['flame']; C = geo['caster']; CF = geo['casterFoot']; T, TF = geo['targets'][0]; imp = SPEC['dragonFlame'][1]
    pre = clamp01(t / imp); post = t - imp; cx, cy = T
    sg = smooth(t / .2) * (1 - smooth((t - imp - .4) / .5))
    sigil2(out, CF[0], CF[1] - 2, 60 - 12 * ease_in(pre), .3, t, sg, (P['mid'], P['body'], P['a1']), 8, 1.5 + 3 * pre)
    if t < imp + .05: compress_in(out, C[0] + 20, C[1] - 6, CF[0], CF[1], pre, P, 28)
    if t < imp:                                                                                # a braided torrent of fire falls onto the target
        k = ease_in(pre)
        for q in range(4):
            pts = []; ws = []
            for j in range(64):
                u = j / 63
                if u > k * 1.05: continue
                x = lerp(cx - 120, cx, u ** .9) + math.sin(u * 9 + t * 14 + q * 1.6) * (14 * (1 - u) + 3); y = lerp(cy - 280, cy, u ** .9) + math.cos(u * 8 + t * 12 + q) * 8 * (1 - u)
                pts.append((x + (q - 1.5) * 9 * (1 - u), y)); ws.append((16 * u ** .6 + 3) * (1 - .15 * q))
            if len(pts) > 3: stack(out, pts, ws, [(1.8, P['deep'], 'add', .3), (1.0, P['body'], 'add', .6), (.55, P['mid'], 'add', .8), (.2, P['a1'], 'add', .95)], 1.0)
        out.append(('g', cx - 120 * (1 - k), cy - 280 * (1 - k), 50, 50, P['mid'], .5 * k)); out.append(('g', cx - 120 * (1 - k), cy - 280 * (1 - k), 20, 20, P['a1'], .8 * k))
    if post >= 0:
        burst_at(out, cx, cy, post, P, 1.2); ground_waves(out, TF[0], TF[1], post, P, 210, 4, 8)
        col_env = smooth(post / .1) * (1 - smooth((post - .9) / .6)); column(out, TF[0], TF[1], post, col_env, P, 250, 96)
        for q in range(5):                                                                     # flames licking up from the ground
            pts = []; ws = []; head = ease_out(clamp01((post - q * .03) / .5)); tail = ease_in(clamp01((post - .9) / .7))
            for j in range(34):
                u = j / 33
                if u > head or u < tail * .85: continue
                pts.append((TF[0] + (q - 2) * 16 + math.sin(u * 8 + post * 9 + q) * (8 + 12 * u), TF[1] - 4 - u * (170 + 40 * frac(q, 2)))); ws.append((16 * (1 - u) ** .8 + 2) * (1 - tail))
            if len(pts) > 3: stack(out, pts, ws, [(1.7, P['deep'], 'add', .3), (1.0, P['body'], 'add', .55), (.5, P['mid'], 'add', .75), (.2, P['a1'], 'add', .9)], 1.0)
        sparks_out(out, cx, cy, post, P, 80, 220, 1.2, 120)
        for i in range(10):                                                                    # heavy smoke rising and thinning out
            u = clamp01((post - .15 - .04 * i) / 1.2)
            if 0 < u < 1: out.append(('g', TF[0] + (frac(i, 1) - .5) * 80, TF[1] - 40 - u * 150, 40 + 30 * u, 36 + 24 * u, P['deep'], .22 * math.sin(math.pi * u)))
        a2 = smooth((post - .2) / .3) * (1 - smooth((t - 2.0) / .2)); sigil2(out, TF[0], TF[1] - 2, 50 + 66 * ease_out(post / .4), .3, post + imp, a2 * (1 - ease_in(post / 1.4)), (P['mid'], P['body'], P['a1']), 8, 1.2)
    ca = smooth((post - .15) / .3) * (1 - smooth((t - 2.0) / .2)) if post > 0 else 0                    # the caster is wrapped in warmth
    if ca > 0: aura(out, C[0], C[1], CF[0], t, ca * .8, PAL['scale'], 46, 70, 8, None)
    return out


# ------------------------------------------------------------------ dragon knight: dragon scale ward (a heavy amber guard)
def scale_ward(t, geo):
    out = []; P = PAL['scale']; (chest, foot) = geo['targets'][0]; fx, fy = foot; cx, cy = chest; gy = geo['ground']; imp = SPEC['dragonScaleWard'][1]
    pre = clamp01(t / imp); post = t - imp
    sg = smooth(t / .2) * (1 - smooth((t - 1.8) / .35))
    sigil2(out, fx, gy - 2, 72 - 14 * ease_in(pre) * (post < 0) + 8 * ease_out(post / .3), .28, t, sg, (P['mid'], P['body'], P['a2']), 10, 1.0 + 3 * ease_in(pre) * (post < 0))
    if post < .05: compress_in(out, cx, cy, fx, fy, pre, P, 30)
    if post >= 0:
        if post < .22: out.append(('f', P['mid'], .12 * math.exp(-post * 14)))
        ground_waves(out, fx, gy, post, P, 200, 5, 9)
        RX, RY = 56, 88
        for layer in range(3):                                                                 # overlapping curved plates close round the body, layer on layer
            d = layer * .12; tt = clamp01((post - d) / .35); env = smooth(tt) * (1 - smooth((t - 1.75 - layer * .06) / .4))
            if env <= .01: continue
            sc = 1 + .1 * layer
            for row in range(7):
                yy = cy + (row - 3) * RY * .27; rr = math.sqrt(max(0.0, 1 - ((row - 3) * .27) ** 2)) * RX * sc
                for k in range(5):
                    a0 = (k * 1.2566 + row * .45 + layer * .6) + t * (.35 if layer % 2 == 0 else -.35)
                    out.append(('a', fx, yy, rr, rr * .27, a0, a0 + 1.35, 3.4 - layer * .5, (P['mid'], P['a2'], P['light'])[layer], .6 * env))
            out.append(('r', fx, cy, RX * sc, RY * sc, 2.4 - layer * .5, (P['light'], P['mid'], P['body'])[layer], .45 * env))
        shell = smooth((post - .1) / .4) * (1 - smooth((t - 1.75) / .4))
        out.append(('g', fx, cy, RX * 1.5, RY * 1.3, P['body'], .2 * shell)); out.append(('g', fx, cy, RX * 1.0, RY * 1.0, P['mid'], .1 * shell))
        wy = cy + RY * (1 - 2 * ((t * .9) % 1.0)); out.append(('e', fx, wy, RX, 10, 0, P['light'], .4 * shell))
        if .1 < post < .6: out.append(('r', fx, cy, 30 + 110 * ease_out((post - .1) / .5), 40 + 150 * ease_out((post - .1) / .5), 2.4 * (1 - (post - .1) / .55) + .5, P['light'], .6 * (1 - (post - .1) / .55)))
        sparks_out(out, cx, cy, post, P, 40, 140, 1.0, 90)
        for i in range(18):
            u = ((t * .35 + frac(i, 1)) % 1.0); a = frac(i, 2) * 6.283 + t * .7; x = fx + math.cos(a) * RX * .95 * frac(i, 3); y = fy - 8 - u * 180; k = shell * math.sin(math.pi * u)
            out.append(('g', x, y, 8, 8, (P['light'], P['a1'], P['mid'])[i % 3], .6 * k)); out.append(('g', x, y, 3, 3, (255, 255, 255), .85 * k))
    return out


# ------------------------------------------------------------------ dragon knight: dragon order (a command that shakes the field)
def dragon_order(t, geo):
    out = []; P = PAL['order']; C = geo['caster']; CF = geo['casterFoot']; imp = SPEC['dragonOrder'][1]
    pre = clamp01(t / imp); post = t - imp; gy = geo['ground']
    sg = smooth(t / .2) * (1 - smooth((t - 1.8) / .3))
    sigil2(out, CF[0], CF[1] - 2, 74 - 14 * ease_in(pre) * (post < 0) + 10 * ease_out(post / .3), .28, t, sg, (P['mid'], P['body'], P['a1']), 12, 1.0 + 3 * ease_in(pre) * (post < 0))
    if post < .05: compress_in(out, C[0], C[1], CF[0], CF[1], pre, P, 34)
    if post >= 0:
        if post < .25: out.append(('f', P['mid'], .16 * math.exp(-post * 12)))
        ground_waves(out, CF[0], CF[1], post, P, 260, 5, 9)
        for k in range(5):                                                                     # the roar: wide arcs of pressure sweeping out across the field
            d = k * .08; tt = post - d
            if tt >= 0:
                r = 40 + 420 * ease_out(tt / .9); out.append(('a', C[0] + 20, C[1], r, r * .55, -1.1, 1.1, 5.0 * (1 - tt / .95) + .8, (P['light'], P['a1'], P['mid'], P['light'], P['a1'])[k], .75 * (1 - ease_in(tt / .95))))
                out.append(('a', C[0] + 20, C[1], r * .94, r * .94 * .55, -1.0, 1.0, 2.0, P['body'], .5 * (1 - ease_in(tt / .95))))
        out.append(('e', C[0] + 120 * ease_out(post / .5), C[1], 160, 7, 0, P['mid'], .35 * (1 - ease_in(post / .6))))
        for n, (chest, foot) in enumerate(geo['targets']):
            tt = post - .1 - .06 * n
            if tt < 0: continue
            fx, fy = foot; cx, cy = chest
            col_env = smooth(tt / .12) * (1 - smooth((tt - .9) / .5)); column(out, fx, fy, tt, col_env, P, 230, 74)
            helix_streams(out, fx, fy, tt, col_env, P, 5, 190, 10.0)
            ground_waves(out, fx, gy, tt, P, 160, 3, 6); sparks_out(out, cx, cy, tt, P, 34, 130, 1.0, 100)
            aura(out, cx, cy, fx, t, smooth((tt - .1) / .4) * (1 - smooth((t - 1.8) / .3)), P, 54, 84, 12, P['a1'])
            for k in range(3):                                                                  # a seal of command over each head
                yy = cy - 120 - k * 12; a0 = t * (2 + k) + k
                out.append(('a', fx, yy, 30 - k * 5, 9 - k * 1.5, a0, a0 + 2.2, 2.2, (P['a1'], P['light'], P['mid'])[k], .8 * smooth((tt - .15) / .2) * (1 - smooth((t - 1.8) / .3))))
    return out


# ================================================================== v6: every skill gets its own signature (no shared burst/column/aura recipe)
def arc_pts(cx, cy, rx, ry, a0, a1, n=40, roll=0.0):
    out = []
    for j in range(n):
        a = lerp(a0, a1, j / (n - 1)); x, y = math.cos(a) * rx, math.sin(a) * ry
        out.append((cx + x * math.cos(roll) - y * math.sin(roll), cy + x * math.sin(roll) + y * math.cos(roll)))
    return out


def bolt(out, A, B, t, seed, P, amp=14, n=16, w=3.2, alpha=1.0, rate=30):
    """A crackling arc between two points: jittering smooth ribbon, bright thin core, soft halo."""
    pts = []; ws = []
    dx, dy = B[0] - A[0], B[1] - A[1]; L = math.hypot(dx, dy) or 1.0; nx, ny = -dy / L, dx / L
    for j in range(n):
        u = j / (n - 1); env = math.sin(math.pi * u) ** .8
        d = amp * env * (math.sin(j * 1.9 + t * rate + seed * 7.1) * .6 + math.sin(j * 3.3 - t * rate * 1.3 + seed * 3.7) * .4)
        pts.append((A[0] + dx * u + nx * d, A[1] + dy * u + ny * d)); ws.append(w * (.55 + .45 * env))
    stack(out, pts, ws, [(2.6, P['body'], 'add', .22), (1.0, P['mid'], 'add', .55), (.4, P['light'], 'add', .95)], alpha)


def flame(out, bx, by, h, w, t, seed, P, alpha=1.0, n=26):
    pts = []; ws = []
    for j in range(n):
        u = j / (n - 1); pts.append((bx + math.sin(u * 6 + t * 9 + seed * 3.3) * w * .5 * u + math.sin(u * 13 - t * 14 + seed) * w * .15 * u, by - u * h)); ws.append(w * (1 - u) ** .85 + .8)
    stack(out, pts, ws, [(1.5, P['deep'], 'add', .22), (1.0, P['body'], 'add', .55), (.5, P['mid'], 'add', .8), (.18, P['a1'], 'add', .95)], alpha)


# ------------------------------------------------------------------ rune slash: five phantom blades cut the target in turn
def rune_slash(t, geo, ti=0):
    out = []; P = PAL['rune']; C = geo['caster']; CF = geo['casterFoot']; T, TF = geo['targets'][ti]; imp = SPEC['runeSlash'][1]
    pre = clamp01((t - .25) / (imp - .25)); cx, cy = T
    ANG = (-.95, .35, 1.25, -.2, -1.75)                                      # the angle of each cut
    for k in range(5 if ti == 0 else 0):                                     # blades gather round the caster, spinning faster and faster
        e = smooth((t - .2 - k * .09) / .35)
        if e <= .01 or t >= imp + .05 * k: continue
        sp = 3 + 14 * pre * pre; a = t * sp + k * 1.2566; R = 52 + 10 * math.sin(t * 5 + k)
        px, py = C[0] + 24 + math.cos(a) * R, C[1] + math.sin(a) * R * .55
        ang = a + 1.571
        pts = [(px + math.cos(ang) * s_ * 24, py + math.sin(ang) * s_ * 24 * .55) for s_ in [i / 11 - .5 for i in range(12)]]
        ws = [9 * math.sin(math.pi * (i / 11)) ** .8 + .6 for i in range(12)]
        stack(out, pts, ws, [(2.2, P['body'], 'add', .25), (1.0, P['mid'], 'add', .6), (.4, P['light'], 'add', .95)], e)
    if t < imp and ti == 0:
        out.append(('g', C[0] + 24, C[1], 40 + 30 * pre, 50 + 30 * pre, P['body'], .22 + .25 * pre)); out.append(('g', C[0] + 24, C[1], 14, 18, P['light'], .8 * pre))
    last = imp + .06 * 4
    for k in range(5):                                                       # the cuts: each appears all at once, burns white, then cools
        a = t - imp - .06 * k
        if a < 0: continue
        th = ANG[k]; L = 150 + 30 * (k % 2)
        fly = clamp01(a / .05)                                                # the blade flashes in from the caster side
        reveal = ease_out(clamp01(a / .07))
        env = (1 - ease_in((a - .06) / .55)) * (1.0 if a < .06 else 1.0)
        ux, uy = math.cos(th), math.sin(th) * .8; nx, ny = -uy, ux
        pts = []; ws = []
        for j in range(30):
            u = j / 29; s_ = (u - .5) * 2; bow = (1 - s_ * s_) * 16
            pts.append((cx + ux * s_ * L * reveal + nx * bow, cy + uy * s_ * L * reveal + ny * bow)); ws.append(10 * math.sin(math.pi * u) ** .75 + .5)
        if env > .01:
            stack(out, pts, ws, [(2.4, P['deep'], 'add', .3), (1.2, P['body'], 'add', .5), (.6, P['mid'], 'add', .7), (.22, P['light'], 'add', .95)], env)
            col = (P['a1'], P['light'])[k % 2]
            out.append(('g', cx, cy, 44, 44, col, .4 * env * (1 - ease_in(a / .3)))); out.append(('e', cx, cy, 120, 3.0, th, P['mid'], .5 * (1 - ease_in(a / .22))))
        for i in range(8):                                                    # chips of light thrown off each cut
            ang2 = th + (frac(i + 9 * k, 3) - .5) * 1.4 + (math.pi if i % 2 else 0); d = (30 + 80 * frac(i + 9 * k, 4)) * ease_out(a / .4)
            out.append(('e', cx + math.cos(ang2) * d, cy + math.sin(ang2) * d * .8, 9, 1.5, ang2, (P['light'], P['a1'])[i % 2], .8 * (1 - ease_in(a / .5))))
    if t - last > 0:                                                         # the stroke is felt after the cuts: a single hard pulse and scattered glass-like light
        a = t - last
        if ti == 0: out.append(('f', P['light'], .1 * math.exp(-a * 20)))
        r = 20 + 100 * ease_out(a / .35); out.append(('r', cx, cy, r, r * .8, 2.4 * (1 - a / .4) + .4, P['mid'], .7 * (1 - ease_in(a / .4))))
        for i in range(26):
            ang2 = frac(i, 3) * 6.283; d = (40 + 130 * frac(i, 4)) * ease_out(a / .6); tr = a / .9
            out.append(('e', cx + math.cos(ang2) * d, cy + math.sin(ang2) * d * .8 + 40 * a * a, 12, 1.4, ang2 + 1.2 * a, (P['light'], P['a1'], P['mid'])[i % 3], .8 * (1 - tr)))
    return out


# ------------------------------------------------------------------ rune ward: six curved panels close like a shutter
def rune_ward(t, geo, ti=0):
    out = []; P = PAL['rune']; (chest, foot) = geo['targets'][ti]; fx, fy = foot; cx, cy = chest; imp = SPEC['runeWard'][1]
    N = 6; H = 150
    close = ease_out(clamp01((t - imp) / .4)) if t >= imp else 0.0
    appear = smooth(t / .4)
    fadeout = 1 - smooth((t - 1.9) / .45)
    R = lerp(112, 50, close) if t >= imp else 112 - 6 * math.sin(t * 6)
    spin = t * (.5 + 4 * (1 - close)) * (1 if t < imp else (1 - close))
    for k in range(N):
        a = spin + k * 2 * math.pi / N; half = math.pi / N * (.86 + .14 * close)
        pts_b = []; ws_b = []; up = []
        for j in range(26):
            u = j / 25; aa = a + (u - .5) * 2 * half * (1 if t >= imp else .6)
            pts_b.append((fx + math.cos(aa) * R, fy - 4 + math.sin(aa) * R * .28))
        # panel = a wall of light: many vertical ribbons along the arc, heights follow a gentle dome
        depth = math.sin(a)
        for j in range(0, 26, 3):
            x0, y0 = pts_b[j]; u = j / 25; h = H * (.92 + .08 * math.sin(u * math.pi)) * (appear if t < imp else 1.0)
            pw = [(x0, y0 - q * h / 14 + math.sin(q * .5 + t * 3 + k) * 1.5) for q in range(15)]
            ww = [6 + 2 * math.sin(q / 14 * math.pi) for q in range(15)]
            out.append(('k', pw, ww, P['body'] if depth < 0 else P['mid'], (.2 if depth < 0 else .34) * appear * fadeout, 'add', 5.0))
        top = [(x, y - H * (appear if t < imp else 1.0)) for x, y in pts_b]; bot = pts_b
        out.append(('k', top, [3.2] * len(top), P['light'], (.5 if depth >= 0 else .3) * appear * fadeout, 'add', 2.0))
        out.append(('k', bot, [3.2] * len(bot), P['light'], (.55 if depth >= 0 else .3) * appear * fadeout, 'add', 2.0))
        ca, sa = math.cos(a), math.sin(a)
        for m in range(3):                                                    # a glyph-like mark rising slowly on each panel
            uu = ((t * .35 + m / 3 + k * .13) % 1.0); x, y = fx + ca * R, fy - 4 + sa * R * .28 - uu * H
            out.append(('g', x, y, 7, 7, P['a1'], .7 * appear * fadeout * math.sin(math.pi * uu)))
    if t >= imp:
        a = t - imp
        if a < .5:                                                            # the shutter locks: one flash on the floor, one ring, a held breath
            if ti == 0: out.append(('f', P['light'], .1 * math.exp(-a * 16)))
            r = 30 + 120 * ease_out(a / .45); out.append(('r', fx, fy - 2, r, r * .28, 3.4 * (1 - a / .5) + .5, P['light'], .8 * (1 - ease_in(a / .5))))
        for k in range(N):                                                    # seams glow in sequence around the ring
            ph = (t * 1.4 - k / N) % 1.0; ang = k * 2 * math.pi / N + spin + math.pi / N
            x, y = fx + math.cos(ang) * R, fy - 4 + math.sin(ang) * R * .28
            pts = [(x, y - q * H / 12) for q in range(13)]
            out.append(('k', pts, [2.6] * 13, P['light'], (.9 * math.exp(-ph * 4)) * fadeout, 'add', 2.0))
        out.append(('g', fx, cy, 70, 100, P['body'], .12 * fadeout))
    if t < imp:                                                               # panels drift in out of motes
        for i in range(30):
            ph = frac(i, 1); a = frac(i, 2) * 6.283 + t * 2; r = 120 + 40 * ph
            out.append(('g', fx + math.cos(a) * r, fy - 6 - frac(i, 3) * H + math.sin(a) * r * .28, 6, 6, P['mid'], .6 * appear * (1 - clamp01((t - imp + .1) / .1))))
    return out


# ------------------------------------------------------------------ battle rune: overcharge, crackling lightning and speed afterimages
def battle_rune(t, geo, ti=0):
    out = []; P = PAL['battle']; (chest, foot) = geo['targets'][ti]; fx, fy = foot; cx, cy = chest; imp = SPEC['battleRune'][1]
    pre = clamp01((t - .05) / (imp - .05)); post = t - imp; fade = 1 - smooth((t - 1.75) / .35)
    NODES = [(cx + math.cos(a) * 46, cy + math.sin(a) * 58) for a in [k * math.pi / 3 + .4 for k in range(6)]]
    if t < imp:                                                               # tiny sparks crawl over the body, the hair stands on end
        for k in range(int(3 + 9 * pre)):
            A = NODES[k % 6]; B = NODES[(k * 5 + 2) % 6]
            if A != B: bolt(out, A, B, t, k, P, 6 + 6 * pre, 10, 1.6, .5 + .5 * pre)
        out.append(('g', cx, cy, 70, 90, P['body'], .15 + .2 * pre))
    if post >= 0:
        if post < .15 and ti == 0: out.append(('f', P['light'], .2 * math.exp(-post * 18)))
        env = smooth(post / .08) * fade
        for k in range(16):                                                    # a field of arcs, each re-rolled by time so it flickers like real discharge
            ph = int(t * 24) + k * 7; r1 = frac(ph, 1); r2 = frac(ph, 2)
            a1 = k * .393 + r1 * .5; ang2 = a1 + 1.2 + r2 * 2.2
            A = (cx + math.cos(a1) * (30 + 20 * r1), cy + math.sin(a1) * (40 + 20 * r1)); B = (fx + math.cos(ang2) * (70 + 60 * r2), fy - 4 + math.sin(ang2) * 18)
            if k % 3 == 0: B = (cx + math.cos(ang2) * (90 + 40 * r2), cy + math.sin(ang2) * (100 + 30 * r2) - 20)
            bolt(out, A, B, t, k + 1, P, 22, 16, 3.0, env * (.45 + .55 * frac(ph, 3)) * (1 - ease_in(post / 1.6) * .6))
        for q in range(4):                                                    # speed afterimages sweeping up the body, each a ghost of the one before
            d = q * .06; aa = post - d
            if 0 <= aa < .5:
                y = fy - 170 * ease_out(aa / .45); w = 62 * (1 - aa / .6)
                pts = [(cx + (u - .5) * 2 * w, y + 8 * math.sin(u * 3.1)) for u in [i / 20 for i in range(21)]]
                out.append(('k', pts, [3.4 * math.sin(math.pi * u) + .4 for u in [i / 20 for i in range(21)]], (P['light'], P['a1'], P['mid'], P['body'])[q], .8 * (1 - aa / .5), 'add', 3.0))
        for i in range(34):                                                    # embers that spit off the discharge
            tb = frac(i, 1) * .6; tt = post - tb
            if not 0 <= tt < .8: continue
            ang = frac(i, 3) * 6.283; d = (50 + 120 * frac(i, 4)) * ease_out(tt / .5)
            x = cx + math.cos(ang) * d; y = cy + math.sin(ang) * d * .6 - 60 * tt * (.4 + frac(i, 5)) + 120 * tt * tt * (frac(i, 6) > .5); k = (1 - tt / .8)
            out.append(('e', x, y, 8, 1.5, ang, (P['light'], P['a1'], P['mid'])[i % 3], .8 * k)); out.append(('g', x, y, 5, 5, P['light'], .7 * k))
        for k in range(6):                                                    # the floor takes the current: scorched glow and a lazy ring
            ang = k * 1.047 + .3; x, y = fx + math.cos(ang) * 60, fy - 4 + math.sin(ang) * 16
            out.append(('g', x, y, 26, 8, P['deep'], .35 * fade)); out.append(('g', x, y, 10, 4, P['mid'], .5 * fade * (.5 + .5 * math.sin(t * 25 + k * 2))))
    return out


# ------------------------------------------------------------------ dragon flame: a fire comet falls and the ground keeps burning
def dragon_flame(t, geo, ti=0):
    out = []; P = PAL['flame']; C = geo['caster']; CF = geo['casterFoot']; T, TF = geo['targets'][ti]; imp = SPEC['dragonFlame'][1]
    cx, cy = T; post = t - imp; pre = clamp01(t / imp)
    SX, SY = cx - 170, cy - 330                                              # where the comet comes from
    out.append(('g', SX, SY, 160, 120, P['body'], .22 * smooth(t / .2) * (1 - smooth(post / .3)))); out.append(('g', SX, SY, 70, 60, P['mid'], .25 * smooth(t / .2) * (1 - smooth(post / .3)))) if post < .4 else None
    def path(tt):
        s = ease_in(clamp01(tt / imp)) ** 1.5
        return lerp(SX, cx, s) + math.sin(s * 5) * 8 * (1 - s), lerp(SY, cy, s), s
    if t < imp + .03:
        hx, hy, hs = path(t)
        pts = []; ws = []
        for i in range(48, -1, -1):
            tt = t - i * .012
            if tt < 0: continue
            x, y, s = path(tt); u = i / 48
            pts.append((x + math.sin(tt * 40 + i * .6) * 5 * u, y + math.cos(tt * 33 + i * .4) * 5 * u)); ws.append((13 * (1 - u) ** .9 + 1.0) * (.5 + .5 * clamp01(tt * 6)))
        if len(pts) > 3: stack(out, pts, ws, [(1.8, P['deep'], 'add', .22), (1.0, P['body'], 'add', .5), (.5, P['mid'], 'add', .8), (.2, P['a1'], 'add', .95)])
        for q in range(12):                                                   # fine tongues streaming off the head
            fp = []; fw = []
            for j in range(18):
                u = j / 17; back = (pts[-1] if pts else (hx, hy)); fp.append((hx - (cx - SX) / 380 * u * 90 + math.sin(u * 7 + t * 20 + q * 1.1) * 10 * u + (q - 5.5) * 3, hy - (cy - SY) / 380 * u * 90 + math.cos(u * 6 + t * 17 + q) * 8 * u)); fw.append(6 * (1 - u) ** .9 + .4)
            out.append(('k', fp, fw, (P['mid'], P['a2'], P['body'])[q % 3], .5, 'add', 1.6))
        out.append(('g', hx, hy, 70, 70, P['body'], .5)); out.append(('g', hx, hy, 34, 34, P['mid'], .8)); out.append(('g', hx, hy, 14, 14, P['a1'], 1.0))
    if post >= 0:
        if post < .25 and ti == 0: out.append(('f', P['mid'], .26 * math.exp(-post * 12)))
        out.append(('g', cx, cy, 290 * (.5 + ease_out(post / .3)), 190 * (.5 + ease_out(post / .3)), P['body'], .45 * (1 - ease_in(post / .7))))
        out.append(('g', cx, cy, 70, 60, P['a1'], .8 * (1 - ease_in(post / .22))))
        for k in range(18):                                                    # the splash runs out along the ground as low sheets of fire
            a = k * 2 * math.pi / 18 + .2 * frac(k, 2); L = (120 + 110 * frac(k, 3)) * ease_out(post / .45)
            x, y = TF[0] + math.cos(a) * L, TF[1] - 4 + math.sin(a) * L * .27
            flame(out, x, y, 40 + 60 * frac(k, 4) * (1 - ease_in(post / 1.4)), 10, t, k, P, (1 - ease_in((post - .4) / 1.2)) * smooth(post / .1))
        for i in range(36):                                                    # the ground goes on burning: many small tongues, each living its own life
            ang = frac(i, 5) * 6.283; rr = 20 + 150 * frac(i, 6); x = TF[0] + math.cos(ang) * rr * 1.1; y = TF[1] - 3 + math.sin(ang) * rr * .27
            born = .15 + .5 * frac(i, 7); lifeA = clamp01((post - born) / .2) * (1 - clamp01((post - born - .9 - .5 * frac(i, 8)) / .5))
            if lifeA > .01: flame(out, x, y, (26 + 44 * frac(i, 9)) * (.7 + .3 * math.sin(t * 11 + i)), 5.5 + 4 * frac(i, 1), t, i + 20, P, lifeA, 18)
        for i in range(14):
            u = clamp01((post - .2 - .05 * i) / 1.3)
            if 0 < u < 1: out.append(('g', TF[0] + (frac(i, 1) - .5) * 100, TF[1] - 30 - u * 190, 36 + 34 * u, 30 + 26 * u, P['deep'], .24 * math.sin(math.pi * u)))
        out.append(('g', TF[0], TF[1] - 2, 120, 26, P['deep'], .36 * smooth(post / .3) * (1 - smooth((post - 1.6) / .6))))   # the scorch stays a while
        for i in range(60):
            tb = .02 + .5 * frac(i, 1); tt = post - tb
            if not 0 <= tt < 1.2: continue
            a = frac(i, 3) * 6.283; r = (40 + 190 * frac(i, 4)) * ease_out(tt / .6); k = 1 - tt / 1.2
            out.append(('e', cx + math.cos(a) * r, cy + 20 + math.sin(a) * r * .4 - 130 * tt * (.4 + frac(i, 5)) + 90 * tt * tt, 9, 1.6, a - 1.2 * tt, (P['a1'], P['mid'], P['a2'])[i % 3], .85 * k * (.6 + .4 * math.sin(tt * 30 + i))))
    if t < imp + .9 and ti == 0:
        e = smooth((t - .05) / .2) * (1 - smooth((t - imp - .5) / .4)); out.append(('g', C[0] + 26, C[1] - 6, 36, 40, P['mid'], .25 * e))
    return out


# ------------------------------------------------------------------ dragon scale ward: heavy guard plates fall and settle into three orbits
def scale_ward(t, geo, ti=0):
    out = []; P = PAL['scale']; (chest, foot) = geo['targets'][ti]; fx, fy = foot; cx, cy = chest; imp = SPEC['dragonScaleWard'][1]
    fadeout = 1 - smooth((t - 1.85) / .4)
    ORB = ((60, .35, 1.0, 5), (74, 1.15, -.65, 5), (86, -1.2, .5, 5))           # radius, tilt (rad), spin speed, plate count
    BR = (96, 52, 14)
    for oi, (R, tilt, spd, n) in enumerate(ORB):
        lock = ease_out(clamp01((t - imp + .16 * (2 - oi) - .1) / .34)) if t >= imp - .3 else 0.0
        for k in range(n):
            drop = clamp01((t - .05 * k - .08 * oi) / (imp - .1)); fall = (1 - ease_out(drop)) ** 1.5
            a0 = spd * t * (1 + 1.5 * (1 - lock)) + k * 2 * math.pi / n + oi
            half = .30 - .03 * oi
            pts = []
            for j in range(24):
                a = a0 + (j / 23 - .5) * 2 * half; x = math.cos(a) * R; z = math.sin(a) * R
                y = z * math.sin(tilt) * 1.0 + fall * -170; px = cx + x * math.cos(tilt * .6); py = cy + y * 1.05 + z * .12
                pts.append((px, py))
            depth = math.sin(a0) * math.cos(tilt)
            alpha = (1.0 if depth > -.3 else .55) * fadeout * smooth(drop * 3)
            ws = [8.5 * math.sin(math.pi * (j / 23)) ** .6 + 1.6 for j in range(24)]
            stack(out, pts, ws, [(1.3, BR, 'mix', .9), (1.0, P['body'], 'mix', 1.0), (.5, P['mid'], 'mix', .85), (.16, P['light'], 'add', .95)], alpha)
            out.append(('k', pts, [w * 2.4 for w in ws], P['body'], .12 * alpha, 'add', 6))
            out.append(('k', pts, [1.0] * len(pts), P['light'], .5 * alpha, 'add', 1.0))
            if t >= imp:                                                       # a trailing glow as each plate wheels round
                tr = [(pts[0][0] - math.cos(a0 - 1.571) * 22 * (u / 5), pts[0][1]) for u in range(6)]
    if t >= imp:
        a = t - imp
        if a < .5:
            if ti == 0: out.append(('f', P['mid'], .12 * math.exp(-a * 16)))
            r = 24 + 130 * ease_out(a / .45); out.append(('r', fx, fy - 2, r, r * .28, 6 * (1 - a / .5) + .6, P['light'], .8 * (1 - ease_in(a / .5))))
            r2 = 40 + 90 * ease_out(a / .35); out.append(('r', cx, cy, r2, r2 * 1.25, 3 * (1 - a / .4) + .5, P['mid'], .6 * (1 - ease_in(a / .4))))
        for oi, (R, tilt, spd, n) in enumerate(ORB):                           # each orbit pulses in turn, a slow heavy heartbeat
            ph = (t * 1.1 - oi * .18) % 1.0
            pts = arc_pts(cx, cy, R * math.cos(tilt * .6), R * math.sin(abs(tilt)) * 1.05 + 2, 0, 6.283, 60, 0)
            out.append(('k', pts, [1.1] * len(pts), P['a2'], (.5 * math.exp(-ph * 3.5) + .14) * fadeout, 'add', 1.2))
        out.append(('g', cx, cy, 80, 110, P['body'], .1 * fadeout))
        for i in range(20):
            u = ((t * .35 + frac(i, 1)) % 1.0); ang = frac(i, 2) * 6.283 + t * .5
            out.append(('g', cx + math.cos(ang) * 80 * frac(i, 3), fy - 6 - u * 190, 7, 7, (P['light'], P['a1'], P['mid'])[i % 3], .6 * fadeout * math.sin(math.pi * u)))
    return out


# ------------------------------------------------------------------ dragon order: three war-drum beats, each answered by the whole field
def dragon_order(t, geo, ti=0):
    out = []; P = PAL['order']; C = geo['caster']; CF = geo['casterFoot']; imp = SPEC['dragonOrder'][1]
    BEATS = (imp, imp + .3, imp + .6); fadeout = 1 - smooth((t - 1.85) / .3)
    pre = clamp01(t / imp)
    if t < imp and ti == 0:
        for k in range(3):                                                    # the stance: light pulled into the chest, three short taps before the first beat
            tap = max(0.0, 1 - abs(t - (.15 + k * .17)) / .06); out.append(('g', C[0], C[1], 44 + 30 * tap, 54 + 30 * tap, P['body'], .12 + .3 * tap))
    for bi, tb in enumerate(BEATS):
        a = t - tb
        if a < 0: continue
        big = 1.0 + .5 * (bi == 2)
        if a < .14 and ti == 0: out.append(('f', P['mid'], (.1 + .08 * bi) * math.exp(-a * 24)))
        for r_i in range(3 if ti == 0 else 0):                                                  # the beat leaves the chest as nested sweeping arcs
            d = r_i * .05; tt = a - d
            if tt < 0: continue
            r = (40 + 470 * ease_out(tt / .85)) * big; fade = 1 - ease_in(tt / .9)
            out.append(('a', C[0] + 20, C[1], r, r * .52, -1.15, 1.15, (7.0 - r_i * 1.8) * fade + .8, (P['light'], P['a1'], P['mid'])[r_i], .85 * fade))
        if ti == 0: r = 20 + 130 * big * ease_out(a / .5); out.append(('r', CF[0], CF[1] - 2, r, r * .27, 6 * (1 - a / .55) + .6, P['mid'], .8 * (1 - ease_in(a / .55))))
        for n, (chest, foot) in [(ti, geo['targets'][ti])]:                     # the answer: a ring snaps inward onto each ally with the flash
            hit = a - .1 - .05 * n
            if hit < 0: continue
            cx, cy = chest; fx, fy = foot
            R0 = 130 * big; r = R0 * (1 - ease_out(hit / .26)) + 14; al = (1 - ease_in(hit / .3)) * smooth(hit / .04)
            out.append(('r', cx, cy, r * .8, r * 1.3, 4.0 * al + .5, (P['a1'], P['light'], P['mid'])[bi], .9 * al))
            out.append(('r', fx, fy - 2, r * 1.4, r * 1.4 * .27, 3.4 * al + .5, P['mid'], .7 * al))
            if hit < .3:
                out.append(('g', cx, cy, 70 * (1 - ease_in(hit / .3)) + 36, 92 * (1 - ease_in(hit / .3)) + 46, P['a1'], .45 * al * (1 + .4 * bi))); out.append(('g', cx, cy, 24, 32, (255, 255, 255), .5 * al))
            for i in range(10):
                ang = frac(i + 11 * bi, 3) * 6.283; d = (30 + 70 * frac(i + 11 * bi, 4)) * ease_out(hit / .4)
                out.append(('e', cx + math.cos(ang) * d, cy + math.sin(ang) * d * .8 - 20 * hit, 9, 1.5, ang, (P['a1'], P['light'], P['a2'])[i % 3], .8 * (1 - ease_in(hit / .55))))
    last = t - BEATS[2]
    for n, (chest, foot) in [(ti, geo['targets'][ti])]:                          # after the last beat each ally keeps the rhythm: a heartbeat of light
        if last < .15: continue
        cx, cy = chest; ph = (t * 2.0 - n * .2) % 1.0; env = smooth((last - .15) / .25) * fadeout
        out.append(('g', cx, cy, 52 + 14 * math.exp(-ph * 5), 80 + 18 * math.exp(-ph * 5), P['body'], (.14 + .3 * math.exp(-ph * 5)) * env))
        out.append(('r', cx, cy, 44 + 30 * ph, 70 + 40 * ph, 1.8 * (1 - ph) + .4, P['a1'], .7 * (1 - ph) * env))
        for i in range(12):
            u = ((t * .5 + frac(i, 1)) % 1.0); ang = frac(i, 2) * 6.283
            out.append(('g', cx + math.cos(ang) * 40 * frac(i, 3), foot[1] - 6 - u * 150, 7, 7, (P['a1'], P['light'], P['mid'])[i % 3], .6 * env * math.sin(math.pi * u)))
    return out


# ================================================================== v7: healing, three tiers with three different characters
PAL['heal'] = dict(deep=(8, 66, 40), body=(40, 190, 100), mid=(110, 235, 150), light=(215, 255, 228), a1=(255, 232, 150), a2=(120, 240, 222))
SPEC.update({'healMicro': (1.35, .1, True), 'healStandard': (1.8, .1, True), 'healStrong': (2.3, .1, True)})
DIM.update({'healMicro': (.26, (.82, .96, .86)), 'healStandard': (.28, (.8, .96, .85)), 'healStrong': (.32, (.78, .95, .84))})


def thin_ring(out, cx, cy, rx, ry, w, col, a): out.append(('r', cx, cy, rx, ry, w, col, a))


# ------------------------------------------------------------------ micro: dew drops of light drifting up, one soft breath
def heal_micro(t, geo, ti=0):
    out = []; P = PAL['heal']; (chest, foot) = geo['targets'][ti]; fx, fy = foot; cx, cy = chest
    fade = 1 - smooth((t - 1.1) / .25)
    r = 10 + 40 * ease_out(t / .6); thin_ring(out, fx, fy - 2, r, r * .27, 1.5 * (1 - t / .7) + .4, P['mid'], .7 * (1 - ease_in(t / .7)))
    pulse = math.exp(-((t - .28) / .13) ** 2); out.append(('g', cx, cy, 60, 74, P['body'], .4 * pulse)); out.append(('g', cx, cy, 18, 22, P['light'], .6 * pulse))
    thin_ring(out, cx, cy, 14 + 40 * ease_out((t - .2) / .45), 18 + 52 * ease_out((t - .2) / .45), 1.2, P['light'], .6 * (1 - ease_in((t - .2) / .5)) * smooth((t - .2) / .05))
    for i in range(7):
        u = clamp01((t - .05 * i) / 1.0)
        if u <= 0 or u >= 1: continue
        def pos(uu): return (fx + (frac(i, 2) - .5) * 44 + math.sin(uu * 5.5 + i * 1.7) * (11 + 9 * frac(i, 3)), fy - 8 - uu * (110 + 50 * frac(i, 4)))
        pts = [pos(max(0.0, u - .16 * (1 - q / 11))) for q in range(12)]; env = math.sin(math.pi * u) ** .8 * fade
        out.append(('k', pts, [.5 + 3.2 * (q / 11) for q in range(12)], P['mid'], .9 * env, 'add', 1.2))
        x, y = pos(u); col = (P['light'], P['a1'], P['mid'])[i % 3]
        out.append(('g', x, y, 15, 15, col, .7 * env)); out.append(('g', x, y, 4.6, 4.6, (255, 255, 255), 1.0 * env))
    return out


# ------------------------------------------------------------------ standard: a double helix of light, a soft dome, shimmering rain
def heal_standard(t, geo, ti=0):
    out = []; P = PAL['heal']; (chest, foot) = geo['targets'][ti]; fx, fy = foot; cx, cy = chest; fade = 1 - smooth((t - 1.45) / .3)
    for q in range(2):                                                                           # two fine ribbons winding upward, one behind the other
        head = ease_out(clamp01(t / .9)); tail = ease_in(clamp01((t - .7) / .8)); pts = []; ws = []
        for j in range(80):
            u = j / 79
            if u > head or u < tail * .9: continue
            ang = q * math.pi + u * 11 - t * 3.2; rr = 38 - 8 * u
            pts.append((fx + math.cos(ang) * rr, fy - 6 - u * 170 + math.sin(ang) * rr * .3)); ws.append((3.2 * math.sin(math.pi * u) ** .6 + .6))
        if len(pts) > 3: stack(out, pts, ws, [(3.0, P['body'], 'add', .16), (1.0, P['mid'], 'add', .6), (.4, P['light'], 'add', .95)], fade)
    if t > .3:
        a = t - .3
        for k in range(2):
            d = k * .12; aa = a - d
            if aa >= 0:
                r = 20 + 80 * ease_out(aa / .6); thin_ring(out, fx, fy - 2, r, r * .27, 1.8 * (1 - aa / .7) + .4, (P['mid'], P['a2'])[k], .75 * (1 - ease_in(aa / .7)))
                thin_ring(out, cx, cy, r * .6, r * 1.1, 1.2, (P['light'], P['mid'])[k], .5 * (1 - ease_in(aa / .7)))
        out.append(('g', cx, cy, 70 * (.5 + ease_out(a / .5)), 100 * (.5 + ease_out(a / .5)), P['body'], .22 * (1 - ease_in(a / 1.0))))
    for i in range(46):                                                                          # shimmering rain of light falling through the aura
        tb = .3 + .9 * frac(i, 1); tt = t - tb
        if not 0 <= tt < .7: continue
        x = fx + (frac(i, 2) - .5) * 150; y = cy - 150 + tt * (190 + 60 * frac(i, 3)); k = math.sin(math.pi * tt / .7) ** .8 * fade
        out.append(('e', x, y, 1.2, 8 + 5 * frac(i, 4), 0, (P['light'], P['mid'], P['a1'])[i % 3], .8 * k)); out.append(('g', x, y, 5, 5, P['mid'], .4 * k))
    for i in range(8):                                                                           # glints on the body
        tb = .4 + .8 * frac(i, 1); tt = t - tb
        if 0 <= tt < .4:
            ang = frac(i, 2) * 6.283; x = cx + math.cos(ang) * 28 * frac(i, 3); y = cy + math.sin(ang) * 50 * frac(i, 4); k = math.sin(math.pi * tt / .4) * fade
            out.append(('e', x, y, 11, 1.1, 0, P['light'], .9 * k)); out.append(('e', x, y, 11, 1.1, 1.571, P['light'], .9 * k)); out.append(('g', x, y, 7, 7, P['mid'], .5 * k))
    return out


# ------------------------------------------------------------------ strong: aurora curtains, a heartbeat, rays of growth, a fountain that falls back as light
def heal_strong(t, geo, ti=0):
    out = []; P = PAL['heal']; (chest, foot) = geo['targets'][ti]; fx, fy = foot; cx, cy = chest; fade = 1 - smooth((t - 1.85) / .4)
    for q in range(4):                                                                           # curtains of light waving round the body
        env = smooth((t - .1 - .06 * q) / .5) * fade; pts = []; ws = []
        for j in range(50):
            u = j / 49; pts.append((fx + (q - 1.5) * 34 + math.sin(u * 4 + t * 1.6 + q * 2) * (14 + 12 * u) , fy - 4 - u * (150 + 40 * frac(q, 1)))); ws.append(20 * math.sin(math.pi * (u * .85 + .08)) ** .8 + 2)
        out.append(('k', pts, ws, (P['body'], P['a2'], P['mid'], P['body'])[q], .3 * env, 'add', 10)); out.append(('k', pts, [w * .1 + .5 for w in ws], (P['light'], P['mid'])[q % 2], .4 * env, 'add', 1.0))
    for k, tb in enumerate((.3, .62)):                                                           # two heartbeats
        a = t - tb
        if a >= 0:
            r = 14 + 130 * ease_out(a / .6); thin_ring(out, cx, cy, r * .9, r * 1.15, 1.8 * (1 - a / .65) + .4, (P['light'], P['mid'])[k], .8 * (1 - ease_in(a / .65)))
            thin_ring(out, fx, fy - 2, r * 1.2, r * 1.2 * .27, 1.8 * (1 - a / .65) + .4, P['mid'], .7 * (1 - ease_in(a / .65)))
            out.append(('g', cx, cy, 60 * (1 - ease_in(a / .3)) + 30, 80 * (1 - ease_in(a / .3)) + 40, P['a1'] if k else P['body'], .35 * (1 - ease_in(a / .35))))
    if t > .3 and t < 1.5:
        env = smooth((t - .3) / .2) * (1 - smooth((t - 1.1) / .4))
        for k in range(30):                                                                      # fine rays of growth, slowly turning
            ang = k * 2 * math.pi / 30 + t * .25; L = 70 + 80 * frac(k, 2); s = 1 + .08 * math.sin(t * 4 + k)
            out.append(('e', cx + math.cos(ang) * L * s / 2, cy + math.sin(ang) * L * s / 2 * .95, L * s / 2, 1.1, ang, (P['mid'], P['light'], P['a2'], P['mid'])[k % 4], .4 * env))
    if t > .3 and ti == 0: out.append(('f', P['a1'], .1 * math.exp(-(t - .3) * 14)))
    for i in range(44):                                                                          # a fountain of light thrown up and falling back
        tb = .25 + .5 * frac(i, 1); tt = t - tb
        if not 0 <= tt < 1.3: continue
        vx = (frac(i, 2) - .5) * 120; vy = -(170 + 100 * frac(i, 3))
        x = fx + vx * tt; y = fy - 10 + vy * tt + 230 * tt * tt; vyn = vy + 460 * tt
        k = math.sin(math.pi * clamp01(tt / 1.3)) ** .6 * fade; col = (P['light'], P['mid'], P['a1'], P['a2'])[i % 4]
        sp = math.hypot(vx, vyn)
        out.append(('e', x - vx * .012, y - vyn * .012, max(3, sp * .02), 1.2, math.atan2(vyn, vx), col, .85 * k)); out.append(('g', x, y, 6, 6, col, .5 * k)); out.append(('g', x, y, 2.4, 2.4, (255, 255, 255), .9 * k))
    out.append(('g', cx, cy, 80 + 6 * math.sin(t * 5), 110 + 6 * math.sin(t * 5), P['body'], .14 * smooth((t - .3) / .4) * fade))
    return out


# ------------------------------------------------------------------ rally: a call that rolls out over every ally and lifts them
PAL['rally'] = dict(deep=(120, 60, 8), body=(240, 150, 30), mid=(255, 213, 96), light=(255, 250, 215), a1=(255, 255, 255), a2=(255, 196, 70))
PAL['sweep'] = dict(deep=(20, 50, 140), body=(92, 170, 255), mid=(190, 232, 255), light=(255, 255, 255), a1=(255, 214, 120), a2=(150, 200, 255))
SPEC.update({'rally': (2.0, .56, True), 'sweep': (2.0, 1.048, False)})


def rally_call(t, geo, ti=0):
    out = []; P = PAL['rally']; C = geo['caster']; CF = geo['casterFoot']; (chest, foot) = geo['targets'][ti]; imp = .56
    fx, fy = foot; cx, cy = chest
    if ti == 0:                                                              # the call: a beam of light gathers over the caster, then waves leave along the ground
        gat = smooth(t / (imp * .9)) * (1 - smooth((t - imp - .1) / .3))
        out.append(('g', C[0], C[1] - 10, 50 * gat + 4, 70 * gat + 4, P['body'], .35 * gat))
        out.append(('e', C[0], C[1] - 70 * gat, 130 * gat + 6, 7, -1.5708, P['mid'], .8 * gat))
        out.append(('e', C[0], C[1] - 70 * gat, 90 * gat + 4, 3, -1.5708, P['light'], gat))
        for w in range(3):
            u = (t - imp - .16 * w) / .8
            if 0 < u < 1:
                r = 30 + 330 * ease_out(u)
                out.append(('r', CF[0], CF[1] - 2, r, r * .26, 3.2 * (1 - u) + .8, (P['mid'], P['a2'], P['light'])[w], .85 * (1 - ease_in(u))))
        if imp <= t < imp + .25: out.append(('f', P['mid'], .2 * math.exp(-(t - imp) * 14)))
    reach = imp + .1 + .3 * clamp01(abs(fx - CF[0]) / 420.0); tt = t - reach  # the wave arrives at each ally a moment after it left the caster
    if tt >= 0:
        env = smooth(tt / .18) * (1 - smooth((tt - 1.0) / .5)); grow = smooth(tt / .25)
        out.append(('g', fx, fy - 2, 70 * env + 4, 20 * env + 2, P['body'], .5 * env))
        out.append(('e', fx, fy - 90 * grow, 110 * grow + 4, 22, -1.5708, P['body'], .30 * env))
        out.append(('e', fx, fy - 90 * grow, 110 * grow + 4, 12, -1.5708, P['mid'], .5 * env))
        out.append(('e', fx, fy - 90 * grow, 108 * grow + 4, 5, -1.5708, P['light'], .8 * env))
        r = 14 + 60 * ease_out(tt / .4); out.append(('r', fx, fy - 2, r, r * .3, 2.4 * (1 - ease_in(tt / .9)) + .8, P['mid'], .9 * (1 - ease_in(tt / 1.1))))
        out.append(('g', cx, cy, 70 * env + 4, 95 * env + 4, P['body'], .22 * env))
        out.append(('r', cx, cy - 78, 26 * grow + 2, 8 * grow + 1, 1.6, P['a1'], .7 * env))
        for k in range(3):                                                   # chevrons climb the body: more, stronger
            u = (tt * .9 + k / 3.0) % 1.0; y = fy - 20 - u * 130; al = env * math.sin(math.pi * u)
            out.append(('e', cx - 8, y + 5, 12, 2.6, -.75, P['light'], al)); out.append(('e', cx + 8, y + 5, 12, 2.6, .75, P['light'], al))
            out.append(('g', cx, y, 16, 12, P['mid'], .35 * al))
    return out


# ------------------------------------------------------------------ sweep: one huge crescent swung through every enemy
def sweep_arc(t, geo, ti=0):
    out = []; P = PAL['sweep']; C = geo['caster']; (T, TF) = geo['targets'][ti]; imp = 1.048
    d = 1.0 if geo['targets'][0][0][0] >= C[0] else -1.0
    far = max(abs(c[0] - C[0]) for c, f in geo['targets']); R = max(220.0, far + 90.0); RY = 100.0; ex, ey = C[0] + d * 30, C[1] + 25
    post = t - imp
    def pt(th, k=1.0): return (ex + d * math.cos(th) * R * k, ey + math.sin(th) * RY * k)
    if ti == 0:
        gat = smooth(t / (imp * .85)) * (1 - smooth(post / .15))
        out.append(('g', C[0] + d * 26, C[1] - 6, 30 * gat + 3, 34 * gat + 3, P['mid'], .45 * gat))
        out.append(('e', C[0] + d * 26, C[1] - 6, 48 * gat + 2, 2.2, -.9 * d, P['light'], .9 * gat))
        if -.05 <= post < 1.0:
            head = lerp(3.4, 6.2, ease_out(clamp01(post / .24))); env = 1 - smooth((post - .24) / .5)
            for echo in range(2):
                h = head - .35 * echo; k = 1 - .07 * echo; pts = []; ws = []
                for j in range(40):
                    u = j / 39.0; th = max(3.4, h - 1.5 * u)
                    pts.append(pt(th, k)); ws.append(26 * (1 - u) ** .8 * (.5 + .5 * math.sin(math.pi * clamp01((th - 3.4) / 2.8))) + 2)
                stack(out, pts, ws, [(2.2, P['deep'], 'add', .25), (1.0, P['body'], 'add', .55), (.5, P['mid'], 'add', .85), (.2, P['light'], 'add', .95)], env * (1.0 if echo == 0 else .55))
            hp = pt(head)
            if post < .5: out.append(('g', hp[0], hp[1], 40, 40, P['body'], .5 * env)); out.append(('g', hp[0], hp[1], 20, 20, P['light'], .8 * env))
        if imp <= t < imp + .25: out.append(('f', P['mid'], .22 * math.exp(-post * 14)))
    hit = imp + .02 + .22 * clamp01(abs(T[0] - C[0]) / R); hp_ = t - hit
    if 0 <= hp_ < .7:                                                         # the crescent reaches this enemy
        k = 1 - ease_in(hp_ / .5)
        out.append(('g', T[0], T[1], 150 * (.6 + ease_out(hp_ / .2)), 100 * (.6 + ease_out(hp_ / .2)), P['body'], .5 * k))
        out.append(('g', T[0], T[1], 60, 50, P['light'], .8 * (1 - ease_in(hp_ / .18))))
        out.append(('e', T[0], T[1], 90 * ease_out(hp_ / .12), 4, -.55 * d, P['light'], 1 - ease_in(hp_ / .4)))
        out.append(('e', T[0], T[1], 70 * ease_out(hp_ / .12), 3, .45 * d, P['mid'], 1 - ease_in(hp_ / .4)))
        for j in range(10):
            jj = j + 31 * ti; a = frac(jj, 3) * 6.2832; r = (30 + 110 * frac(jj, 4)) * ease_out(hp_ / .4)
            out.append(('e', T[0] + math.cos(a) * r, T[1] + math.sin(a) * r * .6, 10, 1.6, a, (P['light'], P['mid'], P['a1'])[j % 3], max(0.0, 1 - hp_ / .6)))
        rr = 20 + 120 * ease_out(hp_ / .5); out.append(('r', TF[0], TF[1] - 2, rr, rr * .26, 2.4 * max(0.0, 1 - hp_ / .6) + .6, P['mid'], .7 * (1 - ease_in(hp_ / .6))))
    return out


def multi(fn):
    """Run a single-target effect once per target. Caster-side parts are emitted only for the first target (ti == 0)."""
    def run(t, geo):
        out = []
        for ti in range(len(geo['targets'])): out += fn(t, geo, ti)
        return out
    return run


_SINGLE = {'starlightPulse': starlight, 'dragonSoulWard': soul, 'dragonScaleWard': scale_ward, 'runeSlash': rune_slash, 'runeWard': rune_ward,
           'battleRune': battle_rune, 'dragonFlame': dragon_flame, 'dragonOrder': dragon_order,
           'healMicro': heal_micro, 'healStandard': heal_standard, 'healStrong': heal_strong, 'rally': rally_call, 'sweep': sweep_arc}
# ------------------------------------------------------------------ atmosphere: themed particles over the whole stage
# Three layers per skill, all closed-form in t with fixed-id randomness: particles that GATHER into the caster while the power builds,
# a FIELD of particles that fills the whole stage with the skill's own weather (dragon flame = a hot updraft of embers, starlight =
# falling twinkling stars, soul ward = rising blue wisps, scale ward = tumbling gilded flakes, runes = glyph fragments, ...),
# and a BURST from every target at the release.
# id: (kind, motion, palette, field count, gather count, burst count per target, rate, size, release time)
ATMOS = {
    'starlightPulse': ('star', 'fall', 'starlight', 70, 28, 22, .42, 1.3, .75),
    'dragonSoulWard': ('wisp', 'rise', 'soul', 64, 28, 18, .34, 1.4, .38),
    'dragonScaleWard': ('flake', 'fall', 'scale', 60, 24, 22, .30, 1.3, .56),
    'runeSlash': ('rune', 'gust', 'rune', 66, 26, 24, .55, 1.3, 1.048),
    'runeWard': ('rune', 'rise', 'rune', 60, 26, 18, .30, 1.3, .72),
    'battleRune': ('spark', 'orbit', 'battle', 60, 26, 24, .50, 1.3, .56),
    'dragonFlame': ('ember', 'rise', 'flame', 64, 22, 20, .50, 1.45, .46),
    'dragonOrder': ('ember', 'gust', 'order', 66, 28, 22, .50, 1.3, .56),
    'rally': ('star', 'rise', 'rally', 60, 24, 18, .34, 1.3, .56),
    'sweep': ('ember', 'gust', 'sweep', 60, 22, 20, .60, 1.2, 1.048),
    'healMicro': ('mote', 'rise', 'heal', 20, 0, 0, .30, 1.1, .3),
    'healStandard': ('mote', 'rise', 'heal', 28, 0, 0, .30, 1.25, .3),
    'healStrong': ('mote', 'rise', 'heal', 36, 0, 0, .30, 1.4, .3),
}


def atmos_cols(name):
    if name == 'starlight': return [(255, 255, 255), (222, 212, 255), (160, 136, 255), (255, 255, 255)]
    if name == 'soul': return [(235, 250, 255), (130, 210, 255), (56, 140, 255), (235, 250, 255)]
    P = PAL[name]; return [P['light'], P['mid'], P['a2'], P['a1']]


def particle(out, kind, x, y, vx, vy, a, s, col, t, i):
    if a < .012: return
    if kind == 'ember':
        out.append(('e', x, y, 18 * s, 3 * s, math.atan2(vy, vx), col, a * .95)); out.append(('g', x, y, 11 * s, 11 * s, col, a * .4))
    elif kind == 'star':
        tw = .55 + .45 * math.sin(t * 9 + i * 1.7); L = 22 * s * (.6 + .4 * tw)
        out.append(('e', x, y, L, 1.8 * s, 0.0, col, a * tw)); out.append(('e', x, y, L * .8, 1.6 * s, 1.5708, col, a * tw)); out.append(('g', x, y, 10 * s, 10 * s, col, a * tw * .35))
    elif kind == 'wisp':
        out.append(('g', x, y, 13 * s, 13 * s, col, a * .85)); out.append(('g', x - vx * .06, y - vy * .06, 9 * s, 9 * s, col, a * .55)); out.append(('g', x - vx * .12, y - vy * .12, 6.5 * s, 6.5 * s, col, a * .35))
    elif kind == 'flake':
        tum = t * 3 + i; out.append(('e', x, y, 13 * s * (.35 + .65 * abs(math.cos(tum))), 5 * s, tum * .7, col, a)); out.append(('g', x, y, 7 * s, 7 * s, col, a * .25))
    elif kind == 'rune':
        a0 = t * 2 + i; out.append(('a', x, y, 11 * s, 11 * s, a0, a0 + 4.2, 2.0, col, a)); out.append(('g', x, y, 14 * s, 14 * s, col, a * .35))
    elif kind == 'spark':
        out.append(('e', x, y, 13 * s, 2.2 * s, math.sin(t * 40 + i) * 1.5, col, a)); out.append(('g', x, y, 9 * s, 9 * s, col, a * .5))
    else:
        out.append(('g', x, y, 9 * s, 9 * s, col, a * .8)); out.append(('g', x, y, 3.5 * s, 3.5 * s, col, a))


def atmosphere(skill, t, geo):
    spec = ATMOS.get(skill)
    if spec is None: return []
    kind, motion, pal, NF, NG, NB, rate, size, imp = spec
    dur = SPEC[skill][0]
    if t < 0 or t >= dur: return []
    cols = atmos_cols(pal); out = []
    C = geo['caster']; Ts = [c for c, f in geo['targets']]; gy = geo['ground']
    xs = [C[0]] + [p[0] for p in Ts]; x0 = min(xs) - 170; x1 = max(xs) + 170; top = gy - 330
    mx = sum(p[0] for p in Ts) / len(Ts); my = sum(p[1] for p in Ts) / len(Ts); d = 1.0 if Ts[0][0] >= C[0] else -1.0
    amb = smooth(t / (imp * .8 + .05)) * (1 - smooth((t - dur * .62) / (dur * .34)))
    lvl = amb * (.45 + .55 * smooth((t - imp * .7) / .4))
    for i in range(NF):                                                     # the field: the skill's own weather across the stage
        sp = (.55 + .9 * frac(i, 3)) * rate; q = t * sp + frac(i, 2); lane = int(math.floor(q)); cyc = q - lane
        ux = frac(i + 17 * lane, 5); vz = frac(i, 4); sway = math.sin(cyc * 6.2832 * (1 + vz) + i)
        if motion == 'rise':
            H = 240 + 90 * vz; x = x0 + (x1 - x0) * ux + sway * 16 * (.4 + cyc); y = gy + 10 - cyc * H; vx = sway * 10; vy = -H * sp
        elif motion == 'fall':
            H = gy - top + 20; x = x0 + (x1 - x0) * ux + sway * 22 * (.4 + cyc); y = top - 20 + cyc * H; vx = sway * 12; vy = H * sp
        elif motion == 'gust':
            W = x1 - x0 + 180; x = (x0 - 90 if d > 0 else x1 + 90) + d * cyc * W; y = gy - 30 - 230 * frac(i + 7 * lane, 6) + sway * 14; vx = d * W * sp; vy = 0.0
        else:
            w = (.8 + 1.2 * vz) * (1.0 if i % 2 == 0 else -1.0); ang = t * w + i * 2.399; R = 60 + 190 * ux
            x = mx + math.cos(ang) * R * 1.2; y = my + math.sin(ang) * R * .35 - 40 * cyc; vx = -math.sin(ang) * R * 1.2 * w; vy = math.cos(ang) * R * .35 * w - 40 * sp
        a = lvl * math.sin(math.pi * cyc) ** .8 * (.65 + .35 * frac(i, 7))
        particle(out, kind, x, y, vx, vy, a, size * (.7 + .6 * vz), cols[i % 4], t, i)
    if NG and t < imp + .02:                                                  # gather: the power is drawn into the caster
        for j in range(NG):
            e = smooth((t - .04 - .3 * imp * frac(j, 3)) / (imp * .8))
            if e <= .01 or e >= 1: continue
            a0 = frac(j, 1) * 6.2832 + t * (1.4 + frac(j, 2)); R0 = 130 + 150 * frac(j, 2); r = R0 * (1 - e) ** 1.4
            x = C[0] + math.cos(a0) * r; y = C[1] + math.sin(a0) * r * .6
            a = smooth(e * 6) * (1 - smooth((e - .85) / .15)) * smooth(t / .12) * .9
            particle(out, kind, x, y, C[0] - x, C[1] - y, a, size, cols[j % 4], t, j + 100)
    post = t - imp
    if NB and post > 0:                                                       # burst: every target throws the power back out
        for ti, T in enumerate(Ts):
            for j in range(NB):
                jj = j + 31 * ti; tt = post - (.02 + .22 * frac(jj, 5)); life = 1.0 + .6 * frac(jj, 6)
                if not 0 <= tt < life: continue
                ang = frac(jj, 7) * 6.2832; spd = 80 + 170 * frac(jj, 8); rr = spd * ease_out(tt / .7); slow = 1 - clamp01(tt / .7)
                if motion == 'fall': dy = 90 * tt * tt; gv = 180 * tt
                else: dy = -70 * tt; gv = -70.0
                x = T[0] + math.cos(ang) * rr; y = T[1] + math.sin(ang) * rr * .55 + dy
                a = (1 - tt / life) ** .8 * smooth(tt / .05) * .95
                particle(out, kind, x, y, math.cos(ang) * spd * slow, math.sin(ang) * spd * .55 * slow + gv, a, size * 1.1, cols[jj % 4], t, jj + 200)
    return out


def with_atmosphere(fn, skill):
    def run(t, geo): return fn(t, geo) + atmosphere(skill, t, geo)
    return run


GENERATORS = {k: with_atmosphere(multi(v), k) for k, v in _SINGLE.items()}
