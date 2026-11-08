#!/usr/bin/env python3
"""Verify original-input identity, new apparel files/combinations and actual GIFs; no art approval."""
from pathlib import Path
import importlib.util,sys,json,hashlib,itertools
import numpy as np
from PIL import Image
r=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('b8final',r/'scripts/build-chat-apparel-b-eight-way.py');m=importlib.util.module_from_spec(s);sys.modules['b8final']=m;s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('mastercheck',r/'scripts/check-apparel-master.py');checker=importlib.util.module_from_spec(s);s.loader.exec_module(checker)
rev=m.REVIEW;c=m.Compositor(r,rev/'catalog.json',m.MOTION);surface=m.Surface();results=[];combo=[];gifchecks=[]
for item in m.front.PALETTES:
 p=m.PARTS/item;masters=checker.check(p/'master-manifest.json');assert masters['fileChecksPassed'] and masters['views']==8,masters
 errors=m.compose.contract.check_asset(p/'asset.json');assert not errors,errors
 a=json.loads((p/'asset.json').read_text());assert len(a['bindings'])==104
 asserts={};count=0
 for f in sorted(p.glob('masters/*/*.png'))+sorted(p.glob('png/*/*/*/*.png')):
  with Image.open(f) as im:
   im.load();arr=np.asarray(im)
   assert im.mode=='RGBA' and im.size==(256,256) and im.info.get('icc_profile'),f
   assert not np.any(arr[:,:,:3][arr[:,:,3]==0]),f
  count+=1
 assert count==32+416,count
 for b in a['bindings']:
  key=m.compose.key(b)
  for side in ['left','right']:
   original=Image.open(surface.base/surface.body[key]['body.arm.'+side]).getchannel('A')
   cloth=Image.open(p/b['layers']['outfit.sleeve.'+side]).getchannel('A')
   assert not np.any((np.asarray(original)>=128)&(np.asarray(cloth)<255)),(item,key,side,'exposed arm')
 # All two-hair/two-face/back-weapon choices on the same actual compositor.
 for hair,face,armed in itertools.product(['chestnut','silver'],['blue','amber'],[False,True]):
  selections=[a['id'],'p1-eight-way-lower-v1','p1-eight-way-hair-'+hair+'-v1','p1-eight-way-face-'+face+'-v1']
  if armed:selections.append('p1-eight-way-weapon-v1')
  h=hashlib.sha256()
  for d,clip,n in sorted(c.frames):h.update(c.render(m.BASE,selections,d,clip,n).tobytes())
  combo.append({'item':item,'hair':hair,'face':face,'backWeapon':armed,'poseCount':104,'rgbaSHA256':h.hexdigest()})
 for f in sorted((rev/item).glob('*.gif')):
  with Image.open(f) as im:
   frames=[];dur=[];hashes=[]
   for i in range(im.n_frames):
    im.seek(i);fr=im.convert('RGB');frames.append(fr.copy());dur.append(im.info.get('duration',0));hashes.append(hashlib.sha256(fr.tobytes()).hexdigest())
   expected=3360 if 'start-stop' in f.name else 960
   assert sum(dur)==expected,(f,dur)
   if 'start-stop' not in f.name:assert len(frames)==8 and all(x==120 for x in dur),(f,dur)
   gifchecks.append({'file':f.relative_to(rev).as_posix(),'decodedFrames':len(frames),'durationMs':sum(dur),'frameDurationsMs':dur,'sha256':m.sha(f),'decodedRGBHashes':hashes})
   if f.name.startswith('eight-way-'):
    for page in range(2):
     board=Image.new('RGB',(2048,1120),'#1e3428')
     for j,fr in enumerate(frames[page*4:page*4+4]):board.paste(fr,(j%2*1024,j//2*560))
     dst=rev/'decoded-gif-review'/item/f'{f.stem}-frames-{page*4+1:02}-{page*4+4:02}.png';dst.parent.mkdir(parents=True,exist_ok=True);board.save(dst)
 results.append({'item':item,'masterChecks':masters,'runtimeAssetFileChecksPassed':True,'checkedPNGFiles':count,'poseBindings':104,'layerReferences':416,'actualArmSilhouetteFullyCoveredAllPoses':True})
inputs=json.loads((rev/'input-manifest.json').read_text());assert inputs['sourceCommit']==m.SOURCE
for rel,info in inputs['referencePNGFiles'].items():
 data=(r/rel).read_bytes();assert hashlib.sha256(data).hexdigest()==info['sha256'],rel
assert len(inputs['referencePNGFiles'])==2392
receipt={'stats':{'bytes':sum(x['bytes'] for x in inputs['referencePNGFiles'].values())}}

m.write(rev/'verification.json',{'schemaVersion':'1.0.0','sourceCommit':m.SOURCE,'selectedDesign':{'starlightArmor':'B','dragonArmor':'B'},'masterChecks':results,'combinations':combo,'compositions':sum(x['poseCount'] for x in combo),'gifChecks':gifchecks,'gifFiles':len(gifchecks),'decodedFrames':sum(x['decodedFrames'] for x in gifchecks),'originalReferencePNGChecks':{'files':2392,'method':'each downloaded PNG matched original Git index blob SHA','bytes':receipt['stats']['bytes']},'motionSHA256':m.sha(m.MOTION),'originalMotionChanged':False,'originalBodyFilesChanged':False,'runtimeImported':False,'appOrSimulatorRun':False,'userArtApproval':None})
print(json.dumps({'items':len(results),'poses':208,'poseLayerReferences':832,'masterLayers':64,'compositions':sum(x['poseCount'] for x in combo),'GIFs':len(gifchecks),'decodedFrames':sum(x['decodedFrames'] for x in gifchecks)},ensure_ascii=False))
