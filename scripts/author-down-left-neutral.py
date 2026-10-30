#!/usr/bin/env python3
"""Reproduce fixed source registration and anatomical ownership for down-left r1.
No repainting, color-based skin cuts, bounds fitting or per-frame corrections.
"""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/down-left/walk-r1';D=R/'Art/Review/P1/neutral-down-left-r1'
(P/'source').mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True)
assert (P/'source/generated-idle-original.png').is_file(), 'Preserved original source required'
im=Image.open(P/'source/generated-idle-original.png').convert('RGBA');scale=.17;dx,dy=24,26;im=im.transform((256,256),Image.Transform.AFFINE,(1/scale,0,-dx/scale,0,1/scale,-dy/scale),Image.Resampling.NEAREST);a=np.array(im);a[a[:,:,3]<128]=0;a[a[:,:,3]>=128,3]=255;Image.fromarray(a).save(P/'source/registered-idle.png')
A=np.array(Image.open(P/'source/registered-idle.png').convert('RGBA'));yy,xx=np.mgrid[:256,:256]
def poly(points):
 m=Image.new('L',(256,256));ImageDraw.Draw(m).polygon([tuple(pt) for pt in points],fill=255);return np.array(m)>0
headpoly=[(85,75),(165,75),(165,121),(143,121),(138,124),(131,127),(122,129),(117,128),(110,124),(85,124)]
head=poly(headpoly)
# Entire armhole and hem outline belongs to garment, never eroded by skin hue.
shirtpoly=[(116,128),(134,127),(140,130),(139,134),(136,138),(136,142),(139,147),(140,153),(141,160),(132,162),(115,160),(114,157),(115,152),(117,148),(117,144),(115,141),(115,136),(116,132)]
shirt=poly(shirtpoly)&~head
pantsRows={157:(113,140),158:(113,141),159:(113,141),160:(112,142),161:(111,142),162:(111,142),163:(111,142),164:(111,143),165:(111,143),166:(111,143),167:(111,143),168:(112,143),169:(114,143),170:(118,143),171:(125,142),172:(126,140),173:(127,137)}
pants=np.zeros((256,256),bool)
for y,(lo,hi) in pantsRows.items():pants[y,lo:hi+1]=True
pants &= ~shirt
armPolys={'right':[(110,128),(118,128),(119,142),(119,153),(115,159),(114,170),(99,171),(98,154),(104,139)],'left':[(139,130),(146,131),(153,147),(157,160),(159,176),(142,178),(141,169),(141,154),(135,143),(135,137)]}
legPolys={'right':[(110,167),(126,167),(128,178),(129,194),(128,208),(101,209),(100,199),(110,191),(110,180)],'left':[(125,169),(142,169),(147,186),(149,201),(151,215),(145,220),(125,220),(123,209),(132,200),(129,190),(123,180)]}
parts={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,mask,**extra):
 arr=A.copy();arr[~mask]=0;p=P/'source'/(name+'.png');Image.fromarray(arr).save(p);parts[name]={'image':str(p.relative_to(P)),'sha256':sha(p),**extra}
save('head.base',head)
headsource=parts.pop('head.base')
save('shirt',shirt)
save('pants',pants)
occupied=head|shirt|pants
for side in ['right','left']:
 mask=poly(armPolys[side])&~occupied
 save('arm.'+side,mask,sourcePolygon=armPolys[side])
 # Wrist partition shares the exact arm deformation field.
 cap=side.title();w=[150,166] if side=='left' else [107,160];e=[146,151] if side=='left' else [110,148];u=np.array(w)-e;t=(xx-w[0])*u[0]+(yy-w[1])*u[1]
 save('hand.'+side,mask&(t>=0),sameMeshDomainAsArm=True)
 occupied|=mask
for side in ['right','left']:
 mask=poly(legPolys[side])&~occupied
 save('leg.'+side,mask,sourcePolygon=legPolys[side]);occupied|=mask
