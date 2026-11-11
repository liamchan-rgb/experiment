"""A fully procedural HD-2D character: a 3D figure made of signed-distance parts on a small skeleton, ray-marched from the game's
oblique camera straight into pixel art (banded light, dithered ramps, outlines). Nothing is drawn by hand and no art of the project is
used. Eight facings are the same figure turned in steps of 45 degrees, so they always agree; gear is a list of parts on named bones
(`LOADOUTS`), so a new item is a few lines here and a re-bake.

Model space: +x the figure's right, +y forward, +z up; 1 unit is the figure's height."""
import numpy as np

F32 = np.float32
def V(*a): return np.array(a, F32)
def norm(v): return v / max(1e-6, float(np.linalg.norm(v)))
def rz(a): c, s = np.cos(a), np.sin(a); return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], F32)       # rows: right, forward, up
def rx(a): c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, s], [0, -s, c]], F32)
def ry(a): c, s = np.cos(a), np.sin(a); return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]], F32)

# ---------------------------------------------------------------- skeleton
STRIDE, HIP_W, SHOULDER_W, LEG, UPPER, FORE, HEAD_R = 0.25, 0.055, 0.1, 0.212, 0.13, 0.12, 0.132

def ik(hip, ankle, l1=LEG, l2=LEG):
    v = ankle - hip; d = min(float(np.linalg.norm(v)), l1 + l2 - 1e-3)
    v = v / max(1e-6, np.linalg.norm(v)) * d
    f = V(0, 1, 0.25); perp = norm(f - v * (f @ v) / (d * d))
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    return hip + v * (a / d) + perp * np.sqrt(max(0.0, l1 * l1 - a * a))

def pose(t=None, breath=0.0):
    """Joint positions and bone frames. `t` in [0,1) is the walk phase (left foot forward at 0); None is standing (`breath` 0..1)."""
    walk = t is not None
    tau = 2 * np.pi * (t if walk else 0)
    hip_z = 0.445 - (0.013 * np.cos(2 * tau) if walk else 0.004 + 0.003 * np.sin(2 * np.pi * breath))
    C = V(0.012 * np.sin(tau) if walk else 0, 0, hip_z)
    twist = 0.14 * np.cos(tau) if walk else 0.0
    lean = 0.07 if walk else 0.0
    Rh, Rc = rz(twist), rx(-lean) @ rz(-twist * 0.9)
    J, B = {}, {}
    for side, name, ph in ((-1, 'l', 0.0), (1, 'r', 0.5)):
        hip = C + V(side * HIP_W, 0, 0) @ Rh
        if walk:
            p = (t + ph) % 1.0
            if p < 0.5:
                y = STRIDE / 2 - STRIDE * p / 0.5; lift = 0.022 * max(0, (p - 0.38) / 0.12); pitch = 0.55 * max(0, (p - 0.38) / 0.12)
            else:
                s = (p - 0.5) / 0.5; e = s * s * (3 - 2 * s)
                y = -STRIDE / 2 + STRIDE * e; lift = 0.022 * (1 - s) + 0.075 * np.sin(np.pi * s); pitch = 0.55 * np.cos(np.pi * s)
        else: y, lift, pitch = 0.0, 0.0, 0.0
        ankle = V(side * (HIP_W + 0.004), y - 0.02, 0.045 + lift)
        knee = ik(hip, ankle)
        toe = ankle + V(side * 0.01, 0.085 * np.cos(pitch), -0.024 - 0.085 * np.sin(pitch) * 0.6)
        J.update({f'hip_{name}': hip, f'knee_{name}': knee, f'ankle_{name}': ankle, f'toe_{name}': toe})
        swing = (-side) * -0.6 * np.cos(tau) if walk else 0.04
        bend = (0.45 + 0.3 * max(0.0, np.sin(swing))) if walk else 0.22
        sh = C + V(0, 0.012, 0.272 + (0.004 * np.sin(2 * np.pi * breath) if not walk else 0)) + V(side * SHOULDER_W, 0, 0) @ Rc
        ud = norm(V(side * 0.2, np.sin(swing), -np.cos(swing)))
        el = sh + ud * UPPER
        fd = norm(V(side * 0.02, np.sin(swing + bend), -np.cos(swing + bend)))
        hand = el + fd * FORE
        J.update({f'shoulder_{name}': sh, f'elbow_{name}': el, f'hand_{name}': hand})
        up = norm(np.cross(fd, V(side, 0, 0))); right = norm(np.cross(fd, up))
        B[f'hand_{name}'] = (hand, np.stack([right, fd, up]).astype(F32))      # forward runs along the forearm
        B[f'forearm_{name}'] = ((el + hand) / 2, np.stack([right, fd, up]).astype(F32))
    chest = C + V(0, 0.012, 0.19)
    neck = C + V(0, 0.02 + lean * 0.2, 0.3)
    bob = 0.006 * np.cos(2 * tau + 0.6) if walk else 0.003 * np.sin(2 * np.pi * breath)
    head = neck + V(0, 0.012, 0.148 + bob)
    J.update(C=C, chest=chest, neck=neck, head=head)
    B.update(hips=(C, Rh), chest=(chest, Rc), back=(chest, Rc), head=(head, rx(0.04) @ rz(twist * 0.25)))
    B['cape'] = (chest + V(0, 0, 0.085) @ Rc, rx(0.2 + (0.13 * np.sin(2 * tau + 1.0) + 0.1 if walk else 0.0)) @ rz(-twist * 0.5 + (0.1 * np.sin(tau) if walk else 0)))
    return J, B

