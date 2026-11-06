"""Per-slot shapes for every P1 asset on the v3 model.

Each asset fills exactly the slots it owns in the existing part pipeline, so the
compositor, atlas rebake, head split and runtime head compositor keep working.
Local frame: x = character's left, y up, z forward.
"""
import math
import numpy as np
from model import Shape, sd_capsule, sd_ellipsoid, sd_cylinder, sd_box, smin
from body import FACING, rot_x

SIDES = (('R', 'right'), ('L', 'left'))


class Frame:
    """World-space helpers for one posed skeleton and facing."""
    def __init__(self, J, facing):
        fx, fz = FACING[facing]
        self.W = np.array([[fz, 0, fx], [0, 1, 0], [-fx, 0, fz]])
        self.J, self.C = J, J['chest_rot']
        self.Bc = self.W @ self.C
        self.pel = self.w(J['pelvis'])

    def w(self, v):
        return self.W @ v

    def chest(self, v):
        """Point given in chest-local coordinates (origin at the pelvis)."""
        return self.w(self.J['pelvis'] + self.C @ np.array(v, float))

    def local(self, p):
        return (p - self.pel) @ self.Bc

    def joint(self, name):
        return self.w(self.J[name])


def torso_sdf(F, widen=0.0, length=0.0, depth=0.0):
    chest_c, shoulder_c, hem_c = F.chest([0, 20, 0]), F.chest([0, 32, 0]), F.chest([0, 2 - length * .5, .5])
    def sdf(p):
        a = sd_ellipsoid(p, chest_c, np.array([16 + widen, 16, 12 + depth]), F.Bc)
        b = sd_ellipsoid(p, shoulder_c, np.array([17 + widen, 7, 11 + depth]), F.Bc)
        c = sd_ellipsoid(p, hem_c, np.array([17 + widen, 10 + length * .5, 13 + depth]), F.Bc)
        return smin(smin(a, b, 4), c, 4)
    return sdf


def collar_shape(F, material, rim, name='collar', radius=6.2):
    up = F.Bc @ np.array([0, 1.0, 0])
    base = F.joint('neck') - up * 6.5
    def sdf(p): return sd_cylinder(p, base, base + up * 4.2, radius, 1.2)
    def detail(p, mat):
        h = (p - base) @ up
        radial = np.linalg.norm((p - base) - h[:, None] * up, axis=1)
        mat = mat.copy(); mat[(h > 3.2) & (radial > radius - 1.6)] = rim; return mat
    return Shape(name, material, sdf, detail, 'torso')


def limb_frac(p, a, b):
    ba = b - a
    return ((p - a) @ ba) / (ba @ ba)


def hand_center(F, side):
    el, wr = F.joint('elbow' + side), F.joint('wrist' + side)
    return wr + (wr - el) / np.linalg.norm(wr - el) * 3.4


# ---------------- base body ----------------
def base(F):
    slots = {}
    neck = F.joint('neck')
    up = F.Bc @ np.array([0, 1.0, 0])
    chest_c = F.chest([0, 19, 0])
    slots['body.torso'] = [
        Shape('skin_torso', 'skin', lambda p: sd_ellipsoid(p, chest_c, np.array([14, 17, 10.5]), F.Bc), group='torso'),
        Shape('neck', 'skin', lambda p: sd_capsule(p, neck - up * 7, neck + up * 1, 4.0), group='torso')]
    for s, name in SIDES:
        sh, el, wr = F.joint('shoulder' + s), F.joint('elbow' + s), F.joint('wrist' + s)
        slots['body.arm.' + name] = [
            Shape('upper_skin' + s, 'skin', lambda p, a=sh, b=el: sd_capsule(p, a, b, 5.0, 4.4), group='arm' + s),
            Shape('fore_skin' + s, 'skin', lambda p, a=el, b=wr: sd_capsule(p, a, b, 4.4, 4.0), group='arm' + s)]
        hc = hand_center(F, s)
        slots['body.hand.' + name] = [Shape('hand' + s, 'skin', lambda p, c=hc: sd_ellipsoid(p, c, np.array([5.0, 5.3, 5.0])), group='hand' + s)]
        hip, knee, ankle = F.joint('hip' + s), F.joint('knee' + s), F.joint('ankle' + s)
        slots['body.leg.' + name] = [
            Shape('thigh_skin' + s, 'skin', lambda p, a=hip, b=knee: sd_capsule(p, a, b, 6.4, 5.8), group='leg' + s),
            Shape('shin_skin' + s, 'skin', lambda p, a=knee, b=ankle: sd_capsule(p, a, b, 5.6, 5.0), group='leg' + s)]
    return slots


