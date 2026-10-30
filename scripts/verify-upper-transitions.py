#!/usr/bin/env python3
"""Check actual modular assembly, transition joins and preserved approved art."""
from pathlib import Path
import hashlib,importlib.util,json,math
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label,binary_dilation,binary_fill_holes
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/P1/neutral-upper-transitions-r6'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=module('compose',R/'scripts/compose-character-parts.py');mirror=module('mirror',R/'scripts/export-neutral-mirrored-pose-map.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return np.array(Image.open(p).convert('RGBA'))
def mask(a):return a[:,:,3]>128
def white(a):
 r,g,b,al=[a[:,:,i].astype(float) for i in range(4)];return int(((r<b*1.15)&(g<b*1.15)&(b>70)&(al>128)).sum())
def connected(m):return label(m,np.ones((3,3)))[1]
def main():
 records={};assets={};motions={};folders={};results={}
 for direction,oldname in [('up-left','walk-r5-coupled-clothing'),('up-right','walk-r5-mirrored-up-left')]:
  P=R/f'Art/Templates/P1-Neutral/{direction}/walk-r6-transitions';old=P.parent/oldname;out=D/direction;folders[direction]=P
  a=json.loads((P/'asset.json').read_text());m=json.loads((P/'motion.json').read_text());assets[direction]=a;motions[direction]=m;assert len(a['bindings'])==len(m['frames'])==13
  assert not compose.contract.check_asset(P/'asset.json')
  assert {(f['clip'],f['frame']) for f in m['frames']}=={('idle',0),*[("walk",i) for i in range(1,9)],*[(c,i) for c in ['walk-start','walk-stop'] for i in [1,2]]}
  (out/'catalog.json').write_text(json.dumps({'assets':[{'id':a['id'],'manifest':str((P/'asset.json').relative_to(R))}]},indent=2)+'\n');comp=compose.Compositor(R,out/'catalog.json',P/'motion.json');(out/'actual-composition').mkdir(exist_ok=True)
  rows=[];near='left' if direction=='up-left' else 'right'
  for idx,f in enumerate(m['frames']):
   im=comp.render(a['id'],[],direction,f['clip'],f['frame']);full=np.array(im);assert np.array_equal(full,read(P/'frames'/f'{idx:02}.png')),(direction,idx,'public assembly differs');im.save(out/'actual-composition'/f'{idx:02}.png');assert connected(mask(full))==1,(direction,idx,'disconnected body')
   if idx<9:
    assert sha(P/'frames'/f'{idx:02}.png')==sha(old/'frames'/f'{idx:02}.png'),(direction,idx,'approved frame changed')
    for slot in a['slots']:assert sha(P/'layers'/f'{idx:02}'/(slot+'.png'))==sha(old/'layers'/f'{idx:02}'/(slot+'.png')),(direction,idx,slot,'approved layer changed')
   layers={slot:read(P/path) for slot,path in a['bindings'][idx]['layers'].items()}
   for slot,layer in layers.items():
    assert connected(mask(layer))==1,(direction,idx,slot,'orphan contour')
    assert not ((binary_fill_holes(mask(layer))&~mask(layer))&~mask(full)).any(),(direction,idx,slot,'visible enclosed hole')
   reference=read(P/'components'/f'{idx:02}'/'junction-reference.png');zone=mask(read(P/'components'/f'{idx:02}'/'junction-zones.png'));missing=mask(reference)&zone&~mask(full);assert not missing.any(),(direction,idx,'visible shoulder/hip hole',np.argwhere(missing).tolist())
   torso=mask(layers['body.torso']);shirt=mask(read(P/'components'/f'{idx:02}'/'shirt.png'));pants=mask(read(P/'components'/f'{idx:02}'/'pants.png'));assert (shirt&pants).sum()>20,(direction,idx,'waist detached')
   sides={}
   for side in ['left','right']:
    arm,hand,leg=[layers[f'body.{part}.{side}'] for part in ['arm','hand','leg']];assert white(arm)==white(hand)==0,(direction,idx,side,'cloth fringe on skin');am,hm,lm=map(mask,[arm,hand,leg]);assert (binary_dilation(am,np.ones((3,3)))&hm).sum()>0,(direction,idx,side,'wrist detached');assert (binary_dilation(am,np.ones((3,3)))&torso).sum()>0,(direction,idx,side,'shoulder detached');assert (lm&torso).sum()>0,(direction,idx,side,'hip detached')
    union=Image.fromarray(arm);union.alpha_composite(Image.fromarray(hand));assert np.array_equal(np.array(union),read(P/'components'/f'{idx:02}'/f'complete-arm.{side}.png')),(direction,idx,side,'hand partition seam')
    visible=int((hm&np.all(full==hand,axis=2)).sum());assert visible>10,(direction,idx,side,'hand hidden')
    if side==near:assert visible==int(hm.sum()),(direction,idx,side,'near hand clipped')
    H,K,A=[np.array(f['joints'][k+side.title()]) for k in ['hip','knee','ankle']];u=(K-H)/np.linalg.norm(K-H);v=(A-K)/np.linalg.norm(A-K);angle=math.degrees(math.acos(float(np.clip(u@v,-1,1))));assert angle<55,(direction,idx,side,'twisted knee',angle)
    x,y=f['soleMarkers'][side];assert lm[y-1:y+2,x-1:x+2].any(),(direction,idx,side,'sole off foot')
    for point in [K,A]:
     x,y=np.rint(point).astype(int);assert lm[y-1:y+2,x-1:x+2].sum()>=4,(direction,idx,side,'joint uncovered')
    sides[side]={'legPixels':int(lm.sum()),'projectedKneeBendDeg':angle,'visibleHandPixels':visible}
   rows.append({'index':idx,'clip':f['clip'],'frame':f['frame'],'junctionMissingPixels':0,'sides':sides})
  # A transition step must be smaller than the corresponding direct idle/walk snap.
  continuity={}
  for name,seq in [('start',[0,9,10,1]),('stop',[8,11,12,0])]:
   steps=[]
   for aa,bb in zip(seq,seq[1:]):
    joints={k:float(np.linalg.norm(np.array(m['frames'][aa]['joints'][k])-np.array(m['frames'][bb]['joints'][k]))) for k in m['frames'][aa]['joints']}
    steps.append({'from':aa,'to':bb,'maximumJointDistance':max(joints.values()),'joints':joints})
   direct=max(float(np.linalg.norm(np.array(m['frames'][seq[0]]['joints'][k])-np.array(m['frames'][seq[-1]]['joints'][k]))) for k in m['frames'][0]['joints'])
   assert max(v['maximumJointDistance'] for v in steps)<direct,(direction,name,'transition exceeds original snap')
   for side in ['left','right']:
    for aa,bb in zip(seq,seq[1:]):assert abs(rows[aa]['sides'][side]['legPixels']-rows[bb]['sides'][side]['legPixels'])/rows[aa]['sides'][side]['legPixels']<.15,(direction,aa,bb,side,'limb area jump')
   continuity[name]={'directEndpointJointDistance':direct,'steps':steps}
  records[direction]=rows;results[direction]={'poses':13,'approvedFramePNGsUnchanged':9,'approvedSemanticLayersUnchanged':72,'junctionHoles':0,'continuity':continuity}
 # Confirm no reintroduction of mirrored lighting/side/attachment errors in new frames.
 L=folders['up-left'];P=folders['up-right'];cfg=json.loads((P/'mirror-authoring.json').read_text())
 for idx,(left,right) in enumerate(zip(motions['up-left']['frames'],motions['up-right']['frames'])):
  assert right['support']==mirror.side(left['support']) and right['drawOrder']==[mirror.side(s) for s in left['drawOrder']]
  for key,point in left['joints'].items():assert np.allclose(right['joints'][mirror.side(key)],[255-point[0],point[1]])
  for slot,path in assets['up-left']['bindings'][idx]['layers'].items():assert np.array_equal(read(L/path)[:,::-1,3],read(P/'layers'/f'{idx:02}'/(mirror.side(slot)+'.png'))[:,:,3])
  head=compose.place(Image.open(P/cfg['headLocalTexture']).convert('RGBA'),right['headToCanvas'],(256,256));assert np.array_equal(np.array(head),read(P/'layers'/f'{idx:02}'/'head.base.png')),(idx,'head attachment mismatch')
  h=np.array(head);ys,xs=np.where(mask(h));by,bx=np.where((h[:,:,0]>240)&(h[:,:,1]>185)&(h[:,:,2]>110)&mask(h));assert bx.mean()<(xs.min()+xs.max())/2-1 and by.mean()<(ys.min()+ys.max())/2,(idx,'head light reversed')
 audit=json.loads((D/'up-left/rig-audit.json').read_text())
 for idx in range(9,13):
  f=motions['up-left']['frames'][idx];contacts=audit['poses'][idx]['contacts'];assert any(not c['airborne'] for c in contacts.values()),(idx,'both feet airborne')
  for side,c in contacts.items():
   if f['support'] in [side,'both']:assert not c['airborne'] and abs(c['groundClearance'])<1e-6,(idx,side,'support foot floats')
   else:assert c['groundClearance']>.2,(idx,side,'swing foot scrapes ground')
 gifChecks=[]
 for out in [D,D/'up-left',D/'up-right']:
  for name,expected in [('walk-120ms.gif',[120]*8),('start-stop-120ms.gif',[480]+[120]*20+[480])]:
   with Image.open(out/name) as g:
    durations=[f.info['duration'] for f in ImageSequence.Iterator(g)];assert durations==expected and g.info['loop']==0,(out,name,durations);gifChecks.append({'file':str((out/name).relative_to(D)),'frames':len(durations),'durationsMs':durations})
 result={'status':'technical-checks-pass','artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'directions':results,'actualCompositorPoses':26,'newTransitionPoses':8,'semanticLayersWithoutOrphans':208,'newJunctionAlphaHoles':0,'headLocalMirrorAttachments':13,'soleGroundingTransitionChecks':4,'gifs':gifChecks,'poses':records,'limits':['Specified idle-to-walk01 and walk08-to-idle paths only','No continuous-player viewing claimed','No full hidden anatomy, wardrobe, runtime, device or IPA acceptance']}
 (D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','actualCompositorPoses','newTransitionPoses','semanticLayersWithoutOrphans','newJunctionAlphaHoles']}))
if __name__=='__main__':main()
