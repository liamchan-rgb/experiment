#!/usr/bin/env python3
"""Import the eight approved whole-pose strips without changing their pixels.

P1 stores nine real columns (idle plus eight poses). The shared distance clock
retains 24 ticks per cycle for the older P2/P3 artwork; runtime sampling maps
three ticks to each P1 pose rather than baking duplicate raster frames.
"""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / 'Art/Integration/P1-approved-gait-v1'
ASSETS = ROOT / 'Sources/Resources/Assets.xcassets'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    review = json.loads((ROOT / 'Art/Review/P1/review.json').read_text())
    footprints = json.loads((RECORDS / 'footprints.json').read_text())
    approved = {i['direction']: i for i in review['items'] if (i.get('approval') or {}).get('status') == 'approved'}
    direction_order = ['down', 'left', 'up', 'right', 'down-right', 'down-left', 'up-left', 'up-right']
    footprint_rows = {d['direction']: d for d in footprints['directions']}
    rows, provenance, hero_rig = [], [], []
    for direction in direction_order:
        item = approved[direction]
        revision = next(v for v in item['revisions'] if v['id'] == item['currentRevision'])
        source = ROOT / 'Art/Review/P1' / revision['strip']
        expected = item['approval']['artifacts']['strip.png']
        assert sha(source) == expected, f'Approved source changed: {direction}'
        strip = Image.open(source).convert('RGBA')
        assert strip.size == (9 * 256, 256)
        assert len({strip.crop((i * 256, 0, (i + 1) * 256, 256)).tobytes() for i in range(1, 9)}) == 8
        rows.append(strip)
        points = footprint_rows[direction]
        assert points['revision'] == item['currentRevision'] and len(points['poses']) == 9
        poses = []
        for column in range(25):
            pose = 0 if column == 0 else 1 + (column - 1) * 8 // 24
            feet = points['poses'][pose]['solePixels']
            assert len(feet) == 2
            poses.append({'feet': [[x / 256, (y + lift * math.cos(math.pi / 6)) / 256, lift / 256]
                                   for x, y, lift in feet]})
        hero_rig.append(poses)
        provenance.append({'direction': direction, 'revision': item['currentRevision'],
                           'source': str(source.relative_to(ROOT)), 'sha256': expected})
    outputs = {}
    for group, suffix in enumerate(['Directions', 'Diagonals']):
        atlas = Image.new('RGBA', (9 * 256, 4 * 256))
        for row in range(4):
            atlas.paste(rows[group * 4 + row], (0, row * 256))
        destination = ASSETS / f'Hero1{suffix}.imageset' / f'Hero1{suffix}.png'
        atlas.save(destination)
        decoded = Image.open(destination).convert('RGBA')
        for row in range(4):
            assert decoded.crop((0, row * 256, 9 * 256, (row + 1) * 256)).tobytes() == rows[group * 4 + row].tobytes()
        outputs[str(destination.relative_to(ROOT))] = sha(destination)
    rig_path = ROOT / 'Sources/Resources/hero-gait.json'
    rig = json.loads(rig_path.read_text())
    rig['authoredFrames'] = [8, 24, 24]
    rig['reviewFrameMs'] = 120
    rig['heroes'][0] = hero_rig
    rig_path.write_text(json.dumps(rig, separators=(',', ':')) + '\n')
    outputs[str(rig_path.relative_to(ROOT))] = sha(rig_path)
    record = {'format': 1, 'status': 'imported-for-demo-device-review', 'date': '2026-10-21',
              'directions': provenance, 'authoredWalkPoses': 8, 'idlePosesPerDirection': 1,
              'frameMs': 120, 'cycleMs': 960, 'rasterColumns': 9, 'distanceClockTicks': 24,
              'pixelChangesToApprovedArtwork': 0, 'interpolatedPoses': 0,
              'footprints': 'footprints.json', 'outputs': outputs,
              'physicalDeviceVisualApproval': None}
    (RECORDS / 'integration.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Imported eight approved P1 directions: nine columns per atlas, original RGBA preserved.')


if __name__ == '__main__':
    main()