# ---------------- trousers and boots ----------------
def lower(F):
    slots = {}
    hips_c = F.chest([0, 1, 0])
    for s, name in SIDES:
        hip, knee, ankle = F.joint('hip' + s), F.joint('knee' + s), F.joint('ankle' + s)
        sx = -1 if s == 'R' else 1
        seat_c = F.chest([sx * 6, 1, 0])
        def pants(p, a=hip, b=knee, c=ankle, seat=seat_c):
            thigh = sd_capsule(p, a, b, 7.6, 7.0)
            shin = sd_capsule(p, b, c, 6.8, 6.2)
            seat_ = sd_ellipsoid(p, seat, np.array([7.4, 6, 8.6]), F.Bc)
            return smin(smin(thigh, shin, 2), seat_, 3)
        def crease(p, mat, a=hip, b=knee, c=ankle):
            mat = mat.copy()
            return mat
        slots['outfit.pants.' + name] = [Shape('pants' + s, 'pants', pants, crease, 'leg' + s)]
        pitch = F.J['foot' + s]
        Fm = F.W @ rot_x(pitch)
        shaft_top = ankle + (knee - ankle) / np.linalg.norm(knee - ankle) * 6
        foot_c = ankle + Fm @ np.array([0, -4.4, 4.2])
        sole_off = Fm @ np.array([0, -9.0, 0])
        def boot(p, a=ankle, t=shaft_top, c=foot_c, Fm=Fm, so=sole_off):
            shaft = sd_capsule(p, a, t, 6.6, 7.0)
            toe = sd_ellipsoid(p, c, np.array([6.8, 5.4, 10.5]), Fm)
            body = smin(shaft, toe, 3)
            n = Fm @ np.array([0, -1.0, 0])
            return np.maximum(body, (p - (a + so)) @ n)
        def boot_detail(p, mat, a=ankle, Fm=Fm, t=shaft_top):
            q = (p - a) @ Fm
            mat = mat.copy()
            mat[q[:, 1] < -7.6] = 'sole'
            top = (p - a) @ ((t - a) / np.linalg.norm(t - a))
            mat[top > 4.4] = 'cuff'
            # laces: a short darker line down the instep
            mat[(np.abs(q[:, 0]) < .9) & (q[:, 2] > 2) & (q[:, 2] < 8) & (q[:, 1] > -5)] = 'cuff'
            return mat
        slots['outfit.boot.' + name] = [Shape('boot' + s, 'boot', boot, boot_detail, 'foot' + s)]
    return slots


# ---------------- outfit helpers ----------------
def sleeves(F, upper_mat, fore_mat, cuff_mat, short=False, bracer=None):
    slots = {}
    for s, name in SIDES:
        sh, el, wr = F.joint('shoulder' + s), F.joint('elbow' + s), F.joint('wrist' + s)
        shapes = []
        if short:
            mid = sh + (el - sh) * .78
            shapes.append(Shape('sleeve' + s, upper_mat, lambda p, a=sh, b=mid: sd_capsule(p, a, b, 6.8, 6.2),
                                lambda p, mat, a=sh, b=mid: np.where(limb_frac(p, a, b) > .8, cuff_mat, mat).astype(object), 'arm' + s))
        else:
            shapes.append(Shape('upper' + s, upper_mat, lambda p, a=sh, b=el: sd_capsule(p, a, b, 6.6, 6.0), group='arm' + s))
            def cuff(p, mat, a=el, b=wr):
                mat = mat.copy(); f = limb_frac(p, a, b)
                mat[f > .78] = cuff_mat
                return mat
            shapes.append(Shape('fore' + s, fore_mat, lambda p, a=el, b=wr: sd_capsule(p, a, b, 6.0, 5.6), cuff, 'arm' + s))
        if bracer:
            b0 = el + (wr - el) * .35
            def brace(p, mat, a=b0, b=wr, rim=bracer[1]):
                f = limb_frac(p, a, b); mat = mat.copy(); mat[(f > .86) | (f < .1)] = rim; return mat
            shapes.append(Shape('bracer' + s, bracer[0], lambda p, a=b0, b=wr: sd_capsule(p, a, b, 5.4, 5.6), brace, 'arm' + s))
        slots['outfit.sleeve.' + name] = shapes
    return slots


