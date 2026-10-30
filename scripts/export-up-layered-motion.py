#!/usr/bin/env python3
"""Bake one back-view source through shared shoulder/waist/shorts/leg fields.
The public appearance compositor stays unchanged. No side-view IK, per-frame painting or bounds fitting.
"""
from pathlib import Path
import hashlib,importlib.util,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageSequence
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/up/walk-r1-layered';D=R/'Art/Review/P1/neutral-up-layered-r1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
mesh=mod('mesh',R/'scripts/export-down-left-motion.py');compose=mesh.compose;edit=mesh.editable;preview=mesh.preview
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
xy,rotate,chain,affine,step=mesh.xy,mesh.rotate,mesh.chain,mesh.affine,mesh.step
smooth,transform,blend,sampler=mesh.smooth,mesh.transform,mesh.blend,mesh.sampler

def main():
 cfg=json.loads((P/'authoring.json').read_text());parts={n:Image.open(P/v['image']).convert('RGBA') for n,v in cfg['parts'].items()};head=Image.open(P/cfg['headSource']['image']).convert('RGBA');assert sha(P/cfg['headSource']['image'])==cfg['headSource']['sha256']
 for n,v in cfg['parts'].items():assert sha(P/v['image'])==v['sha256'],n
 for n in ['layers','frames','editable','components','source-uv']:(P/n).mkdir(exist_ok=True)
 j={n:np.array(v,float) for n,v in cfg['joints'].items()};w=cfg['walk'];c=cfg['coupling'];x0,y0,x1,y1=c['domain'];xx,yy=np.meshgrid(np.arange(x0,x1+1,c['gridStep']),np.arange(y0,y1+1,c['gridStep']));src=np.c_[xx.ravel(),yy.ravel()].astype(float);yy,xx=np.mgrid[:256,:256];uv=np.stack([xx,yy,np.zeros_like(xx),np.full_like(xx,255)],axis=2).astype(np.uint8);uvimage=Image.fromarray(uv);huv=uv.copy();huv[np.array(head)[:,:,3]==0]=0;huv=Image.fromarray(huv)
 schedule=[{'clip':'idle','frame':0,'phase':0,'amount':0}]+[{'clip':'walk','frame':i,'phase':(i-1)/8,'amount':1} for i in range(1,9)]+cfg['transitionPoses'];frames=[];bindings=[];poses=[];audits=[]
 for index,spec in enumerate(schedule):
  amount=spec['amount'];p=spec['phase'];theta=2*math.pi*p;bob=w['bodyBob']*math.cos(2*theta)*amount;sway=-w['weightShift']*math.sin(theta)*amount;upper=rotate(w['torsoTurn']*math.sin(theta)*amount,j['waist'],[sway,bob]);pelvis=rotate(w['pelvisTurn']*math.sin(theta)*amount,j['pelvis'],[sway,bob]);joints={};sole={};contacts={};legmaps={};armmaps={};pantmaps={};tfs={'upper':affine(upper),'pelvis':affine(pelvis)};backArm='left' if math.cos(theta)>=0 else 'right';forwardArm='right' if backArm=='left' else 'left'
  for side in ['left','right']:
   cap=side.title();phase=(p+(0 if side=='left' else .5))%1;phi=2*math.pi*phase;H,K,A=[j[n+cap] for n in ['hip','knee','ankle']];hip=xy(pelvis,H);forward,lift,pitch,contact=step(phase,w['stride'],w['lift']);forward*=amount;lift*=amount;isTransition=spec['clip'].startswith('walk-');support=spec.get('support','both' if amount==0 else ('left' if p<.5 else 'right'));ground=cfg['footContacts.'+side]['flat'][1]-w['depthProjection']*forward;grounded=amount==0 or (support=='both' or support==side) if isTransition else amount==0 or contact!='air'
   if isTransition:lift=0 if grounded else lift+spec.get('footLift',{}).get(side,0)
   dy=ground-cfg['footContacts.'+side]['flat'][1]-lift;ankle=A+[sway*.25,dy];knee=K+[sway*.55,dy*w['kneeAnkleFollow']];knee+= (hip-H)*.35
   foot=rotate(0,A,ankle-A);legmaps[side]=[chain(H,K,hip,knee),chain(K,A,knee,ankle),foot];hem=chain(H,K,hip,knee);pantmaps[side]=hem
   for n,m in zip(['thigh','shin','foot'],legmaps[side]):tfs[n+'.'+side]=affine(m)
   point=xy(foot,cfg['footContacts.'+side]['flat']);sole[side]=np.rint(point).astype(int).tolist();contacts[side]={'type':'transition' if isTransition else contact if amount else 'both','point':point.tolist(),'groundY':float(ground),'airborne':not grounded,'forwardDepth':forward,'projectedLift':lift,'groundClearance':float(ground-point[1])}
   S,E,W=[j[n+cap] for n in ['shoulder','elbow','wrist']];shoulder=xy(upper,S);outward=-1 if side=='left' else 1;handDelta=np.array([outward*w['armReachX']*math.cos(phi),w['armReachY']*math.cos(phi)])*amount;elbow=E+(shoulder-S)*.65+handDelta*.45;wrist=W+(shoulder-S)*.35+handDelta;hm=rotate(.3*outward*math.sin(phi)*amount,W,wrist-W);armmaps[side]=[chain(S,E,shoulder,elbow),chain(E,W,elbow,wrist),hm]
   for n,m in zip(['upperarm','forearm','hand'],armmaps[side]):tfs[n+'.'+side]=affine(m)
   for n,v in [('hip',hip),('knee',knee),('ankle',ankle),('shoulder',shoulder),('elbow',elbow),('wrist',wrist)]:joints[n+cap]=v.tolist()
  # Shared warp joins garment hems to their corresponding thighs and shoulders.
  body=blend(transform(upper,src),transform(pelvis,src),smooth(src[:,1],*c['waistY']));hemfield=blend(transform(pantmaps['left'],src),transform(pantmaps['right'],src),smooth(src[:,0],125,131));body=blend(body,hemfield,smooth(src[:,1],*c['hemFollowY']))
  for side in ['left','right']:
   S,E,W=[j[n+side.title()] for n in ['shoulder','elbow','wrist']];af=mesh.segment_field(src,armmaps[side],[(E[1],4),(W[1],2)]);distance=mesh.path_distance(src,[S,E,W,W+(W-E)*.65]);weight=(1-smooth(distance,*c['armRadius']))*smooth(src[:,1],S[1]-3,S[1]+5)*(1-smooth(src[:,1],S[1]+6,S[1]+12));body=blend(body,af,weight)
  shared=sampler(src,body);components={'shirt':shared(parts['shirt']),'pants':shared(parts['pants'])};torso=components['pants'].copy();torso.alpha_composite(components['shirt']);layers={'body.torso':torso};uvs={'shirt':shared(uvimage),'pants':shared(uvimage)}
  for side in ['left','right']:
   S,E,W=[j[n+side.title()] for n in ['shoulder','elbow','wrist']];af=mesh.segment_field(src,armmaps[side],[(E[1],4),(W[1],2)]);armfield=blend(body,af,smooth(src[:,1],S[1]+c['shoulderBlendY'][0],S[1]+c['shoulderBlendY'][1]));sample=sampler(src,armfield);full=sample(parts['arm.'+side]);hand=sample(parts['hand.'+side]);ar=np.array(full);ar[np.array(hand)[:,:,3]>0]=0;layers['body.arm.'+side]=Image.fromarray(ar);layers['body.hand.'+side]=hand;components['complete-arm.'+side]=full;uvs['arm.'+side]=sample(uvimage)
   K,A=[j[n+side.title()] for n in ['knee','ankle']];lf=mesh.segment_field(src,legmaps[side],[(K[1],4),(A[1],3)]);legfield=blend(body,lf,smooth(src[:,1],*c['legIndependentY']));sample=sampler(src,legfield)
   phase=(p+(0 if side=='left' else .5))%1;state='flat'
   if amount>=.5:
    if spec['clip']=='walk':state='rolled' if .625<=phase<=.75 else 'half-rolled' if .375<=phase<=.875 else 'flat'
    elif spec['clip']=='walk-start' and side=='right':state='half-rolled'
    elif spec['clip']=='walk-stop' and spec['support']!='both' and side!=spec['support']:state='half-rolled'
   legSource=parts['leg.'+side] if state=='flat' else Image.open(P/cfg['footRollStates'][state][side]['image']).convert('RGBA');layers['body.leg.'+side]=sample(legSource);uvs['leg.'+side]=sample(uvimage);contacts[side]['footArtState']=state
  headmat=upper@rotate(w['headSwingDegrees']*math.sin(theta-.3)*amount,j['neck']);origin=cfg['headLocalOrigin'];headlocal=headmat@np.array([[1,0,origin[0]],[0,1,origin[1]],[0,0,1.]])
  box=(origin[0],origin[1],origin[0]+96,origin[1]+96);layers['head.base']=compose.place(head.crop(box),affine(headlocal),(256,256));uvs['head.base']=compose.place(huv.crop(box),affine(headlocal),(256,256));joints['neck']=xy(upper,j['neck']).tolist();tfs['head']=affine(headmat)
  order=['body.leg.left','body.leg.right','body.arm.'+forwardArm,'body.hand.'+forwardArm,'body.torso','body.arm.'+backArm,'body.hand.'+backArm,'head.base'];layers={s:layers[s] for s in order};directory=P/'layers'/f'{index:02}';directory.mkdir(exist_ok=True);paths={}
  for n,im in layers.items():q=directory/(n+'.png');im.save(q);paths[n]=str(q.relative_to(P))
  out=P/'components'/f'{index:02}';out.mkdir(exist_ok=True)
  for n,im in components.items():im.save(out/(n+'.png'))
  shared(parts['junction-reference']).save(out/'junction-reference.png');shared(Image.open(P/'source/junction-zones.png')).save(out/'junction-zones.png');out=P/'source-uv'/f'{index:02}';out.mkdir(exist_ok=True)
  for n,im in uvs.items():im.save(out/(n+'.png'))
  whole=edit.editable(P/'editable',f'{index:02}',layers);whole.save(P/'frames'/f'{index:02}.png');frames.append(whole);bindings.append({'direction':'up','clip':spec['clip'],'frame':spec['frame'],'layers':paths});origin=cfg['headLocalOrigin'];headlocal=headmat@np.array([[1,0,origin[0]],[0,1,origin[1]],[0,0,1.]])
  poses.append({'direction':'up','clip':spec['clip'],'frame':spec['frame'],'facing':[0,-1],'headToCanvas':affine(headlocal),'drawOrder':order,'joints':joints,'soleMarkers':sole,'support':spec.get('support','both' if not amount else 'left' if p<.5 else 'right'),'sockets':{},'artApproval':None});audits.append({'pose':index,'clip':spec['clip'],'frame':spec['frame'],'phase':p,'amount':amount,'partTransforms':tfs,'contacts':contacts,'bodyBob':bob,'weightShift':sway,'backArm':backArm,'forwardArm':forwardArm,'sharedJunctionFieldSHA256':hashlib.sha256(body.astype('<f8').tobytes()).hexdigest(),'pantsFollowBothThighs':True,'rasterRepairs':[]})
 slots=['body.leg.left','body.leg.right','body.arm.left','body.hand.left','body.torso','body.arm.right','body.hand.right','head.base'];asset={'schemaVersion':'1.0.0','id':cfg['id'],'version':'1.0.0','part':'base','compatibility':cfg['compatibility'],'mode':'pose-map','slots':slots,'directions':['up'],'clips':['idle','walk','walk-start','walk-stop'],'bindings':bindings,'sourceFiles':['authoring.json']+[str(p.relative_to(P)) for sub in ['source','editable','source-uv'] for p in sorted((P/sub).rglob('*')) if p.is_file()]};(P/'asset.json').write_text(json.dumps(asset,indent=2)+'\n');motion={'schemaVersion':'1.0.0','rig':'p1-chibi-v1','status':'up-layered-neutral-candidate-awaiting-user-review','artApproval':None,'canvas':[256,256],'compatibility':cfg['compatibility'],'baseManifestSHA256':sha(P/'asset.json'),'durationMs':120,'cycleFrames':list(range(1,9)),'alphaFitOrPerPartResize':False,'frames':poses};(P/'motion.json').write_text(json.dumps(motion,indent=2)+'\n');(D/'rig-audit.json').write_text(json.dumps({'authorAndReviewer':'root','subagentsUsed':False,'artApproval':None,'poses':audits},indent=2)+'\n');(D/'catalog.json').write_text(json.dumps({'assets':[{'id':cfg['id'],'manifest':str((P/'asset.json').relative_to(R))}]},indent=2)+'\n')
 board=Image.new('RGB',(1024,1024),'#17372c');strip=Image.new('RGBA',(13*256,256))
 for i,im in enumerate(frames):x,y=i%4*256,i//4*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white');strip.alpha_composite(im,(i*256,0))
 board.save(D/'all-poses-fullbody-1x.png');board.resize((2048,2048),Image.Resampling.NEAREST).save(D/'all-poses-fullbody-2x.png');strip.save(P/'strip.png');preview.flatten(frames[0],2).save(D/'idle-review-2x.png');preview.gif(frames[1:9],D/'walk-120ms.gif');sequence=[frames[i] for i in [0,9,10]+list(range(1,9))*2+[11,12,0]];preview.gif(sequence,D/'start-stop-120ms.gif',[480]+[120]*20+[480])
 board=Image.new('RGB',(2048,1024),'#17372c')
 with Image.open(D/'walk-120ms.gif') as gif:
  for i,im in enumerate(ImageSequence.Iterator(gif)):
   x,y=i%4*512,i//4*512;board.paste(im.convert('RGB'),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'GIF {i+1}',fill='white')
 board.save(D/'actual-gif-frames-2x.png');print('Exported up13poses,104body layers,91 source UV maps')
if __name__=='__main__':main()
