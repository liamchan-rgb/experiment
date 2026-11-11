"""P1 body model v3: a low-poly 3D chibi rendered straight to pixel art.

Every frame is rasterised at native resolution from signed-distance shapes, so
nothing is rotated or stretched as a bitmap. Oblique game camera: screen x = X,
screen y = ground - Y + Z/2 (Y up, Z toward the camera). Cel shading with
palette ramps sampled from the existing art, 1-px outlines.
"""
import math
import numpy as np

GROUND_Y = 214          # canvas row of the ground point under the character
CENTER_X = 128
VIEW = np.array([0, .5, 1.0]) / math.hypot(.5, 1.0)   # toward the camera
LIGHT = np.array([-.45, .75, .55]); LIGHT /= np.linalg.norm(LIGHT)

def hexes(*cs):
    return np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in cs], np.uint8)

# ramp[0] = outline, 1..5 = shadow .. highlight
RAMPS = {
    'jacket': hexes('#050b07', '#10201a', '#1c3321', '#2c4430', '#3d5439', '#55674c'),
    'collar': hexes('#060d08', '#10200f', '#172b1b', '#1f3922', '#2a4029', '#344a32'),
    'pants': hexes('#0c070a', '#2a2730', '#38353e', '#48444c', '#59565f', '#6b6872'),
    'boot': hexes('#120100', '#3a1d0d', '#552e17', '#6e3e22', '#87512f', '#a8714b'),
    'cuff': hexes('#120100', '#2c1509', '#3e2210', '#4b2b16', '#5a321a', '#6a3c20'),
    'sole': hexes('#0e0000', '#1f0d06', '#2c1509', '#3a1e0e', '#4b2b16', '#5a321a'),
    'skin': hexes('#3c0a02', '#c8683e', '#ec9f70', '#fbbf8f', '#fbcb9a', '#fde0c0'),
    'gold': hexes('#2a1500', '#7a5210', '#a8761a', '#c99a24', '#e6bd44', '#fbe27c'),
    'belt': hexes('#1b0a02', '#35180a', '#552a10', '#6e3414', '#884c25', '#9c6236'),
    'navy': hexes('#030716', '#0c1a3c', '#14275a', '#1d3878', '#2a4b95', '#3d63b0'),
    'tan': hexes('#2a1a0a', '#9a7a52', '#b89770', '#d2b48c', '#e4cba6', '#f2e2c4'),
    'leather': hexes('#1c0a02', '#4e2410', '#6a3418', '#874624', '#a35d34', '#bd7a4c'),
    'darkleather': hexes('#120500', '#2c1206', '#3e1c0b', '#512812', '#63331a', '#764126'),
    'cloth': hexes('#3a3028', '#a8a29a', '#c8c2b8', '#e2ddd3', '#f2eee6', '#ffffff'),
    'silver': hexes('#1a1c26', '#6e7488', '#9aa0b4', '#c4c9d8', '#e2e6f0', '#ffffff'),
    'blue': hexes('#040a24', '#0e2368', '#16348e', '#2048b0', '#3264cc', '#5288e0'),
    'gem': hexes('#12042a', '#3a1080', '#5a20b8', '#7a3ce0', '#a070f4', '#e0c8ff'),
}
METAL = {'silver', 'gold', 'gem'}
HALF = LIGHT + VIEW; HALF /= np.linalg.norm(HALF)

# ---------- signed distance primitives (vectorised over N x 3 points) ----------
def sd_capsule(p, a, b, ra, rb=None):
    rb = ra if rb is None else rb
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[:, None] * ba, axis=1) - (ra + (rb - ra) * h)

def sd_ellipsoid(p, c, r, basis=None):
    q = p - c
    if basis is not None: q = q @ basis           # world -> local (basis columns = local axes)
    k0 = np.linalg.norm(q / r, axis=1)
    k1 = np.linalg.norm(q / (r * r), axis=1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-6)

def sd_cylinder(p, a, b, r, round_=1.0):
    """Capped cylinder from a to b with slightly rounded rims."""
    ba = b - a; L = np.linalg.norm(ba); u = ba / L
    pa = p - a
    h = pa @ u
    radial = np.linalg.norm(pa - h[:, None] * u, axis=1)
    dx, dy = radial - (r - round_), np.abs(h - L / 2) - (L / 2 - round_)
    return np.minimum(np.maximum(dx, dy), 0) + np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) - round_

def sd_box(p, c, half, basis, round_=1.0):
    q = np.abs((p - c) @ basis) - (np.array(half, float) - round_)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0) - round_

def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)

