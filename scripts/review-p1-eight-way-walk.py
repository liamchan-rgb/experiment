#!/usr/bin/env python3
"""Normal-speed review GIF: both P1 looks walking in all eight directions, read straight from the
shipped atlases (columns 1-8 = walk, 120 ms per pose as in hero-gait.json). Offline composite.
Usage: python3 -I scripts/review-p1-eight-way-walk.py <out.gif> [scale]
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'Sources/Resources/Assets.xcassets'
gait = json.loads((ROOT / 'Sources/Resources/hero-gait.json').read_text())['modularP1']
ORDER = [('down', 0, 0), ('down-right', 1, 0), ('right', 0, 3), ('up-right', 1, 3),
         ('up', 0, 2), ('up-left', 1, 2), ('left', 0, 1), ('down-left', 1, 1)]
def main():
    out = Path(sys.argv[1]); scale = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    looks = [(l['title'], l['weaponAtlasNames']['trainingSword']) for l in gait['loadouts']]
    atlases = {n: Image.open(A / f'{n}.imageset/{n}.png').convert('RGBA') for _, names in looks for n in names}
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 14 * scale)
    except OSError: font = ImageFont.load_default()
    cell = 256 * scale // 2
    frames = []
    for pose in range(8):
        canvas = Image.new('RGB', (cell * 8, (cell + 20 * scale) * len(looks)), (120, 140, 90))
        draw = ImageDraw.Draw(canvas)
        for r, (title, names) in enumerate(looks):
            draw.text((6, r * (cell + 20 * scale) + 2), title, fill=(255, 255, 255), font=font)
            for c, (name, group, row) in enumerate(ORDER):
                im = atlases[names[group]].crop(((1 + pose) * 256, row * 256, (2 + pose) * 256, (row + 1) * 256))
                im = im.resize((cell, cell), Image.NEAREST)
                canvas.paste(im, (c * cell, r * (cell + 20 * scale) + 20 * scale), im)
        frames.append(canvas)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=gait['frameMs'], loop=0, optimize=True)
    frames[0].save(out.with_suffix('.png'))
    print(out, frames[0].size, len(frames), 'frames', gait['frameMs'], 'ms')
if __name__ == '__main__':
    main()
