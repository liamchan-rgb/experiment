"""M0 交付物：用法 python3 scripts/character-pixel/build_m0.py [--height 64]
输出到 Art/Review/Character/pixel-m0/（高度不是 64 时输出到 pixel-m0/h<高度>/）：
- frames/        基础款逻辑分辨率帧（1×，RGBA）
- sheet.png      5 方向 × 待机/行走 + 朝右普攻（×4 放大）
- walk-8dir.gif  8 方向行走 + 待机，游戏速度（左侧为镜像）
- battle-scene.gif  真实大小放进战斗场景、与鹿灵并排（待机 → 普攻 → 待机），游戏速度
- swap-compare.png  同一动作的 3 发型 × 3 脸 × 2 服装 组合对比
- checks.json    验收检查（头部逐像素一致、色数、换部件隔离、尺寸）
"""
from __future__ import annotations
import argparse, itertools, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pixelchar as pc

ROOT = HERE.parents[1]
ASSETS = ROOT / 'Sources/Resources/Assets.xcassets'
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
GRASS = (74, 104, 58, 255)
DIRS5 = ['right', 'down_right', 'down', 'up_right', 'up']
DIRS8 = [('right', False), ('down_right', False), ('down', False), ('down_right', True),
         ('right', True), ('up_right', True), ('up', False), ('up_right', False)]
DIR_LABEL = {('right', False): '→', ('down_right', False): '↘', ('down', False): '↓', ('down_right', True): '↙',
             ('right', True): '←', ('up_right', True): '↖', ('up', False): '↑', ('up_right', False): '↗'}
BASE = pc.Look('tousled', 'round', 'blue_tunic')


def big(img, s):
    im = Image.fromarray(np.ascontiguousarray(img))
    return im.resize((im.width * s, im.height * s), Image.Resampling.NEAREST)


def font(n):
    return ImageFont.truetype(FONT, n)


def frame(spec, d, anim, f, look, mirror=False, weapon=None):
    return pc.render(spec, d, anim, f, look, mirror=mirror, weapon=weapon)

# ------------------------------------------------------------------ 帧与总表


def export_frames(spec, out):
    fd = out / 'frames'; fd.mkdir(parents=True, exist_ok=True)
    for d in DIRS5:
        for anim in ('idle', 'walk'):
            for f in range(4):
                Image.fromarray(frame(spec, d, anim, f, BASE)[0]).save(fd / f'{d}-{anim}-{f}.png')
    for anim in ('battle_idle', 'attack'):
        for f in range(4):
            Image.fromarray(frame(spec, 'right', anim, f, BASE)[0]).save(fd / f'right-{anim}-{f}.png')


