"""Offline armor tailoring and motion on one registered anatomical surface.

Source patterns are fitted once to the existing rest body. All pose samplers
use that same rest canvas, with shared shoulder/waist fields. No independently
translated elbows, guessed thigh sockets, or per-frame alpha-bound fitting.
"""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageDraw,ImageChops,ImageFilter
from scipy.spatial import Delaunay
from scipy.ndimage import map_coordinates
from scipy.interpolate import LinearNDInterpolator

def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def warp(im,src,dst,size=(256,256),linear=True):
 src=np.array(src,float);dst=np.array(dst,float);tri=Delaunay(src);uv=np.full((size[1],size[0],2),-100.,float);folds=0
 for ids in (tri.simplices if len(src)<=200 else []):
  s,t=src[ids],dst[ids];old=np.linalg.det(np.c_[s,np.ones(3)]);new=np.linalg.det(np.c_[t,np.ones(3)])
  if abs(new)<1e-7:continue
  if old*new<0:folds+=1
  x0,y0=np.maximum(np.floor(t.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(t.max(0)).astype(int),np.array(size)-1)
  if x1<x0 or y1<y0:continue
  yy,xx=np.mgrid[y0:y1+1,x0:x1+1];p=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)];b=p@np.linalg.inv(np.c_[t,np.ones(3)]);inside=np.all(b>=-1e-7,axis=1);q=b@s
  uv[yy.ravel()[inside],xx.ravel()[inside]]=q[inside]
 if len(src)>200:
  yy,xx=np.mgrid[:size[1],:size[0]];uv=LinearNDInterpolator(dst,src,fill_value=-100)(xx,yy)
 a=np.asarray(im.convert('RGBA'),float)/255.;a[:,:,:3]*=a[:,:,3:4];out=np.zeros((*size[::-1],4),float)
 for c in range(4):out[:,:,c]=map_coordinates(a[:,:,c],[uv[:,:,1],uv[:,:,0]],order=1 if linear else 0,mode='constant',cval=0)
 np.divide(out[:,:,:3],out[:,:,3:4],out=out[:,:,:3],where=out[:,:,3:4]>1e-6);out[out[:,:,3]<1e-6]=0
 return Image.fromarray(np.clip(np.rint(out*255),0,255).astype('uint8'))
def cut(sheet,polygon):
 alpha=Image.new('L',sheet.size);ImageDraw.Draw(alpha).polygon(polygon,fill=255);out=sheet.copy();out.putalpha(ImageChops.multiply(sheet.getchannel('A'),alpha));return out
def rigid(points,a,b,pa,pb):
 a,b,pa,pb=map(lambda x:np.array(x,float),[a,b,pa,pb]);u=b-a;v=pb-pa;old=math.atan2(u[1],u[0]);new=math.atan2(v[1],v[0]);c,s=math.cos(new-old),math.sin(new-old);rot=np.array([[c,-s],[s,c]])
 # Existing raster body can change projected bone length. Longitudinal fitting
 # follows its actual endpoints; transverse garment width remains registered.
 axis=u/np.linalg.norm(u);local=points-a;long=(local@axis)[:,None]*axis;cross=local-long
 return pa+(cross+long*(np.linalg.norm(v)/np.linalg.norm(u)))@rot.T
def cuff_marker(hand,elbow):
 a=np.asarray(hand.getchannel('A'));yy,xx=np.where(a>=160);xy=np.c_[xx,yy].astype(float);distance=np.sum((xy-np.array(elbow))**2,axis=1);order=np.argsort(distance,kind='stable')[:5]
 return xy[order].mean(0).tolist()

