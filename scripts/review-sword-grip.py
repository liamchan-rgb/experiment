#!/usr/bin/env python3
"""Render and validate the common closed fist / compact-hilt revision."""
import importlib.util
import itertools
import json
import io
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Wardrobe/down/v2'
OLD = OUT.parent / 'v1'
spec = importlib.util.spec_from_file_location('review', Path(__file__).with_name('package-wardrobe-review.py'))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
assembly = review.assembly
BASE = 'p1-neutral-down-walk-r3'
OLD_BASE = 'p1-neutral-down-walk-r2'
WEAPON = 'p1-weapon-short-sword-v2'
OLD_WEAPON = 'p1-weapon-short-sword-v1'
OUTFIT = 'p1-outfit-forester-v1'
HAIR = 'p1-hair-chestnut-v1'
FACE = 'p1-face-blue-v1'


def equal(a, b):
    return a.size == b.size and np.array_equal(np.array(a), np.array(b))


def closeup(sprite, grip, scale=6):
    x, y = grip
    return sprite.crop((x-14, y-16, x+16, y+20)).resize((30*scale, 36*scale), Image.Resampling.NEAREST)


def board(before, after, grip):
    out = Image.new('RGB', (560, 710), '#d6e1dd')
    draw = ImageDraw.Draw(out)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    for i, (sprite, label) in enumerate([(before, 'BEFORE'), (after, 'CLOSED GRIP / r2')]):
        x = i * 280
        draw.text((x+20, 15), label, fill='#29494a', font=font)
        full = sprite.crop((80, 66, 176, 226)).resize((192, 320), Image.Resampling.NEAREST)
        out.paste(full, (x+44, 55), full)
        draw.text((x+20, 400), 'THUMB / FINGERS / GUARD', fill='#476567', font=small)
        detail = closeup(sprite, grip)
        out.paste(detail, (x+50, 445), detail)
    return out


def minimum_distance(a, b):
    ay, ax = np.where(a)
    by, bx = np.where(b)
    assert len(ax) and len(bx)
    return int(np.max(np.abs(np.stack([ay, ax], axis=1)[:, None, :] -
                             np.stack([by, bx], axis=1)[None, :, :]), axis=2).min())


def components(image):
    points = set(map(tuple, np.argwhere(np.array(image)[:, :, 3] >= 128)))
    count = 0
    while points:
        count += 1
        pending = [points.pop()]
        while pending:
            y, x = pending.pop()
            for dy, dx in itertools.product([-1, 0, 1], repeat=2):
                point = y+dy, x+dx
                if point in points:
                    points.remove(point)
                    pending.append(point)
    return count


