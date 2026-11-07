#!/usr/bin/env python3
"""Export authored clothing patterns and generated paint at fixed coordinates.

This authoring tool never changes a body or fits an image to an alpha box.
Production assembly reads the finished ordinary pose maps without repairs.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path

from PIL import Image, ImageChops


def export(folder):
    cfg = json.loads((folder / 'authoring.json').read_text())
    asset = json.loads((folder / 'asset.json').read_text())
    plate = Image.open(folder / cfg['source']).convert('RGBA')
    if list(plate.size) != cfg['sourceCanvas']:
        raise ValueError('generated source canvas changed')
    plate = plate.resize(tuple(cfg['targetPlateCanvas']), Image.Resampling.NEAREST)
    green = Image.open(folder / 'source/cloth-underlap-material.png').convert('RGBA')
    green = green.resize((256, 256), Image.Resampling.NEAREST)
    atlas = Image.open(folder / 'source/lower-materials.png').convert('RGBA')
    half = atlas.width // 2
    gray = atlas.crop((0, 0, half, half)).resize((256, 256), Image.Resampling.NEAREST)
    brown = atlas.crop((half, 0, half * 2, half)).resize((256, 256), Image.Resampling.NEAREST)
    common = {}
    for side, box in [('right', (0, 0, 32, 64)), ('left', (32, 0, 64, 64))]:
        mask = Image.open(folder / f'patterns/00/sleeve.{side}.png').convert('L')
        common[side] = green.copy()
        common[side].putalpha(mask)
        paint = Image.new('RGBA', (256, 256))
        paint.paste(plate.crop(box), (92 + box[0], 125))
        paint.putalpha(ImageChops.multiply(paint.getchannel('A'), mask))
        common[side].alpha_composite(paint)
    spec = importlib.util.spec_from_file_location('wardrobe_export', Path(__file__).with_name('export-wardrobe-part.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    compose_spec = importlib.util.spec_from_file_location('part_compose', Path(__file__).with_name('compose-character-parts.py'))
    compose = importlib.util.module_from_spec(compose_spec)
    compose_spec.loader.exec_module(compose)
    motion = cfg['acceptedSleeveMotion']
    for binding in asset['bindings']:
        frame = binding['frame']
        parts = {}
        for slot, relative in binding['layers'].items():
            if slot.startswith('outfit.sleeve.'):
                side = slot.rsplit('.', 1)[1]
                dx, dy = motion[f'{side}RelativeXY'][frame]
                dy += motion['bodyBobY'][frame]
                angle = math.radians(motion[f'{side}AngleDeg'][frame])
                a, b, c, d = math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle)
                px, py = motion['shoulderPivots'][side]
                image = compose.place(common[side], [a, b, c, d, px-a*px-c*py+dx, py-b*px-d*py+dy], (256, 256))
            else:
                original = Image.open(folder / f'source/original-layers/{frame:02}/{slot}.png').convert('RGBA')
                if slot == 'outfit.torso':
                    pattern, material = 'torso', green
                elif slot.startswith('outfit.pants.'):
                    pattern, material = slot.removeprefix('outfit.'), gray
                elif slot.startswith('outfit.boot.'):
                    pattern, material = slot.removeprefix('outfit.'), brown
                else:
                    pattern, material = None, None
                if pattern:
                    image = material.copy()
                    image.putalpha(Image.open(folder / f'patterns/{frame:02}/{pattern}.png').convert('L'))
                    image.alpha_composite(original)
                else:
                    image = original
            image.save(folder / relative)
            parts[slot] = image
        helper.editable(folder / 'editable', f'{frame:02}', parts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    export(args.folder)
