#!/usr/bin/env python3
"""Export the approved down gait as a modular, offline customization pilot.

Artwork is supplied by approved source PNGs and imagegen part originals. This is
the reproducible template renderer: masks, palette material, fixed registration,
anchor transforms and compositing. It never redraws or transforms approved legs.
"""
from __future__ import annotations

import base64
import hashlib
import io
import itertools
import json
import math
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Down/v1'
REF = ROOT / 'Art/Review/P1/directions/down/revisions/r1/frames'
SIZE = (256, 256)
CHOICES = {'hair': ['chestnut', 'silver'], 'face': ['blue', 'amber'],
           'outfit': ['traveler', 'ranger'], 'weapon': ['empty', 'sword']}
ORDER = ['body', 'weapon', 'outfit', 'face', 'hair', 'hands']


def blank():
    return Image.new('RGBA', SIZE)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, 'PNG')
    return b.getvalue()


def uri(im):
    return 'data:image/png;base64,' + base64.b64encode(png_bytes(im)).decode()


def layer(im, mask):
    """Assign source pixels, without altering colour or resampling the pose."""
    a = np.array(im)
    a[~mask] = 0
    return Image.fromarray(a)


def poly(points):
    m = Image.new('1', SIZE)
    ImageDraw.Draw(m).polygon([tuple(p) for p in points], fill=1)
    return np.array(m, dtype=bool)


def composite(layers):
    im = blank()
    for part in layers:
        im.alpha_composite(part)
    return im


def selected_layers(parts, selection):
    filled = selection['hair'] != 'chestnut' or selection['face'] != 'blue'
    return [(slot, parts['body-filled' if filled else 'body'] if slot == 'body'
             else parts['hands'] if slot == 'hands'
             else parts[f'{slot}:{selection[slot]}']) for slot in ORDER]


def asset(name, size):
    im = Image.open(OUT / 'art-source' / f'{name}.png').convert('RGBA')
    # Ignore only faint outside specks when locating the drawing. Original kept.
    bounds = im.getchannel('A').point(lambda a: 255 if a > 16 else 0).getbbox()
    return im.crop(bounds).resize(tuple(size), Image.Resampling.LANCZOS), bounds


def placed(im, xy):
    result = blank()
    result.alpha_composite(im, tuple(map(round, xy)))
    return result


def sword_layer(sprite, anchor, pivot, angle):
    """Single rigid attachment, rotation about the annotated grip, never feet."""
    r = math.radians(angle)
    c, s = math.cos(r), math.sin(r)
    x, y = anchor
    px, py = pivot
    return sprite.transform(SIZE, Image.Transform.AFFINE,
                            (c, s, px-c*x-s*y, -s, c, py+s*x-c*y),
                            Image.Resampling.BICUBIC)


def ranger_material(im):
    """A clothing-only material shader; face, hair, hands and legs excluded."""
    a = np.array(im)
    rgb = a[:, :, :3].astype(float) / 255
    mask = ((rgb[:, :, 2] > rgb[:, :, 0]*1.65) &
            (rgb[:, :, 2] > rgb[:, :, 1]*1.25) & (a[:, :, 3] > 0))
    # Blue material's value shades the new forest-green material; retain outline.
    v = rgb.max(axis=2)
    mask &= v > .10
    mapped = np.stack([v*.26, v*.50, v*.35], axis=2)
    a[:, :, :3][mask] = np.rint(mapped[mask]*255).astype(np.uint8)
    return Image.fromarray(a)


