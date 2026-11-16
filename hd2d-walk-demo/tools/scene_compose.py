"""
3D 战斗场景的合成（HD-2D：物体像素化，雾 / 景深 / 光不像素化）：
  albedo.png  页面 mode=albedo 的低分辨率截图（px 倍，像素块：物体本身的颜色、明暗分档、描边；没有雾）
  depth.png   页面 mode=depth 的全分辨率深度（RGB 打包）
物体先按整张图挑一套调色板限色、最近邻放大成像素块；然后在全分辨率上按真实距离平滑地加：
  远处的雾（带天空的上下渐变）、景深（离舞台越远越虚，前景草也虚）、舞台上的暖光池、从左上斜下的光束、泛光、暗角和调色。
用法：python3 tools/scene_compose.py albedo.png depth.png near far out.png [colors]
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

albedo, depthf, near, far, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
colors = int(sys.argv[6]) if len(sys.argv) > 6 else 40

dimg = Image.open(depthf).convert('RGB')
W, H = dimg.size
# 物体：限色 + 最近邻放大
low = Image.open(albedo).convert('RGB')
low = low.quantize(colors=colors, method=Image.Quantize.MAXCOVERAGE, kmeans=2, dither=Image.Dither.NONE).convert('RGB')
base = np.asarray(low.resize((W, H), Image.NEAREST)).astype(np.float32) / 255

# 深度 → 到镜头的距离（米）；背景（天空）给一个很远的值
d = np.asarray(dimg).astype(np.float64) / 255
z = d[..., 0] * 255 / 256 + d[..., 1] * 255 / 256 / 256 + d[..., 2] / 65536
sky = z > 0.9999
z = np.clip(z, 1e-6, 0.999999)
dist = (near * far) / (far - (far - near) * z)
dist[sky] = far
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
v = yy / H

def blur(img, r):
    if r <= 0: return img
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255

# 1. 景深：舞台（离镜头约 12 米）清晰；越远越虚，镜头前的前景也虚。按模糊半径分几档混合
focus = 12.5
coc = np.clip((dist - focus - 1.5) / 13, 0, 1) + np.clip((focus - 2.0 - dist) / 2.6, 0, 1) * 1.2
coc = np.clip(coc, 0, 1)
levels = [0, 2.5, 6, 12]
stack = [blur(base, r) for r in levels]
pos = coc * (len(levels) - 1)
i0 = np.clip(np.floor(pos).astype(int), 0, len(levels) - 2)
t = (pos - i0)[..., None]
img = np.zeros_like(base)
for k in range(len(levels) - 1):
    m = (i0 == k)[..., None]
    img = np.where(m, stack[k] * (1 - t) + stack[k + 1] * t, img)

# 1b. 镜头前的前景压暗一点（剪影感，把视线推向舞台）
near_k = np.clip((10.5 - dist) / 3, 0, 1)
img = img * (1 - 0.28 * near_k[..., None])

# 2. 雾：随距离平滑变浓，颜色上方偏天空蓝、下方偏暖白
fog_top, fog_bottom = np.array([0.78, 0.86, 0.90]), np.array([0.93, 0.92, 0.84])
fogc = fog_top * (1 - v[..., None]) + fog_bottom * v[..., None]
fog = np.clip((dist - 13.5) / 16, 0, 1) ** 1.1 * 0.82
fog[sky] = 0.55
img = img * (1 - fog[..., None]) + fogc * fog[..., None]

# 3. 光：舞台上的暖色光池（中间偏下最亮）+ 左上斜下的柔和光束
pool = np.exp(-(((xx - W * 0.52) / (W * 0.42)) ** 2) - (((yy - H * 0.66) / (H * 0.30)) ** 2))
img = img * (0.86 + 0.2 * pool[..., None]) + np.array([0.03, 0.022, 0.0]) * pool[..., None]
beam = np.zeros((H, W), np.float32)
for cx, w, k in [(0.30, 0.07, 0.20), (0.46, 0.05, 0.14), (0.62, 0.09, 0.12)]:
    u = (xx - yy * 0.55) / W - cx + 0.25
    beam += k * np.exp(-(u / w) ** 2) * np.clip(1 - v / 0.85, 0, 1)
beam *= np.clip((dist - 9) / 10, 0, 1)  # 光束在人物后面（不罩在舞台前景上）
img = img + np.array([1.0, 0.94, 0.78]) * beam[..., None]

# 4. 泛光：亮处向外晕开
lum = img.mean(-1, keepdims=True)
bright = np.clip(img - 0.75, 0, 1) * (lum > 0.72)
img = img + blur(bright, 14) * 0.9 + blur(bright, 4) * 0.4

# 5. 调色 + 暗角：暗部偏冷、亮部偏暖，四周压暗
l = img.mean(-1, keepdims=True)
img = img * (1 + (np.array([0.88, 0.95, 1.08]) - 1) * (1 - l) * 0.5) * (1 + (np.array([1.06, 1.02, 0.92]) - 1) * l * 0.5)
r = np.sqrt(((xx - W * 0.5) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.62)) ** 2)
img = img * (1 - np.clip((r - 0.7) / 0.6, 0, 1) * 0.35)[..., None]
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out)
print('ok', W, H)
