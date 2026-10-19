#!/usr/bin/env python3
"""Build a registered single-frame review of the point-down forward sword grip."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Wardrobe/down/v4'
spec = importlib.util.spec_from_file_location('assembly', Path(__file__).with_name('compose-character-parts.py'))
assembly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembly)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cfg = json.loads((OUT / 'registration.json').read_text())
    source = Image.open(OUT / 'parts/weapon/source/down.png').convert('RGBA')
    if source.size != (1254, 1254):
        raise ValueError('weapon source must use the fixed1254 plate')
    plate = Image.new('RGBA', source.size)
    plate.paste(source.crop((80, 80, 1174, 1174)), (80, 80))
    author = plate.resize((96, 96), Image.Resampling.NEAREST)
    pixels = np.asarray(author).copy()
    pixels[:, :, 3][pixels[:, :, 3] >= 250] = 255
    author = Image.fromarray(pixels)
    crop = tuple(cfg['weapon']['cropFrom96'])
    alpha = np.asarray(author.getchannel('A')).copy()
    alpha[crop[1]:crop[3], crop[0]:crop[2]] = 0
    assert alpha.max() <= 8, 'weapon must stay in its declared authoring cell'
    weapon = author.crop(crop)
    wp = tuple(cfg['weapon']['pivot'])
    assert weapon.getpixel(wp)[3] >= 128, 'weapon grip pivot misses opaque hilt'
    weapon.save(OUT / 'parts/weapon/local.png')

    raw_hand = Image.open(OUT / 'parts/hand/source/common-hand-r3.png').convert('RGBA')
    if raw_hand.size != (256, 256):
        raise ValueError('shared hand layer source must preserve the256 pose canvas')
    matrix = tuple(cfg['hand']['clockwise90AroundSocket'])
    rotated = raw_hand.transform((256, 256), Image.Transform.AFFINE, matrix,
                                 resample=Image.Resampling.NEAREST)
    box = rotated.getbbox()
    hand = rotated.crop(box)
    hp = (cfg['socket'][0] - box[0], cfg['socket'][1] - box[1])
    assert hand.getpixel(hp)[3] > 0, 'hand rotation moved the authored grip pivot'
    hand.save(OUT / 'parts/hand/local.png')

    engine = assembly.Compositor(ROOT, OUT.parent / 'v2/catalog.json', OUT.parent / 'v2/motion.json')
    selected = ['p1-hair-chestnut-v1', 'p1-face-blue-v1', 'p1-outfit-forester-v1']
    layers = engine.layers('p1-neutral-down-walk-r3', selected, 'down', 'idle', 0)
    previous = engine.render('p1-neutral-down-walk-r3', selected + ['p1-weapon-short-sword-v2'],
                              'down', 'idle', 0)
    old = dict(engine.layers('p1-neutral-down-walk-r3',
                             selected + ['p1-weapon-short-sword-v2'], 'down', 'idle', 0))
    socket = tuple(cfg['socket'])
    placed_weapon = assembly.place(weapon, [1, 0, 0, 1, socket[0]-wp[0], socket[1]-wp[1]], [256, 256])
    placed_hand = assembly.place(hand, [1, 0, 0, 1, box[0], box[1]], [256, 256])
    result = Image.new('RGBA', (256, 256))
    for slot, layer in layers:
        if slot == 'body.hand.right':
            result.alpha_composite(placed_weapon)
            result.alpha_composite(placed_hand)
        else:
            result.alpha_composite(layer)
    result.save(OUT / '00.png')

    changed = np.zeros((256, 256), dtype=bool)
    for image in [placed_hand, placed_weapon, old['body.hand.right'], old['weapon.right']]:
        changed |= np.asarray(image)[:, :, 3] > 0
    assert np.array_equal(np.asarray(previous)[~changed], np.asarray(result)[~changed])
    hpix = np.asarray(placed_hand)[:, :, 3] >= 128
    wpix = np.asarray(placed_weapon)[:, :, 3] >= 128
    cuff = np.asarray(dict(layers)['outfit.sleeve.right'])[:, :, 3] >= 128
    assert (hpix & wpix).any(), 'fingers do not overlap the handle'
    assert (hpix & cuff).any(), 'wrist does not meet the sleeve'

    board = Image.new('RGB', (840, 650), '#d6e1dd')
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    draw.text((25, 15), '00 / FORWARD GRIP / POINT DOWN / EDGE OBLIQUE', font=font, fill='#29494a')
    full = result.crop((74, 66, 176, 226)).resize((306, 480), Image.Resampling.NEAREST)
    board.paste(full, (20, 70), full)
    detail = result.crop((81, 153, 117, 203)).resize((360, 500), Image.Resampling.NEAREST)
    board.paste(detail, (440, 70), detail)
    board.save(OUT / 'review.png')
    independent = Image.new('RGB', (600, 330), '#c6d0cf')
    hs = hand.resize((hand.width * 12, hand.height * 12), Image.Resampling.NEAREST)
    ws = weapon.resize((128, 192), Image.Resampling.NEAREST)
    independent.paste(hs, (35, 65), hs)
    independent.paste(ws, (370, 65), ws)
    labels = ImageDraw.Draw(independent)
    labels.text((20, 20), 'SHARED HAND / FIXED QUARTER TURN', fill='#29494a')
    labels.text((320, 20), 'EDGE-OBLIQUE SWORD / FORESHORTENED GUARD', fill='#29494a')
    independent.save(OUT / 'independent-parts.png')
    record = {'kind': 'single-idle-pose-art-study', 'direction': 'down', 'clip': 'idle', 'frame': 0,
              'artApproval': None, 'socket': list(socket), 'grip': 'normal forward, point-down',
              'handAndWeaponStoredSeparately': True, 'wristSleeveAttached': True,
              'handWeaponOverlapPixels': int((hpix & wpix).sum()),
              'handSleeveOverlapPixels': int((hpix & cuff).sum()),
              'otherPixelsMatchOldCompositionOutsideHandAndWeapon': True,
              'local': {'hand': {'size': list(hand.size), 'pivot': list(hp), 'sha256': digest(OUT/'parts/hand/local.png')},
                        'weapon': {'size': list(weapon.size), 'pivot': list(wp), 'sha256': digest(OUT/'parts/weapon/local.png')}},
              'animationGenerated': False, 'productionManifestGenerated': False,
              'limits': ['Single idle pose only; no nine-frame or production validation.',
                         'Visual grip quality and edge/guard perspective remain subject to review.']}
    (OUT / 'validation.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
