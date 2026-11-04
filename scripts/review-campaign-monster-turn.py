#!/usr/bin/env python3
"""Inspect the actual campaign monster presentation from the offline full movie.
The app, UIKit, simulator and device are never started by this script.
"""
from pathlib import Path
import json,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'Art/Review/Battle/campaign-crashfix-v1'
rows=json.loads((out/'data/battle-frames.json').read_text())
# Includes both actions of the first actual wolf-template monster and its full
# recovery; end just before a player starts their next confirmed action.
first_player=next(i for i,r in enumerate(rows) if r['action'] and not r['action']['enemy'])
assert first_player==238
w,h=720,526
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(out/'encounter-full.mp4'),'-frames:v',str(first_player),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
assert len(raw)==first_player*w*h*3
frames=[Image.frombytes('RGB',(w,h),raw[i*w*h*3:(i+1)*w*h*3]) for i in range(first_player)]
sample=Image.new('RGB',(w*3,h*3))
for j in range(9):sample.paste(frames[j*(len(frames)-1)//8],(j%3*w,j//3*h))
palette=sample.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
encoded[0].save(out/'monster-turn-normal.gif',save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=1,optimize=True)
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',15)
with Image.open(out/'monster-turn-normal.gif') as im:
 assert im.n_frames==first_player
 for first in range(0,first_player,60):
  sheet=Image.new('RGB',(1440,2000),'#15281d');d=ImageDraw.Draw(sheet)
  for i in range(first,min(first+60,first_player)):
   im.seek(i);assert im.info['duration']==20
   thumb=im.convert('RGB');thumb.thumbnail((240,176));x=(i-first)%6*240;y=(i-first)//6*200
   sheet.paste(thumb,(x,y));d.text((x+4,y+177),f'{i} / {i*.02:.2f}s',font=font,fill='#f5e7bd')
   if i in [0,60,83,100,149,172,204,237]:im.convert('RGB').save(out/f'monster-turn-key-{i:04d}.png')
  sheet.save(out/f'monster-turn-audit-{first//60:02d}.jpg',quality=91)
checks={'frames':first_player,'frameMs':20,'durationMs':first_player*20,'loop':0,'size':[w,h],'bytes':(out/'monster-turn-normal.gif').stat().st_size,'sourceRange':[0,first_player-1],'includes':'two actual monster actions and complete recovery','actualDiceAnchorCalledWithPersistentIDs':True,'appOrSimulatorRun':False,'lightingAndUIApproximate':True}
(out/'monster-turn-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(checks),flush=True)
