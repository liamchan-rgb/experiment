"""Continuous procedural skill effects: the way the dragon-flame demo gets its smoothness.

Every effect is a closed-form function of time that returns a list of primitives (soft glows, small hard blocks, rings,
segments). Trails are the same path sampled at delayed times, so motion is continuous at any frame rate; every element
carries a soft additive glow, and a bloom pass (or its stacked-glow approximation in the game) removes the pixel edges.

Primitives (stage points, y grows downward):
  ('g', x, y, rx, ry, rgb, alpha)            soft radial glow
  ('b', x, y, size, rgb, alpha)              small hard square (accent)
  ('r', x, y, rx, ry, width, rgb, alpha)     ring on an ellipse
  ('s', x1, y1, x2, y2, width, rgb, alpha)   segment (glow along it + bright core)
  ('d', x, y, rx, ry, rgb, alpha)            hard diamond (scale plates)
  ('c', x, y, r, rgb, alpha)                 solid disc with normal blending (keeps dark, saturated colour; body of the dragon)
Geometry `geo`: dict(caster=(x,y chest), casterFoot=(x,y), targets=[(chest, foot), ...], center=(x,y), ground=y).
`t` is seconds since the skill started; `impact` is when it lands (peak), `duration` the total length.
"""
import math

SPEC = {  # id: (duration, impact, support)
    'starlightPulse': (1.25, 0.75, False),
    'rally': (1.67, 0.0, True),
    'sweep': (1.0, 0.45, False),
    'dragonSoulWard': (1.67, 0.0, True),
    'dragonScaleWard': (1.0, 0.0, True),
}
TONE = {
    'starlightPulse': [(255, 255, 255), (205, 196, 255), (126, 108, 255), (64, 48, 190)],
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


def tone_at(skill, u):
    """u in 0..1 from hot core to cool tail."""
    T = TONE[skill]
    return T[min(len(T) - 1, int(u * (len(T) - 0.01)))]


# ------------------------------------------------------------------ starlight pulse: a comet of star dust
def starlight(t, geo):
    out = []; C = geo['caster']; T = geo['targets'][0][0]; imp = SPEC['starlightPulse'][1]
    W = TONE['starlightPulse']
    def path(tt):
        s = ease_in(clamp01(tt / imp)) ** 0.8
        x, y = lerp2(C, T, s)
        return x, y - 64 * math.sin(math.pi * s) * (1 - 0.3 * s), s
    if t < imp + 0.02:
        hx, hy, hs = path(t)
        for i in range(28, -1, -1):
            tt = t - i * 0.02
            if tt < 0: continue
            x, y, s = path(tt)
            u = i / 28
            wob = math.sin(tt * 30 + i) * 3 * u
            x += wob; y += math.cos(tt * 26 + i) * 3 * u
            r = 15 * (1 - .75 * u) * (0.6 + 0.4 * clamp01(tt * 8))
            col = tone_at('starlightPulse', u)
            out.append(('g', x, y, r * 2.0, r * 2.0, col, 0.24 * (1 - .5 * u)))
            out.append(('b', x, y, max(1.5, 5 * (1 - u)), W[0] if u < .5 else W[1], 0.9 * (1 - u * .6)))
            if i % 2 == 0:
                jx = math.sin(i * 12.9) * 11 * u; jy = math.cos(i * 7.7) * 11 * u - 6 * u
                out.append(('b', x + jx, y + jy, max(1.2, 2.6 * (1 - u)), W[1], 0.8 * (1 - u)))
        fade = clamp01((imp - t) / 0.05)
        out.append(('g', hx, hy, 46, 46, W[2], 0.38 * fade)); out.append(('g', hx, hy, 22, 22, W[1], 0.5 * fade))
        glint(out, hx, hy, 30 + 4 * math.sin(t * 20), 2.4, W[0], fade, t * 3)
        for k in range(6):
            a = t * 9 + k * math.pi / 3; rr = 20 + 5 * math.sin(t * 6 + k)
            out.append(('b', hx + math.cos(a) * rr, hy + math.sin(a) * rr * .6, 3, W[0], .9 * fade))
    a = t - imp
    if a >= 0:
        cx, cy = T
        if a < .25: out.append(('f', W[2], .16 * math.exp(-a * 16)))
        out.append(('g', cx, cy, 110 * (.5 + ease_out(a / .3)), 110 * (.5 + ease_out(a / .3)), W[2], .42 * (1 - ease_in(a / .5))))
        out.append(('g', cx, cy, 40, 40, W[1], .6 * (1 - ease_in(a / .22))))
        for j, d in enumerate((0, .08)):
            if a - d >= 0:
                r = 14 + 100 * ease_out((a - d) / .42)
                out.append(('r', cx, cy, r, r * .8, 2.5 * (1 - (a - d) / .5), W[1], .9 * (1 - ease_in((a - d) / .5))))
        if a < .5:
            for k in range(8):
                ang = k * math.pi / 4 + .2
                L = (90 if k % 2 == 0 else 52) * ease_out(a / .12) * (1 - ease_in((a - .15) / .35))
                if L > 1: out.append(('s', cx, cy, cx + math.cos(ang) * L, cy + math.sin(ang) * L, 3.4 * (1 - a / .5), W[0], 1 - a / .5))
        for i in range(44):
            life = .45 + .5 * frac(i, 2); tt = a - .02 * frac(i, 5)
            if not 0 <= tt < life: continue
            ang = frac(i, 3) * 6.283; spd = 150 + 240 * frac(i, 4); tr = tt / life
            d = spd * (1 - math.exp(-tt * 5)) / 5
            x = cx + math.cos(ang) * d; y = cy + math.sin(ang) * d * .8 + 120 * tt * tt * (frac(i, 6) > .5)
            tw = .6 + .4 * math.sin(tt * 40 + i)
            out.append(('g', x, y, 9, 9, W[2], .55 * (1 - tr) * tw))
            out.append(('b', x, y, 2.5 * (1 - .6 * tr), W[0], (1 - tr) * tw))
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
    N = 52; coil = ease_out(clamp01(t / .5)); dissolve = smooth((t - .95) / .35)
    shell = smooth((t - .55) / .35) * (1 - smooth((t - 1.2) / .45))
    def body(tt, i):
        ph = tt * 5.4 - i * .13
        r = lerp(70, 40, coil) * (1 + .06 * math.sin(i * .33 + tt * 3))
        rise = 20 + 116 * (1 - math.exp(-max(0, tt) * 2.2)) - i * 1.05 + math.sin(ph * .5) * 6
        return fx + math.cos(ph) * r, fy - rise + math.sin(ph) * r * .34, math.sin(ph)
    if t < 1.35:
        env = 1 - dissolve
        pts = [body(t, i) for i in range(N)]
        def seg_size(i, dep): return (17 * (1 - i / N) ** .8 + 5) * (.82 + .18 * dep)
        live = [i for i in range(N) if not (i > N * (1 - dissolve))]
        if env > .01:
            for i in reversed(live):                      # pass 1: silhouette, so the dark edge only shows on the outline
                x, y, dep = pts[i]; sz = seg_size(i, dep); al = (1.0 if dep > -.2 else .6) * env
                out.append(('g', x, y, sz * 1.7, sz * 1.7, D[2], .16 * env))
                out.append(('c', x, y, sz * .56 + 1.6, (10, 30, 96), .95 * al))
            for i in reversed(live):                      # pass 2: body
                x, y, dep = pts[i]; sz = seg_size(i, dep); al = (1.0 if dep > -.2 else .6) * env
                out.append(('c', x, y, sz * .56, (34, 98, 220) if i / N > .2 else (70, 150, 255), al))
            for i in reversed(live):                      # pass 3: light along the back
                x, y, dep = pts[i]; sz = seg_size(i, dep); al = (1.0 if dep > -.2 else .6) * env
                out.append(('c', x - sz * .1, y - sz * .2, sz * .28, (140, 205, 255), .85 * al))
                if i % 4 == 0: out.append(('b', x + math.sin(i * 9.1) * sz * .5, y - sz * .62, max(2, sz * .24), D[0], .95 * env))
        hx, hy, hd = pts[0]; nx, ny, _ = pts[3]
        ang = math.atan2(hy - ny, hx - nx); c, s = math.cos(ang), math.sin(ang)
        def P(u, v): return hx + c * u - s * v, hy + s * u + c * v
        for k, (u, v, z, col) in enumerate([(4, 0, 14, D[0]), (13, -1, 11, D[1]), (-6, 1, 12, D[2])]):
            x, y = P(u, v); out.append(('c', x, y, z * .75 + 1.5, (10, 30, 96), .95 * env)); out.append(('c', x, y, z * .75, (60, 140, 255) if k != 0 else (140, 205, 255), .98 * env))
        for sgn in (-1, 1):
            x1, y1 = P(-4, sgn * 6); x2, y2 = P(-16, sgn * 13); out.append(('s', x1, y1, x2, y2, 3.5, D[0], .9 * env))
        ex, ey = P(5, -4); out.append(('b', ex, ey, 3.6, (255, 255, 255), env))
        out.append(('g', hx, hy, 44, 44, D[1], .32 * env))
        # breath of light flaring at the snout once coiled
        if .35 < t < .85:
            k = smooth((t - .35) / .2) * (1 - smooth((t - .65) / .2)); x, y = P(18, 0)
            out.append(('g', x, y, 22 * k + 4, 22 * k + 4, D[0], .8 * k))
    if shell > .01:
        cy_ = fy - 62
        for k in range(3):
            r = 1 - k * .06
            out.append(('r', fx, cy_, 48 * r, 74 * r, 2.4, D[1 + (k > 1)], .5 * shell))
        out.append(('g', fx, cy_, 62, 90, D[2], .26 * shell))
        for i in range(14):
            th = t * 1.6 + i * 6.283 / 14 + frac(i, 2); tw = .5 + .5 * math.sin(t * 6 + i)
            out.append(('b', fx + math.cos(th) * 48, cy_ + math.sin(th) * 74 * .98 * (1 if i % 2 else .6), 3.2, D[0], shell * tw))
        out.append(('r', fx, gy - 2, 54, 54 * .28, 2.4, D[1], .65 * shell))
    if .5 < t < 1.1:
        k = 1 - abs(t - .75) / .25
        if k > 0: out.append(('f', D[2], .12 * k))
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


GENERATORS = {'starlightPulse': starlight, 'rally': rally, 'sweep': sweep, 'dragonSoulWard': soul, 'dragonScaleWard': scales}
