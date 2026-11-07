#!/usr/bin/env python3
"""Register the existing short sword and bake empty weapon slots, without repainting."""
from pathlib import Path
import importlib.util,json,hashlib,urllib.request
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'Art/Integration/Equipment-training-sword-v1';D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=R/'scripts/compose-character-parts.py';spec=importlib.util.spec_from_file_location('gear_compositor',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
S=R/'Art/Integration/P1-modular-eight-way-v1';C=m.Compositor(R,S/'catalog.json',S/'motion.json');config=json.loads((R/'Art/Integration/P1-modular-demo-v1/selection.json').read_text());assetdir=R/'Sources/Resources/Assets.xcassets'
directions=['down','left','up','right','down-right','down-left','up-left','up-right'];keys=[('idle',0)]+[('walk',i) for i in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)];records=[];mapping={}
for preset in config['loadouts']:
 names=['P1'+preset['id'].title()+'UnarmedDirections','P1'+preset['id'].title()+'UnarmedDiagonals'];mapping[preset['id']]=names
 for group,name in enumerate(names):
  atlas=Image.new('RGBA',(13*256,4*256));old=Image.open(assetdir/(preset['atlasNames'][group]+'.imageset')/(preset['atlasNames'][group]+'.png')).convert('RGBA')
  for row,direction in enumerate(directions[group*4:group*4+4]):
   for col,(clip,n) in enumerate(keys):
    armed=C.render(config['base'],preset['assets'],direction,clip,n);existing=old.crop((col*256,row*256,(col+1)*256,(row+1)*256));assert armed.tobytes()==existing.tobytes()
    empty=C.render(config['base'],[a for a in preset['assets'] if a!='p1-eight-way-weapon-v1'],direction,clip,n);atlas.paste(empty,(col*256,row*256))
    assert armed.tobytes()!=empty.tobytes(),(direction,clip,n)
    records.append({'appearance':preset['id'],'direction':direction,'clip':clip,'frame':n,'equippedItem':'trainingSword','walkingAsset':'p1-eight-way-weapon-v1','emptyAtlas':name,'row':row,'column':col,'equippedRGBA_SHA256':hashlib.sha256(armed.tobytes()).hexdigest(),'emptyRGBA_SHA256':hashlib.sha256(empty.tobytes()).hexdigest()})
  folder=assetdir/(name+'.imageset');folder.mkdir(exist_ok=True);atlas.save(folder/(name+'.png'));write(folder/'Contents.json',{'images':[{'filename':name+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}})
rigfile=R/'Sources/Resources/hero-gait.json';rig=json.loads(rigfile.read_text())
for p in rig['modularP1']['loadouts']:p['weaponAtlasNames']={'trainingSword':p['atlasNames'],'none':mapping[p['id']]}
rig['equipmentVisuals']={'trainingSword':{'itemID':'trainingSword','walkingAsset':'p1-eight-way-weapon-v1','battleAsset':'MeadowBattleHeroWeapon','iconAsset':'MeadowPartyTrainingSword'}}
rigfile.write_text(json.dumps(rig,separators=(',',':'))+'\n')
icon=assetdir/'MeadowPartyTrainingSword.imageset';icon.mkdir(exist_ok=True);target=icon/'MeadowPartyTrainingSword.png'
url='https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/1e9100c4c18364ea64b3ec974fe957ba4ef42f6f/native/ClassroomProbe/Resources/Art/item_training_sword.png'
if not target.exists():
 with urllib.request.urlopen(url,timeout=40) as res:target.write_bytes(res.read())
assert sha(target)=='0a9adb9c988f637e8cfe0ccf398ba569b007703d4c904f6bfe1aad0b1c01d75a'
write(icon/'Contents.json',{'images':[{'filename':target.name,'idiom':'universal'}],'info':{'author':'xcode','version':1}})
write(D/'walking-bindings.json',records)
write(D/'binding.json',{'schemaVersion':1,'itemID':'trainingSword','sourceArtwork':'reused existing candidate; no new drawing or automatic art approval','walking':{'asset':'p1-eight-way-weapon-v1','manifest':'Art/Parts/P1-v1/eight-way-v1/weapon/asset.json','bindingCountPerAppearance':104,'appearances':2,'all208EquippedCellsUnchanged':True,'emptySlotCellsNew':208,'motionSHA256':sha(S/'motion.json'),'baseSHA256':sha(R/'Art/Parts/P1-v1/eight-way-v1/base/asset.json')},'battle':{'asset':'MeadowBattleHeroWeapon','configuration':'MeadowBattleHeroConfigurationV2','animation':'MeadowBattleHeroAnimationV2','gripPx':[145.6,163.7],'clips':['idle','attack','guard','hit','victory','defeat'],'emptySlotOmitsSameLayerFromActorAndSilhouette':True},'icon':{'sourceURL':url,'sha256':sha(target)},'runtimeBinding':'Sources/Resources/hero-gait.json equipmentVisuals / modularP1.loadouts.weaponAtlasNames','newArtApproval':None})
print('Verified208 existing armed cells unchanged; baked208 empty-slot cells; registered trainingSword with104 walking bindings and6battle clips')
