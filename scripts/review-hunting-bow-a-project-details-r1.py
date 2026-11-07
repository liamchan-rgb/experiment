from pathlib import Path
from PIL import Image,ImageDraw
import json,math
R=Path(__file__).resolve().parents[1];p=R/'scripts/review-hunting-bow-a-project-r1.py';ns={'__file__':str(p)};exec(compile(p.read_text().split("if '--stills' in sys.argv:")[0],str(p),'exec'),ns);D=ns['D'];rows=ns['rows'];font=ns['font']
# Complete character, not isolated joints. Same actual exported animation rows.
bodyframes=[]
for row in [r for r in rows if r['scenario']=='bow']:
 u=next(u for u in row['units'] if u['id']=='p1');im=Image.new('RGB',(256,280),'#20372a');sprite=ns['gear_render'](u['clip'],u['progress'],'huntingBow');im.paste(sprite,(0,0),sprite);ImageDraw.Draw(im).text((6,258),f'P1 / {row["time"]:.2f}s',font=font(16),fill='#ffedc7');bodyframes.append(im)
large=[f.resize((512,560),Image.Resampling.NEAREST) for f in bodyframes];large[0].save(D/'bow-body-normal.gif',save_all=True,append_images=large[1:],duration=20,loop=0,disposal=2,optimize=True)
gif=Image.open(D/'bow-body-normal.gif');assert gif.n_frames==190
for page in range(7):
 board=Image.new('RGB',(1280,1680),'#20372a')
 for j in range(30):
  i=page*30+j
  if i>=gif.n_frames:break
  gif.seek(i);assert gif.info['duration']==20;board.paste(gif.convert('RGB').resize((256,280),Image.Resampling.NEAREST),(j%5*256,j//5*280))
 board.save(D/f'body-decoded-{page+1:02}.jpg',quality=94)
poses=[(clip,v) for clip in ['idle','attack','guard','hit','victory','defeat'] for v in [0,.25,.5,.75,1]]
for page in range(2):
 im=Image.new('RGB',(1024,1120),'#20372a');d=ImageDraw.Draw(im)
 for j,(clip,v) in enumerate(poses[page*15:page*15+15]):
  sprite=ns['gear_render'](clip,v,'huntingBow');x,y=j%4*256,j//4*280;im.paste(sprite,(x,y),sprite);d.text((x+6,y+258),f'{clip} / {v:.2f}',font=font(16),fill='#ffedc7')
 for scale in [1,2]:im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).save(D/f'all-clips-{page+1:02}-{scale}x.png')
samples=[('bow',.5),('bow',1.55),('bow',1.86),('bow',2.0),('bow-heavy',2.06),('bow-lethal',2.1)];height=ns['namespace']['world_h'];board=Image.new('RGB',(3000,(height+34)*2),'#172c21')
for i,(kind,t) in enumerate(samples):
 row=min((r for r in rows if r['scenario']==kind),key=lambda r:abs(r['time']-t));world=ns['scene'](row).convert('RGB');x=i%3*1000;y=i//3*(height+34);board.paste(world,(x,y));ImageDraw.Draw(board).text((x+8,y+height+4),f'{kind} {t:.2f}s',font=font(18),fill='#fff0c8')
for scale in [1,2]:board.resize((board.width*scale,board.height*scale),Image.Resampling.NEAREST).save(D/f'whole-world-{scale}x.png')
print('190frame native complete-body GIF +7decoded pages;30six-clip body keyposes at1x/2x;6whole-world samples at1x/2x ready')
