#!/usr/bin/env python3
"""Export a common relaxed arm motion from the retained natural idle artwork."""
import argparse
import importlib.util
import json
import math
from pathlib import Path

from PIL import Image


def export(folder):
    cfg = json.loads((folder / 'arm-motion-authoring.json').read_text())
    asset = json.loads((folder / 'asset.json').read_text())
    idle = {slot: Image.open(folder / path).convert('RGBA') for slot, path in cfg['sourceBySlot'].items()}
    spec = importlib.util.spec_from_file_location('wardrobe_export', Path(__file__).with_name('export-wardrobe-part.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    compose_spec = importlib.util.spec_from_file_location('part_compose', Path(__file__).with_name('compose-character-parts.py'))
    compose = importlib.util.module_from_spec(compose_spec)
    compose_spec.loader.exec_module(compose)
    for binding in asset['bindings']:
        frame = binding['frame']
        parts = {}
        for slot, relative in binding['layers'].items():
            if slot in idle:
                side = slot.rsplit('.', 1)[1]
                dx, dy = cfg[f'{side}RelativeXY'][frame]
                dy += cfg['bodyBobY'][frame]
                angle = math.radians(cfg[f'{side}AngleDeg'][frame])
                a, b, c, d = math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle)
                px, py = cfg['shoulderPivots'][side]
                image = compose.place(idle[slot], [a, b, c, d, px-a*px-c*py+dx, py-b*px-d*py+dy], (256, 256))
                image.save(folder / relative)
            else:
                image = Image.open(folder / relative).convert('RGBA')
            parts[slot] = image
        whole = helper.editable(folder / 'editable', f'{frame:02}', parts)
        whole.save(folder / 'frames' / f'{frame:02}.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    export(args.folder)
