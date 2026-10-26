#!/usr/bin/env python3
"""Perspective dice review using production Swift mesh projections and receipts.
Offline art composition; never UIKit/device/performance capture.
"""
from pathlib import Path
import sys,json,math,subprocess,functools
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/poly-dice-demo-v1'
old=R/'scripts/review-head-dice-demo.py';namespace={'__file__':str(old)}
source=old.read_text().replace('dice-party-demo-v1','poly-dice-demo-v1').replace('build47','build48')
start=source.index(' for i,(die,pose) in enumerate(zip(row[\'dice\'],row[\'dicePose\'])):')
end=source.index('\n return f',start)
source=source[:start]+''' for i,(die,pose) in enumerate(zip(row['dice'],row['poly'])):
  im=die_image(die,pose);im.putalpha(im.getchannel('A').point(lambda a:round(a*pose['alpha'])))
  spacing=min(82,200/max(1,len(row['dice'])))
  cx=row['diceAnchor']['x']+(i-(len(row['dice'])-1)/2)*spacing
  cy=row['diceAnchor']['y']+43+oy+pose['offsetY']
  f.alpha_composite(im,(round(cx-128),round(cy-120)))
'''+source[end:]
exec(compile(source.split("if '--still' in sys.argv:")[0],str(old),'exec'),namespace)
# The above --prepare path writes requests and exits before rendering.
D=namespace['D'];rows=namespace['rows'];fontpath=namespace['fontpath'];palette_colors={'red':'#c72924','yellow':'#d9a129','green':'#219451','blue':'#1f70cc'}
@functools.lru_cache(None)
def glyph(value):
 im=Image.new('RGBA',(128,128));d=ImageDraw.Draw(im);s=str(value);font=ImageFont.truetype(fontpath,86 if value>9 else 98)
 box=d.textbbox((0,0),s,font=font);w=box[2]-box[0];h=box[3]-box[1]
 d.text(((128-w)/2-box[0],(128-h)/2-box[1]),s,font=font,fill='#fff0c8',stroke_width=2,stroke_fill='#413a23')
 if value in [6,9]:d.line((44,111,84,111),fill='#fff0c8',width=3)
 return im

def die_image(die,p):
 im=Image.new('RGBA',(256,270));d=ImageDraw.Draw(im);radius=p['radius'];color=palette_colors[die['color']];rgb=tuple(int(color[i:i+2],16) for i in [1,3,5]);mix=p['resultMix']
 def text(s,y,size,alpha=1):
  layer=Image.new('RGBA',im.size);dd=ImageDraw.Draw(layer);font=ImageFont.truetype(fontpath,size);b=dd.textbbox((0,0),s,font=font);w=b[2]-b[0]
  dd.text((128-w/2-b[0],120+y),s,font=font,fill=(255,238,195,round(alpha*255)),stroke_width=1,stroke_fill=(20,30,20,round(alpha*170)));im.alpha_composite(layer)
 if die['sides']==0:
  w=min(52,radius*1.6);h=min(40,radius*1.25);d.rounded_rectangle((128-w/2,120-h/2,128+w/2,120+h/2),6,fill=color,outline='#fff0c8',width=2)
  text('?',-19,30,1-mix)
  if die.get('value') is not None:text(('+' if die['color']=='yellow' and die['value']>0 else '')+str(die['value']),-19,30,mix)
  text(die['label'],48,14)
 else:
  for face in p['faces']:
   pts=[(128+q['x']*radius,120+q['y']*radius) for q in face['points']]
   fill=tuple(round(c*face['shade']) for c in rgb);d.polygon(pts,fill=fill);d.line(pts+[pts[0]],fill='#d4c9aa',width=1,joint='curve')
   center,right,up=face['center'],face['right'],face['up'];a=(right['x']-center['x'])*radius*2;b=(right['y']-center['y'])*radius*2;c=(center['x']-up['x'])*radius*2;v=(center['y']-up['y'])*radius*2;det=a*v-b*c
   if abs(det)<.025:continue
   tx=128+center['x']*radius-.5*a-.5*c;ty=120+center['y']*radius-.5*b-.5*v
   inverse=(128*v/det,-128*c/det,128*(-v*tx+c*ty)/det,-128*b/det,128*a/det,128*(b*tx-a*ty)/det)
   im.alpha_composite(glyph(face['value']).transform(im.size,Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC))
  label_y=48 if radius<=34 else int(radius*1.25+8)
  text(die['label'],label_y,14 if radius<=34 else 22,1-mix)
  if die.get('value') is not None:text(f'D{die["sides"]} · {die["value"]}',label_y-2,18 if radius<=34 else 26,mix)
 return im
namespace['die_image']=die_image
scene,old_ui=namespace['scene'],namespace['ui'];font=lambda n:ImageFont.truetype(fontpath,n)
poly=json.loads((D/'poly-frames.json').read_text())
def ui(row,world):
 f=old_ui(row,world);ImageDraw.Draw(f).text((1300,1035),f'{row["time"]:.2f}s',font=font(16),fill='#c6d6b7');return f
