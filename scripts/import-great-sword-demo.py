#!/usr/bin/env python3
"""Register the reviewed heavy sword and its existing modular carrying layers."""
from pathlib import Path
from PIL import Image
import json,hashlib,importlib.util
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Integration/Equipment-great-sword-v1';D.mkdir(parents=True,exist_ok=True)
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,separators=(',',':'),ensure_ascii=False)+'\n')
def asset(n,im):
 d=A/(n+'.imageset');d.mkdir(exist_ok=True);im.save(d/(n+'.png'));dump(d/'Contents.json',{'images':[{'filename':n+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}})
source=R/'Art/Parts/P1-v1/b2-equipment-v1/greatSword'
asset('MeadowPartyGreatSword',Image.open(source/'source/item_great_sword.png').convert('RGBA'));asset('MeadowBattleGreatSword',Image.open(source/'battle-weapon.png').convert('RGBA'))
# Reuse exactly the reviewed PCHIP/Hermite motion, including airborne leg cycles.
p=R/'scripts/review-b2-weapons-actions.py';spec=importlib.util.spec_from_file_location('great_sword_review',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
resource=R/'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/great-sword-v1.json'
states=json.loads((A/'MeadowBattleHeroAnimationV2.dataset/animation.json').read_text())['clips']
state_keys={c:json.loads(json.dumps(v['keys'])) for c,v in states.items() if c!='attack'}
for clip,desired in [('guard',.14),('hit',.18),('victory',.12)]:
 for key in state_keys[clip]:
  if key['t']==0 or clip in ['guard','hit'] and key['t']==1:continue
  key['wrist']=desired-key['lean']-key['shoulder']-key['elbow']
dump(resource,{'schemaVersion':1,'keys':m.motion_keys['greatSword'],'clips':state_keys,'approvedSource':'Art/Scenes/MeadowBattle/b2-weapon-actions-v1/action-poses.json','sourceImpactAt':1.0275,'sourceMotionStartsAt':.12,'sourceMotionDuration':1.65})
S=R/'Art/Integration/P1-modular-eight-way-v1';catalog=json.loads((S/'catalog.json').read_text());part=json.loads((source/'asset.json').read_text());catalog['assets']=[x for x in catalog['assets'] if x['id']!=part['id']]+[{'id':part['id'],'manifest':str((source/'asset.json').relative_to(R))}];dump(D/'catalog.json',catalog)
p=R/'scripts/compose-character-parts.py';spec=importlib.util.spec_from_file_location('great_sword_compositor',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);C=mod.Compositor(R,D/'catalog.json',S/'motion.json')
selection=json.loads((R/'Art/Integration/P1-modular-demo-v1/selection.json').read_text());gait=R/'Sources/Resources/hero-gait.json';rig=json.loads(gait.read_text());records=[]
dirs=['down','left','up','right','down-right','down-left','up-left','up-right'];keys=[('idle',0)]+[('walk',i) for i in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]
for preset in selection['loadouts']:
 names=['P1'+preset['id'].title()+'GreatSwordDirections','P1'+preset['id'].title()+'GreatSwordDiagonals']
 selected=[x for x in preset['assets'] if x!='p1-eight-way-weapon-v1']+[part['id']]
 for group,name in enumerate(names):
  atlas=Image.new('RGBA',(13*256,4*256))
  for row,d in enumerate(dirs[group*4:group*4+4]):
   for col,(clip,n) in enumerate(keys):
    im=C.render(selection['base'],selected,d,clip,n);atlas.paste(im,(col*256,row*256));records.append({'appearance':preset['id'],'direction':d,'clip':clip,'frame':n,'atlas':name,'row':row,'column':col,'RGBA_SHA256':hashlib.sha256(im.tobytes()).hexdigest()})
  asset(name,atlas)
 for p in rig['modularP1']['loadouts']:
  if p['id']==preset['id']:p['weaponAtlasNames']['greatSword']=names
rig['equipmentVisuals']['greatSword']={'itemID':'greatSword','walkingAsset':part['id'],'battleAsset':'MeadowBattleGreatSword','iconAsset':'MeadowPartyGreatSword'}
dump(gait,rig);dump(D/'walking-bindings.json',records);dump(D/'binding.json',{'itemID':'greatSword','appearances':2,'walkingCells':len(records),'existingLayerSource':str(source.relative_to(R)),'sourceApproval':'Art/Review/Battle/b2-weapons-v1/user-approval.json','newRuntimeArtApproval':None,'motionResourceSHA256':hashlib.sha256(resource.read_bytes()).hexdigest(),'allWholeBodyRuntimeFrames':False})
print('Registered greatSword,241 reviewed joint samples and208 modular walking cells.')
