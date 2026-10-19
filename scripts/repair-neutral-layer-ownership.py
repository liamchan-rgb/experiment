#!/usr/bin/env python3
"""Reassign a passing-pose overlap to its anatomical leg, preserving the image.

This is a common base revision for every wardrobe selection, including naked
previews. It neither redraws a pose nor supplies an appearance-specific patch.
"""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Art/Templates/P1-Neutral/down/walk-r1'
OUT = ROOT / 'Art/Templates/P1-Neutral/down/walk-r2'
spec = importlib.util.spec_from_file_location('wardrobe_export', Path(__file__).with_name('export-wardrobe-part.py'))
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((SOURCE / 'asset.json').read_text())
    data['id'] = 'p1-neutral-down-walk-r2'
    data['version'] = '1.0.1'
    for n in range(9):
        folder = OUT / 'layers' / f'{n:02}'
        folder.mkdir(parents=True, exist_ok=True)
        for image in (SOURCE / 'layers' / f'{n:02}').glob('*.png'):
            shutil.copyfile(image, folder / image.name)
    # Only the stray posterior-calf overlap is moved; the foreground foot
    # remains in the anatomical right-leg layer.
    polygon = [[129, 193], [135, 193], [135, 210], [127, 210], [127, 202], [129, 202]]
    mask = Image.new('L', (256, 256))
    ImageDraw.Draw(mask).polygon([tuple(point) for point in polygon], fill=255)
    selected = np.array(mask) > 0
    right_path = OUT / 'layers/07/body.leg.right.png'
    left_path = OUT / 'layers/07/body.leg.left.png'
    right = np.array(Image.open(right_path))
    patch = right.copy()
    patch[~selected] = 0
    right[selected] = 0
    left = Image.open(left_path).convert('RGBA')
    left.alpha_composite(Image.fromarray(patch))
    left.save(left_path)
    Image.fromarray(right).save(right_path)
    motion = json.loads((SOURCE / 'motion.json').read_text())
    (OUT / 'editable').mkdir(exist_ok=True)
    (OUT / 'frames').mkdir(exist_ok=True)
    frame_hashes = {}
    for n in range(9):
        binding = data['bindings'][n]
        images = {slot: Image.open(OUT / relative).convert('RGBA') for slot, relative in binding['layers'].items()}
        ordered = {slot: images[slot] for slot in motion['frames'][n]['drawOrder'] if slot in images}
        actual = exporter.editable(OUT / 'editable', f'{n:02}', ordered)
        expected = Image.open(SOURCE / f'frames/{n:02}.png').convert('RGBA')
        assert np.array_equal(np.array(actual), np.array(expected)), f'body pixels changed in {n}'
        # Preserve the already-approved PNG bytes, after actual layer equality.
        shutil.copyfile(SOURCE / f'frames/{n:02}.png', OUT / f'frames/{n:02}.png')
        frame_hashes[f'frames/{n:02}.png'] = digest(OUT / f'frames/{n:02}.png')
    (OUT / 'asset.json').write_text(json.dumps(data, indent=2) + '\n')
    changed = [f'layers/{n:02}/{slot}.png' for n in range(9) for slot in data['slots']
               if digest(OUT / f'layers/{n:02}/{slot}.png') != digest(SOURCE / f'layers/{n:02}/{slot}.png')]
    assert sorted(changed) == ['layers/07/body.leg.left.png', 'layers/07/body.leg.right.png']
    record = {'kind': 'technical-layer-ownership-correction', 'source': SOURCE.relative_to(ROOT).as_posix(),
              'sourceManifestSHA256': digest(SOURCE / 'asset.json'), 'date': '2026-10-19',
              'reason': 'Frame07 right foreground layer included a posterior left-calf fragment; it covered long trousers.',
              'reassignedPolygon': polygon, 'from': 'body.leg.right', 'to': 'body.leg.left',
              'movedAlphaPixels': int(np.count_nonzero(patch[:, :, 3])), 'changedLayers': changed,
              'approvedCompositePixelEquality': True, 'approvedPNGBytesPreserved': frame_hashes,
              'scope': 'One common base for all new combinations, never selected by appearance ID.',
              'artApproval': None, 'approvalNote': 'Original composed body artwork remains exactly as approved; layer reassignment is technical, not a new user art approval.'}
    (OUT / 'correction.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'correctedLayers': changed, 'movedPixels': record['movedAlphaPixels'], 'posesPixelIdentical': 9}))


if __name__ == '__main__':
    main()
