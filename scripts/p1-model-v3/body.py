"""Forester body + clothes on a posable skeleton (local frame: x = character's left, y up, z forward)."""
import math
import numpy as np
from model import Shape, sd_capsule, sd_ellipsoid, sd_cylinder, smin

FACING = {'down': (0, 1), 'up': (0, -1), 'right': (1, 0), 'left': (-1, 0),
          'down-right': (.7071, .7071), 'down-left': (-.7071, .7071),
          'up-right': (.7071, -.7071), 'up-left': (-.7071, -.7071)}

# proportions (canvas px), matched to the existing down/side idle art
HIP_Y, HIP_X = 38.0, 9.0
THIGH, SHIN, ANKLE_Y = 13.0, 15.0, 9.5
SHOULDER_Y, SHOULDER_X = 74.0, 15.5
UPPER_ARM, FOREARM = 12.0, 10.5
NECK_Y = 82.0

def rot_x(a):  # pitch: +a turns +y toward +z
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rot_y(a):  # yaw: +a turns +z toward +x
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def two_bone(hip, target, l1, l2):
    """Knee bends toward +z (forward). Works in the hip's y-z plane."""
    d = target - hip
    dist = min(np.linalg.norm(d), l1 + l2 - 1e-3)
    d = d / np.linalg.norm(d) * dist
    a = math.acos(np.clip((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1, 1))
    axis = np.array([1.0, 0, 0])   # rotate within y-z plane about the x axis
    # rotate direction toward +z by a (knee forward)
    u = d / dist
    cand = [u * math.cos(a) + np.cross(axis, u) * math.sin(a) * sgn for sgn in (1, -1)]
    k = max(cand, key=lambda v: v[2])
    knee = hip + k * l1
    return knee, hip + d

def skeleton(pose):
    """pose: dict(bob, lean, twist, legs={'R':(u, lift, foot_pitch)}, arms={'R':(swing, bend)})."""
    J = {}
    pelvis = np.array([0, HIP_Y - pose['bob'], 0.0])
    J['pelvis'] = pelvis
    chest_rot = rot_y(pose.get('twist', 0)) @ rot_x(pose.get('lean', 0))
    J['chest_rot'] = chest_rot
    for side, sx in (('R', -1), ('L', 1)):
        hip = pelvis + rot_y(-pose.get('twist', 0) * .5) @ np.array([sx * HIP_X, 0, 0])
        u, lift, pitch = pose['legs'][side]
        target = np.array([hip[0] * .95, ANKLE_Y + lift, u])
        knee, ankle = two_bone(hip, target, THIGH, SHIN)
        J['hip' + side], J['knee' + side], J['ankle' + side], J['foot' + side] = hip, knee, ankle, pitch
        sh = pelvis + chest_rot @ np.array([sx * SHOULDER_X, SHOULDER_Y - HIP_Y, 0])
        swing, bend = pose['arms'][side]
        down = rot_x(-swing) @ np.array([sx * .32, -1, 0]); down /= np.linalg.norm(down)
        elbow = sh + down * UPPER_ARM
        fore = rot_x(-(swing + bend)) @ np.array([sx * .1, -1, 0]); fore /= np.linalg.norm(fore)
        wrist = elbow + fore * FOREARM
        J['shoulder' + side], J['elbow' + side], J['wrist' + side] = sh, elbow, wrist
    J['neck'] = pelvis + chest_rot @ np.array([0, NECK_Y - HIP_Y, 0])
    return J

def shapes(J, facing):
    """Body + forester clothes, transformed to world by the facing."""
    fx, fz = FACING[facing]
    # world = x_l * left + y + z_l * forward ; left = (fz, 0, -fx)
    W = np.array([[fz, 0, fx], [0, 1, 0], [-fx, 0, fz]])
    w = lambda v: W @ v
    C = J['chest_rot']
    pel = w(J['pelvis'])
    out = []
    # ---- torso (jacket) ----
    chest_c = w(J['pelvis'] + C @ np.array([0, 20, 0]))
    shoulder_c = w(J['pelvis'] + C @ np.array([0, 32, 0]))
    hem_c = w(J['pelvis'] + C @ np.array([0, 2, .5]))
    Bc = W @ C                                  # local axes of the chest in world
    def jacket(p):
        a = sd_ellipsoid(p, chest_c, np.array([16, 16, 12]), Bc)
        b = sd_ellipsoid(p, shoulder_c, np.array([17, 7, 11]), Bc)
        c = sd_ellipsoid(p, hem_c, np.array([17, 10, 13]), Bc)
        return smin(smin(a, b, 4), c, 4)
    def jacket_detail(p, mat):
        q = (p - pel) @ Bc                      # chest-local coordinates
        mat = mat.copy()
        front = q[:, 2] > 4
        mat[front & (np.abs(q[:, 0]) < 1.1) & (q[:, 1] > -6) & (q[:, 1] < 37)] = 'gold'     # front placket
        mat[(q[:, 1] > 8.5) & (q[:, 1] < 12.5)] = 'belt'                                     # belt
        mat[front & (np.abs(q[:, 0]) < 2.6) & (q[:, 1] > 8) & (q[:, 1] < 13)] = 'gold'   # buckle
        mat[(q[:, 1] < -5.6)] = 'gold'                                                      # hem band
        return mat
    out.append(Shape('jacket', 'jacket', jacket, jacket_detail, 'torso'))
    neck = w(J['neck'])
    up = W @ C @ np.array([0, 1.0, 0])
    collar_base = neck - up * 6.5
    def collar(p): return sd_cylinder(p, collar_base, collar_base + up * 4.2, 6.2, 1.2)
    def collar_detail(p, mat):
        h = (p - collar_base) @ up
        radial = np.linalg.norm((p - collar_base) - h[:, None] * up, axis=1)
        mat = mat.copy(); mat[(h > 3.2) & (radial > 4.6)] = 'gold'; return mat
    out.append(Shape('collar', 'collar', collar, collar_detail, 'torso'))
    # ---- legs ----
    for side in 'RL':
        hip, knee, ankle = w(J['hip' + side]), w(J['knee' + side]), w(J['ankle' + side])
        out.append(Shape('thigh' + side, 'pants', lambda p, a=hip, b=knee: sd_capsule(p, a, b, 7.6, 7.0), group='leg' + side))
        out.append(Shape('shin' + side, 'pants', lambda p, a=knee, b=ankle: sd_capsule(p, a, b, 6.8, 6.2), group='leg' + side))
        pitch = J['foot' + side]
        F = W @ rot_x(pitch)                      # foot local axes (x left, y up, z toes)
        shaft_top = ankle + (knee - ankle) / np.linalg.norm(knee - ankle) * 6
        foot_c = ankle + F @ np.array([0, -4.4, 4.2])
        sole_y = (F @ np.array([0, -9.0, 0]))     # sole plane offset from ankle
        def boot(p, a=ankle, t=shaft_top, c=foot_c, F=F, s=sole_y):
            shaft = sd_capsule(p, a, t, 6.6, 7.0)
            toe = sd_ellipsoid(p, c, np.array([6.8, 5.4, 10.5]), F)
            body = smin(shaft, toe, 3)
            n = F @ np.array([0, -1.0, 0])
            plane = (p - (a + s)) @ n               # >0 below the sole
            return np.maximum(body, plane)
        def boot_detail(p, mat, a=ankle, F=F, t=shaft_top):
            q = (p - a) @ F
            mat = mat.copy()
            mat[q[:, 1] < -7.6] = 'sole'
            top = ((p - a) @ ((t - a) / np.linalg.norm(t - a)))
            mat[top > 4.4] = 'cuff'
            return mat
        out.append(Shape('boot' + side, 'boot', boot, boot_detail, 'foot' + side))
    # ---- arms (sleeves, cuffs, hands) ----
    for side in 'RL':
        sh, el, wr = w(J['shoulder' + side]), w(J['elbow' + side]), w(J['wrist' + side])
        out.append(Shape('upper' + side, 'jacket', lambda p, a=sh, b=el: sd_capsule(p, a, b, 6.6, 6.0), group='arm' + side))
        def fore(p, a=el, b=wr): return sd_capsule(p, a, b, 6.0, 5.6)
        def cuff(p, mat, a=el, b=wr):
            ba = b - a; h = ((p - a) @ ba) / (ba @ ba)
            mat = mat.copy(); mat[h > .78] = 'gold'; return mat
        out.append(Shape('fore' + side, 'jacket', fore, cuff, 'arm' + side))
        hand_c = wr + (wr - el) / np.linalg.norm(wr - el) * 3.4
        out.append(Shape('hand' + side, 'skin', lambda p, c=hand_c: sd_ellipsoid(p, c, np.array([5.0, 5.3, 5.0])), group='hand' + side))
    return out