# ---------------------------------------------------------------- parts
# A part: (material, kind, args). Kinds: 'cap' (a, b, r1, r2), 'ell' (centre, basis, radii), 'box' (centre, basis, half, round), 'hair' (centre, basis).
SMOOTH = dict(skin=0.02, cloth=0.035, cloth2=0.03, pants=0.03, boots=0.022, hair=0.03, leather=0.012, metal=0.006, accent=0.02, wood=0.008, gem=0.005, cape=0.015, dark=0.01)

def body(J, B, look):
    P = []
    C, (ch, Rc), (hd, Rhd), (_, Rhip) = J['C'], B['chest'], B['head'], B['hips']
    P += [('skin', 'ell', (hd, Rhd, V(HEAD_R, HEAD_R * 0.96, HEAD_R))), ('skin', 'ell', (hd + V(0, 0.02, -0.07) @ Rhd, Rhd, V(HEAD_R * 0.8, HEAD_R * 0.78, HEAD_R * 0.7)))]
    P += [('skin', 'cap', (J['neck'] - V(0, 0, 0.03), hd - V(0, 0, 0.08), 0.032, 0.032))]
    P += [('hair', 'hair', (hd, Rhd))]
    for sx in (-1, 1):                                                                              # side locks in front of the ears
        P += [('hair', 'cap', (hd + V(sx * 0.118, 0.03, 0.02) @ Rhd, hd + V(sx * 0.122, 0.035, -0.12) @ Rhd, 0.034, 0.018))]
    if look.get('ponytail', True):
        b = hd + V(0, -0.135, 0.045) @ Rhd; sway = B['cape'][1]
        P += [('hair', 'cap', (b, b + V(0, -0.075, -0.16) @ sway, 0.046, 0.02)), ('accent', 'ell', (b + V(0, 0.004, 0.0), Rhd, V(0.034, 0.028, 0.03)))]
    else:
        for sx in (-1, 0, 1):                                                                       # long loose hair down the back
            P += [('hair', 'cap', (hd + V(sx * 0.07, -0.1, 0.0) @ Rhd, hd + V(sx * 0.085, -0.12, -0.2) @ B['cape'][1], 0.06, 0.03))]
    # torso: a fitted tunic, shoulders wider than the waist, a skirt flaring below the belt
    P += [('cloth', 'ell', (ch + V(0, 0, 0.045) @ Rc, Rc, V(0.098, 0.068, 0.075))), ('cloth', 'ell', (ch - V(0, 0, 0.07), Rhip, V(0.078, 0.06, 0.08)))]
    P += [('cloth', 'cap', (C + V(0, 0, 0.04), C - V(0, 0.004, 0.07), 0.074, 0.096))]
    P += [('leather', 'ell', (C + V(0, 0, 0.06), Rhip, V(0.09, 0.074, 0.017))), ('metal', 'box', (C + V(0, 0.072, 0.06) @ Rhip, Rhip, V(0.017, 0.007, 0.015), 0.004))]
    P += [('cloth2', 'ell', (ch + V(0, 0.008, 0.1) @ Rc, Rc, V(0.06, 0.055, 0.024)))]                       # collar
    P += [('cloth2', 'box', (ch + V(0, 0.066, 0.02) @ Rc, Rc, V(0.008, 0.006, 0.07), 0.004))]              # placket down the front
    for n, side in (('l', -1), ('r', 1)):
        sh, el, ha = J[f'shoulder_{n}'], J[f'elbow_{n}'], J[f'hand_{n}']
        P += [('cloth', 'cap', (sh, el, 0.04, 0.032)), ('cloth', 'ell', (sh, Rc, V(0.046, 0.044, 0.042)))]
        P += [('cloth2', 'cap', (el, el + (ha - el) * 0.45, 0.032, 0.029)), ('leather', 'cap', (el + (ha - el) * 0.4, el + (ha - el) * 0.92, 0.03, 0.026))]
        P += [('skin', 'ell', (ha + (ha - el) * 0.14, B[f'hand_{n}'][1], V(0.025, 0.031, 0.023)))]
        hp, kn, an, toe = J[f'hip_{n}'], J[f'knee_{n}'], J[f'ankle_{n}'], J[f'toe_{n}']
        P += [('pants', 'cap', (hp, kn, 0.05, 0.039)), ('pants', 'cap', (kn, kn + (an - kn) * 0.35, 0.039, 0.036))]
        P += [('boots', 'cap', (kn + (an - kn) * 0.3, an, 0.039, 0.033)), ('boots', 'cap', (an - V(0, 0, 0.01), toe, 0.034, 0.029))]
        P += [('leather', 'cap', (kn + (an - kn) * 0.27, kn + (an - kn) * 0.36, 0.043, 0.043))]             # boot cuff
    return P

