#!/usr/bin/env python3
"""Offline full-scene rune review. Uses production geometry, receipts and unchanged parts.
Never UIKit, game, simulator or device capture.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,functools,subprocess,sys
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/spellblade-demo-v1';D.mkdir(parents=True,exist_ok=True)
p=R/'scripts/review-armor-demo.py';N={'__file__':str(p)};exec(compile(p.read_text().split('for item in armors:\n frames=[]')[0],str(p),'exec'),N)
p=R/'scripts/review-legendary-staff-demo.py';Q={'__file__':str(p)};exec(compile(p.read_text().split('reports=[]\nfor scenario')[0],str(p),'exec'),Q)
world=Q['world'];S=Q['S'];oldgear=Q['gear'];font=Q['font'];hs=world['hs'];oy=world['oy'];compose=world['compose'];glow=world['glow'];asset=Q['asset'];helpers=world['env']
rows=json.loads((D/'spellblade-frames.json').read_text());requests={(q['kind'],q['frame']):q for q in json.loads((D/'spellblade-light-requests.json').read_text())}
for q in json.loads((D/'spellblade-light-samples.json').read_text())['frames']:world['attached'][(q['kind'],q['frame'])]=q
world['reqs'].update(requests)
# The main review carries rune armor and a great sword; P2 remains the original sword.
S['gear_render']=world['gear_render']=lambda c,p,w:N['actor']('runeArmor',w,c,p) if w=='greatSword' else oldgear(c,p,w)
assert len(world['bodies'])==48 and len(world['winds'])==116
@functools.lru_cache(None)
def tinted(name,color):
 original=asset(name);im=Image.new('RGBA',original.size,(*color,0));im.putalpha(original.getchannel('A'));return im
colors={'violet':(92,64,255),'cyan':(31,191,255),'gold':(252,199,69),'green':(41,255,122),'white':(245,250,255)}
def actor_foot(u,row,overscan=True):
 f=world['feet'][u['id']];r=u.get('weaponPose');root=(r['rootOffset']['x'],r['rootOffset']['y']) if r else world['sample'](u['clip'],u['progress'])[1]
 return (f[0]+(5+root[0])*hs,f[1]+root[1]*hs+(oy if overscan else 0))
def ribbons(f,u,row,front=True,overscan=True):
 key=(row['scenario']+'-'+u['id'],row['frame']);q=world['attached'][key];intensity=requests[key].get('recoveryStrength',1);foot=actor_foot(u,row,overscan)
 layer=Image.new('RGBA',f.size);d=ImageDraw.Draw(layer)
 for strand in q['ribbons']:
  for start in range(0,max(0,len(strand)-1),3):
   segments=[];alphas=[]
   for j in range(start,min(len(strand)-1,start+3)):
    a,b=strand[j],strand[j+1]
    if ((a['depth']+b['depth'])/2>=0)!=front:continue
    segments.append([(foot[0]+a['x']*hs,foot[1]+a['y']*hs),(foot[0]+b['x']*hs,foot[1]+b['y']*hs)]);alphas.append((a['alpha']+b['alpha'])/2)
   if not segments:continue
   alpha=sum(alphas)/len(alphas)*(1 if front else .58)
   for width,color,weight in [(9*intensity,(20,242,102),.2),(3.2*intensity,(102,255,163),.9),(1.1*math.sqrt(intensity),(219,255,207),.85)]:
    for seg in segments:d.line(seg,fill=(*color,round(alpha*weight*255)),width=max(1,round(width*hs)))
 S['add_layer'](f,layer)
world['draw_ribbons']=ribbons
# Match current attached shield, pulse, three optical masks and both depth strands.
def attachments(f,u,q,row):
 key=(row['scenario']+'-'+u['id'],row['frame']);req=requests[key];intensity=req.get('recoveryStrength',1);short={'scenario':row['scenario'],'frame':row['frame'],'actor':row['action'].get('actor',''),'travel':row['action'].get('travel',{}),'playing':bool(row['action'])}
 foot=actor_foot(u,short,False);center=(foot[0],foot[1]-70*hs);alpha=q['shieldOpacity']
 compose(f,asset('BattleVFXRoundBarrier'),center,(240*hs,240*hs),alpha)
 for i in range(6):
  angle=row['time']*1.25+i*2.399;radius=240*hs*.41;size=(9 if i%2==0 else 6)*hs
  im=tinted('BattleVFXMote',(80,245,255));compose(f,im,(center[0]+math.cos(angle)*radius,center[1]+math.sin(angle)*radius),(size,size),alpha*.65)
 age=req.get('recoveryAge',-1);power=q['recoveryPower']
 if 0<=age<1.8:
  compose(f,asset('BattleVFXHealShaft'),(foot[0],foot[1]-82.5*hs),(110*hs,185*hs),power*.10*intensity)
  compose(f,tinted('BattleVFXBurst',(209,255,217)),(foot[0],foot[1]-64*hs),(110*hs,110*hs),world['env']['pulse'](age,.34,.47,.70)*.25*min(1.5,intensity))
  expansion=.65+.65*world['env']['smooth'](age/1.1);compose(f,asset('BattleVFXHealWave'),(foot[0],foot[1]+2*hs),(164*hs*expansion,28*hs),power*.35*min(1.5,intensity))
  for star in q['recovery']:
   size=star['size']*(1+(intensity-1)*.35)*hs;compose(f,asset('BattleVFXHealStar'),(foot[0]+star['x']*hs,foot[1]+star['y']*hs),(size,size),min(1,star['alpha']*intensity))
 ribbons(f,u,short,True,False)
helpers['attachments']=attachments

def recovery_lights(f,row):
 for u in row['units']:
  if not u['id'].startswith('p'):continue
  key=(row['scenario']+'-'+u['id'],row['frame']);q=world['attached'][key];power=q['recoveryPower']*requests[key].get('recoveryStrength',1);foot=world['feet'][u['id']]
  glow(f,(foot[0],foot[1]+oy),105,27,power*.65,(51,199,89));glow(f,(foot[0],foot[1]-70+oy),42,85,power*.12,(51,199,89))
world['draw_recovery_lights']=recovery_lights

def draw_runes(f,row):
 q=row['runes']
 for v in q['glows']:glow(f,(v['point']['x'],v['point']['y']+oy),v['rx'],v['ry'],v['alpha'],colors[v['color']])
 # Every stroke adds independently, just like CGContext plusLighter.
 for stroke in q['strokes']:
  layer=Image.new('RGBA',f.size);d=ImageDraw.Draw(layer);pts=[(v['x'],v['y']+oy) for v in stroke['points']]
  d.line(pts,fill=(*colors[stroke['color']],round(stroke['alpha']*255)),width=max(1,round(stroke['width'])),joint='curve');S['add_layer'](f,layer)
 layer=Image.new('RGBA',f.size);d=ImageDraw.Draw(layer)
 for m in q['motes']:
  x,y=m['point']['x'],m['point']['y']+oy;s=m['size'];a=m['angle'];color=colors[m['color']]
  pts=[(x+xx*math.cos(a)-yy*math.sin(a),y+xx*math.sin(a)+yy*math.cos(a)) for xx,yy in [(0,-s/2),(s/3,0),(0,s/2),(-s/3,0)]]
  d.polygon(pts,fill=(*color,round(m['alpha']*255)))
  if m['id']%6==0:glow(f,(x,y),18,14,m['alpha']*.20,color)
  if m.get('groundAge') is not None and m['groundAge']<.25:glow(f,(m['ground']['x'],m['ground']['y']+oy),28,8,m['alpha']*(1-m['groundAge']/.25)*.55,color)
 S['add_layer'](f,layer)
world['draw_projectile']=draw_runes

def numbers(f,row):
 layer=Image.new('RGBA',f.size);d=ImageDraw.Draw(layer)
 for m in row['damageLabels']:
  age=row['time']-m['at'];a=1-world['env']['smooth']((age-.65)/.35);text=m['text'];c=(255,255,255) if text.startswith('−') else (51,199,89) if text.startswith('＋') else (50,210,255) if text.startswith('盾') else (235,197,107)
  ft=font(24);b=d.textbbox((0,0),text,font=ft);w,h=b[2]-b[0],b[3]-b[1]
  # Damage is centered at contact. Other effect-label origins are exported at
  # the actual separate lines from the same receipt tick.
  if m.get('supportUnit'):
   foot=world['feet'][m['supportUnit']];x=max(4,foot[0]-14-w);y=foot[1]-86+m['supportLine']*36+oy-age*26
  else:x=m['x']-w/2;y=m['y']+oy-h/2-age*26
  d.text((x-b[0],y-b[1]),text,font=ft,fill=(*c,round(a*255)),stroke_width=2,stroke_fill=(0,0,0,round(a*255)))
 f.alpha_composite(layer)
world['draw_damage']=numbers
old_ui=Q['ui']
def ui(row):
 f=old_ui(row,S['scene'](row));d=ImageDraw.Draw(f);u=next(x for x in row['units'] if x['id']=='p1')
 d.rounded_rectangle((954,70,1050,114),8,fill='#eac668');d.text((962,81),'演练设置',font=font(18),fill='#192b21')
 d.rectangle((80,58,660,135),fill='#192b21');d.text((88,66),'小队支援 · P1 魔剑士',font=font(25),fill='#f9edc4');d.text((88,103),{'runeSlash':'符文斩','runeWard':'符文庇护','battleRune':'战斗符文'}[row['action']]+(' · 悬停预示' if row['hover'] else ' · 动作进行中' if row['playing'] else ' · 结算完成'),font=font(18),fill='#bbcba9')
 d.rectangle((80,853,1356,905),fill='#192b21')
 for i,(name,value,maxi,color) in enumerate([('生命',u['hp'],u['maxHP'],'#45d27b'),('护盾',u['shield'],8,'#41cfee'),('行动',u['ap'],u['baseAP'],'#eac668')]):
  x=86+i*372;d.text((x,858),name+(f' {value}/{maxi}' if i<2 else ''),font=font(20),fill='#f9edc4')
  if i<2:
   d.rectangle((x,893,x+350,902),fill='#07110b')
   if value:d.rectangle((x+1,894,x+1+348*min(1,value/maxi),901),fill=color)
  else:
   for j in range(maxi):
    cx=x+10+j*28;cy=897;h=9;d.polygon([(cx,cy-h),(cx+h,cy),(cx,cy+h),(cx-h,cy)],fill=color if j<value else '#303c28',outline=color)
 for x,icon,color,enabled in [(1215,'','#eac668',True),(1260,'↑','#eac668',u['buff']>0),(1305,'盾','#41cfee',u['shield']>0)]:
  if enabled:d.rounded_rectangle((x,859,x+38,897),4,outline=color,width=2);d.text((x+8,862),icon,font=font(22),fill=color)
 badge=asset('MeadowPowerBadge').resize((30,30),Image.Resampling.LANCZOS);f.paste(badge,(1219,863),badge)
 d.rectangle((80,910,1356,1020),fill='#192b21');titles=[('普通攻击','1D12 · 增伤＋'+str(u['attributeDamage']),1),('符文斩','2D12＋2 · 自身恢复4 / 盾4',2),('符文庇护','节点队友恢复8 / 盾6',2),('战斗符文','节点盾4 / 增伤3 · 2轮',1)]
 cw=(1268-110-40)/4
 for i,(name,desc,cost) in enumerate(titles):
  x=86+i*(cw+10);d.rounded_rectangle((round(x),914,round(x+cw),1016),8,fill='#2b4030',outline='#b8a568');d.text((round(x+9),921),name+f' · {cost} AP',font=font(20),fill='#f9edc4');d.text((round(x+9),964),desc,font=font(16),fill='#bbcba9')
 x=86+4*(cw+10);d.rounded_rectangle((round(x),914,round(x+100),1016),8,fill='#eac668');d.text((round(x+25),950),'道具',font=font(20),fill='#192b21')
 d.rectangle((0,f.height-50,f.width,f.height),fill='#0b1811');d.text((35,f.height-29),'Build66 · 正常速度离线美术合成 · 生产规则／符文几何 · 非UIKit／实机录屏',font=font(18),fill='#bbcba9')
 return f.convert('RGB').resize((1020,765),Image.Resampling.LANCZOS)

def stills():
 for scenario in dict.fromkeys(r['scenario'] for r in rows):
  group=[r for r in rows if r['scenario']==scenario];impact=next(r['time'] for r in group if r['impact'] is not None)
  for tm,label in [(0,'standing'),(.6,'hover'),(1.45,'unfold'),(impact+.06,'impact'),(impact+.36,'recovery'),(3.50,'tail'),(4.6,'rest')]:
   row=min(group,key=lambda r:abs(r['time']-tm));ui(row).save(D/(scenario+'-'+label+'.png'))
if '--draft' in sys.argv:stills();print('35 whole-scene keyframes rendered');sys.exit(0)
reports=[]
def save(name,frames):
 pal=Image.new('RGB',(4080,3060))
 for i in range(16):pal.paste(frames[round(i*(len(frames)-1)/15)],(i%4*1020,i//4*765))
 palette=pal.quantize(colors=256);encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames];path=D/(name+'-normal.gif');encoded[0].save(path,save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=2,optimize=False)
 tool=Path('/workspace/gifsicle-1.96/src/gifsicle')
 if tool.exists():temp=path.with_suffix('.opt.gif');subprocess.run([str(tool),'-O3',str(path),'-o',str(temp)],check=True);temp.replace(path)
 gif=Image.open(path);duration=0
 # 25 actual decoded full-scene thumbnails per page, supplemented by full-sized
 # contact/formation/return stills and native whole-body checks.
 for page in range(math.ceil(gif.n_frames/25)):
  sheet=Image.new('RGB',(1280,1100),'#20372a');dd=ImageDraw.Draw(sheet)
  for j in range(25):
   n=page*25+j
   if n>=gif.n_frames:break
   gif.seek(n);duration+=gif.info['duration'];sheet.paste(gif.convert('RGB').resize((256,192)),(j%5*256,j//5*220));dd.text((j%5*256+4,j//5*220+193),f'{name} {n}',font=font(13),fill='#f0e4b6')
  sheet.save(D/f'{name}-decoded-{page+1:02}.png')
 assert duration==len(frames)*20
 info={'file':path.name,'decodedFrames':gif.n_frames,'durationMs':duration,'size':[1020,765]};reports.append(info);print(info,flush=True)
for scenario in ['runeSlash','runeWard','battleRune','runeSlash-lethal']:
 save(scenario,[ui(r) for r in rows if r['scenario']==scenario])
overview=[]
for name in ['runeSlash','runeWard','battleRune']:
 gif=Image.open(D/(name+'-normal.gif'))
 for i in range(gif.n_frames):gif.seek(i);overview.append(gif.convert('RGB').copy())
save('three-skills',overview)
stills()
# Current same guard curve, native outfit/weapon layers, full body1x and2x.
mounts=[('trainingSword',None),('greatSword','runeArmor'),('legendaryStaff','runeArmor'),('huntingBow','leatherArmor'),(None,None)]
board=Image.new('RGB',(1280,len(mounts)*280),'#20372a')
for j,(w,armor) in enumerate(mounts):
 for i,p in enumerate([0,.25,.5,.75,1]):
  im=N['actor'](armor,w,'guard',p) if armor else oldgear('guard',p,w);x=i*256;y=j*280
  board.paste(im,(x,y),im);ImageDraw.Draw(board).text((x+4,y+257),f'{w or "unarmed"} guard{p:.2f}',font=font(13),fill='#f0e4b6')
board.save(D/'cast-mounts-1x.png');board.resize((2560,len(mounts)*560),Image.Resampling.NEAREST).save(D/'cast-mounts-2x.png')
(D/'review.json').write_text(json.dumps({'scope':'Production original-rule receipts, pose/dice/rune fields; unchanged original parts; approximate offline scene/light/UI. Not UIKit/game/device.','animations':reports,'keyframePNGs':35,'newCharacterArt':False,'userArtApproval':None},ensure_ascii=False,indent=2)+'\n')
