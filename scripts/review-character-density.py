"""Pixel-density comparison: the current hero art box-downsampled to N pixels tall, drawn at the real on-screen size beside the forest-warden deer.
Usage: python3 scripts/review-character-density.py   (writes Art/Review/Character/density-v1/). Approximation of the density only, not hand-made pixel art."""
import sys, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'scripts/review-battle-effects-demo.py'; env = {'__file__': str(base)}
src = base.read_text().replace("'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',", "'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',")
exec(compile(src.split('\nframes=[]; traces=[]')[0], str(base), 'exec'), env)
W, H = env['W'], env['H']; plate, foreground, render, shadow = env['plate'], env['foreground'], env['render'], env['shadow']
hs, es, hx, hy, ex, ey, enemy = [env[k] for k in ['hs', 'es', 'hx', 'hy', 'ex', 'ey', 'enemy']]
S = 3
hero = render('idle', 0.1)
BOX = (48, 82, 227, 216)                      # head to feet, sword included
fig = hero.crop(BOX); FW, FH = fig.size
cx3 = (hx + (BOX[0] + BOX[2]) / 2 * hs) * S; bot3 = (hy + BOX[3] * hs) * S; left3 = (hx + BOX[0] * hs) * S; top3 = (hy + BOX[1] * hs) * S
target_h = FH * hs * S
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 34)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 26)

def pixelize(h):
    w = round(FW * h / FH)
    small = fig.resize((w, h), Image.Resampling.BOX); a = np.asarray(small).astype(float)
    mask = a[..., 3] > 110; rgb = a[..., :3]
    px = rgb[mask].astype(np.uint8).reshape(-1, 1, 3)
    q = Image.fromarray(px).quantize(22, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:66]).reshape(-1, 3)[:22]
    d = ((rgb[..., None, :] - pal[None, None]) ** 2).sum(-1); out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = pal[d.argmin(-1)]; out[..., 3] = np.where(mask, 255, 0)
    return Image.fromarray(out)

def scene(variant):
    s = plate.copy(); shadow(s, enemy, ex, ey, es); shadow(s, hero, hx, hy, hs)
    s3 = s.resize((W * S, H * S), Image.Resampling.LANCZOS).convert('RGBA')
    s3.alpha_composite(enemy.resize((round(enemy.width * es * S), round(enemy.height * es * S)), Image.Resampling.NEAREST), (round(ex * S), round(ey * S)))
    if variant is None:
        im = fig.resize((round(FW * hs * S), round(FH * hs * S)), Image.Resampling.NEAREST); s3.alpha_composite(im, (round(left3), round(top3))); k = None
    else:
        small = pixelize(variant); k = max(1, round(target_h / variant))
        im = small.resize((small.width * k, small.height * k), Image.Resampling.NEAREST)
        s3.alpha_composite(im, (round(cx3 - im.width / 2), round(bot3 - im.height)))
    s3.alpha_composite(foreground.resize((W * S, H * S), Image.Resampling.LANCZOS))
    return s3, k

CROP = (80 * S, 225 * S, 700 * S, 510 * S)
panels = []
for label, v in [('现在的角色（约 134 像素高）', None), ('72 像素高', 72), ('51 像素高', 51), ('36 像素高', 36)]:
    s3, k = scene(v); p = s3.crop(CROP).convert('RGB'); d = ImageDraw.Draw(p)
    if v is None: sub = '方块 ≈ 鹿灵的方块（0.9 对 1.0）'
    else: sub = f'每个方块比鹿灵粗约 {k / S / es:.1f} 倍'
    d.rectangle([0, 0, p.width, 100], fill=(18, 24, 20)); d.text((20, 12), label, font=FONT, fill=(255, 236, 170)); d.text((20, 56), sub, font=SMALL, fill=(220, 230, 215))
    panels.append(p)
w, h = panels[0].size; sheet = Image.new('RGB', (w * 2 + 12, h * 2 + 12), (10, 14, 12))
for i, p in enumerate(panels): sheet.paste(p, ((i % 2) * (w + 12), (i // 2) * (h + 12)))
out = ROOT / 'Art/Review/Character/density-v1'; out.mkdir(parents=True, exist_ok=True)
sheet.resize((sheet.width * 2 // 3, sheet.height * 2 // 3), Image.Resampling.LANCZOS).save(out / 'density-compare.png')
for name, p in zip(['now', 'h72', 'h51', 'h36'], panels): p.save(out / f'{name}.png')
print(sheet.size)
