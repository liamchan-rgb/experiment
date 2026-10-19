#!/usr/bin/env python3
"""Render the actual wardrobe crossed with every approved head, at 120 ms."""
import importlib.util
import itertools
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Wardrobe/down/v1'
spec = importlib.util.spec_from_file_location('assembly', Path(__file__).with_name('compose-character-parts.py'))
assembly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembly)


def board(sprites, labels, columns=3, title='P1 / SAME BODY + MOTION / INDEPENDENT WARDROBE'):
    width, height = 300, 405
    rows = (len(sprites) + columns - 1) // columns
    out = Image.new('RGB', (columns * width, 60 + rows * height), '#d6e1dd')
    draw = ImageDraw.Draw(out)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    heading = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
    draw.text((14, 14), title, fill='#29494a', font=heading)
    for i, (sprite, label) in enumerate(zip(sprites, labels)):
        x, y = i % columns * width, 60 + i // columns * height
        draw.text((x + 12, y), label, fill='#3b5c5a', font=font)
        crop = sprite.crop((80, 66, 176, 226)).resize((192, 320), Image.Resampling.NEAREST)
        out.paste(crop, (x + 54, y + 35), crop)
    return out


def normal_gif(frames, path):
    atlas = Image.new('RGB', (frames[0].width * len(frames), frames[0].height))
    for i, im in enumerate(frames):
        atlas.paste(im, (i * im.width, 0))
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    sequence = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames]
    sequence[0].save(path, save_all=True, append_images=sequence[1:], duration=120,
                     loop=0, disposal=1, optimize=False)
    return sequence


def main():
    engine = assembly.Compositor(ROOT, OUT / 'catalog.json', OUT / 'motion.json')
    groups = {}
    for identifier in engine.entries:
        data, _, _ = engine.asset(identifier)
        groups.setdefault(data['part'], []).append(identifier)
    base, = groups['base']
    outfit, = groups['outfit']
    weapon, = groups['weapon']
    rendered, records = {}, []
    for hair, face, dressed, armed in itertools.product(groups['hair'], groups['face'], [False, True], [False, True]):
        selected = [hair, face] + ([outfit] if dressed else []) + ([weapon] if armed else [])
        name = '__'.join([hair, face, 'dressed' if dressed else 'base', 'sword' if armed else 'empty'])
        folder = OUT / 'combinations' / name
        folder.mkdir(parents=True, exist_ok=True)
        images = []
        for n in range(9):
            im = engine.render(base, selected, 'down', 'idle' if n == 0 else 'walk', n)
            im.save(folder / f'{n:02}.png')
            images.append(im)
        strip = Image.new('RGBA', (256 * 9, 256))
        for n, im in enumerate(images):
            strip.paste(im, (n * 256, 0))
        strip.save(folder / 'strip.png')
        record = {'folder': folder.relative_to(OUT).as_posix(), 'base': base, 'assets': selected,
                  'direction': 'down', 'motionSHA256': assembly.digest(OUT / 'motion.json'),
                  'assetManifestSHA256': {k: assembly.digest(engine.asset(k)[1]) for k in [base, *selected]},
                  'frames': {f'{n:02}.png': assembly.digest(folder / f'{n:02}.png') for n in range(9)}}
        (folder / 'composition.json').write_text(json.dumps(record, indent=2) + '\n')
        records.append(record)
        rendered[hair, face, dressed, armed] = images
    hair, face = groups['hair'][0], groups['face'][0]
    cases = [(False, False), (True, False), (True, True)]
    labels = ['COMMON BODY / EMPTY HAND', 'FORESTER / EMPTY HAND', 'FORESTER + SOCKET SWORD']
    def comparison(n):
        return board([rendered[hair, face, a, b][n] for a, b in cases], labels)
    comparison(0).save(OUT / 'review.png')
    normal_gif([comparison(n) for n in range(1, 9)], OUT / 'walk.gif')
    dressed = rendered[hair, face, True, True]
    board(dressed, ['00 IDLE'] + [f'{n:02} WALK' for n in range(1, 9)],
          title='P1 / DOWN / 00 IDLE + 01-08 WALK').save(OUT / 'poses.png')
    heads = [(h, f) for f in groups['face'] for h in groups['hair']]
    board([rendered[h, f, True, True][0] for h, f in heads],
          [h.removeprefix('p1-hair-').removesuffix('-v1') + ' / ' +
           f.removeprefix('p1-face-').removesuffix('-v1') for h, f in heads],
          title='P1 / 3 HAIR x 2 FACE / SAME OUTFIT + SWORD').save(OUT / 'heads-dressed.png')
    local_parts = []
    part_labels = []
    for identifier in [outfit, weapon]:
        for slot, im in engine.layers(base, [identifier], 'down', 'idle', 0):
            if slot.startswith(('outfit.', 'weapon.')):
                local_parts.append(im)
                part_labels.append(slot)
    board(local_parts, part_labels, title='P1 / CLOTH + WEAPON CUTOUTS / NO BODY').save(OUT / 'independent-parts.png')
    (OUT / 'combinations.json').write_text(json.dumps({'count': len(records), 'poses': len(records) * 9,
        'frameMs': 120, 'slowPreviewGenerated': False, 'combinations': records}, indent=2) + '\n')
    print(f'Exported {len(records)} combinations / {len(records) * 9} poses; normal 120 ms GIF only.')


if __name__ == '__main__':
    main()
