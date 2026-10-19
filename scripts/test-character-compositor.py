#!/usr/bin/env python3
"""Integration tests for independent assets, attachment spaces and rejection."""
import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compositor', Path(__file__).with_name('compose-character-parts.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BASE = ROOT / 'Art/Templates/P1-Neutral/down/walk-r1'
TEMPLATE = ROOT / 'Art/Templates/P1-Modular/down/v1'


class CompositorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.motion = json.loads((TEMPLATE / 'motion.json').read_text())
        self.motion.pop('baseManifestSHA256', None)
        self.catalog = {'assets': []}
        base = json.loads((BASE / 'asset.json').read_text())
        base['id'] = 'fixture-body'
        folder = self.root / base['id']
        shutil.copytree(BASE / 'layers', folder / 'layers')
        self.register(base)
        self.make('fixture-hair', 'hair', 'head-local', 'hair.front', (96, 96), (38, 49), (90, 40, 20, 255))
        self.make('fixture-face', 'face', 'head-local', 'face.eyes', (96, 96), (38, 56), (20, 90, 200, 255))

    def register(self, asset):
        folder = self.root / asset['id']
        folder.mkdir(exist_ok=True)
        (folder / 'source.txt').write_text('synthetic test fixture, not delivered character art\n')
        asset['sourceFiles'] = ['source.txt']
        (folder / 'asset.json').write_text(json.dumps(asset))
        self.catalog['assets'].append({'id': asset['id'], 'manifest': asset['id'] + '/asset.json'})

    def make(self, identifier, part, mode, slot, size, point, color):
        folder = self.root / identifier
        folder.mkdir(exist_ok=True)
        image = Image.new('RGBA', size)
        image.putpixel(point, color)
        image.save(folder / 'part.png')
        asset = {'schemaVersion': '1.0.0', 'id': identifier, 'version': '1.0.0', 'part': part,
                 'compatibility': self.motion['compatibility'], 'mode': mode, 'slots': [slot],
                 'directions': ['down'], 'clips': ['idle', 'walk'],
                 'bindings': [{'direction': 'down', 'clip': clip, 'frame': frame, 'layers': {slot: 'part.png'}}
                              for clip, frames in [('idle', [0]), ('walk', range(1, 9))] for frame in frames]}
        if mode == 'socket':
            asset.update(canvas=list(size), pivot=list(point), socket=slot.replace('weapon.', 'grip.'),
                         gripProfile='one-hand-closed')
        self.register(asset)

    def engine(self):
        (self.root / 'catalog.json').write_text(json.dumps(self.catalog))
        (self.root / 'motion.json').write_text(json.dumps(self.motion))
        return module.Compositor(self.root, self.root / 'catalog.json', self.root / 'motion.json')

    def render(self, engine, selected, frame=1):
        return engine.render('fixture-body', selected, 'down', 'walk', frame)

    def test_base_only_reproduces_approved_nine_poses(self):
        engine = self.engine()
        for n in range(9):
            result = engine.render('fixture-body', [], 'down', 'idle' if n == 0 else 'walk', n)
            self.assertTrue(np.array_equal(result, Image.open(BASE / 'frames' / f'{n:02}.png')))

    def test_identifier_rename_does_not_change_rendering(self):
        self.make('unrelated-name-734', 'hair', 'head-local', 'hair.front', (96, 96), (38, 49), (90, 40, 20, 255))
        engine = self.engine()
        for frame in range(1, 9):
            first = self.render(engine, ['fixture-hair', 'fixture-face'], frame)
            renamed = self.render(engine, ['unrelated-name-734', 'fixture-face'], frame)
            self.assertTrue(np.array_equal(first, renamed))

    def test_body_layers_do_not_depend_on_appearance(self):
        engine = self.engine()
        bare = dict(engine.layers('fixture-body', [], 'down', 'walk', 3))
        dressed = dict(engine.layers('fixture-body', ['fixture-hair', 'fixture-face'], 'down', 'walk', 3))
        for slot, image in bare.items():
            self.assertTrue(np.array_equal(image, dressed[slot]))

    def test_head_uses_motion_anchor_and_preserves_local_size(self):
        layers = dict(self.engine().layers('fixture-body', ['fixture-face'], 'down', 'walk', 4))
        self.assertEqual(layers['face.eyes'].getpixel((114, 115)), (20, 90, 200, 255))
        self.assertEqual(np.count_nonzero(np.array(layers['face.eyes'])[:, :, 3]), 1)

    def test_pose_map_uses_authored_world_coordinates(self):
        self.make('fixture-coat', 'outfit', 'pose-map', 'outfit.torso', (256, 256), (125, 155), (0, 140, 60, 255))
        self.assertEqual(self.render(self.engine(), ['fixture-coat']).getpixel((125, 155)), (0, 140, 60, 255))

    def test_socket_pivot_and_rotation_come_from_motion(self):
        self.make('fixture-blade', 'weapon', 'socket', 'weapon.right', (64, 96), (32, 20), (90, 60, 40, 255))
        path = self.root / 'fixture-blade/part.png'
        im = Image.open(path)
        im.putpixel((34, 20), (200, 30, 20, 255))
        im.save(path)
        self.motion['frames'][1]['sockets']['grip.right']['angleDeg'] = 90
        layers = dict(self.engine().layers('fixture-body', ['fixture-blade'], 'down', 'walk', 1))
        x, y = self.motion['frames'][1]['sockets']['grip.right']['position']
        self.assertEqual(layers['weapon.right'].getpixel((x, y)), (90, 60, 40, 255))
        self.assertEqual(layers['weapon.right'].getpixel((x, y + 2)), (200, 30, 20, 255))

    def test_hand_occludes_weapon_handle_by_data_order(self):
        self.make('fixture-blade', 'weapon', 'socket', 'weapon.right', (64, 96), (32, 20), (255, 0, 0, 255))
        engine = self.engine()
        x, y = self.motion['frames'][1]['sockets']['grip.right']['position']
        hand = Image.open(BASE / 'layers/01/body.hand.right.png')
        self.assertEqual(self.render(engine, ['fixture-blade']).getpixel((x, y)), hand.getpixel((x, y)))

    def test_missing_requested_binding_has_no_fallback(self):
        path = self.root / 'fixture-face/asset.json'
        asset = json.loads(path.read_text())
        asset['clips'] = ['idle']
        asset['bindings'] = asset['bindings'][:1]
        path.write_text(json.dumps(asset))
        with self.assertRaisesRegex(ValueError, 'does not supply'):
            self.render(self.engine(), ['fixture-face'])

    def test_duplicate_slot_ownership_rejected(self):
        self.make('other-face', 'face', 'head-local', 'face.eyes', (96, 96), (38, 56), (100, 80, 0, 255))
        with self.assertRaisesRegex(ValueError, 'multiple assets own'):
            self.render(self.engine(), ['fixture-face', 'other-face'])

    def test_unknown_catalog_identifier_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unknown asset'):
            self.render(self.engine(), ['not-registered'])

    def test_additional_body_rejected(self):
        asset = json.loads((self.root / 'fixture-body/asset.json').read_text())
        asset['id'] = 'other-body'
        shutil.copytree(self.root / 'fixture-body', self.root / 'other-body')
        self.register(asset)
        with self.assertRaisesRegex(ValueError, 'another body'):
            self.render(self.engine(), ['other-body'])

    def test_catalog_cannot_escape_root(self):
        self.catalog['assets'][1]['manifest'] = '../outside/asset.json'
        with self.assertRaisesRegex(ValueError, 'relative'):
            self.engine()

    def test_duplicate_catalog_identifier_rejected(self):
        self.catalog['assets'].append(copy.deepcopy(self.catalog['assets'][1]))
        with self.assertRaisesRegex(ValueError, 'duplicate catalog'):
            self.engine()

    def test_unsupported_direction_not_mirrored(self):
        with self.assertRaisesRegex(ValueError, 'does not supply'):
            self.engine().render('fixture-body', ['fixture-hair'], 'up', 'walk', 1)

    def test_omitted_layer_order_rejected(self):
        self.motion['frames'][1]['drawOrder'].remove('face.eyes')
        with self.assertRaisesRegex(ValueError, 'draw order omits'):
            self.render(self.engine(), ['fixture-face'])

    def test_fractional_alpha_copy_is_pixel_exact(self):
        image = Image.new('RGBA', (96, 96))
        image.putpixel((1, 1), (13, 45, 67, 7))
        placed = module.place(image, [1, 0, 0, 1, 76, 61], (256, 256))
        self.assertEqual(placed.getpixel((77, 62)), (13, 45, 67, 7))

    def test_clipping_rejected_without_auto_fit(self):
        image = Image.new('RGBA', (96, 96))
        image.putpixel((90, 90), (20, 20, 20, 255))
        with self.assertRaisesRegex(ValueError, 'crosses'):
            module.place(image, [1, 0, 0, 1, 200, 200], (256, 256))

    def test_singular_matrix_rejected(self):
        with self.assertRaisesRegex(ValueError, 'singular'):
            module.place(Image.new('RGBA', (96, 96)), [1, 0, 0, 0, 0, 0], (256, 256))

    def test_unapproved_production_motion_rejected(self):
        self.engine()
        with self.assertRaisesRegex(ValueError, 'locked motion'):
            module.Compositor(self.root, self.root / 'catalog.json', self.root / 'motion.json', True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
