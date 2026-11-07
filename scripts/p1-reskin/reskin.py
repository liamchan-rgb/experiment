"""Re-skin the approved jog with the ORIGINAL hand-drawn P1 pixels (prototype, one facing).

- torso, head, face, hair, back weapon: original pixels, moved only by the body bob;
- boots and hands: original pixels, translated with the ankle / wrist (never rotated);
- thighs, shins, upper arms, forearms: re-posed in 3D on the original joints; every output
  pixel finds its body point, maps it back to the idle pose and takes the colour the
  original art has there (sleeve folds, trims and shading are the hand-drawn ones).
"""
import json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'p1-model-v3'))
import numpy as np
from PIL import Image
import body, clips

GROUND_Y, CX = 214, 128
SIDE = {'R': 'right', 'L': 'left'}


def load_original(root, facing):
    """Per-slot idle layers (pose-map canvas) of base+lower+forester+weapon+head from a checkout of the original parts."""
    root = Path(root)
    motion = json.loads((root / 'Art/Integration/P1-modular-eight-way-v1/motion.json').read_text())
    frame = next(f for f in motion['frames'] if f['direction'] == facing and f['clip'] == 'idle')
    layers = {}
    for asset in ['base', 'lower', 'forester', 'weapon', 'face-blue', 'hair-chestnut']:
        folder = root / 'Art/Parts/P1-v1/eight-way-v1' / asset
        data = json.loads((folder / 'asset.json').read_text())
        b = next(x for x in data['bindings'] if x['direction'] == facing and x['clip'] == 'idle')
        for slot, rel in b['layers'].items():
            im = np.array(Image.open(folder / rel).convert('RGBA'))
            if data['mode'] == 'head-local':
                a, _, _, d, tx, ty = frame['headToCanvas']
                canvas = np.zeros((256, 256, 4), np.uint8)
                canvas[int(ty):int(ty) + im.shape[0], int(tx):int(tx) + im.shape[1]] = im
                im = canvas
            layers[slot] = im
    return frame, layers


def world_axes(facing):
    fx, fz = body.FACING[facing]
    F = np.array([fx, 0, fz], float)
    L = np.array([fz, 0, -fx], float)          # character's left
    return F, L


def lift(screen, z):
    """Screen pixel -> 3D point at depth z (X right, Y up, Z toward the camera)."""
    sx, sy = screen
    return np.array([sx - CX, GROUND_Y + z / 2 - sy, z], float)


def project(p):
    return np.array([CX + p[0], GROUND_Y - p[1] + p[2] / 2])


def rodrigues(v, k, a):
    return v * math.cos(a) + np.cross(k, v) * math.sin(a) + k * (k @ v) * (1 - math.cos(a))


def min_rotation(u, v):
    """Rotation matrix taking unit u onto unit v."""
    c = float(np.clip(u @ v, -1, 1)); ax = np.cross(u, v); s = np.linalg.norm(ax)
    if s < 1e-9: return np.eye(3)
    k = ax / s; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + K * s + K @ K * (1 - c)


