"""Ray-marches the figure of rig.py from the oblique game camera into a pixel-art sprite."""
import colorsys
import numpy as np
from rig import *

PITCH = np.radians(24.0)            # the camera looks down by this much
PX = 150.0                          # pixels per unit
SIZE = (144, 208)                   # sprite canvas (w, h)
FOOT = (72, 190)                    # where the ground point under the hips lands
CAM_D = V(0, np.cos(PITCH), -np.sin(PITCH)); CAM_R = V(1, 0, 0); CAM_U = V(0, np.sin(PITCH), np.cos(PITCH))
LIGHT = norm(V(-0.55, -0.5, 0.8))   # towards the light, world space (upper left, a little in front)
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], F32) / 16 - 0.47) * 0.09

def ramp(rgb, metal=False):
    """Four tones, dark to light; shadows drift towards violet and lose value, lights drift towards yellow."""
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb)); out = []
    for dv, ds, dh in ((-0.42, 0.12, -0.07), (-0.2, 0.06, -0.035), (0, 0, 0), (0.2 if not metal else 0.34, -0.2, 0.03)):
        hh = (h + (dh if 0.1 < h < 0.75 else -dh)) % 1.0
        out.append(tuple(int(255 * c) for c in colorsys.hsv_to_rgb(hh, min(1, max(0, s + ds)), min(1, max(0, v + dv)))))
    return out

BASE = dict(skin=(246, 196, 160), leather=(120, 78, 50), metal=(176, 184, 198), wood=(132, 92, 58), gem=(90, 220, 230), dark=(40, 36, 48))

def world_dirs(yaw):
    """Camera and light expressed in model space for a figure turned by `yaw` (0 faces away from the camera, pi faces it)."""
    R = rz(yaw)          # rows are the model's axes in world space, so world -> model is v @ R.T
    return CAM_D @ R.T, CAM_R @ R.T, CAM_U @ R.T, LIGHT @ R.T

def project(p, yaw):
    """Model point -> sprite pixel (x, y) and depth along the view."""
    d, r, u, _ = world_dirs(yaw)
    return FOOT[0] + float(p @ r) * PX, FOOT[1] - float(p @ u) * PX, float(p @ d)

