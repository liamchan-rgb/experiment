#!/usr/bin/env python3
"""Bake continuous anatomical contours with shared joint meshes; work in progress.

Source masks, registrations, hip/shoulder underlaps and contact points are
explicit author data. This tool never fits art by bounds or selects a body by
appearance. The runtime continues to consume ordinary 256px pose maps.
"""
import argparse,hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
compose=module('compose',ROOT/'scripts/compose-character-parts.py');editable=module('editable',ROOT/'scripts/export-wardrobe-part.py');preview=module('preview',ROOT/'scripts/export-neutral-direction.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def xy(m,p):return (m@np.r_[p,1])[:2]
def rotate(deg,pivot=(0,0),shift=(0,0)):
 a=math.radians(deg);c,s=math.cos(a),math.sin(a);x,y=pivot;return np.array([[c,-s,x-c*x+s*y+shift[0]],[s,c,y-s*x-c*y+shift[1]],[0,0,1.]])
def affine(m):return [float(m[0,0]),float(m[1,0]),float(m[0,1]),float(m[1,1]),float(m[0,2]),float(m[1,2])]
def chain(a,b,A,B):
 a,b,A,B=map(lambda v:np.array(v,float),[a,b,A,B]);u=(b-a)/np.linalg.norm(b-a);v=(B-A)/np.linalg.norm(B-A);mat=np.outer(v,u)*np.linalg.norm(B-A)/np.linalg.norm(b-a)+np.outer([-v[1],v[0]],[-u[1],u[0]]);m=np.eye(3);m[:2,:2]=mat;m[:2,2]=A-mat@a;return m

def knee_for(f,h,l1,l2):
 d=math.hypot(f,h)
 if not abs(l1-l2)+.001<d<l1+l2-.001:raise ValueError(('unreachable leg target',f,h,l1,l2,d))
 u=np.array([f,h])/d;along=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-along*along));return u*along+np.array([u[1],-u[0]])*height

def step(phase,stride,lift):
 if phase<.5:
  t=phase*2;f=stride*(1-2*t);height=0;pitch=12*(1-min(t/.25,1))-18*max(0,(t-.65)/.35);contact='heel' if t<.18 else ('toe' if t>.72 else 'flat');return f,height,pitch,contact
 t=(phase-.5)*2;f=stride*(-1-2*t+12*t*t-8*t*t*t);height=lift*math.sin(math.pi*t)**1.5;pitch=float(np.interp(t,[0,.3,.6,1],[-18,-12,5,12]));return f,height,pitch,'air'

def meshwarp(im, transforms, transitions, domainbox=None):
 from scipy.interpolate import LinearNDInterpolator
 from scipy.ndimage import map_coordinates
 arr=np.array(im);box=domainbox or im.getbbox()
 if box is None:return im.copy()
 x0,y0,x1,y1=box;xs=np.arange(x0-3,x1+6,3);ys=np.arange(y0-3,y1+6,3);gx,gy=np.meshgrid(xs,ys);src=np.stack([gx.ravel(),gy.ravel()],axis=1).astype(float);hom=np.c_[src,np.ones(len(src))];dst=hom@transforms[0].T
 for i,(level,radius) in enumerate(transitions):
  t=np.clip((src[:,1]-level+radius)/(2*radius),0,1);t=t*t*(3-2*t);target=hom@transforms[i+1].T;dst=dst*(1-t[:,None])+target*t[:,None]
 inverse=LinearNDInterpolator(dst[:,:2],src,fill_value=-100);yy,xx=np.mgrid[:256,:256];q=inverse(xx,yy);out=np.zeros((256,256,4),dtype=np.uint8)
 for ch in range(4):out[:,:,ch]=map_coordinates(arr[:,:,ch],[q[:,:,1],q[:,:,0]],order=0,mode='constant',cval=0)
 return Image.fromarray(out)

