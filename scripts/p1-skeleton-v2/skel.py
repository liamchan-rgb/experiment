"""P1 skeleton v2 prototype: ground-plane IK, projected to screen, RotSprite parts."""
import math
import numpy as np
from PIL import Image

# ---------- RotSprite ----------
def scale2x(a):
    v = np.ascontiguousarray(a).view(np.uint32)[..., 0]
    p = np.pad(v, 1, mode='edge')
    B, D, E, F, H = p[:-2, 1:-1], p[1:-1, :-2], p[1:-1, 1:-1], p[1:-1, 2:], p[2:, 1:-1]
    out = np.empty((v.shape[0] * 2, v.shape[1] * 2), np.uint32)
    out[0::2, 0::2] = np.where((D == B) & (B != F) & (D != H), D, E)
    out[0::2, 1::2] = np.where((B == F) & (B != D) & (F != H), F, E)
    out[1::2, 0::2] = np.where((D == H) & (D != B) & (H != F), D, E)
    out[1::2, 1::2] = np.where((H == F) & (D != H) & (B != F), F, E)
    return out.view(np.uint8).reshape(out.shape + (4,))

class Piece:
    """One layer region (rows mask) of a pose-map image, ready to be re-posed."""
    def __init__(self, image, rows=None, pad=6):
        a = np.array(image)
        if rows is not None:
            lo, hi = rows
            m = np.zeros(a.shape[0], bool); m[max(0, lo):min(a.shape[0], hi)] = True
            a = a.copy(); a[~m] = 0
        ys, xs = np.where(a[..., 3] > 0)
        self.empty = len(xs) == 0
        if self.empty: return
        self.x0, self.y0 = xs.min() - pad, ys.min() - pad
        x1, y1 = xs.max() + pad + 1, ys.max() + pad + 1
        crop = np.zeros((y1 - self.y0, x1 - self.x0, 4), np.uint8)
        sx0, sy0 = max(0, self.x0), max(0, self.y0)
        crop[sy0 - self.y0:sy0 - self.y0 + min(a.shape[0], y1) - sy0, sx0 - self.x0:sx0 - self.x0 + min(a.shape[1], x1) - sx0] = a[sy0:min(a.shape[0], y1), sx0:min(a.shape[1], x1)]
        big = crop
        for _ in range(3): big = scale2x(big)
        self.big = big

    def draw(self, canvas, src_pivot, src_dir, dst_pivot, dst_dir, stretch=1.0):
        """Map so src_pivot->dst_pivot, src_dir->dst_dir, scaling along the axis by stretch."""
        if self.empty: return
        h, w = canvas.shape[:2]
        sd = np.array(src_dir, float); sd /= np.linalg.norm(sd); sn = np.array([-sd[1], sd[0]])
        dd = np.array(dst_dir, float); dd /= np.linalg.norm(dd); dn = np.array([-dd[1], dd[0]])
        # bounding box of destination
        bh, bw = self.big.shape[:2]
        corners = np.array([[self.x0, self.y0], [self.x0 + bw / 8, self.y0], [self.x0, self.y0 + bh / 8], [self.x0 + bw / 8, self.y0 + bh / 8]], float)
        rel = corners - np.array(src_pivot, float)
        a, b = rel @ sd * stretch, rel @ sn
        dst = np.array(dst_pivot, float) + np.outer(a, dd) + np.outer(b, dn)
        X0, Y0 = int(max(0, math.floor(dst[:, 0].min()) - 1)), int(max(0, math.floor(dst[:, 1].min()) - 1))
        X1, Y1 = int(min(w, math.ceil(dst[:, 0].max()) + 2)), int(min(h, math.ceil(dst[:, 1].max()) + 2))
        if X1 <= X0 or Y1 <= Y0: return
        gx, gy = np.meshgrid(np.arange(X0, X1) + .5, np.arange(Y0, Y1) + .5)
        vx, vy = gx - (dst_pivot[0] + .5), gy - (dst_pivot[1] + .5)
        aa, bb = (vx * dd[0] + vy * dd[1]) / stretch, vx * dn[0] + vy * dn[1]
        sx = src_pivot[0] + .5 + aa * sd[0] + bb * sn[0]
        sy = src_pivot[1] + .5 + aa * sd[1] + bb * sn[1]
        ix, iy = np.floor((sx - self.x0) * 8).astype(int), np.floor((sy - self.y0) * 8).astype(int)
        ok = (ix >= 0) & (iy >= 0) & (ix < bw) & (iy < bh)
        px = np.zeros(gx.shape + (4,), np.uint8)
        px[ok] = self.big[iy[ok], ix[ok]]
        region = canvas[Y0:Y1, X0:X1]
        m = px[..., 3] > 0
        region[m] = px[m]

# ---------- ground-plane rig ----------
GROUND = {  # forward on the ground (x right, z toward camera); screen = (x, z/2 - height)
    'down': (0, 1), 'up': (0, -1), 'right': (1, 0), 'left': (-1, 0),
    'down-right': (.7071, .7071), 'down-left': (-.7071, .7071), 'up-right': (.7071, -.7071), 'up-left': (-.7071, -.7071)}

def project(direction, s, v):
    fx, fz = GROUND[direction]
    return np.array([s * fx, .5 * s * fz - v])

def two_bone(l1, l2, s, v):
    """Hip at origin of the (forward s, up v) plane; knee bends forward. Returns knee, ankle."""
    d = math.hypot(s, v)
    reach = l1 + l2 - 1e-3
    if d > reach:
        s, v, d = s * reach / d, v * reach / d, reach
    d = max(d, abs(l1 - l2) + 1e-3)
    base = math.atan2(v, s)
    alpha = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    # two solutions: base +/- alpha; pick knee with larger forward s
    k1 = (l1 * math.cos(base + alpha), l1 * math.sin(base + alpha))
    k2 = (l1 * math.cos(base - alpha), l1 * math.sin(base - alpha))
    knee = k1 if k1[0] >= k2[0] else k2
    return np.array(knee), np.array([s, v])