def render(parts, palette, yaw, head=None):
    """RGBA sprite (uint8, h x w x 4) plus the depth buffer."""
    w, h = SIZE
    d, r, u, light = world_dirs(yaw)
    xs, ys = np.meshgrid(np.arange(w, dtype=F32) + 0.5, np.arange(h, dtype=F32) + 0.5)
    sx, sy = (xs.ravel() - FOOT[0]) / PX, (FOOT[1] - ys.ravel()) / PX
    O = sx[:, None] * r + sy[:, None] * u - d * 2.0
    t = np.zeros(len(O), F32); alive = np.ones(len(O), bool); hit = np.zeros(len(O), bool)
    for _ in range(64):
        idx = np.flatnonzero(alive)
        if not len(idx): break
        dist, _m = field(O[idx] + t[idx, None] * d, parts)
        t[idx] += dist * 0.85
        done = dist < 0.0018
        hit[idx[done]] = True; alive[idx[done]] = False; alive[idx[t[idx] > 4.0]] = False
    H = np.flatnonzero(hit); P = O[H] + t[H, None] * d
    _, mat = field(P, parts)
    e = 0.004; n = np.zeros_like(P)
    for a in range(3):
        o = np.zeros(3, F32); o[a] = e
        n[:, a] = field(P + o, parts)[0] - field(P - o, parts)[0]
    n /= np.maximum(1e-6, np.linalg.norm(n, axis=1))[:, None]
    ao = np.clip(field(P + n * 0.06, parts)[0] / 0.06, 0, 1)
    diff = np.clip(n @ light, 0, 1)
    val = (0.2 + 0.8 * diff) * (0.55 + 0.45 * ao)
    val += 0.22 * np.clip(1 + n @ d, 0, 1) ** 3 * np.clip(n @ light + 0.3, 0, 1)          # rim on the lit side
    val += 0.13 * (mat == MATS.index('skin'))                                           # skin stays bright under the fringe
    px, py = (H % w), (H // w)
    val += BAYER[py % 4, px % 4]
    tone = np.digitize(val, [0.36, 0.58, 0.84])
    ramps = {m: ramp(palette.get(m, BASE.get(m, (128, 128, 128))), m in ('metal', 'gem')) for m in MATS}
    table = np.array([ramps[m] for m in MATS], np.uint8)         # material, tone, rgb
    rgb = table[mat, tone].astype(np.int16)
    metal = np.isin(mat, [MATS.index('metal'), MATS.index('gem')])
    spec = metal & ((n @ norm(light - d)) > 0.93)
    rgb[spec] = (250, 250, 240)
    # the face: painted on the head by direction from the head's centre
    if head is not None:
        hc, Rh = head; q = (P - hc) @ Rh.T; rr = np.linalg.norm(q, axis=1)
        skin = (mat == MATS.index('skin')) & (rr < HEAD_R * 1.1) & (q[:, 1] > 0)
        az, el = np.arctan2(q[:, 0], q[:, 1]), np.arcsin(np.clip(q[:, 2] / np.maximum(rr, 1e-6), -1, 1))
        for sgn in (-1, 1):
            da, de = (az - sgn * 0.4) / 0.2, (el + 0.1) / 0.3
            eye = skin & (da * da + de * de < 1)
            rgb[eye] = (58, 96, 150)
            rgb[eye & (de < -0.25)] = (96, 150, 200)
            rgb[eye & (de > 0.42)] = (44, 32, 44)
            rgb[eye & (de > -0.05) & (de < 0.42) & (da * sgn < -0.15)] = (250, 250, 255)
            blush = skin & (((az - sgn * 0.7) / 0.17) ** 2 + ((el + 0.5) / 0.1) ** 2 < 1)
            rgb[blush] = (rgb[blush] * 0.6 + np.array([240, 130, 120]) * 0.4).astype(np.int16)
        mouth = skin & (np.abs(az) < 0.1) & (np.abs(el + 0.66) < 0.045)
        rgb[mouth] = (170, 92, 84)
    img = np.zeros((h, w, 4), np.uint8); depth = np.full((h, w), 9.0, F32); matmap = np.full((h, w), -1, np.int16)
    img[py, px, :3] = np.clip(rgb, 0, 255); img[py, px, 3] = 255; depth[py, px] = t[H]; matmap[py, px] = mat
    # inner lines: where the surface behind is clearly further away, the far side of the step is darkened
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        near = np.roll(depth, (dy, dx), (0, 1))
        step = (img[..., 3] > 0) & (depth - near > 0.03) & (near < 8)
        img[step, :3] = (img[step, :3] * 0.62).astype(np.uint8)
    # outline: one pixel around the silhouette, a dark version of the colour it borders
    a = img[..., 3] > 0; out = img.copy()
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        na = np.roll(a, (dy, dx), (0, 1)); src = np.roll(img, (dy, dx), (0, 1))
        edge = ~a & na & (out[..., 3] == 0)
        out[edge, :3] = (src[edge, :3] * 0.3 + np.array([14, 10, 22])).astype(np.uint8); out[edge, 3] = 255
    return out, depth

def frame(loadout, yaw, t=None, breath=0.0):
    L = LOADOUTS[loadout]; J, B = pose(t, breath)
    parts = body(J, B, L['look']) + gear(B, L['items'])
    img, depth = render(parts, L['palette'], yaw, B['head'])
    attach = {k: [round(v, 2) for v in project(B[k][0], yaw)] for k in ('hand_l', 'hand_r', 'head', 'back', 'hips')}
    return img, attach

if __name__ == '__main__':
    import sys, time
    from PIL import Image
    t0 = time.time(); tiles = []
    for k in range(8):
        img, _ = frame(sys.argv[1] if len(sys.argv) > 1 else 'knight', np.pi + k * np.pi / 4, t=0.1 * k)
        tiles.append(Image.fromarray(img))
    sheet = Image.new('RGBA', (SIZE[0] * 8, SIZE[1]), (70, 96, 70, 255))
    for i, im in enumerate(tiles): sheet.alpha_composite(im, (i * SIZE[0], 0))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST); sheet.save(sys.argv[2] if len(sys.argv) > 2 else 'test.png')
    print('8 frames', round(time.time() - t0, 1), 's')
