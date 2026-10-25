#!/usr/bin/env python3
"""Normal offline art composition from actual GameCore and production Swift fields.
Not UIKit capture or device/performance verification. No character pixels repainted.
"""
from pathlib import Path
import json,math,subprocess,os,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageChops,ImageFilter
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/party-support-demo-v1';D.mkdir(exist_ok=True,parents=True)
p=R/'scripts/review-battle-effects-demo.py';env={'__file__':str(p)};exec(compile(p.read_text().split('\nframes=[]; traces=[]')[0],str(p),'exec'),env)
render,sample,asset,shadow=[env[k] for k in ['render','sample','asset','shadow']]
W,H,HEADER,FOOTER=1000,600,70,200
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',22);small=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',17);large=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',28)
feet={'p1':(165,420),'p2':(315,505),'m1':(650,395),'m2':(835,510)};hs=.83;es=.82
plate=env['plate'].resize((1000,918),Image.Resampling.LANCZOS).crop((0,200,1000,800));foreground=env['foreground'].resize((1000,918),Image.Resampling.LANCZOS).crop((0,200,1000,800))
assets={n:asset('BattleVFX'+n) for n in ['HealStar','HealWisp','HealShaft','HealWave','RoundBarrier','Mote','Burst','GoldEmber']}
items={n:asset('MeadowParty'+n[0].upper()+n[1:]) for n in ['smallPotion','largePotion','shieldPotion','revivalStone']}
enemy=asset('MeadowBattleForestWarden')
attack=asset('MeadowBattleWardenAttackSheet');enemy_attacks=[attack.crop((i*384,0,(i+1)*384,256)) for i in range(8)]
body=asset('BattleVFXDeathBody60');wind=asset('BattleVFXDeathWind60')
bodies=[body.crop(((i%8)*384,(i//8)*256,(i%8+1)*384,(i//8+1)*256)) for i in range(48)]
winds=[wind.crop(((i%8)*448,(i//8)*320,(i%8+1)*448,(i//8+1)*320)) for i in range(116)]
rows=json.loads((D/'party-frames.json').read_text());legacy=json.loads((D/'legacy-attachment-samples.json').read_text());attached={(r['kind'],r['frame']):r for r in legacy['frames']}
def smooth(x):t=min(1,max(0,x));return t*t*(3-2*t)
def pulse(t,s,p,e):return smooth((t-s)/(p-s)) if t<p else 1-smooth((t-p)/(e-p))
def compose(f,im,c,size,alpha=1,add=False,angle=0):
 if alpha<=0:return
 im=im.resize((max(1,round(size[0])),max(1,round(size[1]))),Image.Resampling.LANCZOS)
 if angle:im=im.rotate(-math.degrees(angle),Image.Resampling.BICUBIC,expand=True)
 if alpha<1:im.putalpha(im.getchannel('A').point(lambda a:round(a*alpha)))
 x,y=round(c[0]-im.width/2),round(c[1]-im.height/2)
 if not add:f.alpha_composite(im,(x,y));return
 left,top=max(0,x),max(0,y);right,bottom=min(f.width,x+im.width),min(f.height,y+im.height)
 if left>=right or top>=bottom:return
 src=im.crop((left-x,top-y,right-x,bottom-y));premul=ImageChops.multiply(src.convert('RGB'),src.getchannel('A').convert('RGB'));old=f.crop((left,top,right,bottom)).convert('RGB');f.paste(ImageChops.add(old,premul),(left,top))
def glow(f,c,rx,ry,a,color):
 if a<=0:return
 key=color
 if key not in glow.cache:
  im=Image.new('RGBA',(96,96));arr=np.zeros((96,96,4),dtype=np.uint8);yy,xx=np.indices((96,96));v=np.maximum(0,1-np.sqrt(((xx-48)/48)**2+((yy-48)/48)**2));arr[:,:,:3]=color;arr[:,:,3]=np.round(v*255);glow.cache[key]=Image.fromarray(arr)
 compose(f,glow.cache[key],c,(rx*2,ry*2),a,True)
glow.cache={}
def hero_at(u,row):
 x,y=feet[u['id']];a=row['action'];v=a.get('travel',{}) if a.get('actor')==u['id'] else {};return x+v.get('x',0)-123*hs,y+v.get('y',0)-214*hs

def attachments(f,u,row,scene_row):
 x,y=hero_at(u,scene_row);root=sample(u['clip'],u['progress'])[1];cx=x+(root[0]+128)*hs;cy=y+(root[1]+144)*hs;foot=(cx,y+(root[1]+214)*hs)
 power=row['recoveryPower'];action=scene_row['action'];a=action.get('age',-1)
 recovery_age=None
 # The legacy requests are the same ages passed to the runtime attachment view.
 request=REQUESTS[(scene_row['scenario']+'-'+u['id'],scene_row['frame'])];recovery_age=request.get('recoveryAge')
 if recovery_age is not None and 0<=recovery_age<1.8:
  age=recovery_age
  compose(f,assets['HealShaft'],(foot[0],foot[1]-82.5*hs),(110*hs,185*hs),power*.5)
  core=assets['Burst'].copy();ar=np.asarray(core).copy();ar[:,:,:3]=[209,255,217];core=Image.fromarray(ar)
  compose(f,core,(foot[0],foot[1]-64*hs),(110*hs,110*hs),pulse(age,.34,.47,.70)*.70)
  expand=.65+.65*smooth(age/1.1);compose(f,assets['HealWave'],(foot[0],foot[1]+2*hs),(164*hs*expand,28*hs),power*.8)
  for q in row['wisps']:compose(f,assets['HealWisp'],(foot[0]+q['x']*hs,foot[1]+q['y']*hs),(85*hs*q['scaleX'],180*hs),q['alpha'],False,q['rotation'])
  for q in row['recovery']:compose(f,assets['HealStar'],(foot[0]+q['x']*hs,foot[1]+q['y']*hs),(q['size']*hs,q['size']*hs),q['alpha'])
 alpha=row['shieldOpacity'];compose(f,assets['RoundBarrier'],(cx,cy),(240*hs,240*hs),alpha)
 for i in range(6):
  angle=scene_row['time']*1.25+i*2.399;radius=240*hs*.41;size=(9 if i%2==0 else 6)*hs
  im=assets['Mote'].copy();ar=np.asarray(im).copy();ar[:,:,:3]=[80,245,255];im=Image.fromarray(ar)
  compose(f,im,(cx+math.cos(angle)*radius,cy+math.sin(angle)*radius),(size,size),alpha*.65)
REQUESTS={(r['kind'],r['frame']):r for r in json.loads((D/'legacy-light-requests.json').read_text())}
def ui(scene,row):
 f=Image.new('RGBA',(W,HEADER+H+FOOTER),'#14251c');f.alpha_composite(scene,(0,HEADER));d=ImageDraw.Draw(f)
 scenario=row['scenario'];titles={'support':'援护 · 友方恢复与授盾','rally':'振奋 · 节点队友增伤','items':'道具 · 实际恢复与授盾','revive':'复活石 · 同节点救援与起身','combat':'真实增伤 / 致死右吹 / 圆盾接触'}
 d.text((18,7),'build46 · 小队支援 / '+titles[scenario],font=font,fill='#f8e9c4');d.text((18,40),'正常速度离线美术预览 · 生产规则/轨迹 · 非UIKit/实机录屏',font=small,fill='#b5cdb7');d.text((W-155,12),f'{row["time"]:.2f}s',font=small,fill='#c8d6bd')
 for i,u in enumerate(row['units']):
  x=16+i*246;y=HEADER+H+10;sel=u['id'] in ['p1','m1']
  d.rounded_rectangle((x,y,x+234,y+85),7,fill='#293c2d',outline='#e6cd83' if sel else '#68744f',width=2 if sel else 1)
  d.text((x+9,y+5),('▶ ' if u['id']==row['current'] else '')+u['name']+f' · {u["ap"]}AP',font=small,fill='#ffedc7')
  d.text((x+9,y+33),f'HP {u["hp"]}/{u["maxHP"]}',font=small,fill='#e9efce');d.text((x+113,y+33),f'盾 {u["shield"]}/8',font=small,fill='#d4ecf2')
  for xx,v,m,col in [(x+9,u['hp'],u['maxHP'],'#7ddd92'),(x+113,u['shield'],8,'#65ddff')]:
   d.rectangle((xx,y+62,xx+91,y+72),fill='#07100a',outline='#817954')
   if v:d.rectangle((xx+1,y+63,xx+1+89*v/m,y+71),fill=col)
  if u['buff']:
   d.rectangle((x+207,y+32,x+228,y+54),fill='#4b401b',outline='#f2d280');d.text((x+211,y+32),'↑',font=small,fill='#ffe69b')
  if u['shield']:
   d.rectangle((x+207,y+59,x+228,y+80),fill='#193b41',outline='#6cdfff');d.text((x+211,y+58),'盾',font=small,fill='#9af1ff')
 for i,(title,detail) in enumerate([('普通攻击','1AP · 1D6＋当前增伤'),('援护','1AP · 恢复6 / 盾4'),('振奋','1AP · 群体增伤2 / 1轮'),('道具','药水 / 复活石')]):
  x=16+i*246;y=HEADER+H+108;d.rounded_rectangle((x,y,x+234,y+77),7,fill='#293c2d',outline='#b8a568');d.text((x+12,y+7),title,font=font,fill='#ffedc7');d.text((x+12,y+44),detail,font=small,fill='#c1d1b4')
 if scenario=='rally' and .95<=row['time']<1.6:
  x=220;y=HEADER+H-100;d.rounded_rectangle((x,y,x+292,y+88),6,fill='#172c20',outline='#e2c573');d.text((x+12,y+8),'振奋 · 伤害＋2',font=font,fill='#ffe7a9');d.text((x+12,y+43),'剩余1轮 · 普攻与伤害技能生效',font=small,fill='#d2dfbf')
 return f.convert('RGB')
reports={}
for scenario in ['support','rally','items','revive','combat']:
 print('Rendering',scenario,flush=True);group=[r for r in rows if r['scenario']==scenario];frames=[]
 for row in group:
  a=row['action'];age=a.get('age',0);dim=pulse(age,0,.4,1.8)*(.58 if a.get('visual')=='attack' else .32) if a else 0
  f=ImageEnhance.Brightness(plate).enhance(1-dim)
  ordered=sorted(row['units'],key=lambda u:feet[u['id']][1])
  for u in ordered:
   if u['id'].startswith('p'):
    im=render(u['clip'],u['progress']);x,y=hero_at(u,row);shadow(f,im,x,y,hs);f.alpha_composite(im.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(x),round(y)))
    attachments(f,u,attached[(scenario+'-'+u['id'],row['frame'])],row)
   else:
    x,y=feet[u['id']];v=a.get('travel',{}) if a.get('actor')==u['id'] else {};ex,ey=x+v.get('x',0)-178.5*es,y+v.get('y',0)-240*es
    da=u.get('deathAge');im=bodies[min(47,int(da*60))] if da is not None else enemy_attacks[min(7,int(min(1,age/.96)*8))] if a.get('actor')==u['id'] else enemy
    shadow(f,enemy,ex,ey,es,1-smooth(da/.75) if da is not None else 1)
    f.alpha_composite(im.resize((round(384*es),round(256*es)),Image.Resampling.NEAREST),(round(ex),round(ey)))
    if da is not None and da<116/60: f.alpha_composite(winds[min(115,int(da*60))].resize((round(448*es),round(320*es)),Image.Resampling.NEAREST),(round(x-178.5*es),round(y-272*es)))
  f.alpha_composite(foreground)
  if a.get('visual')=='support':
   start=feet[a['actor']];end=feet[a['target']];start=(start[0]+5*hs,start[1]-70*hs);end=(end[0]+5*hs,end[1]-70*hs)
   points=[]
   for j in range(41):
    t=j/40;u=1-t;points.append((u*u*start[0]+2*u*t*((start[0]+end[0])/2)+t*t*end[0],u*u*start[1]+2*u*t*(min(start[1],end[1])-90)+t*t*end[1]))
   overlay=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(overlay);alpha=pulse(age,.05,.36,1.12);draw.line(points,fill=(70,255,140,round(alpha*65)),width=8);draw.line(points,fill=(242,211,130,round(alpha*204)),width=2);f.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(.3)))
   for q in row['trail']:compose(f,assets['HealStar'],(q['x'],q['y']),(q['size'],q['size']),q['alpha'],True)
   p=feet[a['target']];glow(f,p,110,26,pulse(age,0,.56,1.5)*.5,(50,255,140))
  if a.get('visual')=='rally':
   for g in row['rally']:
    p=feet[g['id']];c=(p[0]+5*hs,p[1]-70*hs);power=pulse(age,.05,.46,1.5);glow(f,c,48,85,power*.25,(255,175,45))
    for q in g['particles']:compose(f,assets['GoldEmber'],(q['x'],q['y']),(q['size']*.5,q['size']*2),q['alpha'],True)
    for i in range(3):
     t=age-i*.1;alpha=pulse(t,0,.28,.85)
     if alpha>0:
      lay=Image.new('RGBA',(W,H));dd=ImageDraw.Draw(lay);y=c[1]+10-t*75;dd.line([(c[0]-14,y+10), (c[0],y),(c[0]+14,y+10)],fill=(242,211,130,round(alpha*255)),width=3);f.alpha_composite(lay)
  if a.get('action') in items:
   p=feet[a['target']];compose(f,items[a['action']],(p[0],p[1]-130-age*15),(38,38),pulse(age,0,.25,.85),True)
  if a.get('visual')=='revive':
   p=feet[a['target']];compose(f,assets['HealShaft'],(p[0],p[1]-80),(120,220),pulse(age,0,.72,1.9),True)
   for g in row['rally']:
    if g['id']==a['target']:
     for q in g['particles']:compose(f,assets['HealStar'],(q['x'],q['y']),(q['size'],q['size']),q['alpha'],True)
  if a.get('visual')=='attack':
   pp=feet[a['target']];is_enemy=a['enemy'];elapsed=age-(.46 if is_enemy else 1.048);xx=pp[0]+((5+240*.41)*hs if a.get('shielded') else 10) if is_enemy else pp[0]-80;at=(xx,pp[1]-(65 if is_enemy else 72));power=pulse(elapsed,-.035,.035,.52)
   glow(f,at,140,140,power*.48,(255,175,45));glow(f,pp,170,30,power*.65,(255,175,45))
   if 0<=elapsed<.7:
    compose(f,assets['Burst'],at,(150+elapsed*140,150+elapsed*140),power,True)
    if not is_enemy:compose(f,asset('BattleVFXHeavyArc'),at,(210+elapsed*240,210+elapsed*240),power*.9,True)
  for q in attached[(scenario+'-fx',row['frame'])]['particles']:
   at=(q['x'],q['y']);col=(30,200,255) if q['cyan'] else (255,175,45)
   if q['id']%6==0:glow(f,at,22,20,q['alpha']*.2,col)
   if q['groundAge'] is not None and q['groundAge']<.24:
    a1=(1-q['groundAge']/.24)*q['alpha'];glow(f,(q['groundX'],q['groundY']),34,10,a1*.6,col)
   compose(f,asset('BattleVFXCyanShard') if q['cyan'] else assets['GoldEmber'],at,(q['size'],q['size']*.67),q['alpha'],True,q['angle'])
  for m in row['messages']:
   t=row['time']-m['at'];p=feet[m['id']];col='#c4ffc4' if m['kind']=='heal' else '#80edff' if m['kind']=='shield' else '#ffe7a9';y=p[1]-120-t*26+(24 if m['kind']=='shield' else 0);ImageDraw.Draw(f).text((p[0]+90,y),m['text'],font=large,fill=col,stroke_width=2,stroke_fill='#19311d')
  for u in row['units']:
   x,y=feet[u['id']];label=u['name'];yy=y-(140 if u['id'].startswith('p') else 218);dd=ImageDraw.Draw(f);dd.rounded_rectangle((x-78,yy,x+78,yy+27),4,fill='#172c21');dd.text((x-70,yy+1),label,font=small,fill='#fff1c9')
  frames.append(ui(f,row))
 palette_sample=Image.new('RGB',(W*3,(HEADER+H+FOOTER)*3))
 for j,k in enumerate([0,20,40,50,65,80,len(frames)//2,len(frames)*3//4,len(frames)-1]):palette_sample.paste(frames[k],(j%3*W,j//3*(HEADER+H+FOOTER)))
 palette=palette_sample.quantize(colors=256,method=Image.Quantize.MEDIANCUT);name=scenario+'-normal.gif';scale=.85
 while True:
  size=(round(W*scale),round((HEADER+H+FOOTER)*scale));encoded=[f.resize(size,Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
  encoded[0].save(D/name,save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=1,optimize=True)
  binary=os.environ.get('GIFSICLE') or shutil.which('gifsicle') or '/workspace/gifsicle-1.96/src/gifsicle'
  if Path(binary).exists():subprocess.run([binary,'-O3',str(D/name),'-o',str(D/(name+'.tmp'))],check=True);(D/(name+'.tmp')).replace(D/name)
  if (D/name).stat().st_size<19500000:break
  scale=round(scale-.1,2);assert scale>=.45
 gif=Image.open(D/name);assert gif.n_frames==len(frames)
 for page in range(math.ceil(gif.n_frames/40)):
  sheet=Image.new('RGB',(1500,2096),'#15281b')
  for j,k in enumerate(range(page*40,min(gif.n_frames,(page+1)*40))):
   gif.seek(k);assert gif.info['duration']==20;sheet.paste(gif.convert('RGB').resize((300,262)),(j%5*300,j//5*262))
  sheet.save(D/f'{scenario}-decoded-{page+1:02}.jpg',quality=90)
 for sec,label in [(0,'standing'),(.64,'gather'),(1.06,'impact'),(1.5,'tail'),(2.4,'settled')]:frames[min(len(frames)-1,round(sec/.02))].save(D/(scenario+'-'+label+'.png'))
 if scenario=='revive':
  for sec,label in [(1.12,'half-health'),(1.42,'rising')]:frames[round(sec/.02)].save(D/(scenario+'-'+label+'.png'))
 if scenario=='items':frames[round(5.9/.02)].save(D/'items-shield.png')
 if scenario=='combat':
  for sec,label in [(1.5,'lethal'),(2.1,'wind'),(3.26,'shield-contact')]:frames[round(sec/.02)].save(D/('combat-'+label+'.png'))
 reports[scenario]={'file':name,'frames':gif.n_frames,'frameDurationMs':20,'durationMs':len(frames)*20,'bytes':(D/name).stat().st_size,'dimensions':size,'scale':scale}
 print(scenario,reports[scenario],flush=True)
(D/'review-render.json').write_text(json.dumps({'scope':'actual original GameCore states and production Swift fields; offline light/UI approximation, not UIKit or device capture','animations':reports,'newArtApproval':None},indent=2)+'\n')
