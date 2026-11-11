"""Review sheets from the BAKED atlases: 8 facings x 4 looks, jog loop on scrolling ground."""
import json, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import model, body

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Art/Review/P1/model-v3'
ROWS = {'down': (0, 0), 'left': (0, 1), 'up': (0, 2), 'right': (0, 3),
        'down-right': (1, 0), 'down-left': (1, 1), 'up-left': (1, 2), 'up-right': (1, 3)}
ORDER = ['down', 'down-right', 'right', 'up-right', 'up', 'up-left', 'left', 'down-left']
LABEL = {'down': '下', 'down-right': '右下', 'right': '右', 'up-right': '右上', 'up': '上', 'up-left': '左上', 'left': '左', 'down-left': '左下'}
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 15)

def atlases():
    g = json.loads((ROOT / 'Sources/Resources/hero-gait.json').read_text())['modularP1']['loadouts']
    f, w = g[0], g[1]
    return [('林间绿衣', f['weaponAtlasNames']['trainingSword']), ('流浪者', w['weaponAtlasNames']['huntingBow']),
            ('皮甲', f['armorAtlasNames']['leatherArmor']['greatSword']), ('符文甲', w['armorAtlasNames']['runeArmor']['legendaryStaff'])]

def load(name):
    return Image.open(ROOT / f'Sources/Resources/Assets.xcassets/{name}.imageset/{name}.png').convert('RGBA')

def cell(images, facing, column):
    group, row = ROWS[facing]
    return images[group].crop((column * 256, row * 256, column * 256 + 256, row * 256 + 256))

def ground(facing, offset):
    fx, fz = body.FACING[facing]
    ys, xs = np.mgrid[0:256, 0:256].astype(float)
    gx, gz = xs - 128 + offset * fx, 2 * (ys - model.GROUND_Y) + offset * fz
    c = ((np.floor(gx / 16) + np.floor(gz / 16)) % 2).astype(np.uint8)
    img = np.zeros((256, 256, 4), np.uint8)
    img[..., 0] = 70 + 14 * c; img[..., 1] = 104 + 16 * c; img[..., 2] = 60 + 8 * c; img[..., 3] = 255
    return Image.fromarray(img)

def main():
    looks = [(label, [load(n) for n in names]) for label, names in atlases()]
    cw, ch = 104, 150
    for ms, tag in ((40, 'game-speed'), (120, 'slow')):
        frames = []
        for k in range(16):
            W = Image.new('RGB', (8 * cw + 64, len(looks) * ch + 22), (36, 36, 36))
            d = ImageDraw.Draw(W)
            for i, f in enumerate(ORDER):
                d.text((64 + i * cw + cw // 2 - 10, 2), LABEL[f], font=FONT, fill=(255, 230, 150))
            for r, (label, imgs) in enumerate(looks):
                d.text((4, 22 + r * ch + 60), label, font=FONT, fill=(255, 230, 150))
                for i, f in enumerate(ORDER):
                    g = ground(f, -k * 12.0); g.alpha_composite(cell(imgs, f, 1 + k % 8))
                    W.paste(g.crop((76, 82, 180, 232)).convert('RGB'), (64 + i * cw, 22 + r * ch))
            frames.append(W.resize((W.width * 3 // 2, W.height * 3 // 2), Image.NEAREST))
        frames[0].save(OUT / f'eight-way-{tag}.gif', save_all=True, append_images=frames[1:], duration=ms, loop=0)
    # every cell of the first look: idle, start 1-2, jog 1-8, stop 1-2
    imgs = looks[0][1]
    cols = [0, 9, 10] + list(range(1, 9)) + [11, 12]
    S = Image.new('RGBA', (len(cols) * cw, 8 * ch), (74, 104, 62, 255))
    for r, f in enumerate(ORDER):
        for i, c in enumerate(cols):
            S.alpha_composite(cell(imgs, f, c).crop((76, 82, 180, 232)), (i * cw, r * ch))
    S.save(OUT / 'forester-all-cells.png')

if __name__ == '__main__':
    main()