def gear(B, items):
    """Gear parts given in a bone's own frame (right, forward, up from the bone's origin)."""
    P = []
    for bone, mat, kind, a in items:
        o, R = B[bone]
        if kind == 'cap': P.append((mat, 'cap', (o + V(*a[0]) @ R, o + V(*a[1]) @ R, a[2], a[3])))
        elif kind == 'ell': P.append((mat, 'ell', (o + V(*a[0]) @ R, (a[2] if len(a) > 2 else np.eye(3, dtype=F32)) @ R, V(*a[1]))))
        elif kind == 'box': P.append((mat, 'box', (o + V(*a[0]) @ R, (a[3] if len(a) > 3 else np.eye(3, dtype=F32)) @ R, V(*a[1]), a[2])))
    return P

TILT = ry(0.6)
LOADOUTS = {
    # A swordsman: cape, a sword across the back, a round shield on the left forearm, a scarf.
    'knight': dict(look=dict(ponytail=True), palette=dict(cloth=(52, 92, 168), cloth2=(226, 222, 206), pants=(70, 62, 78), boots=(96, 62, 44), hair=(214, 150, 62), accent=(196, 54, 58), cape=(150, 40, 52)), items=[
        ('cape', 'cape', 'box', ((0, -0.088, -0.15), (0.1, 0.01, 0.185), 0.012)),
        ('chest', 'accent', 'ell', ((0, 0.004, 0.098), (0.072, 0.066, 0.028))),
        ('back', 'leather', 'box', ((0.0, -0.1, 0.03), (0.022, 0.014, 0.17), 0.006, TILT)),
        ('back', 'metal', 'box', ((0.118, -0.104, 0.195), (0.05, 0.012, 0.012), 0.004, TILT)),
        ('back', 'wood', 'cap', ((0.125, -0.104, 0.21), (0.16, -0.104, 0.26), 0.014, 0.014)),
        ('back', 'gem', 'ell', ((0.166, -0.104, 0.27), (0.02, 0.02, 0.02))),
        ('forearm_l', 'metal', 'ell', ((-0.045, 0.0, 0.0), (0.014, 0.095, 0.095))),
        ('forearm_l', 'cloth', 'ell', ((-0.051, 0.0, 0.0), (0.014, 0.074, 0.074))),
        ('forearm_l', 'gem', 'ell', ((-0.06, 0.0, 0.0), (0.012, 0.026, 0.026))),
    ]),
    # A mage: robe colours, a pointed hat, a staff on the back, a satchel; no cape, loose hair.
    'mage': dict(look=dict(ponytail=False), palette=dict(cloth=(104, 62, 150), cloth2=(238, 214, 150), pants=(58, 54, 84), boots=(74, 52, 60), hair=(232, 232, 240), accent=(240, 190, 70), cape=(60, 40, 90)), items=[
        ('head', 'cloth', 'ell', ((0, -0.01, 0.085), (0.19, 0.19, 0.018), rx(-0.12))),
        ('head', 'cloth', 'cap', ((0, -0.01, 0.09), (0, -0.07, 0.3), 0.1, 0.01)),
        ('head', 'accent', 'ell', ((0, -0.012, 0.108), (0.106, 0.106, 0.018), rx(-0.12))),
        ('back', 'wood', 'cap', ((-0.15, -0.098, -0.22), (0.12, -0.098, 0.3), 0.013, 0.013)),
        ('back', 'gem', 'ell', ((0.135, -0.098, 0.33), (0.034, 0.034, 0.034))),
        ('back', 'metal', 'ell', ((0.122, -0.098, 0.3), (0.022, 0.022, 0.013))),
        ('hips', 'leather', 'box', ((0.098, 0.0, -0.02), (0.026, 0.045, 0.04), 0.012)),
        ('hips', 'metal', 'box', ((0.128, 0.0, -0.01), (0.004, 0.013, 0.011), 0.003)),
        ('cape', 'cape', 'box', ((0, -0.085, -0.06), (0.085, 0.01, 0.09), 0.012)),
    ]),
}

