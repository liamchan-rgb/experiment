#!/usr/bin/env python3
"""Slice an already drawn review sheet and package unchanged poses for review.

This does not draw, interpolate, deform limbs, or synthesize additional poses.
A sheet uses a common transform; individual drawings register by head landmarks
or an explicit whole-pose silhouette/sole-envelope profile.
"""
import argparse
import hashlib
import json
import math
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def bounds(image):
    return image.getchannel('A').point(lambda a: 255 if a > 32 else 0).getbbox()


def head_landmarks(image):
    """Find this blue-scarfed P1's head before scaling a complete drawing."""
    a = np.array(image)
    bb = bounds(image)
    r, g, b = [a[:, :, k].astype(float) for k in range(3)]
    blue = (b > r * 1.12) & (b > g * .95) & (g > 30) & (a[:, :, 3] > 64)
    counts = blue.sum(axis=1)
    candidates = [y for y in range(bb[1] + int((bb[3] - bb[1]) * .22),
                                    bb[1] + int((bb[3] - bb[1]) * .55))
                  if counts[y] > (bb[2] - bb[0]) * .25]
    if not candidates:
        raise ValueError('Cannot register P1 head: inspect the blue scarf boundary')
    neck = candidates[0]
    head = a[bb[1]:neck, :, 3] > 64
    xs = np.where(head.any(axis=0))[0]
    return {'top': bb[1], 'height': neck - bb[1], 'centerX': float(xs.min() + xs.max()) / 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--columns', type=int, default=3)
    parser.add_argument('--rows', type=int, default=3)
    parser.add_argument('--revision-label', default='R1',
                        help='Caption for the candidate row in the baseline comparison')
    parser.add_argument('--registration-profile', type=Path,
                        help='Optional whole-pose silhouette heights and common sole-envelope line')
    args = parser.parse_args()
    profile = json.loads(args.registration_profile.read_text()) if args.registration_profile else None
    baseline = Image.open(args.baseline).convert('RGBA')
    cells = []
    if args.source.is_dir():
        source_paths = sorted(args.source.glob('[0-9][0-9].png'))
        if len(source_paths) != args.columns * args.rows:
            raise ValueError('Expected one separately drawn source for each numbered pose')
        cells = [Image.open(path).convert('RGBA') for path in source_paths]
        source_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
    else:
        source = Image.open(args.source).convert('RGBA')
        cell_w = math.ceil(source.width / args.columns)
        cell_h = math.ceil(source.height / args.rows)
        source_hashes = {args.source.name: hashlib.sha256(args.source.read_bytes()).hexdigest()}
        for row in range(args.rows):
            for column in range(args.columns):
                box = (column * source.width // args.columns,
                       row * source.height // args.rows,
                       (column + 1) * source.width // args.columns,
                       (row + 1) * source.height // args.rows)
                tile = Image.new('RGBA', (cell_w, cell_h))
                tile.paste(source.crop(box), (0, 0))
                cells.append(tile)
    if profile:
        if not args.source.is_dir() or len(profile['silhouetteHeights']) != len(cells):
            raise ValueError('Registration profile requires one height per separately drawn pose')
        if any(height <= 0 for height in profile['silhouetteHeights']):
            raise ValueError('Registration heights must be positive')
    for index, tile in enumerate(cells):
        if tile.getchannel('A').getextrema()[0] != 0:
            raise ValueError('Expected the artist-supplied transparent background')
        box_alpha = bounds(tile)
        if not box_alpha:
            raise ValueError(f'Empty source pose {index}')
        if min(box_alpha[0], box_alpha[1], tile.width - box_alpha[2], tile.height - box_alpha[3]) < 2:
            raise ValueError(f'Pose touches source edge {index}; inspect clipping')
    old_idle = baseline.crop((0, 0, 256, 256))
    old_bounds, idle_bounds = bounds(old_idle), bounds(cells[0])
    ratio = (old_bounds[3] - old_bounds[1]) / (idle_bounds[3] - idle_bounds[1])
    target_head = head_landmarks(old_idle)
    if args.source.is_dir():
        target_head['height'] = head_landmarks(cells[0])['height'] * ratio
    args.output.mkdir(parents=True, exist_ok=True)
    frame_dir = args.output / 'frames'
    frame_dir.mkdir(exist_ok=True)
    frames, frame_records = [], []
    for index, tile in enumerate(cells):
        if args.source.is_dir():
            head = head_landmarks(tile)
            ratio = target_head['height'] / head['height']
            head_x, head_y = head['centerX'], head['top']
            sway = [0, -1, -1, -1, 0, 1, 1, 1, 0][index]
            bob = [0, 0, 2, 0, -1, 0, 2, 0, -1][index]
            if profile:
                source_box = bounds(tile)
                ratio = profile['silhouetteHeights'][index] / (source_box[3] - source_box[1])
                sway = bob = 0
        else:
            head_x = (idle_bounds[0] + idle_bounds[2]) / 2
            head_y = idle_bounds[1]
            sway = bob = 0
        target = (round(tile.width * ratio), round(tile.height * ratio))
        scale_x, scale_y = target[0] / tile.width, target[1] / tile.height
        anchor_x = target_head['centerX'] if args.source.is_dir() else (old_bounds[0] + old_bounds[2]) / 2
        anchor_y = target_head['top'] if args.source.is_dir() else old_bounds[1]
        offset = (round(anchor_x + sway - head_x * scale_x), round(anchor_y + bob - head_y * scale_y))
        if profile:
            offset = (offset[0], round(profile['soleEnvelopeY'] - source_box[3] * scale_y))
        tile = tile.resize(target, Image.Resampling.NEAREST)
        bb = bounds(tile)
        placed = (bb[0] + offset[0], bb[1] + offset[1], bb[2] + offset[0], bb[3] + offset[1])
        if min(placed[:2]) < 0 or max(placed[2:]) > 256:
            raise ValueError(f'Common packing transform would clip pose {index}')
        frame = Image.new('RGBA', (256, 256))
        frame.paste(tile, offset)
        frame.save(frame_dir / f'{index:02d}.png')
        frames.append(frame)
        frame_records.append({'frame': index, 'alphaBounds': list(bounds(frame)),
                              'wholePoseRegistration': {'scaleX': scale_x, 'scaleY': scale_y, 'offset': list(offset)},
                              'sha256': hashlib.sha256(frame.tobytes()).hexdigest()})
    if len({row['sha256'] for row in frame_records[1:]}) != len(frames) - 1:
        raise ValueError('Duplicate complete walking poses')
    strip = Image.new('RGBA', (256 * len(frames), 256))
    review = Image.new('RGB', (args.columns * 256, args.rows * 280), 'black')
    draw = ImageDraw.Draw(review)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    for index, frame in enumerate(frames):
        strip.paste(frame, (index * 256, 0))
        x, y = index % args.columns * 256, index // args.columns * 280
        draw.text((x + 10, y + 3), '00 IDLE' if index == 0 else f'{index:02d}', fill='white', font=font)
        review.paste(frame, (x, y + 24), frame)
    strip.save(args.output / 'strip.png')
    review.save(args.output / 'review.png')
    review.resize((review.width * 2, review.height * 2), Image.Resampling.NEAREST).save(args.output / 'review-2x.png')
    palette = strip.convert('RGB').quantize(colors=256)
    gif_frames = []
    for frame in frames[1:]:
        rgb = Image.new('RGB', (256, 256), 'black')
        rgb.paste(frame, (0, 0), frame)
        rgb = rgb.resize((512, 512), Image.Resampling.NEAREST)
        gif_frames.append(rgb.quantize(palette=palette, dither=Image.Dither.NONE))
    for filename, duration in [('walk.gif', 120), ('walk-slow.gif', 480)]:
        gif_frames[0].save(args.output / filename, save_all=True, append_images=gif_frames[1:],
                           duration=duration, loop=0, disposal=2, optimize=False)
        with Image.open(args.output / filename) as decoded:
            assert decoded.n_frames == len(frames) - 1
    comparison = Image.new('RGB', (1280, 560), 'black')
    draw = ImageDraw.Draw(comparison)
    for column, (old_index, new_index) in enumerate(zip([0, 1, 7, 13, 19], [0, 1, 3, 5, 7])):
        x = column * 256
        old_frame = baseline.crop((old_index * 256, 0, (old_index + 1) * 256, 256))
        draw.text((x + 10, 3), f'BASE {old_index:02d}', fill='white', font=font)
        comparison.paste(old_frame, (x, 24), old_frame)
        draw.text((x + 10, 283), f'{args.revision_label} {new_index:02d}', fill='white', font=font)
        comparison.paste(frames[new_index], (x, 304), frames[new_index])
    comparison.save(args.output / 'comparison.png')
    report = {'format': 1, 'source': args.source.name, 'sourceSHA256': source_hashes,
              'sourceDimensions': [list(tile.size) for tile in cells], 'reviewGrid': [args.columns, args.rows],
              'cell': 256, 'idleFrames': 1, 'walkingFrames': len(frames) - 1,
              'packing': 'whole-pose nearest-neighbor registration by head landmarks for separately drawn poses; no limb edits, foot scaling or interpolation',
              'durationsMilliseconds': {'normal': 120, 'slow': 480},
              'frames': frame_records, 'artApproval': None}
    if profile:
        report['packing'] = 'uniform whole-pose scaling to declared silhouette heights and sole-envelope alignment; no limb edits, foot scaling or interpolation'
        report['registrationProfile'] = {
            'file': args.registration_profile.name,
            'sha256': hashlib.sha256(args.registration_profile.read_bytes()).hexdigest(),
            'soleEnvelopeY': profile['soleEnvelopeY'],
            'silhouetteHeights': profile['silhouetteHeights']}
    (args.output / 'packing.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ['walkingFrames', 'packing', 'artApproval']}))


if __name__ == '__main__':
    main()
