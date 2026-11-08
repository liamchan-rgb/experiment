#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,subprocess
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'Art/Integration/Equipment-armor-demo-v1';A=R/'Sources/Resources/Assets.xcassets';BASE='d0e94d0226f85e9ffd8caf251a66fe2f019f4401'
def original(path):return subprocess.check_output(['git','-C','/workspace/left-transitions-publish.git','show',BASE+':'+path])
old=json.loads(original('Sources/Resources/hero-gait.json'));new=json.loads((R/'Sources/Resources/hero-gait.json').read_text());oldOnly=json.loads(json.dumps(new));oldOnly.pop('armorVisuals')
for loadout in oldOnly['modularP1']['loadouts']:loadout.pop('armorAtlasNames')
assert oldOnly==old,'Existing gait/carry bindings changed'
unchanged=['Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/BowRig.swift','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/GreatSwordRig.swift','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/LegendaryStaffRig.swift']+['Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/'+x for x in ['reviewed-bow-r7.json','great-sword-v1.json','legendary-staff-v1.json']]+['Vendor/ClassroomGameCore/Sources/ClassroomGameCore/'+x for x in ['GameEngine.swift','Rules.swift','Resources/initial-content.json']]
for p in unchanged:assert (R/p).read_bytes()==original(p),p
bindings=json.loads((D/'walking-bindings.json').read_text());atlases={};assert len(bindings)==2080
for b in bindings:
 name=b['atlas'];p=A/(name+'.imageset')/(name+'.png')
 if name not in atlases:atlases[name]=Image.open(p).convert('RGBA');assert atlases[name].size==(3328,1024)
 c,r=b['column'],b['row'];im=atlases[name].crop((c*256,r*256,c*256+256,r*256+256));assert hashlib.sha256(im.tobytes()).hexdigest()==b['sha256']
source=np.asarray(Image.open(A/'MeadowBattleBowReviewedSleeves.imageset/MeadowBattleBowReviewedSleeves.png').convert('RGBA'));lib=json.loads((R/unchanged[3]).read_text());allowed=np.zeros(source.shape[:2],bool)
for f in lib['frames']:
 for group,index in f['nativeTiles'].items():
  if group not in ['torso','nearUpperArm','nearSleeveConnected','farArm']:continue
  t=lib['tiles'][index];allowed[t['y']:t['y']+t['height'],t['x']:t['x']+t['width']]=True
for armor,v in new['armorVisuals'].items():
 out=np.asarray(Image.open(A/(v['bowAtlas']+'.imageset')/(v['bowAtlas']+'.png')).convert('RGBA'));assert np.array_equal(source[:,:,3],out[:,:,3]);assert np.array_equal(source[~allowed],out[~allowed])
 for n in v['battleLayers'].values():assert (A/(n+'.imageset')/(n+'.png')).is_file()
record={'walkingBindingsVerified':2080,'compiledAtlasInputs':len(atlases),'originalGaitBindingsUnchanged':True,'originalWeaponRigAndJSONAndRulesUnchanged':unchanged,'bowAlphaAndAllNonGarmentTilesUnchanged':True,'newArtApproval':None,'notDeviceValidation':True};(D/'audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
