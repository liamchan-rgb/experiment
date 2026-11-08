#!/usr/bin/env python3
"""Six compact gender-styled haircuts and four independent feature sets.
All use the existing 96px head canvas and original eight-way head transforms.
No skin, ears, jaw, torso, gait, or global motion contract is repainted.
"""
from pathlib import Path
import json,math,copy,sys,subprocess,hashlib,importlib.util
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import distance_transform_edt

R=Path(__file__).resolve().parents[1]
OUT=R/'Art/Parts/P1-v1/custom-heads-v1';D=R/'Art/Review/P1/custom-heads-v1'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
art=load('custom_head_existing_art',R/'scripts/build-chat-apparel-b-eight-way.py')
PROFILE=json.loads((R/'Art/Standards/P1-Parts-v1/profile.json').read_text())
DIRS=art.DIRECTIONS
HAIR={
 'm1-short':{'label':'M1 Short crop','genderStyle':'male','shape':'crop','colors':['#211a16','#493527','#785036','#a6744a','#d4a46b']},
 'm2-sidepart':{'label':'M2 Side part','genderStyle':'male','shape':'part','colors':['#111720','#25303c','#415264','#627a8c','#9aaeba']},
 'm3-topknot':{'label':'M3 Swept knot','genderStyle':'male','shape':'knot','colors':['#262129','#49404a','#756776','#a795a5','#d1bec7']},
 'f1-bob':{'label':'F1 Layered bob','genderStyle':'female','shape':'bob','version':'1.0.2','colors':['#221b31','#3b2d53','#624c7c','#9176ab','#bca8d0']},
 'f2-ponytail':{'label':'F2 Side pony','genderStyle':'female','shape':'pony','colors':['#2b171b','#563038','#8b4b4b','#bd7465','#e7aa8d']},
 'f3-bun':{'label':'F3 Braided bun','genderStyle':'female','shape':'bun','colors':['#382919','#71512f','#a87f43','#d7ad65','#f4d99a']},
}
FACES={
 'm1-bright':{'label':'MA Bright / blue','genderStyle':'male','eye':'#3f7fb0','shadow':'#244666','brow':'#483024','shape':'angular'},
 'm2-calm':{'label':'MB Calm / amber','genderStyle':'male','eye':'#a2773f','shadow':'#5e4128','brow':'#383138','shape':'narrow'},
 'f1-gentle':{'label':'FA Gentle / green','genderStyle':'female','eye':'#4b9075','shadow':'#2e564f','brow':'#57404a','shape':'almond'},
 'f2-clear':{'label':'FB Clear / violet','genderStyle':'female','eye':'#8277aa','shadow':'#51496e','brow':'#61515c','shape':'clear'},
}
BASES={
 'down':[(24,49),(23,39),(27,31),(35,25),(46,23),(58,25),(68,31),(73,40),(72,51),(68,57),(67,47),(61,42),(53,43),(47,46),(40,42),(32,46),(29,55)],
 'down-left':[(28,46),(28,36),(34,29),(44,25),(56,24),(66,29),(73,38),(75,48),(70,60),(64,64),(61,61),(62,56),(61,52),(57,49),(56,56),(54,59),(53,56),(53,51),(49,48),(44,47),(39,48),(35,49),(31,52)],
 'left':[(29,41),(28,34),(34,27),(43,23),(54,23),(65,28),(73,37),(75,47),(70,59),(62,65),(59,60),(61,56),(60,51),(56,48),(52,48),(49,51),(47,57),(44,57),(44,51),(42,48),(40,44),(35,43),(31,44),(29,42)],
 'up-left':[(28,44),(27,35),(33,28),(44,24),(56,24),(67,29),(74,39),(75,49),(70,60),(59,69),(47,70),(37,66),(35,59),(31,56)],
 'up':[(24,43),(25,34),(32,27),(43,23),(54,23),(64,27),(72,35),(74,46),(70,56),(65,64),(55,70),(43,71),(32,65),(27,57)],
}


