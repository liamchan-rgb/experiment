#!/usr/bin/env python3
"""Render all registered down-facing loadouts and record coverage evidence."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CANDIDATE = ROOT / 'Art/Templates/P1-Wardrobe/down/v8-back-carry'
BASE = 'p1-neutral-down-walk-r6-relaxed-arms'
OUTFIT = 'p1-outfit-forester-cover-v2'
SWORD = 'p1-weapon-short-sword-back-v1'
HAIR = {'chestnut': 'p1-hair-chestnut-v1', 'silver': 'p1-hair-silver-v1', 'teal': 'p1-hair-teal-crop-v1'}
FACE = {'blue': 'p1-face-blue-v1', 'amber': 'p1-face-amber-v1'}
BACKGROUND = '#17372c'
BOB = [0, 0, 2, -1, -2, 0, 2, -1, -2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(image, scale=1):
    bg = Image.new('RGBA', image.size, BACKGROUND)
    bg.alpha_composite(image)
    return bg.convert('RGB').resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)


def gif(images, path):
    frames = [flatten(im, 2) for im in images]
    atlas = Image.new('RGB', (512 * len(frames), 512))
    for i, frame in enumerate(frames):
        atlas.paste(frame, (i * 512, 0))
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2)


def main():
    spec = importlib.util.spec_from_file_location('parts', ROOT / 'scripts/compose-character-parts.py')
    parts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parts)
    compositor = parts.Compositor(ROOT, CANDIDATE / 'catalog.json', CANDIDATE / 'motion.json')
    records, coverage, renders = [], [], {}
    for hair, face, dressed, carried in itertools.product(HAIR, FACE, [False, True], [False, True]):
        name = f'{hair}__{face}__{"forester" if dressed else "plain"}__{"back" if carried else "empty"}'
        selected = [HAIR[hair], FACE[face]] + ([OUTFIT] if dressed else []) + ([SWORD] if carried else [])
        directory = OUT / 'combinations' / name
        directory.mkdir(parents=True, exist_ok=True)
        images = []
        for frame in range(9):
            clip = 'idle' if frame == 0 else 'walk'
            layers = compositor.layers(BASE, selected, 'down', clip, frame)
            image = compositor.render(BASE, selected, 'down', clip, frame)
            path = directory / f'{clip}-{frame:02}.png'
            image.save(path)
            records.append({'combination': name, 'frame': frame, 'path': str(path.relative_to(OUT)), 'sha256': digest(path)})
            images.append(image)
            if dressed:
                for slot in ['body.arm.right', 'body.arm.left', 'body.leg.right', 'body.leg.left', 'body.torso']:
                    index = next(i for i, (key, _) in enumerate(layers) if key == slot)
                    contribution = np.array(layers[index][1].getchannel('A'), dtype=float) / 255
                    for _, above in layers[index+1:]:
                        contribution *= 1 - np.array(above.getchannel('A'), dtype=float) / 255
                    if slot == 'body.torso':
                        contribution[:136+BOB[frame]] = 0  # neck/collar intentionally visible
                    coverage.append({'combination': name, 'frame': frame, 'slot': slot, 'pixelsAbove5Percent': int(np.sum(contribution > .05)), 'maxContribution': float(contribution.max())})
        renders[(hair, face, dressed, carried)] = images
        gif(images[1:], directory / 'walk-120ms.gif')
    current = renders[('chestnut', 'blue', True, True)]
    board = Image.new('RGB', (768, 768), BACKGROUND)
    draw = ImageDraw.Draw(board)
    for i, image in enumerate(current):
        x, y = i % 3 * 256, i // 3 * 256
        board.paste(flatten(image), (x, y))
        draw.text((x+5, y+5), f'{i:02}', fill='white')
    board.save(OUT / 'nine-poses-fullbody-1x.png')
    board.resize((1536, 1536), Image.Resampling.NEAREST).save(OUT / 'nine-poses-fullbody-2x.png')
    flatten(current[0]).save(OUT / 'idle-review-1x.png')
    flatten(current[0], 2).save(OUT / 'idle-review-2x.png')
    gif(current[1:], OUT / 'walk-120ms.gif')
    head_board = Image.new('RGB', (768, 512), BACKGROUND)
    for i, (hair, face) in enumerate(itertools.product(HAIR, FACE)):
        head_board.paste(flatten(renders[(hair, face, True, True)][0]), (i%3*256, i//3*256))
    head_board.resize((1536, 1024), Image.Resampling.NEAREST).save(OUT / 'head-combinations-2x.png')
    toggle = Image.new('RGB', (512, 512), BACKGROUND)
    for i, (dressed, carried) in enumerate(itertools.product([False, True], [False, True])):
        toggle.paste(flatten(renders[('chestnut', 'blue', dressed, carried)][0]), (i%2*256, i//2*256))
    toggle.resize((1024, 1024), Image.Resampling.NEAREST).save(OUT / 'outfit-weapon-toggle-2x.png')
    differences = []
    for hair, face, dressed, frame in itertools.product(HAIR, FACE, [False, True], range(9)):
        empty = np.array(renders[(hair, face, dressed, False)][frame])
        carried = np.array(renders[(hair, face, dressed, True)][frame])
        selected = [HAIR[hair], FACE[face]] + ([OUTFIT] if dressed else []) + [SWORD]
        layers = dict(compositor.layers(BASE, selected, 'down', 'idle' if frame == 0 else 'walk', frame))
        changed = np.any(empty != carried, axis=2)
        weapon = np.array(layers['weapon.back'].getchannel('A')) > 0
        hands = (np.array(layers['body.hand.right'].getchannel('A')) >= 250) | (np.array(layers['body.hand.left'].getchannel('A')) >= 250)
        differences.append({'hair': hair, 'face': face, 'dressed': dressed, 'frame': frame, 'outsideWeapon': int(np.sum(changed & ~weapon)), 'withinOpaqueHands': int(np.sum(changed & hands))})
    report = {'status': 'offline evidence; internal visual review required', 'artApproval': None, 'combinations': 24, 'poses': len(records), 'records': records, 'catalogSHA256': digest(CANDIDATE/'catalog.json'), 'motionSHA256': digest(CANDIDATE/'motion.json'), 'base': BASE, 'coverage': coverage, 'weaponToggleChecks': differences, 'gifFrames': 8, 'gifDurationMs': 120, 'scope': 'down only; no simulator/device/runtime/package', 'coverageAllowance': 'neck/collar above y136 + body bob excluded; other torso, arm and leg contributions measured after actual layer compositing'}
    (OUT / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    failures = [c for c in coverage if c['pixelsAbove5Percent']]
    toggle_failures = [d for d in differences if d['outsideWeapon'] or d['withinOpaqueHands']]
    print(json.dumps({'combinations': 24, 'poses': len(records), 'bodyCoverageFailuresAbove5Percent': failures, 'weaponToggleFailures': toggle_failures}, indent=2))
    if failures or toggle_failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
