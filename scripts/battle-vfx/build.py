"""Build the five procedural pixel-art skill sheets.

usage: python3 build.py <out-dir>      # writes <asset>.png for every skill, at the original sheet size
       python3 build.py --assets       # writes straight into Sources/Resources/Assets.xcassets
"""
import os, sys
from pixelvfx import pack_sheet, Grid
from skills import SPECS, GENERATORS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def build(skill):
    asset, n, fps, cw, ch, cols, scale = SPECS[skill]
    frames = [GENERATORS[skill](f, n) for f in range(n)]
    return asset, pack_sheet(frames, scale, (cw, ch), cols)


if __name__ == '__main__':
    Grid.SUPER = 2   # 1 design px = 1 point on the stage, the same density as the character art (override: --super=1)
    args = [a for a in sys.argv[1:] if not a.startswith('--super=')]
    for a in sys.argv[1:]:
        if a.startswith('--super='): Grid.SUPER = int(a.split('=')[1])
    arg = args[0] if args else '.'
    for skill in SPECS:
        asset, sheet = build(skill)
        if arg == '--assets':
            path = os.path.join(ROOT, 'Sources/Resources/Assets.xcassets', asset + '.imageset', asset + '.png')
        else:
            os.makedirs(arg, exist_ok=True); path = os.path.join(arg, asset + '.png')
        sheet.save(path); print(path, sheet.size)
