#!/usr/bin/env python3
"""Register an existing rigid weapon once; share it across left pose bindings."""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[4]


def export():
    cfg = json.loads((FOLDER/'authoring.json').read_text())
    image = Image.open(FOLDER/cfg['source']).convert('RGBA')
    assert list(image.size) == cfg['sourceCanvas']
    image.putalpha(image.getchannel('A').point(lambda alpha: 255 if alpha >= 250 else alpha))
    a,b,c,d,tx,ty = cfg['sourceToCanvas']
    linear = np.array([[a,c],[b,d]])
    inverse = np.linalg.inv(linear)
    offset = -inverse@np.array([tx,ty])
    image = image.transform((256,256),Image.Transform.AFFINE,
                            (*inverse[0],offset[0],*inverse[1],offset[1]),Image.Resampling.NEAREST)
    for point in cfg['discardPixels']:
        assert image.getpixel(tuple(point))[3] <= 8, 'cannot discard visible weapon art'
        image.putpixel(tuple(point),(0,0,0,0))
    image.save(FOLDER/'png/weapon.back.png')
    spec = importlib.util.spec_from_file_location('editable',ROOT/'scripts/export-wardrobe-part.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.editable(FOLDER/'editable','back-scabbard',{'weapon.back':image})
    motion = json.loads((ROOT/'Art/Templates/P1-Neutral/left/walk-r3-complete-transitions/motion.json').read_text())
    manifest = {key:cfg[key] for key in ['id','version','compatibility']}
    manifest.update(schemaVersion='1.0.0',part='weapon',mode='pose-map',directions=['left'],
                    clips=['idle','walk','walk-start','walk-stop'],slots=['weapon.back'],
                    carryProfile='back-scabbard',bindings=[
                        {'direction':'left','clip':frame['clip'],'frame':frame['frame'],
                         'layers':{'weapon.back':'png/weapon.back.png'}} for frame in motion['frames']])
    manifest['sourceFiles'] = ['authoring.json','export.py']+[
        str(path.relative_to(FOLDER)) for directory in ['source','editable']
        for path in sorted((FOLDER/directory).rglob('*')) if path.is_file()]
    (FOLDER/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'id':cfg['id'],'poseBindings':len(manifest['bindings']),'uniqueWeaponImages':1}))


if __name__ == '__main__':
    export()
