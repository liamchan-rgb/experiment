#!/usr/bin/env python3
"""Mechanical fixed-scale registration of the authored 4x2 ImageGen sheet."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/Scenes/MeadowBattle/enemies/forest-warden-motion-v1'
SOURCE=OUT/'reference/cleanup-sheet.png'
im=Image.open(SOURCE).convert('RGBA')
cols=[round(i*im.width/4) for i in range(5)];rows=[round(i*im.height/2) for i in range(3)]
cells=[]
for i in range(8):
 cell=im.crop((cols[i%4],rows[i//4],cols[i%4+1],rows[i//4+1]))
 # Common pixel-art export rule: binary alpha, no opaque background or color painting.
 alpha=cell.getchannel('A').point(lambda a:255 if a>=128 else 0);cell.putalpha(alpha)
 cells.append(cell)
b0=cells[0].getbbox(); scale=232/(b0[3]-b0[1]); target_hip=178.5+(294-(b0[0]+b0[2])/2)*scale
hips=[294,303,309,300,302,308,310,302]
frames=[];contacts=[];register=[]
(OUT/'frames').mkdir(exist_ok=True)
for i,cell in enumerate(cells):
 b=cell.getbbox(); resized=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.NEAREST)
 pos=(round(target_hip-hips[i]*scale),240-round((b[3]-1)*scale))
 frame=Image.new('RGBA',(384,256));frame.paste(resized,pos)
 if i==7:frame=frames[0].copy() # Exact recovered idle closes the clip.
 frames.append(frame);frame.save(OUT/f'frames/{i:02}.png')
 a=frame.getchannel('A'); box=a.getbbox(); xs=[]
 for x in range(384):
  if any(a.getpixel((x,y))>0 for y in range(236,241)):xs.append(x)
 groups=[]
 for x in xs:
  if not groups or x-groups[-1][-1]>7:groups.append([])
  groups[-1].append(x)
 feet=[[round(sum(g)/len(g),2),240] for g in groups if len(g)>=3]
 contacts.append(feet)
 register.append({'frame':i,'sourceCell':[cols[i%4],rows[i//4],cols[i%4+1],rows[i//4+1]],'scale':scale,'translation':list(pos),'alphaBounds':box,'contacts':feet})
sheet=Image.new('RGBA',(384*8,256))
for i,f in enumerate(frames):sheet.paste(f,(384*i,0))
sheet.save(OUT/'attack-strip.png')
gifs=[]
for f in frames:
 bg=Image.new('RGBA',(384,256),'#203627'); bg.alpha_composite(f);gifs.append(bg.convert('RGB'))
gifs[0].save(OUT/'attack.gif',save_all=True,append_images=gifs[1:],duration=120,loop=0,disposal=2)
contact=Image.new('RGB',(384*4,280*2),'#203627');draw=ImageDraw.Draw(contact)
for i,f in enumerate(gifs):contact.paste(f,((i%4)*384,(i//4)*280));draw.text(((i%4)*384+8,(i//4)*280+258),f'{i:02} - {i*120} ms',fill='white')
contact.save(OUT/'contact-sheet.png')
meta={'format':1,'canvasPx':[384,256],'source':str(SOURCE.relative_to(ROOT)),'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'frameMs':120,'contacts':contacts,'registration':register,'recoveryCopiesIdle':True,'alphaExport':'binary alpha at 128; RGB unchanged; fixed shared scale, no per-pose fitting'}
(OUT/'motion.json').write_text(json.dumps(meta,indent=2)+'\n')
assets=ROOT/'Sources/Resources/Assets.xcassets'
def imageset(name,path):
 d=assets/f'{name}.imageset';d.mkdir(exist_ok=True);shutil.copyfile(path,d/f'{name}.png');(d/'Contents.json').write_text(json.dumps({'images':[{'idiom':'universal','filename':f'{name}.png'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')
imageset('MeadowBattleWardenAttackSheet',OUT/'attack-strip.png')
imageset('MeadowBattleForestWarden',OUT/'frames/00.png')
d=assets/'MeadowBattleWardenMotion.dataset';d.mkdir(exist_ok=True);shutil.copyfile(OUT/'motion.json',d/'motion.json');(d/'Contents.json').write_text(json.dumps({'data':[{'idiom':'universal','filename':'motion.json'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')
print('Packed 8 registered frames; scale',scale,'contacts',contacts)
