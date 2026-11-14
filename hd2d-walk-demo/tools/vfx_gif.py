"""
技能特效预览的合成（输出 MP4，带绘制背景的 GIF 太大）：背景（营地宽景）+ 压暗 + 舞台（人物和特效）+ 游戏的镜头（推近、摇镜、震屏、倾斜），放大成 GIF。

用法：python3 tools/vfx_gif.py <vfx-preview 输出目录> <营地素材目录> [放大倍数] [场景 id,...]
营地素材目录里要有 MeadowCampWideFarForest / Ground / Midground 三张（桌游仓库 Assets.xcassets 里的）。
另外按 GROUPS 输出几张拼图（skills / shields / support / hits / monster-hits / deaths）。
"""
import glob, json, math, os, subprocess, sys
from PIL import Image, ImageDraw

src, assets = sys.argv[1], sys.argv[2]
Z = int(sys.argv[3]) if len(sys.argv) > 3 else 3
only = sys.argv[4].split(',') if len(sys.argv) > 4 else None


def backdrop(w, h):
    """营地宽景：高 1201 对应舞台 600，取中间 1000 宽，再缩到舞台像素"""
    layers = []
    for n in ('MeadowCampWideFarForest', 'MeadowCampWideGround', 'MeadowCampWideMidground'):
        f = glob.glob(os.path.join(assets, n + '.imageset', '*.png'))
        if f:
            layers.append(Image.open(f[0]).convert('RGBA'))
    base = Image.new('RGBA', layers[0].size, (60, 90, 50, 255))
    for l in layers:
        base.alpha_composite(l)
    k = 600 / base.height
    full = base.resize((round(base.width * k), 600), Image.LANCZOS)
    x0 = (full.width - 1000) // 2
    crop = full.crop((x0, 0, x0 + 1000, 600))
    return crop.resize((w, h), Image.BOX)


def render(sid):
    meta = json.load(open(os.path.join(src, sid + '.json')))
    w, h, n = meta['w'], meta['h'], meta['n']
    raw = open(os.path.join(src, sid + '.rgba'), 'rb').read()
    bg = backdrop(w, h)
    frames = []
    for i, m in enumerate(meta['frames']):
        stage = Image.frombytes('RGBA', (w, h), raw[i * w * h * 4:(i + 1) * w * h * 4])
        # 压暗背景（带一点技能的色调）
        dim, tint = m['dim'], m['tint']
        b = bg.copy()
        if dim > 0.001:
            r, g, bb, a = b.split()
            r = r.point(lambda v: v * (1 - dim) * (1 - dim * (1 - tint[0])))
            g = g.point(lambda v: v * (1 - dim) * (1 - dim * (1 - tint[1])))
            bb = bb.point(lambda v: v * (1 - dim) * (1 - dim * (1 - tint[2])))
            b = Image.merge('RGBA', (r, g, bb, a))
        b.alpha_composite(stage)
        # 镜头：画面中心往焦点偏 w，推近 zoom，再加上偏移和倾斜（世界跟着镜头动）
        cx = w / 2 + (m['fx'] - w / 2) * m['w']
        cy = h / 2 + (m['fy'] - h / 2) * m['w']
        s = Z * (1 + m['zoom'])
        # 推近时视野不跑出舞台（游戏的宽景比舞台宽，这里只有舞台这么大，所以夹住）
        hw, hh = w / 2 / (1 + m['zoom']), h / 2 / (1 + m['zoom'])
        cx = min(w - hw, max(hw, cx)); cy = min(h - hh, max(hh, cy))
        rot = m['rot']
        ca, sa = math.cos(-rot), math.sin(-rot)
        W, H = w * Z, h * Z
        # 输出像素 (u, v) → 舞台像素
        a = ca / s; bq = -sa / s; d = sa / s; e = ca / s
        c0 = cx - m['dx'] - (a * W / 2 + bq * H / 2)
        f0 = cy - m['dy'] - (d * W / 2 + e * H / 2)
        out = b.transform((W, H), Image.AFFINE, (a, bq, c0, d, e, f0), resample=Image.NEAREST, fillcolor=(30, 40, 30, 255))
        frames.append(out.convert('RGB'))
    return meta, frames


def save_gif(path, frames, fps, loops=3):
    """实际写成 MP4（H.264）：同名 .mp4，循环 loops 遍，手机上能直接播"""
    path = os.path.splitext(path)[0] + '.mp4'
    w, h = frames[0].size
    w2, h2 = w // 2 * 2, h // 2 * 2
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w2}x{h2}', '-r', str(fps), '-i', '-',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium', '-movflags', '+faststart', path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for _ in range(loops):
        for f in frames:
            proc.stdin.write(f.crop((0, 0, w2, h2)).tobytes())
    proc.stdin.close()
    proc.wait()


ids = [os.path.basename(p)[:-5] for p in sorted(glob.glob(os.path.join(src, '*.json')))]
if only:
    ids = [i for i in ids if i in only]
rendered = {}
for sid in ids:
    meta, frames = render(sid)
    rendered[sid] = (meta, frames)
    save_gif(os.path.join(src, sid + '.gif'), frames, meta['fps'])
    print(sid, len(frames))

GROUPS = {
    'skills': ['runeSlash', 'dragonFlame', 'starlightPulse', 'battleRune', 'dragonOrder', 'rally', 'sweep', 'natural20'],
    'shields': ['runeWard', 'dragonScaleWard', 'dragonSoulWard', 'shieldDome', 'shieldShell', 'shieldShellHit', 'hitWard', 'shieldBreak'],
    'support': ['healMicro', 'healStandard', 'healStrong', 'buffAura', 'playerDown', 'downAura', 'revive'],
    'hits': ['hitBlade', 'hitGreat', 'hitBow', 'hitStaff', 'hitAmbush', 'projBow', 'projStaff'],
    'monster-hits': ['hitClaw', 'hitSlime', 'hitWolf', 'hitArrowM', 'hitStone', 'hitTroll', 'hitDragon', 'projArcher', 'projDragon'],
    'deaths': ['deathSlime', 'deathWolf', 'deathGoblin', 'deathStone', 'deathTroll', 'deathDragon', 'deathBurst'],
}


def mosaic(name, group, cols, scale):
    group = [g for g in group if g in rendered]
    if not group:
        return
    fps = rendered[group[0]][0]['fps']
    n = max(len(rendered[g][1]) for g in group) + 6
    cw, ch = rendered[group[0]][1][0].width // Z * scale, rendered[group[0]][1][0].height // Z * scale
    rows = math.ceil(len(group) / cols)
    out = []
    for i in range(n):
        canvas = Image.new('RGB', (cols * cw, rows * ch), (20, 20, 24))
        d = ImageDraw.Draw(canvas)
        for k, g in enumerate(group):
            frames = rendered[g][1]
            f = frames[min(i, len(frames) - 1)].resize((cw, ch), Image.NEAREST)
            canvas.paste(f, ((k % cols) * cw, (k // cols) * ch))
            d.rectangle(((k % cols) * cw, (k // cols) * ch, (k % cols) * cw + cw - 1, (k // cols) * ch + ch - 1), outline=(20, 20, 24), width=2)
        out.append(canvas)
    save_gif(os.path.join(src, name), out, fps)
    print(name, len(out))


for name, group in GROUPS.items():
    mosaic(name + '.gif', group, 2, 2)