def two_bone(hip, target, l1, l2, fwd):
    d = target - hip; dist = np.linalg.norm(d)
    dist_c = np.clip(dist, abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    u = d / dist; target = hip + u * dist_c
    a = math.acos(np.clip((l1 * l1 + dist_c * dist_c - l2 * l2) / (2 * l1 * dist_c), -1, 1))
    n = fwd - u * (fwd @ u); n /= max(np.linalg.norm(n), 1e-9)
    knee = hip + l1 * (u * math.cos(a) + n * math.sin(a))
    return knee, target


class Rig:
    """Original idle joints lifted to 3D with the model's depths; segment lengths from the original."""
    def __init__(self, facing, frame):
        self.facing = facing
        self.F, self.L = world_axes(facing)
        fx, fz = body.FACING[facing]
        W = np.array([[fz, 0, fx], [0, 1, 0], [-fx, 0, fz]])
        Jm = body.skeleton(clips.pose('idle', 0))
        z = {k: (W @ v)[2] for k, v in Jm.items() if isinstance(v, np.ndarray) and v.shape == (3,)}
        j = frame['joints']
        self.idle = {}
        for s in 'RL':
            for name in ['hip', 'knee', 'ankle', 'shoulder', 'elbow', 'wrist']:
                self.idle[name + s] = lift(j[name + ('Right' if s == 'R' else 'Left')], z[name + s])
        self.idle_pose = clips.pose('idle', 0)

    def pose(self, pose):
        P = {}
        bob = pose['bob']
        down = np.array([0, -bob, 0.0])
        for s in 'RL':
            I = self.idle
            hip = I['hip' + s] + down
            l1 = np.linalg.norm(I['knee' + s] - I['hip' + s]); l2 = np.linalg.norm(I['ankle' + s] - I['knee' + s])
            u, lift_, _ = pose['legs'][s]; u0 = self.idle_pose['legs'][s][0]
            target = I['ankle' + s] + self.F * (u - u0) + np.array([0, lift_, 0])
            knee, ankle = two_bone(hip, target, l1, l2, self.F)
            # keep the original's slight knee offset (identity in idle)
            k0, _ = two_bone(I['hip' + s], I['ankle' + s], l1, l2, self.F)
            knee = knee + (I['knee' + s] - k0)
            P['hip' + s], P['knee' + s], P['ankle' + s] = hip, knee, ankle
            sw, bd = pose['arms'][s]; sw0, bd0 = self.idle_pose['arms'][s]
            sh = I['shoulder' + s] + down
            up_v = I['elbow' + s] - I['shoulder' + s]; fo_v = I['wrist' + s] - I['elbow' + s]
            elbow = sh + rodrigues(up_v, self.L, -(sw - sw0))
            wrist = elbow + rodrigues(fo_v, self.L, -((sw - sw0) + (bd - bd0)))
            P['shoulder' + s], P['elbow' + s], P['wrist' + s] = sh, elbow, wrist
        P['bob'] = bob
        return P


def extend(img, steps=4):
    """Drop the source outline, then grow interior colours outward so edge samples never hit outline/holes."""
    a = img.copy(); m = a[..., 3] > 0
    inner = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    a[~inner] = 0; m = inner
    for _ in range(steps):
        grow = ~m
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = np.roll(np.roll(a, dy, 0), dx, 1); nm = np.roll(np.roll(m, dy, 0), dx, 1)
            take = grow & nm & (a[..., 3] == 0)
            a[take] = nb[take]
        m = a[..., 3] > 0
    return a


def stack(layers, slots):
    out = np.zeros((256, 256, 4), np.uint8)
    for s in slots:
        if s in layers:
            m = layers[s][..., 3] > 0
            out[m] = layers[s][m]
    return out


def width_of(img, a, b):
    """Mean half-width of a limb mask perpendicular to a->b (screen)."""
    m = img[..., 3] > 0
    ys, xs = np.nonzero(m)
    if not len(xs): return 5.0
    d = b - a; L = np.linalg.norm(d); u = d / L; n = np.array([-u[1], u[0]])
    rel = np.stack([xs - a[0], ys - a[1]], 1)
    t = rel @ u; o = rel @ n
    keep = (t > L * .15) & (t < L * .85)
    if not keep.any(): return 5.0
    bins = np.round(t[keep]).astype(int)
    widths = [o[keep][bins == k].max() - o[keep][bins == k].min() + 1 for k in np.unique(bins)]
    return float(np.median(widths)) / 2


def march_capsules(segs, box=(60, 60, 200, 236)):
    """segs: list of (a3, b3, r). Returns per-pixel hit point, segment index and depth for the front-most surface."""
    x0, y0, x1, y1 = box
    ys, xs = np.mgrid[y0:y1, x0:x1]; xs = xs.ravel() + .5; ys = ys.ravel() + .5
    view = np.array([0, .5, 1.0]); view /= np.linalg.norm(view)
    zf = 80.0
    o = np.stack([xs - CX, GROUND_Y - ys + .5 * zf, np.full_like(xs, zf)], 1)
    def sd(p):
        out = []
        for a, b, r in segs:
            ba = b - a; h = np.clip(((p - a) @ ba) / (ba @ ba), 0, 1)
            out.append(np.linalg.norm(p - a - h[:, None] * ba, axis=1) - r)
        return np.stack(out)
    t = np.zeros(len(xs)); alive = np.ones(len(xs), bool); hit = np.zeros(len(xs), bool)
    for _ in range(120):
        i = np.where(alive)[0]
        if not len(i): break
        p = o[i] - t[i, None] * view
        d = sd(p).min(0)
        done = d < .05; hit[i[done]] = True; alive[i[done]] = False
        t[i] += np.maximum(d, .05) * ~done
        alive &= t < 2 * zf + 80
    idx = np.where(hit)[0]
    p = o[idx] - t[idx, None] * view
    which = sd(p).argmin(0)
    return ys[idx].astype(int), xs[idx].astype(int), p, which


def render_limb(rig, P, side, kind, texture, radii):
    """Re-posed limb of one side; colour sampled from the idle original through the segment rotation."""
    I = rig.idle
    names = ('hip', 'knee', 'ankle') if kind == 'leg' else ('shoulder', 'elbow', 'wrist')
    a0, b0, c0 = (I[n + side] for n in names)
    a1, b1, c1 = (P[n + side] for n in names)
    segs = [(a1, b1, radii[0]), (b1, c1, radii[1])]
    py, px, p, which = march_capsules(segs)
    out = np.zeros((256, 256, 4), np.uint8)
    if not len(px): return out
    src = np.zeros((len(px), 2))
    for k, ((s0, e0), (s1, e1)) in enumerate([((a0, b0), (a1, b1)), ((b0, c0), (b1, c1))]):
        m = which == k
        R = min_rotation((e1 - s1) / np.linalg.norm(e1 - s1), (e0 - s0) / np.linalg.norm(e0 - s0))
        q = (p[m] - s1) @ R.T + s0
        src[m] = np.stack([CX + q[:, 0], GROUND_Y - q[:, 1] + q[:, 2] / 2], 1)
    sx = np.clip(np.floor(src[:, 0]).astype(int), 0, 255); sy = np.clip(np.floor(src[:, 1]).astype(int), 0, 255)
    col = texture[sy, sx]
    ok = col[:, 3] > 0
    out[py[ok], px[ok]] = col[ok]
    # fresh 1-px outline on the re-posed silhouette, in a darkened tone of the limb
    m = out[..., 3] > 0
    edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    out[edge, :3] = (out[edge, :3] * .38).astype(np.uint8)
    return out


def translated(img, d):
    dx, dy = int(round(d[0])), int(round(d[1]))
    return np.roll(np.roll(img, dy, 0), dx, 1)


def compose(facing, frame, layers, rig, pose):
    P = rig.pose(pose)
    order = frame['drawOrder']
    bob_px = (0, P['bob'])
    canvas = np.zeros((256, 256, 4), np.uint8)
    def over(img):
        m = img[..., 3] > 0; canvas[m] = img[m]
    textures, radii = {}, {}
    for s in 'RL':
        n = SIDE[s]
        I = rig.idle
        textures['leg' + s] = extend(stack(layers, ['outfit.pants.' + n]), steps=6)   # trousers only: no skin between shin and boot
        textures['arm' + s] = extend(stack(layers, ['body.arm.' + n, 'outfit.sleeve.' + n]))
        legimg = stack(layers, ['body.leg.' + n, 'outfit.pants.' + n])
        armimg = stack(layers, ['body.arm.' + n, 'outfit.sleeve.' + n])
        pr = lambda k: project(I[k + s])
        radii['leg' + s] = (width_of(legimg, pr('hip'), pr('knee')), width_of(legimg, pr('knee'), pr('ankle')))
        radii['arm' + s] = (width_of(armimg, pr('shoulder'), pr('elbow')), width_of(armimg, pr('elbow'), pr('wrist')))
    done = set()
    for slot in order:
        side = 'R' if slot.endswith('.right') else 'L' if slot.endswith('.left') else None
        if slot in ('body.leg.right', 'body.leg.left', 'body.arm.right', 'body.arm.left'):
            continue                                       # drawn together with pants / sleeves
        if slot.startswith('outfit.pants.'):
            over(render_limb(rig, P, side, 'leg', textures['leg' + side], radii['leg' + side]))
        elif slot.startswith('outfit.sleeve.'):
            over(render_limb(rig, P, side, 'arm', textures['arm' + side], radii['arm' + side]))
        elif slot.startswith('outfit.boot.'):
            d = project(P['ankle' + side]) - project(rig.idle['ankle' + side])
            over(translated(layers[slot], d))
        elif slot.startswith('body.hand.'):
            d = project(P['wrist' + side]) - project(rig.idle['wrist' + side])
            over(translated(layers[slot], d))
        elif slot in layers:
            over(translated(layers[slot], bob_px))         # torso, head, face, hair, weapon
    return Image.fromarray(canvas)
