#!/usr/bin/env python3
"""Bake independent garment sources on a shared shoulder/waist/hem field.
Runtime consumes ordinary pose maps. Appearance IDs never select rig code.
"""
import argparse,hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.interpolate import LinearNDInterpolator
from scipy.ndimage import map_coordinates
R=Path(__file__).resolve().parents[1]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
rig=module('rig',R/'scripts/export-neutral-continuous-contours.py');compose=rig.compose;editable=rig.editable;preview=rig.preview
xy,rotate,chain,affine,step=rig.xy,rig.rotate,rig.chain,rig.affine,rig.step
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(v,a,b):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def transform(m,points):return np.c_[points,np.ones(len(points))]@m[:2].T
def blend(a,b,w):return a*(1-w[:,None])+b*w[:,None]
def segment_field(points,maps,levels):
 out=transform(maps[0],points)
 for mat,(level,radius) in zip(maps[1:],levels):out=blend(out,transform(mat,points),smooth(points[:,1],level-radius,level+radius))
 return out
def path_distance(points,joints):
 distances=[]
 for a,b in zip(joints[:-1],joints[1:]):
  v=b-a;t=np.clip((points-a)@v/(v@v),0,1);distances.append(np.linalg.norm(points-a-t[:,None]*v,axis=1))
 return np.minimum.reduce(distances)
def sampler(src,dst):
 inverse=LinearNDInterpolator(dst,src,fill_value=-100);yy,xx=np.mgrid[:256,:256];q=inverse(xx,yy)
 def sample(im):
  a=np.array(im);out=np.zeros((256,256,4),np.uint8)
  for ch in range(4):out[:,:,ch]=map_coordinates(a[:,:,ch],[q[:,:,1],q[:,:,0]],order=0,mode='constant',cval=0)
  return Image.fromarray(out)
 return sample