# ---------------------------------------------------------------- distance field
def sd_cap(P, a, b, r1, r2):
    pa, ba = P - a, b - a
    h = np.clip(pa @ ba / max(1e-8, float(ba @ ba)), 0, 1)
    return np.linalg.norm(pa - h[:, None] * ba, axis=1) - (r1 + (r2 - r1) * h)
def sd_ell(P, c, R, rad):
    q = (P - c) @ R.T / rad; k = np.linalg.norm(q, axis=1)
    return (k - 1) * float(rad.min())
def sd_box(P, c, R, half, rnd):
    q = np.abs((P - c) @ R.T) - half
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0) - rnd
def sd_hair(P, c, R):
    """A cap of hair over the head with a window cut for the face; the window's top edge is a zigzag fringe."""
    q = (P - c) @ R.T
    shell = (np.linalg.norm((q - V(0, -0.014, 0.022)) / V(HEAD_R * 1.1, HEAD_R * 1.1, HEAD_R * 1.07), axis=1) - 1) * HEAD_R
    fringe = 0.05 + 0.03 * np.abs(((q[:, 0] * 14.0 + 0.5) % 1.0) - 0.5) * 2 - 0.02 * np.abs(q[:, 0]) / 0.1
    window = np.maximum.reduce([np.abs(q[:, 0]) - 0.098, 0.03 - q[:, 1], q[:, 2] - fringe])
    return np.maximum(shell, -window)

MATS = list(SMOOTH)
def field(P, parts):
    """Nearest distance and material index for points P."""
    per = {}
    for mat, kind, a in parts:
        d = sd_cap(P, *a) if kind == 'cap' else sd_ell(P, *a) if kind == 'ell' else sd_box(P, *a) if kind == 'box' else sd_hair(P, *a)
        if mat in per:
            k = SMOOTH[mat]; o = per[mat]; h = np.clip(0.5 + 0.5 * (d - o) / k, 0, 1)
            per[mat] = d * (1 - h) + o * h - k * h * (1 - h)
        else: per[mat] = d
    best = np.full(len(P), 1e9, F32); idx = np.zeros(len(P), np.int16)
    for mat, d in per.items():
        m = d < best; best = np.where(m, d, best); idx[m] = MATS.index(mat)
    return best, idx
