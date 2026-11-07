from pathlib import Path
import json,math,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label,find_objects,binary_dilation,map_coordinates
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';O=R/'Art/Monsters/bestiary-v1';O.mkdir(parents=True,exist_ok=True)
source=O/'generated-master-atlas.png';slime=O/'slime-complete-master.png'
im=Image.open(source);arr=np.array(im);ids,n=label(arr[:,:,3]>16);cc=[]
for i,sl in enumerate(find_objects(ids),1):
 if sl and (ids[sl]==i).sum()>1000:cc.append((i,sl))
order=['goblinArcher','wolf','slime','stoneGuardian','caveTroll','ruinDragon'];parts={}
for name,(i,sl) in zip(order,cc):
 mask=binary_dilation(ids==i,iterations=2);b=arr.copy();b[~mask]=0
 crop=Image.fromarray(b).crop(Image.fromarray(mask).getbbox());parts[name]=crop
s=Image.open(slime);parts['slime']=s.crop(s.getchannel('A').point(lambda a:255 if a>16 else 0).getbbox())
names=['slime','wolf','goblinArcher','stoneGuardian','caveTroll','ruinDragon'];titles=['捣蛋史莱姆','森林狼','哥布林弓手','石像守卫','洞穴巨魔','遗迹魔龙'];clips={'idle':12,'attack':24,'cast':12,'hurt':8};deathCount=40
Y,X=np.mgrid[:256,:384].astype(float);upper=np.clip((240-Y)/210,0,1);foot=np.clip((240-Y)/40,0,1)
def gauss(x,y,rx,ry):return np.exp(-((X-x)/rx)**2-((Y-y)/ry)**2)*foot
def pulse(t,a,b,c):
 def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
 return smooth((t-a)/(b-a)) if t<b else 1-smooth((t-b)/(c-b))
def warped(master,name,clip,t):
 dy=np.zeros_like(X);dx=np.zeros_like(X)
 if clip=='idle':
  wave=math.sin(t*2*math.pi);dy=-wave*upper*(1.4 if name=='slime' else .7)
  if name=='ruinDragon':dy-=gauss(250,70,105,100)*wave*1.6
 elif clip=='attack':
  prep=pulse(t,0,.23,.43);hit=pulse(t,.28,.46,.78);power=hit-.38*prep
  if name=='slime':
   dx=(X-178.5)*(.065*prep-.04*hit)*foot;dy=(240-Y)*(.12*prep-.07*hit)*foot
  elif name=='wolf':dx=-10*power*gauss(110,140,110,80);dy=5*power*gauss(100,110,100,75)
  elif name=='goblinArcher':dx=-2*power*gauss(120,120,75,65)+3*power*gauss(238,115,38,45)
  elif name=='stoneGuardian':dx=-13*power*gauss(110,150,90,85);dy=-5*power*gauss(100,180,65,60)
  elif name=='caveTroll':dx=-9*power*gauss(95,185,95,60);dy=-14*power*gauss(85,200,100,60)
  else:dx=-9*power*gauss(100,140,90,90);dy=5*power*gauss(95,130,75,70)-4*hit*gauss(245,95,100,90)
 elif clip=='cast':
  p=math.sin(math.pi*t)**2;dy=-2*p*upper
  if name=='ruinDragon':dx=-4*p*gauss(95,130,90,90);dy-=4*p*gauss(250,75,95,90)
 elif clip=='hurt':
  p=pulse(t,0,.18,1);dx=7*p*upper;dy=3*p*upper
 # One continuous inverse field: no disjoint limbs or independently clipped clothes.
 xx=np.clip(np.rint(X-dx).astype(int),0,383);yy=np.clip(np.rint(Y-dy).astype(int),0,255)
 return Image.fromarray(np.array(master)[yy,xx])
def indexed(frame,pal):
 rgba=np.array(frame);rgb=frame.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE);a=np.array(rgb);a[rgba[:,:,3]<64]=255
 out=Image.fromarray(a,'P');out.putpalette(pal.getpalette());out.info['transparency']=255;return out
