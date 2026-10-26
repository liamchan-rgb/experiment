#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Equipment/b2-batch-v1'
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14)
names=[('greatSword','重剑'),('legendaryStaff','传奇权杖'),('leatherArmor','皮甲'),('runeArmor','符文甲')]
def frame(col):
 out=Image.new('RGB',(1024,560),'#20372a');draw=ImageDraw.Draw(out)
 for x,(name,title) in enumerate(names):
  atlas=Image.open(D/name/'forester-walk.png')
  for row,direction in enumerate([0,3]):
   im=atlas.crop((col*256,direction*256,(col+1)*256,(direction+1)*256));out.paste(im,(x*256,row*280),im);draw.text((x*256+8,row*280+255),title+(' · 正下' if row==0 else ' · 左上'),font=font,fill='#ffedc7')
 return out
frames=[frame(i+1) for i in range(8)]
frames[0].save(D/'batch-walk-normal.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=True)
frame(0).save(D/'batch-standing.png')
