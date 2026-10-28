#!/usr/bin/env python3
"""Reuse r4/r5 armor pose maps, with garment-only adaptations of reviewed bow tiles."""
from pathlib import Path
import json,hashlib,importlib.util
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Integration/Equipment-armor-demo-v1';D.mkdir(parents=True,exist_ok=True)
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n')
def asset(n,im):
 d=A/(n+'.imageset');d.mkdir(exist_ok=True);im.save(d/(n+'.png'));dump(d/'Contents.json',{'images':[{'filename':n+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}})
def get(n):return Image.open(A/(n+'.imageset')/(n+'.png')).convert('RGBA')
# Keep the accepted native silhouette, trim, skin and hand registrations. Material
# is authored only inside blue cloth; no skin thresholds erase source alpha.
def cloth_material(im,item,torso=False):
 a=np.asarray(im).copy();r,g,b=[a[:,:,i].astype(float) for i in range(3)];mask=(b>r*1.17)&(b>g*1.13)&(a[:,:,3]>0);shade=np.clip((.30*r+.59*g+.11*b-12)/85,0,1)
 low,high=((44,22,12),(160,99,46)) if item=='leatherArmor' else (((65,75,88),(232,229,211)) if torso else ((7,19,37),(24,70,118)))
 for k in range(3):a[:,:,k][mask]=np.rint(low[k]+shade[mask]*(high[k]-low[k]))
 a[a[:,:,3]==0,:3]=0
 assert np.array_equal(a[:,:,3],np.asarray(im)[:,:,3]);return Image.fromarray(a)
cat=json.loads((R/'Art/Integration/Equipment-b2-batch-v5/catalog.json').read_text());selection=json.loads((R/'Art/Integration/P1-modular-demo-v1/selection.json').read_text());rig=json.loads((R/'Sources/Resources/hero-gait.json').read_text());weapons={'none':None,'trainingSword':'p1-eight-way-weapon-v1','huntingBow':'p1-b2-huntingbow-v1','greatSword':'p1-b2-greatsword-v1','legendaryStaff':'p1-b2-legendarystaff-v1'}
# Pick current manifest IDs, never historical batch versions.
for weapon in ['huntingBow','greatSword','legendaryStaff']:
 p=(R/'Art/Parts/P1-v1/hunting-bow-v1/asset.json') if weapon=='huntingBow' else R/'Art/Parts/P1-v1/b2-equipment-v1'/weapon/'asset.json';v=json.loads(p.read_text());weapons[weapon]=v['id']
 if not any(x['id']==v['id'] for x in cat['assets']):cat['assets'].append({'id':v['id'],'manifest':str(p.relative_to(R))})
dump(D/'catalog.json',cat);sp=importlib.util.spec_from_file_location('compose',R/'scripts/compose-character-parts.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);C=m.Compositor(R,D/'catalog.json',R/'Art/Integration/P1-modular-eight-way-v1/motion.json')
lib=json.loads((R/'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/reviewed-bow-r7.json').read_text());atlas=get('MeadowBattleBowReviewedSleeves');rig['armorVisuals']={};records=[]
for item,rev,prefix in [('leatherArmor','r4','MeadowLeatherArmor'),('runeArmor','r5','MeadowRuneArmor')]:
 folder=R/'Art/Parts/P1-v1'/('b2-armor-'+rev)/item;part=json.loads((folder/'asset.json').read_text());mapping={}
 for p in (folder/'battle').glob('*.png'):
  name=prefix+p.stem.removeprefix('MeadowBattleHero');asset(name,Image.open(p).convert('RGBA'));mapping[p.stem]=name
 icon=prefix+'Icon';asset(icon,Image.open(R/'Art/Parts/P1-v1/b2-equipment-v1'/item/'source'/('item_'+('leather_armor' if item=='leatherArmor' else 'rune_armor')+'.png')).convert('RGBA'))
 bow=atlas.copy();seen=set()
 # Sample chest motifs from the existing fitted cuirass in rest-body UVs.
 # Native bow torso contours/grips remain exact; the material is not a plain
 # palette swap of the old shirt. Canvas-baked states inverse-map their torso.
 core=np.asarray(Image.open(folder/'battle/MeadowBattleHeroWardrobeCore.png').convert('RGBA'))
 _,nearest=distance_transform_edt(core[:,:,3]<128,return_indices=True)
 for frame in lib['frames']:

  for group,index in frame['nativeTiles'].items():
   if group not in ['torso','nearUpperArm','nearSleeveConnected','farArm'] or index in seen:continue
   seen.add(index);t=lib['tiles'][index];box=(t['x'],t['y'],t['x']+t['width'],t['y']+t['height']);src=atlas.crop(box);im=cloth_material(src,item,group=='torso');out=np.asarray(im).copy();pixels=np.asarray(src);red,green,blue=[pixels[:,:,i].astype(float) for i in range(3)];cloth=(blue>red*1.17)&(blue>green*1.13)&(pixels[:,:,3]>0)
   yy,xx=np.mgrid[:t['height'],:t['width']];x=xx+t['canvasX'];y=yy+t['canvasY']
   if group=='torso':
    pose=frame['parts']['torso'];angle=pose['rotation'] if frame.get('canvasBaked') else 0;dx=pose['offset']['x'] if frame.get('canvasBaked') else 0;dy=pose['offset']['y'] if frame.get('canvasBaked') else 0;px,py=pose['pivot']['x'],pose['pivot']['y'];u=x-px-dx;v=y-py-dy
    restX=px+u*np.cos(angle)+v*np.sin(angle);restY=py-u*np.sin(angle)+v*np.cos(angle)
    sx=np.clip(np.rint(110+(restX-111)*35/27),0,255).astype(int);sy=np.clip(np.rint(132+(restY-132)*50/46),0,255).astype(int);texture=core[nearest[0,sy,sx],nearest[1,sy,sx],:3]
    out[:,:,:3][cloth]=texture[cloth]
   elif item=='runeArmor':
    side='far' if group=='farArm' else 'near';hand=lib['tiles'][frame['nativeTiles'][side+'Hand']];hx=hand['canvasX']+hand['width']/2;hy=hand['canvasY']+hand['height']/2
    shoulder=frame['parts'][side+'Upper'];ax=shoulder['pivot']['x']+(shoulder['offset']['x'] if frame.get('canvasBaked') else 0);ay=shoulder['pivot']['y']+(shoulder['offset']['y'] if frame.get('canvasBaked') else 0)
    plate=cloth&((np.hypot(x-hx,y-hy)<12)|(np.hypot(x-ax,y-ay)<8.5));shade=np.clip((.30*red+.59*green+.11*blue-12)/85,0,1)
    for k,(lo,hi) in enumerate([(90,226),(94,227),(105,216)]):out[:,:,k][plate]=np.rint(lo+shade[plate]*(hi-lo))
   bow.paste(Image.fromarray(out),box[:2])
 asset(prefix+'BowLayers',bow)
 # Attack uses the fixed rest torso; state clips use their independently baked
 # native torso tiles. Use the same cuirass UV mapping in both paths.
 src=get('MeadowBattleBowReviewedTorso');ar=np.asarray(src);out=np.asarray(cloth_material(src,item,True)).copy();red,green,blue=[ar[:,:,i].astype(float) for i in range(3)];mask=(blue>red*1.17)&(blue>green*1.13)&(ar[:,:,3]>0);yy,xx=np.mgrid[:256,:256];sx=np.clip(np.rint(110+(xx-111)*35/27),0,255).astype(int);sy=np.clip(np.rint(132+(yy-132)*50/46),0,255).astype(int);tex=core[nearest[0,sy,sx],nearest[1,sy,sx],:3];out[:,:,:3][mask]=tex[mask];asset(prefix+'BowTorso',Image.fromarray(out))
 rig['armorVisuals'][item]={'itemID':item,'iconAsset':icon,'battleLayers':mapping,'bowAtlas':prefix+'BowLayers','bowTorso':prefix+'BowTorso'}
 for preset in selection['loadouts']:
  target=next(p for p in rig['modularP1']['loadouts'] if p['id']==preset['id']);target.setdefault('armorAtlasNames',{})[item]={}
  for weapon,wid in weapons.items():
   selected=[x for x in preset['assets'] if x not in ['p1-eight-way-forester-v1','p1-eight-way-wayfarer-v1','p1-eight-way-weapon-v1']]+[part['id']]+([wid] if wid else [])
   names=[]
   for half,dirs in enumerate([['down','left','up','right'],['down-right','down-left','up-left','up-right']]):
    name='P1'+preset['id'].title()+item.title()+weapon.title()+('Diagonals' if half else 'Directions');names.append(name);sheet=Image.new('RGBA',(3328,1024))
    for row,direction in enumerate(dirs):
     for col,(clip,f) in enumerate([('idle',0)]+[('walk',i) for i in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]):
      im=C.render(selection['base'],selected,direction,clip,f);sheet.paste(im,(col*256,row*256));records.append({'armor':item,'appearance':preset['id'],'weapon':weapon,'direction':direction,'clip':clip,'frame':f,'atlas':name,'row':row,'column':col,'sha256':hashlib.sha256(im.tobytes()).hexdigest()})
    asset(name,sheet)
   target['armorAtlasNames'][item][weapon]=names
 dump(D/(item+'-bow-material.json'),{'sourceAtlas':'MeadowBattleBowReviewedSleeves','silhouetteChanged':False,'handsHeadUnchanged':True,'motionChanged':False,'scope':'Existing cuirass texture mapped inside accepted native bow torso; material-only fitted sleeves variant on accepted independent bow sleeves/torso; not copying generic armor pieces across incompatible arm joints','newArtApproval':None})
dump(R/'Sources/Resources/hero-gait.json',rig);dump(D/'walking-bindings.json',records);dump(D/'binding.json',{'walkingCells':len(records),'appearances':2,'armors':2,'weaponOptions':5,'bodyAndMotionChanged':False,'genericSource':['b2-armor-r4/leatherArmor','b2-armor-r5/runeArmor'],'bowUsesIndependentClothTiles':True,'artApproval':None});print(len(records),'native armor walking bindings exported',flush=True)
