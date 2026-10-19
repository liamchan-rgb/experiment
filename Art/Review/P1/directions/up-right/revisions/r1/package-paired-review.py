#!/usr/bin/env python3
"""Compose unchanged approved-left/candidate-right poses for synchronized review."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def pair_frame(left, right, index, font):
    pair = Image.new('RGB', (512, 280), 'black')
    draw = ImageDraw.Draw(pair)
    draw.text((8, 5), f'{index:02d} UP-LEFT r6 APPROVED', fill='white', font=font)
    draw.text((264, 5), f'{index:02d} UP-RIGHT r1 REVIEW', fill='white', font=font)
    pair.paste(left, (0, 24), left)
    pair.paste(right, (256, 24), right)
    return pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--left', type=Path, required=True)
    parser.add_argument('--right', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    timings = json.loads((args.left / 'packing.json').read_text())['durationsMilliseconds']
    if timings != json.loads((args.right / 'packing.json').read_text())['durationsMilliseconds']:
        raise ValueError('Left/right timing must match before synchronous review')
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
    pairs, records = [], []
    for index in range(9):
        paths = [directory / 'frames' / f'{index:02d}.png' for directory in (args.left, args.right)]
        left, right = [Image.open(path).convert('RGBA') for path in paths]
        if left.size != (256, 256) or right.size != (256, 256):
            raise ValueError('Expected 256 x 256 complete review poses')
        pairs.append(pair_frame(left, right, index, font))
        records.append({'index': index, 'leftPNG': str(paths[0]), 'rightPNG': str(paths[1]),
                        'leftSHA256': hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                        'rightSHA256': hashlib.sha256(paths[1].read_bytes()).hexdigest()})
    args.output.mkdir(parents=True, exist_ok=True)
    grid = Image.new('RGB', (1536, 840), 'black')
    palette_source = Image.new('RGB', (512, 280 * 9), 'black')
    for index, pair in enumerate(pairs):
        grid.paste(pair, ((index % 3) * 512, (index // 3) * 280))
        palette_source.paste(pair, (0, index * 280))
    grid.save(args.output / 'left-right-review.png')
    grid.resize((3072, 1680), Image.Resampling.NEAREST).save(args.output / 'left-right-review-2x.png')
    palette = palette_source.quantize(colors=256)
    gifs = [pair.resize((1024, 560), Image.Resampling.NEAREST).quantize(
        palette=palette, dither=Image.Dither.NONE) for pair in pairs[1:]]
    for name, duration in [('left-right.gif', timings['normal']),
                           ('left-right-slow.gif', timings['slow'])]:
        gifs[0].save(args.output / name, save_all=True, append_images=gifs[1:],
                     duration=duration, loop=0, disposal=2, optimize=False)
        with Image.open(args.output / name) as decoded:
            assert decoded.n_frames == 8
    report = {'format': 1, 'method': 'unchanged complete poses side by side; labels and nearest-neighbor enlargement only',
              'phaseMapping': 'same approved source pose index reflected to opposite camera side; equipment anatomical side still requires layered template',
              'leftReference': str(args.left), 'rightCandidate': str(args.right),
              'idleFrame': 0, 'walkingFrames': list(range(1, 9)),
              'durationsMilliseconds': timings, 'pairs': records, 'rightArtApproval': None}
    (args.output / 'pairing.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Paired numbered grid and synchronized 8-frame loops exported')


if __name__ == '__main__':
    main()
