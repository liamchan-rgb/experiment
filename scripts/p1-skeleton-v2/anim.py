import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import comp, layers, selection, BASE
import skel

SIDES = {'R': ('Right', ['body.leg.right', 'outfit.pants.right', 'outfit.boot.right'], ['body.arm.right', 'outfit.sleeve.right', 'body.hand.right']),
         'L': ('Left', ['body.leg.left', 'outfit.pants.left', 'outfit.boot.left'], ['body.arm.left', 'outfit.sleeve.left', 'body.hand.left'])}
STEP = 12.0   # ground px per pose (24 units per cycle = 96 px)
# Jog cycle for the right foot, q = poses since its contact: (ground forward u, lift)
LEG = [(12, 0), (0, 0), (-12, 0), (-17, 6), (-11, 13), (1, 13), (11, 8), (14, 2)]
BOB = [0, 2, 0, -2]
ARM_SWING = math.radians(24)
ELBOW = math.radians(40)

def lum(a):
    return a[..., 0] * .3 + a[..., 1] * .59 + a[..., 2] * .11

def outline(images, threshold=75, factor=.42):
    """Darken non-dark pixels on the outer edge of the union silhouette of `images`."""
    arrays = [np.array(im) for im in images]
    union = np.zeros(arrays[0].shape[:2], bool)
    for a in arrays: union |= a[..., 3] > 0
    p = np.pad(union, 1)
    edge = union & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    out = []
    for a in arrays:
        a = a.copy()
        m = edge & (a[..., 3] > 0) & (lum(a) > threshold)
        a[m, :3] = (a[m, :3] * factor).astype(np.uint8)
        out.append(Image.fromarray(a))
    return out

def prepare(direction, idle):
    """Repaint pass: limb and torso silhouettes get a clean outline."""
    idle = list(idle)
    names = [s for s, _ in idle]
    groups = [legs for _, legs, _ in SIDES.values()] + [arms for _, _, arms in SIDES.values()]
    groups.append(['body.torso', 'outfit.torso', 'outfit.hem.front'])
    for g in groups:
        idx = [i for i, s in enumerate(names) if s in g]
        if not idx: continue
        for i, im in zip(idx, outline([idle[i][1] for i in idx])):
            idle[i] = (names[i], im)
    return idle

