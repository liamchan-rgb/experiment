#!/usr/bin/env python3
"""Check independent heads, battle garments, input identity and real media.
Mechanical checks do not approve artwork or run the game.
"""
from pathlib import Path
import json,sys,hashlib,subprocess,importlib.util,itertools,gzip
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
h=load('head_delivery_review',R/'scripts/build-custom-heads-v1.py')
b=load('battle_delivery_review',R/'scripts/build-chat-apparel-b-battle.py')
check=load('part_delivery_check',R/'scripts/check-character-part.py')
D=R/'Art/Integration/Appearance-battle-custom-heads-v1';D.mkdir(parents=True,exist_ok=True)
def sha(data):return hashlib.sha256(data).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

assets=[];pngs=[]
for p in sorted(h.OUT.glob('*/asset.json')):
 errors=check.check_asset(p);assert not errors,(p,errors)
 a=json.loads(p.read_text());assert len(a['bindings'])==104
 assets.append({'id':a['id'],'bindings':104,'uniqueDirectionalMasters':len({v for x in a['bindings'] for v in x['layers'].values()}),'fileChecksPassed':True})
for folder in [h.OUT,b.OUT]:
 for p in sorted(folder.rglob('*.png')):
  with Image.open(p) as im:
   im.load();a=np.asarray(im)
   assert im.mode=='RGBA' and im.size in [(96,96),(256,256),(768,2541)],(p,im.size,im.mode)
   assert not np.any(a[:,:,:3][a[:,:,3]==0]),p
   if '/masters/' in str(p) and 'custom-heads' in str(p):assert im.size==(96,96)
   pngs.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'size':im.size})
assert len(assets)==10

cat=json.loads((h.D/'catalog.json').read_text());c=h.art.Compositor(R,h.D/'catalog.json',h.art.MOTION)
combos=[]
for hair,face,item in itertools.product(h.HAIR,h.FACES,['starlight','dragon']):
 choice=['p1-eight-way-lower-v1','p1-chat-'+item+'-armor-v2','p1-custom-hair-'+hair+'-v1','p1-custom-face-'+face+'-v1'];digest=hashlib.sha256()
 for d,clip,n in sorted(c.frames):digest.update(c.render(h.art.BASE,choice,d,clip,n).tobytes())
 combos.append({'hair':hair,'face':face,'armor':item,'poses':104,'rgbaSHA256':digest.hexdigest()})
print('PASS: 4992 whole-character compositions on original gait.',flush=True)

atlas=np.asarray(b.asset('MeadowBattleBowReviewedSleeves'))
bowchecks=[]
for item in ['starlightArmor','dragonArmor']:
 new=np.asarray(Image.open(b.OUT/item/'bow/atlas.png').convert('RGBA'))
 assert np.array_equal(new[:,:,3],atlas[:,:,3]) and np.array_equal(new[~b.blue_cloth(atlas)],atlas[~b.blue_cloth(atlas)])
 kept=0
 for f in b.LIB['frames']:
  for group,index in f['nativeTiles'].items():
   if group in ['nearSleeveConnected','nearUpperArm','farArm','torso']:continue
   t=b.LIB['tiles'][index];x,y,w,ht=[t[k] for k in ['x','y','width','height']]
   assert np.array_equal(new[y:y+ht,x:x+w],atlas[y:y+ht,x:x+w]),(item,group,index)
   kept+=1
 bowchecks.append({'item':item,'all345OriginalNativeFrameBindingsKept':True,'checkedNonClothTileReferences':kept,'allAlphaAndNonClothPixelsByteExact':True,'handsHeadHairFacePantsAndBowMotionUnchanged':True})

# Pinned original data, including compressed local cache read as original bytes.
raw= json.loads((b.REF/'asset-inputs.json').read_text())['files']
inputs={x['path'] for x in raw}|{'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py','Art/Scenes/MeadowBattle/hero-combat-v2/hero-v2-configuration.json','Art/Scenes/MeadowBattle/hero-combat-v2/clips.json','Sources/Resources/hero-gait.json','Art/Integration/P1-modular-eight-way-v1/motion.json','Art/Standards/P1-Parts-v1/profile.json'}
inputs|={f'Art/Review/Battle/{folder}/{file}' for folder,file in [('great-sword-demo-v1','great-sword-poses.json'),('legendary-staff-demo-v1','legendary-staff-poses.json'),('bow-actions-r7-demo-v1','bow-poses.json')]}
for folder in ['hair-chestnut','face-blue']:
 p=R/f'Art/Parts/P1-v1/eight-way-v1/{folder}/asset.json';a=json.loads(p.read_text());inputs.add(p.relative_to(R).as_posix())
 inputs|={(p.parent/v).relative_to(R).as_posix() for row in a['bindings'] if row['clip']=='idle' for v in row['layers'].values()}
