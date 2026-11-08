#!/usr/bin/env python3
"""Adapt selected B clothing to the existing battle rigs, without changing poses.
Uses original generic independent parts and the approved native bow tile atlas.
No App execution, new body, hand swap, equipment rule or gameplay edit.
"""
from pathlib import Path
import json,math,copy,sys,subprocess,hashlib,importlib.util,functools,gzip
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageChops
from scipy.ndimage import distance_transform_edt,maximum_filter

R=Path(__file__).resolve().parents[1]
REF=Path('/workspace/battle-avatar-reference')
OUT=R/'Art/Parts/P1-Battle/chat-apparel-b-v1'
D=R/'Art/Review/Battle/chat-apparel-b-v1'
SOURCE='1f76bce38fb33742ff6eeaef1499c186f14c0fb6'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
art=load('selected_b_battle_art',R/'scripts/build-chat-apparel-b-eight-way.py')
def ref(rel):
 p=R/rel
 return p if p.is_file() else REF/rel
def read(rel):
 p=ref(rel)
 if p.is_file():return json.loads(p.read_text())
 with gzip.open(str(p)+'.gz','rt') as f:return json.load(f)
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@functools.lru_cache(None)
def asset(name):return Image.open(ref(f'Sources/Resources/Assets.xcassets/{name}.imageset/{name}.png')).convert('RGBA')
CFG=read('Art/Scenes/MeadowBattle/hero-combat-v2/hero-v2-configuration.json')
CLIPS=read('Art/Scenes/MeadowBattle/hero-combat-v2/clips.json')
GAIT=read('Sources/Resources/hero-gait.json')
LIB=read('Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/reviewed-bow-r7.json')
WEAPONS=['trainingSword','greatSword','huntingBow','legendaryStaff']
GENERIC_ORDER=GAIT['armorVisuals']['runeArmor']['battleLayerOrder']
SKIN={k:v for k,v in GAIT['armorVisuals']['runeArmor']['battleLayers'].items() if k.endswith('Body') or 'ThighWardrobe' in k}
S=np.array([117.,141.]);E=np.array([128.,158.]);W=np.array([145.6,163.7])
YY,XX=np.mgrid[:256,:256];XY=np.stack([XX,YY],-1)