def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def shape_points(direction,shape):
 source={'right':'left','down-right':'down-left','up-right':'up-left'}.get(direction,direction)
 points=[list(p) for p in BASES[source]]
 if shape=='crop':
  for p in points:
   if p[1]<35:p[1]+=3
  points[2][1]-=3;points[4][1]-=2
  if source in ['up','up-left']:
   for p in points:
    if p[1]>59:p[1]-=4
 elif shape in ['knot','bun']:
  for p in points:
   if source=='down' and p[1]>40 and p[0]<45:p[1]-=2
 elif shape=='part':
  for p in points:
   if source=='down' and 30<=p[0]<=48 and 42<=p[1]<=50:p[1]+=4
   if source=='left' and 30<=p[0]<=44 and 37<=p[1]<=42:p[1]+=3
 elif shape=='bob':
  # Side-swept fringe, tapered ear locks and staggered nape. The back is
  # curved and light rather than a long rectangle with a straight bottom.
  shapes={
   'down':[(24,55),(22,47),(23,37),(27,30),(34,26),(43,23),(53,23),(63,27),(70,34),(73,44),(72,55),(69,61),(70,65),(66,64),(64,69),(61,67),(65,61),(67,54),(66,47),(61,43),(57,42),(53,44),(48,47),(45,48),(43,45),(40,44),(36,45),(31,48),(29,54),(30,60),(29,65),(26,64),(27,59)],
   'left':[(29,42),(28,35),(32,29),(40,25),(49,23),(58,25),(65,28),(71,34),(74,41),(74,51),(72,58),(74,62),(71,61),(71,66),(67,64),(66,69),(61,68),(58,65),(60,59),(59,54),(56,50),(52,48),(49,50),(48,55),(47,59),(44,60),(43,57),(44,51),(42,47),(39,44),(35,44),(32,45),(29,43)],
   'down-left':[(29,43),(27,36),(31,29),(40,25),(50,23),(60,25),(68,30),(73,39),(75,48),(74,56),(71,62),(72,66),(68,64),(66,70),(62,68),(60,64),(61,59),(59,54),(57,51),(56,57),(55,61),(54,60),(54,52),(51,49),(47,49),(43,48),(39,48),(35,50),(32,52),(30,50)],
   'up-left':[(27,45),(26,36),(30,30),(38,25),(48,23),(58,25),(67,30),(72,38),(74,47),(73,56),(70,61),(71,65),(67,63),(65,69),(61,67),(57,70),(52,68),(47,70),(43,68),(39,70),(36,65),(32,65),(32,59),(29,57)],
   'up':[(24,45),(24,37),(29,30),(35,26),(43,23),(54,24),(63,28),(69,35),(72,44),(72,53),(69,60),(70,64),(66,63),(64,68),(60,66),(56,70),(51,68),(47,70),(42,68),(38,70),(34,65),(30,66),(30,61),(27,60)]
  }
  points=shapes[source]
 # Align scalp to the actual directional guide, rather than alpha bounds.
 guides=PROFILE['headLayouts'];guide=guides[direction]
 if 'skullGuide' in guide:cx=(guide['skullGuide'][0]+guide['skullGuide'][2])/2
 else:cx=guide['neck'][0]
 original=PROFILE['headLayouts'][source]
 if 'skullGuide' in original:oldcx=(original['skullGuide'][0]+original['skullGuide'][2])/2
 else:oldcx=original['neck'][0]
 if direction!=source:
  points=[(96-x,y) for x,y in points];oldcx=96-oldcx
 dx=cx-oldcx
 return [(round(x+dx),y) for x,y in points]