def skirt(F, material, trim, bottom=-15.0, opening=.38, panels=0, name='skirt', flare=.3):
    """Coat skirt / tassets: a flared shell round the hips, open at the front, ending at `bottom`."""
    def sdf(p):
        q = F.local(p)
        drop = np.maximum(0, 4 - q[:, 1])
        r = 15.5 + drop * flare                      # flares out toward the hem
        rad = np.hypot(q[:, 0], (q[:, 2] + .5) * 1.12)
        shell = (rad - r) * .85
        cut_top = q[:, 1] - 7.0                      # keep below the chest (the torso covers above)
        cut_bottom = bottom - q[:, 1]
        gap = opening * np.maximum(0, 2 - q[:, 1])   # front opening widening downward
        front = np.where(q[:, 2] > 0, gap - np.abs(q[:, 0]), -9)
        return np.maximum.reduce([shell, cut_top, cut_bottom, front])
    def detail(p, mat):
        q = F.local(p); mat = mat.copy()
        mat[q[:, 1] < bottom + 1.6] = trim
        front = q[:, 2] > 0
        mat[front & (np.abs(q[:, 0]) < opening * np.maximum(0, 2 - q[:, 1]) + 1.4)] = trim
        if panels:
            ang = np.degrees(np.arctan2(q[:, 0], q[:, 2]))
            mat[np.abs(((ang + 180) % (360 / panels)) - 180 / panels) < 4] = trim
        return mat
    return [Shape(name, material, sdf, detail, name)]


def tabards(F, material, trim, bottom=-17.0, name='tabard'):
    """Flat cloth panels hanging at the front and back of the hips."""
    shapes = []
    for k, z in (('front', 12.5), ('back', -12.0)):
        top = F.chest([0, -2, z])
        center = F.chest([0, (bottom - 2) / 2, z * 1.02])
        half = [6.0, (-2 - bottom) / 2, 1.4]
        def sdf(p, c=center, h=half): return sd_box(p, c, h, F.Bc, .9)
        def detail(p, mat, c=center, h=half):
            q = (p - c) @ F.Bc; mat = mat.copy()
            mat[(q[:, 1] < -h[1] + 1.6) | (np.abs(q[:, 0]) > h[0] - 1.4)] = trim
            return mat
        shapes.append(Shape(name + k, material, sdf, detail, name + k))
    return shapes


# ---------------- outfits ----------------
def forester(F):
    tor = torso_sdf(F)
    def detail(p, mat):
        q = F.local(p); mat = mat.copy()
        front = q[:, 2] > 4
        mat[front & (np.abs(q[:, 0]) < 1.1) & (q[:, 1] > -6) & (q[:, 1] < 37)] = 'gold'
        mat[(q[:, 1] > 8.5) & (q[:, 1] < 12.5)] = 'belt'
        mat[front & (np.abs(q[:, 0]) < 2.6) & (q[:, 1] > 8) & (q[:, 1] < 13)] = 'gold'
        mat[q[:, 1] < -5.6] = 'gold'
        return mat
    slots = {'outfit.torso': [Shape('jacket', 'jacket', tor, detail, 'torso'), collar_shape(F, 'collar', 'gold')],
             'outfit.hem.front': []}
    slots.update(sleeves(F, 'jacket', 'jacket', 'gold'))
    return slots


def wayfarer(F):
    tor = torso_sdf(F, depth=.5)
    def detail(p, mat):
        q = F.local(p); mat = mat.copy()
        front = q[:, 2] > 4
        # front opening edges in gold, a little apart
        mat[front & (np.abs(np.abs(q[:, 0]) - 1.6) < .9) & (q[:, 1] > -7) & (q[:, 1] < 36)] = 'gold'
        mat[(q[:, 1] > 8.5) & (q[:, 1] < 12.2)] = 'belt'
        mat[front & (np.abs(q[:, 0]) < 2.6) & (q[:, 1] > 8) & (q[:, 1] < 12.7)] = 'gold'
        return mat
    slots = {'outfit.torso': [Shape('coat', 'navy', tor, detail, 'torso'), collar_shape(F, 'tan', 'tan', radius=6.6)]}
    slots['outfit.hem.front'] = skirt(F, 'navy', 'gold', bottom=-17, opening=.42, name='tail')
    slots.update(sleeves(F, 'navy', 'navy', 'gold'))
    return slots


