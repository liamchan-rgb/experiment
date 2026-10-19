#!/usr/bin/env python3
"""Compose compatible manifest-defined art on an authored motion module.

Asset identifiers are lookup keys only. Artwork is never fitted by its bounds,
recoloured, repaired, or used to select a different body or another appearance.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('part_contract', Path(__file__).with_name('check-character-part.py'))
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(binding):
    return binding['direction'], binding['clip'], binding['frame']


def place(image, matrix, canvas):
    """Apply the motion's explicit local-to-world affine, without art fitting."""
    if len(matrix) != 6 or not all(math.isfinite(v) for v in matrix):
        raise ValueError('invalid attachment transform')
    a, b, c, d, tx, ty = matrix
    det = a * d - b * c
    if abs(det) < 1e-10:
        raise ValueError('singular attachment transform')
    ys, xs = np.where(np.array(image.getchannel('A')) > 8)
    if len(xs):
        wx, wy = a * xs + c * ys + tx, b * xs + d * ys + ty
        if wx.min() < 0 or wy.min() < 0 or wx.max() >= canvas[0] or wy.max() >= canvas[1]:
            raise ValueError('attached artwork crosses the pose canvas; no automatic fitting')
    if (a, b, c, d) == (1, 0, 0, 1) and tx == round(tx) and ty == round(ty):
        out = Image.new('RGBA', canvas)
        out.paste(image, (round(tx), round(ty)))
        return out
    # Motion coordinates name pixel centres by integer index. Pillow evaluates
    # its inverse affine at half-integer pixel centres; translate conventions so
    # a rotated weapon's authored pivot remains exactly on the grip pixel.
    inverse = (d / det, -c / det, (c * ty - d * tx) / det + .5 - (d - c) / (2 * det),
               -b / det, a / det, (b * tx - a * ty) / det + .5 - (a - b) / (2 * det))
    return image.transform(canvas, Image.Transform.AFFINE, inverse, Image.Resampling.NEAREST)


