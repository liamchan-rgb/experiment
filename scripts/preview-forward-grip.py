#!/usr/bin/env python3
"""Export separate local hand/sword cutouts and preview idle00 for art review.

This is a single-pose authoring preview, not a production animation package.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Wardrobe/down/v3'
spec = importlib.util.spec_from_file_location('assembly', Path(__file__).with_name('compose-character-parts.py'))
assembly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembly)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_source(folder, author_canvas):
    raw = Image.open(folder / 'source/down.png').convert('RGBA')
    if raw.size != (1254, 1254):
        raise ValueError('source must retain the fixed1254 local authoring plate')
    clean = Image.new('RGBA', raw.size)
    clean.paste(raw.crop((80, 80, 1174, 1174)), (80, 80))
    result = clean.resize(tuple(author_canvas), Image.Resampling.NEAREST)
    pixels = np.array(result)
    pixels[:, :, 3][pixels[:, :, 3] >= 250] = 255
    return Image.fromarray(pixels)


def main():
    cfg = json.loads((OUT / 'registration.json').read_text())
    pieces = {}
    for name in ['hand', 'weapon']:
        folder = OUT / 'parts' / name
        plate = local_source(folder, cfg[name]['authorCanvas'])
        crop = tuple(cfg[name]['cropFromAuthorCanvas'])
        alpha = np.array(plate)[:, :, 3]
        outside = alpha.copy()
        outside[crop[1]:crop[3], crop[0]:crop[2]] = 0
        assert outside.max() <= 8, f'{name} drawing outside explicit local canvas; do not content-fit'
        local = plate.crop(crop)
        local.save(folder / 'local.png')
        px, py = cfg[name]['pivot']
        assert local.getpixel((px, py))[3] >= 128, f'{name} grip misses actual art'
        pieces[name] = local
    engine = assembly.Compositor(ROOT, OUT.parent / 'v2/catalog.json', OUT.parent / 'v2/motion.json')
    layers = engine.layers('p1-neutral-down-walk-r3',
                          ['p1-hair-chestnut-v1', 'p1-face-blue-v1', 'p1-outfit-forester-v1'],
                          'down', 'idle', 0)
    grip = engine.frames['down', 'idle', 0]['sockets']['grip.right']['position']
    placed = {}
    for name, image in pieces.items():
        px, py = cfg[name]['pivot']
        placed[name] = assembly.place(image, [1, 0, 0, 1, grip[0]-px, grip[1]-py], [256, 256])
    result = Image.new('RGBA', (256, 256))
    for slot, image in layers:
        if slot == 'body.hand.right':
            result.alpha_composite(placed['weapon'])
            result.alpha_composite(placed['hand'])
        else:
            result.alpha_composite(image)
    result.save(OUT / '00.png')
    board = Image.new('RGB', (840, 650), '#d6e1dd')
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    draw.text((25, 15), '00 / FORWARD GRIP / OBLIQUE CUTTING EDGE', font=font, fill='#29494a')
    full = result.crop((74, 66, 176, 226)).resize((306, 480), Image.Resampling.NEAREST)
    board.paste(full, (20, 70), full)
    detail = result.crop((74, 126, 117, 187)).resize((344, 488), Image.Resampling.NEAREST)
    board.paste(detail, (440, 70), detail)
    board.save(OUT / 'review.png')
    independent = Image.new('RGB', (600, 330), '#c6d0cf')
    h = pieces['hand'].resize((160, 160), Image.Resampling.NEAREST)
    w = pieces['weapon'].resize((128, 192), Image.Resampling.NEAREST)
    independent.paste(h, (45, 65), h)
    independent.paste(w, (380, 65), w)
    d = ImageDraw.Draw(independent)
    d.text((20, 20), 'HAND ONLY / NO WEAPON OR CLOTHES', fill='#29494a')
    d.text((320, 20), 'WEAPON ONLY / NO HAND OR SKIN', fill='#29494a')
    independent.save(OUT / 'independent-parts.png')
    previous = engine.render('p1-neutral-down-walk-r3',
                             ['p1-hair-chestnut-v1', 'p1-face-blue-v1', 'p1-outfit-forester-v1',
                              'p1-weapon-short-sword-v2'], 'down', 'idle', 0)
    old_parts = dict(engine.layers('p1-neutral-down-walk-r3',
                                   ['p1-hair-chestnut-v1', 'p1-face-blue-v1', 'p1-outfit-forester-v1',
                                    'p1-weapon-short-sword-v2'], 'down', 'idle', 0))
    changed = np.zeros((256, 256), dtype=bool)
    for image in [placed['hand'], placed['weapon'], old_parts['body.hand.right'], old_parts['weapon.right']]:
        changed |= np.array(image)[:, :, 3] > 0
    assert np.array_equal(np.array(previous)[~changed], np.array(result)[~changed])
    overlap = ((np.array(placed['hand'])[:, :, 3] >= 128) &
               (np.array(placed['weapon'])[:, :, 3] >= 128))
    assert overlap.any(), 'hand does not meet hilt'
    cuff = ((np.array(placed['hand'])[:, :, 3] >= 128) &
            (np.array(dict(layers)['outfit.sleeve.right'])[:, :, 3] >= 128))
    assert cuff.any(), 'wrist does not meet sleeve'
    record = {'kind': 'single-idle-pose-art-study', 'direction': 'down', 'clip': 'idle', 'frame': 0,
              'artApproval': None, 'grip': grip, 'handAndWeaponStoredSeparately': True,
              'headClothesAndOtherBodyPixelsUnchanged': True,
              'handWeaponIntersectionPixels': int(overlap.sum()),
              'wristSleeveIntersectionPixels': int(cuff.sum()),
              'localPNG': {name: {'sha256': digest(OUT / 'parts' / name / 'local.png'),
                                  'size': list(image.size)} for name, image in pieces.items()},
              'animationGenerated': False, 'productionManifestGenerated': False,
              'limits': ['Forward grip and oblique blade perspective require visual user review.',
                         'This authoring preview is not nine-frame animation or production asset validation.']}
    (OUT / 'validation.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
