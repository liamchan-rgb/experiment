#!/usr/bin/env python3
"""Check r5 seams against whole-source junctions and prove shorts are articulated.
These checks supplement main full-body artwork review, not replace it.
"""
from pathlib import Path
import hashlib,importlib.util,json,math
from PIL import Image,ImageSequence
import numpy as np
from scipy.ndimage import label,binary_dilation,binary_fill_holes
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/up-left/walk-r5-coupled-clothing';D=R/'Art/Review/P1/neutral-up-left-r5'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=load('compose',R/'scripts/compose-character-parts.py')
def read(p):return np.array(Image.open(p).convert('RGBA'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def material(a):return a[:,:,3]>128
def white_count(a):
 r,g,b,al=[a[:,:,k].astype(float) for k in range(4)];return int(((r<b*1.15)&(g<b*1.15)&(b>70)&(al>128)).sum())
def connected(mask):return label(mask,np.ones((3,3)))[1]
def apply(m,p):a,b,c,d,x,y=m;return np.array([a*p[0]+c*p[1]+x,b*p[0]+d*p[1]+y])
cfg=json.loads((P/'authoring.json').read_text());asset=json.loads((P/'asset.json').read_text());motion=json.loads((P/'motion.json').read_text());audit=json.loads((D/'rig-audit.json').read_text());assert not compose.contract.check_asset(P/'asset.json')
(D/'catalog.json').write_text(json.dumps({'assets':[{'id':asset['id'],'manifest':str((P/'asset.json').relative_to(R))}]},indent=2)+'\n');comp=compose.Compositor(R,D/'catalog.json',P/'motion.json');(D/'actual-composition').mkdir(exist_ok=True)
for name,part in cfg['parts'].items():
 assert sha(P/part['image'])==part['sha256'],name
 if name.startswith(('arm.','hand.')):assert white_count(read(P/part['image']))==0,(name,'source clothing pixels on arm')
assert sha(P/cfg['headSource']['image'])==cfg['headSource']['sha256']
assert material(read(P/cfg['parts']['pants']['image'])).sum()>100,'pants source is empty'
records=[];pantsHashes=[];legAreas={s:[] for s in ['left','right']};hemDelta={'left':[],'right':[]}
for i,f in enumerate(motion['frames']):
 image=comp.render(asset['id'],[],cfg['direction'],f['clip'],i);a=np.array(image);assert np.array_equal(a,read(P/'frames'/f'{i:02}.png')),(i,'public compositor differs');assert connected(material(a))==1,(i,'whole body disconnected');image.save(D/'actual-composition'/f'{i:02}.png')
 row={'frame':i,'actualCompositorDifferencePixels':0,'sides':{}};torso=read(P/'layers'/f'{i:02}'/'body.torso.png');ref=read(P/'components'/f'{i:02}'/'junction-reference.png');zones=material(read(P/'components'/f'{i:02}'/'junction-zones.png'));required=zones&material(ref);miss=required&~material(a);assert int(miss.sum())==0,(i,'junction alpha holes',np.argwhere(miss).tolist());row['junctionReferenceOpaquePixels']=int(required.sum());row['newJunctionAlphaHoles']=0
 shirt=material(read(P/'components'/f'{i:02}'/'shirt.png'));pants=material(read(P/'components'/f'{i:02}'/'pants.png'));assert (shirt&pants).sum()>20,(i,'waist not overlapped');row['shirtPantsOverlapPixels']=int((shirt&pants).sum());row['pantsPixels']=int(pants.sum());pantsHashes.append(sha(P/'components'/f'{i:02}'/'pants.png'))
 for slot in asset['slots']:
  layer=material(read(P/'layers'/f'{i:02}'/(slot+'.png')));assert connected(layer)==1,(i,slot,'orphan outline');assert not ((binary_fill_holes(layer)&~layer)&~material(a)).any(),(i,slot,'visible enclosed alpha holes')
 for side in ['left','right']:
  arm=read(P/'layers'/f'{i:02}'/f'body.arm.{side}.png');hand=read(P/'layers'/f'{i:02}'/f'body.hand.{side}.png');leg=material(read(P/'layers'/f'{i:02}'/f'body.leg.{side}.png'));am,hm=material(arm),material(hand);assert white_count(arm)==white_count(hand)==0,(i,side,'fabric on arm');contact=int((binary_dilation(am,np.ones((3,3)))&hm).sum());assert contact>0,(i,side,'wrist gap');assert (binary_dilation(am,np.ones((3,3)))&material(torso)).sum()>0,(i,side,'shoulder gap');assert (leg&material(torso)).sum()>0,(i,side,'hip no overlap')
  union=Image.fromarray(arm);union.alpha_composite(Image.fromarray(hand));expected=read(P/'components'/f'{i:02}'/f'complete-arm.{side}.png');assert np.array_equal(np.array(union),expected),(i,side,'arm/hand partition seam')
  visible=int((hm&np.all(a==hand,axis=2)).sum())
  if side=='left':assert visible==int(hm.sum()),(i,'near hand is cropped by clothes')
  else:assert visible>10,(i,'far hand disappeared')
  H,K,A=[np.array(f['joints'][k+side.title()]) for k in ['hip','knee','ankle']];u=(K-H)/np.linalg.norm(K-H);v=(A-K)/np.linalg.norm(A-K);bend=math.degrees(math.acos(float(np.clip(u@v,-1,1))));assert bend<55,(i,side,'excessive knee turn',bend)
  for point in [K,A]:
   x,y=np.rint(point).astype(int);assert leg[y-1:y+2,x-1:x+2].sum()>=4,(i,side,'joint lacks material')
  c=audit['poses'][i]['contacts'][side];x,y=np.rint(c['point']).astype(int);assert leg[y-1:y+2,x-1:x+2].sum()>0,(i,side,'sole outside foot')
  if not c['airborne']:assert abs(c['point'][1]-c['groundY'])<1e-6,(i,side,'stance anchor off ground')
  legAreas[side].append(int(leg.sum()));row['sides'][side]={'wristContactPixels':contact,'armAndHandFabricPixels':0,'completeArmPartitionDifferencePixels':0,'handPixels':int(hm.sum()),'visibleHandPixels':visible,'projectedKneeBendDegrees':bend,'legAreaPixels':int(leg.sum())}
 if i:
  for side,index in [('left',3),('right',4)]:
   landmark=audit['poses'][i]['junctionLandmarks'][index];difference=float(np.linalg.norm(np.array(landmark['destination'])-apply(audit['poses'][i]['partTransforms']['upper'],landmark['source'])));hemDelta[side].append(difference)
 records.append(row)
assert len(set(pantsHashes[1:]))==8,'shorts walk frames not independently articulated'
for side in ['left','right']:
 assert max(hemDelta[side])>1,(side,'hem stays on rigid torso');vals=legAreas[side][1:];changes=[abs(vals[(i+1)%8]-v)/v for i,v in enumerate(vals)];assert max(changes)<.15,(side,'large silhouette jump',changes)
with Image.open(D/'walk-120ms.gif') as g:assert g.n_frames==8 and [im.info['duration'] for im in ImageSequence.Iterator(g)]==[120]*8 and g.info['loop']==0
result={'status':'technical-junction-and-clothing-checks-pass','artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'direction':'up-left','actualCompositorPoses':9,'semanticLayersWithoutOrphans':72,'visibleEnclosedAlphaHoles':0,'wholeSourceJunctionComparisons':9,'newJunctionAlphaHoles':0,'completeArmPartitionChecks':18,'sameSideWristContacts':18,'armsAndHandsWithoutFabric':36,'nearHandsPreservedWithoutClothesClipping':9,'independentPantsWalkFrames':8,'hemDeviationFromRigidTorsoPixels':hemDelta,'normalFrameDurationsMs':[120]*8,'poses':records,'limits':['Main personally reviews whole-body frames; numeric checks are not artwork approval','No continuous-player playback claimed with still-only image viewer','No up-right repair or approval, wardrobe combination, App/device test or IPA']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['actualCompositorPoses','newJunctionAlphaHoles','completeArmPartitionChecks','nearHandsPreservedWithoutClothesClipping','independentPantsWalkFrames']}))
