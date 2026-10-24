#!/usr/bin/env python3
"""Render and audit fixed-source upper-diagonal limbs, independently by side."""
from pathlib import Path
import hashlib,importlib.util,json,math
from PIL import Image,ImageDraw,ImageSequence
import numpy as np
from scipy.ndimage import label,binary_dilation
R=Path(__file__).resolve().parents[1];review=R/'Art/Review/P1/neutral-upper-diagonals-r2';review.mkdir(exist_ok=True)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
compose=load('compose',R/'scripts/compose-character-parts.py');preview=load('preview',R/'scripts/export-neutral-direction.py')
dirs=['up-left','up-right'];catalog={'assets':[{'id':'p1-neutral-'+d+'-walk-r2-fixed-limbs','manifest':f'Art/Templates/P1-Neutral/{d}/walk-r2-fixed-limbs/asset.json'} for d in dirs]};(review/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n');records=[];images={}
for d in dirs:
 p=R/f'Art/Templates/P1-Neutral/{d}/walk-r2-fixed-limbs';cfg=json.loads((p/'authoring.json').read_text());motion=json.loads((p/'motion.json').read_text());audit=json.loads((review/d/'rig-audit.json').read_text());asset=json.loads((p/'asset.json').read_text());assert not compose.contract.check_asset(p/'asset.json');comp=compose.Compositor(R,review/'catalog.json',p/'motion.json');frames=[];checks=[];area={side:[] for side in ['left','right']};bonehistory={};out=review/d/'actual-composition';out.mkdir(exist_ok=True)
 for i,f in enumerate(motion['frames']):
  im=comp.render(asset['id'],[],d,f['clip'],f['frame']);assert np.array_equal(np.array(im),np.array(Image.open(p/'frames'/f'{i:02}.png'))),(d,i,'compositor mismatch');im.save(out/f'{i:02}.png');frames.append(im);row={'frame':i,'actualCompositorDifferencePixels':0,'sides':{}}
  torso=np.array(Image.open(p/f'layers/{i:02}/body.torso.png'))[:,:,3]>32
  for side in ['left','right']:
   arm=np.array(Image.open(p/f'layers/{i:02}/body.arm.{side}.png'))[:,:,3]>32;hand=np.array(Image.open(p/f'layers/{i:02}/body.hand.{side}.png'))[:,:,3]>32;leg=np.array(Image.open(p/f'layers/{i:02}/body.leg.{side}.png'))[:,:,3]>10
   contact=int((binary_dilation(arm,np.ones((3,3)))&hand).sum());assert contact>0,(d,i,side,'wrist disconnected')
   labs,n=label(leg,np.ones((3,3)));assert n==1,(d,i,side,'leg disconnected',n)
   joints={}
   for stem,mask in [('shoulder',arm|hand),('hip',leg),('knee',leg),('ankle',leg)]:
    xy=f['joints'][stem+side.title()];x,y=map(round,xy);radius=9 if stem=='hip' else 3;count=int(mask[max(0,y-radius):y+radius+1,max(0,x-radius):x+radius+1].sum());assert count>0,(d,i,side,stem,'not in limb');joints[stem]={'point':xy,'probeRadius':radius,'limbPixels':count,'hipRootOccludedByShorts':stem=='hip'}
   for stem,mask in [('shoulder',arm|hand),('hip',leg)]:
    x,y=map(round,f['joints'][stem+side.title()]);box=np.zeros((256,256),bool);box[y-9:y+10,x-9:x+10]=True;count=int((binary_dilation(mask,np.ones((3,3)))&torso&box).sum());assert count>0,(d,i,side,stem,'not attached to torso');joints[stem]['torsoContactWithin9']=count
   sole=f['soleMarkers'][side];x,y=sole;assert leg[y,x],(d,i,side,'sole not on same leg',sole)
   area[side].append(int(leg.sum()));row['sides'][side]={'wristContactPixels':contact,'legConnectedComponents':1,'legArea':int(leg.sum()),'sole':sole,'joints':joints}
  for b in audit['frames'][i]['bones']:bonehistory.setdefault(b['segment'],[]).append(b['length'])
  checks.append(row)
 for name,lengths in bonehistory.items():assert max(lengths)-min(lengths)<1e-8,(d,name,'bone length changed')
 areas={}
 for side,vals in area.items():
  walk=vals[1:];deltas=[abs(walk[(i+1)%8]-walk[i])/walk[i] for i in range(8)];areas[side]={'walkAreaPixels':walk,'maxAdjacentRelativeAreaChange':max(deltas),'wrapRelativeAreaChange':deltas[-1]};assert max(deltas)<.25,(d,side,'large silhouette area change',deltas)
 for name in ['body.torso','head.base']:assert (p/f'source/{name}.png').read_bytes()==(p.parent/'walk-r1'/f'layers/00/{name}.png').read_bytes()
 with Image.open(review/d/'walk-120ms.gif') as g:assert g.n_frames==8 and [f.info['duration'] for f in ImageSequence.Iterator(g)]==[120]*8
 images[d]=frames;records.append({'direction':d,'assetErrors':0,'fixedSourceLegHashes':{k:v['sha256'] for k,v in cfg['legSkin'].items()},'boneLengths':{k:v[0] for k,v in bonehistory.items()},'silhouetteArea':areas,'poses':checks})
pairs=[]
for i in range(9):
 im=Image.new('RGBA',(512,256));im.alpha_composite(images['up-left'][i]);im.alpha_composite(images['up-right'][i],(256,0));pairs.append(im)
preview.gif(pairs[1:],review/'walk-comparison-120ms.gif');preview.flatten(pairs[0],2).save(review/'idle-comparison-2x.png');preview.flatten(pairs[0]).save(review/'idle-comparison-1x.png')
board=Image.new('RGB',(1536,768),'#17372c')
for z,d in enumerate(dirs):
 for i,im in enumerate(images[d]):x=z*768+i%3*256;y=i//3*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),d+' '+str(i),fill='white')
board.save(review/'both-directions-nine-poses-1x.png');board.resize((3072,1536),Image.Resampling.NEAREST).save(review/'both-directions-nine-poses-2x.png')
res={'status':'technical-limb-and-composition-checks-pass-user-art-review-pending','artApproval':None,'actualCompositorPoses':18,'layers':144,'sameSideWristContacts':36,'sameSideLegConnectivity':36,'shoulderHipAttachments':72,'soleMarkers':36,'constantBoneChains':16,'normalFrameDurationsMs':[120]*8,'directions':records,'limits':['No user art approval','No player playback claimed; current image viewer exposes GIF still only','No start-stop, clothing combinations or runtime/device testing']};(review/'validation.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps({k:res[k] for k in ['actualCompositorPoses','sameSideWristContacts','sameSideLegConnectivity','shoulderHipAttachments','soleMarkers','constantBoneChains']}))