class Compositor:
    def __init__(self, root, catalog, motion, production=False):
        self.root = Path(root).resolve()
        self.catalog_path = Path(catalog)
        self.motion_path = Path(motion)
        self.motion = json.loads(self.motion_path.read_text())
        self.production = production
        if production and self.motion.get('status') != 'locked':
            raise ValueError('production requires locked motion data')
        self.canvas = tuple(self.motion['canvas'])
        self.frames = {}
        for frame in self.motion['frames']:
            k = key(frame)
            if k in self.frames:
                raise ValueError(f'duplicate motion frame {k}')
            if len(frame['drawOrder']) != len(set(frame['drawOrder'])):
                raise ValueError(f'duplicate slots in draw order {k}')
            self.frames[k] = frame
        self.entries = {}
        for entry in json.loads(self.catalog_path.read_text())['assets']:
            if entry['id'] in self.entries:
                raise ValueError('duplicate catalog identifier')
            self.entries[entry['id']] = contract.safe_file(self.root, entry['manifest'])
        self.assets = {}
        self.images = {}

    def asset(self, identifier):
        if identifier not in self.assets:
            if identifier not in self.entries:
                raise ValueError(f'unknown asset {identifier}')
            path = self.entries[identifier]
            errors = contract.check_asset(path, production=self.production)
            if errors:
                raise ValueError(f'invalid asset {identifier}: ' + '; '.join(errors))
            data = json.loads(path.read_text())
            if data['id'] != identifier:
                raise ValueError('catalog identifier differs from manifest')
            self.assets[identifier] = (data, path, {key(b): b for b in data['bindings']})
        return self.assets[identifier]

    def image(self, folder, relative):
        path = contract.safe_file(folder, relative)
        if path not in self.images:
            with Image.open(path) as im:
                if im.mode != 'RGBA' or im.format != 'PNG':
                    raise ValueError('layer must be an RGBA PNG')
                self.images[path] = im.copy()
        return self.images[path]

    def layers(self, base, selected, direction, clip, frame):
        k = direction, clip, frame
        if k not in self.frames:
            raise ValueError(f'motion does not supply {k}')
        if len(set([base, *selected])) != len([base, *selected]):
            raise ValueError('asset selected more than once')
        base_data, base_path, _ = self.asset(base)
        if base_data['part'] != 'base':
            raise ValueError('base selection must be a complete body package')
        if base_data['compatibility'] != self.motion['compatibility']:
            raise ValueError('base/motion compatibility mismatch')
        pinned = self.motion.get('baseManifestSHA256')
        if pinned and digest(base_path) != pinned:
            raise ValueError('base differs from the motion module authoring reference')
        layers = {}
        for index, identifier in enumerate([base, *selected]):
            asset, path, bindings = self.asset(identifier)
            if index and asset['part'] == 'base':
                raise ValueError('an appearance cannot supply another body')
            if asset['compatibility'] != base_data['compatibility']:
                raise ValueError('appearance/body compatibility mismatch')
            if k not in bindings:
                raise ValueError(f'{identifier} does not supply {k}; no fallback appearance')
            for slot, relative in bindings[k]['layers'].items():
                if slot in layers:
                    raise ValueError(f'multiple assets own {slot}')
                image = self.image(path.parent, relative)
                mode = asset['mode']
                if mode == 'head-local':
                    image = place(image, self.frames[k]['headToCanvas'], self.canvas)
                elif mode == 'socket':
                    socket = self.frames[k]['sockets'][asset['socket']]
                    if socket['angleDeg'] is None:
                        raise ValueError('uncalibrated socket orientation')
                    angle = math.radians(socket['angleDeg'])
                    cosine, sine = math.cos(angle), math.sin(angle)
                    px, py = asset['pivot']
                    x, y = socket['position']
                    image = place(image, [cosine, sine, -sine, cosine,
                                          x - cosine * px + sine * py,
                                          y - sine * px - cosine * py], self.canvas)
                elif mode != 'pose-map':
                    raise ValueError(f'unsupported drawing space {mode}')
                if image.size != self.canvas:
                    raise ValueError('pose-map canvas mismatch; no automatic resizing')
                layers[slot] = image.copy()
        order = self.frames[k]['drawOrder']
        missing = set(layers) - set(order)
        if missing:
            raise ValueError(f'motion draw order omits {sorted(missing)}')
        return [(slot, layers[slot]) for slot in order if slot in layers]

    def render(self, base, selected, direction, clip, frame):
        out = Image.new('RGBA', self.canvas)
        for slot, image in self.layers(base, selected, direction, clip, frame):
            out.alpha_composite(image)
        return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--motion', type=Path, required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--asset', action='append', default=[])
    p.add_argument('--direction', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--production', action='store_true')
    args = p.parse_args()
    try:
        compositor = Compositor(args.root, args.catalog, args.motion, args.production)
        args.out.mkdir(parents=True, exist_ok=True)
        output = []
        for direction, clip, frame in sorted(compositor.frames):
            if direction != args.direction:
                continue
            im = compositor.render(args.base, args.asset, direction, clip, frame)
            name = f'{clip}-{frame:02}.png'
            im.save(args.out / name)
            output.append({'clip': clip, 'frame': frame, 'file': name,
                           'sha256': digest(args.out / name)})
        if not output:
            raise ValueError('motion does not supply the requested direction')
        record = {'base': args.base, 'assets': args.asset, 'direction': args.direction,
                  'motionSHA256': digest(args.motion),
                  'assetManifestSHA256': {k: digest(compositor.asset(k)[1]) for k in [args.base, *args.asset]},
                  'outputs': output}
        (args.out / 'composition.json').write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps({'poses': len(output), 'output': str(args.out)}))
    except (ValueError, OSError, KeyError) as e:
        p.exit(1, str(e) + '\n')


if __name__ == '__main__':
    main()