def native_hair_texture(direction,style):
 """Reuse the approved hair material density on newly authored silhouettes.
 No hair alpha, skin or facial pixels are copied into the new silhouette.
 SVG remains editable pixel runs; no whole character raster is embedded.
 """
 cfg=HAIR[style];a=json.loads((R/'Art/Parts/P1-v1/eight-way-v1/hair-chestnut/asset.json').read_text())
 binding=next(b for b in a['bindings'] if b['direction']==direction and b['clip']=='idle')
 source=np.asarray(Image.open(R/'Art/Parts/P1-v1/eight-way-v1/hair-chestnut'/binding['layers']['hair.front']).convert('RGBA'))
 _,nearest=distance_transform_edt(source[:,:,3]<128,return_indices=True)
 rgb=source[nearest[0],nearest[1],:3].astype(float)
 lum=rgb@np.array([.3,.59,.11]);shade=np.clip((lum-18)/170,0,1)
 yy,xx=np.mgrid[:96,:96]
 # The layered bob has broad curved locks, not vertical barcode stripes.
 if cfg['shape']=='bob':
  side=-1 if direction in ['left','down-left'] else 1
  if direction in ['up','up-left','up-right']:
   flow=(xx-48)/(1+.018*np.clip(yy-28,0,45))+48
  else:flow=xx+side*.010*(yy-39)**2
  ribbons=np.maximum(0,np.cos(flow*.62+.4))**4
  strands=.35+.13*ribbons+.045*np.cos(flow*.23-yy*.06)+.07*(1-np.clip((xx-25)/55,0,1))-.05*np.clip((yy-47)/24,0,1)
  blend=np.clip((yy-45)/11,0,1)
  shade=shade*(1-blend)+strands*blend
 pal=np.array([[int(c[j:j+2],16) for j in [1,3,5]] for c in cfg['colors']],float)
 phase=shade*4;lo=np.minimum(3,phase.astype(int));f=(phase-lo)[:,:,None]
 out=np.rint(pal[lo]*(1-f)+pal[lo+1]*f).astype('uint8')
 chunks=[]
 for y in range(16,77):
  x=16
  while x<84:
   color=out[y,x];end=x+1
   while end<84 and np.array_equal(out[y,end],color):end+=1
   chunks.append(f'<rect x="{x}" y="{y}" width="{end-x}" height="1" fill="#{color[0]:02x}{color[1]:02x}{color[2]:02x}"/>');x=end
 return ''.join(chunks)


