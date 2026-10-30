#!/usr/bin/env python3
"""Rebuild the left-facing Forester shirt and shared traveler lower as 13 pose-map layers."""
from pathlib import Path
import json, math, zipfile, io
import numpy as np
from scipy.ndimage import distance_transform_edt, label
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(__file__).resolve().parent
LOWER=ROOT.parent/'traveler-lower-v1'
TEMPLATE=Path('/workspace/experiment/Art/Templates/P1-Neutral/left/walk-r3-complete-transitions')
SRC=ROOT/'source/00-dressed-clean.png'
SIZE=(256,256); SCALE=.194; TX=4.72; TY=6.4

def fixed_source():
 im=Image.open(SRC).convert('RGBA')
 return im.transform(SIZE,Image.Transform.AFFINE,(1/SCALE,0,-TX/SCALE,0,1/SCALE,-TY/SCALE),Image.Resampling.NEAREST)
def alpha_layer(im,mask):
 a=np.array(im).copy(); a[:,:,3]=np.where(mask,255,0).astype('uint8'); return Image.fromarray(a)
def affine(im,src,dst):
 # PIL needs output-to-input coefficients; solve x,y separately.
 A=np.array([[p[0],p[1],1] for p in dst],float); B=np.array([[p[0],p[1]] for p in src],float)
 c=np.linalg.pinv(A)@B
 return im.transform(SIZE,Image.Transform.AFFINE,(c[0,0],c[1,0],c[2,0],c[0,1],c[1,1],c[2,1]),Image.Resampling.NEAREST)
def rigid_warp(im,srcA,srcB,dstA,dstB):
 # Uniform rotation/scale preserves the authored pixel silhouette while matching a limb axis.
 u=np.array([srcB[0]-srcA[0],srcB[1]-srcA[1]],float);v=np.array([dstB[0]-dstA[0],dstB[1]-dstA[1]],float)
 lu=max(1e-6,float(np.linalg.norm(u)));lv=max(1e-6,float(np.linalg.norm(v)));scale=lv/lu
 ang=math.atan2(v[1],v[0])-math.atan2(u[1],u[0]);c=math.cos(ang);s=math.sin(ang)
 # inverse mapping for PIL: source = srcA + R^T*(dest-dstA)/scale
 a=c/scale;b=s/scale;d=-s/scale;e=c/scale
 xoff=srcA[0]-a*dstA[0]-b*dstA[1];yoff=srcA[1]-d*dstA[0]-e*dstA[1]
 return im.transform(SIZE,Image.Transform.AFFINE,(a,b,xoff,d,e,yoff),Image.Resampling.NEAREST)
def save_editable(folder,idx,parts):
 # OpenRaster keeps each semantic part on its own named layer.
 merged=Image.new('RGBA',SIZE)
 for p in parts.values(): merged.alpha_composite(p)
 def zipwrite(z,name,data,compress_type=zipfile.ZIP_DEFLATED):
  info=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0)); info.compress_type=compress_type; info.create_system=0; info.external_attr=0; info.flag_bits=0
  z.writestr(info,data,compress_type=compress_type,compresslevel=9 if compress_type==zipfile.ZIP_DEFLATED else None)
 xml=['<image version="0.0.1" w="256" h="256" name="%02d">'%idx,'<stack>']; buf=io.BytesIO()
 with zipfile.ZipFile(folder/f'editable/{idx:02}.ora','w') as z:
  zipwrite(z,'mimetype','image/openraster',zipfile.ZIP_STORED)
  for i,(name,p) in enumerate(reversed(list(parts.items()))):
   data=io.BytesIO();p.save(data,format='PNG'); path=f'data/{i}.png';zipwrite(z,path,data.getvalue());xml.append(f'<layer name="{name}" src="{path}" x="0" y="0" opacity="1.0" visibility="visible" composite-op="svg:src-over"/>')
  xml.append('</stack></image>');zipwrite(z,'stack.xml',''.join(xml));data=io.BytesIO();merged.save(data,format='PNG');zipwrite(z,'mergedimage.png',data.getvalue())
 def uri(p):
  b=io.BytesIO();p.save(b,format='PNG');import base64;return base64.b64encode(b.getvalue()).decode()
 groups=''.join(f'<g id="{name}"><image width="256" height="256" href="data:image/png;base64,{uri(p)}"/></g>' for name,p in parts.items())
 (folder/f'editable/{idx:02}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 256 256">{groups}</svg>\n')
