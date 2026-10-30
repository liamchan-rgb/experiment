#!/usr/bin/env python3
"""Export registered blue coat art as ordinary pose maps, using shared motion.

The fixed source registration and seam polygons are authored data. No body,
appearance identifier or runtime compositor is modified by this exporter.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def export(folder):
    cfg = json.loads((folder / 'authoring.json').read_text())
    compose = module('compose', 'compose-character-parts.py')
    helper = module('editable', 'export-wardrobe-part.py')
    source = Image.open(folder / cfg['source']).convert('RGBA')
    assert list(source.size) == cfg['sourceCanvas']
    # Generated opaque paint has alpha253..255; normalize opaque interiors.
    source.putalpha(source.getchannel('A').point(lambda a: 255 if a >= 250 else a))
    # Explicit full-source affine. Never scale/crop according to alpha bounds.
    inverse = cfg['inverseSourceToCanvas']
    registered = source.transform((256, 256), Image.Transform.AFFINE, inverse, Image.Resampling.NEAREST)
    cloth = source.crop(tuple(cfg['clothSwatch'])).resize((256, 256), Image.Resampling.NEAREST)
    assert cloth.getchannel('A').getextrema() == (255, 255)
    common = {}
    for slot, polygon in cfg['partitions'].items():
        mask = Image.new('L', (256, 256))
        ImageDraw.Draw(mask).polygon([tuple(p) for p in polygon], fill=255)
        art = registered.copy()
        art.putalpha(ImageChops.multiply(art.getchannel('A'), mask))
        if slot in cfg['underlapPatterns']:
            pattern = Image.open(folder / cfg['underlapPatterns'][slot]).convert('L')
            underlap = cloth.copy()
            underlap.putalpha(pattern)
            underlap.alpha_composite(art)
            art = underlap
        common[slot] = art
    motion = cfg['sharedArmMotion']
    bindings = []
    for frame in range(9):
        parts, paths = {}, {}
        out = folder / 'png' / f'{frame:02}'
        out.mkdir(parents=True, exist_ok=True)
        for slot in cfg['slots']:
            if slot in common:
                matrix = [1, 0, 0, 1, 0, motion['bodyBobY'][frame]]
                if slot.startswith('outfit.sleeve.'):
                    side = slot.rsplit('.', 1)[1]
                    dx, dy = motion[f'{side}RelativeXY'][frame]
                    dy += motion['bodyBobY'][frame]
                    angle = math.radians(motion[f'{side}AngleDeg'][frame])
                    a, b, c, d = math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle)
                    px, py = motion['shoulderPivots'][side]
                    matrix = [a, b, c, d, px-a*px-c*py+dx, py-b*px-d*py+dy]
                if slot == 'outfit.hem.front':
                    # Two independently authored tails hinge below the belt;
                    # roots remain concealed beneath the torso overlap.
                    art = Image.new('RGBA', (256, 256))
                    for side, box in [('right', (0, 0, 126, 256)), ('left', (126, 0, 256, 256))]:
                        tail = Image.new('RGBA', (256, 256))
                        tail.paste(common[slot].crop(box), box[:2])
                        angle = math.radians(cfg['coatTailMotion'][f'{side}AngleDeg'][frame])
                        a, b, c, d = math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle)
                        px, py = cfg['coatTailMotion']['pivots'][side]
                        dy = motion['bodyBobY'][frame]
                        art.alpha_composite(compose.place(tail, [a,b,c,d,px-a*px-c*py,py-b*px-d*py+dy], (256,256)))
                else:
                    art = compose.place(common[slot], matrix, (256, 256))
            else:
                # Shared trousers/boots are explicit self-contained source art.
                art = Image.open(folder / f'source/shared-lower/{frame:02}/{slot}.png').convert('RGBA')
            relative = f'png/{frame:02}/{slot}.png'
            art.save(folder / relative)
            parts[slot], paths[slot] = art, relative
        (folder / 'editable').mkdir(exist_ok=True)
        helper.editable(folder / 'editable', f'{frame:02}', parts)
        bindings.append({'direction': 'down', 'clip': 'idle' if frame == 0 else 'walk', 'frame': frame, 'layers': paths})
    manifest = {k: cfg[k] for k in ['id', 'compatibility', 'slots']}
    manifest.update(schemaVersion='1.0.0', version='1.0.0', part='outfit', mode='pose-map', directions=['down'], clips=['idle', 'walk'], bindings=bindings)
    manifest['sourceFiles'] = ['authoring.json'] + [str(p.relative_to(folder)) for directory in ['source', 'patterns', 'editable'] for p in sorted((folder/directory).rglob('*')) if p.is_file()]
    (folder / 'asset.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'id': cfg['id'], 'poses': len(bindings), 'parts': len(cfg['slots']) * len(bindings)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    export(p.parse_args().folder)