def hair_svg(direction,style):
 cfg=HAIR[style];colors=cfg['colors'];shape=cfg['shape'];points=shape_points(direction,shape)
 def poly(pts,col):return '<polygon points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="'+col+'"/>'
 def line(pts,col,w=1):return '<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{col}" stroke-width="{w}"/>'
 body=poly(points,colors[0]);allpts=np.array(points);cx=float(allpts[:,0].mean());back=direction in ['up','up-left','up-right'];left=direction in ['left','down-left','up-left'];right=direction in ['right','down-right','up-right']
 contour=poly(points,'white')
 paint=poly([(15,20),(80,20),(82,80),(15,80)],colors[2])
 paint+=poly([(cx+4,20),(83,24),(83,83),(cx+3,83),(cx+11,53)],colors[1])
 paint+=poly([(22,31),(38,24),(54,25),(65,33),(59,39),(44,36),(30,48),(23,53)],colors[3])
 paint+=poly([(27,33),(39,26),(48,26),(43,29),(32,34),(26,42)],colors[4])
 if back:
  # Flow from a crown whorl to the nape, with large stable clusters.
  crown=(int(cx-4),32)
  for i in range(6):
   x=28+i*8
   paint+=line([crown,(x,46),(x+(-3 if x<cx else 3),60),(int(cx+(x-cx)*.50),69)],colors[1] if i%2 else colors[3])
  paint+=line([(int(cx-8),29),(int(cx-5),27),(int(cx),29)],colors[4])
 else:
  # Front/side parting and broad locks, never a striped noise fill.
  part=int(cx+6 if not right else cx-5)
  for i in range(5):
   start=(part+i//2,27+i);endx=27+i*7 if not right else 71-i*7
   paint+=line([start,(round((part+endx)/2),33+i),(endx,42+i%2*2)],colors[1])
   if i<3:paint+=line([(start[0]-2,start[1]),(round((part+endx)/2)-2,32+i)],colors[3])
 if shape=='crop':
  for x,y in points:
   if y<40:paint+=poly([(x,y),(x+4,y+3),(x+1,y+7)],colors[1])
 elif shape=='part':
  paint+=line([(round(cx+9),26),(round(cx+5),32),(round(cx+2),39)],colors[0])
  paint+=line([(round(cx+8),27),(round(cx+4),32)],colors[4])
 elif shape=='bob':
  for x in [27,31,67,71]:paint+=line([(x,43),(x+1,57),(x,70)],colors[1] if x>48 else colors[3])
  if back:paint+=line([(30,66),(40,69),(56,69),(69,66)],colors[1])
 elif shape in ['knot','bun']:
  for i in range(4):paint+=line([(28+i*12,45),(34+i*8,33),(round(cx+7),24)],colors[1])
 outer=''
 if shape in ['knot','bun']:
  bx=round(cx+7 if not right else cx-7);by=22 if shape=='knot' else 24;radius=6 if shape=='knot' else 8
  pts=[(round(bx+radius*math.cos(k*math.pi/4)),round(by+radius*math.sin(k*math.pi/4))) for k in range(8)]
  outer+=poly(pts,colors[0]);outer+=poly([(bx-radius+2,by-2),(bx-2,by-radius+2),(bx+4,by-radius+3),(bx+radius-1,by+1),(bx+2,by+radius-1),(bx-radius+2,by+3)],colors[2])
  outer+=line([(bx-radius+3,by),(bx-2,by-radius+3),(bx+3,by-radius+4)],colors[4])
  outer+=line([(bx-2,by-3),(bx+3,by),(bx,by+4)],colors[1])
 elif shape=='pony':
  bx=73 if left else 24 if right else 70;by=42
  pts=[(bx-3,by-6),(bx+4,by-5),(bx+7,by+2),(bx+6,by+11),(bx+3,by+22),(bx-4,by+27),(bx-2,by+17),(bx-5,by+8)]
  outer+=poly(pts,colors[0]);outer+=poly([(bx-2,by-4),(bx+3,by-3),(bx+5,by+4),(bx+3,by+16),(bx-1,by+23),(bx,by+11),(bx-3,by+4)],colors[2])
  outer+=line([(bx-1,by-2),(bx+2,by+4),(bx,by+17)],colors[3]);outer+=poly([(bx-4,by-3),(bx+4,by-3),(bx+4,by),(bx-4,by)],'#b1a0be')
 # Compact pony/bun is painted in the existing hair.front slot; no unsupported
 # hair.back slot or new motion order is silently introduced.
 # Keep only a fine part/braid accent over the original-density material;
 # the first draft's broad polygon facets are deliberately not exported.
 paint=native_hair_texture(direction,style)
 if shape in ['part','knot','bun']:
  paint+=line([(round(cx+8),27),(round(cx+4),32),(round(cx+1),38)],colors[1])
 if shape=='bob':
  source={'right':'left','down-right':'down-left','up-right':'up-left'}.get(direction,direction)
  part={'down':[(55,27),(51,31),(47,36),(41,40)],'left':[(56,27),(48,30),(40,35),(34,40)],'down-left':[(57,28),(51,32),(44,38),(36,44)]}.get(source)
  if part:
   if direction!=source:part=[(96-x,y) for x,y in part]
   paint+=line(part,colors[1]);paint+=line([(x-1,y-2) for x,y in part[:-1]],colors[3])
 if shape=='bun':
  for y in [37,41,45]:paint+=line([(68,y),(65,y+2),(68,y+4)],colors[3])
 outline='<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+'" fill="none" stroke="'+colors[0]+'" stroke-width="1"/>'
 return '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96" shape-rendering="crispEdges"><defs><clipPath id="cap">'+contour+'</clipPath></defs><g id="hair.front">'+outer+body+'<g clip-path="url(#cap)">'+paint+'</g>'+outline+'</g></svg>\n'


def face_groups(direction,style):
 cfg=FACES[style];layout=PROFILE['headLayouts'][direction];groups={s:[] for s in ['face.eyes','face.brows','face.nose','face.mouth']}
 def poly(s,p,c):groups[s].append('<polygon points="'+' '.join(f'{x},{y}' for x,y in p)+'" fill="'+c+'"/>')
 def rect(s,x,y,w,h,c):groups[s].append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"/>')
 def line(s,p,c,w=1):groups[s].append('<polyline points="'+' '.join(f'{x},{y}' for x,y in p)+f'" fill="none" stroke="{c}" stroke-width="{w}"/>')
 regions=layout['faceRegions'];ink='#2c2830';kind=cfg['shape']
 for box in regions['face.eyes']:
  x0,y0,x1,y1=box;w=x1-x0;h=y1-y0;left=x0+1;right=x1-2;top=y0+1;bottom=min(y1-1,top+(5 if kind=='narrow' else 6));cx=round((left+right)/2)
  poly('face.eyes',[(left,top+1),(left+1,top),(right-1,top),(right,top+1),(right,bottom-1),(right-1,bottom),(left+1,bottom),(left,bottom-1)],'#e7e1d2')
  iw=2 if w<9 else 3;rect('face.eyes',cx-iw//2,top+1,iw,max(2,bottom-top-1),cfg['eye']);rect('face.eyes',cx-iw//2,bottom-2,iw,2,cfg['shadow']);rect('face.eyes',cx,top+2,1,max(2,bottom-top-2),ink);rect('face.eyes',cx-1,top+1,1,1,'#fff3d4')
  if kind=='angular':line('face.eyes',[(left-1,top+1),(left+1,top),(right,top)],ink)
  elif kind=='narrow':line('face.eyes',[(left,top),(right,top+1)],ink);line('face.eyes',[(left+1,bottom),(right-1,bottom)],'#805a4a')
  else:
   line('face.eyes',[(left,top+1),(left+1,top),(right-1,top),(right,top+1)],ink)
   # One restrained outer lash, kept inside the approved feature window.
   edge=left if (left<48 and direction not in ['right','down-right']) else right
   rect('face.eyes',edge,top,1,1,ink)
  line('face.eyes',[(left,bottom-1),(left+1,bottom),(right-1,bottom)],'#986752')
 for box in regions['face.brows']:
  x0,y0,x1,y1=box
  eyes=regions['face.eyes']
  for e in eyes:
   l=max(x0+1,e[0]+1);r=min(x1-1,e[2]-1);y=max(y0+1,min(y1-2,e[1]-3))
   if kind=='angular':line('face.brows',[(l,y+1),(l+2,y),(r,y+1)],cfg['brow'],2)
   elif kind=='narrow':line('face.brows',[(l,y+1),(r,y+1)],cfg['brow'])
   else:line('face.brows',[(l,y+1),(l+2,y),(r-1,y),(r,y+1)],cfg['brow'])
 for x0,y0,x1,y1 in regions['face.nose']:
  cx=round((x0+x1)/2);cy=round((y0+y1)/2)
  line('face.nose',[(cx,cy-1),(cx-1 if direction in ['left','down-left'] else cx+1,cy+1)],'#ac6c47')
 for x0,y0,x1,y1 in regions['face.mouth']:
  cx=round((x0+x1)/2);cy=round((y0+y1)/2);half=1 if x1-x0<7 else 2
  line('face.mouth',[(cx-half,cy),(cx+half,cy)],'#74483d' if cfg['genderStyle']=='male' else '#96594f')
  if kind in ['angular','almond'] and cy+1<y1:rect('face.mouth',cx,cy+1,1,1,'#bc7c63')
 # Preserve the approved feature proportions/material and original nose/lips.
 # These are only feature pixels; the shared head skin/ears/jaw stay separate.
 original=json.loads((R/'Art/Parts/P1-v1/eight-way-v1/face-blue/asset.json').read_text())
 binding=next(b for b in original['bindings'] if b['direction']==direction and b['clip']=='idle')
 import colorsys
 for slot in ['face.eyes','face.nose','face.mouth']:
  pixels=np.asarray(Image.open(R/'Art/Parts/P1-v1/eight-way-v1/face-blue'/binding['layers'][slot]).convert('RGBA')).copy()
  if slot=='face.eyes':
   target=np.array([int(cfg['eye'][j:j+2],16) for j in [1,3,5]],float)
   for y,x in np.argwhere(pixels[:,:,3]>0):
    h,s,v=colorsys.rgb_to_hsv(*(pixels[y,x,:3]/255))
    if .50<h<.76 and s>.30:pixels[y,x,:3]=np.clip(target*(v/.72),0,255).astype('uint8')
  if slot=='face.mouth' and cfg['genderStyle']=='female':
   mask=pixels[:,:,3]>0;pixels[mask,0]=np.clip(pixels[mask,0].astype(int)+18,0,255)
  source=[]
  for y,x in np.argwhere(pixels[:,:,3]>0):
   r,g,b,a=map(int,pixels[y,x]);source.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="#{r:02x}{g:02x}{b:02x}" fill-opacity="{a/255:.6f}"/>')
  groups[slot]=source
  if slot=='face.eyes':
   for x0,y0,x1,y1 in regions['face.eyes']:
    if kind=='narrow':line(slot,[(x0+1,y0+2),(x1-2,y0+2)],ink)
    elif kind in ['almond','clear']:
     outer=x0+1 if x0<48 else x1-2
     rect(slot,outer,y0+1,1,1,ink)
     if kind=='clear' and outer+1<x1:rect(slot,outer+1,y0+1,1,1,ink)
 return {s:''.join(v) for s,v in groups.items()}


def render_svg(path,slot,output):
 output.parent.mkdir(parents=True,exist_ok=True)
 command=['inkscape',str(path),'--export-id='+slot,'--export-id-only','--export-area-page','--export-png-antialias=0','--export-filename='+str(output)]
 result=subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE);fallback=False
 if result.returncode and b'export-png-antialias' in result.stderr and b'Unknown option' in result.stderr:
  # Older Inkscape lacks the flag. Keep the SVG's crispEdges and normalize
  # only transparent edge coverage, never skin-colour filtering or fitting.
  command.remove('--export-png-antialias=0');fallback=True
  result=subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 if result.returncode:raise RuntimeError(result.stderr.decode('utf-8',errors='replace'))

 with Image.open(output) as im:
  a=np.array(im.convert('RGBA'));a[a[:,:,3]==0]=0
 if fallback:a[a[:,:,3]<128]=0;a[a[:,:,3]>=128,3]=255
 Image.fromarray(a).save(output,icc_profile=Path('/usr/share/color/icc/sRGB.icc').read_bytes())


def build():
 manifests=[]
 for part,presets in [('hair',HAIR),('face',FACES)]:
  template=json.loads((R/f'Art/Parts/P1-v1/eight-way-v1/{"hair-chestnut" if part=="hair" else "face-blue"}/asset.json').read_text())
  for style,cfg in presets.items():
   folder=OUT/(part+'-'+style);(folder/'editable').mkdir(parents=True,exist_ok=True);sources=[];paths={}
   for d in DIRS:
    svg=folder/f'editable/{d}.svg'
    if part=='hair':source=hair_svg(d,style);slots=['hair.front']
    else:
     groups=face_groups(d,style);slots=list(groups);source='<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96" shape-rendering="crispEdges">'+''.join(f'<g id="{s}">{v}</g>' for s,v in groups.items())+'</svg>\n'
    svg.write_text(source);sources.append(f'editable/{d}.svg');paths[d]={}
    for slot in slots:
     output=folder/f'masters/{d}/{slot}.png'
     if part=='face' and not groups[slot]:
      output.parent.mkdir(parents=True,exist_ok=True);Image.new('RGBA',(96,96)).save(output)
     else:render_svg(svg,slot,output)
     paths[d][slot]=output.relative_to(folder).as_posix()
   asset=copy.deepcopy(template);asset['id']='p1-custom-'+part+'-'+style+'-v1';asset['version']=cfg.get('version','1.0.1') if part=='hair' else '1.0.0';asset['sourceFiles']=sources+['authoring.json','palette.json']
   asset['bindings']=[{'direction':b['direction'],'clip':b['clip'],'frame':b['frame'],'layers':paths[b['direction']]} for b in template['bindings']]
   write(folder/'palette.json',{'colorSpace':'sRGB','roleColors':cfg.get('colors',{k:cfg[k] for k in ['eye','shadow','brow'] if k in cfg})});write(folder/'asset.json',asset);write(folder/'authoring.json',{'label':cfg['label'],'genderStyle':cfg['genderStyle'],'scope':'gender-styled appearance preset on unchanged shared body; not a separate female body','headCanvas':[96,96],'headToCanvasSource':'original motion, unchanged','slots':asset['slots'],'noSkinEarsJawOrBodyPixels':True,'fullEightDirections':True,'bindingCount':104,'uniqueDirectionalLayerPNGs':8*len(asset['slots']),'hairBackContractChanged':False,'artApproval':None,'runtimeImported':False})
   manifests.append({'id':asset['id'],'manifest':(folder/'asset.json').relative_to(R).as_posix()})
 cat=json.loads((R/'Art/Review/P1/chat-apparel-v2-b-eight-way-r1/catalog.json').read_text());cat['assets']+=manifests;write(D/'catalog.json',cat)
 return manifests


def review():
 c=art.Compositor(R,D/'catalog.json',R/'Art/Integration/P1-modular-eight-way-v1/motion.json');font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
 # Whole figures at original scale, so facial proportions are judged in context.
 for face in FACES:
  board=Image.new('RGB',(6*256,8*280),'#1e3428');dr=ImageDraw.Draw(board)
  for col,(hair,cfg) in enumerate(HAIR.items()):
   for row,d in enumerate(DIRS):
    im=c.render(art.BASE,['p1-eight-way-lower-v1','p1-chat-starlight-armor-v2','p1-custom-hair-'+hair+'-v1','p1-custom-face-'+face+'-v1'],d,'idle',0)
    board.paste(im,(col*256,row*280),im);dr.text((col*256+5,row*280+258),f'{cfg["label"]} / {face} / {d}',font=font,fill='#f3e1b8')
  board.save(D/f'all-hair-{face}-whole-body-1x.png')
 # One complete eight-way walk per hairstyle with an appropriate default face;
 # face/hair remain independent choices, not a new whole-character bitmap.
 for hair,cfg in HAIR.items():
  bindings=load('head_review_shared_appearance',R/'scripts/appearance-scene-binding.py').SceneBindings();choice=bindings.preset(hair)
  frames=[]
  for n in range(1,9):
   board=Image.new('RGB',(4*256,2*280),'#1e3428')
   for i,d in enumerate(DIRS):
    im=c.render(art.BASE,bindings.walking_parts(choice),d,'walk',n);board.paste(art.cell(im,d),(i%4*256,i//4*280))
   frames.append(board)
  art.gif(frames,D/f'{hair}-eight-way-normal.gif',120)
 print('Six hair styles and four face sets exported with eight directional masters and original 104 bindings each.',flush=True)


def battle_overrides():
 """Register new independent heads to the existing battle head, not the walk jaw.
 Constant feature registration handles the slightly different battle artwork;
 all features still follow one unmodified torso/head pose, never independent time.
 """
 battle=load('custom_heads_battle',R/'scripts/build-chat-apparel-b-battle.py')
 for style in HAIR:
  folder=OUT/('hair-'+style);im=Image.new('RGBA',(256,256));im.alpha_composite(Image.open(folder/'masters/right/hair.front.png').convert('RGBA'),(82,60));art.save(im,folder/'battle/hair.png')
  write(folder/'battle/registration.json',{'sourceMaster':'masters/right/hair.front.png','translation':[82,60],'battlePart':'MeadowBattleHeroHair','sameUnmodifiedTorsoPose':True,'canvasBakedBowHandling':'transform fresh local head by original torso, do not transform an already baked tile twice'})
 for style in FACES:
  folder=OUT/('face-'+style);combined=Image.new('RGBA',(256,256));poses={'face.eyes':(82,65),'face.brows':(82,64),'face.mouth':(79,65)}
  for slot,offset in poses.items():
   im=Image.new('RGBA',(256,256));im.alpha_composite(Image.open(folder/f'masters/right/{slot}.png').convert('RGBA'),offset);art.save(im,folder/'battle'/(slot+'.png'));combined.alpha_composite(im)
  # Preserve the original battle nose profile. It is a narrow nose component,
  # not a cheek/ear/jaw skin patch or a different character's full face.
  nose=Image.new('RGBA',(256,256));original=battle.asset('MeadowBattleHeroFace');nose.paste(original.crop((146,116,153,125)),(146,116));art.save(nose,folder/'battle/face.nose.png');combined.alpha_composite(nose);art.save(combined,folder/'battle/face.png')
  write(folder/'battle/registration.json',{'sourceMasters':'masters/right/','featureTranslations':poses,'noseGeometry':'original MeadowBattleHeroFace [146,116,153,125] nose component','battlePart':'MeadowBattleHeroFace','sameUnmodifiedTorsoPose':True,'headSkinEarJawChanged':False})
 # Whole character comparison, with equal-scale head details as supplementary
 # evidence. The full figure remains the primary composition reference.
 bindings=load('head_battle_shared_appearance',R/'scripts/appearance-scene-binding.py').SceneBindings()
 board=Image.new('RGB',(6*256,2*280),'#1e3428');dr=ImageDraw.Draw(board);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
 for col,(hair,cfg) in enumerate(HAIR.items()):
  renderer=battle.Renderer.for_appearance(bindings,bindings.preset(hair))
  for row,weapon in enumerate(['trainingSword','huntingBow']):
   im=renderer.actor(weapon,'idle',0);board.paste(im,(col*256,row*280),im);dr.text((col*256+5,row*280+258),cfg['label']+' '+weapon,font=font,fill='#f3e1b8')
 board.save(D/'battle-head-registration-1x.png')
 frames=[]
 for i in range(86):
  age=i*.02
  p=max(0,age)/.86*((.86-.4)/1.2) if age<=.86 else float(np.clip((age-.4-min(.1,max(0,age-1.048)))/1.2,0,1))
  frame=Image.new('RGB',(6*256,280),'#1e3428');dr=ImageDraw.Draw(frame)
  for col,(hair,cfg) in enumerate(HAIR.items()):
   renderer=battle.Renderer.for_appearance(bindings,bindings.preset(hair))
   im=renderer.actor('huntingBow','attack',p);frame.paste(im,(col*256,0),im);dr.text((col*256+5,258),cfg['label'],font=font,fill='#f3e1b8')
  frames.append(frame)
 art.gif(frames,D/'six-heads-bow-normal.gif',20)


if __name__=='__main__':
 if '--review-only' not in sys.argv:build()
 review()
 battle_overrides()
