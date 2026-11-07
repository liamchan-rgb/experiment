#!/usr/bin/env python3
"""Bake one fixed limb kit along continuous joint chains into ordinary pose maps.

Each direction uses one immutable source per anatomical limb for the full cycle.
Sagittal bone lengths stay fixed; their projection changes continuously.
Shoulder/hip anchors and limb source ownership never swap.
This offline exporter adds no runtime or appearance-specific branches.
"""
import argparse,hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=module('compositor',ROOT/'scripts/compose-character-parts.py')
editable=module('editable',ROOT/'scripts/export-wardrobe-part.py')
preview=module('preview',ROOT/'scripts/export-neutral-direction.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ik(a,b,l1,l2,sign):
 a,b=np.array(a,float),np.array(b,float);v=b-a;d=np.linalg.norm(v)
 if not abs(l1-l2)+.01<d<l1+l2-.01:raise ValueError(('unreachable joint',a.tolist(),b.tolist(),l1,l2,d))
 u=v/d;along=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-along*along));p=a+u*along+sign*np.array([-u[1],u[0]])*height
 return p.tolist()
def skin_leg(image,source_chain,target_chain):
    """Continuous row mesh: monotone vertical mapping, fixed transverse girth.

    A row is shared across the entire limb. Monotonicity prevents folded
    triangles or double-painted knee/ankle fragments. Below the ankle the
    original foot is translated intact, keeping its shape through the cycle.
    """
    from scipy.interpolate import PchipInterpolator
    src=np.array(source_chain,float);dst=np.array(target_chain,float)
    if not np.all(np.diff(src[:,1])>0) or not np.all(np.diff(dst[:,1])>0):
        raise ValueError('leg vertical chain must remain monotone')
    curve=PchipInterpolator(src[:,1],dst[:,1]);shift=PchipInterpolator(src[:,1],dst[:,0]-src[:,0])
    samples=np.linspace(src[0,1],src[-1,1],4097);mapped=curve(samples)
    if not np.all(np.diff(mapped)>0):raise ValueError('folded skin mapping')
    rows=np.arange(256,dtype=float);sy=np.interp(rows,mapped,samples)
    below=rows>=dst[-1,1];above=rows<=dst[0,1]
    sy[below]=rows[below]-(dst[-1,1]-src[-1,1]);sy[above]=rows[above]-(dst[0,1]-src[0,1])
    dx=shift(np.clip(sy,src[0,1],src[-1,1]));xx=np.broadcast_to(np.arange(256),(256,256));sx=np.round(xx-dx[:,None]).astype(int);yy=np.broadcast_to(np.round(sy).astype(int)[:,None],(256,256));valid=(sx>=0)&(sx<256)&(yy>=0)&(yy<256)
    raw=np.array(image);out=np.zeros((256,256,4),np.uint8);out[valid]=raw[yy[valid],sx[valid]];out[out[:,:,3]<=10]=0
    return Image.fromarray(out)

