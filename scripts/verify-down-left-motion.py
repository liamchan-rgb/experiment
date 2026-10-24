#!/usr/bin/env python3
"""Check actual neutral assembly, anatomical seams, foot contacts and GIF timing.
These are technical checks; main full-body art review is recorded separately.
"""
from pathlib import Path
import hashlib,importlib.util,json,math
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label,binary_dilation,binary_fill_holes
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/down-left/walk-r1';D=R/'Art/Review/P1/neutral-down-left-r1'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=module('compose',R/'scripts/compose-character-parts.py')
def read(p):return np.array(Image.open(p).convert('RGBA'))
def solid(a):return a[:,:,3]>128
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def connected(m):return label(m,np.ones((3,3)))[1]
def white(a):
 r,g,b,al=[a[:,:,i].astype(float) for i in range(4)];return int(((r<b*1.15)&(g<b*1.15)&(b>70)&(al>128)).sum())
cfg=json.loads((P/'authoring.json').read_text());asset=json.loads((P/'asset.json').read_text());motion=json.loads((P/'motion.json').read_text());audit=json.loads((D/'rig-audit.json').read_text())
assert not compose.contract.check_asset(P/'asset.json')
assert asset['directions']==['down-left'];assert cfg['facing']==[-1,1] and cfg['nearSide']=='left' and cfg['farSide']=='right'
assert len(asset['bindings'])==len(motion['frames'])==13
assert len({(f['clip'],f['frame']) for f in motion['frames']})==13
(D/'catalog.json').write_text(json.dumps({'assets':[{'id':asset['id'],'manifest':str((P/'asset.json').relative_to(R))}]},indent=2)+'\n')
comp=compose.Compositor(R,D/'catalog.json',P/'motion.json');(D/'actual-composition').mkdir(exist_ok=True)
for name,part in cfg['parts'].items():
 assert sha(P/part['image'])==part['sha256'],name
 if name=='junction-reference':continue
 a=read(P/part['image']);assert connected(solid(a))==1,('source orphan',name)
 if name.startswith(('arm.','hand.')):assert white(a)==0,('source fabric',name,white(a))
