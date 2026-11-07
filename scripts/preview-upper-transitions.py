#!/usr/bin/env python3
"""Whole-body previews of the explicit two-frame start/stop paths."""
from pathlib import Path
import importlib.util,json
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/P1/neutral-upper-transitions-r6'
s=importlib.util.spec_from_file_location('preview',R/'scripts/export-neutral-direction.py');preview=importlib.util.module_from_spec(s);s.loader.exec_module(preview)
def main():
 frames={direction:[Image.open(R/f'Art/Templates/P1-Neutral/{direction}/walk-r6-transitions/frames/{i:02}.png').convert('RGBA') for i in range(13)] for direction in ['up-left','up-right']}
 seq=[0,9,10]+list(range(1,9))*2+[11,12,0];durations=[480]+[120]*(len(seq)-2)+[480]
 comparison=[]
 for i in range(13):
  im=Image.new('RGBA',(512,256));im.alpha_composite(frames['up-left'][i],(0,0));im.alpha_composite(frames['up-right'][i],(256,0));comparison.append(im)
 for direction,items in [*frames.items(),('comparison',comparison)]:
  out=D if direction=='comparison' else D/direction;out.mkdir(parents=True,exist_ok=True)
  preview.gif([items[i] for i in seq],out/'start-stop-120ms.gif',durations)
  preview.gif(items[1:9],out/'walk-120ms.gif');preview.flatten(items[0],2).save(out/'idle-review-2x.png')
  # All transition key poses with boundary frames; native full canvas, never crops.
  order=[0,9,10,1,8,11,12,0];board=Image.new('RGB',(items[0].width*4,512),'#17372c');draw=ImageDraw.Draw(board)
  names=['idle00','start01','start02','walk01','walk08','stop01','stop02','idle00']
  for n,(idx,name) in enumerate(zip(order,names)):
   x,y=n%4*items[0].width,n//4*256;board.paste(preview.flatten(items[idx]),(x,y));draw.text((x+5,y+5),name,fill='white')
  board.save(out/'transition-poses-fullbody-1x.png');board.resize((board.width*2,board.height*2),Image.Resampling.NEAREST).save(out/'transition-poses-fullbody-2x.png')
 (D/'sequence.json').write_text(json.dumps({'indices':seq,'durationsMs':durations,'paths':{'start':['idle00','walk-start01','walk-start02','walk01'],'stop':['walk08','walk-stop01','walk-stop02','idle00']},'arbitraryPhaseInterrupts':False,'artApproval':None},indent=2)+'\n')
 print('Normal-speed upper-diagonal start/stop previews generated')
if __name__=='__main__':main()