def write_ora(path, layers, merged, underpaint=None):
    root = ET.Element('image', version='0.0.1', w='256', h='256', name=path.stem)
    stack = ET.SubElement(root, 'stack')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        def put(name, data, stored=False):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        put('mimetype', 'image/openraster', stored=True)
        for i, (name, im) in enumerate(reversed(layers)):
            src = f'data/layer{i}.png'
            ET.SubElement(stack, 'layer', name=name, src=src, x='0', y='0',
                          opacity='1.0', visibility='visible',
                          **{'composite-op': 'svg:src-over'})
            put(src, png_bytes(im))
        if underpaint is not None:
            ET.SubElement(stack, 'layer', name='underpaint (enable when hiding outfit/hair)',
                          src='data/underpaint.png', x='0', y='0', opacity='1.0',
                          visibility='hidden', **{'composite-op': 'svg:src-over'})
            put('data/underpaint.png', png_bytes(underpaint))
        put('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))
        put('mergedimage.png', png_bytes(merged))
        put('Thumbnails/thumbnail.png', png_bytes(merged.resize((128, 128))))


def write_svg(path, layers, underpaint=None):
    ns = 'http://www.w3.org/2000/svg'
    # OpenRaster is the primary editable format; SVG also has named groups.
    ET.register_namespace('', ns)
    root = ET.Element(f'{{{ns}}}svg', width='256', height='256', viewBox='0 0 256 256')
    if underpaint is not None:
        g = ET.SubElement(root, f'{{{ns}}}g', id='underpaint', style='display:none')
        ET.SubElement(g, f'{{{ns}}}image', width='256', height='256', href=uri(underpaint))
    for name, im in layers:
        g = ET.SubElement(root, f'{{{ns}}}g', id=name)
        ET.SubElement(g, f'{{{ns}}}title').text = name
        ET.SubElement(g, f'{{{ns}}}image', x='0', y='0', width='256', height='256',
                      href=uri(im), **{'image-rendering': 'pixelated'})
    path.write_text(ET.tostring(root, encoding='unicode') + '\n')


def save_gif(path, frames, ms):
    # Opaque review backdrop avoids GIF palette transparency artefacts.
    frames = [composite_review(f).convert('RGB').quantize(colors=255)
              for f in frames]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms,
                   loop=0, disposal=2, optimize=False)


def composite_review(im):
    bg = Image.new('RGBA', im.size, '#18252b')
    bg.alpha_composite(im)
    return bg