assert sha(P/cfg['headSource']['image'])==cfg['headSource']['sha256']
records=[];pantsHashes=[];legAreas={s:[] for s in ['left','right']}
for i,f in enumerate(motion['frames']):
 image=comp.render(asset['id'],[],'down-left',f['clip'],f['frame']);a=np.array(image);assert np.array_equal(a,read(P/'frames'/f'{i:02}.png')),(i,'public assembly differs');image.save(D/'actual-composition'/f'{i:02}.png');assert connected(solid(a))==1,(i,'whole body disconnected')
 if i==0:assert np.array_equal(a,read(P/'source/registered-idle.png')),('idle changed original authored source',int(np.any(a!=read(P/'source/registered-idle.png'),axis=2).sum()))
 torso=solid(read(P/'layers'/f'{i:02}'/'body.torso.png'));ref=solid(read(P/'components'/f'{i:02}'/'junction-reference.png'));zones=solid(read(P/'components'/f'{i:02}'/'junction-zones.png'));miss=ref&zones&~solid(a);assert not miss.any(),(i,'junction holes',np.argwhere(miss).tolist())
 pantsHashes.append(sha(P/'components'/f'{i:02}'/'pants.png'));row={'pose':i,'clip':f['clip'],'frame':f['frame'],'actualCompositorDifferencePixels':0,'junctionAlphaHoles':0,'sides':{}}
 for slot in asset['slots']:
  layer=solid(read(P/'layers'/f'{i:02}'/(slot+'.png')));assert connected(layer)==1,(i,slot,'orphan');assert not ((binary_fill_holes(layer)&~layer)&~solid(a)).any(),(i,slot,'visible enclosed alpha hole')
 for side in ['left','right']:
  ar=read(P/'layers'/f'{i:02}'/f'body.arm.{side}.png');ha=read(P/'layers'/f'{i:02}'/f'body.hand.{side}.png');le=read(P/'layers'/f'{i:02}'/f'body.leg.{side}.png');am,hm,lm=solid(ar),solid(ha),solid(le)
  assert white(ar)==white(ha)==0,(i,side,'fabric on arm')
  assert (binary_dilation(am,np.ones((3,3)))&hm).sum()>0,(i,side,'wrist gap')
  assert (binary_dilation(am,np.ones((3,3)))&torso).sum()>0,(i,side,'shoulder gap')
  assert (binary_dilation(lm,np.ones((3,3)))&torso).sum()>0,(i,side,'hip gap')
  union=Image.fromarray(ar);union.alpha_composite(Image.fromarray(ha));assert np.array_equal(np.array(union),read(P/'components'/f'{i:02}'/f'complete-arm.{side}.png')),(i,side,'arm hand shared mesh differs')
  handVisible=int((hm&np.all(a==ha,axis=2)).sum());assert handVisible>=30,(i,side,'hand obscured',handVisible)
  if side==cfg['nearSide']:assert handVisible==int(hm.sum()),(i,'near hand clipped')
  H,K,A=[np.array(f['joints'][k+side.title()]) for k in ['hip','knee','ankle']];u=(K-H)/np.linalg.norm(K-H);v=(A-K)/np.linalg.norm(A-K);bend=math.degrees(math.acos(float(np.clip(u@v,-1,1))));assert bend<55,(i,side,'knee twist',bend)
  for point in [K,A]:
   x,y=np.rint(point).astype(int);assert lm[y-1:y+2,x-1:x+2].sum()>=4,(i,side,'joint has no material')
  contact=audit['poses'][i]['contacts'][side];x,y=np.rint(contact['point']).astype(int);assert lm[y-1:y+2,x-1:x+2].sum()>0,(i,side,'sole outside foot')
  if not contact['airborne']:assert abs(contact['point'][1]-contact['groundY'])<1e-6,(i,side,'support foot off plane')
  legAreas[side].append(int(lm.sum()));row['sides'][side]={'handPixels':int(hm.sum()),'visibleHandPixels':handVisible,'legAreaPixels':int(lm.sum()),'projectedKneeBendDegrees':bend,'supportAnchorError':None if contact['airborne'] else abs(contact['point'][1]-contact['groundY'])}
 records.append(row)
assert len(set(pantsHashes[1:9]))==8,'pants are not moving'
for side in legAreas:
 vals=legAreas[side][1:9];changes=[abs(vals[(i+1)%8]-v)/v for i,v in enumerate(vals)];assert max(changes)<.15,(side,'silhouette flicker',changes)
for name,durations in [('walk-120ms.gif',[120]*8),('start-stop-120ms.gif',[480]+[120]*20+[480])]:
 with Image.open(D/name) as g:assert g.n_frames==len(durations) and [f.info['duration'] for f in ImageSequence.Iterator(g)]==durations and g.info['loop']==0,name
preserved=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/p)==h for p,h in preserved.items()),'old assets modified'
result={'status':'technical-checks-pass','artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'actualCompositorPoses':13,'semanticLayersWithoutOrphans':104,'newJunctionAlphaHoles':0,'completeArmPartitionChecks':26,'nearHandsPreservedWithoutClothesClipping':13,'independentPantsWalkFrames':8,'sourceIdleRGBARecompositionDifferencePixels':0,'preservedFiles':len(preserved),'normalWalkFrameDurationsMs':[120]*8,'poses':records,'limits':['Main reviews 1x/2x whole-body frames separately; numerical checks are not art approval','Still-only viewer; no claim of continuous playback review','Specified start/stop paths only; no arbitrary phase interruption, wardrobe, App, device or IPA verification']}
(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['actualCompositorPoses','newJunctionAlphaHoles','completeArmPartitionChecks','preservedFiles']}))
