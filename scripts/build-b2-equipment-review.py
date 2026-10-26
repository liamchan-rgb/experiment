#!/usr/bin/env python3
"""Produce the remaining B2 art candidates and a batch-review manifest.

No app assets, body, motion, catalog, or runtime code are overwritten. New
equipment layers use the existing compositor and registered original joints.
"""
from pathlib import Path
import base64, copy, hashlib, importlib.util, io, json, math, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parents[1]
D=R/'Art/Review/Equipment/b2-batch-v1'
P=R/'Art/Parts/P1-v1/b2-equipment-v1'
I=R/'Art/Integration/Equipment-b2-batch-v1'
A=R/'Sources/Resources/Assets.xcassets'
S=R/'Art/Integration/P1-modular-eight-way-v1'
for p in [D,P,I]: p.mkdir(parents=True,exist_ok=True)
FONT='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
font=ImageFont.truetype(FONT,15)
def write(p,data):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def svg(p,im,label):
 buf=io.BytesIO();im.save(buf,format='PNG')
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256"><g id="'+label+'"><image width="256" height="256" href="data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()+'"/></g></svg>')

items=[('greatSword','重剑','great_sword','weapon'),('legendaryStaff','传奇权杖','legendary_staff','weapon'),('leatherArmor','皮甲','leather_armor','armor'),('runeArmor','符文甲','rune_armor','armor'),('powerBadge','力量徽章','power_badge','accessory'),('actionRing','行动戒指','action_ring','accessory')]
inventory=json.loads((R/'docs/planning/boardgame-skills-items-v1/inventory.json').read_text())
defs={x['id']:x for x in inventory['items']}
motion=json.loads((S/'motion.json').read_text());poses=motion['frames']
bykey={(x['direction'],x['clip'],x['frame']):x for x in poses}
dirs=['down','down-left','left','up-left','up','up-right','right','down-right']
labels=['正下','左下','正左','左上','正上','右上','正右','右下']
columns=[('idle',0)]+[('walk',x) for x in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]
old=P.parent/'eight-way-v1'
catalog=json.loads((S/'catalog.json').read_text())
source_maps={}
for item,title,slug,kind in items:
 target=P/item/'source'/('item_'+slug+'.png');target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists(): shutil.copyfile(Path('/workspace/boardgame-audit/icons')/target.name,target)
 assert digest(target)==defs[item]['existingIcon']['sha256']
 (D/item).mkdir(exist_ok=True)
 shutil.copyfile(target,D/item/'icon.png')

# Fixed whole-source transforms: no alpha-bound crop, fitting, per-frame scaling,
# or changes to body placement. Original item drawings supply the visual design.
weapon_settings={'greatSword':{'grip':[174,367],'axis':[216,-298],'scale':.205},'legendaryStaff':{'grip':[232,275],'axis':[110,-150],'scale':.205}}
def registered_weapon(item,grip,angle=None,projection=1,size=1):
 q=weapon_settings[item];src=Image.open(P/item/'source'/('item_'+next(x[2] for x in items if x[0]==item)+'.png')).convert('RGBA')
 sourceangle=math.atan2(q['axis'][1],q['axis'][0]);theta=0 if angle is None else angle-sourceangle
 # Projection is fixed by facing, never derived from alpha bounds.
 vx,vy=math.cos(theta)*q['scale']*size,math.sin(theta)*q['scale']*size
 a,b,c,d=vx*projection,vy,-vy*projection,vx
 x,y=q['grip'];tx=grip[0]-a*x-c*y;ty=grip[1]-b*x-d*y;det=a*d-b*c
 inv=(d/det,-c/det,(c*ty-d*tx)/det,-b/det,a/det,(b*tx-a*ty)/det)
 out=src.transform((256,256),Image.Transform.AFFINE,inv,Image.Resampling.BICUBIC)
 ar=np.asarray(out).copy();ar[ar[:,:,3]==0,:3]=0
 return Image.fromarray(ar)

