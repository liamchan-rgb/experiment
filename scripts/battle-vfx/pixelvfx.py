"""Procedural pixel-art VFX toolkit.

Every frame is drawn on a small grid with hard masks and a few palette colours (no blur, no per-frame noise):
all motion is a closed-form function of time, particles have fixed ids, so consecutive frames stay coherent.
Sheets are written at the original cell size by nearest-neighbour scaling, so the game's specs (frame count,
fps, anchors) stay untouched.
"""
import math
import numpy as np
from PIL import Image

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + .5) / 16.0


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def smooth(x):
    t = min(1.0, max(0.0, x)); return t * t * (3 - 2 * t)


def clamp01(x): return min(1.0, max(0.0, x))
def lerp(a, b, t): return a + (b - a) * t
def ease_out(x): t = clamp01(x); return 1 - (1 - t) ** 3
def ease_in(x): t = clamp01(x); return t * t


def frac(i, salt):
    """Deterministic per-id number in [0, 1): the only 'randomness' allowed in a sheet."""
    return ((i * 73 + salt * 37 + (i * i) * 11) % 101) / 100.0


class Grid:
    """One frame on a w x h grid. Pixel centres are at +0.5; all masks are hard (no antialiasing)."""
    SUPER = 1          # >1 renders the same design on a k-times finer pixel grid (coordinates stay in design units)

    def __init__(self, w, h):
        k = self.k = Grid.SUPER
        self.w, self.h = w * k, h * k
        self.rgba = np.zeros((self.h, self.w, 4), np.uint8)
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        self.x, self.y = (xx + .5) / k, (yy + .5) / k
        self.bayer = np.tile(BAYER4, (self.h // 4 + 1, self.w // 4 + 1))[:self.h, :self.w]

    # ---- masks ----
    def disc(self, cx, cy, r): return (self.x - cx) ** 2 + (self.y - cy) ** 2 <= r * r
    def ellipse(self, cx, cy, rx, ry): return ((self.x - cx) / rx) ** 2 + ((self.y - cy) / ry) ** 2 <= 1
    def ring(self, cx, cy, r0, r1, ry_scale=1.0):
        d2 = (self.x - cx) ** 2 + ((self.y - cy) / ry_scale) ** 2
        return (d2 >= r0 * r0) & (d2 <= r1 * r1)

    def angle(self, cx, cy, ry_scale=1.0):
        return np.arctan2((self.y - cy) / ry_scale, self.x - cx)

    def arc(self, cx, cy, r0, r1, a0, a1, ry_scale=1.0):
        """Annulus restricted to the angles a0 -> a1 (radians, a1 > a0), measured from +x towards +y."""
        ang = (self.angle(cx, cy, ry_scale) - a0) % (2 * math.pi)
        return self.ring(cx, cy, r0, r1, ry_scale) & (ang <= (a1 - a0))

    def segment(self, a, b, w0, w1=None):
        """Capsule from a to b with width tapering w0 -> w1 (full widths)."""
        w1 = w0 if w1 is None else w1
        ax, ay = a; bx, by = b
        dx, dy = bx - ax, by - ay
        L2 = max(dx * dx + dy * dy, 1e-9)
        t = np.clip(((self.x - ax) * dx + (self.y - ay) * dy) / L2, 0, 1)
        px, py = ax + t * dx, ay + t * dy
        d = np.hypot(self.x - px, self.y - py)
        return d <= (w0 + (w1 - w0) * t) / 2

    def poly(self, pts):
        inside = np.zeros((self.h, self.w), bool)
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
            cond = (y1 > self.y) != (y2 > self.y)
            xint = (x2 - x1) * (self.y - y1) / np.where(y2 - y1 == 0, 1e-9, y2 - y1) + x1
            inside ^= cond & (self.x < xint)
        return inside

    def diamond(self, cx, cy, rx, ry): return (np.abs(self.x - cx) / max(rx, 1e-6) + np.abs(self.y - cy) / max(ry, 1e-6)) <= 1

    def star(self, cx, cy, long, short, rot=0.0, points=4):
        """Pointed star with `points` long spikes (hard edged)."""
        ang = np.arctan2(self.y - cy, self.x - cx) - rot
        r = np.hypot(self.x - cx, self.y - cy)
        k = (np.cos(points * ang) + 1) / 2                      # 1 along the spikes, 0 between them
        reach = short + (long - short) * k ** 3
        return r <= reach

    def dither(self, level):
        """Ordered-dither mask: fraction `level` (0..1) of pixels on, in a screen-fixed pattern."""
        return self.bayer < level

    # ---- painting ----
    def fill(self, mask, color, alpha=255):
        self.rgba[mask] = (*color, alpha)

    def fill_if_empty(self, mask, color):
        free = mask & (self.rgba[..., 3] == 0)
        self.rgba[free] = (*color, 255)

    def outline(self, color, mask=None):
        """1-px outline outside every painted pixel (only on empty pixels)."""
        painted = self.rgba[..., 3] > 0
        p = np.pad(painted, 1)
        near = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        edge = near & ~painted
        if mask is not None: edge &= mask
        self.rgba[edge] = (*color, 255)

    def image(self): return Image.fromarray(self.rgba)


def pack_sheet(frames, grid_scale, cell, columns):
    """frames: list of Grid. Scale each by `grid_scale` (nearest) and centre-crop/pad to cell=(w, h)."""
    cw, ch = cell
    rows = math.ceil(len(frames) / columns)
    sheet = Image.new('RGBA', (cw * columns, ch * rows))
    for i, g in enumerate(frames):
        f = grid_scale // g.k
        im = g.image().resize((g.w * f, g.h * f), Image.NEAREST) if f > 1 else g.image()
        ox, oy = (cw - im.width) // 2, (ch - im.height) // 2
        tile = Image.new('RGBA', (cw, ch)); tile.alpha_composite(im.crop((max(0, -ox), max(0, -oy), max(0, -ox) + min(im.width, cw), max(0, -oy) + min(im.height, ch))), (max(0, ox), max(0, oy)))
        sheet.alpha_composite(tile, ((i % columns) * cw, (i // columns) * ch))
    return sheet