def pauldrons(F, material, rim):
    shapes = []
    for s, sx in (('R', -1), ('L', 1)):
        c = F.chest([sx * 15, 34, 0])
        def detail(p, mat, c=c):
            q = F.local(p) - F.local(c[None])[0]
            mat = mat.copy(); mat[q[:, 1] < -2.6] = rim; return mat
        shapes.append(Shape('pauldron' + s, material, lambda p, c=c: sd_ellipsoid(p, c, np.array([8.2, 6.0, 9.2]), F.Bc), detail, 'pauldron' + s))
    return shapes


def leather(F):
    tor = torso_sdf(F, widen=.6, depth=.6)
    def detail(p, mat):
        q = F.local(p); mat = mat.copy()
        front = q[:, 2] > 3
        # white shirt V at the neck
        mat[front & (q[:, 1] > 30) & (np.abs(q[:, 0]) < (q[:, 1] - 30) * .9)] = 'cloth'
        # cross strap from the left shoulder to the right hip, front and back
        mat[np.abs(q[:, 0] * .8 - (q[:, 1] - 18) * .6) < 1.8] = 'darkleather'
        mat[(q[:, 1] > 8.5) & (q[:, 1] < 12.5)] = 'darkleather'
        mat[front & (np.abs(q[:, 0]) < 2.6) & (q[:, 1] > 8) & (q[:, 1] < 13)] = 'gold'
        # stitched hem
        mat[q[:, 1] < -5.4] = 'darkleather'
        return mat
    slots = {'outfit.torso': [Shape('vest', 'leather', tor, detail, 'torso'), collar_shape(F, 'cloth', 'cloth', radius=5.8)] + pauldrons(F, 'leather', 'darkleather')}
    slots['outfit.hem.front'] = skirt(F, 'leather', 'darkleather', bottom=-11, opening=.2, panels=5, name='tasset')
    slots.update(sleeves(F, 'cloth', 'cloth', 'cloth', short=True, bracer=('leather', 'darkleather')))
    return slots


def rune(F):
    tor = torso_sdf(F, widen=1.0, depth=1.0)
    gem_c = F.chest([0, 22, 13.5])
    gem2_c = F.chest([0, 6, 14.5])
    def detail(p, mat):
        q = F.local(p); mat = mat.copy()
        front = q[:, 2] > 4
        mat[front & (np.abs(q[:, 0]) < 1.2) & (q[:, 1] > 0) & (q[:, 1] < 36)] = 'gold'
        # plate edges: a gold line round the chest plate and the waist
        mat[(q[:, 1] > 9.5) & (q[:, 1] < 12)] = 'gold'
        mat[(q[:, 1] < 9.5) & (q[:, 1] > -6)] = 'blue'
        mat[(q[:, 1] < -5.4)] = 'gold'
        return mat
    gems = [Shape('gem', 'gem', lambda p: sd_ellipsoid(p, gem_c, np.array([3.4, 4.4, 2.2]), F.Bc), outline='gold', group='gem'),
            Shape('gem2', 'gem', lambda p: sd_ellipsoid(p, gem2_c, np.array([2.4, 3.0, 1.8]), F.Bc), outline='gold', group='gem2')]
    slots = {'outfit.torso': [Shape('plate', 'silver', tor, detail, 'torso'), collar_shape(F, 'blue', 'gold', radius=6.4)] + gems + pauldrons(F, 'silver', 'gold')}
    slots['outfit.hem.front'] = tabards(F, 'blue', 'gold', bottom=-16)
    slots.update(sleeves(F, 'blue', 'blue', 'blue', bracer=('silver', 'gold')))
    return slots


ASSETS = {
    'p1-eight-way-base-v1': base,
    'p1-eight-way-lower-v1': lower,
    'p1-eight-way-forester-v1': forester,
    'p1-eight-way-wayfarer-v1': wayfarer,
    'p1-b2-leatherarmor-r4': leather,
    'p1-b2-runearmor-r5': rune,
}
# Contact shadows only from parts that are present in every state using the asset.
# Never from the body inside the clothes; outfits only from trousers/boots and themselves.
OCCLUDED_BY = {
    'p1-eight-way-base-v1': ['p1-eight-way-base-v1'],
    'p1-eight-way-lower-v1': ['p1-eight-way-lower-v1'],
}
DEFAULT_OCCLUDERS = ['p1-eight-way-lower-v1']
