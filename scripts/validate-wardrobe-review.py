#!/usr/bin/env python3
"""Validate actual wardrobe integration and report its limits, not art approval."""
import importlib.util
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Wardrobe/down/v1'
spec = importlib.util.spec_from_file_location('review', Path(__file__).with_name('package-wardrobe-review.py'))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
assembly = review.assembly


def equal(a, b):
    return a.size == b.size and np.array_equal(np.array(a), np.array(b))


def overlap(a, b, center=None, radius=(8, 4)):
    mask = (np.array(a)[:, :, 3] >= 128) & (np.array(b)[:, :, 3] >= 128)
    if center is not None:
        x, y = center
        local = np.zeros(mask.shape, dtype=bool)
        local[max(0, y-radius[1]):y+radius[1]+1, max(0, x-radius[0]):x+radius[0]+1] = True
        mask &= local
    y, x = np.where(mask)
    return {'pixels': len(x), 'rows': len(set(y.tolist()))}


def components(image):
    pixels = set(map(tuple, np.argwhere(np.array(image)[:, :, 3] >= 128)))
    count = 0
    while pixels:
        count += 1
        pending = [pixels.pop()]
        while pending:
            y, x = pending.pop()
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    point = y + dy, x + dx
                    if point in pixels:
                        pixels.remove(point)
                        pending.append(point)
    return count


