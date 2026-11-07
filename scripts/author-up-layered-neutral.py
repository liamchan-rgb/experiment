#!/usr/bin/env python3
"""Register one back-view neutral source and author anatomical ownership.
No colour-threshold skin erosion, per-limb resizing or per-frame repainting.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/up/walk-r1-layered';D=R/'Art/Review/P1/neutral-up-layered-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=Image.open(P/'source/generated-idle-original.png').convert('RGBA');assert raw.size==(1254,1254);s=256/raw.width;im=raw.transform((256,256),Image.Transform.AFFINE,(1/s,0,0,0,1/s,0),Image.Resampling.NEAREST);A=np.array(im);A[A[:,:,3]<128]=0;A[A[:,:,3]>=128,3]=255;Image.fromarray(A).save(P/'source/registered-idle.png');Image.fromarray(A).resize((1024,1024),Image.Resampling.NEAREST).save(P/'source/registered-idle-4x.png');yy,xx=np.mgrid[:256,:256];opaque=A[:,:,3]>0
 rows={128:[121,134],129:[120,135],130:[117,138],131:[116,139],132:[116,139],133:[116,139],134:[117,138],135:[117,138],136:[117,138],137:[118,137],138:[118,137],139:[118,137],140:[118,137],141:[118,137],142:[118,137],143:[118,137],144:[117,138],145:[117,138],146:[116,139],147:[115,140],148:[115,140],149:[116,139],150:[116,139],151:[116,139],152:[115,140],153:[115,140],154:[115,140],155:[115,140],156:[114,141],157:[113,141],158:[112,142],159:[112,143],160:[112,144],161:[116,139],162:[119,135]}
 head=opaque&(yy<=127);shirt=np.zeros((256,256),bool)
 for y,(lo,hi) in rows.items():shirt[y,lo:hi+1]=True
 shirt&=opaque
 # Exact source-colour underlap behind the neck pivot; idle remains byte-exact.
 underlap=opaque&(yy>=125)&(yy<=127)&(xx>=122)&(xx<=133);shirt|=underlap
 pants=np.zeros((256,256),bool)
 for y,lo,hi in [(161,112,143),(162,112,143),(163,112,143)]+[(y,111,144) for y in range(164,169)]+[(y,110,145) for y in range(169,175)]+[(175,113,142),(176,118,124),(176,131,137)]:pants[y,lo:hi+1]=True
 pants&=opaque&~shirt&~head;occupied=head|shirt|pants;parts={}
 def save(name,m,**extra):
  a=A.copy();a[~m]=0;p=P/'source'/(name+'.png');Image.fromarray(a).save(p);parts[name]={'image':str(p.relative_to(P)),'sha256':sha(p),**extra}
 save('head.base',head);headSource=parts.pop('head.base');save('shirt',shirt);save('pants',pants)
 for side in ['left','right']:
  outer=(xx<=110) if side=='left' else (xx>=146);half=(xx<128) if side=='left' else (xx>=128);m=opaque&~occupied&(yy<=176)&half&((yy<162)|outer);save('arm.'+side,m);occupied|=m
 for side in ['left','right']:
  m=opaque&~occupied&((xx<128) if side=='left' else (xx>=128));save('leg.'+side,m);occupied|=m
 assert not (opaque&~occupied).any()
 joints={'neck':[128,130],'waist':[128,159],'pelvis':[128,168],'shoulderLeft':[112,138],'elbowLeft':[108,153],'wristLeft':[104,166],'shoulderRight':[143,138],'elbowRight':[148,153],'wristRight':[151,166],'hipLeft':[119,166],'kneeLeft':[119,190],'ankleLeft':[118,208],'hipRight':[136,166],'kneeRight':[137,190],'ankleRight':[137,208]}
 for side in ['left','right']:
  arm=np.array(Image.open(P/parts['arm.'+side]['image']))[:,:,3]>0;w=np.array(joints['wrist'+side.title()]);e=np.array(joints['elbow'+side.title()]);v=w-e;cut=(xx-w[0])*v[0]+(yy-w[1])*v[1]>=0;save('hand.'+side,arm&cut,sameDomainAsArm=True)
 footStates={};footRecords=[]
 for state in ['half-rolled','rolled']:
  q=P/'source'/(state+'-feet-original.png');rawFoot=Image.open(q).convert('RGBA');scale=256/rawFoot.width;ref=rawFoot.transform((256,256),Image.Transform.AFFINE,(1/scale,0,0,0,1/scale,0),Image.Resampling.NEAREST);ref.save(P/'source'/(state+'-feet-registered.png'));ref=np.array(ref);valid=ref[:,:,3]>=128;dist,nearest=distance_transform_edt(~valid,return_indices=True);footStates[state]={}
  for side in ['left','right']:
   leg=np.array(Image.open(P/parts['leg.'+side]['image']));mask=(leg[:,:,3]>0)&(yy>=(210 if state=='half-rolled' else 208))&(leg[:,:,:3].max(2)>60);unmatched=int((mask&(dist>2)).sum());mask&=dist<=2;take=ref[nearest[0][mask],nearest[1][mask],:3];leg[mask,:3]=take;dst=P/'source'/('leg.'+side+'-'+state+'.png');Image.fromarray(leg).save(dst);footStates[state][side]={'image':str(dst.relative_to(P)),'sha256':sha(dst)};footRecords.append({'state':state,'side':side,'changedRegionSourceYAtLeast':210 if state=='half-rolled' else 208,'RGBSamples':int(mask.sum()),'maxSourceGutterDistance':float(dist[mask].max(initial=0)),'alphaChanges':0,'retainedUnmatchedSourcePixels':unmatched,'source':str(q.relative_to(P)),'sourceSHA256':sha(q),'registrationScale':scale})
 save('junction-reference',opaque&~head)
 zones=np.zeros((256,256,4),np.uint8)
 for x0,y0,x1,y1 in [(109,131,119,145),(135,131,146,145),(111,173,125,178),(130,173,144,178),(122,125,134,132)]:zones[y0:y1,x0:x1]=255
 Image.fromarray(zones).save(P/'source/junction-zones.png')
 cfg={'schemaVersion':'1.0.0','id':'p1-neutral-up-walk-r1-layered','direction':'up','facing':[0,-1],'status':'candidate-awaiting-user-review','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'compatibility':{'rig':'p1-chibi-v1','bodyProfile':'p1-standard','actionSet':'locomotion-v1'},'sourceRegistration':{'image':'source/generated-idle-original.png','sourceCanvas':[1254,1254],'uniformScale':s,'translation':[0,0],'alphaThreshold':128,'alphaFit':False,'sha256':sha(P/'source/generated-idle-original.png'),'prompt':'source/prompts/neutral-up.txt'},'headLocalOrigin':[80,61],'headSource':headSource,'parts':parts,'joints':joints,'headOwnership':'source y<=127; existing source neck pixels x122..133 y125..127 duplicate as underlap behind moving skull, no new pigment','shirtRows':rows,'pantsRows':'explicit hem ownership in author script; not a colour skin cut','sourceLight':'upper-left','oldApprovedReference':'Art/Review/P1/directions/up/revisions/r1/approval.json','referenceUse':'Back camera, left/right semantic convention, left-plant01/right-plant05, arm opposition and pass phases. Old source pixels/approval preserved. New neutral artwork/rig is a separate candidate, not pixel-identical reuse of clothed frames.','walk':{'stride':5,'depthProjection':.55,'lift':6,'bodyBob':.4,'weightShift':.4,'torsoTurn':.55,'pelvisTurn':.4,'armReachY':2.3,'armReachX':.45,'kneeAnkleFollow':.6,'headSwingDegrees':.4,'durationMs':120},'coupling':{'domain':[88,118,168,230],'gridStep':1,'waistY':[152,164],'hemFollowY':[164,176],'legIndependentY':[177,186],'armRadius':[7,10],'shoulderBlendY':[4,10]},'footContacts.left':{'flat':[118,216]},'footContacts.right':{'flat':[137,216]},'transitionPoses':[{'clip':'walk-start','frame':1,'phase':0,'amount':1/3,'support':'right','footLift':{'left':1.2}},{'clip':'walk-start','frame':2,'phase':0,'amount':2/3,'support':'right','footLift':{'left':.7}},{'clip':'walk-stop','frame':1,'phase':.875,'amount':2/3,'support':'left','footLift':{'right':.7}},{'clip':'walk-stop','frame':2,'phase':.875,'amount':1/3,'support':'both','footLift':{}}],'transitionScope':'Specified idle->walk01 and walk08->idle only; no arbitrary interruption acceptance'}
 cfg['footRollStates']=footStates;cfg['footRollScope']='Two source-paint RGB variants through the unchanged foot silhouette/ankle/UV. Flat -> half -> rolled -> half -> flat; no generated body/limb geometry imported.'
 (D/'foot-source-registration.json').write_text(json.dumps({'method':cfg['footRollScope'],'records':footRecords},indent=2)+'\n')
 (P/'authoring.json').write_text(json.dumps(cfg,indent=2)+'\n');print('Authored straight-back neutral source ownership')
if __name__=='__main__':main()