for item in weapon_settings:
 folder=P/item;manifest=json.loads((old/'weapon/asset.json').read_text());manifest['id']='p1-b2-'+item.lower()+'-v1';bindings=[];sources=['authoring.json','source/'+next(p.name for p in (folder/'source').iterdir())]
 for f in poses:
  j=f['joints'];rs=j['shoulderRight'];lh=j['hipLeft'];dx,dy=lh[0]-rs[0],lh[1]-rs[1]
  length=math.hypot(dx,dy);axis=(dx/length,dy/length)
  # Sword tip points to the opposite hip. Staff jewel stays above the shoulder.
  direction=1 if item=='greatSword' else -1
  angle=math.atan2(axis[1]*direction,axis[0]*direction)
  grip=(rs[0]+axis[0]*4,rs[1]+axis[1]*4) if item=='greatSword' else (rs[0]+axis[0]*29,rs[1]+axis[1]*29)
  projection=.46 if abs(f['facing'][1])==0 else 1
  im=registered_weapon(item,grip,angle,projection,.88 if item=='greatSword' else 1)
  rel=f"png/{f['direction']}/{f['clip']}/{f['frame']:02}/weapon.back.png";p=folder/rel;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
  editable=f"editable/{f['direction']}-{f['clip']}-{f['frame']:02}.svg";svg(folder/editable,im,'weapon.back');sources.append(editable)
  bindings.append({k:f[k] for k in ['direction','clip','frame']}|{'layers':{'weapon.back':rel}})
 manifest.update(bindings=bindings,sourceFiles=sources,carryProfile='back-staff' if item=='legendaryStaff' else 'back-scabbard')
 write(folder/'asset.json',manifest);write(folder/'authoring.json',{'sourceIconSHA256':digest(next((folder/'source').iterdir())),'fixedWeaponSource':weapon_settings[item],'carryScaleFactor':.88 if item=='greatSword' else 1,'carryGripDistanceFromRightShoulderPx':4 if item=='greatSword' else 29,'method':'whole original icon on original right-shoulder to left-hip plane; no auto bounds fitting','bodyAndMotionModified':False,'artApproval':None})
 catalog['assets'].append({'id':manifest['id'],'manifest':str((folder/'asset.json').relative_to(R))})
 registered_weapon(item,(145.6,163.7)).save(folder/'battle-weapon.png')

# New armor keeps the verified sleeve/cuff silhouette and joint registration.
# Material and separate panel/strap/rivet artwork live only in the new package.
def material(source,kind):
 ar=np.asarray(source).copy();rgb=ar[:,:,:3].astype(float);lum=rgb@np.array([.2126,.7152,.0722])
 dark=lum<43;gold=(rgb[:,:,0]>rgb[:,:,2]*1.2)&(rgb[:,:,1]>rgb[:,:,2]*1.1)
 linen=(rgb.max(2)-rgb.min(2)<36)&(lum>148)
 if kind=='leatherArmor': low=np.array([54,33,25]);high=np.array([167,109,61])
 else: low=np.array([39,51,74]);high=np.array([199,207,199])
 t=np.clip((lum-30)/180,0,1)[:,:,None];new=low+(high-low)*t
 new[dark]=rgb[dark];new[gold]=rgb[gold]*np.array([1,.95,.86]);new[linen]=np.minimum(rgb[linen]*np.array([1,.98,.9]),255)
 ar[:,:,:3]=np.clip(new,0,255).astype('uint8');ar[ar[:,:,3]==0,:3]=0
 return Image.fromarray(ar)
