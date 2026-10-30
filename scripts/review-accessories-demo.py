#!/usr/bin/env python3
"""Offline accessory feedback review from production rules/pose/dice exports.
Not UIKit capture, game execution, simulator or device evidence.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,subprocess
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/accessories-demo-v1';D.mkdir(exist_ok=True)
p=R/'scripts/review-armor-demo.py';N={'__file__':str(p)};exec(compile(p.read_text().split('for item in armors:\n frames=[]')[0],str(p),'exec'),N)
p=R/'scripts/review-legendary-staff-demo.py';Q={'__file__':str(p)};exec(compile(p.read_text().split('reports=[]\nfor scenario')[0],str(p),'exec'),Q)
original=Q['gear'];Q['S']['gear_render']=Q['world']['gear_render']=lambda c,p,w:N['actor']('leatherArmor',w,c,p) if w=='legendaryStaff' else original(c,p,w)
rows=json.loads((D/'accessory-frames.json').read_text());world=Q['world'];font=Q['font'];attached=world['attached']
# Same strong-strike timing and attached light field; equipment changes do not
# alter geometry, emitter timing or animation. Both targets remain alive.
for row in rows:
 for suffix in ['p1','p2','fx']:
  key=(row['scenario']+'-'+suffix,row['frame']);source=('legendary-staff-heavy-'+suffix,row['frame'])
  attached[key]=attached[source];world['reqs'][key]=world['reqs'][source]
A=R/'Sources/Resources/Assets.xcassets'
def icon(item):
 name={'powerBadge':'MeadowPowerBadge','actionRing':'MeadowActionRing'}[item];return Image.open(A/(name+'.imageset')/(name+'.png')).convert('RGBA')
colors={'ink':'#f9edc4','muted':'#bbcba9','gold':'#eac668','panel':'#192b21','green':'#45d27b','blue':'#41cfee'}
def paint(row):
 f=Q['ui'](row,Q['S']['scene'](row));d=ImageDraw.Draw(f);u=next(x for x in row['units'] if x['id']=='p1');readout=u['accessory']
 # Match the native status-row grouping: bars / discrete AP / permanent item
 # followed by the two existing temporary status slots. Values are actual core.
 d.rectangle((80,853,1356,905),fill=colors['panel'])
 for i,(title,value,maximum,c) in enumerate([('生命',u['hp'],u['maxHP'],colors['green']),('护盾',u['shield'],8,colors['blue']),('行动',u['ap'],max(u['baseAP'],u['ap']),colors['gold'])]):
  x=86+i*372;d.text((x,858),title+(f' {value}/{maximum}' if i<2 else ''),font=font(20),fill=colors['ink'])
  if i<2:
   d.rectangle((x,893,x+350,902),fill='#07110b')
   if value:d.rectangle((x+1,894,x+1+348*min(1,value/maximum),901),fill=c)
  else:
   for j in range(maximum):
    cx=x+10+j*28;cy=897;h=9;d.polygon([(cx,cy-h),(cx+h,cy),(cx,cy+h),(cx-h,cy)],fill=c if j<value else '#303c28',outline=c)
 if readout:
  x=1215;d.rounded_rectangle((x,859,x+38,897),4,fill=colors['panel'],outline=colors['gold'],width=2);im=icon(readout['itemID']).resize((30,30),Image.Resampling.LANCZOS);f.paste(im,(x+4,863),im)
  # Show the same tooltip content on an intentional hover interval.
  if row['time']<.75:
   d.rounded_rectangle((x-300,682,x+38,840),7,fill=colors['panel'],outline=colors['gold'],width=2)
   for j,text in enumerate([readout['name']+' · '+readout['summary']]+readout['detail'].split('\n')):d.text((x-288,694+j*36),text,font=font(20),fill=colors['ink'])
 d.rectangle((96,951,349,1005),fill='#293e2d');d.text((96,964),'1D20'+(f'＋{u["attributeDamage"]}' if u['attributeDamage'] else ''),font=font(20),fill=colors['muted'])
 # Native second card is strong strike: its source D6+2 is never replaced by D20.
 x=86+(1268-110-40)/4+10;cw=(1268-110-40)/4
 d.rectangle((round(x+8),951,round(x+cw-8),1005),fill='#293e2d');d.text((round(x+10),964),'1D6＋2'+(f' · 增伤＋{u["attributeDamage"]}' if u['attributeDamage'] else ''),font=font(19),fill=colors['muted'])
 d.rectangle((0,f.height-50,f.width,f.height),fill='#0b1811')
 label='未装备饰品' if not readout else readout['name']+' · '+readout['summary']
 d.text((42,f.height-29),'Build64 · '+label+' · 正常速度离线美术合成 · 非UIKit／实机录屏',font=font(18),fill=colors['muted'])
 return f.convert('RGB').resize((1020,765),Image.Resampling.LANCZOS)
reports=[]
for scenario in sorted(set(x['scenario'] for x in rows)):
 group=[x for x in rows if x['scenario']==scenario];frames=[paint(row) for row in group]
 sample=Image.new('RGB',(4080,3060))
 for j in range(16):sample.paste(frames[round(j*(len(frames)-1)/15)],(j%4*1020,j//4*765))
 palette=sample.quantize(colors=256);encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames];path=D/(scenario+'-normal.gif');encoded[0].save(path,save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=2,optimize=False)
 tool=Path('/workspace/gifsicle-1.96/src/gifsicle')
 if tool.exists():temp=path.with_suffix('.opt.gif');subprocess.run([str(tool),'-O3',str(path),'-o',str(temp)],check=True);temp.replace(path)
 frames[0].save(D/(scenario+'-standing.png'));gif=Image.open(path);duration=0
 for page in range(math.ceil(gif.n_frames/8)):
  out=Image.new('RGB',(1020,1620),'#20372a');dd=ImageDraw.Draw(out)
  for j in range(8):
   i=page*8+j
   if i>=gif.n_frames:break
   gif.seek(i);duration+=gif.info['duration'];out.paste(gif.convert('RGB').resize((510,383)),(j%2*510,j//2*405));dd.text((j%2*510+4,j//2*405+383),f'{scenario} decoded {i}',font=font(14),fill=colors['ink'])
  out.save(D/f'{scenario}-decoded-{page+1:02}.png')
 assert duration==3800
 reports.append({'file':path.name,'actualDecodedFrames':gif.n_frames,'durationMs':duration})
(D/'review.json').write_text(json.dumps({'scope':'Actual original-core equipment and receipts; current production pose/dice exports; approximate offline stage/light/UI composition; no App/simulator/device','animations':reports,'characterArtChanged':False,'newArtApproval':None},indent=2)+'\n');print(reports,flush=True)