def sheet(spec, out):
    W, H = spec.canvas; s = 4; cw = 56; x0 = (W - cw) // 2
    cols = 8; rows = len(DIRS5) + 1
    img = Image.new('RGBA', (cw * s * cols + 120, H * s * rows + 60), GRASS)
    dr = ImageDraw.Draw(img)
    dr.text((130, 10), '待机 4 帧', font=font(28), fill=(255, 240, 190)); dr.text((130 + cw * s * 4, 10), '行走 4 帧', font=font(28), fill=(255, 240, 190))
    for r, d in enumerate(DIRS5):
        dr.text((20, 60 + r * H * s + H * s // 2 - 30), DIR_LABEL[(d, False)], font=font(56), fill=(255, 240, 190))
        for c in range(8):
            anim = 'idle' if c < 4 else 'walk'
            fr = frame(spec, d, anim, c % 4, BASE)[0][:, x0:x0 + cw]
            img.alpha_composite(big(fr, s), (120 + c * cw * s, 60 + r * H * s))
    r = len(DIRS5)
    dr.text((10, 60 + r * H * s + 20), '普攻\n(→)', font=font(28), fill=(255, 240, 190))
    for c in range(4):
        fr = frame(spec, 'right', 'battle_idle', c, BASE)[0][:, x0:x0 + cw]
        img.alpha_composite(big(fr, s), (120 + c * cw * s, 60 + r * H * s))
        fr = frame(spec, 'right', 'attack', c, BASE)[0][:, x0:x0 + cw]
        img.alpha_composite(big(fr, s), (120 + (c + 4) * cw * s, 60 + r * H * s))
    img.convert('RGB').save(out / 'sheet.png')


def to_gif(frames, durations, path, colors=255):
    """全片共用一个调色板（避免逐帧调色闪烁），不抖动。"""
    probe = Image.new('RGB', (frames[0].width, frames[0].height * min(len(frames), 6)))
    step = max(1, len(frames) // 6)
    for i, f in enumerate(frames[::step][:6]):
        probe.paste(f.convert('RGB'), (0, i * frames[0].height))
    pal = probe.quantize(colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=durations, loop=0, optimize=False, disposal=1)


def walk_gif(spec, out):
    W, H = spec.canvas; s = 4; cw = 56; x0 = (W - cw) // 2
    # 一行 8 方向：上半行走，下半待机；行走 4×140ms、待机 4×200ms，取公倍时长 2240ms 让两行同时循环
    t_walk = pc.ANIMS['walk']['ms'][0]
    tick = 70
    total = 2240
    frames, durs = [], []
    lab = Image.new('RGBA', (cw * s * 8, 50), (20, 28, 20, 255))
    d0 = ImageDraw.Draw(lab)
    for i, key in enumerate(DIRS8):
        d0.text((i * cw * s + cw * s // 2 - 16, 4), DIR_LABEL[key], font=font(36), fill=(255, 240, 190))
    cache = {}
    for t in range(0, total, tick):
        im = Image.new('RGBA', (cw * s * 8, H * s * 2 + 50), GRASS)
        im.alpha_composite(lab, (0, 0))
        for i, (d, m) in enumerate(DIRS8):
            for row, anim in enumerate(('walk', 'idle')):
                ms = pc.ANIMS[anim]['ms']
                tt = t % sum(ms); f = 0
                while tt >= ms[f]:
                    tt -= ms[f]; f += 1
                key = (d, m, anim, f)
                if key not in cache:
                    cache[key] = big(frame(spec, d, anim, f, BASE, mirror=m)[0][:, x0:x0 + cw], s)
                im.alpha_composite(cache[key], (i * cw * s, 50 + row * H * s))
        frames.append(im); durs.append(tick)
    to_gif(frames, durs, out / 'walk-8dir.gif')

# ------------------------------------------------------------------ 战斗场景（真实大小，与鹿灵并排）


def asset(name):
    folder = ASSETS / f'{name}.imageset'
    fn = json.loads((folder / 'Contents.json').read_text())['images'][0]['filename']
    return Image.open(folder / fn).convert('RGBA')


def battle_scene(spec, out, look=BASE, name='battle-scene.gif'):
    # 与 scripts/review-battle-effects-demo.py / review-character-density.py 相同的舞台与鹿灵摆放
    W, H, S = 760, 697, 3
    plate = Image.new('RGBA', (W, H))
    for nm, blur in [('MeadowCampFarForest', 3), ('MeadowCampGround', 1.5), ('MeadowCampMidground', 1.5)]:
        plate.alpha_composite(asset(nm).filter(ImageFilter.GaussianBlur(blur)).resize((W, H), Image.Resampling.LANCZOS))
    fg = asset('MeadowCampForeground').resize((W * S, H * S), Image.Resampling.LANCZOS)
    enemy = asset('MeadowBattleForestWarden')
    hs, es = H * .17 / 132, H * .33 / 232
    ex, ey = W * .65 - 178.5 * es, H * .685 - 241 * es
    # 现有主角（头到脚约 134 像素）在舞台上的显示高度 → 新人物同高；逻辑像素放大倍数 = 该高度 / 人物像素高
    target = 134 * hs * S
    px = target / 64.0            # 64 像素高的人物与现有主角同高；48/72 用同一像素尺寸（人变矮/变高）
    foot = (W * .29 * S, H * .69 * S)
    base = plate.resize((W * S, H * S), Image.Resampling.LANCZOS)
    # 鹿灵阴影（与 demo 同样的投影简化为柔和椭圆）+ 鹿灵
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.ellipse([ex * S + 60 * S * es, (ey + 236 * es) * S - 18, (ex + 330 * es) * S, (ey + 236 * es) * S + 26], fill=(9, 11, 6, 110))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    base.alpha_composite(enemy.resize((round(enemy.width * es * S), round(enemy.height * es * S)), Image.Resampling.NEAREST), (round(ex * S), round(ey * S)))
    CROP = (90 * S, 235 * S, 690 * S, 505 * S)
    seq = [('battle_idle', f) for _ in range(3) for f in range(4)] + [('attack', f) for f in range(4)] + [('battle_idle', f) for _ in range(2) for f in range(4)]
    frames, durs = [], []
    Wc, Hc = spec.canvas; ax, ay = spec.anchor
    for anim, f in seq:
        img = frame(spec, 'right', anim, f, look)[0]
        im = Image.fromarray(img)
        sw, shh = round(Wc * px), round(Hc * px)
        im = im.resize((sw, shh), Image.Resampling.NEAREST)
        sc = base.copy()
        # 角色脚下柔和阴影（按逻辑像素对齐）
        s2 = Image.new('RGBA', sc.size, (0, 0, 0, 0)); d2 = ImageDraw.Draw(s2)
        pose = pc.anim_pose(anim, f)
        cx = foot[0] + pose.dx * px
        d2.ellipse([cx - 13 * px, foot[1] - 2.2 * px, cx + 13 * px, foot[1] + 2.6 * px], fill=(9, 11, 6, 120))
        sc.alpha_composite(s2.filter(ImageFilter.GaussianBlur(6)))
        sc.alpha_composite(im, (round(foot[0] - (ax + 0.5) * px), round(foot[1] - (ay + 1) * px)))
        sc.alpha_composite(fg)
        frames.append(sc.crop(CROP)); durs.append(pc.ANIMS[anim]['ms'][f])
    to_gif(frames, durs, out / name)
    frames[0].convert('RGB').save(out / name.replace('.gif', '-still.png'))
    frames[len(frames) - 10].convert('RGB').save(out / name.replace('.gif', '-strike.png'))
    return px

# ------------------------------------------------------------------ 换部件对比


def swap_compare(spec, out, direction='down_right', name='swap-compare.png'):
    W, H = spec.canvas; s = 3; cw = 50; x0 = (W - cw) // 2
    hairs, faces, outfits = list(pc.HAIRS), list(pc.FACES), list(pc.OUTFITS)
    cols = len(hairs) * len(faces); rows = len(outfits)
    img = Image.new('RGBA', (cw * s * cols + 130, (H - 6) * s * rows + 120), GRASS)
    dr = ImageDraw.Draw(img)
    for i, (h, fc) in enumerate(itertools.product(hairs, faces)):
        dr.text((130 + i * cw * s + 8, 10), pc.HAIRS[h]['name'], font=font(22), fill=(255, 240, 190))
        dr.text((130 + i * cw * s + 8, 40), pc.FACES[fc]['name'], font=font(22), fill=(220, 235, 210))
        for r, o in enumerate(outfits):
            fr = frame(spec, direction, 'idle', 0, pc.Look(h, fc, o))[0][6:, x0:x0 + cw]
            img.alpha_composite(big(fr, s), (130 + i * cw * s, 80 + r * (H - 6) * s))
    for r, o in enumerate(outfits):
        dr.text((12, 80 + r * (H - 6) * s + 90), pc.OUTFITS[o]['name'], font=font(22), fill=(255, 240, 190))
    img.convert('RGB').save(out / name)


# ------------------------------------------------------------------ 验收检查

HEADPARTS = {'head', 'hair', 'face'}


def check_head_stable(spec):
    """各帧中头/发/脸像素（扣除整体位移后）与第 0 帧逐像素相同；被手臂/武器遮挡的像素不比较。"""
    res = []
    for d, anim in [(d, a) for d in DIRS5 for a in ('idle', 'walk')] + [('right', 'battle_idle'), ('right', 'attack')]:
        ref = None; offs = []; bad = 0
        for f in range(4):
            img, lay, info = frame(spec, d, anim, f, BASE)
            dx, dy = info['head_offset']; offs.append((dx, dy))
            m = np.isin(lay.part, list(HEADPARTS))
            ys, xs = np.nonzero(m)
            px = {(y - dy, x - dx): tuple(img[y, x]) for y, x in zip(ys, xs)}
            if ref is None:
                ref = px; continue
            common = ref.keys() & px.keys()
            bad += sum(ref[k] != px[k] for k in common)
        bobs = sorted({o[1] - offs[0][1] for o in offs})
        res.append(dict(direction=d, anim=anim, head_offsets=offs, mismatched_pixels=int(bad),
                        vertical_range=int(max(o[1] for o in offs) - min(o[1] for o in offs)),
                        horizontal_range=int(max(o[0] for o in offs) - min(o[0] for o in offs))))
    return res


def check_palette(spec):
    out = {}
    allc = set()
    for h, fc, o in itertools.product(pc.HAIRS, pc.FACES, pc.OUTFITS):
        cols = set()
        for d in DIRS5:
            for anim in ('idle', 'walk'):
                for f in range(4):
                    a = frame(spec, d, anim, f, pc.Look(h, fc, o))[0]
                    cols |= {tuple(c) for c in a[a[..., 3] > 0][:, :3]}
        for anim in ('battle_idle', 'attack'):
            for f in range(4):
                a = frame(spec, 'right', anim, f, pc.Look(h, fc, o))[0]
                cols |= {tuple(c) for c in a[a[..., 3] > 0][:, :3]}
        out[f'{h}/{fc}/{o}'] = len(cols); allc |= cols
    return dict(per_combo=out, max_per_combo=max(out.values()), all_combos_total=len(allc))


def dilate(m):
    o = m.copy()
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    return o


def check_swap(spec):
    """换一个部件：变化像素必须全部落在该部件（任一版本中）覆盖的像素或其 1 像素轮廓内。"""
    cases = []
    owners = {'hair': {'hair'}, 'face': {'face'}, 'outfit': {'outfit'}}
    fails = 0; total = 0
    for slot, opts in [('hair', list(pc.HAIRS)), ('face', list(pc.FACES)), ('outfit', list(pc.OUTFITS))]:
        for a, b in itertools.combinations(opts, 2):
            for d in DIRS5:
                for anim, f in [('idle', 0), ('walk', 1)] + ([('attack', 2)] if d == 'right' else []):
                    LA = pc.Look(**{**BASE.__dict__, slot: a}); LB = pc.Look(**{**BASE.__dict__, slot: b})
                    ia, la, _ = frame(spec, d, anim, f, LA); ib, lb, _ = frame(spec, d, anim, f, LB)
                    diff = np.any(ia != ib, axis=-1)
                    allowed = dilate(np.isin(la.part, list(owners[slot])) | np.isin(lb.part, list(owners[slot])))
                    leak = diff & ~allowed
                    total += 1
                    if leak.any():
                        fails += 1
                        cases.append(dict(slot=slot, a=a, b=b, direction=d, anim=anim, frame=f, leaked_pixels=int(leak.sum())))
    return dict(comparisons=total, failed=fails, failures=cases[:20])


def check_size(spec):
    a = frame(spec, 'down', 'idle', 0, BASE)[0]; ys, xs = np.nonzero(a[..., 3])
    b = frame(spec, 'right', 'idle', 0, BASE)[0]; ys2, xs2 = np.nonzero(b[..., 3])
    return dict(height_down=int(ys.max() - ys.min() + 1), width_down=int(xs.max() - xs.min() + 1),
                height_right=int(ys2.max() - ys2.min() + 1), width_right=int(xs2.max() - xs2.min() + 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--height', type=int, default=64); ap.add_argument('--skip-checks', action='store_true')
    args = ap.parse_args()
    spec = pc.Spec(height=args.height)
    out = ROOT / 'Art/Review/Character/pixel-m0'
    if args.height != 64:
        out = out / f'h{args.height}'
    out.mkdir(parents=True, exist_ok=True)
    export_frames(spec, out)
    sheet(spec, out)
    walk_gif(spec, out)
    px = battle_scene(spec, out)
    swap_compare(spec, out)
    swap_compare(spec, out, 'right', 'swap-compare-right.png')   # 战斗朝向
    if not args.skip_checks:
        rep = dict(spec=dict(height=spec.height, canvas=spec.canvas, pitch_deg=spec.pitch_deg),
                   battle_logical_pixel_size_in_scene_px=round(px, 3),
                   size=check_size(spec), head_stable=check_head_stable(spec), palette=check_palette(spec), swap=check_swap(spec))
        (out / 'checks.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
        hs = rep['head_stable']
        print('size', rep['size'])
        print('head mismatches', sum(r['mismatched_pixels'] for r in hs), 'max vrange', max(r['vertical_range'] for r in hs if r['anim'] in ('idle', 'walk')))
        print('palette max/combo', rep['palette']['max_per_combo'], 'total', rep['palette']['all_combos_total'])
        print('swap', rep['swap']['comparisons'], 'failed', rep['swap']['failed'], rep['swap']['failures'][:3])


if __name__ == '__main__':
    main()
