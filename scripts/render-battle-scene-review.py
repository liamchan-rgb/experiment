#!/usr/bin/env python3
"""Offline artwork composition, not UIKit/GPU execution or a device screenshot."""
from pathlib import Path
import runpy,math,json
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'Sources/Resources/Assets.xcassets';OUT=ROOT/'Media/Build37';OUT.mkdir(exist_ok=True)
mod=runpy.run_path(str(ROOT/'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py'))
render=mod['render'];sample=mod['sample'];W=700;H=round(W*1201/1309)
def asset(n):
 d=ASSETS/f'{n}.imageset';filename=json.loads((d/'Contents.json').read_text())['images'][0]['filename'];return Image.open(d/filename).convert('RGBA')
plate=Image.new('RGBA',(W,H))
for n,blur,sat,contrast in [('MeadowCampFarForest',3,.94,.95),('MeadowCampGround',1.5,.90,.96),('MeadowCampMidground',1.5,1,.96)]:
 im=asset(n);a=im.getchannel('A');im=ImageEnhance.Contrast(ImageEnhance.Color(im.convert('RGB')).enhance(sat)).enhance(contrast).convert('RGBA');im.putalpha(a);im=im.filter(ImageFilter.GaussianBlur(blur));plate.alpha_composite(im.resize((W,H),Image.Resampling.LANCZOS))
foreground=asset('MeadowCampForeground').resize((W,H),Image.Resampling.LANCZOS)
hs=H*.17/132;es=H*.33/232
hx=W*.29-123*hs;hy=H*.69-214*hs;ex=W*.65-178.5*es;ey=H*.685-241*es
motion=json.loads((ROOT/'Art/Scenes/MeadowBattle/enemies/forest-warden-motion-v1/motion.json').read_text())
enemies=[Image.open(ROOT/f'Art/Scenes/MeadowBattle/enemies/forest-warden-motion-v1/frames/{i:02}.png').convert('RGBA') for i in range(8)]
def pulse(p,start,peak,end):
 if p<start or p>end:return 0
 t=(p-start)/(peak-start) if p<peak else (end-p)/(end-peak);return t*t*(3-2*t)
def approach(p):
 if p<.12 or p>=1:return 0
 if .4<=p<=.66:return 1
 t=(p-.12)/.28 if p<.4 else (1-p)/.34;return t*t*(3-2*t)
def point(q,part):
 pivot,offset,a=part;x,y=q[0]-pivot[0],q[1]-pivot[1];c,s=math.cos(a),math.sin(a)
 return pivot[0]+offset[0]+x*c-y*s,pivot[1]+offset[1]+x*s+y*c
contact=sample('attack',.54);tip=point((191,142),contact[0]['MeadowBattleHeroWeapon'])
reach=hx+(tip[0]+contact[1][0])*hs
travel=min(W*.22,max(0,ex+54*es-reach+W*.018))
def cast(image,x,y,scale,sole,contacts):
 # Exact source projection from MeadowBattleGroundingView; raster effects are
 # approximate Pillow equivalents of CGContext/Core Image, deliberately labelled.
 shadow=Image.new('RGBA',image.size,(9,11,6,0));shadow.putalpha(image.getchannel('A').point(lambda a:round(a*.34)))
 a=1/scale;b=-.38/(.15*scale);c=-x/scale+.38*y/(.15*scale)+.38*sole/.15
 d=0;e=-1/(.15*scale);f=y/(.15*scale)+1.15*sole/.15
 out=shadow.transform((W,H),Image.Transform.AFFINE,(a,b,c,d,e,f),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(2.5*scale))
 con=Image.new('RGBA',(W,H));dr=ImageDraw.Draw(con)
 for px,py in contacts:
  cx,cy=x+px*scale,y+py*scale;r=12*scale;dr.ellipse((cx-r,cy-r*.38,cx+r,cy+r*.38),fill=(5,9,4,110))
 out.alpha_composite(con.filter(ImageFilter.GaussianBlur(2*scale)));return out
seed=Image.new('RGB',(1400,700),'#203627');seed.paste(plate.convert('RGB'),(0,0));seed.paste(render('idle',0).resize((512,512),Image.Resampling.NEAREST).convert('RGB'),(700,0));seed.paste(enemies[0].convert('RGB'),(700,444))
palette=seed.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
allframes=[];sheets=[]
for kind in ['strike','enemyStrike','guard','heal','victory','defeat']:
 duration={'strike':1200,'enemyStrike':1320,'guard':960,'heal':960,'victory':1080,'defeat':1080}[kind]
 count=duration//40
 frames=[]
 for i in range(count):
  # 40ms ordinary playback, sampled by elapsed time from the runtime clip JSON.
  elapsed=i*40; p=min(1,elapsed/(960 if kind=='enemyStrike' else duration));clip={'strike':'attack','enemyStrike':'idle','guard':'guard','heal':'idle','victory':'victory','defeat':'defeat'}[kind]
  hp=p
  if kind=='enemyStrike' and p>=.46:clip='hit';hp=min(1,(elapsed-960*.46)/840)
  art=render(clip,hp);pose=sample(clip,hp);root=pose[1];sole=pose[3]+root[1];contacts=[(q[0]+root[0],q[1]+root[1]) for q in pose[4]]
  tx=travel*approach(p) if kind=='strike' else 0
  etx=-(max(0,ex+42*es-(hx+128*hs)-W*.015))*pulse(p,.08,.48,.98) if kind=='enemyStrike' else W*.017*pulse(p,.48,.58,.86) if kind=='strike' else 0
  n=min(7,int(p*8)) if kind=='enemyStrike' else 0;enemy=enemies[n]
  frame=plate.copy();frame.alpha_composite(cast(art,hx+tx,hy,hs,sole,contacts));frame.alpha_composite(cast(enemy,ex+etx,ey,es,240,motion['contacts'][n]))
  frame.alpha_composite(art.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(hx+tx),round(hy)))
  if kind=='victory':enemy=enemy.copy();enemy.putalpha(enemy.getchannel('A').point(lambda a:round(a*(1-.8*p))))
  frame.alpha_composite(enemy.resize((round(384*es),round(256*es)),Image.Resampling.NEAREST),(round(ex+etx),round(ey)))
  frame.alpha_composite(foreground)
  dr=ImageDraw.Draw(frame);dr.rectangle((0,0,W,29),fill=(16,31,21,235));dr.text((10,9),f'OFFLINE ART REVIEW - {kind} - {i*40}ms - no GPU/device capture',fill='white')
  dr.text((12,H-20),'Same art / pose JSON / canvas registration; raster lighting is approximate.',fill='white')
  frames.append(frame.convert('RGB'))
 encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
 encoded[0].save(OUT/f'{kind}-scene-offline.gif',save_all=True,append_images=encoded[1:],duration=40,loop=0,disposal=1,optimize=False)
 allframes.extend(frames)
 for i in [0,count//2,count-1]:sheets.append(frames[i])
encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in allframes]
encoded[0].save(OUT/'battle-actions-offline.gif',save_all=True,append_images=encoded[1:],duration=40,loop=0,disposal=1,optimize=False)
sheet=Image.new('RGB',(W*3,H*6))
for i,f in enumerate(sheets):sheet.paste(f,((i%3)*W,(i//3)*H))
sheet.save(OUT/'battle-scene-contact-sheet.png')
print('Offline battle scene GIFs rendered: sources, JSON and registered silhouettes; not UIKit/GPU/physical-device screenshots.')
