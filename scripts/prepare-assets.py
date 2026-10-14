#!/usr/bin/env python3
"""Normalize generated animation cells; retain source artwork in Art/Generated."""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'Sources/Resources/Assets.xcassets'


def catalog(path, images=None, **extra):
    data = {'info': {'author': 'xcode', 'version': 1}, **extra}
    if images is not None:
        data['images'] = images
    (path / 'Contents.json').write_text(json.dumps(data, indent=2) + '\n')


catalog(ASSETS)
terrain = Image.open(ROOT / 'Art/Generated/meadow-background.png').convert('RGB')
terrain.save(ASSETS / 'MapBackground.imageset/map.png', optimize=True)
catalog(ASSETS / 'MapBackground.imageset', [{'filename': 'map.png', 'idiom': 'universal'}])

source = Image.open(ROOT / 'Art/Generated/heroes-source.png').convert('RGBA')
sheet = Image.new('RGBA', (1024, 768))
for row in range(3):
    for col in range(4):
        cell = source.crop((col * source.width // 4, row * source.height // 3,
                            (col + 1) * source.width // 4, (row + 1) * source.height // 3))
        bounds = cell.getchannel('A').point(lambda alpha: 255 if alpha > 100 else 0).getbbox()
        if bounds is None:
            raise ValueError('Empty animation cell')
        sprite = cell.crop(bounds)
        width = round(sprite.width * 160 / sprite.height)
        sprite = sprite.resize((width, 160), Image.Resampling.NEAREST)
        sheet.alpha_composite(sprite, (col * 256 + (256 - width) // 2, row * 256 + 224 - 160))
sheet.save(ASSETS / 'Heroes.imageset/heroes.png', optimize=True)
catalog(ASSETS / 'Heroes.imageset', [{'filename': 'heroes.png', 'idiom': 'universal'}])

# A crop of the same camp artwork keeps the launcher icon visually consistent.
cx, cy = terrain.width * .28, terrain.height * .49
edge = terrain.height * .44
icon = terrain.crop((round(cx - edge / 2), round(cy - edge / 2),
                     round(cx + edge / 2), round(cy + edge / 2)))
icon.resize((1024, 1024), Image.Resampling.LANCZOS).save(ASSETS / 'AppIcon.appiconset/icon.png')
catalog(ASSETS / 'AppIcon.appiconset', [
    {'filename': 'icon.png', 'idiom': 'universal', 'platform': 'ios', 'size': '1024x1024'}
])
launch = ASSETS / 'LaunchColor.colorset'
launch.mkdir(exist_ok=True)
catalog(launch, colors=[{'idiom': 'universal', 'color': {'color-space': 'srgb',
        'components': {'red': '0.250', 'green': '0.320', 'blue': '0.150', 'alpha': '1.000'}}}])
print('Prepared map, 12 normalized animation frames, app icon and launch color.')
