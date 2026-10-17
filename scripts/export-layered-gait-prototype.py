#!/usr/bin/env python3
"""Export one layered, outfit-swappable walk for OpenToonz/Tahoma2D import.

The current application still consumes complete RGBA poses. This prototype
exports matching transparent PNG levels so an artist can revise a layer or
swap a gear level before the atlas is packed for the app.
"""
from pathlib import Path
import json
import shutil
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build/layered-gait-prototype'
EXPORT = WORK / 'P1-Down'
ARCHIVE = ROOT / 'Art/Prototypes/P1-Down-Layered-Walk.zip'
CELL = 256


def composite(parts):
    result = Image.new('RGBA', (CELL, CELL))
    for part in parts:
        result.alpha_composite(part)
    return result


def recolor_boots(source):
    """Make a blue colorway while retaining the authored shoe pixels/shape."""
    rgba = np.asarray(source).copy()
    rgb = rgba[:, :, :3].astype(np.float32)
    luma = (rgb[:, :, 0] * .2126 + rgb[:, :, 1] * .7152 + rgb[:, :, 2] * .0722) / 255
    # Cool leather dye; luminance preserves the original highlights and shading.
    dye = np.array([.22, .43, .88], dtype=np.float32)
    rgba[:, :, :3] = np.clip((luma[:, :, None] * dye[None, None, :] + .035) * 255, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = np.asarray(source)[:, :, 3]
    return Image.fromarray(rgba)


def write_ora(path, layers, merged):
    """Write a single layered OpenRaster frame for inspection in paint tools."""
    stack = ['<image version="0.0.1" w="256" h="256" name="P1 Down boots colorway">', '<stack>']
    files = []
    for index, (name, image) in enumerate(reversed(layers)):
        filename = f'data/layer{index}.png'
        stack.append(f'<layer name="{name}" src="{filename}" opacity="1.0" visibility="visible" composite-op="svg:src-over" x="0" y="0"/>')
        files.append((filename, image))
    stack.extend(['</stack>', '</image>'])
    xml = ''.join(stack).encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        archive.writestr('stack.xml', xml)
        for filename, image in files:
            import io
            buffer = io.BytesIO(); image.save(buffer, format='PNG')
            archive.writestr(filename, buffer.getvalue())
        import io
        buffer = io.BytesIO(); merged.save(buffer, format='PNG')
        archive.writestr('mergedimage.png', buffer.getvalue())
        thumb = merged.copy(); thumb.thumbnail((256, 256), Image.Resampling.LANCZOS)
        buffer = io.BytesIO(); thumb.save(buffer, format='PNG')
        archive.writestr('Thumbnails/thumbnail.png', buffer.getvalue())


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    if ARCHIVE.exists(): ARCHIVE.unlink()
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location('gait_assets', ROOT / 'scripts/prepare-gait-assets.py')
    gait = module_from_spec(spec); spec.loader.exec_module(gait)
    manifest = {}
    frame_records = []
    ora_layers = []
    comparison = Image.new('RGBA', (6 * 2 * CELL, 4 * (CELL + 28)), (38, 42, 38, 255))
    font = ImageFont.load_default()

    def export(hero, facing, frame_number, body, ordered_layers, reference):
        if hero != 1 or facing != 0: return
        leg_parts = [part for _, name, part in ordered_layers if not name.endswith('-shoe')]
        shoe_parts = [part for _, name, part in ordered_layers if name.endswith('-shoe')]
        legs = composite(leg_parts)
        boots = composite(shoe_parts)
        blue_boots = recolor_boots(boots)
        original = gait.clean_gutter(composite([legs, boots, body]))
        # Preserve the source rig's per-segment depth sorting for the baked
        # outfit. Grouped artist layers remain available for editing, while
        # the game atlas avoids the small ankle overlap from a fixed 3-layer stack.
        blue_parts = [recolor_boots(part) if name.endswith('-shoe') else part
                      for _, name, part in ordered_layers]
        blue = gait.clean_gutter(composite([*blue_parts, body]))
        if frame_number == 12:
            ora_layers.extend([
                (name.replace('-', ' '), recolor_boots(part) if name.endswith('-shoe') else part.copy())
                for _, name, part in ordered_layers
            ])
            ora_layers.append(('Body', body.copy()))
        stem = f'{frame_number:04d}.png'
        for name, image in [('Legs', legs), ('Boots', boots), ('Body', body),
                            ('BlueBoots', blue_boots), ('Reference', reference),
                            ('Reassembled', original), ('BlueVariant', blue)]:
            image.save(EXPORT / f'P1-Down-{name}.{stem}', optimize=True)
        delta = np.abs(np.asarray(reference).astype(np.int16) - np.asarray(original).astype(np.int16))
        changed = int(np.any(delta != 0, axis=2).sum())
        max_channel_delta = int(delta.max(initial=0))
        frame_records.append({'frame': frame_number, 'reassemblyDifferentPixels': changed,
                              'maximumChannelDelta': max_channel_delta})
        col = (frame_number - 1) % 6
        row = (frame_number - 1) // 6
        x = col * 2 * CELL
        y = row * (CELL + 28)
        comparison.alpha_composite(reference, (x, y + 28))
        comparison.alpha_composite(blue, (x + CELL, y + 28))

    # Export callback data without rewriting the production animation atlases.
    def asset_sink(name, image):
        manifest[name] = {'width': image.width, 'height': image.height}

    gait.prepare_gait_assets(ROOT, asset_sink, manifest, layer_export=export, write_metadata=False)
    draw = ImageDraw.Draw(comparison)
    for row in range(4):
        for col in range(6):
            number = row * 6 + col + 1
            y = row * (CELL + 28)
            x = col * 2 * CELL
            draw.text((x + 6, y + 6), f'Pose {number:02d} · original', font=font, fill=(240, 236, 216, 255))
            draw.text((x + CELL + 6, y + 6), f'Pose {number:02d} · blue boots', font=font, fill=(240, 236, 216, 255))
    comparison.save(ROOT / 'Media/LayeredGait-P1-Down.png', optimize=True)

    ora_dir = ROOT / 'Art/Prototypes'
    ora_dir.mkdir(parents=True, exist_ok=True)
    write_ora(ora_dir / 'P1-Down-BlueBoots-Frame12.ora',
              ora_layers,
              Image.open(EXPORT / 'P1-Down-BlueVariant.0012.png').convert('RGBA'))

    for name in ['Legs', 'Boots', 'Body', 'BlueBoots', 'Reference', 'Reassembled', 'BlueVariant']:
        level = EXPORT / f'P1-Down-{name}'
        images = sorted(EXPORT.glob(f'P1-Down-{name}.*.png'))
        assert len(images) == 24, f'{name} sequence must contain 24 frames'
    # The app consumes a whole-pose atlas. Bake the layered colorway into a
    # 24-cell strip so the preview uses the same efficient frame selection.
    atlas = Image.new('RGBA', (CELL * 24, CELL))
    for index in range(24):
        frame = Image.open(EXPORT / f'P1-Down-BlueVariant.{index + 1:04d}.png').convert('RGBA')
        atlas.alpha_composite(frame, (index * CELL, 0))
    atlas.save(EXPORT / 'P1-Down-BlueVariant-Atlas.png', optimize=True)
    asset_dir = ROOT / 'Sources/Resources/Assets.xcassets/LayeredP1BlueVariant.imageset'
    asset_dir.mkdir(parents=True, exist_ok=True)
    atlas.save(asset_dir / 'LayeredP1BlueVariant.png', optimize=True)
    (asset_dir / 'Contents.json').write_text(json.dumps({
        'info': {'author': 'xcode', 'version': 1},
        'images': [{'filename': 'LayeredP1BlueVariant.png', 'idiom': 'universal'}]
    }, indent=2) + '\n')
    max_changed = max(item['reassemblyDifferentPixels'] for item in frame_records)
    result = {'format': 1, 'hero': 'P1', 'facing': 'Down', 'frameCount': 24,
              'cellSize': [CELL, CELL], 'layerOrderBackToFront': ['Legs', 'Boots', 'Body'],
              'previewColorway': 'blue dyed version of the existing rigid shoe pixels',
              'frameComparison': frame_records, 'maximumDifferentPixels': max_changed}
    (EXPORT / 'prototype.json').write_text(json.dumps(result, indent=2) + '\n')
    (EXPORT / 'IMPORT-README.txt').write_text(
        'Layered P1 downward walk prototype\n'
        '\n'
        'Import each numbered PNG sequence as one image level in OpenToonz or Tahoma2D.\n'
        'All sequences contain 24 aligned 256x256 RGBA frames for one walk cycle.\n'
        'Use Legs, Boots (or BlueBoots), then Body, from back to front.\n'
        'Reference is the exact existing game pose and can be used as a guide layer.\n'
        'BlueVariant is a precomposed shoe colorway example.\n'
        'Reassembled shows the grouped-layer result; the app atlas instead preserves per-frame segment depth order.\n'
        '\n'
        'BlueVariant-Atlas is also packed into the app for the gait-test comparison preview.\n'
        'The regular map characters still use their existing full-pose atlases.\n'
        'OpenToonz/Tahoma2D GUI import was not run in the headless build workspace.\n'
    )
    with zipfile.ZipFile(ARCHIVE, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(EXPORT.iterdir()):
            archive.write(path, path.relative_to(EXPORT.parent))
    print(json.dumps({'archive': str(ARCHIVE), 'frameCount': len(frame_records),
                      'maximumDifferentPixels': max_changed,
                      'appAtlas': str(asset_dir / 'LayeredP1BlueVariant.png')}, indent=2))


if __name__ == '__main__':
    main()
