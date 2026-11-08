#!/usr/bin/env python3
"""Prepare left-up r5 source ownership; preserved pixels, explicit joint underlaps."""
from pathlib import Path
import json,hashlib,shutil,importlib.util
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('c',R/'scripts/compose-character-parts.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def poly(points):
 im=Image.new('L',(256,256));ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=255);return np.array(im)>0

def author(folder):
 source=folder/'source';source.mkdir(parents=True,exist_ok=True)
 cfg=json.loads((source/'registration-input-r4.json').read_text());raw=np.array(Image.open(source/'corrected-idle-registered.png').convert('RGBA'));raw[raw[:,:,3]<128]=0;raw[raw[:,:,3]>=128,3]=255;yy,xx=np.mgrid[:256,:256]
 # Authored row ranges follow the complete collar/shirt/shorts ink. This assigns
 # whole spatial regions; no skin-colour filtering or per-pixel colour erosion.
 shirtRows={128:(140,143),129:(122,144),130:(121,145),131:(123,145),132:(124,146),133:(125,147),134:(126,147),135:(126,147),136:(127,147),137:(127,147),138:(127,147),139:(127,147),140:(127,147),141:(126,146),142:(125,146),143:(125,146),144:(124,145),145:(124,145),146:(123,144),147:(123,144),148:(122,144),149:(122,144),150:(121,144),151:(120,145),152:(120,145),153:(120,145),154:(120,145),155:(119,146),156:(119,146),157:(118,147),158:(118,147),159:(118,147),160:(119,148),161:(118,149)}
 pantsRows={160:[(119,148)],161:[(118,149)],162:[(117,149)],163:[(117,149)],164:[(117,149)],165:[(116,150)],166:[(116,149)],167:[(116,149)],168:[(116,150)],169:[(115,150)],170:[(115,150)],171:[(115,150)],172:[(116,149)],173:[(117,148)],174:[(118,134),(135,145)],175:[(123,131),(136,144)]}
 shirt=np.zeros((256,256),bool);pants=shirt.copy()
 for y,(a,b) in shirtRows.items():shirt[y,a:b+1]=True
 for y,ranges in pantsRows.items():
  for a,b in ranges:pants[y,a:b+1]=True
 neck=poly([(124,121),(138,121),(142,132),(137,134),(129,133),(124,130)])
 garment=shirt|pants;cfg['parts']={};bodymat=cfg['sourceRegistration']['bodyMatrix']
 def piece(mask):a=raw.copy();a[~mask]=0;return Image.fromarray(a)
 def save(name,im,**extra):
  image=c.place(im,bodymat,(256,256));p=source/(name+'.png');image.save(p);cfg['parts'][name]={'image':str(p.relative_to(folder)),'sha256':sha(p),**extra};return image
 save('shirt',piece(shirt|neck),authoredRows=shirtRows,neckPolygon=[(124,121),(138,121),(142,132),(137,134),(129,133),(124,130)])
 save('pants',piece(pants),authoredRows=pantsRows)
 armPolys={'left':[(117,129),(125,131),(128,139),(125,149),(119,158),(116,165),(115,178),(101,178),(101,165),(106,152),(111,140),(112,132)],'right':[(145,129),(152,132),(156,147),(160,160),(162,175),(150,177),(148,166),(143,154),(141,139)]}
 # Assign every original arm/hand pixel outside the clothing to the actual arm.
 for side in ['left','right']:
  armMask=poly(armPolys[side])&~garment&~neck
  if side=='left':armMask &= ~((yy>=164)&(xx>=115))
  arm=piece(armMask)
  # A hidden same-skin overlap lives strictly under the original garment, so
  # the shared joint field cannot pull an exposed straight cut away from it.
  shoulderMask=armMask&(yy<=143);patch=piece(shoulderMask);under=c.place(patch,[1,0,0,1,3 if side=='left' else -3,0],(256,256));ua=np.array(under);ua[~garment]=0;whole=Image.fromarray(ua);whole.alpha_composite(arm);arm=whole
  save('arm.'+side,arm,sourcePolygon=armPolys[side],hiddenShoulderOverlapTranslation=[3 if side=='left' else -3,0])
  W=np.array(cfg['sourceJoints']['wrist'+side.title()]);E=np.array(cfg['sourceJoints']['elbow'+side.title()]);u=(W-E)/np.linalg.norm(W-E);t=(xx-W[0])*u[0]+(yy-W[1])*u[1];hand=np.array(arm);hand[t<0]=0;save('hand.'+side,Image.fromarray(hand),sameMeshDomainAsArm=True)
  # Keep the original broad upper thigh, rather than the old narrow row178.
  legMask=poly(cfg['sourcePolygons']['leg.'+side])&(yy>=174)&~garment
  leg=np.array(piece(legMask))
  # Hidden skin root only; the visible original rows174.. are retained verbatim.
  root=raw[176].copy();root[~poly(cfg['sourcePolygons']['leg.'+side])[176]]=0
  for y in range(165,176):
   empty=leg[y,:,3]==0;leg[y,empty]=root[empty]
  # Preserve the already isolated complete foot/calves from r4 below the root.
  old=np.array(Image.open(source/f'preserved-r4-leg.{side}.png'));canonical=c.place(Image.fromarray(leg),bodymat,(256,256));ca=np.array(canonical);ca[yy>=184]=old[yy>=184];p=source/f'leg.{side}.png';Image.fromarray(ca).save(p);cfg['parts']['leg.'+side]={'image':str(p.relative_to(folder)),'sha256':sha(p),'visibleOriginalRowsStart':174,'hiddenRootSourceRow':176,'preservedR4BelowCanvasY':184}
 # New body source used only as a junction reference, never as a replacement body.
 save('junction-reference',piece(((yy>=130)|(neck))&(yy<185)),verificationOnly=True)
 zones=np.zeros((256,256),bool);zones[128:144,111:128]=True;zones[130:144,138:152]=True
 # Hip zones contain authored shorts and original upper-thigh regions, excluding
 # the separate hands passing beside the hips (their external gap is intended).
 hipRegion=pants|((yy>=174)&(poly(cfg['sourcePolygons']['leg.left'])|poly(cfg['sourcePolygons']['leg.right'])))
 hipIm=np.zeros((256,256,4),np.uint8);hipIm[hipRegion]=255;hm=np.array(c.place(Image.fromarray(hipIm),bodymat,(256,256)))[:,:,3]>128;zones |= hm&(yy>=166)&(yy<179)
 zone=np.zeros((256,256,4),np.uint8);zone[zones]=255;Image.fromarray(zone).save(source/'junction-zones.png')
 cfg['junctionZones']='source/junction-zones.png'
 cfg['id']='p1-neutral-up-left-walk-r5-coupled-clothing';cfg['version']=5;cfg['status']='main-only-repair-candidate';cfg['artApproval']=None;cfg['author']='root only; no subagents';cfg['sourceMethod']='complete source spatial ownership; broad original thigh roots; shared shoulder/waist/hem deformation domain';cfg['walk'].update(pelvisTurn=2.0,bodyBob=.55,weightShift=.65,boneMargin=.5);cfg['coupling']={'domain':[92,118,166,222],'gridStep':2,'waistY':[156,166],'hemFollowY':[162,177],'hemThighFollow':.65,'legIndependentY':[179,188],'shoulderBlendY':[-3,6],'armRadius':[7,11],'sampling':'nearest','sharedJointInverseMap':True};cfg['headSource']['sha256']=sha(source/'head.base.png');cfg['scope']='up-left only; up-right remains rejected/unrepaired';(folder/'authoring.json').write_text(json.dumps(cfg,indent=2)+'\n');print('up-left r5 source ownership exported')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);author(p.parse_args().folder)
