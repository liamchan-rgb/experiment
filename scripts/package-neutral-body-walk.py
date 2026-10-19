#!/usr/bin/env python3
"""Export authored neutral walk parts in the approved common body coordinates.

This is a source-art packaging step. Anatomical masks are reviewed authoring
data, never a runtime colour/key/appearance-dependent segmentation heuristic.
"""
import base64
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Art/Templates/P1-Neutral/down/r1'
OUT = ROOT / 'Art/Templates/P1-Neutral/down/walk-r1'
ORDER = ['body.leg.right', 'body.leg.left', 'body.arm.right', 'body.arm.left',
         'body.torso', 'head.base', 'body.hand.right', 'body.hand.left']
SIZE = (256, 256)


def png(im):
    b = io.BytesIO()
    im.save(b, 'PNG')
    return b.getvalue()


def blank():
    return Image.new('RGBA', SIZE)


def partition(im, points):
    mask = Image.new('L', SIZE)
    ImageDraw.Draw(mask).polygon([tuple(x) for x in points], fill=255)
    a = np.array(im)
    a[np.array(mask) == 0] = 0
    return Image.fromarray(a)


def translate(im, dx, dy):
    out = blank()
    # Integer placement must preserve the approved straight-alpha edge pixels.
    # Compositing onto empty RGBA can round low-alpha RGB values unnecessarily.
    out.paste(im, (dx, dy))
    return out


def source(frame):
    name = f'{frame:02}' if isinstance(frame, int) else frame
    im = Image.open(OUT / 'source' / f'{name}.png').convert('RGBA')
    if im.size != (1254, 1254):
        raise ValueError(f'{frame}: incorrect source registration canvas')
    gutter = Image.new('RGBA', im.size)
    gutter.alpha_composite(im.crop((80, 80, 1174, 1174)), (80, 80))
    im = gutter.transform(SIZE, Image.Transform.AFFINE,
                          (6.25, 0, -156.25, 0, 6.25, -237.5), Image.Resampling.BICUBIC)
    a = np.array(im)
    a[:, :, 3][a[:, :, 3] >= 250] = 255
    return Image.fromarray(a)


def compose(parts, order):
    out = blank()
    for name in order:
        out.alpha_composite(parts[name])
    return out


