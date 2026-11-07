#!/usr/bin/env python3
"""Verify the authored left-body package; this does not approve its artwork."""
import hashlib
import importlib.util
import io
import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[4]
BODY = ROOT/'Art/Templates/P1-Neutral/left/walk-r3-complete-transitions'
REVIEW = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    compositor = module('compositor', ROOT/'scripts/compose-character-parts.py')
    exporter = module('exporter', ROOT/'scripts/export-neutral-left-walk.py')
    engine = compositor.Compositor(ROOT, BODY/'catalog.json', BODY/'motion.json')
    config = json.loads((BODY/'authoring.json').read_text())
    motion = json.loads((BODY/'motion.json').read_text())
    manifest = json.loads((BODY/'asset.json').read_text())
    expected_keys = {('idle', 0)} | {('walk', n) for n in range(1, 9)}
    expected_keys |= {(clip, n) for clip in ['walk-start', 'walk-stop'] for n in [1, 2]}
    assert {(f['clip'], f['frame']) for f in motion['frames']} == expected_keys
    assert {(f['clip'], f['frame']) for f in manifest['bindings']} == expected_keys
    source_head = Image.open(BODY/'layers/00/head.base.png').convert('RGBA').crop((76, 61, 172, 157))
    reports = []
    for i, frame in enumerate(motion['frames']):
        path = BODY/f'frames/{i:02}.png'
        actual = np.array(Image.open(path).convert('RGBA'))
        rendered = np.array(engine.render(config['id'], [], 'left', frame['clip'], frame['frame']))
        assert np.array_equal(actual, rendered), ('compositor mismatch', i)
        if i < 9:
            approved = np.array(Image.open(BODY/f'source/approved-r2-frames/{i:02}.png').convert('RGBA'))
            assert np.array_equal(actual, approved), ('approved pose changed', i)
        local = np.array(compositor.place(source_head, frame['headToCanvas'], (256, 256)))
        head = np.array(Image.open(BODY/f'layers/{i:02}/head.base.png').convert('RGBA'))
        visible = (local[:, :, 3] > 0) | (head[:, :, 3] > 0)
        assert not (np.any(local != head, axis=2) & visible).any(), ('head transform mismatch', i)
        components, _ = label(actual[:, :, 3] >= 128, np.ones((3, 3)))
        assert components[110, 124] != 0 and components[110, 124] == components[145, 119], ('neck disconnected', i)
        for side, point in frame['soleMarkers'].items():
            sole = Image.open(BODY/f'layers/{i:02}/body.leg.{side}.png').getchannel('A')
            assert sole.getpixel(tuple(point)) >= 128, ('sole outside leg', i, side, point)
        with zipfile.ZipFile(BODY/f'editable/{i:02}.ora') as archive:
            assert archive.getinfo('mimetype').compress_type == zipfile.ZIP_STORED
            merged = np.array(Image.open(io.BytesIO(archive.read('mergedimage.png'))).convert('RGBA'))
            assert np.array_equal(actual, merged), ('ORA mismatch', i)
        reports.append({'storageIndex': i, 'clip': frame['clip'], 'frame': frame['frame'],
                        'actualCompositorDifferencePixels': 0, 'headAttachmentDifferencePixels': 0,
                        'headNeckConnected': True, 'soleMarkersOnLeg': 2,
                        'approvedR2VisibleRGBAPreserved': True if i < 9 else None})
    output_files = [p for directory in ['layers', 'frames', 'editable']
                    for p in (BODY/directory).rglob('*') if p.is_file()]
    before = {p: sha(p) for p in output_files}
    exporter.export(BODY, REVIEW)
    assert all(sha(p) == digest for p, digest in before.items()), 'nonreproducible art export'
    gif_checks = []
    for name, count, durations in [('walk-120ms.gif', 8, [120]*8),
                                   ('start-stop-120ms.gif', 22, [480]+[120]*20+[480])]:
        image = Image.open(REVIEW/name)
        assert image.n_frames == count and image.info['loop'] == 0
        actual_durations = []
        for i in range(image.n_frames):
            image.seek(i)
            actual_durations.append(image.info['duration'])
        assert actual_durations == durations, (name, actual_durations)
        gif_checks.append({'path': name, 'frames': count, 'durationsMs': actual_durations, 'sha256': sha(REVIEW/name)})
    result = {'status': 'technical checks passed; visual approval remains separate', 'artApproval': None,
              'poseChecks': reports, 'reexportFiles': len(output_files), 'reexportByteDifferences': 0,
              'gifChecks': gif_checks,
              'limits': ['left direction only', 'start path idle00 to walk01; stop path walk08 to idle00',
                         'no arbitrary walk-phase interruption', 'no apparel or runtime/device checks']}
    (REVIEW/'transition-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'verifiedPoses': len(reports), 'reexportFiles': len(output_files), 'gifFiles': len(gif_checks)}))


if __name__ == '__main__':
    main()