def main():
    specs = json.loads((OUT / 'source/frame-specs.json').read_text())
    for d in ['reference', 'layers', 'appearances', 'editable', 'review']:
        (OUT / d).mkdir(exist_ok=True)
    manifest = {'schemaVersion': 1, 'name': 'P1 Down Modular Pilot v1',
                'direction': 'down', 'canvas': [256, 256],
                'coordinateSystem': specs['space'], 'choices': CHOICES,
                'layerOrderBackToFront': ORDER, 'idleFrame': 0,
                'walkFrames': list(range(1, 9)), 'normalFrameMs': 120,
                'slowFrameMs': 480, 'artStatus': 'pilot-awaiting-user-review',
                'motionBaseline': 'approved P1 down r1', 'frames': []}
    web = {'manifest': manifest, 'assets': {}, 'references': []}
    all_parts = []
    for f in specs['frames']:
        fid = f['id']
        src = Image.open(REF / f'{fid}.png').convert('RGBA')
        shutil.copyfile(REF / f'{fid}.png', OUT / 'reference' / f'{fid}.png')
        arr = np.array(src)
        yy, xx = np.indices((256, 256))
        hx, hy = f['head']
        face_path = [(hx+x, hy+y) for x, y in specs['headFacePolygonOffsets']]
        face_mask = poly(face_path)
        head_mask = (yy < hy+7) | face_mask
        # Source scarf crosses the cheek silhouette: keep it in the outfit slot.
        blue = ((arr[:, :, 2].astype(float) > arr[:, :, 0]*1.65) &
                (arr[:, :, 2].astype(float) > arr[:, :, 1]*1.25))
        head_mask &= ~(blue & ((yy > hy+6) | (~face_mask & (yy > hy-2))))
        face_mask &= head_mask
        hair_mask = head_mask & ~face_mask
        hands_mask = np.zeros((256, 256), bool)
        for x0, y0, x1, y1 in f['handBoxes']:
            hands_mask |= (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
        hands_mask &= ~head_mask & ~blue
        wx, wy = f['waist']
        # Hem follows the approved split coat; shorts/boots remain in body slot.
        hem = [(60, 125), (195, 125), (195, wy+15), (wx+24, wy+15),
               (wx+19, wy+24), (wx+10, wy+12), (wx+6, wy+17),
               (wx-8, wy+17), (wx-12, wy+13), (wx-20, wy+25),
               (wx-28, wy+15), (60, wy+15)]
        cloth_mask = (poly(hem) | (blue & (yy < wy+30))) & ~head_mask & ~hands_mask
        body_mask = ~(head_mask | hands_mask | cloth_mask)
        body = layer(src, body_mask)
        skin, _ = asset('head_blank', specs['parts']['head_blank']['size'])
        skin = placed(skin, [hx-24, hy-32])
        # The approved PNG has alpha ~253 even inside the silhouette. Keep its
        # default reassembly untouched; head replacements use a filled body.
        skin = layer(skin, head_mask & (arr[:, :, 3] > 96))
        torso, _ = asset('body_torso', [34, 45])
        torso = placed(torso, [wx-17, wy-27])
        torso = layer(torso, cloth_mask & (arr[:, :, 3] > 96) & (yy < wy+17))
        underpaint = composite([skin, torso])
        filled_body = composite([body, underpaint])
        hair = layer(src, hair_mask)
        face = layer(src, face_mask)
        outfit = layer(src, cloth_mask)
        hands = layer(src, hands_mask)
        silver, _ = asset('hair_silver', specs['parts']['hair_silver']['size'])
        silver = placed(silver, [hx-35, hy-50])
        amber, _ = asset('face_amber', specs['parts']['face_amber']['size'])
        amber = placed(amber, [hx-20, hy-11])
        # Keep the original ears and outer cheek contour while replacing features.
        inner = (xx > hx-18) & (xx < hx+19) & (yy > hy-11) & (yy < hy+15)
        amber = composite([layer(face, ~inner), amber])
        ranger = ranger_material(outfit)
        tx, ty, tw, th = f['torsoBox']
        vest, _ = asset('ranger_vest', [tw, th])
        vest = placed(vest, [tx, ty])
        # The replaceable torso panel must remain behind existing hands/scarf.
        chest = poly([(wx-15, wy-18), (wx+15, wy-18), (wx+15, wy+17),
                      (wx-15, wy+17)]) & cloth_mask & ~((yy < hy+24) & blue)
        vest = layer(vest, chest)
        ranger = composite([ranger, vest])
        sword, _ = asset('sword', specs['parts']['sword']['size'])
        sword = sword_layer(sword, f['rightHand'], specs['parts']['sword']['pivot'], f['swordAngleDeg'])
        parts = {'body': body, 'body-filled': filled_body, 'head-base': skin,
                 'underpaint': underpaint,
                 'hair:chestnut': hair, 'hair:silver': silver,
                 'face:blue': face, 'face:amber': amber,
                 'outfit:traveler': outfit, 'outfit:ranger': ranger,
                 'weapon:empty': blank(), 'weapon:sword': sword, 'hands': hands}
        frame_dir = OUT / 'layers' / fid
        frame_dir.mkdir(exist_ok=True)
        for key, im in parts.items():
            filename = key.replace(':', '-') + '.png'
            im.save(frame_dir / filename)
            web['assets'][f'{fid}/{key}'] = uri(im)
        # Foot contact markers are annotations, measured from the original boot
        # silhouettes; never used to re-register or scale the approved pose.
        feet = {}
        for name, xlo, xhi in [('right', 100, wx), ('left', wx, 150)]:
            roi = (arr[:, :, 3] > 96) & (yy > 187) & (xx >= xlo) & (xx < xhi)
            ys, xs = np.where(roi)
            feet[name] = [int(np.median(xs[ys >= ys.max()-2])), int(ys.max()+1)]
        fm = {k: f[k] for k in ['id', 'phase', 'contact', 'head', 'neck', 'waist',
                               'rightHand', 'leftHand', 'hipRight', 'hipLeft',
                               'kneeRight', 'kneeLeft', 'ankleRight', 'ankleLeft',
                               'swordAngleDeg']}
        fm['soleMarkers'] = feet
        fm['referenceSHA256'] = sha(REF / f'{fid}.png')
        manifest['frames'].append(fm)
        web['references'].append(uri(src))
        all_parts.append(parts)

    combinations = []
    for values in itertools.product(*CHOICES.values()):
        selection = dict(zip(CHOICES, values))
        key = '-'.join(values)
        frames = []
        for i, parts in enumerate(all_parts):
            layers = selected_layers(parts, selection)
            frames.append(composite([im for _, im in layers]))
        atlas = Image.new('RGBA', (256*9, 256))
        for i, im in enumerate(frames):
            atlas.alpha_composite(im, (256*i, 0))
        atlas.save(OUT / 'appearances' / f'{key}.png')
        combinations.append({'key': key, 'selection': selection, 'atlas': f'appearances/{key}.png'})
        if key in ['chestnut-blue-traveler-empty', 'silver-amber-ranger-sword']:
            ed = OUT / 'editable' / key
            ed.mkdir(exist_ok=True)
            for i, parts in enumerate(all_parts):
                layers = selected_layers(parts, selection)
                hidden = parts['underpaint'] if key == 'chestnut-blue-traveler-empty' else None
                write_ora(ed / f'{i:02}.ora', layers, frames[i], hidden)
                write_svg(ed / f'{i:02}.svg', layers, hidden)
            save_gif(OUT / 'review' / f'{key}.gif', frames[1:], 120)
            save_gif(OUT / 'review' / f'{key}-slow.gif', frames[1:], 480)
    manifest['combinations'] = combinations
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    web['manifest'] = manifest
    (OUT / 'source/preview-data.json').write_text(json.dumps(web, ensure_ascii=False, separators=(',', ':'))+'\n')
    template = (ROOT / 'scripts/character-template-preview.html').read_text()
    (OUT / 'preview.html').write_text(template.replace('/*__TEMPLATE_DATA__*/', json.dumps(web, ensure_ascii=False, separators=(',', ':'))))
    # A compact visual review shows the approved original and one combined look.
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    board = Image.new('RGBA', (9*192, 2*216+48), '#18252b')
    d = ImageDraw.Draw(board)
    d.text((16, 8), 'APPROVED MOTION / MODULAR OUTFIT PILOT - 00 idle, 01-08 walk', font=font, fill='#c8dce3')
    for row, key in enumerate(['chestnut-blue-traveler-empty', 'silver-amber-ranger-sword']):
        atlas = Image.open(OUT / 'appearances' / f'{key}.png')
        for i in range(9):
            frame = atlas.crop((256*i, 0, 256*(i+1), 256)).resize((192, 192), Image.Resampling.NEAREST)
            board.alpha_composite(frame, (i*192, 48+row*216))
            d.text((i*192+12, 48+row*216), f'{i:02}', font=font, fill='#a0bac7')
    board.convert('RGB').save(OUT / 'review/comparison.png')
    # Readable paired loops for chat review, from the same registered cells.
    original = Image.open(OUT / 'appearances/chestnut-blue-traveler-empty.png')
    custom = Image.open(OUT / 'appearances/silver-amber-ranger-sword.png')
    paired = []
    for i in range(1, 9):
        canvas = Image.new('RGBA', (840, 580), '#18252b')
        d = ImageDraw.Draw(canvas)
        d.text((18, 12), 'APPROVED GAIT', font=font, fill='#b8cdd3')
        d.text((438, 12), f'MODULAR LOOK / PILOT   {i:02}/08', font=font, fill='#c4d7ae')
        for col, atlas in enumerate([original, custom]):
            frame = atlas.crop((i*256+60, 54, i*256+200, 234)).resize((420, 540), Image.Resampling.NEAREST)
            canvas.alpha_composite(frame, (col*420, 40))
        paired.append(canvas)
    save_gif(OUT / 'review/walk-compare.gif', paired, 120)
    save_gif(OUT / 'review/walk-compare-slow.gif', paired, 480)
    print(f'Exported {len(combinations)} appearances, 9 poses each, 18 ORA + SVG sources, offline preview.')


if __name__ == '__main__':
    main()