records=[]
for index,name in enumerate(names):
 crop=parts[name];ratio=min(328/crop.width,224/crop.height);size=(round(crop.width*ratio),round(crop.height*ratio));crop=crop.resize(size,Image.Resampling.NEAREST)
 master=Image.new('RGBA',(384,256));master.alpha_composite(crop,(round(178.5-crop.width/2),240-crop.height))
 # Fixed palette for every pose prevents quantization flicker.
 pal=master.convert('RGB').quantize(colors=255,method=Image.Quantize.MEDIANCUT);pal.putpalette(pal.getpalette()[:765]+[0,0,0]);master=indexed(master,pal).convert('RGBA')
 (O/name).mkdir(exist_ok=True);master.save(O/name/'master.png')
 frames=[];offsets={}
 for clip,count in clips.items():
  offsets[clip]={'offset':len(frames),'count':count}
  for i in range(count):frames.append(indexed(warped(master,name,clip,i/(count-1)),pal))
 sheet=Image.new('P',(384*8,256*7),255);sheet.putpalette(pal.getpalette());sheet.info['transparency']=255
 for i,f in enumerate(frames):sheet.paste(f,(i%8*384,i//8*256))
 asset='MeadowMonster'+name[0].upper()+name[1:]
 def imageset(tag,image):
  folder=A/(tag+'.imageset');folder.mkdir(parents=True,exist_ok=True);image.save(folder/(tag+'.png'),optimize=True)
  (folder/'Contents.json').write_text(json.dumps({'images':[{'idiom':'universal','filename':tag+'.png'}],'info':{'version':1,'author':'xcode'}})+'\n')
 imageset(asset+'Motion',sheet)
 # Deterministic 3px fragments follow a rightward wind; each species keeps its own silhouette and palette.
 body=np.array(master);tiles=[]
 for y in range(0,256,3):
  for x in range(0,384,3):
   tile=master.crop((x,y,min(x+3,384),min(y+3,256)))
   if tile.getbbox():
    seed=((x*73856093)^(y*19349663))&0xffff;tiles.append((x,y,tile,seed/65535))
 death=Image.new('P',(512*8,320*5),255);death.putpalette(pal.getpalette());death.info['transparency']=255
 for i in range(deathCount):
  t=i/(deathCount-1);canvas=Image.new('RGBA',(512,320))
  if i<deathCount-1:
   for x,y,tile,rng in tiles:
    delay=.10+.28*(x/384)+rng*.12;u=max(0,(t-delay)/(1-delay));fade=max(0,1-u*1.6)
    if fade<=0:continue
    piece=tile.copy();piece.putalpha(piece.getchannel('A').point(lambda a:round(a*fade)))
    dx=round(u*(88+38*rng));dy=round(-math.sin(u*math.pi)*(14+12*rng)+u*u*12)
    canvas.alpha_composite(piece,(x+dx,y+32+dy))
  f=indexed(canvas,pal);death.paste(f,(i%8*512,i//8*320))
 imageset(asset+'Death',death)
 # Contact centers from the actual bottom silhouette instead of four deer feet.
 alpha=np.array(master)[:,:,3];counts=(alpha[232:241]>64).sum(axis=0);runs=[];start=None
 for x,on in enumerate(counts>0):
  if on and start is None:start=x
  if start is not None and (not on or x==383):
   end=x if not on else x+1
   if end-start>=3:runs.append([round((start+end-1)/2,1),240])
   start=None
 if not runs:runs=[[178.5,240]]
 record={'id':name,'name':titles[index],'asset':asset,'canvas':[384,256],'anchor':[178.5,240],'deathCanvas':[512,320],'deathAnchor':[178.5,272],'scale':1.04 if name in ['caveTroll','ruinDragon'] else .88,'contacts':runs,'clips':offsets,'deathCount':deathCount,'sourceCropSize':list(parts[name].size)}
 record['hitAnchor']={'slime': [110, 158], 'wolf': [110, 158], 'goblinArcher': [198, 158], 'stoneGuardian': [183, 158], 'caveTroll': [190, 171], 'ruinDragon': [152, 171]}[name]
 records.append(record)
 print(name,master.getbbox(),len(tiles),flush=True)
(O/'manifest.json').write_text(json.dumps({'version':1,'displayTargetFPS':60,'attackSeconds':.96,'deathSeconds':.8,'records':records,'animationMethod':'registered continuous full-surface deformation; not separately redrawn limbs','sourceApproval':None,'appRun':False},ensure_ascii=False,indent=2)+'\n')
folder=A/'MeadowMonsterVisuals.dataset';folder.mkdir(exist_ok=True);shutil.copyfile(O/'manifest.json',folder/'motion.json');(folder/'Contents.json').write_text(json.dumps({'data':[{'idiom':'universal','filename':'motion.json'}],'info':{'version':1,'author':'xcode'}})+'\n')
# First full-body audit board at native sprite scale, with original hero size unaltered.
board=Image.new('RGB',(1152,640),'#1d3226');d=ImageDraw.Draw(board);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',20)
for i,record in enumerate(records):
 f=Image.open(O/record['id']/'master.png');x=i%3*384;y=i//3*320;board.paste(f,(x,y+36),f);d.text((x+10,y+5),record['name'],font=font,fill='#edd08b');d.line((x,y+276,x+383,y+276),fill='#6c7854')
board.save(O/'master-audit.jpg',quality=95)