def export(folder,review):
 cfg=json.loads((folder/'authoring.json').read_text());review.mkdir(parents=True,exist_ok=True)
 for sub in ['layers','frames','editable']:(folder/sub).mkdir(exist_ok=True)
 parts={k:Image.open(folder/v['image']).convert('RGBA') for k,v in cfg['parts'].items()};head=Image.open(folder/cfg['headSource']['image']).convert('RGBA');assert sha(folder/cfg['headSource']['image'])==cfg['headSource']['sha256']
 for k,v in cfg['parts'].items():assert sha(folder/v['image'])==v['sha256']
 j0={k:np.array(v,float) for k,v in cfg['joints'].items()};w=cfg['walk'];dsgn=cfg['facing'][0];far,near=('right','left') if dsgn<0 else ('left','right');order=['body.leg.'+far,'body.leg.'+near,'body.arm.'+far,'body.hand.'+far,'body.arm.'+near,'body.hand.'+near,'body.torso','head.base'];frames=[];bindings=[];motion=[];audit=[]
 for idx in range(9):
  walk=idx>0;p=(idx-1)/8 if walk else 0;theta=2*math.pi*p;bob=w['bodyBob']*math.cos(2*theta) if walk else 0;sway=-w['weightShift']*math.sin(theta) if walk else 0
  upper=rotate(-w['torsoTurn']*math.sin(theta) if walk else 0,j0['waist'],[sway,bob]);pelvis=rotate(w['pelvisTurn']*math.sin(theta) if walk else 0,j0['pelvis'],[sway,bob]);rendered={s:Image.new('RGBA',(256,256)) for s in order};joint={};sole={};transforms={};contactmap={};lengths={}
  for side in ['left','right']:
   cap=side.title();phase=(p+(0 if side=='left' else .5))%1;H,K,A=[j0[n+cap] for n in ['hip','knee','ankle']];hip=xy(pelvis,H)
   if walk:
    f,lift,pitch,contact=step(phase,w['stride'],w['lift']);angle=-dsgn*pitch*.45;fm=rotate(angle,A);profile=cfg['footContacts.'+side]['contactPolygon'];anchor=max(profile,key=lambda pt:xy(fm,pt)[1]);relative=xy(fm,anchor)-A
    floor=cfg['footContacts.'+side]['flat'][1];ground=floor+w['forwardToScreenY']*f;ankley=ground-relative[1]-w['heightScale']*lift
    forward=f+(H[0]-hip[0])/(dsgn*w['forwardScale']);depth=(ankley-hip[1]-w['forwardToScreenY']*forward)/w['heightScale'];l1=np.linalg.norm(K-H)/w['heightScale']+w['boneMargin'];l2=np.linalg.norm(A-K)/w['heightScale']+w['boneMargin'];sag=knee_for(forward,depth,l1,l2)
    lateral=A[0]-H[0];knee=np.array([hip[0]+dsgn*w['forwardScale']*sag[0]+lateral*sag[1]/depth,hip[1]+w['heightScale']*sag[1]+w['forwardToScreenY']*sag[0]]);ankle=np.array([A[0]+dsgn*w['forwardScale']*f,ankley]);lengths['thigh.'+side]=float(l1);lengths['shin.'+side]=float(l2)
   else:knee=K.copy();ankle=A.copy();fm=np.eye(3);contact='both';anchor=cfg['footContacts.'+side]['flat'];relative=np.array(anchor)-A;ground=anchor[1]
   legmaps={'thigh.'+side:chain(H,K,hip,knee),'shin.'+side:chain(K,A,knee,ankle)};footmap=fm.copy();footmap[:2,2]+=ankle-A;legmaps['foot.'+side]=footmap
   rendered['body.leg.'+side]=meshwarp(parts['leg.'+side],list(legmaps.values()),[(K[1],4),(A[1],3)])
   for name,mat in legmaps.items():transforms[name]=affine(mat)
   footpoint=xy(footmap,anchor);sole[side]=[round(float(x)) for x in footpoint];contactmap[side]={'type':contact,'point':footpoint.tolist(),'groundY':float(ground),'airborne':contact=='air','footAngleDeg':float(angle) if walk else 0}
   S,E,W=[j0[n+cap] for n in ['shoulder','elbow','wrist']];shoulder=xy(upper,S)
   a=dsgn*w['armSwing']*math.cos(2*math.pi*phase) if walk else 0;b=a+(w['elbowFlex']*(.35+.65*math.sin(2*math.pi*phase+.7))) if walk else 0
   elbow=shoulder+xy(rotate(a),E-S);wrist=elbow+xy(rotate(b),W-E);armmaps={'upperarm.'+side:chain(S,E,shoulder,elbow),'forearm.'+side:chain(E,W,elbow,wrist)}
   for name,mat in armmaps.items():transforms[name]=affine(mat)
   hm=rotate(b+(w['wristFollow']*math.sin(2*math.pi*phase-.5) if walk else 0),W,wrist-W);ams=list(armmaps.values())+[hm];full=meshwarp(parts['arm.'+side],ams,[(E[1],4),(W[1],2)]);hand=meshwarp(parts['hand.'+side],ams,[(E[1],4),(W[1],2)],parts['arm.'+side].getbbox());fullarr=np.array(full);fullarr[np.array(hand)[:,:,3]>0]=0;rendered['body.arm.'+side]=Image.fromarray(fullarr);rendered['body.hand.'+side]=hand;transforms['hand.'+side]=affine(hm)
   for name,point in [('hip',hip),('knee',knee),('ankle',ankle),('shoulder',shoulder),('elbow',elbow),('wrist',wrist)]:joint[name+cap]=point.tolist()
  rendered['body.torso']=compose.place(parts['pelvis'],affine(pelvis),(256,256));rendered['body.torso'].alpha_composite(compose.place(parts['torso'],affine(upper),(256,256)))
  headmat=upper@rotate(.45*math.sin(theta-.3) if walk else 0,j0['neck']);rendered['head.base']=compose.place(head,affine(headmat),(256,256));joint['neck']=xy(upper,j0['neck']).tolist();transforms.update(torso=affine(upper),pelvis=affine(pelvis),head=affine(headmat))
  cleanup=[]
  rendered={s:rendered[s] for s in order};directory=folder/'layers'/f'{idx:02}';directory.mkdir(exist_ok=True);paths={}
  for slot,im in rendered.items():q=directory/(slot+'.png');im.save(q);paths[slot]=str(q.relative_to(folder))
  whole=editable.editable(folder/'editable',f'{idx:02}',rendered);whole.save(folder/'frames'/f'{idx:02}.png');frames.append(whole);clip='walk' if walk else 'idle';bindings.append({'direction':cfg['direction'],'clip':clip,'frame':idx,'layers':paths});origin=cfg['headLocalOrigin'];headlocal=headmat@np.array([[1,0,origin[0]],[0,1,origin[1]],[0,0,1]])
  motion.append({'direction':cfg['direction'],'clip':clip,'frame':idx,'facing':cfg['facing'],'headToCanvas':affine(headlocal),'drawOrder':order,'joints':joint,'soleMarkers':sole,'support':'both' if not walk else ('left' if p<.5 else 'right'),'sockets':{},'artApproval':None});audit.append({'frame':idx,'partTransforms':transforms,'contacts':contactmap,'sagittalLengths':lengths,'bodyBob':bob,'weightShift':sway,'mainAuthoredSources':True,'continuousContourMesh':True,'rasterEdgeCleanup':cleanup})
 asset={'schemaVersion':'1.0.0','id':cfg['id'],'version':'4.0.0','part':'base','compatibility':cfg['compatibility'],'mode':'pose-map','slots':order,'directions':[cfg['direction']],'clips':['idle','walk'],'bindings':bindings,'sourceFiles':['authoring.json']+[str(q.relative_to(folder)) for sub in ['source','editable'] for q in sorted((folder/sub).rglob('*')) if q.is_file()]};(folder/'asset.json').write_text(json.dumps(asset,indent=2)+'\n');(folder/'motion.json').write_text(json.dumps({'schemaVersion':'1.0.0','rig':'p1-chibi-v1','status':'candidate-main-frame-review-only','artApproval':None,'canvas':[256,256],'compatibility':cfg['compatibility'],'baseManifestSHA256':sha(folder/'asset.json'),'durationMs':120,'cycleFrames':list(range(1,9)),'alphaFitOrPerPartResize':False,'frames':motion},indent=2)+'\n');(review/'rig-audit.json').write_text(json.dumps({'artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'poses':audit},indent=2)+'\n')
 board=Image.new('RGB',(768,768),'#17372c');strip=Image.new('RGBA',(2304,256))
 for i,im in enumerate(frames):x,y=i%3*256,i//3*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white');strip.alpha_composite(im,(i*256,0))
 board.save(review/'nine-poses-fullbody-1x.png');board.resize((1536,1536),Image.Resampling.NEAREST).save(review/'nine-poses-fullbody-2x.png');strip.save(folder/'strip.png');preview.flatten(frames[0],2).save(review/'idle-review-2x.png');preview.gif(frames[1:],review/'walk-120ms.gif');print(cfg['direction'],'continuous-contour pose maps exported')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--review',type=Path,required=True);a=p.parse_args();export(a.folder,a.review)
