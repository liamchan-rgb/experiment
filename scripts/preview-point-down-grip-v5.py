#!/usr/bin/env python3
"""Build the v5 single-frame continuous-arm grip study from its recorded inputs."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Wardrobe/down/v5'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cfg = json.loads((OUT / 'registration.json').read_text())
    source = Image.open(OUT / 'source/guide-with-completed-grip.png').convert('RGBA')
    base = Image.open(OUT / 'references/00-without-grip.png').convert('RGBA')
    if source.size != tuple(cfg['sourceCanvas']) or base.size != tuple(cfg['worldCanvas']):
        raise ValueError('source or base canvas differs from the recorded registration')

    # Invert the fixed sourceToWorld mapping from the current motion manifest.
    local = source.transform(
        tuple(cfg['worldCanvas']), Image.Transform.AFFINE,
        (6.25, 0, -156.25, 0, 6.25, -237.5),
        resample=Image.Resampling.NEAREST)
    rect = tuple(cfg['overlayRect'])
    patch = local.crop(rect)
    if patch.getchannel('A').getbbox() is None:
        raise ValueError('registered hand and weapon crop is empty')
    patch.save(OUT / 'parts/grip/registered-overlay.png')

    result = base.copy()
    result.alpha_composite(patch, tuple(cfg['overlayOrigin']))
    result.save(OUT / '00.png')

    before = np.asarray(base)
    after = np.asarray(result)
    x0, y0, x1, y1 = rect
    changed = np.any(before != after, axis=2)
    outside = changed.copy()
    outside[y0:y1, x0:x1] = False
    if outside.any():
        raise AssertionError('pixels outside the declared grip overlay changed')

    board = Image.new('RGB', (840, 650), '#d6e1dd')
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    draw.text((25, 15), '00 / CONTINUOUS ARM / FORWARD GRIP / POINT DOWN', font=font, fill='#29494a')
    full = result.crop((74, 66, 176, 226)).resize((306, 480), Image.Resampling.NEAREST)
    board.paste(full, (20, 70), full)
    detail = result.crop((84, 150, 118, 208)).resize((360, 580), Image.Resampling.NEAREST)
    board.paste(detail, (440, 70), detail)
    board.save(OUT / 'review.png')

    record = {
        'kind': 'single-idle-pose-art-study',
        'direction': 'down',
        'clip': 'idle',
        'frame': 0,
        'status': 'awaiting_user_art_review',
        'artApproval': None,
        'reviewImage': 'review.png',
        'baseImage': 'references/00-without-grip.png',
        'generatedGuide': 'source/guide-with-completed-grip.png',
        'registeredOverlay': 'parts/grip/registered-overlay.png',
        'overlayRect': list(rect),
        'outsideOverlayPixelsUnchanged': True,
        'sourceSHA256': digest(OUT / 'source/guide-with-completed-grip.png'),
        'baseSHA256': digest(OUT / 'references/00-without-grip.png'),
        'overlaySHA256': digest(OUT / 'parts/grip/registered-overlay.png'),
        'reviewSHA256': digest(OUT / 'review.png'),
        'assembledSHA256': digest(OUT / '00.png'),
        'animationGenerated': False,
        'productionManifestGenerated': False,
        'limits': [
            'One idle pose only; no nine-pose or animation validation.',
            'The forearm, hand and sword are one registered overlay for this visual study, not yet independently swappable parts.',
            'Visual grip and wrist continuity were reviewed at full pose and enlarged detail; this does not constitute user approval.'
        ]
    }
    (OUT / 'validation.json').write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
