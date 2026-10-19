#!/usr/bin/env python3
"""Build a reproducible standalone wardrobe source/review bundle."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Prototypes/P1-Wardrobe-v1.zip'


def main():
    files = {}
    trees = ['Art/Standards/P1-Parts-v1', 'Art/Parts/P1-v1',
             'Art/Templates/P1-Wardrobe/down/v1', 'Art/Templates/P1-Neutral/down/walk-r2',
             'Art/Templates/P1-Modular/down/v1']
    for tree in trees:
        for path in (ROOT / tree).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.name != 'download.json':
                files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    # Include the original neutral body's runtime/editable material and approval,
    # not its full older image-generation history or historical slow preview.
    original = ROOT / 'Art/Templates/P1-Neutral/down/walk-r1'
    for relative in ['asset.json', 'motion.json', 'approval.json', 'README.md',
                     'layers', 'frames', 'editable', 'shared']:
        target = original / relative
        for path in [target] if target.is_file() else target.rglob('*'):
            if path.is_file():
                files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for name in ['check-character-part.py', 'compose-character-parts.py', 'test-character-compositor.py',
                 'export-character-head-part.py', 'package-modular-head-review.py',
                 'export-wardrobe-part.py', 'repair-neutral-layer-ownership.py',
                 'package-wardrobe-review.py', 'validate-wardrobe-review.py', 'bundle-wardrobe-review.py']:
        files['scripts/' + name] = (ROOT / 'scripts' / name).read_bytes()
    files['requirements.txt'] = b'Pillow>=9.2\nnumpy\njsonschema\n'
    files['README.md'] = '''# P1 wardrobe source bundle v1

Open Art/Templates/P1-Wardrobe/down/v1/walk.gif for the normal 120ms preview,
or poses.png for idle00 + walk01-08. No HTML execution is needed.

Install Python3 dependencies with `python3 -m pip install -r requirements.txt`.
Run `python3 scripts/test-character-compositor.py` for 19 integration checks.

Assemble the actual parts with the unchanged generic compositor:

```sh
python3 scripts/compose-character-parts.py \\
  --catalog Art/Templates/P1-Wardrobe/down/v1/catalog.json \\
  --motion Art/Templates/P1-Wardrobe/down/v1/motion.json \\
  --base p1-neutral-down-walk-r2 \\
  --asset p1-hair-chestnut-v1 --asset p1-face-blue-v1 \\
  --asset p1-outfit-forester-v1 --asset p1-weapon-short-sword-v1 \\
  --direction down --out /tmp/p1-wardrobe
```

The common body r2 only reassigns48 pixels in frame07 to their anatomical leg.
Its nine body composites are pixel-identical to the approved r1. All24 new
combinations use r2; no appearance chooses a separate body. Motion changes
only its pinned base manifest SHA; pose geometry/order and engine are unchanged.

The heads and original neutral poses were user approved. The new outfit and
sword await art review. One down direction, one outfit and one sword do not
constitute a complete eight-direction game wardrobe.

The bundle includes raw sources/prompts, editable ORA/SVG, runtime PNGs,
manifests, all216 outputs and review tools. Full older body-generation and
direction-review history remains in the repository. Full historical protection
checks in validate-wardrobe-review.py require that complete repository.

See Art/Templates/P1-Wardrobe/down/v1/README.md for the Chinese detailed report.
'''.encode()
    for relative in files:
        if relative.endswith('.gif'):
            from PIL import Image
            import io
            with Image.open(io.BytesIO(files[relative])) as image:
                for i in range(image.n_frames):
                    image.seek(i)
                    assert image.info['duration'] == 120, 'bundle must contain only normal previews'
    inventory = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files['bundle-manifest.json'] = (json.dumps({'files': inventory}, indent=2) + '\n').encode()
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, 'w') as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo('P1-Wardrobe-v1/' + name, date_time=(2026, 10, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    print(json.dumps({'files': len(files), 'bytes': OUT.stat().st_size,
                      'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