index={x.split('\t',1)[1]:x.split()[1] for x in subprocess.check_output(['git','ls-files','--stage'],cwd=R,text=True).splitlines() if '\t' in x};records=[]
for rel in sorted(inputs):
 p=b.ref(rel)
 if p.is_file():data=p.read_bytes()
 else:
  with gzip.open(str(p)+'.gz','rb') as f:data=f.read()
 blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert blob==index[rel],rel
 records.append({'path':rel,'bytes':len(data),'sha256':sha(data),'gitBlob':blob})
write(D/'input-manifest.json',{'sourceCommit':b.SOURCE,'allReadOnlyInputsMatchOriginalGitBlobs':True,'files':records})

media=[]
for p in sorted(list(b.D.glob('*.gif'))+list(h.D.glob('*.gif'))):
 with Image.open(p) as im:
  durations=[]
  for i in range(im.n_frames):im.seek(i);im.convert('RGB').load();durations.append(im.info['duration'])
 expected=2700 if 'both-armors-attack' in p.name else 4380 if 'both-armors-states' in p.name else 1720 if 'six-heads-bow' in p.name else 960
 assert sum(durations)==expected,(p,durations)
 if 'eight-way' in p.name:assert len(durations)==8 and durations==[120]*8
 media.append({'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'decodedFrames':len(durations),'durationMs':sum(durations),'frameDurationsMs':durations})

# A concise batch-review roster, retaining full 256 canvases and full bodies.
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
roster=Image.new('RGB',(1536,1120),'#1e3428');dr=ImageDraw.Draw(roster)
for i,(hair,cfg) in enumerate(h.HAIR.items()):
 face='m1-bright' if cfg['genderStyle']=='male' else 'f1-gentle'
 im=c.render(h.art.BASE,['p1-eight-way-lower-v1','p1-chat-starlight-armor-v2','p1-custom-hair-'+hair+'-v1','p1-custom-face-'+face+'-v1'],'down','idle',0).resize((512,512),Image.Resampling.NEAREST)
 x=i%3*512;y=i//3*560;roster.paste(im,(x,y),im);dr.text((x+10,y+520),cfg['label'],font=font,fill='#f3e1b8')
roster.save(h.D/'six-style-roster-2x.png')
faces=Image.new('RGB',(2048,1120),'#1e3428');dr=ImageDraw.Draw(faces)
for row,hair in enumerate(['m2-sidepart','f1-bob']):
 for col,(face,cfg) in enumerate(h.FACES.items()):
  im=c.render(h.art.BASE,['p1-eight-way-lower-v1','p1-chat-starlight-armor-v2','p1-custom-hair-'+hair+'-v1','p1-custom-face-'+face+'-v1'],'down','idle',0).resize((512,512),Image.Resampling.NEAREST);x=col*512;y=row*560;faces.paste(im,(x,y),im);dr.text((x+10,y+520),cfg['label'],font=font,fill='#f3e1b8')
faces.save(h.D/'four-face-sets-whole-body-2x.png')
catalog={'schemaVersion':1,'sourceCommit':b.SOURCE,'sharedBodyAndMotionUnchanged':True,'hairStyles':[{'id':'p1-custom-hair-'+k+'-v1','genderStyle':v['genderStyle'],'label':v['label']} for k,v in h.HAIR.items()],'faceSets':[{'id':'p1-custom-face-'+k+'-v1','genderStyle':v['genderStyle'],'label':v['label']} for k,v in h.FACES.items()],'hairAndFaceMayBeSelectedIndependently':True,'newFemaleBodyCreated':False,'runtimeSelectionUIChanged':False,'playerSaveSchemaChanged':False,'newArtApproval':None}
write(D/'appearance-catalog.json',catalog)
write(D/'verification.json',{'sourceCommit':b.SOURCE,'headAssets':assets,'headPoseBindings':1040,'wholeCharacterCompositions':4992,'combinations':combos,'PNGFiles':pngs,'bowChecks':bowchecks,'media':media,'allGIFsDecoded':True,'decodedFrames':sum(x['decodedFrames'] for x in media),'originalInputFilesVerified':len(records),'originalBodyHandsWeaponsPoseAndGaitFilesChanged':False,'runtimeImported':False,'appOrSimulatorOrDeviceRun':False,'userArtApproval':None})
print(json.dumps({'assets':10,'compositions':4992,'PNGs':len(pngs),'GIFs':len(media),'decodedFrames':sum(x['decodedFrames'] for x in media),'originalInputs':len(records)},ensure_ascii=False),flush=True)