def gallery(row):
 f=Image.new('RGBA',(1200,850),'#102319');d=ImageDraw.Draw(f)
 d.text((28,16),'build48 · 多面骰翻面与减速落面' if row['group']=='types' else 'build48 · 多骰与固定加值分开表示',font=font(28),fill='#fff0c8')
 d.text((28,62),'数字固定在各骰面 · 三轴转动 · 结果来自原规则回执',font=font(20),fill='#c6d6b7')
 if row['group']=='types':
  for i,e in enumerate(row['entries']):
   x=20+i%3*395;y=105+i//3*337;d.rounded_rectangle((x,y,x+375,y+318),12,fill='#203a2a',outline='#a29560',width=2)
   d.text((x+16,y+10),e['title'],font=font(26),fill='#fff0c8')
   p={**e['samples'][0],'radius':78};im=die_image(e['dice'][0],p);im.putalpha(im.getchannel('A').point(lambda a:round(a*p['alpha'])));f.alpha_composite(im,(x+60,round(y+42+p['offsetY'])))
 else:
  for i,e in enumerate(row['entries']):
   y=120+i*300;d.rounded_rectangle((20,y,1180,y+280),12,fill='#203a2a',outline='#a29560',width=2);d.text((38,y+14),e['title'],font=font(26),fill='#fff0c8')
   n=len(e['dice']);spacing=110
   for j,(die,p) in enumerate(zip(e['dice'],e['samples'])):
    p={**p,'radius':48 if die['sides']>0 else 34};im=die_image(die,p);im.putalpha(im.getchannel('A').point(lambda a:round(a*p['alpha'])));cx=600+(j-(n-1)/2)*spacing;f.alpha_composite(im,(round(cx-128),round(y+48+p['offsetY'])))
 caption='D4/D10为离线骰型样片，其余取现有武器公式；没有新增武器外观。' if row['group']=='types' else '仅审核既有技能的骰子公式；未新增突袭或符文斩的动作特效。'
 d.text((28,796),caption,font=font(18),fill='#c6d6b7');d.text((28,825),'正常速度离线美术合成 · 非UIKit / 实机录屏',font=font(16),fill='#a8bba0')
 d.text((1070,825),f'{row["time"]:.2f}s',font=font(16),fill='#c6d6b7')
 return f.convert('RGB')
def save(name,frames):
 width,height=frames[0].size;sheet=Image.new('RGB',(width*3,height*3))
 for j,k in enumerate([0,10,25,45,60,75,90,len(frames)*3//4,len(frames)-1]):sheet.paste(frames[k],(j%3*width,j//3*height))
 pal=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT);scale=.85
 while True:
  size=(round(width*scale),round(height*scale));encoded=[f.resize(size,Image.Resampling.LANCZOS).quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
  encoded[0].save(D/(name+'-normal.gif'),save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=1,optimize=True)
  subprocess.run(['/workspace/gifsicle-1.96/src/gifsicle','-O3',str(D/(name+'-normal.gif')),'-o',str(D/(name+'.tmp'))],check=True);(D/(name+'.tmp')).replace(D/(name+'-normal.gif'))
  if (D/(name+'-normal.gif')).stat().st_size<19500000:break
  scale=round(scale-.1,2);assert scale>=.45
 gif=Image.open(D/(name+'-normal.gif'));assert gif.n_frames==len(frames)
 for page in range(math.ceil(len(frames)/30)):
  contact=Image.new('RGB',(1500,1800),'#15281b')
  for j,k in enumerate(range(page*30,min(len(frames),(page+1)*30))):
   gif.seek(k);assert gif.info['duration']==20;thumb=gif.convert('RGB');thumb.thumbnail((300,270));contact.paste(thumb,(j%5*300,j//5*300));ImageDraw.Draw(contact).text((j%5*300,j//5*300+272),f'{k} / {k*.02:.2f}s',font=font(16),fill='#fff0c8')
  contact.save(D/f'{name}-decoded-{page+1:02}.jpg',quality=90)
 for t,label in [(0,'standing'),(.5,'rolling'),(1.2,'impact'),(1.9,'landed'),(2.25,'held'),(3.2,'retired')]:frames[min(len(frames)-1,round(t/.02))].save(D/(name+'-'+label+'.png'))
 info={'file':name+'-normal.gif','frames':len(frames),'frameDurationMs':20,'durationMs':len(frames)*20,'dimensions':size,'bytes':(D/(name+'-normal.gif')).stat().st_size};print(name,info,flush=True);return info
if '--stills' in sys.argv:
 for group in ['types','bonus']:
  for t,label in [(.5,'rolling'),(1.9,'landed')]:
   row=next(r for r in poly if r['group']==group and abs(r['time']-t)<.001);gallery(row).save(D/(group+'-draft-'+label+'.png'))
 sys.exit(0)
reports=json.loads((D/'review-render.json').read_text())['animations'] if (D/'review-render.json').exists() else {}
for group in ['types','bonus']:
 if '--only' in sys.argv and group not in sys.argv[sys.argv.index('--only')+1:]:continue
 reports[group]=save(group,[gallery(r) for r in poly if r['group']==group])
for group in ['attack-buff','support']:
 if '--only' in sys.argv and group not in sys.argv[sys.argv.index('--only')+1:]:continue
 rs=[r for r in rows if r['scenario']==group];reports[group]=save(group,[ui(r,scene(r)) for r in rs])
(D/'review-render.json').write_text(json.dumps({'scope':'production Swift projected polyhedra and actual original-core receipts; offline composition, not UIKit/device capture','animations':reports,'newArtApproval':None},indent=2)+'\n')
