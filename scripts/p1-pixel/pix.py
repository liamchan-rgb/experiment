"""Rule-drawn pixel chibi (like the demo pack's pixel_walker, at higher resolution).
Every pixel is placed by drawing rules on the target grid; no 3D rendering.
Pose comes from the approved jog skeleton (scripts/p1-model-v3/body.py + clips.py)."""
import math, sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'p1-model-v3'))
import numpy as np
from PIL import Image
import body, clips

def hx(c): return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)] + [255], np.uint8)
# ramps: [outline, shadow, base, light, highlight]
PAL = {
 'jacket': [hx('#0b150e'), hx('#1c3321'), hx('#2f4631'), hx('#46603f'), hx('#62795a')],
 'gold':   [hx('#3a2204'), hx('#8a5c12'), hx('#c99a24'), hx('#f0c850'), hx('#fff0a0')],
 'belt':   [hx('#1e0c04'), hx('#4a240e'), hx('#6e3a1a'), hx('#8c5430'), hx('#a46a40')],
 'pants':  [hx('#100c12'), hx('#2c2932'), hx('#403c46'), hx('#56535c'), hx('#6c6972')],
 'boot':   [hx('#1a0802'), hx('#4a2610'), hx('#6e3e22'), hx('#946038'), hx('#b07a50')],
 'skin':   [hx('#5a1e0a'), hx('#e0956a'), hx('#fbc896'), hx('#fde0bc'), hx('#fff0dc')],
 'hair':   [hx('#3a1206'), hx('#7a3214'), hx('#a8501e'), hx('#d07632'), hx('#f0a058')],
 'eye':    [hx('#0a1440'), hx('#1c3c9a'), hx('#2f6ad8'), hx('#6aa8f4'), hx('#ffffff')],
 'white':  [hx('#5a5a6a'), hx('#c8ccd8'), hx('#ffffff'), hx('#ffffff'), hx('#ffffff')],
 'mouth':  [hx('#5a1e0a'), hx('#a84a32'), hx('#c8604a'), hx('#c8604a'), hx('#c8604a')],
}

class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = np.zeros((h, w, 4), np.uint8)
        self.yy, self.xx = np.mgrid[0:h, 0:w] + .5

    # ---- masks ----
    def capsule(self, a, b, r):
        a, b = np.array(a, float), np.array(b, float)
        ba = b - a; L = max(ba @ ba, 1e-9)
        px, py = self.xx - a[0], self.yy - a[1]
        t = np.clip((px * ba[0] + py * ba[1]) / L, 0, 1)
        return (px - t * ba[0]) ** 2 + (py - t * ba[1]) ** 2 <= r * r

    def ellipse(self, c, rx, ry):
        return ((self.xx - c[0]) / rx) ** 2 + ((self.yy - c[1]) / ry) ** 2 <= 1

    def poly(self, pts):
        pts = np.array(pts, float); inside = np.zeros((self.h, self.w), bool)
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
            cond = ((y1 > self.yy) != (y2 > self.yy))
            xint = (x2 - x1) * (self.yy - y1) / np.where(y2 - y1 == 0, 1e-9, y2 - y1) + x1
            inside ^= cond & (self.xx < xint)
        return inside

    # ---- painting ----
    def paint(self, mask, ramp, light=(-1, -1), band=1, outline=True, shade=True):
        """Pixel-art cel shading: shadow band on the side away from the light, a lit rim toward it."""
        if not mask.any(): return
        col = PAL[ramp]
        tone = np.full(mask.shape, 2)
        if shade:
            lx, ly = light
            def shifted(m, dx, dy):
                return np.roll(np.roll(m, dy, 0), dx, 1)
            away = mask & ~shifted(mask, lx * band, ly * band)    # pixel whose neighbour away from light is outside -> shadow side
            toward = mask & ~shifted(mask, -lx, -ly)             # lit rim
            tone[away] = 1
            tone[toward & ~away] = 3
        border = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)) if outline else np.zeros_like(mask)
        tone[border] = 0
        for t in range(5):
            m = mask & (tone == t)
            self.img[m] = col[t]

    def put(self, x, y, ramp, t=2):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h: self.img[y, x] = PAL[ramp][t]

    def image(self):
        return Image.fromarray(self.img)


