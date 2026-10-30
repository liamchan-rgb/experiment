#!/usr/bin/env python3
"""Synthetic format/region probes. These are not character art approvals."""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import jsonschema
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
STANDARD=ROOT/'Art/Standards/P1-Parts-v1'
spec=importlib.util.spec_from_file_location('part_checker',ROOT/'scripts/check-character-part.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.folder=Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def package(self,part):
        a=json.loads((STANDARD/'examples'/part/'asset.json').read_text())
        a['sourceFiles']=['source/probe.svg']
        source=self.folder/'source/probe.svg'
        source.parent.mkdir(parents=True,exist_ok=True)
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><title>Coordinate probe, not character art</title></svg>')
        for b in a['bindings']:
            for slot,value in b['layers'].items():
                size=a.get('canvas',[256,256] if a['mode']=='pose-map' else [96,96])
                im=Image.new('RGBA',size)
                d=ImageDraw.Draw(im)
                if slot=='hair.front':d.rectangle((24,16,72,43),fill='#aaaaaa')
                elif slot=='face.eyes':
                    d.rectangle((36,55,40,59),fill='#244cc0');d.rectangle((56,55,60,59),fill='#244cc0')
                elif slot=='face.brows':d.line((34,48,42,48),fill='#4e3020')
                elif slot=='face.nose':d.point((48,60),fill='#4e3020')
                elif slot=='face.mouth':d.line((45,66,51,66),fill='#4e3020')
                elif slot.startswith('outfit.'):d.rectangle((112,140,140,170),fill='#447755')
                elif slot.startswith('weapon.'):d.rectangle((30,10,34,60),fill='#888899')
                p=self.folder/value;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
        return a

    def back_weapon_package(self):
        a=self.package('weapon')
        a['mode']='pose-map'
        a['slots']=['weapon.back']
        for key in ('canvas','pivot','socket','gripProfile'):
            a.pop(key,None)
        a['carryProfile']='back-scabbard'
        im=Image.new('RGBA',(256,256))
        ImageDraw.Draw(im).polygon([(96,90),(101,86),(148,170),(141,176)],fill='#8a5538')
        ImageDraw.Draw(im).rectangle((93,85,102,91),fill='#aa8844')
        (self.folder/'png').mkdir(exist_ok=True)
        im.save(self.folder/'png/back.png')
        for binding in a['bindings']:
            binding['layers']={'weapon.back':'png/back.png'}
        return a

    def check(self,a,**kwargs):
        path=self.folder/'asset.json';path.write_text(json.dumps(a))
        return checker.check_asset(path,**kwargs)

    def assert_reject(self,a,message):
        errors=self.check(a)
        self.assertTrue(any(message in e for e in errors),errors)

    def test_schema_and_four_examples(self):
        schema=json.loads((STANDARD/'asset.schema.json').read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        for part in ['hair','face','outfit','weapon']:
            with self.subTest(part=part):
                path=STANDARD/'examples'/part/'asset.json'
                self.assertEqual(checker.check_asset(path,schema_only=True),[])
                self.assertTrue(checker.check_asset(path)) # PNGs are not delivered.

    def test_valid_coordinate_probes_for_each_part(self):
        for part in ['hair','face','outfit','weapon']:
            with self.subTest(part=part):self.assertEqual(self.check(self.package(part)),[])

    def test_back_scabbard_is_a_valid_pose_map_without_grip_contract(self):
        a=self.back_weapon_package()
        self.assertNotIn('gripProfile',a)
        self.assertNotIn('socket',a)
        self.assertEqual(self.check(a),[])

    def test_back_slot_requires_back_scabbard_profile(self):
        a=self.back_weapon_package();a.pop('carryProfile')
        self.assert_reject(a,'carryProfile')

    def test_back_and_hand_slots_cannot_share_a_hand_grip_profile(self):
        a=self.back_weapon_package();a.pop('carryProfile')
        a['gripProfile']='one-hand-closed'
        a['slots'].append('weapon.right')
        for binding in a['bindings']:
            binding['layers']['weapon.right']='png/back.png'
        self.assert_reject(a,'carryProfile')

    def test_back_scabbard_rejects_grip_or_wrong_weapon_slot(self):
        a=self.back_weapon_package();a['gripProfile']='one-hand-closed'
        self.assertTrue(self.check(a))
        a=self.back_weapon_package();a['slots']=['weapon.right']
        for b in a['bindings']:b['layers']={'weapon.right':'png/back.png'}
        self.assertTrue(any('does not contain' in e for e in self.check(a)))

    def test_face_dependency_rejected(self):
        a=self.package('hair');a['compatibility']['requiresFace']='amber'
        self.assert_reject(a,'Additional properties')

    def test_asset_id_does_not_change_validation(self):
        a=self.package('hair');a['id']='never-seen-third-hairstyle'
        self.assertEqual(self.check(a),[])

    def test_no_auto_resize_of_old_silver_hair_canvas(self):
        a=self.package('hair');Image.new('RGBA',(70,55)).save(self.folder/'png/down-front.png')
        self.assert_reject(a,'no auto-fit')

    def test_front_hair_cannot_move_or_cover_eye_windows(self):
        a=self.package('hair');path=self.folder/'png/down-front.png'
        im=Image.open(path);im.putpixel((38,56),(150,150,150,255));im.save(path)
        self.assert_reject(a,'protected eye window')

    def test_whole_face_skin_patch_rejected(self):
        a=self.package('face');im=Image.new('RGBA',(96,96));ImageDraw.Draw(im).rectangle((24,32,72,73),fill='#ffc090');im.save(self.folder/'png/down-eyes.png')
        self.assert_reject(a,'outside standard feature regions')

    def test_hair_cannot_own_head_base(self):
        a=self.package('hair');a['slots'].append('head.base')
        for b in a['bindings']:b['layers']['head.base']='png/down-back.png'
        self.assert_reject(a,'slot ownership')

    def test_missing_frame_rejected(self):
        a=self.package('hair');a['bindings'].pop(4)
        self.assert_reject(a,'coverage mismatch')

    def test_duplicate_frame_rejected(self):
        a=self.package('hair');a['bindings'].append(copy.deepcopy(a['bindings'][0]))
        self.assert_reject(a,'duplicate binding')

    def transition_package(self):
        a=self.package('outfit')
        original=copy.deepcopy(a['bindings'][0])
        for clip in ['walk-start','walk-stop']:
            a['clips'].append(clip)
            for frame in [1,2]:
                b=copy.deepcopy(original)
                b.update(clip=clip,frame=frame)
                a['bindings'].append(b)
        return a

    def test_optional_start_stop_clips_are_complete_independent_pose_maps(self):
        self.assertEqual(self.check(self.transition_package()),[])

    def test_transition_clip_cannot_fall_back_to_walk_or_idle(self):
        a=self.transition_package()
        a['bindings']=[b for b in a['bindings'] if not (b['clip']=='walk-stop' and b['frame']==2)]
        self.assert_reject(a,'coverage mismatch')

    def test_transition_clip_rejects_undeclared_and_wrong_frame_coverage(self):
        a=self.transition_package()
        a['clips'].remove('walk-start')
        self.assert_reject(a,'coverage mismatch')
        a=self.transition_package()
        next(b for b in a['bindings'] if b['clip']=='walk-start' and b['frame']==1)['frame']=0
        self.assert_reject(a,'coverage mismatch')

    def test_undeclared_view_rejected(self):
        a=self.package('hair');a['bindings'][0]['direction']='up'
        self.assert_reject(a,'coverage mismatch')

    def test_foreign_part_in_frame_rejected(self):
        a=self.package('hair');a['bindings'][0]['layers']['face.eyes']='png/down-front.png'
        self.assert_reject(a,'layers differ')

    def test_path_escape_rejected(self):
        a=self.package('hair');a['bindings'][0]['layers']['hair.front']='../external.png'
        self.assert_reject(a,'must be relative')

    def test_opaque_rgb_export_rejected(self):
        a=self.package('hair');Image.new('RGB',(96,96)).save(self.folder/'png/down-front.png')
        self.assert_reject(a,'RGBA PNG')

    def test_handle_must_contain_pivot(self):
        a=self.package('weapon');path=self.folder/'png/down.png';im=Image.open(path);im.putpixel((32,20),(0,0,0,0));im.save(path)
        self.assert_reject(a,'outside solid handle')

    def test_wrong_anatomical_hand_rejected(self):
        a=self.package('weapon');a['socket']='grip.left'
        self.assert_reject(a,'anatomical grip socket')

    def test_socket_clipping_rejected(self):
        a=self.package('weapon');a['canvas']=[256,256]
        im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im);d.rectangle((30,10,34,60),fill='#888899');d.point((250,250),fill='#888899');im.save(self.folder/'png/down.png')
        self.assert_reject(a,'cell safety margin')

    def test_unlocked_partial_rig_not_production_ready(self):
        errors=self.check(self.package('hair'),production=True)
        self.assertTrue(any('not locked' in e for e in errors))
        self.assertTrue(any('eight directions' in e for e in errors))

    def test_original_approved_motion_hashes_unchanged(self):
        lock=json.loads((ROOT/'Art/Templates/P1-Motion-v1.json').read_text())
        self.assertEqual(len(lock['directions']),8)
        for direction in lock['directions'].values():
            for f in direction['frames']:
                self.assertEqual(hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest(),f['sha256'])


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'scope':'synthetic declaration/geometry/file probes; no character art approval',
            'artApproval':None,
            'notAssessedHere':['anatomy or clothing visual approval',
                               'separate third-resource integration evidence',
                               'complete production template or App runtime']}
    (STANDARD/'contract-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
