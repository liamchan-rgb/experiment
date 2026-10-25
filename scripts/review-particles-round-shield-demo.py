#!/usr/bin/env python3
"""Offline art review from imported assets and production Swift traces; not UIKit."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageChops
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Art/Review/Battle/particles-round-shield-demo-v1';OUT.mkdir(exist_ok=True,parents=True)
base=ROOT/'scripts/review-battle-effects-demo.py';env={'__file__':str(base)}
exec(compile(base.read_text().split('\nframes=[]; traces=[]')[0],str(base),'exec'),env)
W,H,UI=env['W'],env['H'],env['UI'];plate,foreground=env['plate'],env['foreground'];render,sample=env['render'],env['sample'];asset=env['asset'];smooth,pulse=env['smooth'],env['pulse'];hs,es,hx,hy,ex,ey=[env[k] for k in ['hs','es','hx','hy','ex','ey']];point=env['point'];shadow=env['shadow'];light=env['light'];font,small,large=[env[k] for k in ['font','small','large']]
assets={n:asset('BattleVFX'+n) for n in ['HeavyArc','HeavySpray','Barrier','WardHit','HeavyHitMask','RoundBarrier','CyanShard','GoldEmber','GroundSpark','Slash','Burst','Mote','Ring']}
body=asset('BattleVFXDeathBody');wind=asset('BattleVFXDeathWindHeavy')
bodies=[body.crop(((i%8)*384,(i//8)*256,(i%8+1)*384,(i//8+1)*256)) for i in range(48)]
winds=[wind.crop(((i%8)*640,(i//8)*320,(i%8+1)*640,(i//8+1)*320)) for i in range(48)]
enemy=asset('MeadowBattleForestWarden');sheet=asset('MeadowBattleWardenAttackSheet');cell=sheet.width//8;enemy_attack=[sheet.crop((i*cell,0,(i+1)*cell,sheet.height)) for i in range(8)]
trace_path=OUT/'controller-trace.json'
if not trace_path.exists():trace_path=OUT/'controller-trace-linux.json'
control=json.loads(trace_path.read_text());last=[r for r in control['lastStrike'] if r['fps']==30];ward=[r for r in control['shieldSequence'] if r['fps']==30]
HIT=2.6+next(r['elapsed'] for r in last if r['impact']);BIRTH=next(r['time'] for r in ward if r['gained']>0);BLOCK=next(r['time'] for r in ward if r['absorbed']>0)
contact=sample('attack',.54);tip=point((191,142),contact[0]['MeadowBattleHeroWeapon']);reach=hx+(tip[0]+contact[1][0])*hs;travel=min(W*.22,max(0,ex+125*es-reach));impact=(reach+travel,hy+(tip[1]+contact[1][1])*hs)

def compose(frame,image,center,size,alpha=1,add=False):
 if alpha<=0:return
 im=image.resize((max(1,round(size[0])),max(1,round(size[1]))),Image.Resampling.LANCZOS)
 if alpha<1:im.putalpha(im.getchannel('A').point(lambda a:round(a*alpha)))
 x,y=round(center[0]-im.width/2),round(center[1]-im.height/2)
 if not add:frame.alpha_composite(im,(x,y));return
 left,top=max(0,x),max(0,y);right,bottom=min(frame.width,x+im.width),min(frame.height,y+im.height)
 if left>=right or top>=bottom:return
 src=im.crop((left-x,top-y,right-x,bottom-y));premul=ImageChops.multiply(src.convert('RGB'),src.getchannel('A').convert('RGB'));old=frame.crop((left,top,right,bottom)).convert('RGB');lit=ImageChops.add(old,premul);frame.paste(lit,(left,top))

def optics(f,key,c,w,h,a=1):compose(f,assets[key],c,(w,h),a,True)

def blue_ground(f,at,strength):
 if strength<=0:return
 overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
 d.ellipse((at[0]-75,at[1]-20,at[0]+75,at[1]+20),fill=(30,200,255,round(strength*120)))
 from PIL import ImageFilter
 f.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(16)))

def camera(f,age,kind):
 shake=4*(1-smooth(age/.28)) if kind=='attack' and 0<=age<.5 else 1.5*(1-smooth(age/.22)) if 0<=age<.22 else 0
 zoom=.045*(1-smooth(age/.5)) if kind=='attack' and 0<=age<.5 else 0
 dx=math.sin(age*83)*shake;dy=math.cos(age*64)*shake*.55;scale=1+zoom
 return f.transform((W,H),Image.Transform.AFFINE,(1/scale,0,W/2-(W/2+dx)/scale,0,1/scale,H/2-(H/2+dy)/scale),Image.Resampling.BICUBIC)

def ui(scene,t,kind,hp=3,shield=0,damage=False):
 f=Image.new('RGBA',(W,H+UI),(15,24,22,255));f.alpha_composite(scene);d=ImageDraw.Draw(f)
 d.rectangle((0,0,W,35),fill=(12,23,22,235));d.text((16,6),'build42 · 强击与护盾离线美术复核',font=font,fill='#f5e8c7');d.text((W-215,10),f'非实机  {t:04.2f}s',font=small,fill='#bbc5bc')
 stage=('致死命中 · 同步右吹' if damage else '强技能预示' if 1.6<=t<2.6 else '强击') if kind=='attack' else '护盾展开' if t<.96 else '持续护盾' if t<2 else '格挡 · 最后盾值耗尽' if t>=BLOCK else '鹿灵冲撞'
 d.text((18,H-35),stage,font=font,fill='#ffe9b8')
 d.text((18,H+8),'固定强度 · 无蓄力层级',font=small,fill='#becbbf')
 for x,title,detail in [(18,'强击','5点伤害 · 1AP'),(270,'简易防护','4点护盾 · 1AP')]:
  active=(kind=='attack' and x==18 and 1.6<=t<4.3) or (kind=='shield' and x==270 and t<.96)
  d.rounded_rectangle((x,H+34,x+234,H+96),8,fill='#29372b',outline='#ffe3a1' if active else '#586858',width=2 if active else 1)
  d.text((x+13,H+39),title,font=font,fill='#ffe5b2');d.text((x+13,H+68),detail,font=small,fill='#aabb9f')
 d.text((530,H+43),f'鹿灵 HP {hp}/18' if kind=='attack' else f'P1 HP 12/12 盾{shield}',font=font,fill='#d3ddcc')
 d.text((530,H+72),'素材与生产时钟共享 · 光照近似',font=small,fill='#aabb9f')
 return f.convert('RGB')

def pose_time(elapsed):
 a=max(0,elapsed-.4);return max(0,a-min(.10,max(0,a-.648)))

debris_rows=json.loads((OUT/'production-light-trajectories.json').read_text())
debris_frames={(r['kind'],r['frame']):r['particles'] for r in debris_rows}

def colored_light(f,center,rx,ry,alpha,cyan=False):
 if alpha<=0:return
 # Local additive illumination of existing environment pixels, no repaint.
 from PIL import ImageFilter
 overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
 d.ellipse((center[0]-rx*.65,center[1]-ry*.65,center[0]+rx*.65,center[1]+ry*.65),fill=(18,130,255,round(160*alpha)) if cyan else (255,175,45,round(140*alpha)))
 overlay=overlay.filter(ImageFilter.GaussianBlur(max(2,ry*.4)))
 compose(f,overlay,(W/2,H/2),(W,H),1,True)

def debris_ground(f,particles):
 pools=0
 for q in particles:
  if q['id']%6==0:colored_light(f,(q['x'],q['y']),24,20,q['alpha']*.25,q['cyan'])
  if q['groundAge'] is not None and q['groundAge']<.24 and pools<12:
   a=(1-q['groundAge']/.24)*q['alpha'];c=(q['groundX'],q['groundY']);colored_light(f,c,36,10,a*.65,q['cyan']);optics(f,'WardHit' if q['cyan'] else 'GroundSpark',c,30,12,a*.9);pools+=1

def debris_front(f,particles):
 for q in particles:
  sprite=assets['CyanShard' if q['cyan'] else 'GoldEmber'].resize((max(1,round(q['size'])),max(1,round(q['size']*.67))),Image.Resampling.LANCZOS)
  angle=q['angle']+(math.pi/4 if q['cyan'] else -math.pi*.75)
  sprite=sprite.rotate(-math.degrees(angle),resample=Image.Resampling.BICUBIC,expand=True)
  compose(f,sprite,(q['x'],q['y']),sprite.size,q['alpha'],True)

all_reports={}
for kind,count in [('attack',165),('shield',120)]:
 frames=[];events=[]
 for i in range(count):
  t=i*.04;fo=(W*.29,H*.69);ef=(W*.65,H*.685);debris=debris_frames[(kind,i)]
  if kind=='attack':
   elapsed=max(0,t-2.6);p=min(1,pose_time(elapsed)/1.2);a=t-HIT;dead=t>=HIT;focus=1.6<=t<2.6;fe=smooth((t-1.6)/.28) if focus else 0
   dim=.45*fe if t<2.6 else (.45+(.64-.45)*smooth(elapsed/.44))*(1-smooth((elapsed-2)/1.36))
   if dead:dim=max(dim,.82*pulse(a,0,.035,.225))
   clip='attack' if 3<=t<4.3 else 'victory' if 4.3<=t<5.38 else 'idle';pr=p if clip=='attack' else min(1,(t-4.3)/1.08) if clip=='victory' else t%2.4/2.4
   hero=render(clip,pr);approach=0 if clip!='attack' or p<.12 else smooth((p-.12)/.28) if p<.4 else 1 if p<=.66 else smooth((1-p)/.34)
   tx=travel*approach;recoil=W*.025*pulse(a,-.02,.14,.52) if dead else 0
   monster=bodies[min(47,int(max(0,a)/.04))] if dead else enemy
   f=ImageEnhance.Brightness(plate).enhance(1-dim)
   burst=pulse(a,-.035,.035,.52) if dead else 0
   light(f,impact,(195,190),burst*.9);light(f,(impact[0]+20,ef[1]),(235,55),burst)
   if burst>0:optics(f,'HeavySpray',(impact[0]+45,ef[1]-3),260*(1+max(0,a)*2),35,burst*.55)
   debris_ground(f,debris)
   if dead and a<1.4:
    colored_light(f,(impact[0]+a*95,ef[1]),180,42,.38*(1-smooth(a/1.4)))
    colored_light(f,(impact[0]+a*90,impact[1]),115,95,.18*(1-smooth(a/1.4)))
   shadow(f,hero,hx+tx,hy,hs);shadow(f,monster,ex+recoil,ey,es)
   f.alpha_composite(hero.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(hx+tx),round(hy)))
   f.alpha_composite(ImageEnhance.Brightness(monster).enhance(1-dim*.55).resize((round(384*es),round(256*es)),Image.Resampling.NEAREST),(round(ex+recoil),round(ey)))
   if dead:
    wind=winds[min(47,int(a/.04))];f.alpha_composite(wind.resize((round(640*es),round(320*es)),Image.Resampling.LANCZOS),(round(ex),round(ey-32*es)))
   f.alpha_composite(ImageEnhance.Brightness(foreground).enhance(1-dim))
   ring=.9*.7*fe if focus else .65*(1-smooth((elapsed-.24)/.16)) if 2.6<=t<3 else 0
   optics(f,'Ring',fo,110,46,ring)
   if focus:
    for j in range(7):
     angle=j*2.399+t*1.7;optics(f,'Mote',(fo[0]+math.cos(angle)*31,fo[1]-58+math.sin(angle)*24),12,12,.9*fe*.9)
   if burst>0:
    spread=max(0,a);optics(f,'Slash',impact,225,225,pulse(a,-.06,0,.25));optics(f,'HeavyArc',impact,245+spread*220,245+spread*220,burst*.95);optics(f,'Burst',impact,205+spread*145,205+spread*145,burst)
    optics(f,'HeavySpray',(impact[0]+95+spread*75,impact[1]-15),250+spread*180,160,burst*.9)
    for j in range(26):
     ang=j*2.399;dist=spread*(150+(j%5)*38);optics(f,'Mote',(impact[0]+math.cos(ang)*dist,impact[1]+math.sin(ang)*dist),22 if j%4==0 else 10,7 if j%4==0 else 10,burst*.9)
   debris_front(f,debris)
   f=camera(f,a,'attack') if dead else f
   if dead and a<.7:ImageDraw.Draw(f).text((impact[0]+20,impact[1]-40-a*30),'3',font=large,fill='#fff3cd',stroke_width=2,stroke_fill='#463016')
   frame=ui(f,t,kind,0 if dead else 3,damage=dead)
   events.append({'frame':i,'timeMs':i*40,'hp':0 if dead else 3,'damageVisible':dead and a<.7,'deathActive':dead,'ringAlpha':ring,'darken':dim,'cameraAge':max(0,a) if dead else None})
  else:
   shield=0 if t<BIRTH else 4 if t<BLOCK else 0
   spawn_age=t-BIRTH;contact_age=t-BLOCK;spawn=pulse(spawn_age,0,.10,.45) if spawn_age>=0 else 0;hit=pulse(contact_age,-.02,.025,.38) if contact_age>=0 else 0
   enemy_p=min(1,max(0,(t-2)/.96)) if t>=2 else 0
   if t<.96:clip='guard';pr=t/.96
   elif t>=BLOCK and t<3.44:clip='guard';pr=min(1,contact_age/.96)
   else:clip='idle';pr=t%2.4/2.4
   hero=render(clip,pr);monster=enemy_attack[min(7,int(enemy_p*8))] if 2<=t<3.44 else enemy
   enemy_tx=-max(0,ex+42*es-(hx+128*hs+60*hs)-W*.015)*pulse(enemy_p,.08,.48,.98) if 2<=t<3.44 else 0
   f=plate.copy();blue_ground(f,fo,spawn*.7+hit*.9);debris_ground(f,debris);shadow(f,hero,hx,hy,hs);shadow(f,monster,ex+enemy_tx,ey,es)
   f.alpha_composite(hero.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(hx),round(hy)))
   f.alpha_composite(monster.resize((round(384*es),round(256*es)),Image.Resampling.NEAREST),(round(ex+enemy_tx),round(ey)))
   f.alpha_composite(foreground)
   wc=(fo[0]+6,fo[1]-66);scale=.68+.32*smooth(spawn_age/.28) if spawn_age>=0 else 1
   alpha=.60+spawn*.4+hit*.4 if shield>0 else 0
   if 0<=contact_age<.25:alpha=max(alpha,.95*(1-smooth(contact_age/.25)))
   optics(f,'RoundBarrier',wc,132*scale,132*scale,alpha)
   if 0<=contact_age<.4:
    size=80+contact_age*150;optics(f,'WardHit',(fo[0]+65+size*.33,fo[1]-66),size,size,hit*.9)
   debris_front(f,debris)
   f=camera(f,contact_age,'shield') if contact_age>=0 else f
   if 0<=contact_age<.7:ImageDraw.Draw(f).text((fo[0]+20,fo[1]-105),'格挡',font=large,fill='#bfffff',stroke_width=2,stroke_fill='#123b48')
   frame=ui(f,t,kind,18,shield)
   events.append({'frame':i,'timeMs':i*40,'heroHP':12,'shield':shield,'generation':spawn_age>=0,'block':contact_age>=0,'breakAge':max(0,contact_age) if contact_age>=0 else None})
  frames.append(frame)
 palette_source=Image.new('RGB',(W*3,(H+UI)*3))
 for j,k in enumerate([0,count//5,count//3,count//2,min(count-1,int((HIT if kind=='attack' else BLOCK)/.04)),min(count-1,int((HIT+.12 if kind=='attack' else BIRTH+.12)/.04)),count*3//4,count*4//5,count-1]):palette_source.paste(frames[k],((j%3)*W,(j//3)*(H+UI)))
 pal=palette_source.quantize(colors=256,method=Image.Quantize.MEDIANCUT);encoded=[f.quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
 name='heavy-strike-normal.gif' if kind=='attack' else 'shield-normal.gif';encoded[0].save(OUT/name,save_all=True,append_images=encoded[1:],duration=40,loop=0,disposal=1,optimize=True)
 gif=Image.open(OUT/name);assert gif.n_frames==count
 for page in range(math.ceil(count/24)):
  sheet=Image.new('RGB',(1520,2424),'#111a15')
  for j,k in enumerate(range(page*24,min(count,(page+1)*24))):
   gif.seek(k);assert gif.info['duration']==40;sheet.paste(gif.convert('RGB').resize((380,404)),((j%4)*380,(j//4)*404))
  sheet.save(OUT/f'{kind}-decoded-{page+1:02}.jpg',quality=88)
 frames[0].save(OUT/f'{kind}-standing.png')
 for sec,label in ([(HIT+.03,'impact'),(HIT+.3,'dissolve'),(HIT+.82,'ground-contact')] if kind=='attack' else [(BIRTH+.12,'generation'),(1.5,'sustain'),(BLOCK+.04,'block'),(BLOCK+.24,'break'),(BLOCK+.65,'ground-contact')]):frames[min(count-1,round(sec/.04))].save(OUT/f'{kind}-{label}.png')
 (OUT/f'{kind}-trace.json').write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n');all_reports[kind]={'frames':count,'frameDurationMs':40,'durationMs':count*40,'gifBytes':(OUT/name).stat().st_size,'file':name}
(OUT/'review-render.json').write_text(json.dumps({'scope':'offline shared art and production Swift events; not UIKit/GPU/device capture','productionTrace':str(trace_path.relative_to(ROOT)),'hitTime':HIT,'shieldBirth':BIRTH,'shieldBlockBreak':BLOCK,'animations':all_reports,'lightTrajectories':'production-light-trajectories.json','artApproval':None},indent=2)+'\n')
print(json.dumps(all_reports))
