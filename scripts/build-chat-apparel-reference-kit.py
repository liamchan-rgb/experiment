#!/usr/bin/env python3
"""Build documentation/reference examples from existing art, without editing it.
Chat paints five static master views; Codex reuses the authored rig for poses.
"""
import base64,csv,hashlib,importlib.util,json,shutil,sys,zipfile
import numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2';E=D/'examples';T=D/'templates';I=D/'integration'
VIEWS={'front':'down','front-quarter-left':'down-left','profile-left':'left','rear-quarter-left':'up-left','back':'up'}
SLOTS=['outfit.torso','outfit.sleeve.left','outfit.sleeve.right','outfit.hem.front']
ITEMS={'starlightArmor':'p1-chat-starlight-armor-v2','dragonArmor':'p1-chat-dragon-armor-v2'}
MOTION=ROOT/'Art/Integration/P1-modular-eight-way-v1/motion.json';BASE='p1-eight-way-base-v1'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree_sha(root):
 h=hashlib.sha256();files=sorted(p for p in root.rglob('*') if p.is_file())
 for p in files:h.update((p.relative_to(root).as_posix()+'\0'+sha(p)+'\n').encode())
 return {'sha256':h.hexdigest(),'files':len(files)}
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
fontfile=next(p for p in ['/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if Path(p).exists())
def font(n):return ImageFont.truetype(fontfile,n)
def bg(im,scale=1):
 out=Image.new('RGB',(256*scale,256*scale),'#1e3428');im=im.resize(out.size,Image.Resampling.NEAREST);out.paste(im,(0,0),im);return out
def cell(im,label,scale=1):
 out=Image.new('RGB',(256*scale,282*scale),'#1e3428');out.paste(bg(im,scale),(0,0));ImageDraw.Draw(out).text((6*scale,260*scale),label,font=font(11*scale),fill='#f6e4b9');return out
protected_roots=[ROOT/'Art/Parts/P1-v1/eight-way-v1',ROOT/'Art/Parts/P1-v1/b5-set-armors-v1']
protected_before={str(p.relative_to(ROOT)):tree_sha(p) for p in protected_roots}
for p in [E,T,I,E/'body-guides',E/'blue-coat-masters',E/'historical-b5']:p.mkdir(parents=True,exist_ok=True)
motion=json.loads(MOTION.read_text());pose={(f['direction'],f['clip'],f['frame']):f for f in motion['frames']}
C=load('master_example_compositor',ROOT/'scripts/compose-character-parts.py').Compositor
c=C(ROOT,ROOT/'Art/Integration/P1-modular-eight-way-v1/catalog.json',MOTION)
choices=['p1-eight-way-lower-v1','p1-eight-way-hair-chestnut-v1','p1-eight-way-face-blue-v1'];blue='p1-eight-way-wayfarer-v1'
surface_module=load('master_example_surface',ROOT/'scripts/armor-shared-surface-r4.py')
cuff_reference=surface_module.ArmorSurface(ROOT)
resolved_joints={}
manifest={'schemaVersion':'1.0.0','kind':'p1-apparel-masters','id':'p1-reference-blue-coat-masters','baseId':BASE,'canvas':[256,256],'referenceMotionSHA256':sha(MOTION),'referenceOnly':True,'referenceType':'static pose layer layout; hidden pattern completeness is not approved','views':[],'sourceFiles':[]}
normalizations=[]
input_files=[MOTION,ROOT/'scripts/armor-shared-surface-r4.py',ROOT/'scripts/build-b5-set-armors.py',ROOT/'Art/Parts/P1-v1/eight-way-v1/base/asset.json',ROOT/'Art/Parts/P1-v1/eight-way-v1/wayfarer/asset.json',ROOT/'Art/Standards/P1-Parts-v1/profile.json',ROOT/'Art/Standards/P1-Parts-v1/asset.schema.json']
guide_board=Image.new('RGB',(5*512,580),'#1e3428');layer_board=Image.new('RGB',(6*256,5*282),'#1e3428')
for vi,(view,direction) in enumerate(VIEWS.items()):
 f=pose[direction,'idle',0];joints=cuff_reference.joints(f);resolved_joints[view]=joints;body=c.render(BASE,choices,direction,'idle',0);body.save(E/'body-guides'/f'{view}.png')
 guide=body.copy();dd=ImageDraw.Draw(guide)
 for side,col in [('Left','#45e7ee'),('Right','#ffae4d')]:
  chain=[tuple(joints[k+side]) for k in ['shoulder','elbow','wrist']];dd.line(chain,fill=col,width=1)
  for x,y in chain:dd.ellipse((x-1,y-1,x+1,y+1),fill=col)
 for key,col in [('neck','#ffffff'),('hipLeft','#fa7fcd'),('hipRight','#fa7fcd')]:
  x,y=joints[key];dd.ellipse((x-1,y-1,x+1,y+1),fill=col)
 guide.save(E/'body-guides'/f'{view}-joints.png');guide_board.paste(cell(guide,view+' / idle0',2),(vi*512,0))
 layers=dict(c.layers(BASE,choices+[blue],direction,'idle',0));layer_board.paste(cell(body,'body reference'),(0,vi*282))
 row={'view':view,'referencePose':{'direction':direction,'clip':'idle','frame':0},'layers':{}}
 groups={}
 for si,slot in enumerate(SLOTS):
  rel=f'masters/{view}/{slot}.png';target=E/'blue-coat-masters'/rel;target.parent.mkdir(parents=True,exist_ok=True)
  asset=c.asset(blue);b=asset[2][direction,'idle',0];source=asset[1].parent/b['layers'][slot];original=np.array(Image.open(source).convert('RGBA'));clean=original.copy();count=int(np.any(clean[:,:,:3]!=0,axis=2)[clean[:,:,3]==0].sum());clean[clean[:,:,3]==0]=0;Image.fromarray(clean).save(target);assert np.array_equal(clean[:,:,3],original[:,:,3]);assert np.array_equal(clean[original[:,:,3]>0],original[original[:,:,3]>0]);normalizations.append({'view':view,'slot':slot,'originalSHA256':sha(source),'referenceSHA256':sha(target),'clearedInvisibleRGBPixels':count,'visibleRGBAAndAlphaUnchanged':True});input_files.append(source);row['layers'][slot]=rel
  layer_board.paste(cell(layers[slot],slot),(256*(si+1),vi*282));encoded=base64.b64encode(target.read_bytes()).decode()
  groups[slot]=f'<g id="{slot}"><image width="256" height="256" href="data:image/png;base64,{encoded}"/></g>'
  if layers[slot].getchannel('A').getbbox() is None:row.setdefault('transparentLayers',{})[slot]='existing example has no hem in this static view'
 svg=E/'blue-coat-masters'/f'editable/{view}.svg';svg.parent.mkdir(exist_ok=True);svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'+''.join(groups[slot] for slot in f['drawOrder'] if slot in groups)+'</svg>\n')
 row['referenceLayerOrder']=[slot for slot in f['drawOrder'] if slot in SLOTS];manifest['sourceFiles'].append(f'editable/{view}.svg');manifest['views'].append(row)
 full=c.render(BASE,choices+[blue],direction,'idle',0);layer_board.paste(cell(full,'same body + blue coat'),(5*256,vi*282))
write(E/'body-guides/joints.json',{'source':'motion joints; missing profile wrist uses existing cuff_marker on original hand pixels','views':resolved_joints})
ImageDraw.Draw(guide_board).text((10,9),'REFERENCE ONLY / cyan: character LEFT / orange: RIGHT / white: neck / pink: hip',font=font(18),fill='#f6e4b9')
guide_board.save(E/'01-five-master-guides-2x.png');layer_board.save(E/'02-four-layers-and-composite-1x.png');layer_board.resize((layer_board.width*2,layer_board.height*2),Image.Resampling.NEAREST).save(E/'02-four-layers-and-composite-2x.png')
write(E/'blue-coat-masters/source/reference-normalization.json',normalizations);manifest['sourceFiles'].append('source/reference-normalization.json')
write(E/'blue-coat-masters/source/palette.json',{'referenceOnly':True,'note':'Use existing blue coat for position and pixel density; do not recolor it as the new armor.'});manifest['sourceFiles'].append('source/palette.json');write(E/'blue-coat-masters/master-manifest.json',manifest)
# Real existing sampler, used read-only; compare every output pixel to the old export.
surface_module=load('master_example_surface',ROOT/'scripts/armor-shared-surface-r4.py')
b5c=C(ROOT,ROOT/'Art/Review/P1/b5-set-armors-v1/catalog.json',MOTION);evidence=[];demo=[]
for item in ITEMS:
 folder=ROOT/'Art/Parts/P1-v1/b5-set-armors-v1'/item;dest=E/'historical-b5'/item;dest.mkdir(parents=True,exist_ok=True)
 for name in ['armor-design.svg','armor-template-sheet.png','palette.json']:
  source=folder/'source'/name;shutil.copyfile(source,dest/name);input_files.append(source)
 surface=surface_module.ArmorSurface(ROOT);surface.sheet=Image.open(folder/'source/armor-template-sheet.png').convert('RGBA');surface.patterns={}
 if item=='starlightArmor':
  for view,direction in VIEWS.items():
   for slot,im in surface.fit('leatherArmor',direction).items():
    a=np.array(im);a[a[:,:,3]==0]=0;target=dest/'registered-patterns'/view/(slot+'.png');target.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(a).save(target)
 a=json.loads((folder/'asset.json').read_text());bindings={(b['direction'],b['clip'],b['frame']):b for b in a['bindings']}
 for n in range(1,9):
  actual=surface.render('leatherArmor',pose['down','walk',n])
  for slot in SLOTS:
   expected=Image.open(folder/bindings['down','walk',n]['layers'][slot]).convert('RGBA')
   assert actual[slot].tobytes()==expected.tobytes(),(item,n,slot)
  if item=='starlightArmor':demo.append(b5c.render(BASE,choices+['p1-b5-starlight-armor-v1'],'down','walk',n))
 evidence.append({'item':item,'masterSourceSHA256':sha(folder/'source/armor-template-sheet.png'),'sourceCanvas':list(surface.sheet.size),'poseCount':8,'comparedLayers':32,'allPixelsMatchExistingExport':True,'newDesignApproved':False})
 tech=ROOT/f'Art/Review/P1/b5-set-armors-v1/preview/p1-b5-{"starlight-armor" if item=="starlightArmor" else "dragon-armor"}-v1/standing-1x.png';shutil.copyfile(tech,E/f'HISTORY-TOO-PLAIN-{item}.png');input_files.append(tech)
board=Image.new('RGB',(4*256,3*282+58),'#1e3428');dd=ImageDraw.Draw(board);dd.text((10,8),'TECHNICAL REUSE ONLY / old design is not approved',font=font(17),fill='#ffe4a4');dd.text((10,28),'仅演示母版复用；旧造型不是新设计标准',font=font(14),fill='#f6e4b9')
master=Image.open(E/'historical-b5/starlightArmor/armor-template-sheet.png').convert('RGBA').crop((0,0,1774,450));master.thumbnail((1010,245),Image.Resampling.LANCZOS);board.paste(master,(7,40),master)
for j,im in enumerate(demo):board.paste(cell(im,f'program output walk{j+1:02d}'),((j%4)*256,282+(j//4)*282+58))
board.save(E/'03-one-master-to-eight-frames.png')
frames=[bg(im) for im in demo];palette=Image.new('RGB',(256*4,256*2))
for j,f in enumerate(frames):palette.paste(f,(j%4*256,j//4*256))
pal=palette.quantize(colors=256);encoded=[f.quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
encoded[0].save(E/'03-reuse-demo-normal.gif',save_all=True,append_images=encoded[1:],duration=120,loop=0,disposal=1,optimize=True)
with Image.open(E/'03-reuse-demo-normal.gif') as im:
 assert im.n_frames==8
 for n in range(8):im.seek(n);assert im.info['duration']==120
write(E/'reuse-verification.json',{'method':'existing five-view surface sampler, no artwork/body/motion edits','items':evidence,'comparedLayers':64,'demoGIF':{'frames':8,'frameMs':120,'durationMs':960},'artApproval':None,'appOrSimulatorRun':False})
for src,name in [('Art/Review/Equipment/b2-batch-v5/rune-left-walk-normal.gif','rune-left-cuff-approved.gif'),('Art/Review/Equipment/b2-batch-v5/rune-right-walk-normal.gif','rune-right-cuff-approved.gif'),('Art/Review/Equipment/b2-batch-v5/user-approval-profile.json','rune-cuff-approval-scope.json')]:
 p=ROOT/src;shutil.copyfile(p,E/name);input_files.append(p)
# Author-facing 40 master entries; Codex-only 832 program output references.
master_rows=[];pose_rows=[]
for item,identifier in ITEMS.items():
 m={'schemaVersion':'1.0.0','kind':'p1-apparel-masters','id':identifier,'baseId':BASE,'canvas':[256,256],'referenceMotionSHA256':sha(MOTION),'views':[],'sourceFiles':[f'editable/{v}.svg' for v in VIEWS]+['source/palette.json','source/prompts.txt']}
 for view,direction in VIEWS.items():
  row={'view':view,'referencePose':{'direction':direction,'clip':'idle','frame':0},'layers':{}}
  for slot in SLOTS:
   rel=f'masters/{view}/{slot}.png';row['layers'][slot]=rel;master_rows.append([item,identifier,view,slot,rel,direction,'idle',0,'Chat','not_started'])
  m['views'].append(row)
 write(T/f'{item}-master.json.template',m)
 for frame in motion['frames']:
  for slot in SLOTS:pose_rows.append([item,identifier,frame['direction'],frame['clip'],frame['frame'],slot,f"png/{frame['direction']}/{frame['clip']}/{frame['frame']:02d}/{slot}.png",'Codex','pending_master_input'])
assert len(master_rows)==40 and len(pose_rows)==832
with (T/'master-delivery-plan-40.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['item','id','view','slot','file','referenceDirection','referenceClip','referenceFrame','owner','status']);w.writerows(master_rows)
with (I/'pose-export-plan-832.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['item','id','direction','clip','frame','slot','file','owner','status']);w.writerows(pose_rows)
write(T/'handoff-record.json',{'templateOnly':True,'stage':'not_started','status':'incomplete','selectedDesign':{'starlightArmor':None,'dragonArmor':None},'actualMasterFiles':[],'expectedDefaultMasterReferencesPerItem':20,'inputFilesActuallyRead':[],'fileChecksActuallyRun':[],'fullBodyReviewActuallyDone':[],'missingItems':[],'capabilityLimits':[],'userArtApproval':None,'poseFramesCreatedByChat':False,'codexIntegrationCompleted':False})
write(E/'input-snapshot.json',{'source':'existing project files, unchanged','baseId':BASE,'motionSHA256':sha(MOTION),'staticMasterViews':VIEWS,'inputSHA256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(input_files))},'newArmorCreated':False,'referenceBoardsOnly':True})
protected_after={str(p.relative_to(ROOT)):tree_sha(p) for p in protected_roots};assert protected_after==protected_before
# Keep only the new master-route documents in the downloadable kit.
checker=load('check_master_example',ROOT/'scripts/check-apparel-master.py');report=checker.check(E/'blue-coat-masters/master-manifest.json');assert report['fileChecksPassed'],report
write(D/'verification.json',{'blueMasterExample':report,'masterPlanRows':40,'codexOutputPlanRows':832,'existingSamplerComparedLayers':64,'existingSamplerPixelIdentity':True,'sourceFilesUnmodified':True,'referenceCopiesClearOnlyInvisibleRGB':True,'normalizedReferenceLayers':sum(n['clearedInvisibleRGBPixels']>0 for n in normalizations),'newArmorCreated':False,'appOrSimulatorRun':False,'protectedOriginalTreesBefore':protected_before,'protectedOriginalTreesAfter':protected_after})
start=(D/'CHAT_START.txt').read_text();(ROOT/'Downloads/Chat-Apparel-Masters-v2.txt').write_text(start)
files=[p for p in D.rglob('*') if p.is_file()];names={p.relative_to(D).as_posix():p for p in files}
names['00_START_HERE.txt']=D/'CHAT_START.txt';names['tools/check-apparel-master.py']=ROOT/'scripts/check-apparel-master.py'
zip_path=ROOT/'Downloads/Chat-Apparel-Masters-v2.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,p in sorted(names.items()):
  info=zipfile.ZipInfo('Meadow-Apparel-Masters-v2/'+name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
write(ROOT/'Downloads/Chat-Apparel-Masters-v2.json',{'scope':'static apparel master taskbook and existing-art reference examples, not an IPA','zip':zip_path.name,'bytes':zip_path.stat().st_size,'sha256':sha(zip_path),'files':len(names),'chatMasterReferences':40,'codexPoseOutputReferences':832,'newDesignApproved':False})
print(json.dumps({'zipBytes':zip_path.stat().st_size,'zipSHA256':sha(zip_path),'files':len(names),'blueMasterCheck':report,'existingSamplerPixelChecks':64},ensure_ascii=False),flush=True)