def screen(J, k, facing, s, origin):
    fx, fz = body.FACING[facing]
    W = np.array([[fz, 0, fx], [0, 1, 0], [-fx, 0, fz]])
    p = W @ J[k] if not isinstance(k, np.ndarray) else W @ k
    return np.array([origin[0] + p[0] * s, origin[1] + (-p[1] + .5 * p[2]) * s])


def rt_side(side, sh, P):
    return np.zeros(2)


def draw(pose, facing='down-right', H=48, W=32):
    """Character ~ H px tall. Proportions follow the approved model (head ~ 1/3 of height)."""
    c = Canvas(W, H)
    s = (H - 2) / 140.0          # model is ~140 canvas px from sole to hair top
    origin = (W / 2, H - 2)
    J = body.skeleton(pose)
    P = lambda k: screen(J, k, facing, s, origin)
    S = lambda v: v * s           # model px -> sprite px
    lw = lambda r: max(1.0, r * s)
    band = 1 if H < 60 else 2
    # far side first (left side of the character is far in a down-right view)
    for side in ('L', 'R'):
        far = side == 'L'
        hip, knee, ank = P('hip' + side), P('knee' + side), P('ankle' + side)
        legm = c.capsule(hip, knee, lw(8.0)) | c.capsule(knee, ank, lw(7.0))
        bootm = c.capsule(ank + [0, -S(2)], ank + [S(5.5), S(5.5)], lw(6.0))
        bootm |= c.capsule(ank + [-S(2), S(4)], ank + [S(7), S(6.5)], lw(4.6))
        if far:
            c.paint(legm, 'pants', band=band); c.paint(bootm, 'boot', band=band)
        else:
            near_leg = (legm, bootm)
        sh, el, wr = P('shoulder' + side), P('elbow' + side), P('wrist' + side)
        armm = c.capsule(sh + rt_side(side, sh, P) * 0, el, lw(7.0)) | c.capsule(el, wr, lw(6.4))
        handc = wr + (wr - el) / max(1e-6, np.linalg.norm(wr - el)) * S(3.5)
        handm = c.ellipse(handc, max(lw(5.0), 1.7), max(lw(5.0), 1.7))
        if far:
            c.paint(armm, 'jacket', band=band); c.paint(handm, 'skin', band=band)
        else:
            near_arm = (armm, handm, el, wr)
    # torso (jacket) as a polygon: shoulders -> waist -> flared hem, leaning with the chest
    pel = P('pelvis'); neck = P('neck')
    up = (neck - pel) / np.linalg.norm(neck - pel); rt = np.array([-up[1], up[0]])
    hw_sh, hw_wa, hw_hem = S(20), S(17.5), S(19.5)
    sh_c = pel + up * S(34); wa_c = pel + up * S(12); hem_c = pel + up * S(-6)
    torso = c.poly([sh_c - rt * hw_sh * .85 + up * S(2), sh_c + rt * hw_sh * .85 + up * S(2),
                    sh_c + rt * hw_sh, wa_c + rt * hw_wa, hem_c + rt * hw_hem, hem_c - rt * hw_hem,
                    wa_c - rt * hw_wa, sh_c - rt * hw_sh])
    torso |= c.ellipse(sh_c + up * S(1), hw_sh, S(6))
    # near leg goes behind the jacket hem but in front of the far leg
    c.paint(near_leg[0], 'pants', band=band); c.paint(near_leg[1], 'boot', band=band)
    c.paint(torso, 'jacket', band=band)
    # jacket details: belt, buckle, placket, buttons, hem trim (front is offset toward the facing)
    fx, fz = body.FACING[facing]
    front = rt * (-fx * .35)   # down-right: front shifts toward screen right a little
    belt = torso & c.capsule(wa_c - rt * hw_wa * 1.2, wa_c + rt * hw_wa * 1.2, max(.8, S(2.2)))
    c.paint(belt, 'belt', band=band, outline=False)
    bk = wa_c + front * S(1) + rt * S(5)
    n = 2 if H < 60 else 3
    for dx in range(n):
        for dy in range(n):
            c.put(bk[0] - n // 2 + dx, bk[1] - n // 2 + dy, 'gold', 3 if (dx + dy) == 0 else 2)
    hem = torso & ~c.poly([hem_c - rt * 40 + up * S(2.2), hem_c + rt * 40 + up * S(2.2), hem_c + rt * 40 - up * 20, hem_c - rt * 40 - up * 20]) ^ torso
    c.paint(hem & torso, 'gold', band=band, outline=False, shade=False)
    for k, yy in enumerate((30, 23, 16)):
        b = pel + up * S(yy) + rt * S(5)
        c.put(b[0], b[1], 'gold', 3)
    # collar
    col = c.ellipse(neck + up * S(-3), S(6.5), S(3.4))
    c.paint(col, 'jacket', band=band)
    # near arm in front of the torso
    armm, handm, el, wr = near_arm
    c.paint(armm, 'jacket', band=band)
    if H >= 60:   # at 32x48 a cuff band is wider than the forearm reads; leave it out
        cuff = armm & c.capsule(wr - (wr - el) * .26, wr - (wr - el) * .12, lw(6.4))
        c.paint(cuff, 'gold', band=band, outline=False, shade=False)
    c.paint(handm, 'skin', band=band)
    draw_head(c, neck, up, s, facing)
    return c


def draw_head(c, neck, up, s, facing, k=1.28):
    S = lambda v: v * s * k
    big = s > .45
    band = 2 if big else 1
    hc = neck + up * S(19) + np.array([S(1), 0])         # head centre; chin overlaps the collar
    P = lambda x, y: hc + [S(x), S(y)]
    face = c.ellipse(P(2, 3), S(19), S(18)) | c.ellipse(P(5, 11), S(12), S(9))
    ear = c.ellipse(P(-12, 6), S(3.6), S(4.6))
    c.paint(face | ear, 'skin', band=band)
    # hair: rounded back mass, crown, bangs to the brows, side lock over the ear's front
    hair = c.ellipse(P(-3, -5), S(23), S(19)) & ~c.poly([P(-5, 2), P(3, -2), P(30, -1), P(30, 40), P(-5, 40)])
    for x, y, w, l in [(-4, -3, 7, 11), (2, -4, 7, 12), (8, -4, 7, 11), (14, -3, 6, 9), (19, -1, 5, 7)]:
        hair |= c.poly([P(x - w / 2, y - 6), P(x + w / 2, y - 6), P(x + w * .25, y + l - 4)])
    hair |= c.poly([P(-16, -3), P(-6, -1), P(-8, 15), P(-12, 17), P(-17, 9)])               # side lock
    hair |= c.poly([P(-25, -8), P(-17, -6), P(-22, 8)]) | c.poly([P(-22, -14), P(-12, -18), P(-28, -16)])  # nape locks
    hair |= c.poly([P(-8, -22), P(4, -24), P(-4, -29)]) | c.poly([P(6, -22), P(16, -18), P(12, -27)])     # two crown tufts
    c.paint(hair, 'hair', band=band)
    for x, y, n in ([(-12, -14, 3), (-2, -18, 3), (8, -16, 2)] if big else [(-8, -15, 2), (2, -17, 1)]):
        p = P(x, y)
        for i in range(n): c.put(p[0] + i, p[1] + i * .5, 'hair', 4)       # short highlight strokes
    # eyes on the visible face: near eye (screen-left) wider, far eye narrower
    hgt = 5 if big else 3
    for ex, w in ((-2, 4 if big else 2), (10, 3 if big else 2)):
        e = P(ex, 6)
        x0, y0 = int(round(e[0])), int(round(e[1]))
        for dx in range(w):
            c.put(x0 + dx, y0 - 1, 'eye', 0)
            for dy in range(hgt - 1):
                c.put(x0 + dx, y0 + dy, 'eye', 1 if dy == 0 else (3 if dy == hgt - 2 else 2))
        c.put(x0 + (1 if big else 0), y0, 'white', 2)
        if big: c.put(x0 + w - 1, y0 + 1, 'white', 2)
    m = P(6, 15)
    c.put(m[0], m[1], 'mouth', 1)
    if big: c.put(m[0] + 1, m[1], 'mouth', 1)
    if big:
        b = P(13, 12); c.put(b[0], b[1], 'mouth', 2)
