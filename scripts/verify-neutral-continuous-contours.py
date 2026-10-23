#!/usr/bin/env python3
"""Recompose upper diagonal r4 and check explicit limb/material boundaries.
These are technical checks, not automatic artwork approval.
"""
from pathlib import Path
import hashlib,importlib.util,json,math
from PIL import Image,ImageDraw,ImageSequence
import numpy as np
from scipy.ndimage import label,binary_dilation
R=Path(__file__).resolve().parents[1];review=R/'Art/Review/P1/neutral-upper-diagonals-r4';review.mkdir(exist_ok=True)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pixels(p):return np.array(Image.open(p).convert('RGBA'))
def components(a):return label(a,np.ones((3,3)))[1]
def white_count(a):
 r,g,b,alpha=[a[:,:,k].astype(float) for k in range(4)];return int(((r<b*1.15)&(g<b*1.15)&(b>70)&(alpha>128)).sum())
compose=load('compose',R/'scripts/compose-character-parts.py');preview=load('preview',R/'scripts/export-neutral-direction.py');dirs=['up-left','up-right'];catalog={'assets':[{'id':'p1-neutral-'+d+'-walk-r4-continuous-contours','manifest':f'Art/Templates/P1-Neutral/{d}/walk-r4-continuous-contours/asset.json'} for d in dirs]};(review/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n');records=[];images={}
for d in dirs:
 p=R/f'Art/Templates/P1-Neutral/{d}/walk-r4-continuous-contours';cfg=json.loads((p/'authoring.json').read_text());motion=json.loads((p/'motion.json').read_text());audit=json.loads((review/d/'rig-audit.json').read_text());asset=json.loads((p/'asset.json').read_text());errors=compose.contract.check_asset(p/'asset.json');assert not errors,errors;comp=compose.Compositor(R,review/'catalog.json',p/'motion.json');frames=[];checks=[];area={side:[] for side in ['left','right']};bonehistory={};out=review/d/'actual-composition';out.mkdir(exist_ok=True)
 for name,part in cfg['parts'].items():
  a=pixels(p/part['image']);assert sha(p/part['image'])==part['sha256']
  if name.startswith(('arm.','hand.')):assert white_count(a)==0,(d,name,'fabric on limb source')
 assert sha(p/cfg['headSource']['image'])==cfg['headSource']['sha256']
 for i,f in enumerate(motion['frames']):
  im=comp.render(asset['id'],[],d,f['clip'],f['frame']);whole=np.array(im);assert np.array_equal(whole,pixels(p/'frames'/f'{i:02}.png')),(d,i,'compositor mismatch');assert components(whole[:,:,3]>128)==1,(d,i,'whole disconnected');im.save(out/f'{i:02}.png');frames.append(im);row={'frame':i,'actualCompositorDifferencePixels':0,'sides':{}}
  torso=pixels(p/f'layers/{i:02}/body.torso.png')[:,:,3]>128
  for fp in (p/'layers'/f'{i:02}').glob('*.png'):assert components(pixels(fp)[:,:,3]>128)==1,(d,i,fp.name,'orphan contour')
  for side in ['left','right']:
   arma=pixels(p/f'layers/{i:02}/body.arm.{side}.png');handa=pixels(p/f'layers/{i:02}/body.hand.{side}.png');arm=arma[:,:,3]>128;hand=handa[:,:,3]>128;leg=pixels(p/f'layers/{i:02}/body.leg.{side}.png')[:,:,3]>128
   assert white_count(arma)==white_count(handa)==0,(d,i,side,'fabric on arm or hand')
   wristcontact=int((binary_dilation(arm,np.ones((3,3)))&hand).sum());assert wristcontact>0,(d,i,side,'wrist disconnected')
   assert int((binary_dilation(arm,np.ones((3,3)))&torso).sum())>0,(d,i,side,'shoulder disconnected')
   assert int((leg&torso).sum())>0,(d,i,side,'hip has no underlap')
   H,K,A=[np.array(f['joints'][stem+side.title()]) for stem in ['hip','knee','ankle']];axis=(K-H)/np.linalg.norm(K-H);normal=np.array([-axis[1],axis[0]]);samples=[]
   # A solid 3px-wide corridor through the hip seam, rather than any pixel in a large radius.
   for t in np.linspace(0,.8,21):
    for offset in [-1,0,1]:
     x,y=np.rint(H+(K-H)*t+normal*offset).astype(int);assert whole[y,x,3]>128,(d,i,side,'hip corridor hole',(int(x),int(y)));samples.append([int(x),int(y)])
   for stem,pos in [('knee',K),('ankle',A)]:
    x,y=np.rint(pos).astype(int);assert leg[y-1:y+2,x-1:x+2].sum()>=4,(d,i,side,stem,'joint lacks material')
   u=(K-H)/np.linalg.norm(K-H);v=(A-K)/np.linalg.norm(A-K);bend=math.degrees(math.acos(float(np.clip(u@v,-1,1))));assert bend<55,(d,i,side,'excessive projected knee bend',bend)
   contact=audit['poses'][i]['contacts'][side];x,y=np.rint(contact['point']).astype(int);near=int(leg[y-1:y+2,x-1:x+2].sum());assert near>0,(d,i,side,'sole lacks material')
   if not contact['airborne']:assert abs(contact['point'][1]-contact['groundY'])<1e-6,(d,i,side,'stance foot off floor')
   area[side].append(int(leg.sum()));row['sides'][side]={'wristContactPixels':wristcontact,'legConnectedComponents':1,'armOrHandFabricPixels':0,'hipCorridorSamples':samples,'projectedKneeBendDegrees':bend,'handAreaPixels':int(hand.sum()),'legAreaPixels':int(leg.sum()),'soleNeighborhoodPixels':near,'hipUnderlapPixels':int((leg&torso).sum())}
  if i:
   for name,length in audit['poses'][i]['sagittalLengths'].items():bonehistory.setdefault(name,[]).append(length)
  checks.append(row)
 for name,values in bonehistory.items():assert max(values)-min(values)<1e-9,(d,name,'bone length changed')
 areas={}
 for side,vals in area.items():
  walk=vals[1:];deltas=[abs(walk[(i+1)%8]-walk[i])/walk[i] for i in range(8)];assert max(deltas)<.15,(d,side,'large silhouette area change',deltas);areas[side]={'walkAreaPixels':walk,'maximumAdjacentRelativeChange':max(deltas),'wrapRelativeChange':deltas[-1]}
 images[d]=frames;records.append({'direction':d,'assetErrors':0,'sourceHashChecks':len(cfg['parts'])+1,'boneLengths':{k:v[0] for k,v in bonehistory.items()},'silhouetteArea':areas,'poses':checks})
pairs=[]
for i in range(9):
 im=Image.new('RGBA',(512,256));im.alpha_composite(images['up-left'][i]);im.alpha_composite(images['up-right'][i],(256,0));pairs.append(im)
preview.gif(pairs[1:],review/'walk-comparison-120ms.gif');preview.flatten(pairs[0],2).save(review/'idle-comparison-2x.png');preview.flatten(pairs[0]).save(review/'idle-comparison-1x.png')
board=Image.new('RGB',(1536,768),'#17372c')
for z,d in enumerate(dirs):
 for i,im in enumerate(images[d]):x=z*768+i%3*256;y=i//3*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),d+' '+str(i),fill='white')
board.save(review/'both-directions-nine-poses-1x.png');board.resize((3072,1536),Image.Resampling.NEAREST).save(review/'both-directions-nine-poses-2x.png')
for name in ['walk-comparison-120ms.gif','up-left/walk-120ms.gif','up-right/walk-120ms.gif']:
 with Image.open(review/name) as g:assert g.n_frames==8 and [f.info['duration'] for f in ImageSequence.Iterator(g)]==[120]*8 and g.info['loop']==0
res={'status':'technical-composition-and-boundary-checks-pass-not-art-approval','artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'actualCompositorPoses':18,'individualLayersWithoutOrphans':144,'sameSideWristContacts':36,'sameSideLegConnectivity':36,'armsAndHandsWithoutFabric':72,'solidHipCorridors':36,'hipCorridorWidthPixels':3,'hipCorridorSamplesPerSide':63,'normalFrameDurationsMs':[120]*8,'directions':records,'limits':['Technical checks do not establish natural walking or user artwork acceptance','Current image viewer exposes GIF still only: no continuous-player playback claimed','No start/stop, wardrobe combinations, runtime/device testing or IPA']};(review/'validation.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps({k:res[k] for k in ['actualCompositorPoses','sameSideWristContacts','sameSideLegConnectivity','armsAndHandsWithoutFabric','solidHipCorridors']}))