def main():
    engine = assembly.Compositor(ROOT, OUT / 'catalog.json', OUT / 'motion.json')
    previous = assembly.Compositor(ROOT, OLD / 'catalog.json', OLD / 'motion.json')
    changed_motion = [key for key in set(engine.motion) | set(previous.motion)
                      if engine.motion.get(key) != previous.motion.get(key)]
    assert changed_motion == ['baseManifestSHA256']
    before = json.loads((OUT / 'integration-before.json').read_text())
    for path, expected in before['frozenFiles'].items():
        assert assembly.digest(ROOT / path) == expected, f'old file changed: {path}'
    old_body = ROOT / 'Art/Templates/P1-Neutral/down/walk-r2'
    new_body = ROOT / 'Art/Templates/P1-Neutral/down/walk-r3'
    body_changes = []
    for n in range(9):
        for slot in engine.asset(BASE)[0]['slots']:
            relative = f'layers/{n:02}/{slot}.png'
            if assembly.digest(old_body / relative) != assembly.digest(new_body / relative):
                body_changes.append(relative)
                assert slot == 'body.hand.right', f'unrelated body edit: {relative}'
    assert len(body_changes) == 9
    groups = {}
    for identifier in engine.entries:
        data, _, _ = engine.asset(identifier)
        groups.setdefault(data['part'], []).append(identifier)
    for key in ['frames', 'empty-hand']:
        (OUT / key).mkdir(exist_ok=True)
    contact = []
    records = []
    independent = {}
    reference_hand = Image.open(new_body / 'shared/grip-right-local.png').convert('RGBA')
    assert components(reference_hand) == 1, 'detached clothing fragments in shared hand'
    weapon_data, weapon_path, _ = engine.asset(WEAPON)
    local_weapon = Image.open(weapon_path.parent / weapon_data['bindings'][0]['layers']['weapon.right']).convert('RGBA')
    handle_mask = Image.new('RGBA', local_weapon.size)
    handle_mask.paste(local_weapon.crop((30, 25, 35, 34)), (30, 25))
    guard_mask = Image.new('RGBA', local_weapon.size)
    guard_mask.paste(local_weapon.crop((22, 34, 43, 38)), (22, 34))
    boards, before_images, after_images = [], [], []
    for hair, face, dressed, armed in itertools.product(groups['hair'], groups['face'], [False, True], [False, True]):
        selected = [hair, face] + ([OUTFIT] if dressed else []) + ([WEAPON] if armed else [])
        old_selected = [OLD_WEAPON if item == WEAPON else item for item in selected]
        outputs = []
        for n in range(9):
            clip = 'idle' if n == 0 else 'walk'
            parts = dict(engine.layers(BASE, selected, 'down', clip, n))
            old_parts = dict(previous.layers(OLD_BASE, old_selected, 'down', clip, n))
            actual = engine.render(BASE, selected, 'down', clip, n)
            old_image = previous.render(OLD_BASE, old_selected, 'down', clip, n)
            grip = engine.frames['down', clip, n]['sockets']['grip.right']['position']
            x, y = grip
            hand = parts['body.hand.right']
            assert equal(hand.crop((x-12, y-12, x+12, y+12)), reference_hand), 'hand slips relative to grip'
            changed_area = np.zeros((256, 256), dtype=bool)
            for slot in ['body.hand.right', 'weapon.right']:
                for images in [parts, old_parts]:
                    if slot in images:
                        changed_area |= np.array(images[slot])[:, :, 3] > 0
            assert np.array_equal(np.array(actual)[~changed_area], np.array(old_image)[~changed_area])
            for slot, image in parts.items():
                if slot not in ['body.hand.right', 'weapon.right']:
                    assert equal(image, old_parts[slot]), f'unrelated layer changed: {slot}'
                key = slot, n, hair if slot.startswith('hair.') else face if slot.startswith('face.') else None
                if slot.startswith(('body.', 'head.', 'outfit.', 'weapon.')):
                    if key in independent:
                        assert equal(image, independent[key]), f'appearance-dependent common layer: {slot}'
                    else:
                        independent[key] = image
            outputs.append(assembly.digest(new_body / f'layers/{n:02}/body.hand.right.png'))
            if hair == HAIR and face == FACE and dressed and armed:
                actual.save(OUT / f'frames/{n:02}.png')
                before_images.append(old_image)
                after_images.append(actual)
                boards.append(board(old_image, actual, grip))
                # Entire opaque finger area remains in front of the weapon.
                hand_pixels = np.array(hand)
                opaque = hand_pixels[:, :, 3] == 255
                assert np.array_equal(np.array(actual)[opaque], hand_pixels[opaque])
                pivot_x, pivot_y = weapon_data['pivot']
                world_handle = assembly.place(handle_mask, [1, 0, 0, 1, x-pivot_x, y-pivot_y], [256, 256])
                world_guard = assembly.place(guard_mask, [1, 0, 0, 1, x-pivot_x, y-pivot_y], [256, 256])
                hp = np.array(hand)[:, :, 3] >= 128
                hm = np.array(world_handle)[:, :, 3] >= 128
                coverage = np.count_nonzero(hp & hm) / np.count_nonzero(hm)
                assert coverage >= .8, 'fingers do not enclose the compact handle'
                gap = minimum_distance(hp, np.array(world_guard)[:, :, 3] >= 128)
                assert gap <= 1, 'guard detached from lower fingers'
                pose = engine.frames['down', clip, n]
                wrist = pose['joints'].get('wristRight', [x, y-5])
                a = np.array(parts['body.arm.right'])[:, :, 3] >= 128
                mask = np.zeros((256, 256), dtype=bool)
                wx, wy = wrist
                mask[wy-4:wy+5, wx-8:wx+9] = True
                rows = len(set(np.where(hp & a & mask)[0].tolist()))
                assert rows >= 2, 'wrist disconnected'
                contact.append({'frame': n, 'grip': grip, 'handleCoveredByFingers': round(coverage, 4),
                                'guardToFingersPixelDistance': gap, 'wristOverlapRows': rows})
            elif hair == HAIR and face == FACE and dressed and not armed:
                actual.save(OUT / f'empty-hand/{n:02}.png')
        records.append({'assets': selected, 'poses': 9, 'commonHandSHA256': outputs})
    boards[0].save(OUT / 'review.png')
    sequence = review.normal_gif(boards[1:], OUT / 'walk.gif')
    gif = Image.open(OUT / 'walk.gif')
    assert gif.n_frames == 8 and gif.info['loop'] == 0
    for n, expected in enumerate(sequence):
        gif.seek(n)
        assert gif.info['duration'] == 120 and equal(gif.convert('RGB'), expected.convert('RGB'))
    sheet = Image.new('RGB', (3*240, 3*270), '#d6e1dd')
    draw = ImageDraw.Draw(sheet)
    for n, sprite in enumerate(after_images):
        grip = engine.motion['frames'][n]['sockets']['grip.right']['position']
        detail = closeup(sprite, grip)
        x, y = n%3*240+30, n//3*270+35
        sheet.paste(detail, (x, y), detail)
        draw.text((x, y-22), f'{n:02} / '+('IDLE' if n == 0 else 'WALK'), fill='#29494a')
    sheet.save(OUT / 'grip-closeups.png')
    review.board(after_images, ['00 IDLE']+[f'{n:02} WALK' for n in range(1, 9)],
                 title='P1 / COMMON CLOSED FIST / COMPACT HILT').save(OUT / 'poses.png')
    cutouts = Image.new('RGB', (600, 300), '#c6d0cf')
    local_hand = reference_hand.resize((192, 192), Image.Resampling.NEAREST)
    cutouts.paste(local_hand, (40, 60), local_hand)
    local_sword = local_weapon.resize((128, 192), Image.Resampling.NEAREST)
    cutouts.paste(local_sword, (380, 60), local_sword)
    draw = ImageDraw.Draw(cutouts)
    draw.text((30, 20), 'COMMON HAND / NO WEAPON', fill='#29494a')
    draw.text((330, 20), 'SWORD / NO HAND OR SKIN', fill='#29494a')
    cutouts.save(OUT / 'independent-parts.png')
    (OUT / 'combinations.json').write_text(json.dumps({'base': BASE, 'count': 24, 'poses': 216,
        'records': records, 'sameHandWhenEmptyAndArmed': True}, indent=2)+'\n')
    editable_count = 0
    for folder in [new_body, weapon_path.parent]:
        for ora in sorted((folder / 'editable').glob('*.ora')):
            with zipfile.ZipFile(ora) as archive:
                assert archive.testzip() is None
                node = ET.fromstring(archive.read('stack.xml'))
                merged = Image.new('RGBA', (int(node.attrib['w']), int(node.attrib['h'])))
                for layer in reversed(list(node.find('stack'))):
                    merged.alpha_composite(Image.open(io.BytesIO(archive.read(layer.attrib['src']))).convert('RGBA'))
                expected = (engine.render(BASE, [], 'down', 'idle' if int(ora.stem) == 0 else 'walk', int(ora.stem))
                            if folder == new_body else local_weapon)
                assert equal(merged, expected)
                assert equal(Image.open(io.BytesIO(archive.read('mergedimage.png'))), expected)
                ET.parse(ora.with_suffix('.svg'))
                editable_count += 1
        generation = json.loads((folder / 'generation.json').read_text())
        for record in generation['records']:
            assert assembly.digest(folder / record['file']) == record['sha256']
            assert assembly.digest(folder / record['promptFile']) == record['promptSHA256']
            for reference in record['references']:
                assert assembly.digest(ROOT / reference['path']) == reference['sha256']
    result = {'passed': True, 'userFeedback': '剑没有握持感', 'artApproval': None,
              'frozenFilesPreserved': len(before['frozenFiles']), 'engineAndContractChanged': [],
              'motionChangedFields': changed_motion, 'commonBodyChangedLayers': body_changes,
              'otherBodyLayersByteExact': 63, 'sameCommonHandWhenEmptyAndArmed': True,
              'outfitAndHeadLayersUnchanged': True, 'combinations': 24, 'poses': 216,
              'sharedHandStrongAlphaComponents': 1, 'toolOutputsAndReferencesVerified': 2,
              'editableORARecompositions': editable_count, 'svgXMLValid': editable_count,
              'contactChecks': contact, 'gif': {'frames': 8, 'frameMs': 120, 'loop': 0},
              'limits': ['Visual grip still requires user review; contact tests do not certify naturalness.',
                         'Downward one-hand carry only; no attack or other grip poses.',
                         'New common right fist is an art revision, not previously approved body pixels.']}
    (OUT / 'validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'passed': True, 'combinations': 24, 'poses': 216, 'contact': contact}, indent=2))


if __name__ == '__main__':
    main()
