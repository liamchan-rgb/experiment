"""
3D 场景 + 像素人物 / 技能特效的合成：
  背景 = 3D 场景逐帧截图（scenes3d，renderAt(t, hit)，魔像在命中时白闪、后仰）；
  舞台 = scripts/vfx-preview.ts 在 VFX_STAGE 下输出的透明层（人物 + 特效，精灵像素）；
  按 1 精灵像素 = K 屏幕像素最近邻放大叠上去，再套游戏的镜头（推近、摇镜、震屏、倾斜）和压暗。
用法：python3 tools/golem_skill.py <背景帧目录> <舞台目录> <场景 id> <K> <输出.mp4>
"""
import glob, json, math, os, subprocess, sys
from PIL import Image

bgdir, sdir, sid, K, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
meta = json.load(open(os.path.join(sdir, sid + '.json')))
w, h, n = meta['w'], meta['h'], meta['n']
raw = open(os.path.join(sdir, sid + '.rgba'), 'rb').read()
bgs = sorted(glob.glob(os.path.join(bgdir, 'f*.png')))
W, H = w * K, h * K
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(meta['fps']), '-i', '-',
       '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', out]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
frames = []
for i, m in enumerate(meta['frames']):
    bg = Image.open(bgs[min(i, len(bgs) - 1)]).convert('RGBA').resize((W, H))
    dim, tint = m['dim'], m['tint']
    if dim > 0.001:
        r, g, b, a = bg.split()
        r = r.point(lambda v: v * (1 - dim) * (1 - dim * (1 - tint[0])))
        g = g.point(lambda v: v * (1 - dim) * (1 - dim * (1 - tint[1])))
        b = b.point(lambda v: v * (1 - dim) * (1 - dim * (1 - tint[2])))
        bg = Image.merge('RGBA', (r, g, b, a))
    st = Image.frombytes('RGBA', (w, h), raw[i * w * h * 4:(i + 1) * w * h * 4]).resize((W, H), Image.NEAREST)
    bg.alpha_composite(st)
    # 镜头（舞台像素 → 屏幕像素 × K）
    cx = W / 2 + (m['fx'] * K - W / 2) * m['w']
    cy = H / 2 + (m['fy'] * K - H / 2) * m['w']
    s = 1 + m['zoom']
    hw, hh = W / 2 / s, H / 2 / s
    cx = min(W - hw, max(hw, cx)); cy = min(H - hh, max(hh, cy))
    ca, sa = math.cos(-m['rot']), math.sin(-m['rot'])
    a, bq, d, e = ca / s, -sa / s, sa / s, ca / s
    c0 = cx - m['dx'] * K - (a * W / 2 + bq * H / 2)
    f0 = cy - m['dy'] * K - (d * W / 2 + e * H / 2)
    frame = bg.transform((W, H), Image.AFFINE, (a, bq, c0, d, e, f0), resample=Image.BILINEAR, fillcolor=(30, 40, 30, 255)).convert('RGB')
    frames.append(frame)
# 播两遍，中间停半秒
for loop in range(2):
    for f in frames:
        proc.stdin.write(f.tobytes())
    for _ in range(10):
        proc.stdin.write(frames[-1].tobytes())
proc.stdin.close(); proc.wait()
frames[[k for k, m in enumerate(meta['frames']) if m['t'] >= 1.1][0] if any(m['t'] >= 1.1 for m in meta['frames']) else -1].save(os.path.splitext(out)[0] + '.png')
print(out, len(frames))
