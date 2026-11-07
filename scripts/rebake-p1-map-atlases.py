#!/usr/bin/env python3
"""Re-bake every shipped P1 map atlas from its layered parts.

Uses the same part selections that build-p1-head-split.py verified to
reproduce all 60 atlases exactly (2 outfits x 5 weapon states x no/leather/
rune armor, Directions + Diagonals). Run this after changing shared parts
(e.g. the base body), then re-run build-p1-head-split.py.

Atlas names, sizes (13 x 4 x 256), cell order, anchors and hero-gait.json are
unchanged; only pixels follow the parts.

Usage: python3 -I scripts/rebake-p1-map-atlases.py
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('p1_head_split', ROOT / 'scripts/build-p1-head-split.py')
split = importlib.util.module_from_spec(spec)
spec.loader.exec_module(split)


def main():
    compositor = split.load_compositor()
    base = json.loads(split.SELECTION.read_text())['base']
    gait = json.loads((ROOT / 'Sources/Resources/hero-gait.json').read_text())
    record = []
    for key, body_selection, outfit, names, weapon, armor in split.states(gait):
        selection = body_selection + [split.HEADS[outfit]['hair'], split.HEADS[outfit]['face']]
        for group, name in enumerate(names):
            atlas = Image.new('RGBA', (13 * 256, 4 * 256))
            for row, direction in enumerate(split.DIRECTIONS[group * 4:group * 4 + 4]):
                for column, (clip, frame) in enumerate(split.KEYS):
                    atlas.paste(compositor.render(base, selection, direction, clip, frame), (column * 256, row * 256))
            path = split.ASSETS / f'{name}.imageset/{name}.png'
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            atlas.save(path, optimize=True)
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            record.append({'atlas': name, 'state': key, 'outfit': outfit, 'selection': selection,
                           'sha256Before': before, 'sha256After': after})
            print(name, 'changed' if before != after else 'unchanged', flush=True)
    (split.RECORD / 'rebake.json').write_text(json.dumps(record, indent=1) + '\n')


if __name__ == '__main__':
    main()