unassigned=(A[:,:,3]>0)&~occupied
print('unassigned',np.argwhere(unassigned).tolist())
save('junction-reference',~head)
zones=poly([(110,130),(146,130),(148,144),(110,145)])|poly([(110,164),(144,164),(146,181),(111,181)])
z=np.zeros((256,256,4),np.uint8);z[zones]=255;Image.fromarray(z).save(P/'source/junction-zones.png')
# Explicit cut landmarks are recorded; no per-frame pixel repair.
cfg={'schemaVersion':'1.0.0','id':'p1-neutral-down-left-walk-r1','direction':'down-left','facing':[-1,1],'compatibility':{'rig':'p1-chibi-v1','bodyProfile':'p1-standard','actionSet':'locomotion-v1'},'status':'candidate-awaiting-user-review','artApproval':None,'author':'root only; no subagents','sourceRegistration':{'uniformScale':.17,'translation':[24,26],'alphaFit':False,'alphaThreshold':128,'sourceCanvas':[1254,1254]},'sourceMethod':'Single new authored standing source; explicit spatial ownership; shared shoulder/waist/hem inverse maps; no per-pose raster repair','headPartition':headpoly,'headLocalOrigin':[76,61],'headSource':headsource,'parts':parts,'joints':{'neck':[127,131],'waist':[126,159],'pelvis':[127,167],'shoulderLeft':[140,138],'elbowLeft':[146,151],'wristLeft':[150,166],'shoulderRight':[114,136],'elbowRight':[110,148],'wristRight':[107,160],'hipLeft':[135,170],'kneeLeft':[139,187],'ankleLeft':[140,205],'hipRight':[119,169],'kneeRight':[118,183],'ankleRight':[119,198]},'nearSide':'left','farSide':'right','walk':{'stride':5.0,'lift':2.8,'bodyBob':.55,'weightShift':.55,'torsoTurn':.6,'pelvisTurn':1.3,'boneMargin':.45,'armSwing':6.0,'elbowFlex':1.7,'wristFollow':.6,'forwardScale':.65,'heightScale':1.0,'forwardToScreenY':.3,'durationMs':120},'coupling':{'domain':[88,118,166,230],'gridStep':2,'waistY':[153,164],'hemFollowY':[160,174],'hemThighFollow':.65,'legIndependentY':[175,185],'shoulderBlendY':[-3,6],'armRadius':[7,11],'sampling':'nearest','sharedJointInverseMap':True},'footContacts.left':{'flat':[136,215],'contactPolygon':[[129,213],[130,208],[137,204],[144,204],[147,210],[145,214],[141,215],[133,215]]},'footContacts.right':{'flat':[113,205],'contactPolygon':[[106,204],[105,201],[111,198],[118,195],[124,198],[125,202],[120,204],[113,205]]},'junctionZones':'source/junction-zones.png','pantsRows':pantsRows,'shirtPolygon':shirtpoly,'transitionPoses':[{'clip':'walk-start','frame':1,'phase':0,'amount':1/3,'support':'right','footLift':{'left':1.5}},{'clip':'walk-start','frame':2,'phase':0,'amount':2/3,'support':'right','footLift':{'left':.9}},{'clip':'walk-stop','frame':1,'phase':.875,'amount':2/3,'support':'left','footLift':{'right':.7}},{'clip':'walk-stop','frame':2,'phase':.875,'amount':1/3,'support':'both','footLift':{}}],'transitionScope':{'start':'idle00 -> walk-start01/02 -> walk01','stop':'walk08 -> walk-stop01/02 -> idle00','durationMs':120,'arbitraryPhaseInterrupts':False,'approvalInherited':False}}
(P/'authoring.json').write_text(json.dumps(cfg,indent=2)+'\n')

