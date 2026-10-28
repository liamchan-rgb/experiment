#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,copy,subprocess,math
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/armor-demo-v1'
p=R/'scripts/review-armor-demo.py';N={'__file__':str(p)};exec(compile(p.read_text().split('for item in armors:\n frames=[]')[0],str(p),'exec'),N)
p=R/'scripts/review-legendary-staff-demo.py';Q={'__file__':str(p)};exec(compile(p.read_text().split("reports=[]\nfor scenario")[0],str(p),'exec'),Q)
original=Q['gear'];Q['S']['gear_render']=Q['world']['gear_render']=lambda c,p,w:N['actor']('runeArmor',w,c,p) if w=='legendaryStaff' else original(c,p,w)
frames=[]
for row in Q['rows']:
 if row['scenario']!='legendary-staff':continue
 row=copy.deepcopy(row)
 for u in row['units']:
  if u['id']=='p1':u['maxHP']+=8
 im=Q['ui'](row,Q['S']['scene'](row)).convert('RGB').resize((1020,765),Image.Resampling.LANCZOS);dd=ImageDraw.Draw(im);dd.rectangle((0,737,1019,764),fill='#0b1811');dd.text((35,741),'Build61 · 护甲挂载 · 正常速度离线美术合成 · 非 UIKit／实机录屏',font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',12),fill='#c7d5b4');frames.append(im)
frames[0].save(D/'battle-standing.png');palette=Image.new('RGB',(4080,3060))
for i in range(16):palette.paste(frames[round(i*(len(frames)-1)/15)],(i%4*1020,i//4*765))
pal=palette.quantize(colors=256);encoded=[x.quantize(palette=pal,dither=Image.Dither.NONE) for x in frames];p=D/'battle-normal.gif';encoded[0].save(p,save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=2,optimize=False)
opt=Path('/workspace/gifsicle-1.96/src/gifsicle')
if opt.exists():temp=p.with_suffix('.opt.gif');subprocess.run([str(opt),'-O3',str(p),'-o',str(temp)],check=True);temp.replace(p)
gif=Image.open(p);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14)
for page in range(math.ceil(gif.n_frames/8)):
 out=Image.new('RGB',(1020,4*405),'#20372a');dd=ImageDraw.Draw(out)
 for j in range(8):
  i=page*8+j
  if i>=gif.n_frames:break
  gif.seek(i);out.paste(gif.convert('RGB').resize((510,383)),(j%2*510,j//2*405));dd.text((j%2*510+4,j//2*405+383),f'decoded {i}',font=font,fill='#f0e4b6')
 out.save(D/f'battle-decoded-{page+1:02}.png')
W=R/'Art/Review/P1/armor-demo-v1';gifs=[Image.open(p) for p in sorted(W.glob('*walk-normal.gif'))]
for i in range(8):
 out=Image.new('RGB',(2048,1120),'#20372a')
 for j,g in enumerate(gifs):g.seek(i);out.paste(g.convert('RGB'),(j%2*1024,j//2*560))
 out.save(W/f'walk-decoded-{i+1:02}.png')
print(json.dumps({'battleDecodedFrames':gif.n_frames,'battleMs':sum((gif.seek(i) or gif.info['duration']) for i in range(gif.n_frames)),'walkingDecodedFrames':32}),flush=True)
