"""Prototype review: new jog cycle vs the shipped walk, at game speed and slowed."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from PIL import Image, ImageDraw, ImageFont
import anim
from common import ROOT

OUT = ROOT / 'Art/Review/P1/skeleton-v2-prototype'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 16)
ROW = {'down-right': 0, 'down-left': 1, 'up-left': 2, 'up-right': 3}

def main(direction='down-right'):
    new = [anim.pose(direction, p)[0] for p in range(8)]
    shipped = Image.open(ROOT / 'Sources/Resources/Assets.xcassets/Hero1Diagonals.imageset/Hero1Diagonals.png').convert('RGBA')
    old = [shipped.crop(((p + 1) * 256, ROW[direction] * 256, (p + 2) * 256, (ROW[direction] + 1) * 256)) for p in range(8)]
    for ms, tag in ((40, 'game-speed'), (120, 'slow')):
        frames = []
        for k in range(24):
            p = k % 8
            W = Image.new('RGB', (2 * 216 + 10, 300), (40, 40, 40))
            for i, cells in enumerate((old, new)):
                g = anim.ground_frame(direction, -k * anim.STEP)
                g.alpha_composite(cells[p])
                W.paste(g.crop((74, 92, 182, 232)).resize((216, 280), Image.NEAREST).convert('RGB'), (i * 226, 20))
            d = ImageDraw.Draw(W)
            d.text((6, 1), '现在', font=FONT, fill=(255, 230, 150)); d.text((232, 1), '新骨骼原型（小跑）', font=FONT, fill=(255, 230, 150))
            frames.append(W)
        frames[0].save(OUT / f'{direction}-{tag}.gif', save_all=True, append_images=frames[1:], duration=ms, loop=0)
    sheet = Image.new('RGBA', (8 * 240, 320), (74, 104, 62, 255))
    for p, c in enumerate(new):
        sheet.alpha_composite(c.crop((68, 76, 188, 236)).resize((240, 320), Image.NEAREST), (p * 240, 0))
    sheet.save(OUT / f'{direction}-poses.png')

if __name__ == '__main__':
    main(*sys.argv[1:])
