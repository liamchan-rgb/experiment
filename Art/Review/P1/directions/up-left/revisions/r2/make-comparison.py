#!/usr/bin/env python3
"""Lay out complete unchanged r1/r2 poses for review; no pose editing."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json

p = Path(__file__).resolve().parent
old = p.parent / 'r1'
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
pairs, records = [], []
grid = Image.new('RGB', (768, 560), 'black')
for i in range(9):
    a, b = [Image.open(d / 'frames' / f'{i:02d}.png').convert('RGBA') for d in (old, p)]
    pair = Image.new('RGB', (512, 280), 'black')
    draw = ImageDraw.Draw(pair)
    for x, label, frame in [(0, 'R1 PRIOR (NOT APPROVED)', a), (256, 'R2 REVIEW', b)]:
        draw.text((x + 6, 5), f'{i:02d} {label}', fill='white', font=font)
        pair.paste(frame, (x, 24), frame)
    pairs.append(pair)
    if i in (4, 5, 6):
        x = (i - 4) * 256
        gd = ImageDraw.Draw(grid)
        for y, label, frame in [(0, 'R1 PRIOR', a), (280, 'R2 REVIEW', b)]:
            gd.text((x + 8, y + 4), f'{label} {i:02d}', fill='white', font=font)
            grid.paste(frame, (x, y + 24), frame)
    records.append({'frame': i, 'r1SHA256': hashlib.sha256((old / 'frames' / f'{i:02d}.png').read_bytes()).hexdigest(),
                    'r2SHA256': hashlib.sha256((p / 'frames' / f'{i:02d}.png').read_bytes()).hexdigest()})
grid.save(p / 'comparison-r1-r2.png')
grid.resize((1536, 1120), Image.Resampling.NEAREST).save(p / 'comparison-r1-r2-2x.png')
palette_source = Image.new('RGB', (512, 9 * 280), 'black')
for i, pair in enumerate(pairs): palette_source.paste(pair, (0, i * 280))
palette = palette_source.quantize(colors=256)
gif_frames = [pair.resize((1024, 560), Image.Resampling.NEAREST).quantize(palette=palette, dither=Image.Dither.NONE) for pair in pairs[1:]]
for name, duration in [('r1-r2.gif', 120), ('r1-r2-slow.gif', 480)]:
    gif_frames[0].save(p / name, save_all=True, append_images=gif_frames[1:], duration=duration, loop=0, disposal=2, optimize=False)
(p / 'comparison-packing.json').write_text(json.dumps({'method': 'unchanged complete poses laid out with labels; nearest-neighbor preview only',
    'frames': records, 'r1ArtApproval': None, 'r2ArtApproval': None, 'phaseOrder': list(range(1, 9)),
    'durationsMs': {'normal': 120, 'slow': 480}}, indent=2) + '\n')
print('04–06 before/after grid and synchronized full-cycle comparisons exported')
