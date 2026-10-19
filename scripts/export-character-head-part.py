#!/usr/bin/env python3
"""Package an authored head layer using its fixed whole-canvas registration."""
import argparse
import base64
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def png(im):
    b = io.BytesIO()
    im.save(b, 'PNG')
    return b.getvalue()


def editable(folder, parts):
    node = ET.Element('image', version='0.0.1', w='96', h='96', name=folder.name)
    stack = ET.SubElement(node, 'stack')
    whole = Image.new('RGBA', (96, 96))
    for im in parts.values():
        whole.alpha_composite(im)
    with zipfile.ZipFile(folder / 'editable.ora', 'w') as z:
        def put(name, data, stored=False):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        put('mimetype', 'image/openraster', True)
        for i, (slot, im) in enumerate(reversed(list(parts.items()))):
            src = f'data/{i}.png'
            ET.SubElement(stack, 'layer', name=slot, src=src, x='0', y='0',
                          opacity='1.0', visibility='visible', **{'composite-op': 'svg:src-over'})
            put(src, png(im))
        put('stack.xml', ET.tostring(node, encoding='utf-8', xml_declaration=True))
        put('mergedimage.png', png(whole))
    ns = 'http://www.w3.org/2000/svg'
    ink = 'http://www.inkscape.org/namespaces/inkscape'
    ET.register_namespace('', ns)
    ET.register_namespace('inkscape', ink)
    svg = ET.Element(f'{{{ns}}}svg', width='768', height='768', viewBox='0 0 96 96')
    for slot, im in parts.items():
        group = ET.SubElement(svg, f'{{{ns}}}g', id=slot)
        group.set(f'{{{ink}}}groupmode', 'layer')
        group.set(f'{{{ink}}}label', slot)
        ET.SubElement(group, f'{{{ns}}}image', width='96', height='96',
                      href='data:image/png;base64,' + base64.b64encode(png(im)).decode())
    (folder / 'editable.svg').write_text(ET.tostring(svg, encoding='unicode') + '\n')


def export(folder):
    folder = Path(folder)
    cfg = json.loads((folder / 'authoring.json').read_text())
    source = Image.open(folder / cfg['source']).convert('RGBA')
    if source.size != tuple(cfg['sourceCanvas']):
        raise ValueError('source registration canvas differs; no content fitting')
    clean = Image.new('RGBA', source.size)
    x0, y0, x1, y1 = cfg['registrationGutter']
    clean.paste(source.crop((x0, y0, x1, y1)), (x0, y0))
    local = clean.resize((96, 96), Image.Resampling.NEAREST)
    a = np.array(local)
    a[:, :, 3][a[:, :, 3] >= 250] = 255
    local = Image.fromarray(a)
    masks = {}
    for slot, boxes in cfg['regions'].items():
        mask = Image.new('L', (96, 96))
        draw = ImageDraw.Draw(mask)
        for x0, y0, x1, y1 in boxes:
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=255)
        masks[slot] = np.array(mask) > 0
    counts = sum(m.astype(int) for m in masks.values())
    if np.any(counts > 1):
        raise ValueError('authoring partitions overlap')
    if np.any((np.array(local)[:, :, 3] > 8) & (counts == 0)):
        raise ValueError('source art falls outside registered semantic regions; redraw, do not fit/crop to repair')
    (folder / 'png').mkdir(exist_ok=True)
    parts = {}
    for slot, mask in masks.items():
        pixels = np.array(local)
        pixels[~mask] = 0
        im = Image.fromarray(pixels)
        im.save(folder / 'png' / f'{slot}.png')
        parts[slot] = im
    editable(folder, parts)
    compatibility = json.loads((ROOT / 'Art/Standards/P1-Parts-v1/profile.json').read_text())
    manifest = {'schemaVersion': '1.0.0', 'id': cfg['id'], 'version': '1.0.0', 'part': cfg['part'],
                'compatibility': {'rig': compatibility['id'], 'bodyProfile': compatibility['bodyProfile'],
                                  'actionSet': compatibility['actionSet']},
                'mode': 'head-local', 'slots': list(parts), 'directions': ['down'], 'clips': ['idle', 'walk'],
                'sourceFiles': ['source/down.png', 'editable.ora', 'editable.svg'],
                'bindings': [{'direction': 'down', 'clip': clip, 'frame': frame,
                              'layers': {slot: f'png/{slot}.png' for slot in parts}}
                             for clip, indices in compatibility['clips'].items() for frame in indices]}
    (folder / 'asset.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    args = p.parse_args()
    try:
        manifest = export(args.folder)
        print(json.dumps({'asset': manifest['id'], 'slots': manifest['slots']}))
    except (OSError, ValueError, KeyError) as e:
        p.exit(1, str(e) + '\n')


if __name__ == '__main__':
    main()
