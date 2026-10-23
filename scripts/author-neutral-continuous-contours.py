#!/usr/bin/env python3
"""Main-authored offline source ownership and registration for upper-diagonal r4.
All inputs are preserved in each template source directory.
No runtime or appearance-specific branches are introduced.
"""
from pathlib import Path
import ast,json,shutil,hashlib,importlib.util
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];REC={}
for direction in ['up-left','up-right']:
 cfg=json.loads((R/f'Art/Templates/P1-Neutral/{direction}/walk-r4-continuous-contours/source/registration-input.json').read_text());REC[direction]={'bodyMatrix':cfg['sourceRegistration']['bodyMatrix'],'joints':cfg['sourceJoints'],'polys':cfg['sourcePolygons']}
s=importlib.util.spec_from_file_location('c',R/'scripts/compose-character-parts.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def poly(points):im=Image.new('L',(256,256));ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=255);return np.array(im)>0
def mapped(pt,m):a,b,c,d,x,y=m;return[a*pt[0]+c*pt[1]+x,b*pt[0]+d*pt[1]+y]
for direction,rec in REC.items():
 folder=R/f'Art/Templates/P1-Neutral/{direction}/walk-r4-continuous-contours';source=folder/'source';source.mkdir(parents=True,exist_ok=True)
 shutil.copy(source/'head-before-neck-cleanup.png',source/'head.base.png')
 cfg=json.loads((source/'registration-input.json').read_text());cfg['id']='p1-neutral-'+direction+'-walk-r4-continuous-contours';cfg['parts']={};cfg['status']='candidate-main-frame-review-only';cfg['version']=4;cfg['skinClassifier']=None;cfg['sourceMethod']='complete source contours partitioned by authored polygons, no skin-colour erosion; hidden root rows extended under garment; continuous shared mesh';cfg.pop('sourceRemovedIslands',None)
 raw=Image.open(source/'corrected-idle-registered.png').convert('RGBA');arr=np.array(raw);arr[arr[:,:,3]<128]=0;arr[arr[:,:,3]>=128,3]=255;yy,xx=np.mgrid[:256,:256]
 # Trace ownership by spatial boundaries. Preserve every skin/outline colour.
 if direction=='up-left':
  near=[(118,130),(121,131),(123,133),(124,135),(124,140),(123,143),(121,147),(119,150),(118,153),(117,157),(115,161),(113,164),(113,165),(114,170),(114,176),(102,176),(102,165),(106,157),(108,149),(112,141),(112,135)]
  far=[(146,132),(149,133),(151,141),(155,153),(156,160),(160,166),(159,175),(149,175),(149,166),(147,161),(145,156),(144,151),(144,146),(146,140)]
  clothing=[(122,129),(127,128),(139,128),(146,131),(145,140),(143,146),(143,152),(145,158),(149,163),(149,170),(147,174),(137,175),(134,173),(132,174),(124,175),(116,174),(114,171),(114,166),(116,161),(118,154),(120,149),(123,143),(125,137),(124,133)]
  neck=[(124,121),(138,121),(142,132),(137,134),(129,133),(124,130)]
  rec['joints']['hipLeft']=[123,166];rec['joints']['hipRight']=[141,166]
 else:
  near=[(138,130),(145,130),(149,134),(149,141),(152,151),(156,159),(161,165),(161,176),(149,176),(147,172),(147,166),(144,161),(141,155),(139,149),(138,143),(137,137)]
  far=[(112,129),(115,130),(116,133),(116,138),(117,140),(115,146),(114,151),(115,158),(117,163),(118,169),(114,172),(105,170),(104,162),(105,155),(104,149),(107,140),(109,134)]
  clothing=[(116,129),(122,128),(133,127),(139,130),(138,134),(137,137),(137,143),(139,150),(140,155),(143,161),(145,169),(144,174),(136,175),(129,175),(126,174),(122,175),(116,174),(113,170),(113,163),(115,158),(115,150),(117,144),(118,140),(117,135)]
  neck=[(121,119),(133,119),(135,128),(131,131),(124,131),(120,128)]
  rec['joints']['hipLeft']=[120,165];rec['joints']['hipRight']=[136,166]
 # Explicit row boundaries keep complete skin regions; the garment owns its edging.
 if direction=='up-left':
  far=[(148,132),(151,135),(153,143),(155,153),(156,160),(160,166),(159,175),(149,175),(149,166),(148,161),(147,158),(146,155),(145,151),(145,146),(147,141)]
 else:
  far=[(112,129),(114,130),(114,137),(115,140),(114,146),(114,151),(115,158),(116,163),(116,170),(111,172),(105,170),(104,162),(105,155),(104,149),(107,140),(109,134)]
  near=[(138,130),(145,130),(149,134),(149,141),(152,151),(156,159),(161,165),(161,176),(149,176),(147,172),(147,166),(144,161),(142,156),(141,152),(140,148),(139,143),(138,137)]
 cfg['joints']={k:mapped(v,rec['bodyMatrix']) for k,v in rec['joints'].items()};cfg['sourceJoints']=rec['joints'];cfg['rootExtensionRows']=[165,178]
 def piece(mask):a=arr.copy();a[~mask]=0;return Image.fromarray(a)
 def save(name,im,**data):
  out=c.place(im,rec['bodyMatrix'],(256,256));p=source/(name+'.png');out.save(p);cfg['parts'][name]={'image':str(p.relative_to(folder)),'sha256':sha(p),**data};return out
 save('torso',piece(((yy>=128)&(yy<=174)&~(poly(near)|poly(far)))|poly(neck)),ownership='complete source minus both authored arm regions, rows 128 through174; no colour filtering')
 # Waist ownership retained in one source layer to avoid overlapping shirt/shorts seams.
 save('pelvis',Image.new('RGBA',(256,256)))
 for side in ['left','right']:
  nearSide='left' if direction=='up-left' else 'right';armPoly=near if side==nearSide else far;fullArm=piece(poly(armPoly));W=np.array(rec['joints']['wrist'+side.title()]);E=np.array(rec['joints']['elbow'+side.title()]);u=(W-E)/np.linalg.norm(W-E);t=(xx-W[0])*u[0]+(yy-W[1])*u[1]
  save('arm.'+side,fullArm,sourcePolygon=armPoly)
  save('hand.'+side,piece(poly(armPoly)&(t>=0)),sourcePolygon=armPoly)
  leg=np.array(piece(poly(rec['polys']['leg.'+side])&(yy>=178)))
  # Extend an existing full skin cross-section upward solely into hidden hip volume.
  for y in range(165,178):leg[y]=leg[178]
  if direction=='up-left' and side=='right':
   # The original far toe overlaps the near foot. Reuse the complete same-facing
   # near foot contour with fixed registration instead of copying that overlap.
   nearFoot=piece(poly([[123,203],[130,203],[133,207],[135,212],[133,217],[123,217],[110,214],[110,207],[118,205]])&(yy>=203))
   newFoot=c.place(nearFoot,[1,0,0,1,16,-2],(256,256));leg[yy>=201]=0;tmp=Image.fromarray(leg);tmp.alpha_composite(newFoot);leg=np.array(tmp)
   rec['joints']['ankleRight']=[143,202];cfg['joints']['ankleRight']=mapped([143,202],rec['bodyMatrix'])
  if direction=='up-right' and side=='right':leg[(xx<131)&(yy>=203)]=0
  save('leg.'+side,Image.fromarray(leg),sourcePolygon=rec['polys']['leg.'+side],hiddenRootSourceRow=178)
 headarr=np.array(Image.open(source/'head.base.png'));headarr[yy>=(129 if direction=='up-left' else 125)]=0;Image.fromarray(headarr).save(source/'head.base.png')
 cfg['sourceAlphaThreshold']=128;cfg['headSource']['cleanup']='head-before-neck-cleanup.png, clip below y129 up-left/y125 up-right; complete neck supplied by torso source';cfg['headSource']['sha256']=sha(source/'head.base.png');cfg['walk'].update(stride=5.5,lift=3.0,bodyBob=.45,weightShift=.45,torsoTurn=.7,pelvisTurn=0,boneMargin=.35,forwardScale=.65,heightScale=1.0,forwardToScreenY=-.25,armSwing=7,elbowFlex=3,wristFollow=1)
 cfg['mesh']={'jointBlendHalfWidth':4,'gridStep':3,'sampling':'nearest','sourceColorThreshold':False,'hipInsideShorts':True}
 # Retain authored foot contact profiles from original source, used without fitting.
 oldcfg=json.loads((source/'registration-input.json').read_text())
 from scipy.spatial import ConvexHull
 for side in ['left','right']:
  la=np.array(Image.open(source/('leg.'+side+'.png')));A=cfg['joints']['ankle'+side.title()];ys,xs=np.where((la[:,:,3]>128)&(yy>=A[1]));pts=np.c_[xs,ys];hull=ConvexHull(pts);bottom=pts[ys==ys.max()];cfg['footContacts.'+side]={'flat':bottom[len(bottom)//2].tolist(),'contactPolygon':pts[hull.vertices].tolist()}

 (folder/'authoring.json').write_text(json.dumps(cfg,indent=2)+'\n');print(direction,'continuous source ownership prepared')
