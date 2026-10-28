#!/usr/bin/env python3
"""Receipt-bound dice/monster review; offline composition, not UIKit/device capture."""
from pathlib import Path
import sys,json,math,os,subprocess,functools
from PIL import Image,ImageDraw,ImageFont,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/dice-party-demo-v1';D.mkdir(exist_ok=True,parents=True)
p=R/'scripts/review-party-support-demo.py';env={'__file__':str(p)};exec(compile(p.read_text().split('\nreports={}')[0],str(p),'exec'),env)
asset,render,sample,shadow,compose,glow=[env[k] for k in ['asset','render','sample','shadow','compose','glow']]
asset=functools.lru_cache(None)(asset)
feet,hs,es=env['feet'],env['hs'],env['es'];rows=json.loads((D/'dice-frames.json').read_text());requests=[]
# Request production attachment/particle fields from exact receipt transitions.
for scenario in dict.fromkeys(r['scenario'] for r in rows):
 group=[r for r in rows if r['scenario']==scenario];prior=None;births={};heals={};forms={};contacts={};breaks={};emit=[]
 for row in group:
  time=row['time'];age=row['age'];units={u['id']:u for u in row['units']};kind=row['action'];target=row['target']
  if row['playing'] and abs(age)<1e-8:
   hit=.46 if row['enemy'] else 1.048 if kind=='attack' else .56 if kind=='support' else .46
   if kind in ['support','largePotion']:heals[target]=time+max(0,hit-.46)
   if kind in ['support','simpleGuard']:forms[target]=time+max(0,hit-.46)
  if prior:
   for uid,u in units.items():
    old=prior[uid];foot=feet[uid];absorbed=old['shield']-u['shield'];registered=row.get('hitPoints',{}).get(uid) if scenario.startswith('great-sword') and uid.startswith('m') else None
    if u['shield']>old['shield']:births[uid]=time
    if absorbed>0:contacts[uid]=time
    if absorbed>0 and u['shield']==0:breaks[uid]=time
    if u['hp']<old['hp'] or absorbed>0:
     emit.append({'kind':'shieldContact' if absorbed>0 else 'strike','at':time,'x':registered['x'] if registered else foot[0]+((5+240*.41)*hs if absorbed>0 else -80 if uid.startswith('m') else 0),'y':registered['y'] if registered else foot[1]-(65 if uid.startswith('p') else 72),'floor':foot[1]})
    if old['hp']>0 and u['hp']==0:emit.append({'kind':'death','at':time,'x':registered['x'] if registered else foot[0]-80,'y':registered['y'] if registered else foot[1]-72,'floor':foot[1]})
  for uid in ['p1','p2']:
   r={'kind':scenario+'-'+uid,'frame':row['frame'],'time':time,'shield':units[uid]['shield'],'emitters':[]}
   for key,source in [('recoveryAge',heals),('formation',forms),('birth',births),('contact',contacts),('broken',breaks)]:
    if uid in source and (key!='formation' or units[uid]['shield']==0):r[key]=time-source[uid]
   requests.append(r)
  requests.append({'kind':scenario+'-fx','frame':row['frame'],'time':time,'shield':0,'emitters':[{**{k:v for k,v in e.items() if k!='at'},'age':time-e['at']} for e in emit if time-e['at']<3]})
  prior=units
