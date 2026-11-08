#!/usr/bin/env python3
"""Rebuild only the bow keyframe's jacket from the original game's cloth pixels."""
from pathlib import Path
import json,math,shutil,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
old=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r4';D=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r5';D.mkdir(exist_ok=True)
for n in ['drawing-hand.png','grip-hand.png','farArm.png','nearUpperArm.png','nearForeArm.png']:shutil.copyfile(old/n,D/n)
source=Image.open(R/'Art/Parts/P1-Battle/right-idle-v3/outfit-forester/wardrobe.png').convert('RGBA')
core=Image.open(R/'Sources/Resources/Assets.xcassets/MeadowBattleBowWardrobeCore.imageset/MeadowBattleBowWardrobeCore.png').convert('RGBA')
# Exposed fabric from the original jacket/sleeve has the existing sprite's palette and weave.
def blue(c):return c[3]>200 and c[2]>c[0]*1.3 and c[2]>c[1]*1.12 and c[2]>45
fabric=[(x,y,source.getpixel((x,y))) for y in range(139,159) for x in range(114,140) if blue(source.getpixel((x,y)))]
def fabric_pixel(x,y):
 ix,iy=round(x),round(y);c=source.getpixel((ix,iy))
 if blue(c):return c
 return min(fabric,key=lambda p:(p[0]-x)**2+(p[1]-y)**2)[2]
outline=Image.new('L',(256,256));dd=ImageDraw.Draw(outline)
dd.polygon([(116,135),(126,135),(137,139),(142,143),(143,147),(141,152),(140,158),(138,165),(137,169),(134,173),(115,170),(116,164),(115,156),(114,148)],fill=255)
coat=Image.new('RGBA',(256,256));rows={}
for y in range(135,174):
 xs=[x for x in range(256) if outline.getpixel((x,y))];rows[y]=(min(xs),max(xs))
 for x in xs:
  left,right=rows[y];u=(x-left)/max(1,right-left)
  if x in [left,right] or y==173:c=(27,44,65,255)
  else:
   sx=115+u*22;sy=min(157,140+max(0,y-139)*.56)
   c=fabric_pixel(sx,sy)
   # Restrained back-plane and underarm shading, rather than a large belly highlight.
   factor=.84 if u<.16 else .96 if u>.84 else 1
   if 145<=y<=148:factor*=.90
   c=tuple(round(v*factor) for v in c[:3])+(255,)
  coat.putpixel((x,y),c)
# Preserve the exact original neckline/front trim and belt pixels, excluding old arm fragments.
mask=Image.new('L',(256,256));dm=ImageDraw.Draw(mask)
dm.rectangle((112,126,146,141),fill=255)
dm.rectangle((114,160,138,174),fill=255)
from PIL import ImageChops
original=core.copy();original.putalpha(ImageChops.multiply(original.getchannel('A'),mask));coat.alpha_composite(original)
# Recover the original belt clasp, which was removed from the old sword-arm cutout.
buckle=source.crop((130,166,138,172));coat.alpha_composite(buckle,(130,166))
# Short cloth creases use sampled original blue tones, at the waist and beneath the arm.
d=ImageDraw.Draw(coat)
# Continue the original narrow placket where the old bent sword sleeve concealed it.
seam=[(138,143),(139,149),(138,155),(137,161),(135,166)]
d.line(seam,fill=(27,43,55,255),width=3)
d.line(seam,fill=(193,172,113,255),width=2)
d.line([(x-1,y) for x,y in seam],fill=(239,226,175,255),width=1)
d.line([(116,148),(119,151),(123,153)],fill=fabric_pixel(115,153),width=1)
d.line([(117,150),(120,152)],fill=fabric_pixel(120,142),width=1)
d.line([(120,160),(123,162),(126,163)],fill=fabric_pixel(125,153),width=1)
for y in range(256):
 for x in range(256):
  c=coat.getpixel((x,y))
  # Old neckline/belt cutouts must not reintroduce the previous loose side contour.
  if 142<=y<=165 and not outline.getpixel((x,y)):c=(0,0,0,0)
  coat.putpixel((x,y),c[:3]+(255,) if c[3]>=128 else (0,0,0,0))
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
sources=['Art/Parts/P1-Battle/right-idle-v3/outfit-forester/wardrobe.png','Sources/Resources/Assets.xcassets/MeadowBattleBowWardrobeCore.imageset/MeadowBattleBowWardrobeCore.png']
(D/'authoring.json').write_text(json.dumps({'method':'reuse original native jacket pixels; fitted underarm, waist and placket; no image generation','sources':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in sources},'script':'scripts/author-bow-jacket-r5.py','frozenFrom':str(old.relative_to(R)),'frozenParts':['drawing-hand.png','grip-hand.png','farArm.png','nearUpperArm.png','nearForeArm.png'],'runtimeImported':False,'userApproved':False},indent=2)+'\n')
print('Authored native jacket from existing fabric/trim; hand and arm files copied unchanged.')