def canonical_assets(item):
 folder=OUT/item;folder.mkdir(parents=True,exist_ok=True)
 joints={'neck':[128,132],'shoulderRight':S.tolist(),'elbowRight':E.tolist(),'wristRight':W.tolist(),
         'shoulderLeft':[122,143],'elbowLeft':[116,155],'wristLeft':[108,161],
         'hipRight':[134,175],'hipLeft':[115,176]}
 c=art.Camera(item,'down-right',joints);c.h=42
 groups={'outfit.torso':c.torso(),'outfit.hem.front':c.hem(),
         'outfit.sleeve.left':art.sleeve(item,'down-right',joints,'left'),
         'outfit.sleeve.right':art.sleeve(item,'down-right',joints,'right')}
 svg=folder/'editable/battle-right.svg';svg.parent.mkdir(exist_ok=True)
 svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256" shape-rendering="crispEdges">'+''.join(f'<g id="{s}">{v}</g>' for s,v in groups.items())+'</svg>\n')
 layers={}
 for slot in groups:
  p=folder/f'masters/{slot}.png';p.parent.mkdir(exist_ok=True)
  subprocess.run(['inkscape',str(svg),'--export-id='+slot,'--export-id-only','--export-area-page','--export-png-antialias=0','--export-filename='+str(p)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  with Image.open(p) as im:art.save(im,p)
  layers[slot]=Image.open(p).convert('RGBA')
 # Fitted cloth allowance under the newly authored breast/arm plates; only
 # alpha of the existing tailored garment is used, never old decoration RGB.
 oldcore=asset('MeadowRuneArmorWardrobeCore')
 coremask=np.asarray(oldcore.getchannel('A')).copy();coremask[179:]=0
 palette=art.front.PALETTES[item]
 def rgb(k):return tuple(int(palette[k][j:j+2],16) for j in [1,3,5])
 core=np.zeros((256,256,4),dtype=np.uint8);core[coremask>8]=(*rgb('clothShadow'),255)
 core[(coremask>8)&(XX<126)]=(*rgb('cloth'),255)
 core=Image.fromarray(core)
 core.alpha_composite(layers['outfit.sleeve.left'])
 core.alpha_composite(layers['outfit.torso'])
 hem=layers['outfit.hem.front'];top=hem.copy();ImageDraw.Draw(top).rectangle((0,180,255,255),fill=0);core.alpha_composite(top)
 near=np.asarray(layers['outfit.sleeve.right']).copy()
 axis=(E-S)/np.linalg.norm(E-S);low=(W-E)/np.linalg.norm(W-E);bis=axis+low;bis/=np.linalg.norm(bis)
 along=(XY-S)@axis;elbow=(XY-E)@bis
 cap=near.copy();cap[along>7]=0
 upper=near.copy();upper[(along<4)|(elbow>3)]=0
 fore=near.copy();fore[elbow< -3]=0
 result={'MeadowBattleHeroWardrobeCore':core,
         'MeadowBattleHeroPauldronNearWardrobe':Image.fromarray(cap),
         'MeadowBattleHeroArmNearUpperWardrobe':Image.fromarray(upper),
         'MeadowBattleHeroArmNearForearmWardrobe':Image.fromarray(fore)}
 for side in ['Far','Near']:
  im=hem.copy();dr=ImageDraw.Draw(im);dr.rectangle((0,0,255,176),fill=0)
  dr.rectangle((128,0,255,255) if side=='Far' else (0,0,126,255),fill=0)
  result['MeadowBattleHeroHem'+side+'Wardrobe']=im
 for slot,im in result.items():art.save(im,folder/'generic'/(slot+'.png'))
 return result


def blue_cloth(pixels):
 r,g,b=[pixels[:,:,i].astype(float) for i in range(3)]
 return (b>r*1.17)&(b>g*1.13)&(pixels[:,:,3]>0)


def bow_material(src,item,group,record=None,tile=None,core=None):
 pixels=np.asarray(src).copy();out=pixels.copy();mask=blue_cloth(pixels)
 pal=art.front.PALETTES[item]
 rgb=lambda k:np.array([int(pal[k][j:j+2],16) for j in [1,3,5]],float)
 shade=np.clip((pixels[:,:,:3]@np.array([.30,.59,.11])-12)/85,0,1)
 lo,hi=rgb('clothShadow'),rgb('clothLight')
 for k in range(3):out[:,:,k][mask]=np.rint(lo[k]+shade[mask]*(hi[k]-lo[k]))
 yy,xx=np.mgrid[:src.height,:src.width]
 x=xx+(tile['canvasX'] if tile else 0);y=yy+(tile['canvasY'] if tile else 0)
 if group=='torso':
  dx=dy=angle=0;px,py=132,167
  if record:
   pose=record['parts']['torso'];px,py=pose['pivot']['x'],pose['pivot']['y']
   if record.get('canvasBaked'):dx,dy,angle=pose['offset']['x'],pose['offset']['y'],pose['rotation']
  u=x-px-dx;v=y-py-dy;rx=px+u*np.cos(angle)+v*np.sin(angle);ry=py-u*np.sin(angle)+v*np.cos(angle)
  # Same rest-body registration on every state, not a moving chest sticker.
  sx=np.clip(np.rint(110+(rx-111)*35/27),0,255).astype(int);sy=np.clip(np.rint(132+(ry-132)*46/46),0,255).astype(int)
  a=np.asarray(core);_,nearest=distance_transform_edt(a[:,:,3]<128,return_indices=True)
  texture=a[nearest[0,sy,sx],nearest[1,sy,sx],:3];out[:,:,:3][mask]=texture[mask]
 elif record and group in ['nearSleeveConnected','nearUpperArm','farArm']:
  side='far' if group=='farArm' else 'near';hand=LIB['tiles'][record['nativeTiles'][side+'Hand']]
  hx=hand['canvasX']+hand['width']/2;hy=hand['canvasY']+hand['height']/2
  sh=record['parts'][side+'Upper'];ax=sh['pivot']['x'];ay=sh['pivot']['y']
  if record.get('canvasBaked'):ax+=sh['offset']['x'];ay+=sh['offset']['y']
  wrist=np.hypot(x-hx,y-hy)<11;shoulder=np.hypot(x-ax,y-ay)<7.5
  metal=mask&(wrist|shoulder)
  a,b=(rgb('metalShadow'),rgb('metalLight')) if item=='starlightArmor' else (rgb('clothShadow'),rgb('gold'))
  for k in range(3):out[:,:,k][metal]=np.rint(a[k]+shade[metal]*(b[k]-a[k]))
  edge=mask&((np.abs(np.hypot(x-hx,y-hy)-9)<1)|(np.abs(np.hypot(x-ax,y-ay)-6)<.8))
  out[:,:,:3][edge]=rgb('metal' if item=='starlightArmor' else 'goldShadow').astype('uint8')
 out[out[:,:,3]==0]=0
 assert np.array_equal(out[:,:,3],pixels[:,:,3])
 assert np.array_equal(out[~mask],pixels[~mask])
 return Image.fromarray(out)


def bow_assets(item,core):
 original=asset('MeadowBattleBowReviewedSleeves');out=original.copy();seen={}
 for f in LIB['frames']:
  for group,index in f['nativeTiles'].items():
   if group not in ['torso','nearUpperArm','nearSleeveConnected','farArm'] or index in seen:continue
   t=LIB['tiles'][index];box=(t['x'],t['y'],t['x']+t['width'],t['y']+t['height'])
   source=original.crop(box);paint=bow_material(source,item,group,f,t,core);out.paste(paint,box[:2]);seen[index]=group
 art.save(out,OUT/item/'bow/atlas.png')
 torso=bow_material(asset('MeadowBattleBowReviewedTorso'),item,'torso',core=core)
 art.save(torso,OUT/item/'bow/torso.png')
 before=np.asarray(original);after=np.asarray(out);allowed=blue_cloth(before)
 assert np.array_equal(before[~allowed],after[~allowed]) and np.array_equal(before[:,:,3],after[:,:,3])
 write(OUT/item/'bow/material-check.json',{'originalAtlasSHA256':sha(ref('Sources/Resources/Assets.xcassets/MeadowBattleBowReviewedSleeves.imageset/MeadowBattleBowReviewedSleeves.png')),'editedClothTiles':len(seen),'allNonClothPixelsAndAlphaByteExact':True,'handsNotRepaintedOrSwapped':True,'nativeMotionChanged':False,'shortFittedBowVariant':True})
 return out,torso


def generic_sample(clip,p):
 # Original runtime JSON sampler; strip only the historical GIF output loop.
 global _generic
 if '_generic' not in globals():
  text=ref('Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py').read_text();text=text[:text.index('\nfor clip,data in lib[')]
  text=text.replace("ROOT=Path(__file__).resolve().parents[4]",'ROOT=R').replace("ART=Path(__file__).resolve().parent", "ART=ref('Art/Scenes/MeadowBattle/hero-combat-v2/hero-v2-configuration.json').parent")
  text=text.replace("LAYERS={n:Image.open(ASSETS/f'{n}.imageset/{n}.png').convert('RGBA') for n in config['layers']}",'LAYERS={n:asset(n) for n in config["layers"]}')
  _generic={'R':R,'REF':REF,'ref':ref,'asset':asset,'__file__':str(ref('Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py'))};exec(compile(text,'original-battle-sampler','exec'),_generic)
 return _generic['sample'](clip,p)


@functools.lru_cache(None)
def pose_tables():
 result={}
 for w,folder,name in [('greatSword','great-sword-demo-v1','great-sword-poses.json'),('legendaryStaff','legendary-staff-demo-v1','legendary-staff-poses.json'),('huntingBow','bow-actions-r7-demo-v1','bow-poses.json')]:
  rows=read(f'Art/Review/Battle/{folder}/{name}')
  result[w]={(x.get('clip','attack'),round(x['progress']*600)):x['sample'] for x in rows}
 return result


def transform(im,t,root):
 pivot,off,angle=t
 im=im.rotate(-math.degrees(angle),Image.Resampling.NEAREST,center=pivot)
 result=Image.new('RGBA',(256,256));result.alpha_composite(im,(round(off[0]+root[0]),round(off[1]+root[1])))
 return result


@functools.lru_cache(None)
def wardrobe(item):
 parts={n:Image.open(OUT/item/'generic'/(n+'.png')).convert('RGBA') for n in ['MeadowBattleHeroWardrobeCore','MeadowBattleHeroPauldronNearWardrobe','MeadowBattleHeroArmNearUpperWardrobe','MeadowBattleHeroArmNearForearmWardrobe','MeadowBattleHeroHemFarWardrobe','MeadowBattleHeroHemNearWardrobe']}
 return parts,Image.open(OUT/item/'bow/atlas.png').convert('RGBA'),Image.open(OUT/item/'bow/torso.png').convert('RGBA')

@functools.lru_cache(None)
def head_image(path):return Image.open(path).convert('RGBA')

class Renderer:
 def __init__(self,item,hair=None,face=None):
  self.item=item;self.parts,self.bowAtlas,self.bowTorso=wardrobe(item)
  self.head={}
  if hair:self.head['MeadowBattleHeroHair']=head_image(str(R/f'Art/Parts/P1-v1/custom-heads-v1/hair-{hair}/battle/hair.png'))
  if face:self.head['MeadowBattleHeroFace']=head_image(str(R/f'Art/Parts/P1-v1/custom-heads-v1/face-{face}/battle/face.png'))
 def generic(self,weapon,clip,p):
  if weapon in ['greatSword','legendaryStaff']:
   q=pose_tables()[weapon][clip,round(p*600)];root=(q['rootOffset']['x'],q['rootOffset']['y']);ts={n:((t['pivot']['x'],t['pivot']['y']),(t['offset']['x'],t['offset']['y']),t['rotation']) for n,t in q['layers'].items()}
  else:ts,root,*_=generic_sample(clip,p)
  ts=dict(ts);a=ts['MeadowBattleHeroArmNearUpperWardrobe'];b=ts['MeadowBattleHeroWardrobeCore'];delta=math.atan2(math.sin(a[2]-b[2]),math.cos(a[2]-b[2]))
  ts['MeadowBattleHeroPauldronNearWardrobe']=(a[0],a[1],b[2]+np.clip(delta*.38,-math.pi/15,math.pi/15))
  for side in ['Far','Near']:
   t=ts['MeadowBattleHeroLeg'+side+'ThighWardrobe'];delta=math.atan2(math.sin(t[2]-b[2]),math.cos(t[2]-b[2]));ts['MeadowBattleHeroHem'+side+'Wardrobe']=(t[0],t[1],b[2]+np.clip(delta*.35,-math.pi/22.5,math.pi/22.5))
  out=Image.new('RGBA',(256,256))
  for name in GENERIC_ORDER:
   if name=='MeadowBattleHeroJointUnderlay' and clip=='idle' and weapon!='legendaryStaff':continue
   if name in self.head:im=self.head[name]
   elif name in self.parts:im=self.parts[name]
   else:im=asset({'MeadowBattleHeroWeapon':{'greatSword':'MeadowBattleGreatSword','legendaryStaff':'MeadowBattleLegendaryStaff'}.get(weapon,'MeadowBattleHeroWeapon'),**SKIN}.get(name,name))
   out.alpha_composite(transform(im,ts.get(name,((0,0),(0,0),0)),root))
  return out
 def bow(self,clip,p):
  rig=pose_tables()['huntingBow'][clip,round(p*600)]
  transforms,root,*_=generic_sample('idle' if clip in ['idle','attack'] else clip,p)
  if rig.get('canvasBaked'):root=(rig['rootOffset']['x'],rig['rootOffset']['y'])
  skip={'MeadowBattleHeroWeapon','MeadowBattleHeroFarHand','MeadowBattleHeroNearHand','MeadowBattleHeroJointUnderlay','MeadowBattleHeroWardrobeCore','MeadowBattleHeroArmNearUpperBody','MeadowBattleHeroArmNearForearmBody','MeadowBattleHeroArmNearUpperWardrobe','MeadowBattleHeroArmNearForearmWardrobe'}
  names=[n for n in CFG['layers'] if n not in skip];i=names.index('MeadowBattleHeroHair');order=names[:i]+['farArm','nearUpperArm','torso','nearSleeveConnected','head']+names[i:]+['MeadowBattleHeroWeapon','geometry','farHand','nearHand'];out=Image.new('RGBA',(256,256))
  for name in order:
   if name=='geometry':
    dr=ImageDraw.Draw(out);dr.line([(round(rig[k]['x']+root[0]),round(rig[k]['y']+root[1])) for k in ['upperTip','stringHand','lowerTip']],fill='#e1c78c',width=1)
    if rig['arrowVisible']:
     a=rig['arrowTail'];b=rig['arrowTip'];ax=a['x']+root[0];ay=a['y']+root[1];bx=b['x']+root[0];by=b['y']+root[1];dr.line((ax,ay,bx,by),fill='#d4ab66',width=1);dr.polygon([(bx+2,by),(bx-3,by-2),(bx-3,by+2)],fill='#d8e0d9')
    continue
   if name in self.head:
    im=self.head[name];t=rig['parts']['torso'];pose=((t['pivot']['x'],t['pivot']['y']),(t['offset']['x'],t['offset']['y']),t['rotation'])
   elif name in rig['nativeTiles']:
    tile=LIB['tiles'][rig['nativeTiles'][name]];im=Image.new('RGBA',(256,256));im.paste(self.bowAtlas.crop((tile['x'],tile['y'],tile['x']+tile['width'],tile['y']+tile['height'])),(tile['canvasX'],tile['canvasY']))
    t=rig['parts']['torso'];pose=((t['pivot']['x'],t['pivot']['y']),(0,0) if rig.get('canvasBaked') else (t['offset']['x'],t['offset']['y']),0 if rig.get('canvasBaked') else t['rotation'])
   elif name in ['torso','head']:
    im=(self.bowTorso if name=='torso' else asset('MeadowBattleBowReviewedBodyCore')).copy();t=rig['parts']['torso'];pose=((t['pivot']['x'],t['pivot']['y']),(t['offset']['x'],t['offset']['y']),t['rotation'])
    if name=='head':
     mask=Image.new('L',(256,256));dr=ImageDraw.Draw(mask);dr.rectangle((100,75,156,132),fill=255);dr.polygon([(121,126),(135,130),(134,138),(125,138),(119,134)],fill=255);im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
   else:
    target={'MeadowBattleHeroBodyCore':'MeadowBattleBowReviewedBodyCore','MeadowBattleHeroLegNearThighWardrobe':'MeadowBattleBowReviewedLegNearThighWardrobe','MeadowBattleHeroLegFarThighWardrobe':'MeadowBattleBowReviewedLegFarThighWardrobe','MeadowBattleHeroWeapon':'MeadowBattleHuntingBow'}.get(name,name);im=asset(target).copy();pose=transforms.get(name,((0,0),(0,0),0))
    if name=='MeadowBattleHeroBodyCore':
     mask=Image.new('L',(256,256));ImageDraw.Draw(mask).rectangle((100,174,152,190),fill=255);im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
    if name=='MeadowBattleHeroWeapon':
     t=rig['parts']['bow'];pose=((t['pivot']['x'],t['pivot']['y']),(t['offset']['x'],t['offset']['y']),t['rotation'])
   out.alpha_composite(transform(im,pose,root))
  return out
 def actor(self,weapon,clip,p):
  if clip=='revive':clip='defeat';p=1-p*p*(3-2*p)
  return self.bow(clip,p) if weapon=='huntingBow' else self.generic(weapon,clip,p)


def review(stills=False):
 D.mkdir(parents=True,exist_ok=True);renderers={item:Renderer(item) for item in art.front.PALETTES}
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
 reports=[]
 for item,renderer in renderers.items():
  for weapon in WEAPONS:
   board=Image.new('RGB',(5*256,7*280),'#1e3428');dr=ImageDraw.Draw(board)
   for row,clip in enumerate(['idle','attack','guard','hit','victory','defeat','revive']):
    for col,p in enumerate([0,.25,.5,.75,1]):
     im=renderer.actor(weapon,clip,p);x=col*256;y=row*280;board.paste(im,(x,y),im);dr.text((x+5,y+258),f'{item} {weapon} {clip} {p:.2f}',fill='#f3e1b8',font=font)
   board.save(D/f'{item}-{weapon}-states-1x.png');board.resize((2560,3920),Image.Resampling.NEAREST).save(D/f'{item}-{weapon}-states-2x.png')
 if stills:return
 for sequence in ['attack','states']:
  timings=[('attack',2700)] if sequence=='attack' else [('guard',1400),('hit',700),('victory',1080),('defeat',600),('revive',600)]
  frames=[]
  for clip,duration in timings:
   for i in range(duration//20):
    age=i*.02;p=i/max(1,duration//20-1)
    frame=Image.new('RGB',(1024,560),'#1e3428');dr=ImageDraw.Draw(frame)
    for row,(item,renderer) in enumerate(renderers.items()):
     for col,weapon in enumerate(WEAPONS):
      c,q=clip,p
      if clip=='attack':
       t=age-.5;c='idle' if t<0 or t>=1.7 else 'attack'
       if weapon=='greatSword':a=t*1.0275/1.048 if t<=1.048 else 1.0275 if t<=1.148 else 1.0275+.7425*min(1,(t-1.148)/.552);q=np.clip((a-.12)/1.65,0,1)
       elif weapon=='legendaryStaff':a=t*1.25/1.048 if t<=1.048 else 1.25 if t<=1.148 else 1.25+.52*min(1,(t-1.148)/.552);q=np.clip((a-.12)/1.65,0,1)
       elif weapon=='huntingBow':q=0 if t<0 else 1 if t>1.7 else (max(0,t)/.86*((.86-.4)/1.2) if t<=.86 else np.clip((t-.4-min(.1,max(0,t-1.048)))/1.2,0,1))
       else:q=np.clip((t-.4-min(.1,max(0,t-1.048)))/1.2,0,1)
      im=renderer.actor(weapon,c,float(q));frame.paste(im,(col*256,row*280),im);dr.text((col*256+5,row*280+258),f'{item} {weapon} {c}',fill='#f3e1b8',font=font)
    frames.append(frame)
  art.gif(frames,D/f'both-armors-{sequence}-normal.gif',20)
  with Image.open(D/f'both-armors-{sequence}-normal.gif') as im:
   decoded=[];total=0
   for n in range(im.n_frames):im.seek(n);decoded.append(im.convert('RGB').copy());total+=im.info['duration']
   assert total==len(frames)*20
   # Inspect all actual decoded frames on 1x whole-body pages.
   for start in range(0,len(decoded),4):
    page=Image.new('RGB',(2048,1120),'#1e3428')
    for j,f in enumerate(decoded[start:start+4]):page.paste(f,(j%2*1024,j//2*560))
    path=D/'decoded'/f'{sequence}-{start//4+1:03}.png';path.parent.mkdir(exist_ok=True);page.save(path)
   reports.append({'file':f'both-armors-{sequence}-normal.gif','frames':len(decoded),'durationMs':total,'sha256':sha(D/f'both-armors-{sequence}-normal.gif')})
 write(D/'animation-checks.json',{'clips':reports,'scope':'existing production pose samples; independent layer rendering, not App or device capture','newArtApproval':None})


if __name__=='__main__':
 for item in art.front.PALETTES:
  parts=canonical_assets(item);bow_assets(item,parts['MeadowBattleHeroWardrobeCore'])
  write(OUT/item/'battle-manifest.json',{'schemaVersion':1,'item':item,'design':'B','sourceCommit':SOURCE,'genericParts':{n:'generic/'+n+'.png' for n in parts},'existingBodyParts':SKIN,'genericLayerOrder':GENERIC_ORDER,'bowAtlas':'bow/atlas.png','bowTorso':'bow/torso.png','originalNativeBowJSON':'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/reviewed-bow-r7.json','weapons':WEAPONS,'clips':['idle','attack','guard','hit','victory','defeat','revive'],'originalBodyHandWeaponPoseOrRulesChanged':False,'runtimeImported':False,'artApproval':None})
 review('--stills' in sys.argv)