def editable(frame, parts, whole, order):
    node = ET.Element('image', version='0.0.1', w='256', h='256', name=f'Neutral down {frame:02}')
    stack = ET.SubElement(node, 'stack')
    target = OUT / 'editable' / f'{frame:02}.ora'
    with zipfile.ZipFile(target, 'w') as z:
        def put(name, data, stored=False):
            zi = zipfile.ZipInfo(name, date_time=(2026, 10, 18, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            z.writestr(zi, data)
        put('mimetype', 'image/openraster', True)
        for i, name in enumerate(reversed(order)):
            path = f'data/{i}.png'
            ET.SubElement(stack, 'layer', name=name, src=path, x='0', y='0',
                          opacity='1.0', visibility='visible', **{'composite-op': 'svg:src-over'})
            put(path, png(parts[name]))
        put('stack.xml', ET.tostring(node, encoding='utf-8', xml_declaration=True))
        put('mergedimage.png', png(whole))
        put('Thumbnails/thumbnail.png', png(whole.resize((128, 128))))
    ns = 'http://www.w3.org/2000/svg'
    ink = 'http://www.inkscape.org/namespaces/inkscape'
    ET.register_namespace('', ns)
    ET.register_namespace('inkscape', ink)
    svg = ET.Element(f'{{{ns}}}svg', width='256', height='256', viewBox='0 0 256 256')
    for name in order:
        g = ET.SubElement(svg, f'{{{ns}}}g', id=name)
        g.set(f'{{{ink}}}groupmode', 'layer')
        g.set(f'{{{ink}}}label', name)
        ET.SubElement(g, f'{{{ns}}}image', width='256', height='256',
                      href='data:image/png;base64,' + base64.b64encode(png(parts[name])).decode())
    (OUT / 'editable' / f'{frame:02}.svg').write_text(ET.tostring(svg, encoding='unicode') + '\n')


def review(frames):
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    bg = '#dce4df'
    sheet = Image.new('RGB', (1080, 1530), bg)
    d = ImageDraw.Draw(sheet)
    d.text((20, 14), 'P1 / COMMON NEUTRAL BODY / DOWN WALK r1', font=font, fill='#254345')
    labels = ['00  APPROVED IDLE', '01  RIGHT CONTACT', '02  RIGHT SUPPORT',
              '03  LEFT PASSING', '04  LEFT LATE SWING', '05  LEFT CONTACT',
              '06  LEFT SUPPORT', '07  RIGHT PASSING', '08  RIGHT LATE SWING']
    for i, im in enumerate(frames):
        x, y = (i % 3) * 360, 55 + (i // 3) * 485
        d.text((x + 12, y), labels[i], font=small, fill='#486567')
        sprite = im.crop((70, 70, 182, 225)).resize((336, 465), Image.Resampling.NEAREST)
        sheet.paste(sprite, (x + 10, y + 20), sprite)
    sheet.save(OUT / 'review.png')
    # A single palette prevents per-frame palette changes in the review loop.
    rgb = []
    for im in frames[1:]:
        canvas = Image.new('RGBA', SIZE, bg)
        canvas.alpha_composite(im)
        rgb.append(canvas.convert('RGB').crop((64, 64, 192, 232)).resize((512, 672), Image.Resampling.NEAREST))
    atlas = Image.new('RGB', (512 * 8, 672))
    for i, im in enumerate(rgb):
        atlas.paste(im, (i * 512, 0))
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    quantized = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in rgb]
    for name, duration in [('walk.gif', 120), ('walk-slow.gif', 480)]:
        quantized[0].save(OUT / name, save_all=True, append_images=quantized[1:],
                          duration=duration, loop=0, disposal=1, optimize=False)
    return quantized


def main():
    config = json.loads((OUT / 'extraction.json').read_text())
    base = {k: Image.open(BASE / 'layers/00' / f'{k}.png').convert('RGBA') for k in ORDER}
    for d in ['frames', 'layers', 'editable']:
        (OUT / d).mkdir(exist_ok=True)
    (OUT / 'shared').mkdir(exist_ok=True)
    for src, dst in [('head-down.png', 'head-down.png'), ('approval.json', 'idle-approval.json')]:
        shutil.copyfile(BASE / src, OUT / 'shared' / dst)
    frames, bindings, motion = [], [], []
    for frame in range(9):
        cfg = config['poses'][str(frame)]
        order = cfg.get('drawOrder', ORDER)
        dx, dy = cfg['bodyTranslation']
        if frame == 0:
            parts = base
        else:
            art = source(frame)
            parts = {k: translate(base[k], dx, dy) for k in ['head.base', 'body.torso']}
            for side in ['right', 'left']:
                for kind in ['arm', 'hand', 'leg']:
                    key = f'body.{kind}.{side}'
                    selected = source(cfg['partSources'][key]) if key in cfg.get('partSources', {}) else art
                    visible = partition(selected, cfg['partitions'][key])
                    if kind == 'leg':
                        visible = partition(visible, [(0, cfg['visibleLegCutY']), (255, cfg['visibleLegCutY']),
                                                      (255, 255), (0, 255)])
                        # The complete, approved hip cap is hidden by the common
                        # safety shorts. All visible articulated leg art is new.
                        root = partition(translate(base[key], dx, dy),
                                         [(0, 0), (255, 0), (255, cfg['rootClipY']), (0, cfg['rootClipY'])])
                        for hidden in cfg.get('hiddenCompletions', {}).get(key, []):
                            root.alpha_composite(partition(translate(base[key], dx, dy), hidden))
                        root.alpha_composite(visible)
                        parts[key] = root
                    else:
                        parts[key] = visible
        whole = compose(parts, order)
        target = OUT / 'layers' / f'{frame:02}'
        target.mkdir(exist_ok=True)
        for key, im in parts.items():
            im.save(target / f'{key}.png')
        whole.save(OUT / 'frames' / f'{frame:02}.png')
        editable(frame, parts, whole, order)
        frames.append(whole)
        bindings.append({'direction': 'down', 'clip': 'idle' if frame == 0 else 'walk', 'frame': frame,
                         'layers': {k: f'layers/{frame:02}/{k}.png' for k in ORDER}})
        motion.append({'direction': 'down', 'clip': 'idle' if frame == 0 else 'walk', 'frame': frame,
                       'facing': [0, 1], 'headToCanvas': [1, 0, 0, 1, 76 + dx, 61 + dy],
                       'bodyTranslation': [dx, dy], 'drawOrder': order,
                       'joints': cfg['joints'], 'sockets': cfg['sockets'],
                       'soleMarkers': cfg['soleMarkers'], 'support': cfg['support'],
                       'artApproval': 'idle r1 approval.json' if frame == 0 else None})
    strip = Image.new('RGBA', (256 * 9, 256))
    for i, im in enumerate(frames):
        strip.alpha_composite(im, (256 * i, 0))
    strip.save(OUT / 'strip.png')
    review(frames)
    manifest = {'schemaVersion': '1.0.0', 'id': 'p1-neutral-down-walk-r1', 'version': '1.0.0',
                'part': 'base', 'compatibility': {'rig': 'p1-chibi-v1', 'bodyProfile': 'p1-standard',
                                                'actionSet': 'locomotion-v1'},
                'mode': 'pose-map', 'slots': ORDER, 'directions': ['down'], 'clips': ['idle', 'walk'],
                'sourceFiles': [f'editable/{i:02}.{ext}' for i in range(9) for ext in ['ora', 'svg']],
                'bindings': bindings}
    (OUT / 'asset.json').write_text(json.dumps(manifest, indent=2) + '\n')
    registration = {'schemaVersion': '1.0.0', 'rig': 'p1-chibi-v1',
                    'status': 'down-walk-candidate-awaiting-artwork-review',
                    'bodyApproval': 'shared/idle-approval.json', 'artApproval': None,
                    'approvalArtifactRootInRepository': 'Art/Templates/P1-Neutral/down/r1',
                    'sourceCanvas': [1254, 1254], 'sourceToWorld': [.16, 0, 0, .16, 25, 38],
                    'alphaFitOrPerPartResize': False,
                    'durationMs': 120, 'slowDurationMs': 480, 'cycleFrames': list(range(1, 9)),
                    'headReference': 'shared/head-down.png',
                    'socketAngles': 'proposed vertical grip; weapon artwork not yet validated', 'frames': motion}
    (OUT / 'motion.json').write_text(json.dumps(registration, indent=2) + '\n')
    print('Exported approved idle + eight neutral walk poses, 72 layers, ORA/SVG, motion and review loops.')


if __name__ == '__main__':
    main()
