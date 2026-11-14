"""
从 Momji Pixel 的「Free Prototype Character Asset Pack」（CC BY 4.0）里提取动作关键帧。

原型小人每个身体部位是一种颜色：头、胸、骨盆、两条手臂（上臂 / 前臂各一色）、两条腿（大腿 / 小腿各一色），
剑是黑色。逐帧找出各部位的像素，算出：
  头中心、颈（胸部顶端）、髋（骨盆中心）、两只手的肩 / 肘 / 手、两条腿的髋 / 膝 / 脚、剑的握点和指向。
坐标以「待机第 0 帧」的髋为原点、像素为单位，x 向前（原型朝右）、y 向上。输出 JSON，由 rig.ts 换算到 Q 版骨架。

用法：python3 -I tools/extract_mocap.py <解压后的素材包目录> <输出 json>
"""
import json, math, os, sys
from PIL import Image

SKIN = (231, 213, 179); CHEST = (207, 87, 60); PELVIS = (136, 75, 43)
ARM_NEAR = ((117, 167, 67), (70, 130, 50))    # 绿色：握剑的那只手（近侧）
ARM_FAR = ((60, 94, 139), (37, 58, 94))       # 蓝色：远侧
LEG_A = ((198, 81, 151), (162, 62, 140))      # 粉 / 紫
LEG_B = ((165, 48, 48), (117, 36, 56))        # 红 / 暗红
SWORD = (9, 10, 20)

CLIPS = {
    'attack1': 'Sword Character/Split/Sword Character Prototype-V1-Attack1.png',
    'attack2': 'Sword Character/Split/Sword Character Prototype-V1-Attack2.png',
    'attack3': 'Sword Character/Split/Sword Character Prototype-V1-Attack3.png',
    'dash': 'Sword Character/Split/Sword Character Prototype-V1-Dash-Attack.png',
    'hurt': 'Base Character/Split/Hurt-70ms.png',
    'die': 'Base Character/Split/Die-70ms.png',
    'idle': 'Base Character/Split/Prototype Character-Idle-100ms.png',
}


def groups(frame):
    px = frame.load(); g = {}
    for y in range(frame.height):
        for x in range(frame.width):
            p = px[x, y]
            if p[3]: g.setdefault(p[:3], []).append((x, y))
    return g


def mean(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else None


def far(pts, ref):
    return max(pts, key=lambda p: (p[0] - ref[0]) ** 2 + (p[1] - ref[1]) ** 2) if pts else None


def near(pts, ref):
    return min(pts, key=lambda p: (p[0] - ref[0]) ** 2 + (p[1] - ref[1]) ** 2) if pts else None


def limb(g, upper, lower, anchor):
    """根（肩 / 髋）= 上段离躯干锚点最近的像素；关节（肘 / 膝）= 两段交界的中心；末端（手 / 脚）= 下段离根最远的像素"""
    up, lo = g.get(upper, []), g.get(lower, [])
    if not up or not lo or anchor is None:
        return None
    # 两段颜色在不同的素材里会对调：离躯干锚点更近的那段才是上臂 / 大腿
    if near(lo, anchor) and near(up, anchor):
        du = min((p[0] - anchor[0]) ** 2 + (p[1] - anchor[1]) ** 2 for p in up)
        dl = min((p[0] - anchor[0]) ** 2 + (p[1] - anchor[1]) ** 2 for p in lo)
        if dl < du:
            up, lo = lo, up
    los = set(lo)
    joint = [p for p in up if any((p[0] + dx, p[1] + dy) in los for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    j = mean(joint) if joint else mean(up)
    root = near(up, anchor)
    end = far(lo, root)
    return {'root': (root[0] + 0.5, root[1] + 0.5), 'joint': (j[0] + 0.5, j[1] + 0.5), 'end': (end[0] + 0.5, end[1] + 0.5)}


def frame_pose(frame):
    g = groups(frame)
    head = mean(g.get(SKIN, []))
    chest, pelvis = g.get(CHEST, []), g.get(PELVIS, [])
    hip = mean(pelvis)
    neck = None
    if chest:
        top = min(p[1] for p in chest)
        neck = mean([p for p in chest if p[1] <= top + 1])
    arm_n, arm_f = limb(g, *ARM_NEAR, neck), limb(g, *ARM_FAR, neck)
    leg_a, leg_b = limb(g, *LEG_A, hip), limb(g, *LEG_B, hip)
    sword = None
    blades = g.get(SWORD, [])
    if blades and arm_n:
        hilt = min(blades, key=lambda p: (p[0] - arm_n['end'][0]) ** 2 + (p[1] - arm_n['end'][1]) ** 2)
        tip = far(blades, hilt)
        if math.hypot(tip[0] - hilt[0], tip[1] - hilt[1]) > 3:
            sword = {'hilt': hilt, 'tip': tip}
    white = len(g.get((235, 237, 233), []))
    return {'head': head, 'neck': neck, 'hip': hip, 'armNear': arm_n, 'armFar': arm_f, 'legA': leg_a, 'legB': leg_b, 'sword': sword, 'smear': white}


def main():
    root, out = sys.argv[1], sys.argv[2]
    data = {}
    origin = None
    for name, rel in CLIPS.items():
        im = Image.open(os.path.join(root, rel)).convert('RGBA')
        frames = [frame_pose(im.crop((i * 112, 0, i * 112 + 112, 112))) for i in range(im.width // 112)]
        data[name] = frames
        if name == 'idle':
            origin = frames[0]['hip']
    # 以待机髋点为原点，y 朝上
    ground = max(p['legA']['end'][1] for p in data['idle'] if p['legA'])
    def tr(p):
        return None if p is None else [round(p[0] - origin[0], 2), round(ground - p[1], 2)]
    def conv(v):
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        if isinstance(v, tuple) and len(v) == 2 and all(isinstance(t, (int, float)) for t in v):
            return tr(v)
        return v
    result = {'source': 'Free Prototype Character Asset Pack by Momji Pixel (CC BY 4.0)', 'units': 'pixels, x forward (facing right), y up from the ground; x relative to idle hip',
              'clips': {k: [conv(f) for f in v] for k, v in data.items()}}
    with open(out, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print({k: len(v) for k, v in data.items()})


if __name__ == '__main__':
    main()