def clip_to_geometry(art, geom):
 arr=np.array(art).copy();arr[:,:,3][~geom]=0;return Image.fromarray(arr)
def keep_body_attached(art, body_alpha, threshold=32):
 arr=np.array(art).copy(); labels,count=label(arr[:,:,3]>=threshold,structure=np.ones((3,3),dtype=np.uint8)); keep=np.zeros(labels.shape,dtype=bool)
 for i in range(1,count+1):
  comp=labels==i
  if np.any(comp & (body_alpha>=threshold)): keep |= comp
 arr[:,:,3][~keep]=0
 return Image.fromarray(arr)
def cover_to_geometry(art, geom):
 arr=np.array(art).copy(); src=arr[:,:,3]>0
 if not src.any(): return art
 _,idx=distance_transform_edt(~src,return_indices=True)
 missing=geom&~src
 arr[missing,:3]=arr[idx[0][missing],idx[1][missing],:3]
 arr[:,:,3][geom]=255
 return Image.fromarray(arr)
def main():
 raw=fixed_source(); px=np.array(raw); r,g,b,a=px.transpose(2,0,1); yy,xx=np.mgrid[:256,:256]
 # Edited artwork supplies the pixels. These explicit semantic color masks are fixed in the registered idle source.
 green=(a>0)&(g>r*1.22)&(g>b*.76)&(r<110)&(g<180)&(yy>=127)&(yy<=164)&(xx>=108)&(xx<=141)
 gold=(a>0)&(r>=190)&(r<g*1.55)&(g>b*1.55)&(g>=125)&(b<=110)&(yy>=127)&(yy<=166)&(xx>=108)&(xx<=145)
 upper_source={
  'torso':(green&(xx<=134),gold&(xx<=129)),
  'sleeve.left':(green&(xx>=126)&(xx<=134)&(yy>=135),gold&(xx>=126)&(xx<=134)&(yy>=135)),
  'sleeve.right':(green&(xx>=134)&(yy>=137)&(yy<=164),gold&(xx>=134)&(yy>=137)&(yy<=166)),
 }
 # Lower clothing: gray trouser fill and brown boot fill, with a one-pixel outline and seam underlap.
 pants=(a>0)&(yy>=167)&(yy<=207)&(xx>=105)&(xx<=145)&(r>18)&(r<115)&(g>18)&(g<120)&(b>18)&(b<130)&((np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b]))<18)
 boots=(a>0)&(yy>=200)&(yy<=219)&(xx>=100)&(xx<=148)&(r>45)&(r<190)&(g>20)&(g<120)&(b<100)&(r>g*1.15)
 # Wider binary masks include the dark outline as attached garment edge; keep each constrained to its silhouette zone.
 def dilate(mask,n=3): return np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(n)))>0
 boots=dilate(boots)&(yy>=200)&(yy<=219)&(xx>=99)&(xx<=149)&(a>0)
 base=json.loads((TEMPLATE/'source/hidden-geometry.json').read_text())['poses']
 def guide(slot, frame, rows):
  im=np.array(Image.open(TEMPLATE/f'source/visible-layers/{frame:02}/{slot}.png').convert('RGBA'))[:,:,3]
  pts=[]
  for y in rows:
   ys,xs=np.where(im[max(0,y-2):min(256,y+3)]>=128)
   if len(xs): pts.append([int(round(float(np.median(xs)))), int(round(float(np.median(ys))+max(0,y-2)))])
   else:
    yyv=np.where(np.count_nonzero(im>=128,axis=1)>0)[0]; yyv=yyv[(yyv>=168)&(yyv<=220)]; ry=int(yyv[np.argmin(np.abs(yyv-y))]) if len(yyv) else y
    xs=np.where(im[ry]>=128)[0]; pts.append([int(round(float(np.median(xs)))) if len(xs) else 128,ry])
  return pts
 def legguide(side, frame):
  pose=base[frame]; leg=pose['legs'][f'body.leg.{side}']; hip=leg['hip']; sole=pose['soleMarkers'][side]
  layer=np.array(Image.open(TEMPLATE/f'source/visible-layers/{frame:02}/body.leg.{side}.png').convert('RGBA'))[:,:,3]
  def snap(center, radius=10):
   cx,cy=center; y0=max(0,int(cy-radius)); y1=min(256,int(cy+radius+1)); x0=max(0,int(cx-radius));x1=min(256,int(cx+radius+1))
   ys,xs=np.where(layer[y0:y1,x0:x1]>=128); xs=xs+x0;ys=ys+y0
   if not len(xs): return [int(round(cx)),int(round(cy))]
   j=np.argmin((xs-cx)**2+(ys-cy)**2); return [int(xs[j]),int(ys[j])]
  mid=[(hip[0]+sole[0])/2,(hip[1]+sole[1])/2]
  ankle=[sole[0],sole[1]-5]
  return [hip,snap(mid,12),snap(ankle,9)]
 def armguide(side, frame):
  # The body authoring joints are the fixed sleeve guide; generated cuff registration is checked against the exposed hand layer.
  a=base[frame]['arms'][f'body.arm.{side}'];return [a['shoulder'],a['elbow'],a['wrist']]
 poses=[]; bindings=[]
 for i,p in enumerate(base):
  frame=i; clip='idle' if i==0 else ('walk' if i<=8 else ('walk-start' if i<=10 else 'walk-stop')); key=i if i==0 or i>8 else i
  joints=p['arms']; legs=p['legs']; soles=p['soleMarkers']
  # Surface split to nearest articulated leg path in the reference pose.
  def near_line(x,y,A,B):
   vx=B[0]-A[0];vy=B[1]-A[1];t=np.clip(((x-A[0])*vx+(y-A[1])*vy)/(vx*vx+vy*vy+1e-9),0,1);return (x-(A[0]+t*vx))**2+(y-(A[1]+t*vy))**2
  # Author source lower layers split once at the two idle anatomical paths.
  if i==0:
   leg_masks={}
   basepose=base[0]
   for side in ['left','right']:
    hip,knee,an=legguide(side,0)
    leg_masks[side]=near_line(xx,yy,hip,knee)+near_line(xx,yy,knee,an)
   which_left=leg_masks['left']<=leg_masks['right']
  else:
   which_left=pose_split
  pose_split=which_left
  lp=p['legs']['body.leg.left']; rp=p['legs']['body.leg.right']
  source0={side:legguide(side,0) for side in ['left','right']}
  target0={side:legguide(side,frame) for side in ['left','right']}
  parts={}
  # Green fill and gold piping stay separate during authoring; fill color is sampled from green cloth only.
  for side in ['torso','sleeve.left','sleeve.right']:
   green_mask,gold_mask=upper_source[side]
   art=alpha_layer(raw,green_mask)
   if side.startswith('sleeve'):
    semantic='left' if side.endswith('left') else 'right'; arm=f'body.arm.{semantic}'
    old=armguide(semantic,0); new=armguide(semantic,frame)
    art=rigid_warp(art,old[0],old[2],new[0],new[2])
    bodyalpha=np.array(Image.open(TEMPLATE/f'source/visible-layers/{frame:02}/{arm}.png').convert('RGBA'))[:,:,3]
    # Cover the complete authored arm silhouette; the compositor places the untouched hand layer above it.
    geom=np.asarray(Image.fromarray((bodyalpha>0).astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
    art=cover_to_geometry(art,geom); art=clip_to_geometry(art,geom)
   else:
    bodyalpha=np.array(Image.open(TEMPLATE/f'source/visible-layers/{frame:02}/body.torso.png').convert('RGBA'))[:,:,3]>=128
    geom=bodyalpha&(yy>=127)&(yy<=168)&(xx>=104)&(xx<=144)
    geom=np.asarray(Image.fromarray(geom.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
    geom &= (yy>=126)&(yy<=169)&(xx>=103)&(xx<=145)
    art=cover_to_geometry(art,geom); art=clip_to_geometry(art,geom)
   trim=alpha_layer(raw,gold_mask)
   if side.startswith('sleeve'):
    semantic='left' if side.endswith('left') else 'right';old=armguide(semantic,0);new=armguide(semantic,frame)
    trim=rigid_warp(trim,old[0],old[2],new[0],new[2]);trim=clip_to_geometry(trim,geom)
   else: trim=clip_to_geometry(trim,geom)
   art.alpha_composite(trim)
   if side.startswith('sleeve'): art=keep_body_attached(art,bodyalpha,32)
   parts['outfit.'+side]=art
  for side,geo in [('left',lp),('right',rp)]:
   mask=pants& (which_left if side=='left' else ~which_left)
   old=source0[side]; new=target0[side]
   # Bend the trouser at the observed knee instead of rotating the whole leg as one rigid piece.
   upper=near_line(xx,yy,old[0],old[1])<=near_line(xx,yy,old[1],old[2])
   up=rigid_warp(alpha_layer(raw,mask&upper),old[0],old[1],new[0],new[1])
   low=rigid_warp(alpha_layer(raw,mask&~upper),old[1],old[2],new[1],new[2])
   art=up.copy();art.alpha_composite(low)
   bodyalpha=np.array(Image.open(TEMPLATE/f'source/visible-layers/{frame:02}/body.leg.{side}.png').convert('RGBA'))[:,:,3]>=128
   sole_y=soles[side][1]; torsoalpha=np.array(Image.open(TEMPLATE/f'source/visible-layers/{frame:02}/body.torso.png').convert('RGBA'))[:,:,3]>=128
   torso_waist=torsoalpha&(yy>=169)&(yy<=180)
   geom=(bodyalpha&(yy>=168)&(yy<=sole_y-4))|torso_waist
   geom=np.asarray(Image.fromarray(geom.astype('uint8')*255).filter(ImageFilter.MaxFilter(5)))>0
   geom &= (yy>=168)&(yy<=sole_y-3)
   art=cover_to_geometry(art,geom)
   # Soften resampled folds before clipping; this avoids blocky horizontal nearest-neighbor bands across the knee.
   aa=np.array(art); field=aa[:,:,:3].copy(); field[~geom]=np.array([64,64,64],dtype='uint8'); smooth=np.array(Image.fromarray(field).filter(ImageFilter.GaussianBlur(1.0))); aa[:,:,:3][geom]=smooth[geom]; art=Image.fromarray(aa)
   art=clip_to_geometry(art,geom)
   parts[f'outfit.pants.{side}']=art
  for side,geo in [('left',lp),('right',rp)]:
   mask=boots&(which_left if side=='left' else ~which_left)
   art=alpha_layer(raw,mask)
   old=source0[side]; new=target0[side]; oldsole=base[0]['soleMarkers'][side]; newsole=soles[side]
   toe0=[oldsole[0]-5,oldsole[1]]; toe1=[newsole[0]-5,newsole[1]]
   art=rigid_warp(art,old[2],oldsole,new[2],newsole)
   bodyalpha=np.array(Image.open(TEMPLATE/f'source/visible-layers/{frame:02}/body.leg.{side}.png').convert('RGBA'))[:,:,3]
   sole_y=soles[side][1]; sole_x=soles[side][0]
   geom=(bodyalpha>0)&(yy>=sole_y-16)&(yy<=sole_y+1)&(xx>=sole_x-18)&(xx<=sole_x+18)
   geom=np.asarray(Image.fromarray(geom.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
   geom &= (yy>=sole_y-17)&(yy<=sole_y+1)&(xx>=sole_x-18)&(xx<=sole_x+18)
   art=cover_to_geometry(art,geom);art=clip_to_geometry(art,geom)
   art=keep_body_attached(art,bodyalpha,32)
   parts[f'outfit.boot.{side}']=art
  logical=0 if clip=='idle' else (frame if clip=='walk' else (frame-8 if clip=='walk-start' else frame-10))
  poses.append({'storagePose':frame,'clip':clip,'clipFrame':logical,'layers':list(parts),'armGuides':p['arms'],'legGuides':p['legs'],'soleMarkers':soles})
  for slot,art in parts.items():
   out=ROOT/f'png/{frame:02}/{slot}.png' if slot.startswith('outfit.torso') or slot.startswith('outfit.sleeve') else LOWER/f'png/{frame:02}/{slot}.png'
   out.parent.mkdir(parents=True,exist_ok=True);art.save(out)
  # save semantic layer editables per-package
  upp={k:v for k,v in parts.items() if k.startswith('outfit.torso') or k.startswith('outfit.sleeve')}
  low={k:v for k,v in parts.items() if k.startswith('outfit.pants') or k.startswith('outfit.boot')}
  (ROOT/'editable').mkdir(exist_ok=True);(LOWER/'editable').mkdir(exist_ok=True)
  save_editable(ROOT,frame,upp);save_editable(LOWER,frame,low)
  bindings.append({'direction':'left','clip':clip,'frame':logical,'layers':{s:f'png/{frame:02}/{s}.png' for s in upp}})
  # Lower manifest uses its own paths, all four slots on every frame.
  if i==0: lower_bindings=[]
  lower_bindings.append({'direction':'left','clip':clip,'frame':logical,'layers':{s:f'png/{frame:02}/{s}.png' for s in low}})
  # Render complete body preview: fixed template full-body body remains authoritative; layers overdraw only garments.
  body=Image.open(TEMPLATE/f'frames/{frame:02}.png').convert('RGBA')
  for slot in ['outfit.pants.right','outfit.pants.left','outfit.boot.right','outfit.boot.left','outfit.sleeve.right','outfit.torso','outfit.sleeve.left']:
   body.alpha_composite(parts[slot])
  (ROOT/f'review/frames/{frame:02}.png').parent.mkdir(parents=True,exist_ok=True);body.save(ROOT/f'review/frames/{frame:02}.png')
  if i==0: registered=raw; registered.save(ROOT/'source/registered-dressed-preview.png')
 # Build exact manifests and authoring record.
 compat={'rig':'p1-chibi-v1','bodyProfile':'p1-standard','actionSet':'locomotion-v1'}
 for folder,part,slots,binds,id_ in [(ROOT,'outfit',['outfit.torso','outfit.sleeve.right','outfit.sleeve.left'],bindings,'p1-left-forester-v1'),(LOWER,'outfit',['outfit.pants.right','outfit.pants.left','outfit.boot.right','outfit.boot.left'],lower_bindings,'p1-left-traveler-lower-v1')]:
  manifest={'schemaVersion':'1.0.0','id':id_,'version':'1.0.0','part':part,'compatibility':compat,'mode':'pose-map','slots':slots,'directions':['left'],'clips':['idle','walk','walk-start','walk-stop'],'sourceFiles':['source/00-dressed-clean.png','source/prompt-00.txt','authoring.json']+[f'editable/{i:02}.{e}' for i in range(13) for e in ['ora','svg']],'bindings':binds}
  (folder/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n')
 authoring={'schemaVersion':'1.0.0','id':'p1-left-forester-and-traveler-lower','compatibility':compat,'mode':'pose-map','canvas':[256,256],'source':'source/00-dressed-clean.png','drawOrder':{'upper':['outfit.sleeve.right','outfit.torso','outfit.sleeve.left'],'lower':['outfit.pants.right','outfit.pants.left','outfit.boot.right','outfit.boot.left']},'sourceCanvas':[1254,1254],'registration':{'scale':SCALE,'translation':[TX,TY],'method':'fixed source-to-canvas affine; never alpha-fit'},'baseTemplate':str(TEMPLATE),'poses':poses,'materialRules':{'shirt':'forest green with antique-gold piping','pants':'charcoal gray','boots':'warm brown','handClearance':'sleeves stop at wrist crease; hands remain exposed','soleRule':'boot sole affine follows each authored soleMarker; no common ground clamp','detachedPixels':'sleeve/boot connected components must intersect the matching visible body slot at alpha >=32','underlap':'masks expand by 1px at clothing outline; waistband/boot tops overlap base clothing by >=2px'}}
 (ROOT/'authoring.json').write_text(json.dumps(authoring,indent=2)+'\n');(LOWER/'authoring.json').write_text(json.dumps(authoring,indent=2)+'\n')
 # normal-speed GIF: each authored pose is held exactly 120ms.
 from PIL import Image as PIL
 frames=[PIL.open(ROOT/f'review/frames/{i:02}.png').convert('RGBA') for i in range(13)]
 frames[0].save(ROOT/'review/forester-lower-13poses-120ms.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2)
 # Four-column overview for quick authored-pose review.
 sheet=Image.new('RGBA',(4*256,4*256),(43,48,55,255))
 for i,fr in enumerate(frames): sheet.alpha_composite(fr,((i%4)*256,(i//4)*256))
 sheet.convert('RGB').save(ROOT/'review/contact-sheet-13.png')
 # Independent alpha-mask audit: garments must cover torso/legs/arms while hands remain separate compositor layers.
 audit=[]
 for i in range(13):
  def amask(path): return np.array(Image.open(path).convert('RGBA'))[:,:,3]>=128
  vdir=TEMPLATE/f'source/visible-layers/{i:02}'
  torso=amask(vdir/'body.torso.png'); upper=amask(ROOT/f'png/{i:02}/outfit.torso.png')
  pantsL=amask(LOWER/f'png/{i:02}/outfit.pants.left.png');pantsR=amask(LOWER/f'png/{i:02}/outfit.pants.right.png')
  pants=pantsL|pantsR
  torsoMiss=int(np.count_nonzero(torso&~(upper|pants)))
  legMiss=0;armMiss=0
  for side in ['left','right']:
   bodyleg=amask(vdir/f'body.leg.{side}.png');pant=amask(LOWER/f'png/{i:02}/outfit.pants.{side}.png');boot=amask(LOWER/f'png/{i:02}/outfit.boot.{side}.png')
   legMiss+=int(np.count_nonzero(bodyleg&~(pant|boot)))
   bodyarm=amask(vdir/f'body.arm.{side}.png');sleeve=amask(ROOT/f'png/{i:02}/outfit.sleeve.{side}.png')
   armMiss+=int(np.count_nonzero(bodyarm&~sleeve))
  audit.append({'storagePose':i,'torsoUncovered':torsoMiss,'legUncovered':legMiss,'armUncovered':armMiss})
 validation={'schemaVersion':'1.0.0','sourceRegistration':{'scale':SCALE,'translation':[TX,TY],'registeredCanvas':[256,256]},'pngSlotFiles':91,'poseCount':13,'frameDurationMs':120,'coverageAlphaThreshold':128,'poseCoverage':audit,'allTorsoLegArmPixelsCovered':all(not x['torsoUncovered'] and not x['legUncovered'] and not x['armUncovered'] for x in audit),'scope':'internal semantic body-layer mask audit; hands are retained from the base template above sleeves'}
 (ROOT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');(LOWER/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
 print(json.dumps({'forester_bindings':len(bindings),'lower_bindings':len(lower_bindings),'source_registered':raw.size,'pngs':sum(1 for _ in ROOT.glob('png/**/*.png'))+sum(1 for _ in LOWER.glob('png/**/*.png')),'allCoveragePass':validation['allTorsoLegArmPixelsCovered']}))
if __name__=='__main__': main()
