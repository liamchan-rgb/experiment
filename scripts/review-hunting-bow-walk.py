#!/usr/bin/env python3
"""Native full-body art review of equipped and empty slots. Not device capture."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/P1/hunting-bow-v1';D.mkdir(parents=True,exist_ok=True);A=R/'Sources/Resources/Assets.xcassets'
rig=json.loads((R/'Sources/Resources/hero-gait.json').read_text());presets=rig['modularP1']['loadouts'];dirs=['down','left','up','right','down-right','down-left','up-left','up-right'];labels=['下','左','上','右','右下','左下','左上','右上'];font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',20)
images={n:Image.open(A/(n+'.imageset')/(n+'.png')).convert('RGBA') for p in presets for ns in p['weaponAtlasNames'].values() for n in ns}
def cell(p,state,d,col):
 im=images[p['weaponAtlasNames'][state][d//4]];row=d%4;return im.crop((col*256,row*256,(col+1)*256,(row+1)*256))
def board(cols,stamp=""):
 out=Image.new('RGB',(2048,4*286+48),'#20372a');dr=ImageDraw.Draw(out)
 for row,(p,state) in enumerate((p,state) for p in presets for state in ['huntingBow','none']):
  for d in range(8):
   im=cell(p,state,d,cols[d]);out.paste(im,(d*256,row*286+28),im);dr.text((d*256+7,row*286+2),p['title']+(' · 背弓' if state=='huntingBow' else ' · 空背')+' / '+labels[d],font=font,fill='#ffedc7')
 dr.text((8,4*286+8),'八方向整身原尺寸 · 共用原身体/动作 · 正常120ms/帧 · 离线资源合成',font=font,fill='#ffedc7');dr.text((1880,4*286+8),str(stamp),font=font,fill='#ffedc7');return out
board([0]*8).save(D/'standing.png')
for p in presets:
 for d,name in enumerate(dirs):
  out=Image.new('RGB',(13*256,2*286+26),'#20372a');dr=ImageDraw.Draw(out)
  for row,state in enumerate(['huntingBow','none']):
   for col in range(13):
    im=cell(p,state,d,col);out.paste(im,(col*256,row*286+26),im);dr.text((col*256+5,row*286+2),('背弓' if row==0 else '空背')+f' / {col:02}',font=font,fill='#ffedc7')
  name=p['id']+'-'+name;out.save(D/(name+'-1x.png'));out.resize((out.width*2,out.height*2),Image.Resampling.NEAREST).save(D/(name+'-2x.png'))
frames=[board([i+1]*8,f"{i*0.12:.2f}s") for i in range(8)];frames[0].save(D/'walk-normal.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=True)
# Each direction's explicit authored entry/exit phase, no arbitrary pose reset.
columns=[]
for step in range(13):
 seq=[]
 for d in range(8):
  entry=rig['modularP1']['directions'][d]['entryPhase'];exit=rig['modularP1']['directions'][d]['exitPhase']
  if step==0:col=0
  elif step<=2:col=8+step
  elif step<=10:col=1+(entry+step-3)%8
  else:col=step
  seq.append(col)
 columns.append(seq)
frames=[board(c,f"{i*0.12:.2f}s") for i,c in enumerate(columns)];frames[0].save(D/'transitions-normal.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=True)
for n in ['walk','transitions']:
 im=Image.open(D/(n+'-normal.gif'));steps=im.n_frames;page=Image.new('RGB',(2048*2,im.height*math.ceil(steps/2)))
 for i in range(steps):im.seek(i);assert im.info['duration']==120;page.paste(im.convert('RGB'),(i%2*2048,i//2*im.height))
 page.save(D/(n+'-decoded.jpg'),quality=90)
(D/'review-render.json').write_text(json.dumps({'date':'2026-10-26','normalFrameMs':120,'nativeBodyCanvas':[256,256],'explicitBindingsPerAppearance':104,'appearances':2,'states':['huntingBow','none'],'nativePoseBoards':16,'boardScales':[1,2],'wholeBodiesRepresented':416,'walkFrames':8,'transitionFrames':len(columns),'transitionColumns':columns,'newArtApproval':None},indent=2)+'\n')
print('Native416body board set,8frame walk and13frame authored entry/exit GIFs ready')
