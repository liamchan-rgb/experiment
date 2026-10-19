#!/usr/bin/env python3
"""Render every catalogued hair/face combination at normal walk speed only."""
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Modular/down/v1'
spec = importlib.util.spec_from_file_location('assembly', Path(__file__).with_name('compose-character-parts.py'))
assembly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembly)


def main():
    engine = assembly.Compositor(ROOT, OUT / 'catalog.json', OUT / 'motion.json')
    groups = {}
    for identifier in engine.entries:
        data, _, _ = engine.asset(identifier)
        groups.setdefault(data['part'], []).append(identifier)
    bases = groups.get('base', [])
    if len(bases) != 1:
        raise ValueError('review requires exactly one common body')
    base = bases[0]
    hairs, faces = groups['hair'], groups['face']
    catalog = json.loads((OUT / 'catalog.json').read_text())
    labels = {e['id']: e.get('label', e['id']) for e in catalog['assets']}
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    bg = '#dce4df'
    records, rendered = [], {}
    for face in faces:
        for hair in hairs:
            folder = OUT / 'combinations' / (hair + '__' + face)
            folder.mkdir(parents=True, exist_ok=True)
            frames = []
            for frame in range(9):
                im = engine.render(base, [hair, face], 'down', 'idle' if frame == 0 else 'walk', frame)
                im.save(folder / f'{frame:02}.png')
                frames.append(im)
            strip = Image.new('RGBA', (256 * 9, 256))
            for i, im in enumerate(frames):
                strip.alpha_composite(im, (i * 256, 0))
            strip.save(folder / 'strip.png')
            rendered[hair, face] = frames
            record = {'base': base, 'assets': [hair, face], 'direction': 'down',
                      'motionSHA256': assembly.digest(OUT / 'motion.json'),
                      'assetManifestSHA256': {k: assembly.digest(engine.asset(k)[1]) for k in [base, hair, face]},
                      'frameSHA256': {f'{i:02}.png': assembly.digest(folder / f'{i:02}.png') for i in range(9)}}
            (folder / 'composition.json').write_text(json.dumps(record, indent=2) + '\n')
            records.append(record)
    def board(frame, heads=False):
        cw, ch = (320, 310) if heads else (280, 405)
        image = Image.new('RGB', (cw * len(hairs), 65 + ch * len(faces)), bg)
        d = ImageDraw.Draw(image)
        d.text((16, 12), 'P1 / INDEPENDENT HAIR x FACE / SAME BODY', font=title, fill='#254345')
        for row, face in enumerate(faces):
            for col, hair in enumerate(hairs):
                x, y = col * cw, 65 + row * ch
                d.text((x + 12, y), labels[hair] + ' / ' + labels[face], font=font, fill='#486567')
                sprite = rendered[hair, face][frame]
                crop = (88, 72, 164, 140) if heads else (64, 64, 192, 232)
                scale = 4 if heads else 2
                sprite = sprite.crop(crop)
                sprite = sprite.resize((sprite.width * scale, sprite.height * scale), Image.Resampling.NEAREST)
                image.paste(sprite, (x + (cw - sprite.width) // 2, y + 25), sprite)
        return image
    board(0).save(OUT / 'review.png')
    board(0, heads=True).save(OUT / 'heads.png')
    frames = [board(i) for i in range(1, 9)]
    palette_board = Image.new('RGB', (frames[0].width * 8, frames[0].height))
    for i, im in enumerate(frames):
        palette_board.paste(im, (im.width * i, 0))
    palette = palette_board.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    sequence = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames]
    sequence[0].save(OUT / 'walk.gif', save_all=True, append_images=sequence[1:],
                     duration=120, loop=0, disposal=1, optimize=False)
    # Show the actual independent cutouts against an opaque review background.
    ids = hairs + faces
    parts = Image.new('RGB', (320 * len(ids), 340), '#c6d0cf')
    pd = ImageDraw.Draw(parts)
    for i, identifier in enumerate(ids):
        data, path, _ = engine.asset(identifier)
        local = Image.new('RGBA', (96, 96))
        for relative in data['bindings'][0]['layers'].values():
            local.alpha_composite(Image.open(path.parent / relative).convert('RGBA'))
        local = local.resize((288, 288), Image.Resampling.NEAREST)
        parts.paste(local, (i * 320 + 16, 40), local)
        pd.text((i * 320 + 12, 12), labels[identifier] + ' / NO BASE', font=font, fill='#254345')
    parts.save(OUT / 'independent-parts.png')
    (OUT / 'combinations.json').write_text(json.dumps({'combinations': records, 'frameMs': 120,
                                                      'slowPreviewGenerated': False}, indent=2) + '\n')
    print(f'Exported {len(records)} independent combinations, normal 120ms loop, full-body/head/parts PNGs.')


if __name__ == '__main__':
    main()