import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
from scipy.ndimage import label
cfg=json.loads((P/'authoring.json').read_text());A=np.array(Image.open(P/'source/registered-idle.png'));yy,xx=np.mgrid[:256,:256]
head=np.array(Image.open(P/'source/head.base.png'));shirt=np.array(Image.open(P/'source/shirt.png'));assigned=(head[:,:,3]>0)|(shirt[:,:,3]>0); neck=(A[:,:,3]>0)&~assigned&(yy<131);shirt[neck]=A[neck];Image.fromarray(shirt).save(P/'source/shirt.png');cfg['parts']['shirt']['sha256']=hashlib.sha256((P/'source/shirt.png').read_bytes()).hexdigest();cfg['parts']['shirt']['jawNeckOwnershipPixels']=[[int(x),int(y)] for y,x in np.argwhere(neck)];assigned|=neck
# Complete authored pants hems; skin below each curved hem belongs to its own thigh.
rows={157:(113,140),158:(113,141),159:(113,141),160:(112,142),161:(111,142),162:(111,142),163:(111,142),164:(111,143),165:(111,143),166:(111,142),167:(111,142),168:(113,142),169:(114,142),170:(117,141),171:(125,141),172:(126,139),173:(127,136)}
pm=np.zeros((256,256),bool)
for y,(lo,hi) in rows.items():pm[y,lo:hi+1]=True
pm&=~assigned
out={};out['pants']=A.copy();out['pants'][~pm]=0;assigned|=pm
# Full spatial arm contours, with shorts/thigh edge expressly excluded.
for side in ['right','left']:
 mask=Image.new('L',(256,256));ImageDraw.Draw(mask).polygon([tuple(p) for p in cfg['parts']['arm.'+side]['sourcePolygon']],fill=255);old=np.array(mask)>0
 if side=='right':old&=yy<168
 else:old&=~((yy>=173)&(xx<146));old&=~((yy==172)&(xx<144));old&=~((yy==171)&(xx<144));old&=~((yy>=175)&(xx<147))
 arm=old&~assigned;out['arm.'+side]=A.copy();out['arm.'+side][~arm]=0;assigned|=arm
# Explicit inter-thigh cut follows crotch; never let the far leg steal near-leg border.
mid=[(0,126),(176,126),(178,126),(181,128),(185,130),(190,130),(199,128),(210,127),(220,127),(256,127)]
cut=np.interp(np.arange(256),[x[0] for x in mid],[x[1] for x in mid])[:,None]
for side in ['right','left']:
 m=(A[:,:,3]>0)&~assigned&(yy>=167)&((xx<cut) if side=='right' else (xx>=cut))
 out['leg.'+side]=A.copy();out['leg.'+side][~m]=0;assigned|=m
assert not ((A[:,:,3]>0)&~assigned).any(),np.argwhere((A[:,:,3]>0)&~assigned).tolist()
for side in ['left','right']:
 w=np.array(cfg['joints']['wrist'+side.title()]);e=np.array(cfg['joints']['elbow'+side.title()]);u=w-e;t=(xx-w[0])*u[0]+(yy-w[1])*u[1]
 out['hand.'+side]=out['arm.'+side].copy();out['hand.'+side][t<0]=0
for name,a in out.items():
 p=P/'source'/(name+'.png');Image.fromarray(a).save(p);cfg['parts'][name]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 l,n=label(a[:,:,3]>0,np.ones((3,3)));print(name,n,[(int((l==i).sum())) for i in range(1,n+1)])
cfg['pantsRows']=rows;cfg['sourceOwnershipRepairs']={'farArmExcludedAtOrBelowY':168,'nearArmInnerEdge':{'171':144,'172':144,'173':146,'174':146,'175andBelow':147},'interThighCutYX':mid,'unassignedOpaqueSourcePixels':0,'sourcePixelsDiscarded':0,'method':'spatial anatomical reownership; no color filtering or per-frame erosion'}
(P/'authoring.json').write_text(json.dumps(cfg,indent=2)+'\n')

cfg=json.loads((P/'authoring.json').read_text())
cfg['coupling'].update(gridStep=1,hemBlendCenterX=126.5,hemBlendRadius=2.5,legIndependentY=[179,188])
cfg['junctionLandmarks']=[[114,137],[140,138],[126,159],[136,173],[120,169],[127,175]]
cfg['sourceOwnershipRepairs']['sourcePixelsDiscardedScope']='Registered opaque source pixels; raw alpha threshold is separately declared'
cfg['walk']['kneeSwingFollow']=.8
cfg['walk']['kneeMethod']='authored rest projection, proportional hip/ankle tracking, forward swing flexion; no side-view IK imposed on front-diagonal anatomy'
(P/'authoring.json').write_text(json.dumps(cfg,indent=2)+'\n')
z=Image.new('RGBA',(256,256));d=ImageDraw.Draw(z)
for box in [(112,130,119,142),(135,132,146,143),(111,167,125,175),(126,171,142,176)]:d.rectangle(box,fill='white')
z.save(P/'source/junction-zones.png')