class ArmorSurface:
 def __init__(self,root):
  self.root=Path(root);self.sheet=Image.open(self.root/'Art/Parts/P1-v1/b2-armor-r4/armor-only.png').convert('RGBA')
  self.motion=json.loads((self.root/'Art/Integration/P1-modular-eight-way-v1/motion.json').read_text());self.rests={f['direction']:f for f in self.motion['frames'] if f['clip']=='idle'}
  self.base=self.root/'Art/Parts/P1-v1/eight-way-v1/base';base=json.loads((self.base/'asset.json').read_text());self.body={(b['direction'],b['clip'],b['frame']):b['layers'] for b in base['bindings']};self.marker_cache={};self.patterns={}
  y,x=np.mgrid[115:196:2,88:170:2];self.grid=np.c_[x.ravel(),y.ravel()].astype(float)
  self.waist={'down':164,'down-left':161,'left':164,'up-left':159,'up':159,'up-right':159,'right':164,'down-right':161}
  self.body_width={'down':(114,144),'down-left':(114,142),'left':(114,136),'up-left':(114,143),'up':(112,144),'up-right':(113,142),'right':(120,142),'down-right':(114,142)}
 def joints(self,f):
  k=f['direction'],f['clip'],f['frame']
  if k not in self.marker_cache:
   j={key:list(v) for key,v in f['joints'].items()}
   for side in ['Left','Right']:
    if 'wrist'+side not in j:
     hand=Image.open(self.base/self.body[k]['body.hand.'+side.lower()]).convert('RGBA');j['wrist'+side]=cuff_marker(hand,j['elbow'+side])
   self.marker_cache[k]=j
  return self.marker_cache[k]
 def fit(self,item,d):
  key=item,d
  if key in self.patterns:return self.patterns[key]
  rune=item=='runeArmor';mirror=d in ['right','up-right','down-right'];view='profile' if d in ['left','right'] else 'back' if d=='up' else 'rear-quarter' if d in ['up-left','up-right'] else 'front-quarter' if d in ['down-left','down-right'] else 'front'
  # Named source control rows: collar silhouette, shoulder plane, belt plane,
  # lower edge. Each view is actually drawn from that camera, not narrowed front.
  cfg={
   'front':dict(x=[70,171,247,332,430],y=[114,180,295,405],neck=[247,128],belt=247,body=[(184,117),(314,117),(334,192),(332,263),(340,313),(162,313),(176,263),(173,192)],hem=[(167,280),(335,280),(396,411),(110,411)],arms=[([130,184],[120,269],[115,340]),([368,183],[379,269],[383,340])],polys=[[(183,120),(109,132),(84,207),(87,262),(156,284),(177,250),(185,205)],[(311,120),(382,133),(414,208),(415,262),(345,284),(323,250),(311,205)]]),
   'front-quarter':dict(x=[455,530,590,654,760],y=[117,182,295,405],neck=[586,135],belt=558,body=[(555,120),(633,120),(650,180),(647,259),(673,315),(515,315),(528,256),(527,185)],hem=[(520,278),(675,278),(708,412),(487,412)],arms=[([511,182],[504,267],[499,340]),([682,182],[692,269],[698,340])],polys=[[(550,128),(507,145),(483,201),(485,265),(528,283),(542,244),(550,201)],[(645,124),(701,124),(752,174),(755,234),(732,284),(653,284),(644,242)]]),
   'profile':dict(x=[770,802,839,869,988],y=[114,181,295,405],neck=[853,132],belt=822,body=[(829,119),(882,119),(872,166),(859,215),(861,267),(925,316),(798,316),(802,212)],hem=[(800,279),(927,279),(974,412),(784,412)],arms=[([807,182],[800,269],[795,340]),([902,183],[912,269],[916,340])],polys=[[(819,140),(794,165),(786,226),(811,273),(833,262),(837,198)],[(860,132),(908,115),(962,154),(974,219),(946,276),(864,284),(854,242)]]),
   'rear-quarter':dict(x=[1020,1110,1190,1272,1355],y=[118,182,295,405],neck=[1192,135],belt=1192,body=[(1151,120),(1246,120),(1267,187),(1263,265),(1286,315),(1091,315),(1120,265),(1121,187)],hem=[(1105,280),(1284,280),(1321,412),(1051,412)],arms=[([1104,184],[1086,269],[1078,340]),([1301,184],[1310,269],[1318,340])],polys=[[(1156,123),(1084,136),(1040,194),(1035,260),(1106,286),(1135,245),(1148,204)],[(1251,124),(1300,136),(1320,181),(1328,251),(1292,274),(1266,236)]]),
   'back':dict(x=[1365,1450,1531,1613,1701],y=[116,182,295,405],neck=[1531,134],belt=1531,body=[(1468,119),(1591,119),(1611,189),(1610,263),(1627,314),(1433,314),(1450,263),(1450,189)],hem=[(1440,280),(1623,280),(1671,414),(1397,414)],arms=[([1418,184],[1404,269],[1398,340]),([1642,184],[1653,269],[1658,340])],polys=[[(1467,122),(1404,138),(1375,201),(1379,259),(1443,283),(1461,245),(1468,206)],[(1595,121),(1663,138),(1686,201),(1685,260),(1624,284),(1603,244),(1593,203)]])
  }[view]
  # The second garment has a longer full sleeve and its own collar/belt rows.
  if rune:
   def Y(y):return 457+(y-114)*(330/291)
   cfg={k:([[x,Y(y)] for x,y in v] if k in ['body','hem'] else [[[x,Y(y)] for x,y in poly] for poly in v] if k=='polys' else [[[x,Y(y)] for x,y in chain] for chain in v] if k=='arms' else [Y(y) for y in v] if k=='y' else [v[0],Y(v[1])] if k=='neck' else v) for k,v in cfg.items()}
   # Cuffs and elbow locations are measured on the full-length blue sleeve.
   for chain in cfg['arms']:
    chain[0][1]=538;chain[1][1]=612;chain[2][1]=686
   # Explicit non-self-intersecting full sleeve contours for this garment.
   rune_polys={
    'front': [[(178,470),(102,487),(72,545),(79,605),(65,695),(137,708),(173,645),(183,569)],[(316,470),(392,487),(422,545),(415,605),(429,695),(357,708),(321,645),(311,569)]],
    'front-quarter': [[(544,474),(501,485),(475,538),(480,600),(472,680),(511,697),(534,640),(550,567)],[(640,478),(699,471),(758,526),(749,592),(746,625),(733,695),(657,701),(650,641),(636,584)]],
    'profile': [[(819,475),(794,510),(786,580),(811,650),(833,690),(837,560)],[(857,471),(915,462),(966,515),(979,563),(957,622),(946,701),(866,713),(848,662),(845,600)]],
    'rear-quarter': [[(1156,475),(1084,482),(1040,537),(1030,600),(1029,697),(1091,712),(1120,648),(1146,570)],[(1256,477),(1305,484),(1335,540),(1339,608),(1325,701),(1272,706),(1264,644),(1261,573)]],
    'back': [[(1465,474),(1401,480),(1366,536),(1372,603),(1360,699),(1426,707),(1451,645),(1469,569)],[(1597,474),(1661,480),(1696,536),(1690,603),(1702,699),(1636,707),(1611,645),(1593,569)]]}
   cfg['polys']=rune_polys[view]
   if view=='rear-quarter':cfg['arms'][1][1][0]=1305;cfg['arms'][1][2][0]=1302
  r=self.joints(self.rests[d]);neck=np.array(r['neck']);wl,wr=self.body_width[d];waist=self.waist[d]
  tx=np.array([wl-8,wl,(wl+wr)/2,wr,wr+8],float)
  if mirror:tx=tx[::-1]
  src=np.array([(x,y) for y in cfg['y'] for x in cfg['x']],float);dst=np.array([(x,y) for y in [neck[1]-3,neck[1]+10,waist,waist+23] for x in tx],float)
  src[12,0]=cfg['belt'];dst[12,0]=(r['hipLeft'][0]+r['hipRight'][0])/2
  src=np.vstack([src,cfg['neck']]);dst=np.vstack([dst,neck])
  result={'outfit.torso':warp(cut(self.sheet,cfg['body']),src,dst),'outfit.hem.front':warp(cut(self.sheet,cfg['hem']),src,dst)}
  screen=sorted(['Left','Right'],key=lambda side:r['shoulder'+side][0]);indices=[1,0] if mirror else [0,1]
  for side,i in zip(screen,indices):
   S,E,W=map(lambda p:np.array(p,float),cfg['arms'][i]);polygon=cfg['polys'][i]
   if view=='profile' and i==0:
    # Real profile has no visible far arm. Its hidden sleeve uses the front
    # pattern and remains behind torso by the original rig's layer order.
    S=np.array([130,538 if rune else 184.]);E=np.array([120,612 if rune else 269.]);W=np.array([115,686 if rune else 340.]);polygon=[(183,460),(109,475),(72,535),(78,625),(72,700),(145,700),(165,625),(182,540)] if rune else [(183,120),(109,132),(84,207),(87,262),(156,284),(177,250),(185,205)]
   ts,te,tw=[np.array(r[n+side],float) for n in ['shoulder','elbow','wrist']];src_arm=[];dst_arm=[]
   widths=[58,48,37,32,30] if rune else [52,44,34,30,28];limits=[10.5,9.5,6.5,6.5,6.0] if rune else [10,9,6,4.5,4.3]
   for p,q,sw,dt in [(S-(E-S)*.65,ts-(te-ts)*.35,widths[0],limits[0]),(S,ts,widths[1],limits[1]),(E,te,widths[2],limits[2]),(W,tw,widths[3],limits[3]),(W+(W-E)*.3,tw+(tw-te)*.12,widths[4],limits[4])]:
    v=(E-S) if np.dot(p-S,p-S)<np.dot(p-W,p-W) else (W-E);n=np.array([-v[1],v[0]])/np.linalg.norm(v);v2=(te-ts) if np.dot(q-ts,q-ts)<np.dot(q-tw,q-tw) else (tw-te);nn=np.array([-v2[1],v2[0]])/np.linalg.norm(v2)
    if mirror:nn=-nn
    src_arm.extend([p-n*sw,p,p+n*sw]);dst_arm.extend([q-nn*dt,q,q+nn*dt])
   sleeve=warp(cut(self.sheet,polygon),src_arm,dst_arm)
   near='Right' if mirror else 'Left'
   if view not in ['front','back'] and side!=near:
    # Receding sleeve reads in shadow, including its cream/silver material.
    # Keep the original far arm; a bright far cuff looked like a loose fin.
    shaded=np.asarray(sleeve).copy();shaded[:,:,:3]=np.rint(shaded[:,:,:3]*np.array([.63,.66,.69])).astype('uint8');sleeve=Image.fromarray(shaded)
   result['outfit.sleeve.'+side.lower()]=sleeve
  self.patterns[key]=result
  return result
 def torso_field(self,f,p):
  r=self.joints(self.rests[f['direction']]);j=self.joints(f)
  if f['direction']=='down':
   # The original front rig gives the two shoulders independently animated
   # vertical offsets. Those are arm markers, not a chest rotation. Drive the
   # cuirass from neck and pelvis so it follows the body without twisting.
   rh=(np.array(r['hipLeft'])+np.array(r['hipRight']))/2;h=(np.array(j['hipLeft'])+np.array(j['hipRight']))/2
   return rigid(p,r['neck'],rh,j['neck'],h)
  return rigid(p,r['shoulderLeft'],r['shoulderRight'],j['shoulderLeft'],j['shoulderRight'])
 def pauldron_field(self,f,side,p):
  r=self.joints(self.rests[f['direction']]);j=self.joints(f)
  S,E,W=[np.array(r[n+side],float) for n in ['shoulder','elbow','wrist']];TS,TE,TW=[np.array(j[n+side],float) for n in ['shoulder','elbow','wrist']]
  # Establish body orientation using one coherent torso frame. Each rigid
  # shoulder plate pivots by a bounded portion of the arm's actual swing.
  body=self.torso_field(f,np.array([S,S+[1,0]],float));axis=body[1]-body[0];a=math.atan2(axis[1],axis[0]);co,si=math.cos(a),math.sin(a);R=np.array([[co,-si],[si,co]])
  u=E-S;v=TE-TS;arm_angle=math.atan2(v[1],v[0])-math.atan2(u[1],u[0])-a;arm_angle=(arm_angle+math.pi)%(2*math.pi)-math.pi
  tilt=np.clip(.38*arm_angle,math.radians(-9),math.radians(9))
  # Shoulder translation stays close to the torso, then follows a restrained
  # amount of the visible arm's own motion; this is strongest in profile.
  anchor=body[0]+(.30 if f['direction']=='down' else .82)*(TS-body[0])
  elbow_delta=(TE-TS)-R@(E-S);wrist_delta=(TW-TS)-R@(W-S)
  offset=np.clip(.10*elbow_delta+.18*wrist_delta,-.80,.80)
  anchor=anchor+offset;angle=a+tilt;c,sn=math.cos(angle),math.sin(angle);rot=np.array([[c,-sn],[sn,c]])
  return anchor+(p-S)@rot.T
 def fields(self,f,slot):
  d=f['direction'];j=self.joints(f);r=self.joints(self.rests[d]);p=self.grid;neck=np.array(r['neck']);waist=self.waist[d]
  upper=self.torso_field(f,p);pelvis=rigid(p,r['hipLeft'],r['hipRight'],j['hipLeft'],j['hipRight']);blend=smooth(neck[1]+12,waist+3,p[:,1])[:,None];body=upper*(1-blend)+pelvis*blend
  if 'sleeve' in slot:
   side=slot.split('.')[-1].title();S,E,W=[np.array(r[n+side],float) for n in ['shoulder','elbow','wrist']];TS,TE,TW=[np.array(j[n+side],float) for n in ['shoulder','elbow','wrist']]
   v=E-S;axis=v/np.linalg.norm(v)+(W-E)/np.linalg.norm(W-E);axis/=np.linalg.norm(axis);along=(p-E)@axis;half=min(10.,abs(np.dot(W-E,axis))*.98,abs(np.dot(S-E,axis))*.98);jointblend=smooth(-half,half,along)
   def bone_angle(a,b):return math.atan2(b[1],b[0])-math.atan2(a[1],a[0])
   aa=bone_angle(E-S,TE-TS);bb=bone_angle(W-E,TW-TE);delta=(bb-aa+math.pi)%(2*math.pi)-math.pi;theta=aa+delta*jointblend
   def stretch(v,w):
    axis=v/np.linalg.norm(v);return np.eye(2)+np.outer(axis,axis)*(np.linalg.norm(w)/np.linalg.norm(v)-1)
   local=(p-E);a=local@stretch(E-S,TE-TS).T;b=local@stretch(W-E,TW-TE).T;local=a*(1-jointblend[:,None])+b*jointblend[:,None]
   c,sn=np.cos(theta),np.sin(theta);return TE+np.c_[local[:,0]*c-local[:,1]*sn,local[:,0]*sn+local[:,1]*c]

  if slot=='outfit.hem.front':
   moved=[]
   for side in ['Left','Right']:
    H=np.array(r['hip'+side]);K=r.get('knee'+side)
    moved.append(rigid(p,H,K,j['hip'+side],j['knee'+side]) if K and 'knee'+side in j else p+np.array(j['hip'+side])-H)
   left_is_screen_left=r['hipLeft'][0]<r['hipRight'][0];xmid=(r['hipLeft'][0]+r['hipRight'][0])/2;w=smooth(xmid-5,xmid+5,p[:,0])[:,None];legs=moved[0]*(1-w)+moved[1]*w if left_is_screen_left else moved[1]*(1-w)+moved[0]*w;follow=smooth(waist+5,waist+22,p[:,1])[:,None];return body*(1-follow)+legs*follow
  return body
 def render(self,item,f):
  result={};r=self.joints(self.rests[f['direction']]);j=self.joints(f);yy,xx=np.mgrid[:256,:256];points=np.stack([xx,yy],-1)
  for slot,im in self.fit(item,f['direction']).items():
   if 'sleeve' not in slot:
    result[slot]=warp(im,self.grid,self.fields(f,slot),linear=False);continue
   # Keep the plate anchored at the shoulder while it follows the arm with
   # bounded rotation and offset; the sleeve continues through the elbow.
   side=slot.split('.')[-1].title();S=np.array(r['shoulder'+side]);E=np.array(r['elbow'+side]);axis=(E-S)/np.linalg.norm(E-S);along=(points-S)@axis
   cap=np.asarray(im).copy();sleeve=cap.copy();cap[along>7]=0;sleeve[along<4]=0
   cap=warp(Image.fromarray(cap),self.grid,self.pauldron_field(f,side,self.grid),linear=False)
   arm=warp(Image.fromarray(sleeve),self.grid,self.fields(f,slot),linear=False)
   far_profile=f['direction']=='left' and side=='Right' or f['direction']=='right' and side=='Left'
   if far_profile:
    # The far upper arm is strongly foreshortened in the original profile.
    # Its moving undersleeve may add a one-pixel cloth allowance, but cannot
    # project a bright wedge outside that fixed anatomical visibility region.
    path=self.body[(f['direction'],f['clip'],f['frame'])]['body.arm.'+side.lower()]
    region=Image.open(self.base/path).convert('RGBA').getchannel('A').filter(ImageFilter.MaxFilter(3))
    arm.putalpha(ImageChops.multiply(arm.getchannel('A'),region))
   arm.alpha_composite(cap);result[slot]=arm
  return result

 def battle_layers(self,item):
  import copy
  b=ArmorSurface(self.root);f=copy.deepcopy(b.rests['right'])
  f['joints'].update(neck=[128,132],shoulderRight=[117,141],elbowRight=[128,158],wristRight=[145.6,163.7],shoulderLeft=[122,143],elbowLeft=[116,155],wristLeft=[108,161],hipRight=[134,175],hipLeft=[115,176])
  b.rests['right']=f;b.marker_cache[('right','idle',0)]=f['joints'];b.waist['right']=174;b.body_width['right']=(110,141)
  layers=b.fit(item,'right');core=layers['outfit.sleeve.left'].copy();core.alpha_composite(layers['outfit.torso']);hem=layers['outfit.hem.front'];top=hem.copy();ImageDraw.Draw(top).rectangle((0,182,255,255),fill=0);core.alpha_composite(top)
  new={'MeadowBattleHeroWardrobeCore':core};sleeve=layers['outfit.sleeve.right'];yy,xx=np.mgrid[:256,:256];S=np.array([117,141]);E=np.array([128,158]);v=E-S;along=(np.stack([xx,yy],-1)-S)@v/np.linalg.norm(v);boundary=np.linalg.norm(v)
  cap=np.asarray(sleeve).copy();moving=cap.copy();cap[along>7]=0;moving[along<4]=0;new['MeadowBattleHeroPauldronNearWardrobe']=Image.fromarray(cap);sleeve=Image.fromarray(moving)
  for name,mask in [('Upper',along<=boundary+2.5),('Forearm',along>=boundary-2.5)]:
   out=np.asarray(sleeve).copy();out[~mask]=0;new['MeadowBattleHeroArmNear'+name+'Wardrobe']=Image.fromarray(out)
  for side in ['Near','Far']:
   name='MeadowBattleHeroLeg'+side+'ThighWardrobe';pants=Image.open(self.root/'Sources/Resources/Assets.xcassets'/(name+'.imageset')/(name+'.png')).convert('RGBA');ImageDraw.Draw(pants).rectangle((0,0,255,173),fill=0);piece=hem.copy();dr=ImageDraw.Draw(piece);dr.rectangle((0,0,255,180),fill=0);dr.rectangle((0,0,127,255) if side=='Near' else (129,0,255,255),fill=0);pants.alpha_composite(piece);new[name]=pants
  return new
