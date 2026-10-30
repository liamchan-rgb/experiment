#!/usr/bin/env python3
"""Native jacket-only correction: flat chest, coherent leather belt and cloth hem."""
from pathlib import Path
from statistics import median
import hashlib,json,shutil
from PIL import Image,ImageDraw,ImageChops
R=Path(__file__).resolve().parents[1]
old=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r5'
D=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r6';D.mkdir(exist_ok=True)
frozen=['drawing-hand.png','grip-hand.png','farArm.png','nearUpperArm.png','nearForeArm.png']
for n in frozen:shutil.copyfile(old/n,D/n)
source_path=R/'Art/Parts/P1-Battle/right-idle-v3/outfit-forester/wardrobe.png'
core_path=R/'Sources/Resources/Assets.xcassets/MeadowBattleBowWardrobeCore.imageset/MeadowBattleBowWardrobeCore.png'
source=Image.open(source_path).convert('RGBA');core=Image.open(core_path).convert('RGBA')
def blue(c):return c[3]>200 and c[2]>c[0]*1.3 and c[2]>c[1]*1.12 and c[2]>45
fabric=[(x,y,source.getpixel((x,y))) for y in range(139,159) for x in range(114,140) if blue(source.getpixel((x,y)))]
palette=sorted({c[:3] for x,y,c in fabric})
def donor(x,y):return min(fabric,key=lambda p:(p[0]-x)**2+(p[1]-y)**2)[2]
def native_color(rgb):return min(palette,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))+(255,)
outline=Image.new('L',(256,256));od=ImageDraw.Draw(outline)
# The chest no longer advances in front of the shoulder line before receding.
od.polygon([(116,135),(126,135),(137,139),(141,143),(140,150),(139,156),(138,162),(137,167),(135,172),(116,171),(116,163),(115,155),(114,148)],fill=255)
coat=Image.new('RGBA',(256,256))
for y in range(135,173):
 xs=[x for x in range(256) if outline.getpixel((x,y))]
 if not xs:continue
 left,right=min(xs),max(xs)
 for x in xs:
  if x in [left,right]:color=(27,44,65,255)
  else:
   u=(x-left)/max(1,right-left);sx=129+u*6;sy=144+(y-140)*.32
   c=donor(sx,sy)
   local=[donor(sx+dx,sy+dy) for dx,dy in [(-1,0),(0,-1),(0,0),(1,0),(0,1)]]
   # Transfer only fine native fabric variation, not the old rounded arm lighting.
   grain=[max(-5,min(5,c[k]-median(q[k] for q in local))) for k in range(3)]
   shade=.83 if u<.16 else .93 if u>.86 else 1
   if 145<=y<=148:shade*=.94
   color=native_color([(base+grain[k]*.55)*shade for k,base in enumerate((47,84,139))])
  coat.putpixel((x,y),color)
# Retain only the original neckline, not the damaged belt and old sleeve cutout.
mask=Image.new('L',(256,256));ImageDraw.Draw(mask).rectangle((112,126,146,141),fill=255)
neckline=core.copy();neckline.putalpha(ImageChops.multiply(neckline.getchannel('A'),mask));coat.alpha_composite(neckline)
d=ImageDraw.Draw(coat)
# Narrow, receding placket; no forward bulge and no round specular patch.
seam=[(137,144),(137,150),(136,156),(135,162),(134,166)]
d.line(seam,fill=(27,43,55,255),width=3)
d.line(seam,fill=(190,171,114,255),width=2)
d.line([(x-1,y) for x,y in seam],fill=(236,225,179,255),width=1)
d.line([(117,149),(120,152)],fill=native_color((40,72,121)),width=1)
d.line([(118,150),(120,151)],fill=native_color((50,88,146)),width=1)
d.line([(119,156),(122,158),(126,159)],fill=native_color((43,78,131)),width=1)
d.line([(120,155),(123,157)],fill=native_color((50,89,146)),width=1)
# Complete cloth hem, leather band and clasp replace overlapping legacy fragments.
def poly(c,p):d.polygon(p,fill=c)
poly('#24313b',[(115,165),(120,167),(128,169),(132,169),(136,168),(138,169),(137,172),(132,173),(125,173),(114,170),(114,167)])
poly('#d7c995',[(115,167),(120,169),(128,171),(132,171),(136,169),(137,170),(135,172),(125,172),(115,169)])
d.line([(115,167),(120,169),(128,171),(132,171),(136,169)],fill='#f1e6bb',width=1)
poly('#3e2b1a',[(115,160),(121,162),(129,164),(135,164),(138,166),(138,170),(132,171),(124,169),(116,166),(115,164)])
poly('#9d652c',[(116,162),(122,164),(130,166),(135,166),(136,167),(136,169),(130,169),(124,167),(116,165)])
d.line([(116,162),(122,164),(130,166),(133,166)],fill='#c18a43',width=1)
d.line([(116,165),(124,168),(130,170),(133,170)],fill='#684323',width=1)
# One continuous gold ring and a dark leather opening, aligned with the band.
d.rectangle((132,165,137,170),fill='#44321e')
d.rectangle((133,166,137,170),fill='#d8bd77')
d.rectangle((134,167,136,169),fill='#6e4826')
d.line((133,166,137,166),fill='#f0dea0',width=1)
d.point((135,168),fill='#e3c783')
for y in range(256):
 for x in range(256):
  c=coat.getpixel((x,y));coat.putpixel((x,y),c[:3]+(255,) if c[3]>=128 else (0,0,0,0))
coat.save(D/'torso.png')
p=json.loads((old/'pose.json').read_text());p['surfaces']=[s for s in p['surfaces'] if s['group']!='torso']
for y in range(256):
 x=0
 while x<256:
  c=coat.getpixel((x,y))
  if not c[3]:x+=1;continue
  end=x
  while end+1<256 and coat.getpixel((end+1,y))==c:end+=1
  p['surfaces'].append({'group':'torso','color':c[0]*65536+c[1]*256+c[2],'points':[{'x':x,'y':y},{'x':end,'y':y},{'x':end,'y':y},{'x':x,'y':y}]});x=end+1
(D/'pose.json').write_text(json.dumps(p,indent=2)+'\n')
sources=[source_path,core_path]
(D/'authoring.json').write_text(json.dumps({'method':'flatten chest contour and lighting; transfer only fine existing fabric detail; author one complete native belt/clasp/hem instead of legacy fragments','sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'script':'scripts/author-bow-jacket-r6.py','frozenFrom':str(old.relative_to(R)),'frozenParts':frozen,'runtimeImported':False,'userApproved':False},indent=2)+'\n')
print('Authored jacket chest and coherent native belt/hem; hands and arms frozen.')
