#!/usr/bin/env python3
"""Export only two replacement armor candidates; freeze original and approved art."""
from pathlib import Path
import json,copy,math,hashlib,importlib.util,base64,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Equipment/b2-batch-v3';P=R/'Art/Parts/P1-v1/b2-armor-r3';I=R/'Art/Integration/Equipment-b2-batch-v3';S=R/'Art/Integration/P1-modular-eight-way-v1';A=R/'Sources/Resources/Assets.xcassets';old=R/'Art/Review/Equipment/b2-batch-v2'
for p in [D,P,I]:p.mkdir(parents=True,exist_ok=True)
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
surface=load('surface',R/'scripts/armor-shared-surface.py').ArmorSurface(R);mod=load('compose',R/'scripts/compose-character-parts.py');motion=surface.motion;catalog=json.loads((R/'Art/Integration/Equipment-b2-batch-v1/catalog.json').read_text());manifest=json.loads((old/'manifest.json').read_text());manifest.update(id='b2-batch-v3',title='B2 两甲共用贴合返修 · 第三轮',previousBatch='b2-batch-v2',previousResourceRevisionSHA256=manifest['resourceRevisionSHA256']);dirs=manifest['directions'];cols=manifest['columns'];font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',14)
for item in ['leatherArmor','runeArmor']:
 folder=P/item;folder.mkdir(exist_ok=True);template=json.loads((R/'Art/Parts/P1-v1/eight-way-v1/wayfarer/asset.json').read_text());template['id']='p1-b2-'+item.lower()+'-r3';bindings=[];sources=['authoring.json','armor-only.png'];shutil.copyfile(P/'armor-only.png',folder/'armor-only.png')
 for f in motion['frames']:
  layers={}
  for slot,im in surface.render(item,f).items():
   rel=f"png/{f['direction']}/{f['clip']}/{f['frame']:02}/{slot}.png";path=folder/rel;path.parent.mkdir(parents=True,exist_ok=True);im.save(path);layers[slot]=rel
   ed=f"editable/{f['direction']}-{f['clip']}-{f['frame']:02}-{slot}.svg";p=folder/ed;p.parent.mkdir(exist_ok=True);p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><g id="'+slot+'"><image width="256" height="256" href="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"/></g></svg>');sources.append(ed)
  bindings.append({k:f[k] for k in ['direction','clip','frame']}|{'layers':layers})
 template.update(sourceFiles=sources,bindings=bindings);write(folder/'asset.json',template);write(folder/'authoring.json',{'sourceSHA256':sha(P/'armor-only.png'),'exporter':'scripts/build-b2-armor-r3.py','surface':'scripts/armor-shared-surface.py','sourceViews':['front','front-quarter-left','profile-left','rear-quarter-left','back'],'method':'once-only anatomical source pattern fitting to original native rest; shared continuous torso/waist and whole sleeve field; exact original pose joints and layer order','profileWrists':'five nearest solid original hand marker pixels to its elbow; frozen per pose, not garment alpha fitting','bodyMotionModified':False,'oldApprovedArtModified':False,'artApproval':None})
 catalog['assets'].append({'id':template['id'],'manifest':str((folder/'asset.json').relative_to(R))})
