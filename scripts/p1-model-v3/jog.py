"""Jog cycle on the v3 model + review GIFs (game speed and slowed) for one facing."""
import math, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parents[1] / 'p1-skeleton-v2'))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import model, body, compare
from common import ROOT

STEP = 12.0   # ground px per pose: 24 distance units per cycle = 96 px
# right foot, q = poses since its contact: (forward u, lift, toe pitch; + = toes down)
LEG = [(12, 0, -.15), (0, 0, 0), (-12, 0, .35), (-16, 6, .9), (-10, 12, 1.1), (2, 12, .5), (11, 7, 0), (14, 2, -.2)]
BOB = [0, 2, 0, -2]
SWING, BEND, LEAN, TWIST = .55, .9, .12, .12

def jog_pose(p):
    c = math.cos(2 * math.pi * p / 8)
    arms = {}
    for side, sign in (('R', -1), ('L', 1)):
        swing = SWING * c * sign
        arms[side] = (swing, BEND + .4 * max(0, swing) / SWING)
    return dict(bob=BOB[p % 4], lean=LEAN, twist=-TWIST * c,
                legs={'R': LEG[p % 8], 'L': LEG[(p + 4) % 8]}, arms=arms)

def frame(facing, pose):
    J = body.skeleton(pose)
    rgba, _, _ = model.render(body.shapes(J, facing))
    return compare.with_head(facing, Image.fromarray(rgba), J)

def ground(facing, offset):
    fx, fz = body.FACING[facing]
    ys, xs = np.mgrid[0:256, 0:256].astype(float)
    gx, gz = xs - 128 + offset * fx, 2 * (ys - model.GROUND_Y) + offset * fz
    c = ((np.floor(gx / 16) + np.floor(gz / 16)) % 2).astype(np.uint8)
    img = np.zeros((256, 256, 4), np.uint8)
    img[..., 0] = 70 + 14 * c; img[..., 1] = 104 + 16 * c; img[..., 2] = 60 + 8 * c; img[..., 3] = 255
    return Image.fromarray(img)

def review(facing, out_dir):
    cells = [frame(facing, jog_pose(p)) for p in range(8)]
    font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 16)
    for ms, tag in ((40, 'game-speed'), (120, 'slow')):
        frames = []
        for k in range(24):
            g = ground(facing, -k * STEP); g.alpha_composite(cells[k % 8])
            W = Image.new('RGB', (240, 300), (40, 40, 40))
            W.paste(g.crop((68, 88, 188, 238)).resize((240, 300), Image.NEAREST).convert('RGB'), (0, 0))
            frames.append(W)
        frames[0].save(out_dir / f'{facing}-{tag}.gif', save_all=True, append_images=frames[1:], duration=ms, loop=0)
    sheet = Image.new('RGBA', (8 * 240, 320), (74, 104, 62, 255))
    for p, c in enumerate(cells):
        sheet.alpha_composite(c.crop((68, 76, 188, 236)).resize((240, 320), Image.NEAREST), (p * 240, 0))
    sheet.save(out_dir / f'{facing}-poses.png')
    return cells

if __name__ == '__main__':
    out = ROOT / 'Art/Review/P1/model-v3'
    out.mkdir(parents=True, exist_ok=True)
    for f in sys.argv[1:] or ['down-right']:
        review(f, out)