def decorate(source,kind,slot,frame=None,battle=False):
 out=material(source,kind);overlay=Image.new('RGBA',(256,256));d=ImageDraw.Draw(overlay)
 leather=kind=='leatherArmor';edge='#4d3020' if leather else '#343d51';trim='#d3a660';panel='#9b643a' if leather else '#b9c6cc';lit='#c08d54' if leather else '#e5e4cf'
 if battle:
  origin=(126,150);width=22;bottom=173;back=False
 else:
  j=frame['joints'];origin=((j['shoulderLeft'][0]+j['shoulderRight'][0])/2,j['neck'][1]+15);width=max(7,abs(j['shoulderRight'][0]-j['shoulderLeft'][0])*.78);bottom=(j['hipLeft'][1]+j['hipRight'][1])/2+1;back=frame['facing'][1]<0
 cx,cy=origin
 if slot=='outfit.torso' or battle and slot=='MeadowBattleHeroWardrobeCore':
  w=width/2
  points=[(cx-w,cy),(cx+w,cy),(cx+w-2,bottom-7),(cx,bottom-3),(cx-w+2,bottom-7)]
  d.polygon(points,fill=panel,outline=edge)
  # Faceted plate rather than a flat fill: fixed upper-left key light.
  d.polygon([(cx-w+1,cy+1),(cx,cy+2),(cx,bottom-5),(cx-w+3,bottom-8)],fill='#ae7744' if leather else '#d1d6ce')
  d.polygon([(cx,cy+2),(cx+w-1,cy+1),(cx+w-3,bottom-8),(cx,bottom-5)],fill='#7b4e2e' if leather else '#7e939f')
  d.line([points[0],points[1],points[2]],fill=lit,width=1)
  d.line((cx-w+2,cy+6,cx+w-2,cy+6),fill='#7b4e2e' if leather else '#929da4',width=1)
  if leather:
   d.line((cx-w,cy+1,cx+w-2,bottom-8),fill=edge,width=4);d.line((cx-w,cy,cx+w-2,bottom-9),fill='#b17a43',width=2)
   for xx,yy in [points[0],points[1],points[2],points[-1]]:d.rectangle((round(xx),round(yy)+2,round(xx)+1,round(yy)+3),fill=trim)
   d.line((cx-w+3,bottom-12,cx+w-3,bottom-12),fill=edge,width=1)
  else:
   d.line((cx,cy+1,cx,bottom-5),fill=trim,width=2)
   if not back:d.polygon([(cx,cy+3),(cx+4,cy+8),(cx,cy+13),(cx-4,cy+8)],fill='#ad79c7',outline=trim)
   else:d.line([(cx-4,cy+6),(cx,cy+3),(cx+4,cy+6),(cx,cy+12),(cx-4,cy+6)],fill='#6e88ac',width=1)
  d.line((cx-w-2,bottom-4,cx+w+2,bottom-4),fill=edge,width=4);d.line((cx-w-2,bottom-5,cx+w+2,bottom-5),fill=trim,width=1)
 elif 'sleeve' in slot or battle and slot=='MeadowBattleHeroArmNearUpperWardrobe':
  if battle:sx,sy=117,141
  else:
   side='Left' if slot.endswith('left') else 'Right';sx,sy=frame['joints']['shoulder'+side]
  d.polygon([(sx-7,sy+2),(sx-3,sy-1),(sx+4,sy),(sx+7,sy+7),(sx+3,sy+10),(sx-6,sy+8)],fill=panel,outline=edge)
  d.line((sx-5,sy+3,sx+3,sy+3),fill=lit,width=1)
  d.line((sx-5,sy+7,sx+4,sy+8),fill=trim,width=1)
 elif slot=='outfit.hem.front':
  for x in [cx-9,cx-3,cx+3,cx+9]:d.line((x,bottom,x-2,bottom+13),fill=edge,width=1)
 # Clip decor to the exact independent garment, retaining the source alpha.
 alpha=out.getchannel('A');oa=np.array(overlay.getchannel('A'),dtype=np.uint16);sa=np.array(alpha,dtype=np.uint16);overlay.putalpha(Image.fromarray(((oa*sa)//255).astype('uint8')))
 out.alpha_composite(overlay);out.putalpha(alpha)
 arr=np.asarray(out).copy();arr[arr[:,:,3]==0,:3]=0
 return Image.fromarray(arr)

for item in ['leatherArmor','runeArmor']:
 folder=P/item;src=old/'wayfarer';manifest=json.loads((src/'asset.json').read_text());manifest['id']='p1-b2-'+item.lower()+'-v1';sources=['authoring.json','source/'+next((folder/'source').iterdir()).name];bindings=[]
 for b in manifest['bindings']:
  f=bykey[(b['direction'],b['clip'],b['frame'])];layers={}
  for slot,relative in b['layers'].items():
   im=decorate(Image.open(src/relative).convert('RGBA'),item,slot,f);p=folder/relative;p.parent.mkdir(parents=True,exist_ok=True);im.save(p);layers[slot]=relative
   ed=f"editable/{b['direction']}-{b['clip']}-{b['frame']:02}-{slot}.svg";svg(folder/ed,im,slot);sources.append(ed)
  bindings.append({k:b[k] for k in ['direction','clip','frame']}|{'layers':layers})
 manifest.update(sourceFiles=sources,bindings=bindings)
 write(folder/'asset.json',manifest);write(folder/'authoring.json',{'sourceGarment':'p1-eight-way-wayfarer-v1','method':'new separate armor material/panel/strap/pauldron artwork, clipped to original per-pose independent garment silhouettes','registration':'existing registered joints, no extra translation or motion phase rotation','originalGarmentModified':False,'artApproval':None})
 catalog['assets'].append({'id':manifest['id'],'manifest':str((folder/'asset.json').relative_to(R))})
 bdir=folder/'battle';bdir.mkdir(exist_ok=True)
 for name in ['MeadowBattleHeroWardrobeCore','MeadowBattleHeroArmNearUpperWardrobe','MeadowBattleHeroArmNearForearmWardrobe']:
  im=decorate(Image.open(A/(name+'.imageset')/(name+'.png')).convert('RGBA'),item,name,battle=True);im.save(bdir/(name+'.png'))

write(I/'catalog.json',catalog)
spec=importlib.util.spec_from_file_location('batch_compositor',R/'scripts/compose-character-parts.py');comp=importlib.util.module_from_spec(spec);spec.loader.exec_module(comp)
C=comp.Compositor(R,I/'catalog.json',S/'motion.json')
selection=json.loads((R/'Art/Integration/P1-modular-demo-v1/selection.json').read_text())
presets=selection['loadouts'];output=[]
for item,title,slug,kind in items:
 entry={'id':item,'name':title,'kind':kind,'icon':item+'/icon.png','definition':defs[item]['definition'],'artApproval':None,'runtimeIntegrated':False,'revision':'b2-batch-v1','walk':{},'battle':{},'checks':[]}
 if kind=='accessory':
  entry.update(scope='图标与装备信息；不制作夸大尺寸的人物挂件',existingIconReused=True)
  output.append(entry);continue
 assetid='p1-b2-'+item.lower()+'-v1'
 for preset in presets:
  selected=[a for a in preset['assets'] if not (a=='p1-eight-way-weapon-v1' and kind=='weapon') and not (kind=='armor' and a in ['p1-eight-way-forester-v1','p1-eight-way-wayfarer-v1'])]+[assetid]
  atlas=Image.new('RGBA',(13*256,8*256))
  for row,d in enumerate(dirs):
   for col,(clip,n) in enumerate(columns):atlas.paste(C.render(selection['base'],selected,d,clip,n),(col*256,row*256))
  name=preset['id']+'-walk.png';atlas.save(D/item/name);entry['walk'][preset['id']]=item+'/'+name
  # New garment is shared; head/face and lower remain the original selections.
  entry['checks'].append({'appearance':preset['id'],'bindings':104})
 frames=[]
 atlas=Image.open(D/item/'forester-walk.png')
 for n in range(8):
  board=Image.new('RGB',(1024,560),'#20372a');draw=ImageDraw.Draw(board)
  for row,d in enumerate(dirs):
   sprite=atlas.crop(((n+1)*256,row*256,(n+2)*256,(row+1)*256));x=row%4*256;y=row//4*280;board.paste(sprite,(x,y),sprite);draw.text((x+8,y+254),labels[row]+' · '+title,font=font,fill='#ffedc7')
  frames.append(board)
 frames[0].save(D/item/'walk-normal.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=True)
 entry['gif']=item+'/walk-normal.gif'
 standing=Image.new('RGB',(1024,560),'#20372a');draw=ImageDraw.Draw(standing)
 for row in range(8):
  sprite=atlas.crop((0,row*256,256,(row+1)*256));x=row%4*256;y=row//4*280;standing.paste(sprite,(x,y),sprite);draw.text((x+8,y+254),labels[row]+' · '+title,font=font,fill='#ffedc7')
 standing.save(D/item/'standing.png');entry['standing']=item+'/standing.png'
 output.append(entry)

# Offline battle attachment candidates, using the current production clip data.
source=R/'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py';ns={'__file__':str(source)}
exec(compile(source.read_text().split("\nfor clip,data in lib['clips'].items():")[0],str(source),'exec'),ns)
ns['lib']=json.loads((A/'MeadowBattleHeroAnimationV2.dataset/animation.json').read_text())
original_layers=copy.copy(ns['LAYERS']);original_clips=copy.deepcopy(ns['lib'])
def smooth(v):return v*v*(3-2*v)
# Preserve impact phase .54. Longer anticipation followed by a firm swing and
# slower recovery; this candidate clip is separate from the production library.
def sword_phase(p):
 anchors=[(0,0),(.32,.14),(.43,.28),(.54,.54),(.66,.62),(1,1)]
 for (a,x),(b,y) in zip(anchors,anchors[1:]):
  if p<=b:return x+(y-x)*smooth((p-a)/(b-a))
 return 1
for entry in output:
 item=entry['id'];kind=entry['kind']
 if kind=='accessory':continue
 ns['LAYERS']=copy.copy(original_layers)
 ns['lib']=copy.deepcopy(original_clips)
 if kind=='weapon':
  # Longer blades and jeweled staff heads must clear the unchanged face.
  # Candidate-only arm keys; original production clips remain untouched.
  for key in ns['lib']['clips']['attack']['keys']:
   if key['t']==.14:key.update(shoulder=-.16,elbow=-.24,wrist=.18)
   if key['t']==.28:key.update(shoulder=-.22,elbow=-.30,wrist=.22)
   if key['t']==.45:key.update(shoulder=-.20,elbow=-.20,wrist=.12)
  for name in ['guard','hit','victory']:
   for key in ns['lib']['clips'][name]['keys']:
    if key['lean']+key['shoulder']+key['elbow']+key['wrist']<-.55:
     key['shoulder']=max(key['shoulder'],-.22)
     key['elbow']=max(key['elbow'],-.30)
     key['wrist']=max(key['wrist'],.18)
  write(P/item/'battle-clips.json',ns['lib'])
 if kind=='weapon':ns['LAYERS']['MeadowBattleHeroWeapon']=Image.open(P/item/'battle-weapon.png').convert('RGBA')
 else:
  for path in (P/item/'battle').glob('*.png'):ns['LAYERS'][path.stem]=Image.open(path).convert('RGBA')
 for clip in ['idle','attack','guard','hit','victory','defeat']:
  duration=1800 if item=='greatSword' and clip=='attack' else ns['lib']['clips'][clip]['durationMs']
  count=duration//20
  atlas=Image.new('RGBA',(256*10,256*math.ceil(count/10)));frames=[]
  for n in range(count):
   p=n/(count-1)
   phase=sword_phase(p) if item=='greatSword' and clip=='attack' else p
   sprite=ns['render'](clip,phase);atlas.paste(sprite,(n%10*256,n//10*256))
   frame=Image.new('RGB',(512,512),'#20372a');frame.paste(sprite.resize((512,512),Image.Resampling.NEAREST),(0,0),sprite.resize((512,512),Image.Resampling.NEAREST));frames.append(frame)
  filename='battle-'+clip+'.png';atlas.save(D/item/filename);entry['battle'][clip]={'file':item+'/'+filename,'frames':count,'frameMs':20,'columns':10}
  if clip=='attack':
   frames[0].save(D/item/'battle-normal.gif',save_all=True,append_images=frames[1:],duration=20,loop=0,disposal=2,optimize=True);entry['battleGif']=item+'/battle-normal.gif'
 entry['battleScope']='侧向完整人物持握/衣物挂载候选；不代表技能光效或原子结算接入'
 if item=='legendaryStaff':entry['battleScope']='现有侧向六动作的权杖持握检查；专用投射/施法演出尚待整合，不算已完成'

manifest={'id':'b2-batch-v1','title':'B2 基础装备 · 批量美术审核','date':'2026-10-26','bodyCanvas':[256,256],'walkFrameMs':120,'directions':dirs,'directionLabels':labels,'columns':[{'clip':c,'frame':n} for c,n in columns],'items':output,'scope':'六件素材审核候选；不修改当前demo，不包含未完成的规则/UI/存档或专用施法接入','sourceBodyManifestSHA256':digest(old/'base/asset.json'),'sourceMotionSHA256':digest(S/'motion.json'),'newArtApproval':None}
files=sorted(p for p in D.rglob('*') if p.is_file() and p.parent!=D and p.suffix in ['.png','.gif'])
write(D/'files.json',{str(p.relative_to(D)):digest(p) for p in files})
manifest['resourceRevisionSHA256']=digest(D/'files.json');write(D/'manifest.json',manifest)
print(json.dumps({'items':len(output),'newWalkingBindings':4*104,'appearances':2,'newBodyArtwork':False,'runtimeModified':False,'review':str(D),'revision':manifest['resourceRevisionSHA256']},ensure_ascii=False))
