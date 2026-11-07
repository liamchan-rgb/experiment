"""Offline preview of the three hand-built healing sheets on the review battle scene, at the sizes the landscape view draws them
(held frames, nearest scaling, additive). Approximation of the UIKit drawing, 20 fps."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'scripts/review-battle-effects-demo.py'
env = {'__file__': str(base)}
src = base.read_text().replace("'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',", "'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',")
exec(compile(src.split('\nframes=[]; traces=[]')[0], str(base), 'exec'), env)
plate, foreground, render, shadow = env['plate'], env['foreground'], env['render'], env['shadow']
hs, es, hx, hy, ex, ey, enemy = [env[k] for k in ['hs', 'es', 'hx', 'hy', 'ex', 'ey', 'enemy']]
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
TIERS = [('micro', 'BattleVFXHealingMicroSheet', (208, 208), 320, 320, 1.0), ('standard', 'BattleVFXHealingStandardSheet', (248, 207), 320, 268, 0.90), ('strong', 'BattleVFXHealingStrongSheet', (258, 258), 320, 320, 0.66)]
UNIT = 1.0
foot = (hx + 128 * hs, hy + 240 * hs)


def scene(t):
    s = plate.copy(); hero = render('idle', (t % 2.4) / 2.4)
    shadow(s, enemy, ex, ey, es); shadow(s, hero, hx, hy, hs)
    s.alpha_composite(hero.resize((round(256 * hs), round(256 * hs)), Image.Resampling.NEAREST), (round(hx), round(hy)))
    s.alpha_composite(enemy.resize((round(enemy.width * es), round(enemy.height * es)), Image.Resampling.NEAREST), (round(ex), round(ey)))
    s.alpha_composite(foreground)
    return np.asarray(s.convert('RGB')).astype(float)


def frame(tier, t):
    name, asset, size, cw, ch, anchor = tier
    buf = scene(t); f = int(t * 20)
    if f < 20:
        sheet = Image.open(ROOT / f'Sources/Resources/Assets.xcassets/{asset}.imageset/{asset}.png').convert('RGBA')
        cell = sheet.crop(((f % 5) * cw, (f // 5) * ch, (f % 5) * cw + cw, (f // 5) * ch + ch)).resize((round(size[0] * UNIT), round(size[1] * UNIT)), Image.Resampling.NEAREST)
        a = np.asarray(cell).astype(float); layer = a[..., :3] * a[..., 3:] / 255 * 0.95
        x0 = round(foot[0] - cell.width / 2); y0 = round(foot[1] - cell.height * anchor)
        H, W = buf.shape[:2]
        ys, xs = slice(max(0, y0), min(H, y0 + cell.height)), slice(max(0, x0), min(W, x0 + cell.width))
        buf[ys, xs] += layer[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
    return Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8))


CROP = (int(hx - 90), int(hy - 70), int(hx + 330), int(hy + 280))
panels = []
for tier in TIERS:
    fr = [frame(tier, k / 20.0).crop(CROP) for k in range(26)]
    panels.append(fr)
    fr[0].save(OUT / f'heal-{tier[0]}.gif', save_all=True, append_images=fr[1:], duration=50, loop=0, optimize=True)
combo = []
for k in range(26):
    c = Image.new('RGB', (panels[0][0].width * 3 + 12, panels[0][0].height))
    for i in range(3): c.paste(panels[i][k], (i * (panels[0][0].width + 6), 0))
    combo.append(c)
combo[0].save(OUT / 'healing-micro-standard-strong.gif', save_all=True, append_images=combo[1:], duration=50, loop=0, optimize=True)
combo[9].save(OUT / 'healing-peak.png')
print('ok', combo[0].size)
