#!/usr/bin/env python3
"""Export registered wardrobe authoring layers; never infer fit from artwork.

All partitions, patches and translations are explicit authoring data. The
runtime consumes the resulting ordinary pose-map/socket manifests unchanged.
"""
import argparse
import base64
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw


def png(im):
    stream = io.BytesIO()
    im.save(stream, 'PNG')
    return stream.getvalue()


def editable(folder, name, parts):
    size = next(iter(parts.values())).size
    whole = Image.new('RGBA', size)
    for im in parts.values():
        whole.alpha_composite(im)
    node = ET.Element('image', version='0.0.1', w=str(size[0]), h=str(size[1]), name=name)
    stack = ET.SubElement(node, 'stack')
    with zipfile.ZipFile(folder / f'{name}.ora', 'w') as archive:
        def put(path, data, stored=False):
            info = zipfile.ZipInfo(path, date_time=(2026, 10, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
        put('mimetype', 'image/openraster', True)
        for i, (slot, im) in enumerate(reversed(list(parts.items()))):
            src = f'data/{i}.png'
            ET.SubElement(stack, 'layer', name=slot, src=src, x='0', y='0', opacity='1.0',
                          visibility='visible', **{'composite-op': 'svg:src-over'})
            put(src, png(im))
        put('stack.xml', ET.tostring(node, encoding='utf-8', xml_declaration=True))
        put('mergedimage.png', png(whole))
    ns = 'http://www.w3.org/2000/svg'
    ET.register_namespace('', ns)
    svg = ET.Element(f'{{{ns}}}svg', width=str(size[0] * 4), height=str(size[1] * 4),
                     viewBox=f'0 0 {size[0]} {size[1]}')
    for slot, im in parts.items():
        group = ET.SubElement(svg, f'{{{ns}}}g', id=slot)
        ET.SubElement(group, f'{{{ns}}}image', width=str(size[0]), height=str(size[1]),
                      href='data:image/png;base64,' + base64.b64encode(png(im)).decode())
    (folder / f'{name}.svg').write_text(ET.tostring(svg, encoding='unicode') + '\n')
    return whole


def export(folder):
    cfg = json.loads((folder / 'authoring.json').read_text())
    cache = {}
    def source(relative):
        if relative not in cache:
            raw = Image.open(folder / relative).convert('RGBA')
            if raw.size != tuple(cfg['sourceCanvas']):
                raise ValueError('source canvas differs from fixed registration')
            clean = Image.new('RGBA', raw.size)
            box = tuple(cfg['registrationGutter'])
            clean.paste(raw.crop(box), box[:2])
            if 'inverseSourceToCanvas' in cfg:
                im = clean.transform(tuple(cfg['authorCanvas']), Image.Transform.AFFINE,
                                     cfg['inverseSourceToCanvas'], Image.Resampling.NEAREST)
            else:
                im = clean.resize(tuple(cfg['authorCanvas']), Image.Resampling.NEAREST)
            pixels = np.array(im)
            pixels[:, :, 3][pixels[:, :, 3] >= 250] = 255
            cache[relative] = Image.fromarray(pixels)
        return cache[relative]
    def piece(recipe):
        im = source(recipe['source']).copy()
        if 'polygons' in recipe:
            mask = Image.new('L', im.size)
            draw = ImageDraw.Draw(mask)
            for polygon in recipe['polygons']:
                draw.polygon([tuple(point) for point in polygon], fill=255)
            for polygon in recipe.get('excludePolygons', []):
                draw.polygon([tuple(point) for point in polygon], fill=0)
            pixels = np.array(im)
            pixels[np.array(mask) == 0] = 0
            im = Image.fromarray(pixels)
        if 'crop' in recipe:
            im = im.crop(tuple(recipe['crop']))
        target = Image.new('RGBA', tuple(cfg['canvas']))
        target.paste(im, tuple(recipe.get('translate', [0, 0])))
        return target
    bindings = []
    sources = set()
    editable_dir = folder / 'editable'
    editable_dir.mkdir(exist_ok=True)
    for pose in cfg['poses']:
        parts, paths = {}, {}
        index = pose['frame']
        output = folder / 'png' / f'{index:02}'
        output.mkdir(parents=True, exist_ok=True)
        def build(slot, ancestors=()):
            if slot in parts:
                return parts[slot]
            if slot in ancestors:
                raise ValueError('cyclic hidden-under authoring layers')
            layer = Image.new('RGBA', tuple(cfg['canvas']))
            for recipe in pose['layers'][slot]:
                sources.add(recipe['source'])
                item = piece(recipe)
                if 'hiddenUnder' in recipe:
                    occluder = build(recipe['hiddenUnder'], (*ancestors, slot))
                    pixels = np.array(item)
                    pixels[np.array(occluder)[:, :, 3] < 250] = 0
                    item = Image.fromarray(pixels)
                layer.alpha_composite(item)
            parts[slot] = layer
            return layer
        # Preserve authored draw order despite dependencies used only for
        # hidden material completion. No such dependency enters the manifest.
        for slot in pose['layers']:
            layer = build(slot)
            relative = f'png/{index:02}/{slot}.png'
            layer.save(folder / relative)
            paths[slot] = relative
        parts = {slot: parts[slot] for slot in pose['layers']}
        editable(editable_dir, f'{index:02}', parts)
        bindings.append({'direction': 'down', 'clip': pose['clip'], 'frame': index, 'layers': paths})
    if cfg['mode'] == 'socket':
        # A rigid weapon has one drawing shared by all poses.
        bindings = [{'direction': 'down', 'clip': 'idle' if i == 0 else 'walk', 'frame': i,
                     'layers': bindings[0]['layers']} for i in range(9)]
    manifest = {'schemaVersion': '1.0.0', 'id': cfg['id'], 'version': '1.0.0', 'part': cfg['part'],
                'compatibility': cfg['compatibility'], 'mode': cfg['mode'],
                'slots': list(cfg['poses'][0]['layers']), 'directions': ['down'], 'clips': ['idle', 'walk'],
                'sourceFiles': sorted(sources) + ['authoring.json'] +
                    [f'editable/{pose["frame"]:02}.{ext}' for pose in cfg['poses'] for ext in ['ora', 'svg']],
                'bindings': bindings}
    if cfg['mode'] == 'socket':
        manifest.update({k: cfg[k] for k in ['canvas', 'pivot', 'socket', 'gripProfile']})
    (folder / 'asset.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    manifest = export(args.folder)
    print(json.dumps({'asset': manifest['id'], 'bindings': len(manifest['bindings'])}))