def main():
    engine = assembly.Compositor(ROOT, OUT / 'catalog.json', OUT / 'motion.json')
    before = json.loads((OUT / 'integration-before.json').read_text())
    frozen = before['frozenFiles']
    for path, expected in {**frozen, **before['protectedImages']}.items():
        assert assembly.digest(ROOT / path) == expected, f'frozen file changed: {path}'
    old_motion = ROOT / 'Art/Templates/P1-Modular/down/v1/motion.json'
    old_data = json.loads(old_motion.read_text())
    new_data = json.loads((OUT / 'motion.json').read_text())
    changed_motion_fields = [k for k in set(old_data) | set(new_data) if old_data.get(k) != new_data.get(k)]
    assert changed_motion_fields == ['baseManifestSHA256']
    assert new_data['frames'] == old_data['frames']
    previous = json.loads((old_motion.parent / 'catalog.json').read_text())['assets']
    current = json.loads((OUT / 'catalog.json').read_text())['assets']
    assert current[1:len(previous)] == previous[1:] and len(current) == len(previous) + 2
    correction_folder = ROOT / 'Art/Templates/P1-Neutral/down/walk-r2'
    correction = json.loads((correction_folder / 'correction.json').read_text())
    corrected_base = current[0]['id']
    for n in range(9):
        base_image = engine.render(corrected_base, [], 'down', 'idle' if n == 0 else 'walk', n)
        approved = Image.open(ROOT / f'Art/Templates/P1-Neutral/down/walk-r1/frames/{n:02}.png')
        assert equal(base_image, approved), f'corrected body changes approved pixels: {n}'
    packages = []
    for identifier in engine.entries:
        data, path, _ = engine.asset(identifier)
        if data['part'] in ['outfit', 'weapon']:
            packages.append({'id': identifier, 'manifest': path.relative_to(ROOT).as_posix(),
                             'sha256': assembly.digest(path), 'slots': data['slots']})
    combinations = json.loads((OUT / 'combinations.json').read_text())['combinations']
    assert len(combinations) == 24
    independent = {}
    seams, grips = [], []
    count = 0
    for combination in combinations:
        base, selected = combination['base'], combination['assets']
        for n in range(9):
            clip = 'idle' if n == 0 else 'walk'
            parts = dict(engine.layers(base, selected, 'down', clip, n))
            body = dict(engine.layers(base, [], 'down', clip, n))
            for slot, image in parts.items():
                if slot in body:
                    assert equal(image, body[slot]), f'body switched: {slot}'
                else:
                    owner = next(identifier for identifier in selected if slot in engine.asset(identifier)[0]['slots'])
                    key = owner, slot, n
                    if key in independent:
                        assert equal(image, independent[key]), f'paired dependency: {key}'
                    else:
                        independent[key] = image
            folder = OUT / combination['folder']
            expected = engine.render(base, selected, 'down', clip, n)
            assert equal(Image.open(folder / f'{n:02}.png'), expected)
            assert assembly.digest(folder / f'{n:02}.png') == combination['frames'][f'{n:02}.png']
            strip = Image.open(folder / 'strip.png')
            assert equal(strip.crop((n * 256, 0, (n + 1) * 256, 256)), expected)
            if 'weapon.right' in parts:
                hit = overlap(parts['weapon.right'], parts['body.hand.right'])
                assert hit['pixels'] > 0, f'sword misses actual fist: {n}'
                x, y = engine.frames['down', clip, n]['sockets']['grip.right']['position']
                assert parts['weapon.right'].getpixel((x, y))[3] >= 128
                assert parts['body.hand.right'].getpixel((x, y))[3] >= 128
                hand = np.array(parts['body.hand.right'])
                mask = hand[:, :, 3] == 255
                assert np.array_equal(np.array(expected)[mask], hand[mask]), 'weapon draws over fist'
                if len(grips) < 9:
                    grips.append({'frame': n, 'position': [x, y], **hit})
            if 'outfit.torso' in parts and len(seams) < 9:
                record = {'frame': n}
                for side in ['right', 'left']:
                    pose = engine.frames['down', clip, n]
                    title_side = side.title()
                    grip_x, grip_y = pose['sockets']['grip.' + side]['position']
                    centers = {'shoulder': pose['joints']['shoulder' + title_side],
                               'cuff': pose['joints'].get('wrist' + title_side, [grip_x, grip_y - 5]),
                               'hip': pose['joints']['hip' + title_side],
                               'ankle': pose['joints']['ankle' + title_side]}
                    for label, a, b in [
                        ('shoulder', f'outfit.torso', f'outfit.sleeve.{side}'),
                        ('cuff', f'outfit.sleeve.{side}', f'body.arm.{side}'),
                        ('hip', 'outfit.hem.front', f'outfit.pants.{side}'),
                        ('ankle', f'outfit.pants.{side}', f'outfit.boot.{side}')]:
                        # Measure at the actual joint, not the whole overlapping
                        # sleeve/leg, which could hide a disconnected cuff.
                        hit = overlap(parts[a], parts[b], centers[label], (8, 8 if label == 'hip' else 4))
                        hit['joint'] = centers[label]
                        record[label + '.' + side] = hit
                seams.append(record)
            count += 1
    ora_count = 0
    clean_layers = 0
    source_count = 0
    for package in packages + [{'manifest': current[0]['manifest']}]:
        folder = (ROOT / package['manifest']).parent
        data = json.loads((folder / 'asset.json').read_text())
        if data['part'] in ['outfit', 'weapon']:
            for relative in {value for binding in data['bindings'] for value in binding['layers'].values()}:
                assert components(Image.open(folder / relative)) == 1, f'detached part fragments: {relative}'
                clean_layers += 1
            generation = json.loads((folder / 'generation.json').read_text())
            for record in generation['records']:
                assert assembly.digest(folder / record['file']) == record['sha256']
                assert assembly.digest(folder / record['promptFile']) == record['promptSHA256']
                for reference in record['references']:
                    assert assembly.digest(ROOT / reference['path']) == reference['sha256']
                source_count += 1
        for ora in sorted((folder / 'editable').glob('*.ora')):
            n = int(ora.stem)
            binding = data['bindings'][n]
            with zipfile.ZipFile(ora) as archive:
                assert archive.testzip() is None
                node = ET.fromstring(archive.read('stack.xml'))
                merged = Image.new('RGBA', (int(node.attrib['w']), int(node.attrib['h'])))
                import io
                for layer in reversed(list(node.find('stack'))):
                    merged.alpha_composite(Image.open(io.BytesIO(archive.read(layer.attrib['src']))).convert('RGBA'))
                expected = Image.new('RGBA', merged.size)
                for slot in engine.frames['down', 'idle' if n == 0 else 'walk', n]['drawOrder']:
                    if slot in binding['layers']:
                        expected.alpha_composite(Image.open(folder / binding['layers'][slot]).convert('RGBA'))
                assert equal(merged, expected)
                assert equal(Image.open(io.BytesIO(archive.read('mergedimage.png'))), expected)
                svg = ET.parse(ora.with_suffix('.svg'))
                import base64
                ns = {'svg': 'http://www.w3.org/2000/svg'}
                for group in svg.findall('svg:g', ns):
                    slot = group.attrib['id']
                    embedded = group.find('svg:image', ns).attrib['href'].split(',', 1)[1]
                    assert equal(Image.open(io.BytesIO(base64.b64decode(embedded))),
                                 Image.open(folder / binding['layers'][slot]))
                ora_count += 1
    # Rebuild the same review boards and compare every decoded GIF frame.
    base = combinations[0]['base']
    hair, face = combinations[0]['assets'][:2]
    outfit = next(p['id'] for p in packages if engine.asset(p['id'])[0]['part'] == 'outfit')
    weapon = next(p['id'] for p in packages if engine.asset(p['id'])[0]['part'] == 'weapon')
    cases = [[hair, face], [hair, face, outfit], [hair, face, outfit, weapon]]
    labels = ['COMMON BODY / EMPTY HAND', 'FORESTER / EMPTY HAND', 'FORESTER + SOCKET SWORD']
    frames = [review.board([engine.render(base, ids, 'down', 'walk', n) for ids in cases], labels) for n in range(1, 9)]
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        reference = review.normal_gif(frames, Path(tmp) / 'walk.gif')
        gif = Image.open(OUT / 'walk.gif')
        assert gif.n_frames == 8 and gif.info['loop'] == 0
        for n in range(8):
            gif.seek(n)
            assert gif.info['duration'] == 120
            assert equal(gif.convert('RGB'), reference[n].convert('RGB'))
    for record in seams:
        for label, hit in record.items():
            if label != 'frame':
                assert hit['rows'] >= 2, f'garment seam lacks 2px underlap: {record["frame"]} {label}'
    outfit_folder = engine.asset(outfit)[1].parent
    authoring = json.loads((outfit_folder / 'authoring.json').read_text())
    boot_checks = []
    for side in ['right', 'left']:
        slot = f'outfit.boot.{side}'
        reference = Image.open(outfit_folder / f'png/00/{slot}.png').convert('RGBA')
        original_recipe = authoring['poses'][0]['layers'][slot][0]
        for n in range(9):
            recipe = authoring['poses'][n]['layers'][slot][0]
            assert recipe['source'] == original_recipe['source'] == 'source/00.png'
            assert recipe['polygons'] == original_recipe['polygons']
            shift = [a - b for a, b in zip(recipe['translate'], original_recipe['translate'])]
            expected = Image.new('RGBA', (256, 256))
            expected.paste(reference, tuple(shift))
            actual = Image.open(outfit_folder / f'png/{n:02}/{slot}.png').convert('RGBA')
            assert equal(expected, actual), 'boot shape or size changed across frames'
            x, y = new_data['frames'][n]['soleMarkers'][side]
            ys, _ = np.where(np.array(actual)[:, :, 3] >= 128)
            assert int(ys.max()) == y and actual.getpixel((x, y))[3] >= 128
            boot_checks.append({'frame': n, 'side': side, 'sole': [x, y], 'translation': recipe['translate']})
    proof = {'passed': True, 'frozenFilesChecked': len(frozen), 'protectedImagesChecked': len(before['protectedImages']),
             'originalFrozenFilesChanged': [], 'runtimeAndContractChanged': [],
             'motionPoseDataIdenticalToApprovedHeadModule': True, 'motionChangedFields': changed_motion_fields,
             'commonBodyTechnicalCorrection': correction,
             'catalogOldHeadEntriesUnchanged': True, 'catalogCommonBaseReplaced': current[0],
             'catalogEntriesAdded': current[len(previous):],
             'packages': packages, 'combinations': 24, 'poses': count, 'artApproval': None}
    (OUT / 'integration-after.json').write_text(json.dumps(proof, indent=2) + '\n')
    result = {**proof, 'actualPartLayersIndependentAcrossAllSelections': True,
              'bodyLayersUnchangedInAll216Poses': True, 'editableORARecompositions': ora_count,
              'strongAlphaConnectedArtLayers': clean_layers, 'toolOutputsAndPromptReferencesVerified': source_count,
              'completeBootShapePreservedAtApprovedSoleHeight': boot_checks,
              'svgXMLValid': ora_count, 'gripAndHandOcclusion': grips, 'seamMeasurements': seams,
              'gif': {'frames': 8, 'frameMs': 120, 'cycleMs': 960, 'loop': 0, 'decodedPixelsVerified': True},
              'slowPreviewGenerated': False,
              'limits': ['Visual naturalness requires user review.', 'Down direction only; no game runtime or device test.',
                         'ORA/SVG checked structurally and by pixels; no desktop editor GUI round-trip.']}
    (OUT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'combinations': 24, 'poses': count, 'editable': ora_count,
                      'seams': seams}, indent=2))


if __name__ == '__main__':
    main()
