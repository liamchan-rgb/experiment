#!/usr/bin/env python3
"""Registered battle armor repair; leaves approved hands, bones and walk atlases intact."""
from pathlib import Path
import importlib.util,copy,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageChops
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Parts/P1-Battle/armor-fit-r1';D.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('surface',R/'scripts/armor-shared-surface-r4.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b=m.ArmorSurface(R);f=copy.deepcopy(b.rests['right']);f['joints'].update(neck=[128,132],shoulderRight=[117,141],elbowRight=[128,158],wristRight=[145.6,163.7],shoulderLeft=[122,143],elbowLeft=[116,155],wristLeft=[108,161],hipRight=[134,175],hipLeft=[115,176]);b.rests['right']=f;b.marker_cache[('right','idle',0)]=f['joints'];b.waist['right']=174;b.body_width['right']=(110,141)
def get(n):return Image.open(A/(n+'.imageset')/(n+'.png')).convert('RGBA')
def save(item,slot,im):
 name=('MeadowLeatherArmor' if item=='leatherArmor' else 'MeadowRuneArmor')+slot.removeprefix('MeadowBattleHero');p=D/item;p.mkdir(exist_ok=True);a=np.asarray(im).copy();a[a[:,:,3]==0]=0;im=Image.fromarray(a);im.save(p/(slot+'.png'));target=A/(name+'.imageset');target.mkdir(exist_ok=True);im.save(target/(name+'.png'));(target/'Contents.json').write_text(json.dumps({'images':[{'filename':name+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},separators=(',',':'))+'\n');return name
# Two anatomical skin parts are complete through the elbow. Their pivots and
# the separate original hand are unchanged; sleeve masking never edits skin.
def skin(start,end,r0,r1):
 out=Image.new('RGBA',(256,256));a=np.array(start,float);z=np.array(end,float);v=z-a;length=np.linalg.norm(v);axis=v/length;n=np.array([-axis[1],axis[0]]);yy,xx=np.mgrid[:256,:256];p=np.stack([xx,yy],-1)-a;u=p@axis;q=p@n;t=np.clip(u/length,0,1);radius=r0+(r1-r0)*t;dist=np.sqrt(q*q+np.maximum(-u,0)**2+np.maximum(u-length,0)**2);mask=dist<=radius;edge=dist>radius-1.1;colors=np.zeros((256,256,4),dtype=np.uint8);colors[mask]=(251,184,137,255);colors[mask&(q>radius*.30)]=(222,142,96,255);colors[mask&(q<-radius*.20)]=(255,199,153,255);colors[mask&edge]=(92,49,29,255);return Image.fromarray(colors)
S=np.array([117.,141.]);E=np.array([128.,158.]);W=np.array([145.6,163.7]);axis=(W-E)/np.linalg.norm(W-E);n=np.array([-axis[1],axis[0]]);yy,xx=np.mgrid[:256,:256];p=np.stack([xx,yy],-1);upperaxis=(E-S)/np.linalg.norm(E-S);bisector=upperaxis+axis;bisector/=np.linalg.norm(bisector);cut=(p-E)@bisector
rig=json.loads((R/'Sources/Resources/hero-gait.json').read_text())
for item in ['leatherArmor','runeArmor']:
 layers=b.fit(item,'right');new={};core=layers['outfit.sleeve.left'].copy();core.alpha_composite(layers['outfit.torso']);hem=layers['outfit.hem.front'];top=hem.copy();ImageDraw.Draw(top).rectangle((0,182,255,255),fill=0);core.alpha_composite(top);new['MeadowBattleHeroWardrobeCore']=core
 # Neither thigh carries garment pixels. The long panels are independent,
 # overlap the belt underside and render over the finished trouser silhouette.
 for side in ['Far','Near']:
  pants=get('MeadowBattleHeroLeg'+side+'ThighWardrobe');ImageDraw.Draw(pants).rectangle((0,0,255,173),fill=0);new['MeadowBattleHeroLeg'+side+'ThighWardrobe']=pants
  panel=hem.copy();dr=ImageDraw.Draw(panel);dr.rectangle((0,0,255,178),fill=0);dr.rectangle((128,0,255,255) if side=='Far' else (0,0,126,255),fill=0);new['MeadowBattleHeroHem'+side+'Wardrobe']=panel
 new['MeadowBattleHeroArmNearUpperBody']=skin(S,E,4.6,4.7);new['MeadowBattleHeroArmNearForearmBody']=skin(E,[143.5,163.1],4.7,3.5)
 sleeve=np.asarray(layers['outfit.sleeve.right']).copy();along=(p-S)@upperaxis;cap=sleeve.copy();cap[along>7]=0;new['MeadowBattleHeroPauldronNearWardrobe']=Image.fromarray(cap);sleeve[along<4]=0;sleeve[cut>2.5]=0
 new['MeadowBattleHeroArmNearUpperWardrobe']=Image.fromarray(sleeve)
 forearm=Image.new('RGBA',(256,256))
 if item=='runeArmor':
  # Tailor a narrow, closed bracer to the existing elbow/wrist axis. Material
  # samples come from the fitted source; a gold rim separates cuff from hand.
  src=np.asarray(layers['outfit.sleeve.right']);u=(p-E)@axis;q=(p-E)@n;length=14.3;t=np.clip(u/length,0,1);width=5.2-1.5*t;mask=(u>=-2.5)&(u<=length)&(abs(q)<=width);out=np.zeros_like(src)
  # Preserve the source blue sleeve fold character rather than a square cut.
  out[mask]=(16,43,73,255);out[mask&(q<-1)]=(24,68,107,255);out[mask&(q>2)]=(9,23,43,255)
  plate=mask&(u>=7)&(abs(q)<width-.7);out[plate]=(186,192,187,255);out[plate&(q<-1)]=(236,233,211,255);out[plate&(q>1.5)]=(109,124,139,255)
  edge=mask&((abs(q)>width-1)|(u>length-1));out[edge]=(88,57,25,255);rim=mask&(((u>6)&(u<7.6))|((u>length-2.2)&(u<length-1.0)));out[rim]=(222,166,52,255);out[rim&(q<-1)]=(255,224,111,255);forearm=Image.fromarray(out)
 new['MeadowBattleHeroArmNearForearmWardrobe']=forearm
 mapping=rig['armorVisuals'][item]['battleLayers']
 order=json.loads((R/'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/legendary-staff-v1.json').read_text())['layerOrder']
 front=['MeadowBattleHeroWardrobeCore','MeadowBattleHeroHemFarWardrobe','MeadowBattleHeroHemNearWardrobe','MeadowBattleHeroArmNearUpperBody','MeadowBattleHeroArmNearUpperWardrobe','MeadowBattleHeroPauldronNearWardrobe','MeadowBattleHeroArmNearForearmBody','MeadowBattleHeroArmNearForearmWardrobe']
 order=[n for n in order if n not in front];i=order.index('MeadowBattleHeroWeapon');order[i:i]=front;rig['armorVisuals'][item]['battleLayerOrder']=order
 for slot,im in new.items():mapping[slot]=save(item,slot,im)
(R/'Sources/Resources/hero-gait.json').write_text(json.dumps(rig,ensure_ascii=False,separators=(',',':'))+'\n')
(D/'manifest.json').write_text(json.dumps({'source':'b2-armor-r4/r5 registered battle patterns','handAssetsChanged':False,'boneAndMotionChanged':False,'walkingChanged':False,'repairs':['complete independently articulated near arm skin','fitted rune forearm cuff','clean trousers and separate overlaid hem panels'],'hemPolicy':'upper attachment overlaps torso; bounded leg-follow below belt','userApproval':None},indent=2)+'\n')
print('Two battle armors repaired from registered native layers.')