class Shape:
    def __init__(self, name, material, sdf, local=None, group=None, outline=None):
        self.name, self.material, self.sdf, self.local = name, material, sdf, local
        self.group = group or name
        self.outline = outline

def render(shapes, size=256, box=(66, 56, 192, 234), steps=90, occluders=()):
    """Ray-march every pixel of `box`; returns RGBA, depth map and shape-index map."""
    x0, y0, x1, y1 = box
    ys, xs = np.mgrid[y0:y1, x0:x1]
    xs, ys = xs.ravel() + .5, ys.ravel() + .5
    z_front = 70.0
    origin = np.stack([xs - CENTER_X, GROUND_Y - ys + .5 * z_front, np.full_like(xs, z_front)], 1)
    direction = -VIEW
    t = np.zeros(len(xs)); hit = np.zeros(len(xs), bool); alive = np.ones(len(xs), bool)
    def field(p):
        return np.min(np.stack([s.sdf(p) for s in shapes]), axis=0)
    for _ in range(steps):
        idx = np.where(alive)[0]
        if not len(idx): break
        p = origin[idx] + t[idx, None] * direction
        d = field(p)
        done = d < .05
        hit[idx[done]] = True; alive[idx[done]] = False
        t[idx] += np.maximum(d, .05) * ~done
        far = t > 2 * z_front + 60
        alive &= ~far
    rgba = np.zeros((size, size, 4), np.uint8)
    depth = np.full((size, size), -1e9)
    sid = np.full((size, size), -1, int)
    idx = np.where(hit)[0]
    if not len(idx):
        return rgba, depth, sid
    p = origin[idx] + t[idx, None] * direction
    dists = np.stack([s.sdf(p) for s in shapes])
    which = np.argmin(dists, axis=0)
    e = .25
    n = np.stack([field(p + [e, 0, 0]) - field(p - [e, 0, 0]),
                  field(p + [0, e, 0]) - field(p - [0, e, 0]),
                  field(p + [0, 0, e]) - field(p - [0, 0, e])], 1)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
    light = n @ LIGHT
    py0, px0 = ys[idx].astype(int), xs[idx].astype(int)
    bayer = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - .5)[py0 % 4, px0 % 4]
    h = (px0 * 73856093 ^ py0 * 19349663) & 1023
    grain = (h / 1023.0 - .5)
    dl = light + bayer * .17 + grain * .10               # ordered dither + fine grain, like the hand-drawn art
    tone = np.select([dl < -.05, dl < .3, dl < .62, dl < .9], [1, 2, 3, 4], 5)
    spec = (n @ HALF) > .93
    if occluders:
        # contact shadow: surfaces tucked against another part (under collars, belts, arms) go one tone darker
        near = np.min(np.stack([o.sdf(p) for o in occluders]), axis=0) < 2.2
        tone = np.where(near, np.maximum(1, tone - 1), tone)
    py, px = ys[idx].astype(int), xs[idx].astype(int)
    colours = np.zeros((len(idx), 3), np.uint8)
    for k, s in enumerate(shapes):
        m = which == k
        if not m.any(): continue
        material = np.full(m.sum(), s.material, object)
        if s.local is not None:
            material = s.local(p[m], material)
        for name in set(material):
            mm = material == name
            t = tone[m][mm]
            if name in METAL:
                t = np.where(spec[m][mm], 5, np.minimum(t, 4))
            colours[np.where(m)[0][mm]] = RAMPS[name][t]
    rgba[py, px, :3] = colours; rgba[py, px, 3] = 255
    depth[py, px] = (p @ VIEW)
    sid[py, px] = which
    # outlines: silhouette, and depth steps between different groups
    groups = np.array([hash(s.group) % 100003 for s in shapes])
    gmap = np.where(sid >= 0, groups[np.maximum(sid, 0)], -1)
    out = rgba.copy()
    sil_any = np.zeros(sid.shape, bool)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        sil_any |= (sid >= 0) & (np.roll(gmap, (dy, dx), (0, 1)) == -1)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb_d = np.roll(depth, (dy, dx), (0, 1)); nb_g = np.roll(gmap, (dy, dx), (0, 1))
        sil = (sid >= 0) & (nb_g == -1)
        step = (sid >= 0) & (nb_g != -1) & (nb_g != gmap) & (nb_d > depth + 2.5)
        edge = sil | step
        for k, s in enumerate(shapes):
            m = edge & (sid == k)
            if m.any():
                ramp = RAMPS[s.outline or s.material]
                out[m & sil_any, :3] = ramp[0]
                out[m & ~sil_any, :3] = ramp[1]
    return out, depth, sid
