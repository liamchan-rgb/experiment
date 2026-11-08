#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Review/P1/great-sword-demo-v1';D.mkdir(parents=True,exist_ok=True)
rig=json.loads((R/'Sources/Resources/hero-gait.json').read_text());font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14);dirs=['down','left','up','right','down-right','down-left','up-left','up-right'];atlases={}
for preset in rig['modularP1']['loadouts']:
 for n in preset['weaponAtlasNames']['greatSword']:atlases[n]=Image.open(A/(n+'.imageset')/(n+'.png')).convert('RGBA')
 for di,d in enumerate(dirs):
  name=preset['weaponAtlasNames']['greatSword'][di//4];atlas=atlases[name];board=Image.new('RGB',(1024,1120),'#20372a')
  for c in range(13):
   im=atlas.crop((c*256,di%4*256,(c+1)*256,(di%4+1)*256));x=c%4*256;y=c//4*280;board.paste(im,(x,y),im);ImageDraw.Draw(board).text((x+6,y+258),f'{preset["id"]} {d} {c:02}',font=font,fill='#f0e4b6')
  board.save(D/f'{preset["id"]}-{d}-1x.png');board.resize((2048,2240),Image.Resampling.NEAREST).save(D/f'{preset["id"]}-{d}-2x.png')
reports=[]
for action,columns in [('walk',list(range(1,9))),('transitions',[0,9,10,1,2,3,4,5,6,7,8,11,12,0])]:
 frames=[]
 for c in columns:
  board=Image.new('RGB',(1024,1120),'#20372a')
  for pi,preset in enumerate(rig['modularP1']['loadouts']):
   for di,d in enumerate(dirs):
    n=preset['weaponAtlasNames']['greatSword'][di//4];im=atlases[n].crop((c*256,di%4*256,(c+1)*256,(di%4+1)*256));x=di%4*256;y=(di//4+pi*2)*280;board.paste(im,(x,y),im);ImageDraw.Draw(board).text((x+6,y+258),f'{preset["id"]} {d}',font=font,fill='#f0e4b6')
  frames.append(board)
 pal=Image.new('RGB',(1024*4,1120*2))
 for i,f in enumerate(frames[:8]):pal.paste(f,(i%4*1024,i//4*1120))
 pal=pal.quantize(colors=256);enc=[f.quantize(palette=pal,dither=Image.Dither.NONE) for f in frames];p=D/(action+'-normal.gif');enc[0].save(p,save_all=True,append_images=enc[1:],duration=120,loop=0,disposal=2,optimize=False)
 gif=Image.open(p)
 for page in range(math.ceil(gif.n_frames/2)):
  out=Image.new('RGB',(2048,1144),'#20372a')
  for j in range(2):
   n=page*2+j
   if n>=gif.n_frames:break
   gif.seek(n);out.paste(gif.convert('RGB'),(j*1024,0));ImageDraw.Draw(out).text((j*1024+6,1122),f'{n} / {gif.info["duration"]}ms',font=font,fill='#f0e4b6')
  out.save(D/f'{action}-decoded-{page+1:02}.jpg',quality=96)
 reports.append({'file':p.name,'frames':gif.n_frames,'frameDurationMs':120,'bytes':p.stat().st_size})
(D/'review.json').write_text(json.dumps({'scope':'208 native modular cells; two original appearances; gait timing preserved','animations':reports,'userApproval':None},indent=2)+'\n');print('208 native walking cells,32 native/enlarged boards and2normalGIFs ready.')
