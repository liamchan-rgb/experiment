#!/usr/bin/env python3
"""Build full-body, normal-speed focused and transition review media."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]/'Art/Review/Equipment/b2-batch-v4';font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',16)
for direction,row in [('front',0),('left',2)]:
 frames=[]
 for n in range(1,9):
  out=Image.new('RGBA',(512,350),'#20372a');dr=ImageDraw.Draw(out)
  for col,(item,label) in enumerate([('leatherArmor','皮甲'),('runeArmor','符文甲')]):
   atlas=Image.open(R/item/'forester-walk.png').convert('RGBA');im=atlas.crop((n*256+64,row*256+56,n*256+192,row*256+220)).resize((256,328),Image.Resampling.NEAREST);out.alpha_composite(im,(col*256,0));dr.text((col*256+8,330),label+' · '+('正下' if direction=='front' else '正左'),font=font,fill='#ffedc7')
  frames.append(out.convert('RGB'))
 frames[0].save(R/f'batch-{direction}-walk-normal.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=True)
print('Front and left full-body walk GIFs, 8 frames x 120 ms')

from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parents[1]/'Art/Review/Equipment/b2-batch-v4';B=D/'contact-sheets';B.mkdir(exist_ok=True);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',12);dirs=['down','down-left','left','up-left','up','up-right','right','down-right'];entries=[1,4,4,4,4,0,0,0];atlases={item:Image.open(D/item/'forester-walk.png').convert('RGBA') for item in ['leatherArmor','runeArmor']}
def actor(item,row,col):
 im=atlases[item].crop((col*256+64,row*256+56,col*256+192,row*256+220));return im.resize((256,328),Image.Resampling.NEAREST)
for row,d in enumerate(dirs):
 entry=entries[row];first=1+entry;last=1+(entry+7)%8;cols=[0,9,10,first,last,11,12,0];labs=['idle','start1','start2','walk entry','walk exit','stop1','stop2','idle'];out=Image.new('RGBA',(1024,1400),'#20372a')
 for k,item in enumerate(['leatherArmor','runeArmor']):
  for i,(col,label) in enumerate(zip(cols,labs)):
   x=i%4*256;y=(2*k+i//4)*350;out.alpha_composite(actor(item,row,col),(x,y));ImageDraw.Draw(out).text((x+4,y+330),f'{item} {d} {label}',font=font,fill='white')
 out.save(B/f'transition-{d}.png')
 if d in ['down','left']:
  # Original gait phase, exactly two complete walks between both transitions.
  seq=[0,9,10]+[1+(entry+i)%8 for i in range(16)]+[11,12,0];durations=[480]+[120]*20+[480];frames=[]
  for col in seq:
   im=Image.new('RGBA',(512,350),'#20372a')
   for k,item in enumerate(['leatherArmor','runeArmor']):
    im.alpha_composite(actor(item,row,col),(k*256,0));ImageDraw.Draw(im).text((k*256+8,330),('皮甲' if k==0 else '符文甲')+' · '+('正下' if d=='down' else '正左'),font=font,fill='#ffedc7')
   frames.append(im.convert('RGB'))
  frames[0].save(D/f'batch-{d}-start-stop-normal.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2,optimize=True)
print('Eight-direction idle/entry/exit/stop contact sheets and two real-paced 22-stage transition GIFs')
