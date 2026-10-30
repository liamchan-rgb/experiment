#!/usr/bin/env python3
"""Check independent head resources against the unchanged approved body/motion."""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/down-left/heads-v1';T=R/'Art/Templates/P1-Heads/down-left/v1-independent';D=R/'Art/Review/P1/modular-down-left-heads-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=mod('compose',R/'scripts/compose-character-parts.py')
def read(p):return np.array(Image.open(p).convert('RGBA'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def solid(a):return a[:,:,3]>128
cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['bodyTemplate'];base=json.loads((B/'asset.json').read_text());sourceMotion=json.loads((B/'motion.json').read_text());motion=json.loads((T/'motion.json').read_text());profile=json.loads((R/'Art/Standards/P1-Parts-v1/profile.json').read_text());oldProfile=json.loads((D/'baseline-profile.json').read_text());stripped=copy.deepcopy(profile);newLayout=stripped['headLayouts'].pop('down-left');assert stripped==oldProfile,'existing profile fields changed'
assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256']
approval=json.loads((R/cfg['bodyApproval']).read_text());assert approval['status']=='approved'
for name,h in approval['artifacts'].items():assert sha((R/cfg['bodyApproval']).parent/name)==h
for name,pack in cfg['packages'].items():
 assert not compose.contract.check_asset(P/name/'asset.json'),name
 for slot in pack['slots']:
  a=read(P/name/'png'/(slot+'.png'));mask=solid(a);assert mask.any()
  if slot=='hair.front':assert label(mask,np.ones((3,3)))[1]==1,(name,'hair orphan')
  if slot.startswith('face.'):assert int(mask.sum())<=70,(name,slot,'face patch exceeds feature-only scope')
for left,right in zip(sourceMotion['frames'],motion['frames']):
 assert right['drawOrder']==left['drawOrder']+['face.eyes','face.brows','face.nose','face.mouth','hair.front']
 for k in set(left)-{'drawOrder','artApproval'}:assert left[k]==right[k],('original motion field changed',k)
head=solid(read(B/cfg.get('headSource','source/head.base.png'))[61:157,76:172]);yy,xx=np.mgrid[:96,:96];# Crown and rear contour, excluding the intentional V-shaped frontal parting.
# Frontal hairline/forehead proportions are reviewed on whole-body views.
scalp=head&((yy<=36)|((xx>=70)&(yy<=50)))
for hair in ['hair-chestnut','hair-silver']:
 h=solid(read(P/hair/'png/hair.front.png'));missing=scalp&~h;assert not missing.any(),(hair,'exposed scalp cap',np.argwhere(missing).tolist())
 for face in ['face-blue','face-amber']:
  eyes=solid(read(P/face/'png/face.eyes.png'));assert not (eyes&h).any(),(hair,face,'source eye clipped by fringe')
  assert (eyes&~head).sum()==0,(face,'eyes outside common face')
comp=compose.Compositor(R,T/'catalog.json',T/'motion.json');records=[];baseOnly=0;visibilities=[]
for i,f in enumerate(motion['frames']):
 original=read(B/'frames'/f'{i:02}.png');bare=comp.render(base['id'],[],'down-left',f['clip'],f['frame']);assert np.array_equal(np.array(bare),original),(i,'bare body changed');baseOnly+=1
 for hair,face in itertools.product(['hair-chestnut','hair-silver'],['face-blue','face-amber']):
  selected=[cfg['packages'][hair]['id'],cfg['packages'][face]['id']];a=np.array(comp.render(base['id'],selected,'down-left',f['clip'],f['frame']));path=D/'combinations'/(hair+'__'+face)/f'{i:02}.png';assert np.array_equal(a,read(path)),(i,hair,face,'actual compositor mismatch')
  actual=comp.layers(base['id'],selected,'down-left',f['clip'],f['frame']);layers=dict(actual);mask=np.zeros((256,256),bool)
  for slot,im in actual:
   if slot in base['slots']:assert np.array_equal(np.array(im),read(B/'layers'/f'{i:02}'/(slot+'.png'))),(i,slot,'neutral layer changed')
   else:
    expected=compose.place(Image.open(P/(hair if slot=='hair.front' else face)/'png'/(slot+'.png')),f['headToCanvas'],(256,256));assert np.array_equal(np.array(im),np.array(expected)),(i,slot,'head attachment mismatch');mask|=solid(np.array(im))
  assert np.array_equal(a[~mask],original[~mask]),(i,hair,face,'non-head pixels changed')
  visibility={}
  for slot in ['face.eyes','face.nose','face.mouth']:
   part=np.array(layers[slot]);m=solid(part);assert m.any(),(i,hair,face,slot,'feature disappeared');assert np.array_equal(a[m],part[m]),(i,hair,face,slot,'feature occluded');visibility[slot]=int(m.sum())
  assert visibility['face.mouth']>=2,(i,hair,face,'mouth degenerates to a speck')
  records.append({'pose':i,'hair':hair,'face':face,'actualCompositorDifferencePixels':0,'originalBodyLayerDifferences':0,'pixelsChangedOutsideHeadResourceFootprint':0,'fullyVisibleFeaturePixels':visibility});visibilities.append(visibility)
for hair,face in itertools.product(['hair-chestnut','hair-silver'],['face-blue','face-amber']):
 for name,durations in [('walk-120ms.gif',[120]*8),('start-stop-120ms.gif',[480]+[120]*20+[480])]:
  with Image.open(D/'combinations'/(hair+'__'+face)/name) as g:assert g.n_frames==len(durations) and [im.info['duration'] for im in ImageSequence.Iterator(g)]==durations and g.info['loop']==0
for name,durations in [('walk-comparison-120ms.gif',[120]*8),('start-stop-comparison-120ms.gif',[480]+[120]*20+[480])]:
 with Image.open(D/name) as g:assert g.n_frames==len(durations) and [im.info['duration'] for im in ImageSequence.Iterator(g)]==durations and g.info['loop']==0
preserved=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/p)==h for p,h in preserved.items()),'old source/art changed'
result={'status':'independent-head-resource-checks-pass','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'assetManifests':4,'independentCombinations':4,'actualCompositorPoses':len(records),'bareBodyPosesUnchanged':baseOnly,'originalBodyLayerComparisons':len(records)*8,'eyeNoseMouthVisibilityChecks':len(records)*3,'originalMotionGeometryUnchanged':True,'profileChange':'Only a new down-left head-layout data entry; existing entries unchanged','crownAndRearScalpGaps':0,'preservedFiles':len(preserved),'normalWalkDurationsMs':[120]*8,'poses':records,'limits':['Main full-body artwork review separate; no user approval inferred','Still viewer; no continuous playback review claimed','Down-left head resources only, no new clothes/weapon, other-direction art, hidden anatomy, App or IPA']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['assetManifests','independentCombinations','actualCompositorPoses','bareBodyPosesUnchanged','eyeNoseMouthVisibilityChecks','preservedFiles']}))