(D/'dice-light-requests.json').write_text(json.dumps(requests,separators=(',',':'))+'\n')
if '--prepare' in sys.argv:print(f'Prepared {len(requests)} production field requests');sys.exit(0)
legacy=json.loads((D/'dice-light-samples.json').read_text());attached={(r['kind'],r['frame']):r for r in legacy['frames']};reqs={(r['kind'],r['frame']):r for r in requests}
fontpath='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc';fonts={i:ImageFont.truetype(fontpath,i) for i in [14,16,17,18,20,22,24,26,30]}
# Current shared layout at1440x1080, no safe-area inset; production layout constants.
CW,CH=1440,1080;left=72;ww=1296;gap=18;head=(72,54,1296,76);detail=(72,852,1296,174);track=(72,754,1296,80);maprect=(72,148,599,588);stage=(689,148,679,588);scene_scale=stage[2]/1000
map_image=asset('MeadowGround');map_static=map_image.resize((599,588),Image.Resampling.LANCZOS)
# Map composition uses current map asset and real prop data; wind/Metal light are not simulated.
scene_data=json.loads((R/'Sources/Resources/SceneMap.json').read_text())
for prop in sorted(scene_data['props'],key=lambda x:x['y']):
 if not 0<prop['x']<1300 or not 0<prop['y']<1300:continue
 try:im=asset(prop['asset'])
 except Exception:continue
 w=round(prop['width']*.6);h=round(im.height/im.width*w);im=im.resize((max(1,w),max(1,h)),Image.Resampling.LANCZOS)
 if prop.get('mirror'):im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 x=round(prop['x']*.46);y=round(prop['y']*.46);map_static.alpha_composite(im,(x-w//2,y-h))
# Source pixels registered at same1000-wide world origin as production; overscan fills card height.
plate=env['env']['plate'].resize((1000,918),Image.Resampling.LANCZOS) if 'env' in env else None
# Use source four layers, not a recropped old preview.
scene_layers=[asset(n).resize((1000,918),Image.Resampling.LANCZOS) for n in ['MeadowCampFarForest','MeadowCampGround','MeadowCampMidground','MeadowCampForeground']]
world_h=round(stage[3]/scene_scale);oy=(world_h-600)/2
env['compose'].__globals__['H']=world_h
shadow.__globals__['W']=1000;shadow.__globals__['H']=world_h
back=Image.new('RGBA',(1000,world_h),'#1a2b20')
for im in scene_layers[:3]:back.alpha_composite(im,(0,round(oy-159)))
fg=Image.new('RGBA',back.size);fg.alpha_composite(scene_layers[3],(0,round(oy-159)))
enemy=asset('MeadowBattleForestWarden');attacks=env['enemy_attacks'];bodies,winds=env['bodies'],env['winds'];colors={'red':'#c72924','yellow':'#d9a129','green':'#219451','blue':'#1f70cc'}
def text(d,pos,s,size=20,color='#ffedc7'):d.text(pos,s,font=fonts[size],fill=color)
def box(d,r,fill='#192c21',outline='#998c55',rad=10,width=1):d.rounded_rectangle(r,rad,fill=fill,outline=outline,width=width)
def die_image(die,pose):
 im=Image.new('RGBA',(100,110));d=ImageDraw.Draw(im);c=colors[die['color']]
 d.polygon([(69,27),(77,33),(77,70),(69,77)],fill=c);d.polygon([(29,27),(37,21),(77,21),(69,27)],fill=c)
 d.rounded_rectangle((27,27,73,73),7,fill=c,outline='#fff0c8',width=2)
 mix=pose['resultMix'];moving=str(pose['face']) if die['sides']>0 else '?'
 def face(s,a):
  overlay=Image.new('RGBA',im.size);dd=ImageDraw.Draw(overlay);w=dd.textbbox((0,0),s,font=fonts[30])[2];dd.text((50-w/2,27),s,font=fonts[30],fill=(255,238,195,round(a*255)),stroke_width=1,stroke_fill=(20,30,20,round(a*170)));im.alpha_composite(overlay)
 face(moving,1-mix)
 if die.get('value') is not None:face(str(die['value']),mix)
 label=die['label'];w=d.textbbox((0,0),label,font=fonts[14])[2];text(d,(50-w/2,80),label,14)
 return im

def scene(row):
 f=back.copy();f=Image.blend(f,Image.new('RGBA',f.size,'black'),row['darkness']);time=row['time'];units={u['id']:u for u in row['units']};travel=row['travel']
 for uid in sorted(units,key=lambda uid:feet[uid][1]):
  u=units[uid];x,y=feet[uid];dx=travel['x'] if row['playing'] and uid==row['actor'] else 0;dy=travel['y'] if row['playing'] and uid==row['actor'] else 0
  if uid.startswith('p'):
   im=render(u['clip'],u['progress']);xx=x+dx-123*hs;yy=y+dy-214*hs
   shadow(f,im,xx,yy+oy,hs);f.alpha_composite(im.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(xx),round(yy+oy)))
   oldrow={'scenario':row['scenario'],'frame':row['frame'],'time':time,'action':{'actor':row['actor'],'target':row['target'],'age':row['age'],'travel':row['travel']} if row['playing'] else {}}
   # Reuse renderer attachment composition after translating world into overscan.
   layer=Image.new('RGBA',(1000,600));env['attached']=attached
   attachment=attached[(row['scenario']+'-'+uid,row['frame'])]
   env['attachments'].__globals__['REQUESTS']=reqs
   env['attachments'](layer,u,attachment,oldrow)
   f.alpha_composite(layer,(0,round(oy)))
  else:
   motion=u['monster'];dage=u['deathAge'];im=bodies[min(47,max(0,int(dage*60)))] if dage is not None else attacks[min(7,int(motion['progress']*8))]
   sy=1 if dage is not None else motion['scaleY'];recoil=0 if dage is not None else motion['recoil'];xx=x+dx-178.5*es+recoil;yy=y+dy-240*es*sy
   shadow(f,im,xx,yy+oy,es,alpha=1 if dage is None else 1-env['smooth'](dage/.75));size=(round(384*es),round(256*es*sy));im=im.resize(size,Image.Resampling.NEAREST)
   if dage is None and motion['flash']>0:
    white=Image.new('RGBA',size,'white');white.putalpha(im.getchannel('A').point(lambda a:round(a*motion['flash'])));im.alpha_composite(white)
   f.alpha_composite(im,(round(xx),round(yy+oy)))
   if dage is not None and dage<116/60:
    wind=winds[min(115,int(dage*60))].resize((round(448*es),round(320*es)),Image.Resampling.NEAREST);f.alpha_composite(wind,(round(x-178.5*es),round(y-272*es+oy)))
 f.alpha_composite(fg)
 # Retain release effects. Only selection preparation light is replaced by dice.
 if row['playing'] and row['action']=='support':
  start=env['env'].get('noop') if False else None
  fr=feet[row['actor']];to=feet[row['target']];a=row['age']
  for q in range(28):
   t=(a-q*.018)/.55
   if 0<t<1:
    x=(1-t)**2*(fr[0]+5*hs)+2*(1-t)*t*(fr[0]+to[0])/2+t*t*(to[0]+5*hs);y=(1-t)**2*(fr[1]-70*hs)+2*(1-t)*t*(min(fr[1],to[1])-70*hs-90)+t*t*(to[1]-70*hs)
    compose(f,asset('BattleVFXHealStar'),(x,y+oy),(11,11),math.sin(math.pi*t),True)
 if row['playing'] and row['action']=='attack':
  a=row['age']-(.46 if row['enemy'] else 1.048)
  if -.035<a<.7:
   p=feet[row['target']];at=(p[0]+(10 if row['enemy'] else -80),p[1]-(65 if row['enemy'] else 72)+oy);power=env['pulse'](a,-.035,.035,.52)
   glow(f,at,140,140,power*.48,(255,175,45));compose(f,asset('BattleVFXBurst'),at,(150+max(0,a)*140,150+max(0,a)*140),power,True)
   if not row['enemy']:compose(f,asset('BattleVFXHeavyArc'),at,(210+max(0,a)*240,210+max(0,a)*240),power*.9,True)
 for q in attached[(row['scenario']+'-fx',row['frame'])]['particles']:
  compose(f,asset('BattleVFXCyanShard' if q['cyan'] else 'BattleVFXGoldEmber'),(q['x'],q['y']+oy),(q['size'],q['size']*.67),q['alpha'],True,q['angle'])
 dd=ImageDraw.Draw(f)
 for uid,u in units.items():
  x,y=feet[uid];yy=y-(242 if uid.startswith('m') else 170)+oy
  box(dd,(x-88,yy,x+88,yy+44),fill='#172b20',outline=None,rad=5);text(dd,(x-80,yy),f'{uid.upper()}   {u["hp"]}/{u["maxHP"]}',17)
  dd.rectangle((x-80,yy+27,x+80,yy+34),fill='#06110a')
  if u['hp']>0:dd.rectangle((x-80,yy+27,x-80+160*u['hp']/u['maxHP'],yy+34),fill='#43d177')
  if u['shield']>0:dd.rectangle((x-80,yy+36,x-80+160*u['shield']/8,yy+40),fill='#41cfee')
 x=row['diceAnchor']['x'];y=row['diceAnchor']['y'];dx=0;dy=0
 for i,(die,pose) in enumerate(zip(row['dice'],row['dicePose'])):
  im=die_image(die,pose);im=im.resize((round(100*pose['scale']),round(110*pose['scale'])),Image.Resampling.BICUBIC).rotate(-math.degrees(pose['angle']),Image.Resampling.BICUBIC,expand=True);im.putalpha(im.getchannel('A').point(lambda a:round(a*pose['alpha'])))
  cx=x+dx+(i-(len(row['dice'])-1)/2)*62;cy=y+43+oy+pose['offsetY']
  f.alpha_composite(im,(round(cx-im.width/2),round(cy-50)))
 return f

def ui(row,world):
 f=Image.new('RGB',(CW,CH),'#0d1812');d=ImageDraw.Draw(f)
 def rect(r):x,y,w,h=r;return(x,y,x+w,y+h)
 box(d,rect(head));box(d,rect(stage));box(d,rect(track));box(d,rect(detail))
 f.paste(map_static.convert('RGB'),maprect[:2]);box(d,rect(maprect),fill=None)
 f.paste(world.resize((stage[2],stage[3]),Image.Resampling.LANCZOS).convert('RGB'),stage[:2])
 text(d,(88,62),f'小队支援 · {row["current"].upper()} 行动',26)
 text(d,(88,101),'按原单人布局 · 点选目标 / 技能',16,color='#bbcca9')
 for x,w,t in [(954,96,'重置演练'),(1058,178,'结束行动'),(1244,112,'返回单人')]:box(d,(x,70,x+w,114),fill='#eac668',outline=None,rad=8);text(d,(x+8,81),t,18,color='#192d21')
 box(d,(84,160,264,192),outline=None);text(d,(94,164),'Meadow Journey',18)
 ids=['p2','p1','m1','m2'];y=788;xs=[234+i*324 for i in range(4)]
 d.line((xs[0],y,xs[-1],y),fill='#657252',width=5);cur=ids.index(row['current'])
 if cur:d.line((xs[0],y,xs[cur],y),fill='#eac668',width=5)
 for uid,x in zip(ids,xs):
  current=uid==row['current'];d.ellipse((x-22,y-22,x+22,y+22),fill='#293c2d',outline='#eac668' if current or uid in row['acted'] else '#829476',width=3 if current else 2)
  if uid.startswith('p'):
   im=asset('Hero'+uid[1:]+'Directions');cell=im.height//4;im=im.crop((0,0,cell,cell)).resize((40,40),Image.Resampling.NEAREST);f.paste(im,(x-20,y-20),im)
  else:
   for px,py,rx,ry in [(-9,-7,4,6),(0,-12,4,6),(9,-7,4,6),(0,6,10,8)]:d.ellipse((x+px-rx,y+py-ry,x+px+rx,y+py+ry),fill='#eac668')
  text(d,(x-25,y+25),uid.upper() if uid.startswith('p') else '鹿灵'+('甲' if uid=='m1' else '乙'),16)
  if current:text(d,(x-8,y-34),'▼',14)
 u=next(u for u in row['units'] if u['id']==row['current'])
 for i,(title,v,m,c) in enumerate([('生命',u['hp'],u['maxHP'],'#48d17b'),('护盾',u['shield'],8,'#41cfee'),('行动',u['ap'],3 if u['id'].startswith('p') else 1,'#eac668')]):
  x=86+i*394;text(d,(x,862),f'{title} {v}/{m}',18);d.rectangle((x,891,x+370,900),fill='#07110b')
  if v:d.rectangle((x+1,892,x+1+368*min(1,v/m),899),fill=c)
 if u['buff']:box(d,(1268,860,1306,898),fill='#4b401b',outline='#eac668',rad=4);text(d,(1278,865),'↑',20)
 if u['shield']:box(d,(1313,860,1351,898),fill='#193b41',outline='#6ceaff',rad=4);text(d,(1319,865),'盾',20)
 titles=[('普通攻击','1D6＋当前增伤'),('援护','恢复6 / 盾4'),('振奋','友方增伤2 / 1轮')] if row['current']=='p2' else [('普通攻击','1D6＋当前增伤'),('强击','1D6＋2'),('喘息','自身恢复4'),('简易防护','自身护盾4')] if row['current']=='p1' else []
 cw=(1268-110-len(titles)*10)/max(1,len(titles))
 for i,(title,desc) in enumerate(titles):
  x=86+i*(cw+10);box(d,(x,914,x+cw,1016),fill='#2b4030',outline='#b8a568',rad=9);text(d,(x+10,921),title+' · 1 AP',20);text(d,(x+10,958),desc,17,color='#bbcca9')
 x=86+len(titles)*(cw+10);box(d,(x,914,x+100,1016),fill='#eac668',outline=None,rad=8);text(d,(x+25,950),'道具',20,color='#192d21')
 text(d,(72,1036),'build47 · 正常速度离线美术合成 · 非UIKit / 实机录屏 · 地图与光照为近似',16,color='#a4b99d')
 return f

if '--still' in sys.argv:
 row=next(r for r in rows if r['scenario']=='support' and r['frame']==25);ui(row,scene(row)).save(D/'layout-first.png');sys.exit(0)
reports=json.loads((D/'review-render.json').read_text())['animations'] if (D/'review-render.json').exists() else {}
for scenario in dict.fromkeys(r['scenario'] for r in rows):
 if '--only' in sys.argv and scenario not in sys.argv[sys.argv.index('--only')+1:]:continue
 group=[r for r in rows if r['scenario']==scenario];frames=[ui(row,scene(row)) for row in group]
 pal=Image.new('RGB',(CW*3,CH*3))
 for j,k in enumerate([0,15,40,55,70,85,100,len(frames)//2,len(frames)-1]):pal.paste(frames[k],(j%3*CW,j//3*CH))
 pal=pal.quantize(colors=256,method=Image.Quantize.MEDIANCUT);scale=.75;name=scenario+'-normal.gif'
 while True:
  size=(round(CW*scale),round(CH*scale));encoded=[f.resize(size,Image.Resampling.LANCZOS).quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
  encoded[0].save(D/name,save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=1,optimize=True)
  subprocess.run(['/workspace/gifsicle-1.96/src/gifsicle','-O3',str(D/name),'-o',str(D/(name+'.tmp'))],check=True);(D/(name+'.tmp')).replace(D/name)
  if (D/name).stat().st_size<19500000:break
  scale=round(scale-.1,2);assert scale>=.45
 gif=Image.open(D/name);assert gif.n_frames==len(frames)
 for page in range(math.ceil(len(frames)/30)):
  sheet=Image.new('RGB',(1440,1620),'#14251b')
  for j,k in enumerate(range(page*30,min(len(frames),(page+1)*30))):
   gif.seek(k);assert gif.info['duration']==20;thumb=gif.convert('RGB').resize((288,216));sheet.paste(thumb,(j%5*288,j//5*270));dd=ImageDraw.Draw(sheet);text(dd,(j%5*288,j//5*270+217),f'{k} / {k*.02:.2f}s',16)
  sheet.save(D/f'{scenario}-decoded-{page+1:02}.jpg',quality=90)
 for t,label in [(0,'standing'),(.5,'hover'),(1.1,'release'),(2.2 if scenario in ['attack-buff','lethal'] else 1.8,'result'),(3.4,'settled')]:frames[min(len(frames)-1,round(t/.02))].save(D/(scenario+'-'+label+'.png'))
 reports[scenario]={'file':name,'frames':len(frames),'frameDurationMs':20,'durationMs':len(frames)*20,'bytes':(D/name).stat().st_size,'dimensions':size};print(scenario,reports[scenario],flush=True)
(D/'review-render.json').write_text(json.dumps({'scope':'offline composition from production dice/monster and actual core receipts; not UIKit/device; map/lighting/UI approximated','animations':reports,'newArtApproval':None},indent=2)+'\n')