def pose(direction, p, sel=None, params=None):
    P = dict(LEG=LEG, BOB=BOB, ARM_SWING=ARM_SWING, ELBOW=ELBOW)
    if params: P.update(params)
    frame = comp.frames[(direction, 'idle', 0)]
    J = {k: np.array(v, float) for k, v in frame['joints'].items()}
    idle = prepare(direction, layers(direction, 'idle', 0, sel or selection()))
    bob = P['BOB'][p % 4]
    canvas = np.zeros((256, 256, 4), np.uint8)
    slot_side = {}
    for side, (name, legs, arms) in SIDES.items():
        for s in legs: slot_side[s] = (side, 'leg')
        for s in arms: slot_side[s] = (side, 'arm')
    rig = {}
    for side, (name, _, _) in SIDES.items():
        hip, knee, ankle = J['hip' + name], J['knee' + name], J['ankle' + name]
        l1, l2 = abs(knee[1] - hip[1]), abs(ankle[1] - knee[1])
        lat1, lat2 = knee[0] - hip[0], ankle[0] - knee[0]
        u, lift = P['LEG'][(p if side == 'R' else p + 4) % 8]
        k, a = skel.two_bone(l1, l2, u, -(l1 + l2) + bob + lift)
        hs = hip + np.array([0, bob])
        ks = hs + skel.project(direction, *k) + np.array([lat1, 0])
        as_ = hs + skel.project(direction, *a) + np.array([lat1 + lat2, 0])
        rig[side, 'leg'] = [(hip, knee, hs, ks), (knee, ankle, ks, as_)]
        sh, el, wr = J['shoulder' + name], J['elbow' + name], J['wrist' + name]
        m1, m2 = abs(el[1] - sh[1]), abs(wr[1] - el[1])
        alat1, alat2 = el[0] - sh[0], wr[0] - el[0]
        swing = P['ARM_SWING'] * math.cos(2 * math.pi * p / 8) * (1 if side == 'L' else -1)
        bend = P['ELBOW'] * (1 + .35 * max(0, swing) / P['ARM_SWING'])
        e = np.array([m1 * math.sin(swing), -m1 * math.cos(swing)])
        w = e + np.array([m2 * math.sin(swing + bend), -m2 * math.cos(swing + bend)])
        ss = sh + np.array([0, bob])
        es = ss + skel.project(direction, *e) + np.array([alat1, 0])
        ws = ss + skel.project(direction, *w) + np.array([alat1 + alat2, 0])
        rig[side, 'arm'] = [(sh, el, ss, es), (el, wr, es, ws)]
    def rigid(im, anchor, target, canvas=canvas):
        """Exact pixels, translated so `anchor` lands on `target` (no rotation, no scaling)."""
        dx, dy = (int(round(v)) for v in (target - anchor))
        a = np.roll(np.array(im), (dy, dx), axis=(0, 1))
        m = a[..., 3] > 0
        canvas[m] = a[m]

    def segment(im, rows, joint, canvas=canvas):
        (p0, c0, P0, C0), (p1, c1, P1, C1) = joint
        upper = skel.Piece(im, (rows[0], int(c0[1]) + 3))
        lower = skel.Piece(im, (int(c0[1]) - 2, rows[1]))
        for piece, (sp, sc, dp, dc) in ((lower, (p1, c1, P1, C1)), (upper, (p0, c0, P0, C0))):
            sd, dd = sc - sp, dc - dp
            piece.draw(canvas, sp, sd, dp, dd, np.linalg.norm(dd) / np.linalg.norm(sd))
        # joint cap: a disc of source pixels around the joint, rotated halfway
        r = 4 if np.linalg.norm(c1 - c0) > 14 else 3
        disc = np.array(im).copy()
        yy, xx = np.mgrid[0:256, 0:256]
        disc[((xx - c0[0]) ** 2 + (yy - c0[1]) ** 2 > r * r) | (yy < rows[0]) | (yy >= rows[1])] = 0
        d0 = (c0 - p0) / np.linalg.norm(c0 - p0) + (c1 - p1) / np.linalg.norm(c1 - p1)
        d1 = (C0 - P0) / np.linalg.norm(C0 - P0) + (C1 - P1) / np.linalg.norm(C1 - P1)
        skel.Piece(Image.fromarray(disc)).draw(canvas, c0, d0, C0, d1)

    legs_buf = {}
    last_leg_slot = {}
    for slot, _ in idle:
        if slot in slot_side and slot_side[slot][1] == 'leg':
            last_leg_slot[slot_side[slot][0]] = slot
    for slot, im in idle:
        if slot in slot_side:
            side, kind = slot_side[slot]
            joint = rig[side, kind]
            end_src, end_dst = joint[1][1], joint[1][3]
            if kind == 'leg':
                # Legs build in their own buffers; the skin leg only shows inside the clothing.
                skin, cloth = legs_buf.setdefault(side, (np.zeros_like(canvas), np.zeros_like(canvas)))
                if slot.startswith('body.leg'):
                    cut = int(end_src[1])
                    segment(im, (-999, cut + 2), joint, skin)
                    foot = np.array(im).copy(); foot[:cut - 1] = 0
                    rigid(Image.fromarray(foot), end_src, end_dst, skin)
                elif slot.startswith('outfit.boot'):
                    rigid(im, end_src, end_dst, cloth)   # shoes keep their exact pixels
                else:
                    segment(im, (-999, 999), joint, cloth)
                if slot == last_leg_slot[side]:
                    covered = cloth[..., 3] > 0
                    if covered.any():
                        skin[~covered] = 0
                    for layer in (skin, cloth):
                        m = layer[..., 3] > 0
                        canvas[m] = layer[m]
            elif slot.startswith('body.hand'):
                rigid(im, end_src, end_dst)              # hands keep their exact pixels
            else:
                segment(im, (-999, 999), joint)          # sleeves bend at the elbow
        else:
            a = np.array(im)
            if bob:
                a = np.roll(a, bob, axis=0)
            m = a[..., 3] > 0
            canvas[m] = a[m]
    return Image.fromarray(canvas), rig

def ground_frame(direction, offset, size=256):
    """Checker ground in ground coords projected; offset = ground px travelled."""
    fx, fz = skel.GROUND[direction]
    ys, xs = np.mgrid[0:size, 0:size].astype(float)
    # screen (x, y) relative to (128, 214) -> ground (gx, gz) with height 0: gz = 2*(y-214)
    gx, gz = xs - 128 + offset * fx, 2 * (ys - 214) + offset * fz
    c = ((np.floor(gx / 16) + np.floor(gz / 16)) % 2).astype(np.uint8)
    img = np.zeros((size, size, 4), np.uint8)
    img[..., 0] = 70 + 14 * c; img[..., 1] = 104 + 16 * c; img[..., 2] = 60 + 8 * c; img[..., 3] = 255
    return Image.fromarray(img)

if __name__ == '__main__':
    direction = sys.argv[1] if len(sys.argv) > 1 else 'down-right'
    cells = [pose(direction, p)[0] for p in range(8)]
    sheet = Image.new('RGBA', (8 * 120 * 3, 160 * 3), (74, 104, 62, 255))
    for p, c in enumerate(cells):
        sheet.alpha_composite(c.crop((68, 76, 188, 236)).resize((360, 480), Image.NEAREST), (p * 360, 0))
    sheet.save(f'v3_{direction}_poses.png')
    for ms, tag in ((40, 'game'), (120, 'slow')):
        frames = []
        for k in range(24):
            p = k % 8
            g = ground_frame(direction, -k * STEP)
            g.alpha_composite(cells[p])
            frames.append(g.crop((56, 64, 200, 240)).resize((288, 352), Image.NEAREST).convert('RGB'))
        frames[0].save(f'v3_{direction}_{tag}.gif', save_all=True, append_images=frames[1:], duration=ms, loop=0)
