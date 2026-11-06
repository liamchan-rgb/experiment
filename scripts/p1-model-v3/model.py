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
    'jacket': hexes('#060d08', '#15271b', '#213a26', '#2f4631', '#3e5439', '#52634a'),
    'collar': hexes('#060d08', '#10200f', '#172b1b', '#1f3922', '#2a4029', '#344a32'),
    'pants': hexes('#0e080b', '#26232b', '#322f38', '#403c44', '#4c4951', '#5a5760'),
    'boot': hexes('#120100', '#3a1d0d', '#552e17', '#6e3e22', '#87512f', '#a8714b'),
    'cuff': hexes('#120100', '#2c1509', '#3e2210', '#4b2b16', '#5a321a', '#6a3c20'),
    'sole': hexes('#0e0000', '#1f0d06', '#2c1509', '#3a1e0e', '#4b2b16', '#5a321a'),
    'skin': hexes('#3c0a02', '#c8683e', '#ec9f70', '#fbbf8f', '#fbcb9a', '#fde0c0'),
    'gold': hexes('#2a1500', '#7a5210', '#b0801a', '#d8a82c', '#f2d062', '#fff0aa'),
    'belt': hexes('#1b0a02', '#35180a', '#552a10', '#6e3414', '#884c25', '#9c6236'),
}

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

def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)

class Shape:
    def __init__(self, name, material, sdf, local=None, group=None):
        self.name, self.material, self.sdf, self.local = name, material, sdf, local
        self.group = group or name

def render(shapes, size=256, box=(70, 60, 190, 232), steps=90):
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
    tone = np.select([light < -.05, light < .3, light < .62, light < .9], [1, 2, 3, 4], 5)
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
            colours[np.where(m)[0][mm]] = RAMPS[name][tone[m][mm]]
    rgba[py, px, :3] = colours; rgba[py, px, 3] = 255
    depth[py, px] = (p @ VIEW)
    sid[py, px] = which
    # outlines: silhouette, and depth steps between different groups
    groups = np.array([hash(s.group) % 100003 for s in shapes])
    gmap = np.where(sid >= 0, groups[np.maximum(sid, 0)], -1)
    out = rgba.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb_d = np.roll(depth, (dy, dx), (0, 1)); nb_g = np.roll(gmap, (dy, dx), (0, 1))
        sil = (sid >= 0) & (nb_g == -1)
        step = (sid >= 0) & (nb_g != -1) & (nb_g != gmap) & (nb_d > depth + 2.5)
        edge = sil | step
        for k, s in enumerate(shapes):
            m = edge & (sid == k)
            if m.any():
                out[m, :3] = RAMPS[s.material][0]
    return out, depth, sid
