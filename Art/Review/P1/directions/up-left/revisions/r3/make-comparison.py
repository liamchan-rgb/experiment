#!/usr/bin/env python3
"""Lay out complete unchanged prior/candidate poses for review; no pose editing."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json

p = Path(__file__).resolve().parent
old = p.parent / 'r2'
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
pairs, records = [], []
grid = Image.new('RGB', (256, 560), 'black')
for i in range(9):
    a, b = [Image.open(d / 'frames' / f'{i:02d}.png').convert('RGBA') for d in (old, p)]
    pair = Image.new('RGB', (512, 280), 'black')
    draw = ImageDraw.Draw(pair)
    for x, label, frame in [(0, 'R2 PRIOR (NOT APPROVED)', a), (256, 'R3 REVIEW', b)]:
        draw.text((x + 6, 5), f'{i:02d} {label}', fill='white', font=font)
        pair.paste(frame, (x, 24), frame)
    pairs.append(pair)
    if i == 4:
        x = 0
        gd = ImageDraw.Draw(grid)
        for y, label, frame in [(0, 'R2 PRIOR', a), (280, 'R3 REVIEW', b)]:
            gd.text((x + 8, y + 4), f'{label} {i:02d}', fill='white', font=font)
            grid.paste(frame, (x, y + 24), frame)
    records.append({'frame': i, 'r2SHA256_PRIOR': hashlib.sha256((old / 'frames' / f'{i:02d}.png').read_bytes()).hexdigest(),
                    'r3SHA256': hashlib.sha256((p / 'frames' / f'{i:02d}.png').read_bytes()).hexdigest()})
grid.save(p / 'comparison-r2-r3.png')
grid.resize((512, 1120), Image.Resampling.NEAREST).save(p / 'comparison-r2-r3-2x.png')
palette_source = Image.new('RGB', (512, 9 * 280), 'black')
for i, pair in enumerate(pairs): palette_source.paste(pair, (0, i * 280))
palette = palette_source.quantize(colors=256)
gif_frames = [pair.resize((1024, 560), Image.Resampling.NEAREST).quantize(palette=palette, dither=Image.Dither.NONE) for pair in pairs[1:]]
for name, duration in [('r2-r3.gif', 120), ('r2-r3-slow.gif', 480)]:
    gif_frames[0].save(p / name, save_all=True, append_images=gif_frames[1:], duration=duration, loop=0, disposal=2, optimize=False)
(p / 'comparison-packing.json').write_text(json.dumps({'method': 'unchanged complete poses laid out with labels; nearest-neighbor preview only',
    'frames': records, 'r2ArtApproval_PRIOR': None, 'r3ArtApproval': None, 'phaseOrder': list(range(1, 9)),
    'durationsMs': {'normal': 120, 'slow': 480}}, indent=2) + '\n')
print('04 before/after grid and synchronized full-cycle comparisons exported')

box = (96, 160, 180, 230)
detail = Image.new('RGB', (1008, 460), 'black')
draw = ImageDraw.Draw(detail)
for x, folder, label in [(0, old, 'R2 PRIOR 04'), (504, p, 'R3 REVIEW 04')]:
    frame = Image.open(folder / 'frames/04.png').convert('RGBA').crop(box)
    rgb = Image.new('RGB', frame.size, 'black'); rgb.paste(frame, (0, 0), frame)
    detail.paste(rgb.resize((504, 420), Image.Resampling.NEAREST), (x, 40))
    draw.text((x + 8, 8), label, fill='white', font=font)
detail.save(p / 'detail-04.png')
