#!/usr/bin/env python3
"""Verify public assembly, anatomy/cloth ownership, shared seams and foot/head bindings. Not a visual-approval tool."""
from pathlib import Path
import hashlib,importlib.util,json,math
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label,binary_dilation,binary_fill_holes
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/up/walk-r1-layered';D=R/'Art/Review/P1/neutral-up-layered-r1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=mod('compose',R/'scripts/compose-character-parts.py')
read=lambda p:np.array(Image.open(p).convert('RGBA'))
solid=lambda a:a[:,:,3]>128
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
components=lambda m:label(m,np.ones((3,3)))[1]
def white(a):
 r,g,b,al=[a[:,:,i].astype(float) for i in range(4)];return int(((abs(r-b)<25)&(abs(g-b)<25)&(b>120)&(al>128)).sum())
def main():
 cfg=json.loads((P/'authoring.json').read_text());asset=json.loads((P/'asset.json').read_text());motion=json.loads((P/'motion.json').read_text());audit=json.loads((D/'rig-audit.json').read_text());assert not compose.contract.check_asset(P/'asset.json');assert asset['directions']==['up'] and cfg['facing']==[0,-1];assert len(asset['bindings'])==len(motion['frames'])==13;assert {f['clip'] for f in motion['frames']}=={'idle','walk','walk-start','walk-stop'};comp=compose.Compositor(R,D/'catalog.json',P/'motion.json');origin=cfg['headLocalOrigin'];localhead=Image.open(P/cfg['headSource']['image']).crop((origin[0],origin[1],origin[0]+96,origin[1]+96));(D/'actual-composition').mkdir(exist_ok=True);records=[];pantHashes=[];handChecks=headChecks=jointChecks=0;source={n:read(P/v['image']) for n,v in cfg['parts'].items()}
 for n,a in source.items():
  if n=='junction-reference':continue
  assert components(solid(a))==1,('source fragment',n)
  if n.startswith(('arm.','hand.','leg.')):assert white(a)==0,('cloth on skin source',n,white(a))
 for state,sides in cfg['footRollStates'].items():
  for side,v in sides.items():
   assert sha(P/v['image'])==v['sha256'];a=read(P/v['image']);b=source['leg.'+side];assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:208],b[:208]),(state,side,'foot paint changes calf/other anatomy')
 for i,f in enumerate(motion['frames']):
  im=comp.render(asset['id'],[],'up',f['clip'],f['frame']);a=np.array(im);assert np.array_equal(a,read(P/'frames'/f'{i:02}.png')),(i,'actual compositor differs');im.save(D/'actual-composition'/f'{i:02}.png');assert components(solid(a))==1,(i,'whole-body disconnect')
  if i==0:assert np.array_equal(a,read(P/'source/registered-idle.png')),(i,'idle source differs')
  layers={p.stem:read(p) for p in (P/'layers'/f'{i:02}').glob('*.png')};torso=solid(layers['body.torso']);head=np.array(compose.place(localhead,f['headToCanvas'],(256,256)));assert np.array_equal(head,layers['head.base']),(i,'head-local future attachment differs');headChecks+=1
  ref=solid(read(P/'components'/f'{i:02}'/'junction-reference.png'));zones=solid(read(P/'components'/f'{i:02}'/'junction-zones.png'));missing=ref&zones&~solid(a);assert not missing.any(),(i,'shared-junction hole',np.argwhere(missing).tolist())
  pantHashes.append(sha(P/'components'/f'{i:02}'/'pants.png'));row={'pose':i,'clip':f['clip'],'frame':f['frame'],'actualCompositorDifferencePixels':0,'junctionHoles':0,'sides':{}}
  for slot,layer in layers.items():
   m=solid(layer);assert components(m)==1,(i,slot,'layer orphan');assert not ((binary_fill_holes(m)&~m)&~solid(a)).any(),(i,slot,'visible enclosed gap')
  for side in ['left','right']:
   arm,hand,leg=[layers[n+'.'+side] for n in ['body.arm','body.hand','body.leg']];am,hm,lm=map(solid,[arm,hand,leg]);assert white(arm)==white(hand)==white(leg)==0,(i,side,'skin layer has cloth')
   assert (binary_dilation(am,np.ones((3,3)))&hm).any(),(i,side,'wrist gap');assert (binary_dilation(am,np.ones((3,3)))&torso).any(),(i,side,'shoulder gap');assert (binary_dilation(lm,np.ones((3,3)))&torso).any(),(i,side,'hip gap')
   whole=Image.fromarray(arm);whole.alpha_composite(Image.fromarray(hand));assert np.array_equal(np.array(whole),read(P/'components'/f'{i:02}'/('complete-arm.'+side+'.png'))),(i,side,'hand/arm mesh mismatch');visible=int((hm&np.all(a==hand,axis=2)).sum());assert visible>=int(hm.sum())*.8,(i,side,'hand unexpectedly hidden',visible,int(hm.sum()));handChecks+=1
   H,K,A=[np.array(f['joints'][n+side.title()]) for n in ['hip','knee','ankle']];u=(K-H)/np.linalg.norm(K-H);v=(A-K)/np.linalg.norm(A-K);bend=math.degrees(math.acos(float(np.clip(u@v,-1,1))));assert bend<15,(i,side,'back-view knee twists out',bend)
   for point in [K,A]:
    x,y=np.rint(point).astype(int);assert lm[y-1:y+2,x-1:x+2].sum()>=3,(i,side,'joint has no material');jointChecks+=1
   contact=audit['poses'][i]['contacts'][side];x,y=np.rint(contact['point']).astype(int);assert lm[y-1:y+2,x-1:x+2].any(),(i,side,'sole outside foot')
   if not contact['airborne']:assert abs(contact['point'][1]-contact['groundY'])<1e-6,(i,side,'contact anchor leaves floor')
   row['sides'][side]={'visibleHandPixels':visible,'handPixels':int(hm.sum()),'legArea':int(lm.sum()),'projectedKneeBendDegrees':bend,'footArtState':contact['footArtState'],'supportAnchorError':None if contact['airborne'] else abs(contact['point'][1]-contact['groundY'])}
  records.append(row)
 assert len(set(pantHashes[1:9]))>=6,'shorts freeze while legs move'
 for name,durations in [('walk-120ms.gif',[120]*8),('start-stop-120ms.gif',[480]+[120]*20+[480])]:
  with Image.open(D/name) as g:assert g.n_frames==len(durations) and [im.info['duration'] for im in ImageSequence.Iterator(g)]==durations and g.info['loop']==0
 old=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/k)==h for k,h in old.items()),'old artwork/source changed'
 result={'status':'technical-checks-pass','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'actualCompositorPoses':13,'semanticLayersWithoutOrphans':104,'newJunctionAlphaHoles':0,'completeArmPartitionChecks':handChecks,'headLocalPlacementChecks':headChecks,'kneeAnkleMaterialChecks':jointChecks,'independentPantsWalkFrames':len(set(pantHashes[1:9])),'sourceIdleRGBARecompositionDifferencePixels':0,'footRollSourceVariants':2,'footVariantAlphaDifferencePixels':0,'preservedFiles':len(old),'poses':records,'limits':['New neutral source and motion adaptation reference old approved back camera/phase; they are not identical old clothed pixels or inherited user approval','Main reviews complete1x/2x images separately; technical pass is not artwork approval','Still viewer: complete frame/timing check only, no continuous playback claim','Specified idle->walk01/walk08->idle only; no arbitrary interruption, new appearances, App/device or IPA acceptance']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['poses','limits']}))
if __name__=='__main__':main()
