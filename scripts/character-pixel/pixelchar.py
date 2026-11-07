"""MeadowJourney 路线 B：参数化像素人 · 参考生成器 v0（M0 小实验）

确定性，无随机数。输入 = 部件选择 + 朝向 + 动作 + 帧；输出 = 逻辑分辨率 RGBA 帧（再由调用方整数倍最近邻放大）。

做法：骨架在“身体局部坐标”(a=右, b=上, c=前) 里摆姿势；每个部件是几个简单体积（球/椭球/胶囊）。
按固定斜俯角正交投影到逻辑像素网格，逐像素求交，按法线与左上光源量化成 3 个明度，再画 1 像素深色轮廓。
五官是固定像素印章，贴在头部投影出来的锚点上。

关键约束（M0 验收）：
- 头部（头 + 头发 + 五官）每个朝向只渲染一次，之后每帧整体按整数像素平移 → 各帧逐像素相同，只有整体起伏。
- 各部件分层合成；换一个部件只会改动该部件自身覆盖的像素（及其 1 像素轮廓）。
- 全部颜色来自固定调色板，每个组合不超过 24 色。
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
import numpy as np

# ---------------------------------------------------------------- 调色板

def hx(c: str):
    return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))

OUTLINE = hx('#2a1c1a')
SKIN = [hx('#c98667'), hx('#f0b896'), hx('#ffdcc0')]          # 暗 / 中 / 亮
WHITE = hx('#f4f1ea')                                           # 眼白，兼作钢刃最亮色
STEEL = [hx('#6b7480'), hx('#a9b4bf'), WHITE]
LEATHER = [hx('#4f2a18'), hx('#7a4526'), hx('#a8693c')]

HAIR_COLORS = {
    'brown': [hx('#5e321f'), hx('#94532a'), hx('#c47a3a')],
    'silver': [hx('#6f6a86'), hx('#aaa5bb'), hx('#e2e0ea')],
    'ink': [hx('#2f2a3d'), hx('#4a4462'), hx('#6c6690')],
}
IRIS_COLORS = {
    'blue': [hx('#22448f'), hx('#4a86d6')],
    'amber': [hx('#80450f'), hx('#d79a2c')],
    'green': [hx('#22553a'), hx('#4ea468')],
}

OUTFITS = {
    # 概念图基础款：蓝色束腰上衣、米金镶边、棕腰带、灰裤、棕靴
    'blue_tunic': dict(name='行旅蓝衣', cloth=[hx('#26407a'), hx('#3d67b0'), hx('#5f93dc')],
                       trim=[hx('#c4913c'), hx('#f2d48a')], pants=[hx('#3e3a45'), hx('#5f5b66'), hx('#8a8690')],
                       sleeve='long', hem=13.5, hem_r=8.4, boot_top=5.0, collar=True, buttons=False),
    # 待用户确认的第二套：林间绿衣（短袖到肘 + 皮护腕、长下摆、高靴）
    'green_jerkin': dict(name='林间绿衣', cloth=[hx('#2b4a2c'), hx('#467339'), hx('#6f9c4a')],
                         trim=[hx('#c4913c'), hx('#f2d48a')], pants=[hx('#4a3b33'), hx('#6b574a'), hx('#8f7865')],
                         sleeve='elbow', hem=11.0, hem_r=9.4, boot_top=8.0, collar=False, buttons=True),
}

# ---------------------------------------------------------------- 规格

@dataclass
class Spec:
    height: int = 64              # 人物逻辑像素高度（可切 48 / 64 / 72）
    pitch_deg: float = 14.0       # 斜俯角
    canvas: tuple = (80, 76)      # 逻辑画布（宽, 高）
    anchor: tuple = (40, 71)      # 脚底中心在画布中的像素位置

    @property
    def k(self):
        return self.height / 64.0

    @property
    def face_tier(self):
        return 48 if self.height <= 52 else (72 if self.height >= 70 else 64)


DIRS = {  # 朝向名 → 偏航角（0 = 面向镜头，90 = 面向屏幕右）
    'right': 90.0, 'down_right': 40.0, 'down': 0.0, 'up_right': 140.0, 'up': 180.0,
}

# ---------------------------------------------------------------- 几何工具

def _norm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def sd_sphere(p, c, r):
    return np.linalg.norm(p - c, axis=-1) - r


def sd_ellipsoid(p, c, rad):
    q = (p - c) / rad
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / rad, axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def sd_capsule(p, a, b, ra, rb, scale=(1, 1, 1)):
    """胶囊/圆锥台；scale 用来把截面压扁（例如躯干前后较薄）。返回 (距离, 沿轴参数 t)。"""
    s = np.asarray(scale, float)
    pa = (p - a) / s
    ba = (b - a) / s
    h = np.clip((pa @ ba) / max(ba @ ba, 1e-9), 0, 1)
    d = np.linalg.norm(pa - h[:, None] * ba, axis=-1) * s.min() - (ra + (rb - ra) * h)
    return d, h


@dataclass
class Prim:
    kind: str
    args: tuple
    mat: str            # 材质槽：skin / cloth / pants / leather / hair / ...
    part: str           # 部件归属：body / outfit / head / hair / face / weapon
    group: str          # 用于内部轮廓：不同 group 之间深度断开时画线
    tag: str = ''       # 材质细分规则用


def eval_prims(prims, p):
    best = np.full(len(p), 1e9)
    idx = np.full(len(p), -1)
    tpar = np.zeros(len(p))
    for i, pr in enumerate(prims):
        if pr.kind == 'sphere':
            d = sd_sphere(p, *pr.args); t = np.zeros(len(p))
        elif pr.kind == 'ellipsoid':
            d = sd_ellipsoid(p, *pr.args); t = np.zeros(len(p))
        elif pr.kind == 'capsule':
            d, t = sd_capsule(p, *pr.args)
        elif pr.kind == 'clip':         # 任意 prim 再与一个约束取交（例如平底下摆）
            inner, fn = pr.args
            d, t = eval_prims([inner], p)[0], eval_prims([inner], p)[2]
            d = np.maximum(d, fn(p))
        elif pr.kind == 'cut':          # 被半空间裁掉的球壳（头发）
            c, r, fn = pr.args
            d = np.maximum(sd_sphere(p, c, r), fn(p - c)); t = np.zeros(len(p))
        else:
            raise ValueError(pr.kind)
        m = d < best
        best = np.where(m, d, best); idx = np.where(m, i, idx); tpar = np.where(m, t, tpar)
    return best, idx, tpar

# ---------------------------------------------------------------- 投影与光栅化


class Camera:
    def __init__(self, spec: Spec, yaw_deg: float):
        self.spec = spec
        a = math.radians(spec.pitch_deg)
        self.X = np.array([1.0, 0, 0])
        self.U = np.array([0, math.cos(a), -math.sin(a)])   # 屏幕“上”
        self.D = np.array([0, math.sin(a), math.cos(a)])    # 指向镜头
        y = math.radians(yaw_deg)
        self.fwd = np.array([math.sin(y), 0, math.cos(y)])
        self.right = np.array([-math.cos(y), 0, math.sin(y)])
        self.up = np.array([0, 1.0, 0])
        W, H = spec.canvas
        ys, xs = np.mgrid[0:H, 0:W]
        self.px = xs.ravel(); self.py = ys.ravel()

    def local_to_world(self, q):
        q = np.asarray(q, float)
        return q[..., 0:1] * self.right + q[..., 1:2] * self.up + q[..., 2:3] * self.fwd

    def world_to_local(self, w):
        return np.stack([w @ self.right, w @ self.up, w @ self.fwd], axis=-1)

    def project(self, q, shift=(0, 0)):
        """局部坐标点 → 画布像素坐标（浮点）。"""
        w = self.local_to_world(q)
        ax, ay = self.spec.anchor
        return np.array([ax + w @ self.X + shift[0], ay - w @ self.U + shift[1]])

    def view_dir_local(self):
        return self.world_to_local(self.D[None])[0]


LIGHT_WORLD = _norm([-0.55, 0.75, 0.62])     # 左上前方
SHADE_T = {   # (亮阈, 暗阈)：法线·光 > 亮阈 → 亮；< 暗阈 → 暗
    'skin': (0.62, 0.05), 'hair': (0.72, 0.12), 'cloth': (0.55, 0.0), 'pants': (0.5, 0.05),
    'leather': (0.55, 0.05), 'trim': (0.35, 0.35), 'steel': (0.5, 0.0),
}


@dataclass
class Layer:
    """一层像素：材质、明度、部件归属、深度。"""
    mat: np.ndarray
    shade: np.ndarray
    part: np.ndarray
    depth: np.ndarray
    group: np.ndarray

    @staticmethod
    def empty(shape):
        return Layer(np.full(shape, '', object), np.zeros(shape, np.int8), np.full(shape, '', object),
                     np.full(shape, -1e9), np.full(shape, '', object))

    @property
    def alpha(self):
        return self.mat != ''


def raster(cam: Camera, prims, matfn, shift=(0, 0)):
    """逐像素沿视线行进求交。shift 为整数像素平移（保证同一物体平移后像素完全相同）。"""
    spec = cam.spec
    W, H = spec.canvas
    ax, ay = spec.anchor
    sx = cam.px + 0.5 - ax - shift[0]
    su = ay - (cam.py + 0.5) + shift[1]
    n = len(sx)
    o = sx[:, None] * cam.X + su[:, None] * cam.U
    dep = np.full(n, 70.0)
    alive = np.ones(n, bool)
    hit = np.zeros(n, bool)
    for _ in range(140):
        if not alive.any():
            break
        ii = np.nonzero(alive)[0]
        pw = o[ii] + dep[ii, None] * cam.D
        d, _, _ = eval_prims(prims, cam.world_to_local(pw))
        h = d < 0.02
        hit[ii[h]] = True; alive[ii[h]] = False
        dep[ii[~h]] -= np.maximum(d[~h] * 0.7, 0.05)
        gone = dep < -70
        alive &= ~gone
    lay = Layer.empty((H, W))
    hi = np.nonzero(hit)[0]
    if len(hi) == 0:
        return lay
    pw = o[hi] + dep[hi, None] * cam.D
    pl = cam.world_to_local(pw)
    d0, idx, tpar = eval_prims(prims, pl)
    e = 0.15
    grad = np.zeros_like(pl)
    for k in range(3):
        dv = np.zeros(3); dv[k] = e
        grad[:, k] = eval_prims(prims, pl + dv)[0] - eval_prims(prims, pl - dv)[0]
    nl = grad / np.maximum(np.linalg.norm(grad, axis=-1, keepdims=True), 1e-9)
    light_l = cam.world_to_local(LIGHT_WORLD[None])[0]
    lam = nl @ light_l
    yy, xx = cam.py[hi], cam.px[hi]
    for j in range(len(hi)):
        pr = prims[idx[j]]
        mat = matfn(pr, pl[j], tpar[j], nl[j])
        hi_t, lo_t = SHADE_T.get(mat.split(':')[0], (0.55, 0.05))
        s = 2 if lam[j] > hi_t else (0 if lam[j] < lo_t else 1)
        if mat.startswith('trim'):
            s = 1 if lam[j] > hi_t else 0
        lay.mat[yy[j], xx[j]] = mat
        lay.shade[yy[j], xx[j]] = s
        lay.part[yy[j], xx[j]] = pr.part if not mat.endswith('@outfit') else 'outfit'
        lay.depth[yy[j], xx[j]] = dep[hi[j]]
        lay.group[yy[j], xx[j]] = pr.group
    lay.mat = np.vectorize(lambda m: m.replace('@outfit', ''))(lay.mat).astype(object)
    return lay


def tidy(lay: Layer):
    """去掉孤立的单像素明度斑点（同材质内）。"""
    H, W = lay.mat.shape
    s = lay.shade.copy()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            m = lay.mat[y, x]
            if not m:
                continue
            nb = [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
            same = [lay.shade[q] for q in nb if lay.mat[q] == m]
            if len(same) >= 3 and all(v == same[0] for v in same) and same[0] != lay.shade[y, x]:
                s[y, x] = same[0]
    lay.shade = s
    return lay


def outline(lay: Layer, depth_gap=2.6):
    """1 像素内轮廓：剪影边界；以及同层内深度断开处（画在较近一侧）。"""
    a = lay.alpha
    H, W = a.shape
    edge = np.zeros_like(a)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb_a = np.zeros_like(a)
        nb_d = np.full(a.shape, -1e9)
        nb_g = np.full(a.shape, '', object)
        ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
        xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
        nb_a[yd, xd] = a[ys, xs]; nb_d[yd, xd] = lay.depth[ys, xs]; nb_g[yd, xd] = lay.group[ys, xs]
        edge |= a & ~nb_a
        edge |= a & nb_a & (lay.depth - nb_d > depth_gap) & (nb_g != lay.group)
    lay.mat = np.where(edge, 'outline', lay.mat).astype(object)
    return lay


def composite(layers):
    """按顺序覆盖（后者在上）。"""
    out = Layer.empty(layers[0].mat.shape)
    for L in layers:
        m = L.alpha
        out.mat = np.where(m, L.mat, out.mat).astype(object)
        out.shade = np.where(m, L.shade, out.shade)
        out.part = np.where(m, L.part, out.part).astype(object)
        out.depth = np.where(m, L.depth, out.depth)
        out.group = np.where(m, L.group, out.group).astype(object)
    return out


def shift_layer(lay: Layer, dx: int, dy: int):
    H, W = lay.mat.shape
    out = Layer.empty((H, W))
    ys = slice(max(-dy, 0), H - max(dy, 0)); yd = slice(max(dy, 0), H - max(-dy, 0))
    xs = slice(max(-dx, 0), W - max(dx, 0)); xd = slice(max(dx, 0), W - max(-dx, 0))
    for f in ('mat', 'shade', 'part', 'depth', 'group'):
        getattr(out, f)[yd, xd] = getattr(lay, f)[ys, xs]
    return out

# ---------------------------------------------------------------- 骨架与姿势


@dataclass
class Pose:
    bob: int = 0                 # 身体整体上下（像素，正 = 向下）
    head_dy: int = 0             # 头相对身体额外起伏（像素）
    dx: int = 0                  # 整体水平位移（像素）
    lean: float = 0.0            # 躯干前倾（度）
    hip: tuple = (0.0, 0.0)      # 左/右大腿前摆角（度）
    knee: tuple = (4.0, 4.0)     # 左/右膝弯（度）
    shoulder: tuple = (0.0, 0.0) # 左/右上臂前摆（度）
    abduct: tuple = (10.0, 10.0) # 左/右上臂外展（度）
    elbow: tuple = (12.0, 12.0)  # 左/右肘弯（度，向前）
    weapon: float | None = None  # 武器在屏幕上的角度（度，0 = 指向屏幕右，逆时针为正）；None = 不持武器
    lift: tuple = (0.0, 0.0)     # 左/右脚抬高（局部单位）


def skeleton(spec: Spec, pose: Pose):
    k = spec.k
    J = {}
    lean = math.radians(pose.lean)

    def rot_lean(q, pivot):
        q = np.asarray(q, float) - pivot
        b, c = q[1], q[2]
        return pivot + np.array([q[0], b * math.cos(lean) - c * math.sin(lean), b * math.sin(lean) + c * math.cos(lean)])

    pelvis = np.array([0, 19.5 * k, 0])
    J['pelvis'] = pelvis
    for side, sgn, i in (('R', 1, 1), ('L', -1, 0)):
        hip = np.array([sgn * 3.1 * k, 18.0 * k, 0])
        th = math.radians(pose.hip[i]); kn = math.radians(pose.knee[i])
        L1, L2 = 8.3 * k, 7.8 * k
        knee = hip + L1 * np.array([0, -math.cos(th), math.sin(th)])
        ank = knee + L2 * np.array([0, -math.cos(th - kn), math.sin(th - kn)])
        ank = ank + np.array([0, pose.lift[i] * k, 0])
        J['hip' + side], J['knee' + side], J['ankle' + side] = hip, knee, ank
        J['toe' + side] = ank + np.array([0, -1.2 * k, 3.0 * k])
        J['heel' + side] = ank + np.array([0, -1.2 * k, -0.6 * k])
        sh = rot_lean([sgn * 8.0 * k, 31.6 * k, 0], pelvis)
        ps = math.radians(pose.shoulder[i]); ab = math.radians(pose.abduct[i]); el = math.radians(pose.elbow[i])
        A1, A2 = 6.0 * k, 5.6 * k
        d1 = np.array([sgn * math.sin(ab), -math.cos(ps) * math.cos(ab), math.sin(ps) * math.cos(ab)])
        elb = sh + A1 * d1
        d2 = np.array([sgn * math.sin(ab) * 0.5, -math.cos(ps + el), math.sin(ps + el)])
        d2 = d2 / np.linalg.norm(d2)
        wr = elb + A2 * d2
        J['shoulder' + side], J['elbow' + side], J['wrist' + side] = sh, elb, wr
        J['hand' + side] = wr + 1.4 * k * d2
    J['waist'] = rot_lean([0, 22.0 * k, 0], pelvis)
    J['chest'] = rot_lean([0, 29.5 * k, 0], pelvis)
    J['neck'] = rot_lean([0, 34.5 * k, 0], pelvis)
    return J

# ---------------------------------------------------------------- 部件：身体与服装


def body_prims(spec: Spec, J, outfit: dict, sides=('L', 'R')):
    k = spec.k
    P = []
    hem_b = outfit['hem'] * k
    # 躯干（衣）
    P.append(Prim('capsule', (J['waist'], J['chest'], 6.3 * k, 7.3 * k, (1, 1, 0.86)), 'cloth', 'outfit', 'torso', 'torso'))
    P.append(Prim('capsule', (J['chest'] + np.array([0, 1.2 * k, 0]), J['neck'] - np.array([0, 0.8 * k, 0]), 7.2 * k, 5.2 * k, (1, 1, 0.84)), 'cloth', 'outfit', 'torso', 'torso'))
    # 下摆（向下张开的圆锥台）
    hem = np.array([0, hem_b, 0]) + (J['waist'] - np.array([0, 22.0 * k, 0])) * 0.6
    hb = float(hem[1])
    skirt = Prim('capsule', (J['waist'] + np.array([0, 0.5 * k, 0]), hem - np.array([0, 4.0 * k, 0]), 6.4 * k, outfit['hem_r'] * k, (1, 1, 0.9)), 'cloth', 'outfit', 'torso', 'skirt')
    P.append(Prim('clip', (skirt, lambda q, hb=hb: hb - q[:, 1]), 'cloth', 'outfit', 'torso', 'skirt'))
    # 脖子
    P.append(Prim('capsule', (J['neck'] - np.array([0, 1.0 * k, 0]), J['neck'] + np.array([0, 3.0 * k, 0]), 2.4 * k, 2.4 * k), 'skin', 'body', 'torso', 'neck'))
    for s in sides:
        g = 'leg' + s
        P.append(Prim('capsule', (J['hip' + s], J['knee' + s], 3.0 * k, 2.6 * k), 'pants', 'outfit', g, 'thigh'))
        P.append(Prim('capsule', (J['knee' + s], J['ankle' + s], 2.6 * k, 2.3 * k), 'pants', 'outfit', g, 'shin' + s))
        P.append(Prim('capsule', (J['heel' + s], J['toe' + s], 2.2 * k, 1.9 * k), 'leather', 'outfit', g, 'foot'))
    return P


def arm_prims(spec: Spec, J, outfit: dict, s: str):
    k = spec.k
    g = 'arm' + s
    return [
        Prim('sphere', (J['shoulder' + s], 2.9 * k), 'cloth', 'outfit', g, 'shoulder'),
        Prim('capsule', (J['shoulder' + s], J['elbow' + s], 2.75 * k, 2.45 * k), 'cloth', 'outfit', g, 'upper'),
        Prim('capsule', (J['elbow' + s], J['wrist' + s], 2.45 * k, 2.2 * k), 'cloth', 'outfit', g, 'fore'),
        Prim('sphere', (J['hand' + s], 2.05 * k), 'skin', 'body', g, 'hand'),
    ]


def make_matfn(spec: Spec, J, outfit: dict):
    k = spec.k

    def fn(pr: Prim, q, t, n):
        tag = pr.tag
        if pr.mat == 'skin':
            return 'skin'
        if tag in ('torso', 'skirt'):
            b = q[1]
            wb = J['waist'][1]
            if wb - 1.4 * k <= b <= wb + 0.9 * k:
                if abs(q[0]) < 1.3 * k and q[2] > 0:
                    return 'trim@outfit'
                return 'leather@outfit'
            if tag == 'skirt' and b < outfit['hem'] * k + 1.3 * k + (J['waist'][1] - 22 * k) * 0.6:
                return 'trim@outfit'
            if outfit['collar'] and tag == 'torso' and b > J['neck'][1] - 1.3 * k and abs(q[0]) < 5.0 * k:
                return 'trim@outfit'
            if outfit['buttons'] and tag == 'torso' and abs(q[0]) < 0.7 * k and q[2] > 0 and b > wb + 2 * k:
                rel = (b - wb) / k
                return 'trim@outfit' if (rel % 3.2) < 1.0 else 'cloth@outfit'
            if not outfit['buttons'] and tag == 'torso' and abs(q[0]) < 0.55 * k and q[2] > 0 and b > wb + 1 * k:
                return 'cloth:seam@outfit'
            return 'cloth@outfit'
        if tag == 'fore':
            if outfit['sleeve'] == 'elbow':
                if t > 0.62:
                    return 'leather@outfit'
                if t < 0.12:
                    return 'trim@outfit'
                return 'skin@outfit'
            return 'trim@outfit' if t > 0.82 else 'cloth@outfit'
        if tag.startswith('shin'):
            boot_t = 1.0 - (outfit['boot_top'] * k) / np.linalg.norm(J['knee' + tag[-1]] - J['ankle' + tag[-1]])
            return 'leather@outfit' if t > boot_t else 'pants@outfit'
        if tag == 'foot':
            return 'leather@outfit'
        return pr.mat + '@outfit' if pr.part == 'outfit' else pr.mat

    return fn

# ---------------------------------------------------------------- 部件：头、发型、脸

HEAD_R = (12.4, 11.4, 11.0)


def head_center(spec: Spec):
    return np.array([0, 48.0 * spec.k, 0.4 * spec.k])


def head_prims(spec: Spec):
    k = spec.k
    hc = head_center(spec)
    return [
        Prim('ellipsoid', (hc, np.array(HEAD_R) * k), 'skin', 'head', 'head', 'skull'),
        Prim('ellipsoid', (hc + np.array([0, -4.2, 2.6]) * k, np.array([9.6, 7.0, 8.0]) * k), 'skin', 'head', 'head', 'cheek'),
        Prim('sphere', (hc + np.array([0, -4.6, 10.9]) * k, 1.25 * k), 'skin', 'head', 'head', 'nose'),
        Prim('ellipsoid', (hc + np.array([11.6, -2.0, -0.6]) * k, np.array([1.6, 2.3, 1.4]) * k), 'skin', 'head', 'head', 'ear'),
        Prim('ellipsoid', (hc + np.array([-11.6, -2.0, -0.6]) * k, np.array([1.6, 2.3, 1.4]) * k), 'skin', 'head', 'head', 'ear'),
    ]


def _sph(q):
    """头部局部向量 → (方位角, 仰角)。方位 0 = 正前，+90 = 角色右侧。"""
    az = np.degrees(np.arctan2(q[..., 0], q[..., 2]))
    el = np.degrees(np.arctan2(q[..., 1], np.hypot(q[..., 0], q[..., 2])))
    return az, el


def _tri(x):
    """周期 1 的三角波，0..1。"""
    f = x - np.floor(x)
    return 1 - 2 * np.abs(f - 0.5)


def spikes(hc, R, k, specs, r0=2.4, droop=0.35):
    """向外、略向下的尖发束（圆锥台）。specs = (方位角, 仰角, 伸出长度)。"""
    out = []
    for ang, el, ln in specs:
        a, e = math.radians(ang), math.radians(el)
        d = np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])
        base = hc + d * (R[1] - 0.5 * k)
        tipd = _norm(d + np.array([0, -droop, 0]))
        out.append(Prim('capsule', (base, base + tipd * (ln + 2.0) * k, r0 * k, 0.35 * k), 'hair', 'hair', 'hair', 'tuft'))
    return out


def hair_prims(spec: Spec, style: str):
    """返回 (前层 prims, 后层 prims)。后层 = 会被身体挡住的部分（马尾等）。"""
    k = spec.k
    hc = head_center(spec)
    R = np.array(HEAD_R) * k

    def shell(extra, cutfn, tag='cap'):
        rr = float(max(R)) + extra * k

        def fn(q):
            return cutfn(q)
        return Prim('cut', (hc + np.array([0, 0.6 * k, -0.3 * k]), rr, fn), 'hair', 'hair', 'hair', tag)

    front, back = [], []
    if style == 'tousled':
        # 短碎发：前额参差刘海，侧边到耳上，后脑到颈
        def cut(q):
            az, el = _sph(q)
            aa = np.abs(az)
            # 发际线仰角：前 → 侧 → 后
            base = np.where(aa < 52, 7 + 15 * _tri((az + 8) / 17.0), np.where(aa < 105, 7 - 17 * (aa - 52) / 53, -10 - 22 * (aa - 105) / 75))
            return (base - el) * 0.25
        front.append(shell(1.3, cut))
        front += spikes(hc, R, k, [(-150, 40, 4.0), (165, 30, 4.2), (-120, 58, 3.6), (130, 52, 3.6), (-60, 70, 3.0),
                                    (60, 66, 3.2), (0, 74, 3.0), (-122, 22, 3.4), (122, 18, 3.4), (-180, 10, 3.6)])
    elif style == 'swept':
        # 侧分后掠：额头一侧露出，另一侧一缕盖到眉
        def cut(q):
            az, el = _sph(q)
            aa = np.abs(az)
            fr = np.where(az > -6, 24 - 0.12 * az, 3 - 0.10 * az + 9 * _tri((az + 2) / 18.0))
            base = np.where(aa < 52, fr, np.where(aa < 112, 9 - 15 * (aa - 52) / 60, -6 - 26 * (aa - 112) / 68))
            return (base - el) * 0.25
        front.append(shell(1.5, cut))
        front += spikes(hc, R, k, [(-170, 20, 4.0), (175, 8, 4.4), (-140, 10, 3.6), (145, 4, 3.6), (-125, 18, 2.6), (125, 12, 2.6)],
                        r0=2.6, droop=0.9)
        front.append(Prim('sphere', (hc + np.array([-3.0, 10.0, 6.0]) * k, 3.4 * k), 'hair', 'hair', 'hair', 'tuft'))
    elif style == 'ponytail':
        # 齐刘海 + 鬓发 + 高马尾
        def cut(q):
            az, el = _sph(q)
            aa = np.abs(az)
            fr = 7 + 3 * _tri((az + 4) / 10.0)
            base = np.where(aa < 50, fr, np.where(aa < 82, -38, np.where(aa < 112, 2 - 8 * (aa - 82) / 30, -6 - 30 * (aa - 112) / 68)))
            return (base - el) * 0.25
        front.append(shell(1.3, cut))
        tie = hc + np.array([0, 6.5, -11.0]) * k
        front.append(Prim('sphere', (tie, 2.6 * k), 'hair', 'hair', 'hair', 'tie'))
        back.append(Prim('capsule', (tie, tie + np.array([0, -8.0, -4.0]) * k, 3.2 * k, 2.6 * k), 'hair', 'hair', 'hairback', 'tail'))
        back.append(Prim('capsule', (tie + np.array([0, -8.0, -4.0]) * k, tie + np.array([0, -17.0, -3.0]) * k, 2.6 * k, 1.2 * k), 'hair', 'hair', 'hairback', 'tail'))
    else:
        raise ValueError(style)
    return front, back


HAIRS = {
    'tousled': dict(name='短碎发', color='brown'),
    'swept': dict(name='侧分后掠', color='silver'),
    'ponytail': dict(name='高马尾', color='ink'),
}

# 五官印章：O=轮廓色 W=眼白 I=虹膜暗 i=虹膜亮 H=高光 S=肤暗 .=不画
FACES = {
    # 图样画的是“屏幕左侧那只眼”（外眼角在左）；另一只自动镜像
    'round': dict(name='圆眼', iris='blue', eye=['OOO', 'WHI', 'WIi', '.ii'], eye_s=['OO', 'HI', 'Ii', 'i.'],
                  brow=['SSSS'], brow_dy=-2, mouth=['OO'], mouth_dy=4),
    'sharp': dict(name='锐眼', iris='amber', eye=['OOO', 'WHI', '.Ii'], eye_s=['OO', 'HI', 'Ii'],
                  brow=['OO..', '..OO'], brow_dy=-2, mouth=['OOO'], mouth_dy=4),
    'soft': dict(name='柔眼', iris='green', eye=['OOOO', '.WHI', '.WIi', '..ii'], eye_s=['OOO', '.HI', '.Ii', '.i.'],
                 brow=['.SSS'], brow_dy=-3, mouth=['.O'], mouth_dy=4),
}


def face_anchor(cam: Camera, spec: Spec, lateral: float, up: float):
    """头部表面上一点（左右偏、上下偏，单位：局部像素）的投影坐标、法线朝向镜头程度。"""
    k = spec.k
    hc = head_center(spec)
    R = np.array(HEAD_R) * k
    x, y = lateral * k, up * k
    z = R[2] * math.sqrt(max(0.0, 1 - (x / R[0]) ** 2 - (y / R[1]) ** 2)) + 0.4 * k
    q = hc + np.array([x, y, z - 3.4 * k])     # 眼口略内收，侧面时离面部前缘 2～3 像素
    p = cam.project(q)
    nrm = _norm([x / R[0] ** 2, y / R[1] ** 2, (z - 0.4 * k) / R[2] ** 2])
    facing = nrm @ cam.view_dir_local()
    return p, facing, q


def stamp_face(lay: Layer, cam: Camera, spec: Spec, face: str):
    f = FACES[face]
    eyes = []
    for side in (1, -1):   # 角色右眼(a>0)、左眼
        p, facing, _ = face_anchor(cam, spec, 5.0 * side, -2.4)
        if facing < 0.18:
            continue
        eyes.append((side, p, facing))
    for side, p, facing in eyes:
        pat = f['eye'] if facing > 0.62 else f['eye_s']
        # 图样按“屏幕左侧那只眼”画；屏幕右侧的眼镜像
        on_screen_left = p[0] < cam.project(head_center(spec))[0]
        if not on_screen_left:
            pat = [r[::-1] for r in pat]
        w = len(pat[0])
        x0 = int(round(p[0] - w / 2)); y0 = int(round(p[1] - 2))
        _put(lay, pat, x0, y0, face)
        bpat = f['brow'] if facing > 0.62 else [r[:3] for r in f['brow']]
        if not on_screen_left:
            bpat = [r[::-1] for r in bpat]
        bw = len(bpat[0])
        bx = x0 + (w - bw) // 2 + (0 if on_screen_left else (w - bw) - (w - bw) // 2 * 2)
        _put(lay, bpat, bx, y0 + f['brow_dy'] - len(bpat) + 1, face)
    if eyes:
        p, facing, _ = face_anchor(cam, spec, 0.0, -7.6)
        if facing > 0.1:
            pat = f['mouth']
            w = len(pat[0])
            if facing < 0.55:
                pat = [r[:2] for r in pat]; w = 2
            # 侧面时嘴靠近面部前缘
            _put(lay, pat, int(round(p[0] - w / 2)), int(round(p[1])), face)
    return lay


def _put(lay: Layer, pat, x0, y0, face):
    H, W = lay.mat.shape
    for j, row in enumerate(pat):
        for i, ch in enumerate(row):
            y, x = y0 + j, x0 + i
            if ch == '.' or not (0 <= y < H and 0 <= x < W):
                continue
            if lay.mat[y, x] != 'skin':      # 只画在可见皮肤上（被刘海盖住处不画）
                continue
            mat, sh = {'O': ('outline', 0), 'W': ('white', 2), 'I': ('iris', 0), 'i': ('iris', 1), 'H': ('white', 2), 'S': ('skin', 0)}[ch]
            lay.mat[y, x] = 'f_' + mat
            lay.shade[y, x] = sh
            lay.part[y, x] = 'face'

# ---------------------------------------------------------------- 武器（屏幕空间像素画）


def draw_sword(lay: Layer, hand_px, angle_deg, k=1.0, depth=50.0):
    H, W = lay.mat.shape
    a = math.radians(angle_deg)
    d = np.array([math.cos(a), -math.sin(a)])
    nrm = np.array([-d[1], d[0]])
    hx0, hy0 = hand_px
    pts = []

    def put(x, y, mat, sh):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < W and 0 <= y < H:
            lay.mat[y, x] = mat; lay.shade[y, x] = sh; lay.part[y, x] = 'weapon'
            lay.depth[y, x] = depth; lay.group[y, x] = 'weapon'

    L = int(round(19 * k))
    # 刀身 2 像素宽 + 轮廓
    for i in range(-int(round(4 * k)), L + 1):
        c = np.array([hx0, hy0]) + d * i
        for w, mat, sh in ((-1.5, 'outline', 0), (-0.5, 'steel', 2), (0.5, 'steel', 1), (1.5, 'outline', 0)):
            if i < 2:
                continue
            put(*(c + nrm * w), mat, sh)
    tip = np.array([hx0, hy0]) + d * (L + 1)
    put(*tip, 'outline', 0)
    # 护手
    for w in range(-3, 4):
        g = np.array([hx0, hy0]) + d * 1.5 + nrm * w * 0.9
        put(*g, 'trim', 1 if w < 0 else 0)
    # 剑柄
    for i in range(-3, 1):
        c = np.array([hx0, hy0]) + d * i
        put(*c, 'leather', 1)
    put(*(np.array([hx0, hy0]) + d * -4), 'trim', 1)

# ---------------------------------------------------------------- 动作


def anim_pose(anim: str, frame: int) -> Pose:
    if anim == 'idle':
        # 4 帧呼吸：第 2、3 帧身体下沉 1 像素、手臂微收
        down = frame in (1, 2)
        return Pose(bob=1 if down else 0, hip=(0, 0), knee=(5, 5), shoulder=(-4, -4),
                    abduct=(12, 12) if not down else (10, 10), elbow=(14, 14) if not down else (18, 18))
    if anim == 'walk':
        # 4 帧：接触 / 经过 / 接触(反) / 经过(反)
        swing = [(26, -22), (4, -2), (-22, 26), (-2, 4)][frame]
        knee = [(4, 10), (6, 42), (10, 4), (42, 6)][frame]
        lift = [(0, 0), (0, 2.0), (0, 0), (2.0, 0)][frame]
        arm = [(-22, 24), (-4, 6), (24, -22), (6, -4)][frame]
        return Pose(bob=[1, 0, 1, 0][frame], hip=(swing[0], swing[1]), knee=knee, lift=lift,
                    shoulder=arm, abduct=(8, 8), elbow=(16, 16))
    if anim == 'battle_idle':
        down = frame in (1, 2)
        return Pose(bob=1 if down else 0, hip=(12, -14), knee=(14, 8), shoulder=(-14, 38), abduct=(8, 14),
                    elbow=(20, 46 if not down else 50), weapon=52 if not down else 50, lean=4)
    if anim == 'attack':
        P = [
            Pose(bob=0, dx=-1, lean=-6, hip=(14, -18), knee=(16, 8), shoulder=(-26, 168), abduct=(6, 16), elbow=(14, 26), weapon=150),
            Pose(bob=1, dx=3, lean=8, hip=(24, -22), knee=(22, 6), shoulder=(-18, 100), abduct=(6, 12), elbow=(16, 6), weapon=40),
            Pose(bob=2, dx=6, lean=14, hip=(32, -26), knee=(40, 4), shoulder=(-30, 62), abduct=(6, 10), elbow=(14, 0), weapon=-28),
            Pose(bob=1, dx=3, lean=8, hip=(20, -18), knee=(22, 8), shoulder=(-20, 44), abduct=(8, 12), elbow=(18, 30), weapon=20),
        ]
        return P[frame]
    raise ValueError(anim)


ANIMS = {
    'idle': dict(frames=4, ms=[220, 180, 220, 180]),
    'walk': dict(frames=4, ms=[140, 140, 140, 140]),
    'battle_idle': dict(frames=4, ms=[220, 180, 220, 180]),
    'attack': dict(frames=4, ms=[140, 70, 220, 200]),
}

# ---------------------------------------------------------------- 装配


@dataclass
class Look:
    hair: str = 'tousled'
    face: str = 'round'
    outfit: str = 'blue_tunic'


_HEAD_CACHE = {}


def clean_strands(lay: Layer):
    """发束分缝只保留纵向连续 ≥2 像素的线，去掉点状噪点。"""
    m = lay.mat == 'hair:dark'
    up = np.zeros_like(m); dn = np.zeros_like(m)
    up[1:] = m[:-1]; dn[:-1] = m[1:]
    dl = np.zeros_like(m); dr = np.zeros_like(m)
    dl[1:, 1:] = m[:-1, :-1]; dr[1:, :-1] = m[:-1, 1:]
    dl2 = np.zeros_like(m); dr2 = np.zeros_like(m)
    dl2[:-1, 1:] = m[1:, :-1]; dr2[:-1, :-1] = m[1:, 1:]
    keep = m & (up | dn | dl | dr | dl2 | dr2)
    lay.mat = np.where(m & ~keep, 'hair', lay.mat).astype(object)
    return lay


def hair_matfn(spec: Spec, style: str):
    """头发：按发束方向画暗色分缝（发束从发旋向外，略带旋转）。"""
    hc = head_center(spec) + np.array([0, 0.6 * spec.k, -0.3 * spec.k])
    width = {'tousled': 21.0, 'swept': 17.0, 'ponytail': 15.0}[style]
    swirl = {'tousled': 0.35, 'swept': -0.9, 'ponytail': 0.0}[style]

    def fn(pr, q, t, n):
        if pr.mat != 'hair':
            return pr.mat
        if pr.tag in ('tuft', 'tie'):
            return 'hair'
        az, el = _sph(np.asarray(q) - hc)
        if pr.tag == 'tail':
            return 'hair:dark' if (t * 6.0) % 1.0 < 0.18 else 'hair'
        if el > 55:
            return 'hair'
        f = ((az + swirl * el) / width) % 1.0
        return 'hair:dark' if f < 0.2 else 'hair'
    return fn


def head_layers(spec: Spec, direction: str, look: Look):
    """(前层, 后层)：每个朝向渲染一次并缓存，供所有帧整体平移使用。"""
    key = (spec.height, direction, look.hair, look.face)
    if key in _HEAD_CACHE:
        return _HEAD_CACHE[key]
    cam = Camera(spec, DIRS[direction])
    hp = head_prims(spec)
    hf, hb = hair_prims(spec, look.hair)
    fn = hair_matfn(spec, look.hair)
    head = raster(cam, hp + hf, fn)
    tidy(head)
    clean_strands(head)
    stamp_face(head, cam, spec, look.face)
    outline(head)
    # 刘海与额头之间的分界只按深度；脸部印章不参与
    back = raster(cam, hb, fn) if hb else Layer.empty(head.mat.shape)
    if hb:
        tidy(back); outline(back)
    _HEAD_CACHE[key] = (head, back)
    return head, back


def neck_offset(J, spec):
    """头随脖子整体平移的整数像素（只取整数，保证头部像素不变）。"""
    return J['neck'] - np.array([0, 34.5 * spec.k, 0])


def build_frame(spec: Spec, direction: str, anim: str, frame: int, look: Look, weapon: bool | None = None):
    pose = anim_pose(anim, frame)
    cam = Camera(spec, DIRS[direction])
    outfit = OUTFITS[look.outfit]
    J = skeleton(spec, pose)
    matfn = make_matfn(spec, J, outfit)
    shift = (pose.dx, pose.bob)
    # 远近：角色右侧(a>0) 朝镜头的程度
    near, far = ('R', 'L') if (cam.right @ cam.D) >= 0 else ('L', 'R')
    face_cam = DIRS[direction] <= 90
    body = raster(cam, body_prims(spec, J, outfit), matfn, shift)
    arm_far = raster(cam, arm_prims(spec, J, outfit, far), matfn, shift)
    arm_near = raster(cam, arm_prims(spec, J, outfit, near), matfn, shift)
    for L in (body, arm_far, arm_near):
        tidy(L); outline(L)
    head, hair_back = head_layers(spec, direction, look)
    off = neck_offset(J, spec)
    hp = cam.project(head_center(spec) + off) - cam.project(head_center(spec))
    hdx, hdy = int(round(hp[0])) + pose.dx, int(round(hp[1])) + pose.bob + pose.head_dy
    head_s = shift_layer(head, hdx, hdy)
    back_s = shift_layer(hair_back, hdx, hdy)
    layers = []
    front_view = DIRS[direction] < 100
    if front_view:
        layers += [back_s, arm_far, body, head_s, arm_near]
    else:
        layers += [arm_far, body, arm_near, head_s, back_s]
    use_weapon = pose.weapon is not None if weapon is None else weapon
    if use_weapon and pose.weapon is not None:
        wl = Layer.empty(body.mat.shape)
        hand = cam.project(J['hand' + 'R'], shift)
        draw_sword(wl, (hand[0], hand[1]), pose.weapon, spec.k)
        # 握剑手在剑柄之上：重新盖一次手
        hand_layer = raster(cam, [arm_prims(spec, J, outfit, 'R')[-1]], matfn, shift)
        tidy(hand_layer); outline(hand_layer)
        layers += [wl, hand_layer] if near == 'R' else [wl]
        if near != 'R':
            layers = [wl] + layers
    out = composite(layers)
    return out, dict(head_offset=(hdx, hdy), pose=pose)


def palette_for(look: Look):
    o = OUTFITS[look.outfit]
    hair = HAIR_COLORS[HAIRS[look.hair]['color']]
    iris = IRIS_COLORS[FACES[look.face]['iris']]
    return {
        'outline': [OUTLINE] * 3, 'skin': SKIN, 'f_skin': SKIN, 'hair': hair, 'cloth': o['cloth'], 'cloth:seam': [o['cloth'][0]] * 3,
        'pants': o['pants'], 'leather': LEATHER, 'trim': [o['trim'][0], o['trim'][1], o['trim'][1]], 'steel': STEEL,
        'hair:dark': [hair[0], hair[0], hair[1]], 'f_outline': [OUTLINE] * 3, 'f_white': [WHITE] * 3, 'f_iris': [iris[0], iris[1], iris[1]], 'white': [WHITE] * 3,
    }


def to_rgba(lay: Layer, look: Look):
    pal = palette_for(look)
    H, W = lay.mat.shape
    img = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        for x in range(W):
            m = lay.mat[y, x]
            if not m:
                continue
            c = pal[m][int(lay.shade[y, x])]
            img[y, x, :3] = c; img[y, x, 3] = 255
    return img


def render(spec: Spec, direction: str, anim: str, frame: int, look: Look, mirror=False, weapon=None):
    lay, info = build_frame(spec, direction, anim, frame, look, weapon)
    img = to_rgba(lay, look)
    if mirror:
        img = img[:, ::-1].copy()
    return img, lay, info