def render(folder,review):
 cfg=json.loads((folder/'authoring.json').read_text());direction=cfg['direction'];dsgn=cfg['screenForward'][0]
 for sub in ['layers','frames','editable']:(folder/sub).mkdir(exist_ok=True)
 review.mkdir(parents=True,exist_ok=True)
 for side in ['left','right']:
  r=cfg['legSkin'][side];assert sha(folder/r['image'])==r['sha256']
  for kind in ['arm','hand']:assert sha(folder/cfg['rigidArms'][side][kind])==cfg['rigidArms'][side][kind+'SHA256']
 torso=Image.open(folder/'source/body.torso.png').convert('RGBA');head=Image.open(folder/'source/head.base.png').convert('RGBA')
 frames=[];bindings=[];motion=[];audits=[]
 for idx in range(9):
  walking=idx!=0;p=(idx-1)/8 if walking else 0;bob=(-cfg['walk']['bodyBob']*math.cos(4*math.pi*p)) if walking else 0
  parts={s:Image.new('RGBA',(256,256)) for s in cfg['drawOrder']};joints={};soles={};matrices={};bones=[]
  for side in ['left','right']:
   cap=side.title();phase=(p+(0 if side=='left' else .5))%1
   hip=[cfg['anchors']['hip'+cap][0],cfg['anchors']['hip'+cap][1]+bob]
   upper=cfg['boneLengths'][side]['thigh'];lower=cfg['boneLengths'][side]['shin']
   travel=math.cos(2*math.pi*phase) if walking else 0
   lift=cfg['walk']['lift']*max(0,-math.sin(2*math.pi*phase))**2 if walking else 0
   stride=cfg['walk']['stride']*travel;depth=upper+lower-cfg['walk']['restShortening']-lift
   sagittal_knee=ik([0,0],[stride,depth],upper,lower,-1)
   def project(pt):return [hip[0]+dsgn*cfg['projection']['forwardScale']*pt[0],hip[1]+cfg['projection']['heightScale']*pt[1]+cfg['projection']['forwardToScreenY']*pt[0]]
   knee=project(sagittal_knee);ankle=project([stride,depth])
   recipe=cfg['legSkin'][side];source_chain=recipe['sourceChain'];image=Image.open(folder/recipe['image']).convert('RGBA')
   part=skin_leg(image,source_chain,[hip,knee,ankle])
   from scipy.ndimage import label
   aa=np.array(part);labs,n=label(aa[:,:,3]>10,np.ones((3,3)));sizes=np.bincount(labs.ravel());main=np.argmax(sizes[1:])+1
   for k in range(1,n+1):
    if k!=main:
     if sizes[k]>cfg['postRasterMaxIsolatedPixels']:raise ValueError(('isolated leg region',idx,side,int(sizes[k])))
     aa[labs==k]=0
   parts['body.leg.'+side]=Image.fromarray(aa)
   marker=recipe['sole'];soles[side]=[round(marker[0]+ankle[0]-source_chain[2][0]),round(marker[1]+ankle[1]-source_chain[2][1])]
   for bone,a,b in [('thigh',hip,knee),('shin',knee,ankle)]:bones.append({'segment':bone+'.'+side,'length':upper if bone=='thigh' else lower,'projectedLength':math.dist(a,b),'root':a,'end':b,'sourceSHA256':sha(folder/recipe['image'])})
   shoulder=[cfg['anchors']['shoulder'+cap][0],cfg['anchors']['shoulder'+cap][1]+bob]
   # Entire original arm/hand pair follows one modest shoulder-pivot rotation;
   # their pixels cannot part from each other and elbow lengths cannot change.
   arm=cfg['rigidArms'][side];ang=math.radians(dsgn*arm['swingDegrees']*math.cos(2*math.pi*phase)) if walking else 0;co,si=math.cos(ang),math.sin(ang);ox,oy=arm['sourceJoints']['shoulder'];mat=[co,si,-si,co,shoulder[0]-co*ox+si*oy,shoulder[1]-si*ox-co*oy]
   parts['body.arm.'+side]=compose.place(Image.open(folder/arm['arm']).convert('RGBA'),mat,(256,256));parts['body.hand.'+side]=compose.place(Image.open(folder/arm['hand']).convert('RGBA'),mat,(256,256));matrices['arm.rigid.'+side]=mat
   def turn(pt):return [co*pt[0]-si*pt[1]+mat[4],si*pt[0]+co*pt[1]+mat[5]]
   elbow=turn(arm['sourceJoints']['elbow']);wrist=turn(arm['sourceJoints']['wrist'])
   for bone,a,b in [('upperarm',shoulder,elbow),('forearm',elbow,wrist)]:bones.append({'segment':bone+'.'+side,'length':math.dist(a,b),'root':a,'end':b,'sourceSHA256':sha(folder/arm['arm'])})
   for name,point in [('shoulder',shoulder),('elbow',elbow),('wrist',wrist),('hip',hip),('knee',knee),('ankle',ankle)]:joints[name+cap]=point
  bodymat=[1,0,0,1,0,bob];parts['body.torso']=compose.place(torso,bodymat,(256,256))
  neck=cfg['anchors']['neck'];angle=(cfg['walk']['headSwingDeg']*math.sin(2*math.pi*p)) if walking else 0;c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle));x,y=neck;hmat=[c,s,-s,c,x-c*x+s*y,y-s*x-c*y+bob]
  parts['head.base']=compose.place(head,hmat,(256,256));joints['neck']=[x,y+bob]
  parts={slot:parts[slot] for slot in cfg['drawOrder']};paths={}
  layerdir=folder/'layers'/f'{idx:02}';layerdir.mkdir(exist_ok=True)
  for slot,im in parts.items():q=layerdir/(slot+'.png');im.save(q);paths[slot]=str(q.relative_to(folder))
  whole=editable.editable(folder/'editable',f'{idx:02}',parts);whole.save(folder/'frames'/f'{idx:02}.png');frames.append(whole)
  clip='walk' if walking else 'idle';frame=idx
  bindings.append({'direction':direction,'clip':clip,'frame':frame,'layers':paths})
  origin=cfg['headLocalOrigin'];motion.append({'direction':direction,'clip':clip,'frame':frame,'facing':cfg['facing'],'headToCanvas':hmat[:4]+[c*origin[0]-s*origin[1]+hmat[4],s*origin[0]+c*origin[1]+hmat[5]],'drawOrder':cfg['drawOrder'],'joints':joints,'soleMarkers':soles,'support':'both' if not walking else ('left' if p<.5 else 'right'),'sockets':{},'artApproval':None})
  audits.append({'frame':idx,'segmentTransforms':matrices,'bones':bones,'bodyBob':bob,'shoulderAndHipAnchorsFixedToTorso':True})
 asset={'schemaVersion':'1.0.0','id':cfg['id'],'version':'2.0.0','part':'base','compatibility':cfg['compatibility'],'mode':'pose-map','slots':cfg['drawOrder'],'directions':[direction],'clips':['idle','walk'],'bindings':bindings,'sourceFiles':['authoring.json']+[str(p.relative_to(folder)) for sub in ['source','editable'] for p in sorted((folder/sub).rglob('*')) if p.is_file()]}
 (folder/'asset.json').write_text(json.dumps(asset,indent=2)+'\n');(folder/'motion.json').write_text(json.dumps({'schemaVersion':'1.0.0','rig':'p1-chibi-v1','status':'candidate-awaiting-user-art-review','artApproval':None,'canvas':[256,256],'compatibility':cfg['compatibility'],'baseManifestSHA256':sha(folder/'asset.json'),'durationMs':120,'cycleFrames':list(range(1,9)),'alphaFitOrPerPartResize':False,'frames':motion},indent=2)+'\n');(review/'rig-audit.json').write_text(json.dumps({'artApproval':None,'method':'Single immutable whole-leg skin mesh with shared vertices, fixed-length IK and shoulder-pivot arms; no per-frame art swaps','frames':audits},indent=2)+'\n')
 strip=Image.new('RGBA',(2304,256));board=Image.new('RGB',(768,768),'#17372c')
 for i,im in enumerate(frames):strip.alpha_composite(im,(i*256,0));x,y=i%3*256,i//3*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white')
 strip.save(folder/'strip.png');board.save(review/'nine-poses-fullbody-1x.png');board.resize((1536,1536),Image.Resampling.NEAREST).save(review/'nine-poses-fullbody-2x.png');preview.gif(frames[1:],review/'walk-120ms.gif');preview.flatten(frames[0],2).save(review/'idle-review-2x.png')
 print(direction,'fixed segment rig exported',len(frames),'poses')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--review',type=Path,required=True);a=p.parse_args();render(a.folder,a.review)