def export(folder,review):
 cfg=json.loads((folder/'authoring.json').read_text());review.mkdir(parents=True,exist_ok=True)
 for sub in ['layers','frames','editable','components']:(folder/sub).mkdir(exist_ok=True)
 parts={k:Image.open(folder/v['image']).convert('RGBA') for k,v in cfg['parts'].items()}
 for name,v in cfg['parts'].items():assert sha(folder/v['image'])==v['sha256'],name
 head=Image.open(folder/cfg['headSource']['image']).convert('RGBA');assert sha(folder/cfg['headSource']['image'])==cfg['headSource']['sha256']
 j={k:np.array(v,float) for k,v in cfg['joints'].items()};w=cfg['walk'];couple=cfg['coupling'];dsgn=cfg['facing'][0];far,near=('right','left') if dsgn<0 else ('left','right');order=['body.leg.'+far,'body.leg.'+near,'body.arm.'+far,'body.hand.'+far,'body.torso','body.arm.'+near,'body.hand.'+near,'head.base']
 x0,y0,x1,y1=couple['domain'];gx,gy=np.meshgrid(np.arange(x0,x1+1,couple['gridStep']),np.arange(y0,y1+1,couple['gridStep']));src=np.c_[gx.ravel(),gy.ravel()].astype(float)
 frames=[];bindings=[];motion=[];audit=[]
 schedule=[{'clip':'idle','frame':0,'phase':0,'amount':0}]+[{'clip':'walk','frame':i,'phase':(i-1)/8,'amount':1} for i in range(1,9)]+cfg.get('transitionPoses',[])
 for idx,spec in enumerate(schedule):
  walk=idx>0;p=spec['phase'];theta=2*math.pi*p;bob=w['bodyBob']*math.cos(2*theta) if walk else 0;sway=-w['weightShift']*math.sin(theta) if walk else 0
  upper=rotate(-w['torsoTurn']*math.sin(theta) if walk else 0,j['waist'],[sway,bob]);pelvis=rotate(w['pelvisTurn']*math.sin(theta) if walk else 0,j['pelvis'],[sway,bob]);joint={};contacts={};sole={};legmaps={};armmaps={};pantmaps={};transforms={}
  for side in ['left','right']:
   cap=side.title();phase=(p+(0 if side=='left' else .5))%1;H,K,A=[j[n+cap] for n in ['hip','knee','ankle']];hip=xy(pelvis,H)
   if walk:
    f,lift,pitch,contact=step(phase,w['stride'],w['lift']);angle=-dsgn*pitch*.45;fm=rotate(angle,A);anchor=max(cfg['footContacts.'+side]['contactPolygon'],key=lambda pt:xy(fm,pt)[1]);relative=xy(fm,anchor)-A;ground=cfg['footContacts.'+side]['flat'][1]+w['forwardToScreenY']*f;ankley=ground-relative[1]-w['heightScale']*lift
    forward=f+(H[0]-hip[0])/(dsgn*w['forwardScale']);depth=(ankley-hip[1]-w['forwardToScreenY']*forward)/w['heightScale'];l1=np.linalg.norm(K-H)/w['heightScale']+w['boneMargin'];l2=np.linalg.norm(A-K)/w['heightScale']+w['boneMargin'];sag=rig.knee_for(forward,depth,l1,l2);lateral=A[0]-H[0];knee=np.array([hip[0]+dsgn*w['forwardScale']*sag[0]+lateral*sag[1]/depth,hip[1]+w['heightScale']*sag[1]+w['forwardToScreenY']*sag[0]]);ankle=np.array([A[0]+dsgn*w['forwardScale']*f,ankley])
   else:knee=K.copy();ankle=A.copy();fm=np.eye(3);contact='both';angle=0;anchor=cfg['footContacts.'+side]['flat'];ground=anchor[1]
   foot=fm.copy();foot[:2,2]+=ankle-A;legmaps[side]=[chain(H,K,hip,knee),chain(K,A,knee,ankle),foot]
   turn=math.degrees(math.atan2(*(knee-hip)[::-1])-math.atan2(*(K-H)[::-1]));pantmaps[side]=rotate(turn*couple['hemThighFollow'],H,hip-H)
   for key,mat in zip(['thigh','shin','foot'],legmaps[side]):transforms[key+'.'+side]=affine(mat)
   fp=xy(foot,anchor);sole[side]=np.rint(fp).astype(int).tolist();contacts[side]={'type':contact,'point':fp.tolist(),'groundY':float(ground),'airborne':contact=='air','footAngleDeg':angle}
   S,E,W=[j[n+cap] for n in ['shoulder','elbow','wrist']];shoulder=xy(upper,S);a=dsgn*w['armSwing']*math.cos(2*math.pi*phase) if walk else 0;b=a+w['elbowFlex']*(.35+.65*math.sin(2*math.pi*phase+.7)) if walk else 0;elbow=shoulder+xy(rotate(a),E-S);wrist=elbow+xy(rotate(b),W-E);hm=rotate(b+(w['wristFollow']*math.sin(2*math.pi*phase-.5) if walk else 0),W,wrist-W);armmaps[side]=[chain(S,E,shoulder,elbow),chain(E,W,elbow,wrist),hm]
   for key,mat in zip(['upperarm','forearm','hand'],armmaps[side]):transforms[key+'.'+side]=affine(mat)
   for name,value in [('hip',hip),('knee',knee),('ankle',ankle),('shoulder',shoulder),('elbow',elbow),('wrist',wrist)]:joint[name+cap]=value.tolist()
  if spec['clip'] in ('walk-start','walk-stop'):
   amount=spec['amount']
   # Interpolate joint targets and rigid rotations, never crossfade raster poses.
   upper=rotate(-w['torsoTurn']*math.sin(theta)*amount,j['waist'],[sway*amount,bob*amount])
   pelvis=rotate(w['pelvisTurn']*math.sin(theta)*amount,j['pelvis'],[sway*amount,bob*amount])
   for side in ['left','right']:
    cap=side.title();phase=(p+(0 if side=='left' else .5))%1
    H,K,A=[j[n+cap] for n in ['hip','knee','ankle']];hip=xy(pelvis,H)
    knee=K+(np.array(joint['knee'+cap])-K)*amount
    ankle=A+(np.array(joint['ankle'+cap])-A)*amount
    # Lift the advancing foot on the authored take-off/settle path.
    extra=spec.get('footLift',{}).get(side,0);ankle[1]-=extra;knee[1]-=extra*.5
    angle=contacts[side]['footAngleDeg']*amount;fm=rotate(angle,A)
    anchor=max(cfg['footContacts.'+side]['contactPolygon'],key=lambda pt:xy(fm,pt)[1])
    ground=cfg['footContacts.'+side]['flat'][1]+(contacts[side]['groundY']-cfg['footContacts.'+side]['flat'][1])*amount
    support=spec['support'];grounded=support=='both' or support==side
    if grounded:
     correction=ground-(xy(fm,anchor)[1]+ankle[1]-A[1])
     ankle[1]+=correction;knee[1]+=correction*.5
    foot=fm.copy();foot[:2,2]+=ankle-A
    legmaps[side]=[chain(H,K,hip,knee),chain(K,A,knee,ankle),foot]
    turn=math.degrees(math.atan2(*(knee-hip)[::-1])-math.atan2(*(K-H)[::-1]))
    pantmaps[side]=rotate(turn*couple['hemThighFollow'],H,hip-H)
    fp=xy(foot,anchor);sole[side]=np.rint(fp).astype(int).tolist()
    ground=cfg['footContacts.'+side]['flat'][1]+(contacts[side]['groundY']-cfg['footContacts.'+side]['flat'][1])*amount
    contacts[side]={'type':'transition','point':fp.tolist(),'groundY':float(ground),'airborne':not grounded,'footAngleDeg':angle,'groundClearance':float(ground-fp[1])}
    S,E,W=[j[n+cap] for n in ['shoulder','elbow','wrist']];shoulder=xy(upper,S)
    a=dsgn*w['armSwing']*math.cos(2*math.pi*phase)*amount
    b=a+w['elbowFlex']*(.35+.65*math.sin(2*math.pi*phase+.7))*amount
    elbow=shoulder+xy(rotate(a),E-S);wrist=elbow+xy(rotate(b),W-E)
    hm=rotate(b+w['wristFollow']*math.sin(2*math.pi*phase-.5)*amount,W,wrist-W)
    armmaps[side]=[chain(S,E,shoulder,elbow),chain(E,W,elbow,wrist),hm]
    for key,mat in zip(['thigh','shin','foot'],legmaps[side]):transforms[key+'.'+side]=affine(mat)
    for key,mat in zip(['upperarm','forearm','hand'],armmaps[side]):transforms[key+'.'+side]=affine(mat)
    for name,value in [('hip',hip),('knee',knee),('ankle',ankle),('shoulder',shoulder),('elbow',elbow),('wrist',wrist)]:joint[name+cap]=value.tolist()
   bob*=amount;sway*=amount
  # Same spatial field is used for shoulders, shirt, belt, shorts and thigh roots.
  waist=smooth(src[:,1],*couple['waistY']);body=blend(transform(upper,src),transform(pelvis,src),waist)
  mid=(j['hipLeft'][0]+j['hipRight'][0])/2;sideweight=smooth(src[:,0],mid-3,mid+3);pantfield=blend(transform(pantmaps['left'],src),transform(pantmaps['right'],src),sideweight);body=blend(body,pantfield,smooth(src[:,1],*couple['hemFollowY']))
  for side in ['left','right']:
   S,E,W=[j[n+side.title()] for n in ['shoulder','elbow','wrist']];distance=path_distance(src,[S,E,W,W+(W-E)*.65]);weight=(1-smooth(distance,*couple['armRadius']))*smooth(src[:,1],S[1]+couple['shoulderBlendY'][0],S[1]+couple['shoulderBlendY'][1]);armfield=segment_field(src,armmaps[side],[(E[1],4),(W[1],2)]);body=blend(body,armfield,weight*(1-smooth(src[:,1],S[1]+6,S[1]+12)))
  shared=sampler(src,body);rendered={name:Image.new('RGBA',(256,256)) for name in order};components={}
  components['shirt']=shared(parts['shirt']);components['pants']=shared(parts['pants']);torso=components['pants'].copy();torso.alpha_composite(components['shirt']);rendered['body.torso']=torso
  for side in ['left','right']:
   S,E,W=[j[n+side.title()] for n in ['shoulder','elbow','wrist']];af=segment_field(src,armmaps[side],[(E[1],4),(W[1],2)]);armdst=blend(body,af,smooth(src[:,1],S[1]+6,S[1]+12));armSample=sampler(src,armdst);full=armSample(parts['arm.'+side]);hand=armSample(parts['hand.'+side]);
   if side==near:
    fa=np.array(full);ha=np.array(hand);yy,xx=np.mgrid[:256,:256];hide=(np.array(components['shirt'])[:,:,3]>128)&(yy<j['shoulder'+side.title()][1]+13);fa[hide]=0;ha[hide]=0;full=Image.fromarray(fa);hand=Image.fromarray(ha)
   fa=np.array(full);ha=np.array(hand);fa[ha[:,:,3]>0]=0;rendered['body.arm.'+side]=Image.fromarray(fa);rendered['body.hand.'+side]=hand;components['complete-arm.'+side]=full
   K,A=[j[n+side.title()] for n in ['knee','ankle']];legfield=segment_field(src,legmaps[side],[(K[1],4),(A[1],3)]);dst=blend(body,legfield,smooth(src[:,1],*couple['legIndependentY']));rendered['body.leg.'+side]=sampler(src,dst)(parts['leg.'+side])
  headmat=upper@rotate(.45*math.sin(theta-.3)*spec['amount'] if walk else 0,j['neck']);rendered['head.base']=compose.place(head,affine(headmat),(256,256));joint['neck']=xy(upper,j['neck']).tolist();transforms.update(upper=affine(upper),pelvis=affine(pelvis),head=affine(headmat));rendered={slot:rendered[slot] for slot in order}
  directory=folder/'layers'/f'{idx:02}';directory.mkdir(exist_ok=True);paths={}
  for slot,im in rendered.items():q=directory/(slot+'.png');im.save(q);paths[slot]=str(q.relative_to(folder))
  componentdir=folder/'components'/f'{idx:02}';componentdir.mkdir(exist_ok=True)
  for name,im in components.items():im.save(componentdir/(name+'.png'))
  shared(parts['junction-reference']).save(componentdir/'junction-reference.png');shared(Image.open(folder/cfg['junctionZones']).convert('RGBA')).save(componentdir/'junction-zones.png')
  whole=editable.editable(folder/'editable',f'{idx:02}',rendered);whole.save(folder/'frames'/f'{idx:02}.png');frames.append(whole);clip=spec['clip'];bindings.append({'direction':cfg['direction'],'clip':clip,'frame':spec['frame'],'layers':paths});origin=cfg['headLocalOrigin'];headlocal=headmat@np.array([[1,0,origin[0]],[0,1,origin[1]],[0,0,1]])
  motion.append({'direction':cfg['direction'],'clip':clip,'frame':spec['frame'],'facing':cfg['facing'],'headToCanvas':affine(headlocal),'drawOrder':order,'joints':joint,'soleMarkers':sole,'support':spec.get('support','both' if not walk else ('left' if p<.5 else 'right')),'sockets':{},'artApproval':None});audit.append({'frame':idx,'partTransforms':transforms,'contacts':contacts,'bodyBob':bob,'weightShift':sway,'sharedJunctionFieldSHA256':hashlib.sha256(body.astype('<f8').tobytes()).hexdigest(),'pantsFollowBothThighs':True,'independentPantsSource':True,'rasterRepairs':[]})
  # Preserve exact shared maps at visible seam landmarks for auditing.
  probes=np.array([[116,138],[141,141],[128,162],[119,176],[137,176],[128,175]],float);inv=LinearNDInterpolator(src,body);audit[-1]['junctionLandmarks']=[{'source':p.tolist(),'destination':q.tolist()} for p,q in zip(probes,inv(probes))]
 asset={'schemaVersion':'1.0.0','id':cfg['id'],'version':'5.0.0','part':'base','compatibility':cfg['compatibility'],'mode':'pose-map','slots':order,'directions':[cfg['direction']],'clips':list(dict.fromkeys(b['clip'] for b in bindings)),'bindings':bindings,'sourceFiles':['authoring.json']+[str(q.relative_to(folder)) for sub in ['source','editable'] for q in sorted((folder/sub).rglob('*')) if q.is_file()]};(folder/'asset.json').write_text(json.dumps(asset,indent=2)+'\n');(folder/'motion.json').write_text(json.dumps({'schemaVersion':'1.0.0','rig':'p1-chibi-v1','status':'main-only-repair-candidate','artApproval':None,'canvas':[256,256],'compatibility':cfg['compatibility'],'baseManifestSHA256':sha(folder/'asset.json'),'durationMs':120,'cycleFrames':list(range(1,9)),'alphaFitOrPerPartResize':False,'frames':motion},indent=2)+'\n');(review/'rig-audit.json').write_text(json.dumps({'repairAndReviewOwner':'root','subagentsUsed':False,'artApproval':None,'poses':audit},indent=2)+'\n')
 board=Image.new('RGB',(768,768),'#17372c');strip=Image.new('RGBA',(len(frames)*256,256))
 for i,im in enumerate(frames):x,y=i%3*256,i//3*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white');strip.alpha_composite(im,(i*256,0))
 board.save(review/'nine-poses-fullbody-1x.png');board.resize((1536,1536),Image.Resampling.NEAREST).save(review/'nine-poses-fullbody-2x.png');strip.save(folder/'strip.png');preview.flatten(frames[0],2).save(review/'idle-review-2x.png');preview.gif(frames[1:9],review/'walk-120ms.gif');print(cfg['direction'],'coupled clothing and junctions exported')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--review',type=Path,required=True);a=p.parse_args();export(a.folder,a.review)
