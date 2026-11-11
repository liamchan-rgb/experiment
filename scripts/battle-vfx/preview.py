"""Real-speed old-vs-new preview: old = cross-fade + smooth scaling, new = held frames + nearest (additive on a meadow-ish dark ground)."""
import os, sys, subprocess, io
import numpy as np
from PIL import Image
from skills import SPECS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
NEW = sys.argv[1]; OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SCALE = 0.62
BG = np.zeros((10, 10, 3), np.uint8)


def old_sheet(asset):
    rel = f'Sources/Resources/Assets.xcassets/{asset}.imageset/{asset}.png'
    data = subprocess.check_output(['git', '-C', ROOT, 'show', f'HEAD:{rel}'])
    return Image.open(io.BytesIO(data)).convert('RGBA')


def cell(sheet, i, cw, ch, cols):
    return sheet.crop(((i % cols) * cw, (i // cols) * ch, (i % cols) * cw + cw, (i // cols) * ch + ch))


def additive(bg, im):
    a = np.asarray(im).astype(float)
    return np.clip(bg + a[..., :3] * a[..., 3:] / 255, 0, 255)


def ground(w, h):
    y = np.linspace(0, 1, h)[:, None, None]
    return (np.array([38, 58, 44]) * (1 - y) + np.array([24, 38, 30]) * y) * np.ones((h, w, 3))


for skill, (asset, n, fps, cw, ch, cols, sc) in SPECS.items():
    old = old_sheet(asset); new = Image.open(os.path.join(NEW, asset + '.png')).convert('RGBA')
    W, H = int(cw * SCALE), int(ch * SCALE)
    frames = []
    sub = 4                                           # render at 4 x spec fps then drop to 25 fps GIF steps below
    ticks = int(n / fps * 25)
    for t in range(ticks + 6):
        time = t / 25.0
        pos = min(time * fps, n - 1e-6) if time * fps < n else None
        panels = []
        for kind in ('old', 'new'):
            bg = ground(W, H)
            if pos is not None:
                i = int(pos); f = pos - i
                if kind == 'old':
                    a = cell(old, i, cw, ch, cols).resize((W, H), Image.BILINEAR)
                    bg = additive(bg, a) if i == n - 1 else additive(additive(bg, _ := Image.fromarray((np.asarray(a) * np.array([1, 1, 1, 1 - f])).astype(np.uint8))), Image.fromarray((np.asarray(cell(old, i + 1, cw, ch, cols).resize((W, H), Image.BILINEAR)) * np.array([1, 1, 1, f])).astype(np.uint8)))
                else:
                    a = cell(new, i, cw, ch, cols).resize((W, H), Image.NEAREST)
                    bg = additive(bg, a)
            panels.append(Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)))
        canvas = Image.new('RGB', (W * 2 + 6, H), (0, 0, 0)); canvas.paste(panels[0], (0, 0)); canvas.paste(panels[1], (W + 6, 0))
        frames.append(canvas)
    frames[0].save(os.path.join(OUT, f'{skill}-old-vs-new.gif'), save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
    print(skill, len(frames), os.path.getsize(os.path.join(OUT, f'{skill}-old-vs-new.gif')) // 1024, 'KB')
