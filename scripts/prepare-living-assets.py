#!/usr/bin/env python3
"""Extract independently rendered objects and align direction frames for runtime assembly."""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'Art/Generated/LivingScene'
CATALOG = ROOT / 'Sources/Resources/Assets.xcassets'
manifest = {}
GAIT_PHASES = ['idle', 'contact-a', 'passing', 'contact-b']


def save_asset(name, image):
    path = CATALOG / (name + '.imageset')
    path.mkdir(exist_ok=True)
    image.save(path / (name + '.png'), optimize=True)
    (path / 'Contents.json').write_text(json.dumps({
        'info': {'author': 'xcode', 'version': 1},
        'images': [{'filename': name + '.png', 'idiom': 'universal'}]
    }, indent=2) + '\n')
    manifest[name] = {'width': image.width, 'height': image.height,
                      'decodedBytes': image.width * image.height * 4}


def main_figure(cell):
    """Ignore a neighboring row's stray boot pixels outside the main figure."""
    mask = cell.getchannel('A').point(lambda alpha: 255 if alpha > 80 else 0)
    bands = []
    start = None
    for y in range(cell.height + 1):
        occupied = y < cell.height and mask.crop((0, y, cell.width, y + 1)).getbbox() is not None
        if occupied and start is None:
            start = y
        elif not occupied and start is not None:
            bands.append((start, y))
            start = None
    if not bands:
        raise ValueError('Empty hero frame')
    top, bottom = max(bands, key=lambda band: band[1] - band[0])
    cell = cell.crop((0, top, cell.width, bottom))
    bounds = cell.getchannel('A').point(lambda alpha: 255 if alpha > 80 else 0).getbbox()
    return cell.crop(bounds)


save_asset('MeadowGround', Image.open(RAW / 'ground.png').convert('RGB'))

# Regions follow the actual atlas's transparent gutters, rather than assuming equal object widths.
terrain_regions = [
    ('OakA', (0, 0, 535, 580)), ('OakB', (535, 0, 1090, 580)),
    ('Pines', (1090, 0, 1536, 580)), ('RockLow', (0, 580, 550, 1024)),
    ('RockHigh', (550, 580, 1110, 1024)), ('RockSmall', (1110, 580, 1536, 1024))
]
props_regions = [
    ('CampTent', (0, 0, 615, 580)), ('WatchTower', (615, 0, 1000, 580)),
    ('Shrub', (1000, 0, 1536, 580)), ('Fence', (0, 580, 500, 1024)),
    ('Flowers', (500, 580, 1070, 1024)), ('Banner', (1070, 580, 1536, 1024))
]
for source_name, regions in [('terrain-atlas.png', terrain_regions), ('props-atlas.png', props_regions)]:
    source = Image.open(RAW / source_name).convert('RGBA')
    assert source.size == (1536, 1024)
    for name, region in regions:
        override = RAW / f'{name.lower()}-v1.3.png'
        cell = Image.open(override).convert('RGBA') if override.exists() else source.crop(region)
        bounds = cell.getchannel('A').point(lambda alpha: 255 if alpha > 48 else 0).getbbox()
        if bounds is None:
            raise ValueError('Empty object: ' + name)
        sprite = cell.crop(bounds)
        if override.exists():
            sprite.thumbnail((576, 576), Image.Resampling.NEAREST)
        # Keep native object resolution; a transparent gutter protects shader deformation edges.
        padded = Image.new('RGBA', (sprite.width + 16, sprite.height + 16))
        padded.alpha_composite(sprite, (8, 8))
        save_asset(name, padded)

# Keep the animation source and packing rules reproducible alongside environment art.
import runpy
gait = runpy.run_path(str(ROOT / 'scripts/prepare-gait-assets.py'))
gait['prepare_gait_assets'](ROOT, save_asset, manifest)

(ROOT / 'Art/Generated/LivingScene/asset-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Prepared', len(manifest), 'independent assets; decoded texture budget:',
      round(sum(item['decodedBytes'] for item in manifest.values()) / (1024 * 1024), 1), 'MiB')
