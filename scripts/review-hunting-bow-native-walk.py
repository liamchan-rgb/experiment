from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/P1/hunting-bow-v1';A=R/'Sources/Resources/Assets.xcassets';rig=json.loads((R/'Sources/Resources/hero-gait.json').read_text());font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',18);dirs=['down','left','up','right','down-right','down-left','up-left','up-right']
for p in rig['modularP1']['loadouts']:
 for di,d in enumerate(dirs):
  name=p['weaponAtlasNames']['huntingBow'][di//4];atlas=Image.open(A/(name+'.imageset')/(name+'.png')).convert('RGBA');im=Image.new('RGB',(1024,4*280),'#20372a');dr=ImageDraw.Draw(im)
  for col in range(13):
   tile=atlas.crop((col*256,di%4*256,(col+1)*256,(di%4+1)*256));x,y=col%4*256,col//4*280;im.paste(tile,(x,y),tile);dr.text((x+8,y+256),f'{p["id"]} {d} {col:02}',font=font,fill='#ffedc7')
  for scale in [1,2]:im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).save(D/f'native-{p["id"]}-{d}-{scale}x.png')
for name in ['walk','transitions']:
 im=Image.open(D/(name+'-normal.gif'))
 for page in range(math.ceil(im.n_frames/2)):
  out=Image.new('RGB',(1024,1192),'#20372a')
  for j in range(2):
   i=page*2+j
   if i>=im.n_frames:break
   im.seek(i);out.paste(im.convert('RGB').resize((1024,596),Image.Resampling.NEAREST),(0,j*596))
  out.save(D/f'{name}-decoded-{page+1:02}.jpg',quality=94)
print('32 native bow boards and11decoded walking pages ready')
