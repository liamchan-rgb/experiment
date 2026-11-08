#!/usr/bin/env python3
"""Verify clothing coverage, original rig, hand/face preservation and toggles."""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label,binary_dilation
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/down-left/wardrobe-v1';T=R/'Art/Templates/P1-Wardrobe/down-left/v1-independent';D=R/'Art/Review/P1/modular-down-left-wardrobe-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
exp=mod('exporter',R/'scripts/export-down-left-wardrobe.py');compose=exp.compose
read=lambda p:np.array(Image.open(p).convert('RGBA'))
solid=lambda a:a[:,:,3]>128
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
connected=lambda a:label(a,np.ones((3,3)))[1]
cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['baseTemplate'];base=json.loads((B/'asset.json').read_text());old=json.loads((B/'motion.json').read_text());motion=json.loads((T/'motion.json').read_text());catalog=json.loads((T/'catalog.json').read_text());assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256']
for a in catalog['assets']:assert not compose.contract.check_asset(R/a['manifest']),a['id']
for f,g in zip(old['frames'],motion['frames']):
 for key in set(f)-{'drawOrder','artApproval'}:assert f[key]==g[key],('motion changed',key)
 assert [s for s in g['drawOrder'] if s in base['slots']]==f['drawOrder']
comp=compose.Compositor(R,T/'catalog.json',T/'motion.json');yy,xx=np.mgrid[:256,:256]
def maskim(m):
 a=np.zeros((256,256,4),np.uint8);a[m]=255;return Image.fromarray(a)
required={'torso':maskim(solid(read(B/'source/shirt.png'))&(yy>=130)),'shorts':maskim(solid(read(B/'source/pants.png')))}
for side in ['left','right']:
 required['leg.'+side]=Image.open(B/'source'/('leg.'+side+'.png')).convert('RGBA');required['arm.'+side]=maskim(solid(read(B/'source'/('arm.'+side+'.png')))&(yy>=131)&(yy<=(165 if side=='left' else 159))&~solid(read(B/'source'/('hand.'+side+'.png'))))
records=[];handChecks=faceChecks=coverageChecks=0;swordChecks=0
for i,f in enumerate(motion['frames']):
 assert np.array_equal(np.array(comp.render(base['id'],[],'down-left',f['clip'],f['frame'])),read(B/'frames'/f'{i:02}.png'))
 needed={k:solid(np.array(exp.uv_sample(im,'shirt' if k in ['torso','shorts'] else k,i,cfg))) for k,im in required.items()};handmask=exp.visible_hands(B,old['frames'][i],i)
 for outfit,hair,face,sword in itertools.product(['forester','wayfarer'],['chestnut','silver'],['blue','amber'],[False,True]):
  selected=['p1-down-left-'+outfit+'-v1','p1-down-left-lower-v1','p1-hair-'+hair+'-down-left-v1','p1-face-'+face+'-down-left-v1']+(['p1-down-left-back-scabbard-v1'] if sword else []);layers=dict(comp.layers(base['id'],selected,'down-left',f['clip'],f['frame']));a=np.array(comp.render(base['id'],selected,'down-left',f['clip'],f['frame']));key=f'{outfit}__{hair}__{face}__'+('back' if sword else 'empty');assert np.array_equal(a,read(D/'combinations'/key/f'{i:02}.png')),(i,key,'actual assembly differs');assert connected(solid(a))==1,(i,key,'whole character disconnected')
  outfitAlpha=np.zeros((256,256),bool)
  for slot,im in layers.items():
   if slot.startswith('outfit.'):outfitAlpha|=solid(np.array(im))
   if slot in base['slots']:assert np.array_equal(np.array(im),read(B/'layers'/f'{i:02}'/(slot+'.png'))),(i,key,slot,'original body layer changed')
  for part,m in needed.items():
   missing=m&~outfitAlpha&~handmask;assert not missing.any(),(i,key,part,'clothing gap',np.argwhere(missing).tolist());coverageChecks+=1
  for side in ['left','right']:
   hand=np.array(layers['body.hand.'+side]);visible=solid(hand)&handmask;assert np.array_equal(a[visible],hand[visible]),(i,key,side,'hand cropped/replaced');handChecks+=1
  for slot in ['face.eyes','face.nose','face.mouth']:
   part=np.array(layers[slot]);m=solid(part);assert m.any() and np.array_equal(a[m],part[m]),(i,key,slot,'face clipped');faceChecks+=1
  records.append({'pose':i,'combination':key,'actualCompositorDifferencePixels':0,'clothingCoverageGaps':0,'originalHandPixelsPreserved':True,'faceFeaturesPreserved':True})
  if sword:
   empty=np.array(comp.render(base['id'],selected[:-1],'down-left',f['clip'],f['frame']));weapon=solid(np.array(layers['weapon.back']));changed=np.any(empty!=a,axis=2);assert changed.any(),(i,key,'back weapon not visible');assert not (changed&~weapon).any();assert not (changed&handmask).any(),(i,key,'sword changes hand');head=solid(np.array(layers['head.base']));assert not (changed&head).any(),(i,key,'sword changes face/head');swordChecks+=1
for name,durations in [('outfits-walk-120ms.gif',[120]*8),('outfits-start-stop-120ms.gif',[480]+[120]*20+[480])]:
 with Image.open(D/name) as g:assert g.n_frames==len(durations) and [im.info['duration'] for im in ImageSequence.Iterator(g)]==durations and g.info['loop']==0
preserved=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/p)==h for p,h in preserved.items()),'old assets changed'
result={'status':'independent-wardrobe-technical-checks-pass','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'manifestsChecked':len(catalog['assets']),'actualCompositorPoses':len(records),'combinations':16,'originalMotionGeometryUnchanged':True,'bareBodyPosesUnchanged':13,'coverageChecks':coverageChecks,'handPreservationChecks':handChecks,'facePreservationChecks':faceChecks,'weaponToggleChecks':swordChecks,'preservedFiles':len(preserved),'poses':records,'limits':['Main checks full-body artwork separately; numeric checks are not artwork approval','Still viewer: complete frames and timing only; no continuous-playback claim','Current left-down module only; no other missing-direction completion, female characters, App/device or IPA acceptance']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['manifestsChecked','actualCompositorPoses','coverageChecks','handPreservationChecks','facePreservationChecks','weaponToggleChecks','preservedFiles']}))
