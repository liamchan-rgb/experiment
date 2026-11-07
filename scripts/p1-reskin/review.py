"""Review: original walk vs low-poly model v3 vs re-skinned jog (down-right, forester), same scale."""
import io, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import reskin, clips

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Art/Review/P1/reskin-v1'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 18)

def atlas(rev):
    p = 'Sources/Resources/Assets.xcassets/Hero1Diagonals.imageset/Hero1Diagonals.png'
    return Image.open(io.BytesIO(subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{rev}:{p}']))).convert('RGBA')

def ground(offset, fx=.7071, fz=.7071):
    ys, xs = np.mgrid[0:256, 0:256].astype(float)
    gx, gz = xs - 128 + offset * fx, 2 * (ys - 214) + offset * fz
    c = ((np.floor(gx / 16) + np.floor(gz / 16)) % 2).astype(np.uint8)
    img = np.zeros((256, 256, 4), np.uint8)
    img[..., 0] = 70 + 14 * c; img[..., 1] = 104 + 16 * c; img[..., 2] = 60 + 8 * c; img[..., 3] = 255
    return Image.fromarray(img)

def main(orig_root):
    OUT.mkdir(parents=True, exist_ok=True)
    frame, layers = reskin.load_original(orig_root, 'down-right')
    rig = reskin.Rig('down-right', frame)
    old, lowpoly = atlas('527e3548'), atlas('70e323d2')
    keys = [('idle', 0)] + [('walk-start', 1), ('walk-start', 2)] + [('walk', n) for n in range(1, 9)] + [('walk-stop', 1), ('walk-stop', 2)]
    cols = {'idle': 0, 'walk-start': 8, 'walk-stop': 10}
    def atlas_cell(a, clip, n):
        c = n if clip == 'walk' else 0 if clip == 'idle' else cols[clip] + n
        return a.crop((c * 256, 0, c * 256 + 256, 256))
    rows = [('原画（原来的走路）', lambda k, n: atlas_cell(old, k, n)),
            ('低模 v3（已否决）', lambda k, n: atlas_cell(lowpoly, k, n)),
            ('原画上皮（新小跑）', lambda k, n: reskin.compose('down-right', frame, layers, rig, clips.pose(k, n)))]
    cells = {label: [f(k, n) for k, n in keys] for label, f in rows}
    Z = 2
    for ms, tag in ((120, 'slow'), (40, 'game-speed')):
        frames = []
        for t in range(16):
            F = Image.new('RGB', (3 * (120 * Z + 16) + 16, 160 * Z + 44), (40, 40, 40))
            d = ImageDraw.Draw(F)
            for i, (label, _) in enumerate(rows):
                x = 16 + i * (120 * Z + 16)
                d.text((x, 8), label, font=FONT, fill=(255, 230, 150))
                g = ground(-t * 12.0) if i == 2 else Image.new('RGBA', (256, 256), (74, 104, 62, 255))
                g.alpha_composite(cells[label][3 + t % 8])
                F.paste(g.crop((68, 76, 188, 236)).resize((120 * Z, 160 * Z), Image.NEAREST).convert('RGB'), (x, 40))
            frames.append(F)
        frames[0].save(OUT / f'down-right-{tag}.gif', save_all=True, append_images=frames[1:], duration=ms, loop=0)
    # every cell of the re-skinned version, plus the original idle for reference
    S = Image.new('RGBA', (len(keys) * 120, 3 * 160), (74, 104, 62, 255))
    for r, (label, _) in enumerate(rows):
        for i, c in enumerate(cells[label]):
            S.alpha_composite(c.crop((68, 76, 188, 236)), (i * 120, r * 160))
    S.save(OUT / 'down-right-all-cells.png')

if __name__ == '__main__':
    main(sys.argv[1])