write(I/'catalog.json',catalog);C=mod.Compositor(R,I/'catalog.json',S/'motion.json');selection=json.loads((R/'Art/Integration/P1-modular-demo-v1/selection.json').read_text())
src=R/'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py';ns={'__file__':str(src)};exec(compile(src.read_text().split("\nfor clip,data in lib['clips'].items():")[0],str(src),'exec'),ns);ns['lib']=json.loads((A/'MeadowBattleHeroAnimationV2.dataset/animation.json').read_text());original_battle=copy.copy(ns['LAYERS'])
for entry in manifest['items']:
 item=entry['id']
 if item not in ['leatherArmor','runeArmor']:continue
 entry.update(revision='b2-armor-r3',artApproval=None,scope='五种真实视角源版型、肩肘腕连续袖面与胸腰/短护裙共用变形；原身体动作保持',battleScope='按战斗原肩肘腕重新裁制，同一衣物源；六原动作离线挂载候选，非实机')
 dest=D/item;dest.mkdir(exist_ok=True);shutil.copyfile(old/item/'icon.png',dest/'icon.png')
 for preset in selection['loadouts']:
  selected=[a for a in preset['assets'] if a not in ['p1-eight-way-forester-v1','p1-eight-way-wayfarer-v1']]+['p1-b2-'+item.lower()+'-r3'];atlas=Image.new('RGBA',(3328,2048))
  for row,d in enumerate(dirs):
   for col,f in enumerate(cols):atlas.paste(C.render(selection['base'],selected,d,f['clip'],f['frame']),(col*256,row*256))
  atlas.save(dest/(preset['id']+'-walk.png'))
 atlas=Image.open(dest/'forester-walk.png');walk=[]
 for col in range(9):
  board=Image.new('RGB',(1024,560),'#20372a');dr=ImageDraw.Draw(board)
  for row,label in enumerate(manifest['directionLabels']):
   im=atlas.crop((col*256,row*256,(col+1)*256,(row+1)*256));x,y=row%4*256,row//4*280;board.paste(im,(x,y),im);dr.text((x+7,y+256),entry['name']+' · '+label,font=font,fill='#ffedc7')
  if col==0:board.save(dest/'standing.png')
  else:walk.append(board)
 walk[0].save(dest/'walk-normal.gif',save_all=True,append_images=walk[1:],duration=120,loop=0,disposal=2,optimize=True)
 new=surface.battle_layers(item);bdir=P/item/'battle';bdir.mkdir(exist_ok=True)
 for name,im in new.items():im.save(bdir/(name+'.png'))
 ns['LAYERS']=dict(original_battle,**new)
 for clip in ['idle','attack','guard','hit','victory','defeat']:
  count=ns['lib']['clips'][clip]['durationMs']//20;atlas=Image.new('RGBA',(2560,math.ceil(count/10)*256));frames=[]
  for n in range(count):
   im=ns['render'](clip,n/count);atlas.paste(im,(n%10*256,n//10*256));frame=Image.new('RGB',(512,512),'#20372a');big=im.resize((512,512),Image.Resampling.NEAREST);frame.paste(big,(0,0),big);frames.append(frame)
  atlas.save(dest/('battle-'+clip+'.png'));entry['battle'][clip]['frames']=count
  if clip=='attack':frames[0].save(dest/'battle-normal.gif',save_all=True,append_images=frames[1:],duration=20,loop=0,disposal=2,optimize=True)
for item in ['leatherArmor','runeArmor']:
 for root in [P/item/'png',P/item/'battle']:
  for p in root.rglob('*.png'):
   ar=np.asarray(Image.open(p).convert('RGBA')).copy();ar[ar[:,:,3]==0,:3]=0;Image.fromarray(ar).save(p)
files={str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file() and p.relative_to(D).parts[0] in ['leatherArmor','runeArmor'] and p.suffix in ['.png','.gif']};write(D/'files.json',files);manifest['resourceRevisionSHA256']=sha(D/'files.json');write(D/'manifest.json',manifest)
# Compact normal-speed whole-body summary, only the two repaired items.
stand=Image.new('RGB',(1024,1120),'#20372a');frames=[]
for row,item in enumerate(['leatherArmor','runeArmor']):stand.paste(Image.open(D/item/'standing.png'),(0,row*560))
stand.save(D/'batch-standing.png')
for n in range(8):
 out=Image.new('RGB',(1024,1120),'#20372a')
 for row,item in enumerate(['leatherArmor','runeArmor']):
  im=Image.open(D/item/'walk-normal.gif');im.seek(n);out.paste(im.convert('RGB'),(0,row*560))
 frames.append(out)
frames[0].save(D/'batch-walk-normal.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=True)
print(json.dumps({'revision':manifest['resourceRevisionSHA256'],'bindings':208,'artApproval':None}))
