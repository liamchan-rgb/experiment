from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/armor-fit-r2'
# Comparison decodes the actual delivery GIFs, preserving all recorded holds.
gifs=[Image.open(D/(x+'-attack-normal.gif')) for x in ['leatherArmor','runeArmor']];frames=[];dur=[]
for i in range(gifs[0].n_frames):
 out=Image.new('RGB',(1024,560),'#20372a')
 for j,g in enumerate(gifs):g.seek(i);out.paste(g.convert('RGB').crop((768,0,1024,280)).resize((512,560),Image.Resampling.NEAREST),(j*512,0))
 frames.append(out);dur.append(gifs[0].info['duration'])
frames[0].save(D/'armors-standing.png');frames[0].save(D/'armors-body-normal.gif',save_all=True,append_images=frames[1:],duration=dur,loop=0,disposal=2,optimize=True)
# Compact whole-body contact sheets of every decoded frame, unchanged bow
# column omitted. All pixels are at native scale; no torso-only crops.
for item in ['leatherArmor','runeArmor']:
 for clip in ['attack','states']:
  g=Image.open(D/(item+'-'+clip+'-normal.gif'));cells=[]
  for i in range(g.n_frames):
   g.seek(i);fr=g.convert('RGB');cell=Image.new('RGB',(600,180),'#20372a')
   for j,col in enumerate([0,2,3]):cell.paste(fr.crop((col*256+48,48,col*256+248,228)),(j*200,0))
   ImageDraw.Draw(cell).text((2,2),str(i),fill='white');cells.append(cell)
  for page in range(math.ceil(len(cells)/12)):
   out=Image.new('RGB',(1200,1080),'#20372a')
   for j,c in enumerate(cells[page*12:page*12+12]):out.paste(c,(j%2*600,j//2*180))
   out.save(D/(item+'-'+clip+'-contact-'+str(page+1).zfill(2)+'.png'))
print('actual GIF decoded frames 462; comparison duration',sum(dur))
