#!/usr/bin/env python3
"""Export a shared closed fist at existing grip sockets, for every appearance."""
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Neutral/down/walk-r3'
SOURCE = ROOT / 'Art/Templates/P1-Neutral/down/walk-r2'
spec = importlib.util.spec_from_file_location('wardrobe_export', Path(__file__).with_name('export-wardrobe-part.py'))
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def main():
    config = json.loads((OUT / 'grip-profile.json').read_text())
    source = Image.open(OUT / config['source']).convert('RGBA')
    assert source.size == (1254, 1254), 'fixed registration canvas required'
    whole = source.transform((256, 256), Image.Transform.AFFINE,
                             (6.25, 0, -156.25, 0, 6.25, -237.5), Image.Resampling.NEAREST)
    mask = Image.new('L', (256, 256))
    draw = ImageDraw.Draw(mask)
    for polygon in config['handPolygons']:
        draw.polygon([tuple(point) for point in polygon], fill=255)
    pixels = np.array(whole)
    pixels[np.array(mask) == 0] = 0
    pixels[:, :, 3][pixels[:, :, 3] >= 250] = 255
    hand = Image.fromarray(pixels)
    (OUT / 'shared').mkdir(exist_ok=True)
    hand.save(OUT / 'shared/grip-right.png')
    x, y = config['referenceGrip']
    hand.crop((x - 12, y - 12, x + 12, y + 12)).save(OUT / 'shared/grip-right-local.png')
    data = json.loads((SOURCE / 'asset.json').read_text())
    data['id'] = 'p1-neutral-down-walk-r3'
    data['version'] = '1.0.2'
    data['sourceFiles'] += ['source/grip-down.png', 'grip-profile.json', 'shared/grip-right-local.png']
    motion = json.loads((ROOT / 'Art/Templates/P1-Wardrobe/down/v1/motion.json').read_text())
    for n, binding in enumerate(data['bindings']):
        folder = OUT / 'layers' / f'{n:02}'
        folder.mkdir(parents=True, exist_ok=True)
        for path in (SOURCE / 'layers' / f'{n:02}').glob('*.png'):
            if path.name != 'body.hand.right.png':
                shutil.copyfile(path, folder / path.name)
        grip = motion['frames'][n]['sockets']['grip.right']['position']
        shifted = Image.new('RGBA', (256, 256))
        shifted.paste(hand, (grip[0] - x, grip[1] - y))
        shifted.save(folder / 'body.hand.right.png')
        images = {slot: Image.open(OUT / relative).convert('RGBA') for slot, relative in binding['layers'].items()}
        ordered = {slot: images[slot] for slot in motion['frames'][n]['drawOrder'] if slot in images}
        (OUT / 'editable').mkdir(exist_ok=True)
        result = exporter.editable(OUT / 'editable', f'{n:02}', ordered)
        (OUT / 'frames').mkdir(exist_ok=True)
        result.save(OUT / f'frames/{n:02}.png')
    (OUT / 'asset.json').write_text(json.dumps(data, indent=2) + '\n')
    print('Exported shared closed grip at nine original sockets; other63 body layers copied unchanged.')


if __name__ == '__main__':
    main()
