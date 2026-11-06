#!/usr/bin/env python3
"""Split the P1 map atlases into body sheets and per-part head sheets.

Every shipped P1 atlas (2 outfits x 5 weapon states x no/leather/rune armor,
Directions + Diagonals) is re-rendered from its layered parts with the shared
compositor, then split by slot:

  under  layers drawn before hair.back (back weapon in down/left/right views)
  body   everything else except face and hair (head.base and hands included)
  head   one sheet per head part variant: face.eyes/brows/nose/mouth, hair.front
         (and hair.back when a hairstyle has one), already placed per frame.

Runtime stacking order: under -> hair.back -> body -> eyes -> brows -> nose ->
mouth -> hair.front. Hands never overlap the head in any of the 3,120 cells
(checked here: no hand is drawn above an overlapping head part), so moving the head above
the hands changes no pixel.

The script fails unless re-stacking every state with its original head
reproduces the shipped atlas within 1 colour level (8-bit rounding at soft
edges when layers are pre-merged). Original atlases are not modified.

Usage: python3 -I scripts/build-p1-head-split.py [--check-only]
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
sys.dont_write_bytecode = True
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'Sources/Resources/Assets.xcassets'
MOTION = ROOT / 'Art/Integration/P1-modular-eight-way-v1/motion.json'
SELECTION = ROOT / 'Art/Integration/P1-modular-demo-v1/selection.json'
RECORD = ROOT / 'Art/Integration/P1-head-split-v1'
DIRECTIONS = ['down', 'left', 'up', 'right', 'down-right', 'down-left', 'up-left', 'up-right']
KEYS = [('idle', 0)] + [('walk', n) for n in range(1, 9)] + [('walk-start', 1), ('walk-start', 2), ('walk-stop', 1), ('walk-stop', 2)]
GROUPS = ['Directions', 'Diagonals']
HEAD_SLOTS = ['hair.back', 'face.eyes', 'face.brows', 'face.nose', 'face.mouth', 'hair.front']
SLOT_NAMES = {'hair.back': 'HairBack', 'face.eyes': 'Eyes', 'face.brows': 'Brows', 'face.nose': 'Nose',
              'face.mouth': 'Mouth', 'hair.front': 'HairFront'}
WEAPONS = {'none': [], 'trainingSword': ['p1-eight-way-weapon-v1'], 'huntingBow': ['p1-hunting-bow-v1'],
           'greatSword': ['p1-b2-greatsword-v1'], 'legendaryStaff': ['p1-b2-legendarystaff-v1']}
ARMORS = {'leatherArmor': 'p1-b2-leatherarmor-r4', 'runeArmor': 'p1-b2-runearmor-r5'}
OUTFITS = {'forester': 'p1-eight-way-forester-v1', 'wayfarer': 'p1-eight-way-wayfarer-v1'}
HEADS = {'forester': {'hair': 'p1-eight-way-hair-chestnut-v1', 'face': 'p1-eight-way-face-blue-v1'},
         'wayfarer': {'hair': 'p1-eight-way-hair-silver-v1', 'face': 'p1-eight-way-face-amber-v1'}}
VARIANT_NAMES = {'p1-eight-way-hair-chestnut-v1': 'Chestnut', 'p1-eight-way-hair-silver-v1': 'Silver',
                 'p1-eight-way-face-blue-v1': 'Blue', 'p1-eight-way-face-amber-v1': 'Amber'}
LOWER = 'p1-eight-way-lower-v1'


def title(text):
    return ''.join(part[:1].upper() + part[1:] for part in text.replace('-', ' ').split())


def load_compositor():
    sys.path.insert(0, str(ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location('p1_head_split_compositor', ROOT / 'scripts/compose-character-parts.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ids = {}
    for path in sorted((ROOT / 'Art/Parts/P1-v1').rglob('asset.json')):
        try:
            data = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if 'id' in data:
            ids.setdefault(data['id'], str(path.relative_to(ROOT)))
    RECORD.mkdir(parents=True, exist_ok=True)
    catalog = RECORD / 'catalog.json'
    catalog.write_text(json.dumps({'assets': [{'id': k, 'manifest': v} for k, v in sorted(ids.items())]}, indent=1) + '\n')
    return module.Compositor(ROOT, catalog, MOTION)


def states(gait):
    """(state key, body selection, original appearance, atlas names) for every shipped P1 atlas pair."""
    result = []
    for loadout in gait['modularP1']['loadouts']:
        outfit = loadout['id']
        for weapon, names in loadout['weaponAtlasNames'].items():
            result.append((title(outfit) + title(weapon), [OUTFITS[outfit], LOWER] + WEAPONS[weapon], outfit, names, weapon, None))
        for armor, per_weapon in loadout['armorAtlasNames'].items():
            for weapon, names in per_weapon.items():
                result.append((title(armor) + title(weapon), [LOWER, ARMORS[armor]] + WEAPONS[weapon], outfit, names, weapon, armor))
    return result


def stack(images):
    out = Image.new('RGBA', (256, 256))
    for image in images:
        out.alpha_composite(image)
    return out


def write_imageset(name, image):
    folder = ASSETS / f'{name}.imageset'
    folder.mkdir(exist_ok=True)
    image.save(folder / f'{name}.png', optimize=True)
    (folder / 'Contents.json').write_text(json.dumps({'images': [{'filename': f'{name}.png', 'idiom': 'universal'}],
                                                       'info': {'author': 'xcode', 'version': 1}}, indent=2) + '\n')
    return hashlib.sha256((folder / f'{name}.png').read_bytes()).hexdigest()


def main():
    check_only = '--check-only' in sys.argv
    compositor = load_compositor()
    base = json.loads(SELECTION.read_text())['base']
    gait = json.loads((ROOT / 'Sources/Resources/hero-gait.json').read_text())
    bodies, heads, report, outputs = {}, {}, [], {}
    worst, differing, hand_head = 0, 0, 0
    for key, body_selection, outfit, names, weapon, armor in states(gait):
        head_selection = [HEADS[outfit]['hair'], HEADS[outfit]['face']]
        for group, atlas_name in enumerate(names):
            shipped = np.array(Image.open(ASSETS / f'{atlas_name}.imageset/{atlas_name}.png').convert('RGBA'))
            sheets = {'under': Image.new('RGBA', (13 * 256, 4 * 256)), 'body': Image.new('RGBA', (13 * 256, 4 * 256))}
            head_sheets = {}
            rebuilt = Image.new('RGBA', (13 * 256, 4 * 256))
            for row, direction in enumerate(DIRECTIONS[group * 4:group * 4 + 4]):
                for column, (clip, frame) in enumerate(KEYS):
                    layers = compositor.layers(base, body_selection + head_selection, direction, clip, frame)
                    order = compositor.frames[(direction, clip, frame)]['drawOrder']
                    split = order.index('hair.back') if 'hair.back' in order else -1
                    under = [im for slot, im in layers if slot not in HEAD_SLOTS and order.index(slot) < split]
                    body = [im for slot, im in layers if slot not in HEAD_SLOTS and order.index(slot) > split]
                    head = {slot: im for slot, im in layers if slot in HEAD_SLOTS}
                    # Only a hand drawn ABOVE an overlapping head part would change pixels when
                    # the runtime stacks the head over the body; a hand tucked under the hair is fine.
                    first_head = min((order.index(slot) for slot in head), default=len(order))
                    hands = np.zeros((256, 256), bool)
                    for slot, im in layers:
                        if slot.startswith('body.hand') and order.index(slot) > first_head:
                            hands |= np.array(im.getchannel('A')) > 0
                    covered = np.zeros((256, 256), bool)
                    for im in head.values():
                        covered |= np.array(im.getchannel('A')) > 0
                    hand_head += int((hands & covered).any())
                    box = (column * 256, row * 256)
                    under_cell, body_cell = stack(under), stack(body)
                    sheets['under'].paste(under_cell, box)
                    sheets['body'].paste(body_cell, box)
                    cell = Image.new('RGBA', (256, 256))
                    for part in [under_cell] + ([head['hair.back']] if 'hair.back' in head else []) + [body_cell] + \
                            [head[slot] for slot in HEAD_SLOTS[1:] if slot in head]:
                        cell.alpha_composite(part)
                    rebuilt.paste(cell, box)
                    for slot, im in head.items():
                        owner = HEADS[outfit]['hair'] if slot.startswith('hair') else HEADS[outfit]['face']
                        head_sheets.setdefault((slot, owner), Image.new('RGBA', (13 * 256, 4 * 256))).paste(im, box)
            diff = np.abs(np.array(rebuilt).astype(int) - shipped.astype(int)).max(-1)
            worst = max(worst, int(diff.max()))
            differing += int((diff > 0).sum())
            body_hash = hashlib.sha256(sheets['body'].tobytes() + sheets['under'].tobytes()).hexdigest()
            bodies.setdefault((key, group), (body_hash, sheets, atlas_name))
            if bodies[(key, group)][0] != body_hash:
                raise SystemExit(f'body sheet for {key} differs between appearances; split is not head-only')
            for (slot, owner), sheet in head_sheets.items():
                digest = hashlib.sha256(sheet.tobytes()).hexdigest()
                previous = heads.setdefault((slot, owner, group), (digest, sheet))
                if previous[0] != digest:
                    raise SystemExit(f'{slot} of {owner} depends on equipment; head sheets must be equipment-free')
            report.append({'state': key, 'outfit': outfit, 'weapon': weapon, 'armor': armor, 'group': GROUPS[group],
                           'shippedAtlas': atlas_name, 'maxChannelDifference': int(diff.max()),
                           'differingPixels': int((diff > 0).sum())})
            print(f'{atlas_name}: max diff {int(diff.max())}, {int((diff > 0).sum())} px', flush=True)
    if hand_head:
        raise SystemExit(f'{hand_head} cells have a hand over the head; runtime order would change pixels')
    if worst > 1:
        raise SystemExit(f'split re-stack differs from shipped atlases by up to {worst} levels')
    manifest = {'schemaVersion': 1, 'cell': 256, 'columns': 13, 'rows': 4, 'groups': GROUPS,
                'stackOrder': ['under', 'hair.back', 'body', 'face.eyes', 'face.brows', 'face.nose', 'face.mouth', 'hair.front'],
                'states': {}, 'headParts': {}, 'defaults': {}}
    if not check_only:
        for (key, group), (_, sheets, _) in sorted(bodies.items()):
            for part in ('under', 'body'):
                name = f'P1Split{part.title()}{key}{GROUPS[group]}'
                outputs[name] = write_imageset(name, sheets[part])
                manifest['states'].setdefault(key, {}).setdefault(part, [None, None])[group] = name
        for (slot, owner, group), (_, sheet) in sorted(heads.items()):
            name = f'P1Head{SLOT_NAMES[slot]}{VARIANT_NAMES[owner]}{GROUPS[group]}'
            outputs[name] = write_imageset(name, sheet)
            manifest['headParts'].setdefault(slot, {}).setdefault(VARIANT_NAMES[owner].lower(), [None, None])[group] = name
        for outfit, parts in HEADS.items():
            manifest['defaults'][outfit] = {slot: VARIANT_NAMES[parts['hair' if slot.startswith('hair') else 'face']].lower()
                                            for slot in HEAD_SLOTS if slot in manifest['headParts']}
        for key, _, outfit, names, weapon, armor in states(gait):
            manifest['states'][key].update({'weapon': weapon, 'armor': armor})
        dataset = ASSETS / 'P1HeadSplitManifest.dataset'
        dataset.mkdir(exist_ok=True)
        (dataset / 'manifest.json').write_text(json.dumps(manifest, indent=1, sort_keys=True) + '\n')
        (dataset / 'Contents.json').write_text(json.dumps({'data': [{'filename': 'manifest.json', 'idiom': 'universal'}],
                                                           'info': {'author': 'xcode', 'version': 1}}, indent=2) + '\n')
    (RECORD / 'verification.json').write_text(json.dumps({
        'cellsChecked': len(report) * 52, 'handOverHeadCells': hand_head, 'worstChannelDifference': worst,
        'differingPixelsTotal': differing, 'uniqueBodyStates': len({k for k, _ in bodies}),
        'headSheets': len(heads), 'perAtlas': report, 'outputs': outputs,
        'note': 'Re-stacking split sheets with each original head vs shipped atlases; offline Pillow compositing.'}, indent=1) + '\n')
    print(f'worst diff {worst}, differing px {differing}, hand-over-head cells {hand_head}, '
          f'unique bodies {len({k for k, _ in bodies})}, head sheets {len(heads)}')


if __name__ == '__main__':
    main()
