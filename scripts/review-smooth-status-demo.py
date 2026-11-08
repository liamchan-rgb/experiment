#!/usr/bin/env python3
"""Offline art review from imported assets and production Swift traces; not UIKit."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageChops
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Art/Review/Battle/smooth-status-demo-v1';OUT.mkdir(exist_ok=True,parents=True)
base=ROOT/'scripts/review-battle-effects-demo.py';env={'__file__':str(base)}
exec(compile(base.read_text().split('\nframes=[]; traces=[]')[0],str(base),'exec'),env)
W,H,UI=env['W'],env['H'],env['UI'];plate,foreground=env['plate'],env['foreground'];render,sample=env['render'],env['sample'];asset=env['asset'];smooth,pulse=env['smooth'],env['pulse'];hs,es,hx,hy,ex,ey=[env[k] for k in ['hs','es','hx','hy','ex','ey']];point=env['point'];shadow=env['shadow'];light=env['light'];font,small,large=[env[k] for k in ['font','small','large']]
UI=160
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',20)
small=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',17)
assets={n:asset('BattleVFX'+n) for n in ['HeavyArc','HeavySpray','Barrier','WardHit','HeavyHitMask','HealStar','HealWisp','HealShaft','HealWave','RoundBarrier','CyanShard','GoldEmber','GroundSpark','Slash','Burst','Mote','Ring']}
body=asset('BattleVFXDeathBody60');wind=asset('BattleVFXDeathWind60')
bodies=[body.crop(((i%8)*384,(i//8)*256,(i%8+1)*384,(i//8+1)*256)) for i in range(48)]
winds=[wind.crop(((i%8)*448,(i//8)*320,(i%8+1)*448,(i//8+1)*320)) for i in range(116)]
enemy=asset('MeadowBattleForestWarden');sheet=asset('MeadowBattleWardenAttackSheet');cell=sheet.width//8;enemy_attack=[sheet.crop((i*cell,0,(i+1)*cell,sheet.height)) for i in range(8)]
trace_path=OUT/'controller-trace.json'
if not trace_path.exists():trace_path=OUT/'controller-trace-linux.json'
control=json.loads(trace_path.read_text());last=[r for r in control['lastStrike'] if r['fps']==60];ward=[r for r in control['shieldSequence'] if r['fps']==60]
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
 d.rectangle((0,0,W,35),fill=(12,23,22,235));d.text((16,6),'build44 · 强击与护盾离线美术复核',font=font,fill='#f5e8c7');d.text((W-215,10),f'非实机  {t:04.2f}s',font=small,fill='#bbc5bc')
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

# This script samples the existing actor, but reads all new light/recovery motion
# and shield geometry directly from the production Swift exporter.
import sys
SHIELD_ATTACK=1.4
SHIELD_HIT=SHIELD_ATTACK+(HIT-2.6)
BLOCK=4+(BLOCK-2)
HEAL_START=.6
healtrace=[r for r in control['healSequence'] if r['fps']==60]
HEAL_HIT=HEAL_START+next(r['elapsed'] for r in healtrace if r['healed']>0)
COUNTS={'attack':330,'shield':360,'heal':190}

def pose_state(kind,t):
 tx=0
 if kind=='attack':
  clip='attack' if 3<=t<4.3 else 'victory' if 4.3<=t<5.38 else 'idle'
  pr=min(1,pose_time(max(0,t-2.6))/1.2) if clip=='attack' else min(1,(t-4.3)/1.08) if clip=='victory' else t%2.4/2.4
 elif kind=='shield':
  clip='guard' if t<.96 or BLOCK<=t<5.44 else 'attack' if SHIELD_ATTACK+.4<=t<3.1 else 'idle'
  pr=t/.96 if t<.96 else min(1,(t-BLOCK)/.96) if clip=='guard' else min(1,pose_time(t-SHIELD_ATTACK)/1.2) if clip=='attack' else t%2.4/2.4
 else:
  clip='idle';pr=(t-HEAL_START)/1.2 if HEAL_START<=t<HEAL_START+1.2 else t%2.4/2.4
 if clip=='attack':
  approach=0 if pr<.12 else smooth((pr-.12)/.28) if pr<.4 else 1 if pr<=.66 else smooth((1-pr)/.34)
  tx=travel*approach
 root=sample(clip,pr)[1]
 return clip,pr,tx,root

def attachment_center(kind,t):
 _,_,tx,root=pose_state(kind,t)
 return (hx+tx+(root[0]+128)*hs,hy+(root[1]+144)*hs)

if '--requests-only' in sys.argv:
 requests=[]
 for kind,count in COUNTS.items():
  for i in range(count):
   t=i*.02;emit=[]
   if kind=='attack' and t>=HIT:emit=[{'kind':k,'age':t-HIT,'x':impact[0],'y':impact[1],'floor':H*.685} for k in ['strike','death']]
   if kind=='shield':
    if t>=SHIELD_HIT:emit.append({'kind':'strike','age':t-SHIELD_HIT,'x':impact[0],'y':impact[1],'floor':H*.685})
    if t>=BLOCK:
     c=attachment_center(kind,BLOCK)
     emit += [{'kind':'shieldContact','age':t-BLOCK,'x':c[0]+98.4*hs,'y':c[1],'floor':H*.69},{'kind':'shieldBreak','age':t-BLOCK,'x':c[0],'y':c[1],'floor':H*.69}]
   r={'kind':kind,'frame':i,'emitters':emit,'time':t,'shield':4 if kind=='shield' and BIRTH<=t<BLOCK else 0}
   if kind=='shield':
    if t<BIRTH:r['formation']=t
    if t>=BIRTH:r['birth']=t-BIRTH
    if t>=BLOCK:r['contact']=t-BLOCK;r['broken']=t-BLOCK
   if kind=='heal':r['recoveryAge']=t-HEAL_START
   requests.append(r)
 (OUT/'light-requests.json').write_text(json.dumps(requests,indent=2)+'\n');print('Wrote',len(requests),'production trajectory requests');sys.exit(0)

data=json.loads((OUT/'production-skill-trajectories.json').read_text());geo=data['geometry'];samples={(r['kind'],r['frame']):r for r in data['frames']}

def rotate_sprite(f,key,c,w,h,a,angle=0,add=True,flip=False):
 im=assets[key].resize((max(1,round(w)),max(1,round(h))),Image.Resampling.LANCZOS)
 if flip:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 if angle:im=im.rotate(-math.degrees(angle),resample=Image.Resampling.BICUBIC,expand=True)
 compose(f,im,c,im.size,a,add)

def colored_light(f,c,rx,ry,a,color=(255,175,45)):
 if a<=0:return
 from PIL import ImageFilter
 layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer);d.ellipse((c[0]-rx*.65,c[1]-ry*.65,c[0]+rx*.65,c[1]+ry*.65),fill=(*color,round(140*min(1,a))))
 layer=layer.filter(ImageFilter.GaussianBlur(max(2,ry*.4)));compose(f,layer,(W/2,H/2),(W,H),1,True)

def debris_ground(f,particles):
 pools=0
 for q in particles:
  col=(18,130,255) if q['cyan'] else (255,175,45)
  if q['id']%6==0:colored_light(f,(q['x'],q['y']),24,20,q['alpha']*.25,col)
  if q['groundAge'] is not None and q['groundAge']<.24 and pools<12:
   a=(1-q['groundAge']/.24)*q['alpha'];c=(q['groundX'],q['groundY']);colored_light(f,c,36,10,a*.65,col);optics(f,'WardHit' if q['cyan'] else 'GroundSpark',c,30,12,a*.9);pools+=1

def debris_front(f,particles):
 for q in particles:rotate_sprite(f,'CyanShard' if q['cyan'] else 'GoldEmber',(q['x'],q['y']),q['size'],q['size']*.67,q['alpha'],q['angle']+(math.pi/4 if q['cyan'] else -math.pi*.75))

def strike_ground(f,a,foot):
 burst=pulse(a,-.035,.035,.52) if a>=0 else 0
 light(f,impact,(195,190),burst*.9);light(f,(impact[0]+20,foot[1]),(235,55),burst)
 if 0<=a<.5:optics(f,'HeavySpray',(impact[0]+45,foot[1]-3),260*(1+a*2),22+a*70,burst*.55)

def strike_front(f,a):
 if not 0<=a<.7:return
 burst=pulse(a,-.035,.035,.52)
 optics(f,'Slash',impact,225,225,pulse(a,-.06,0,.25))
 rotate_sprite(f,'HeavyArc',impact,225+a*300,225+a*300,burst*.9,-.65+a*3.8)
 optics(f,'HeavyArc',(impact[0]+a*22,impact[1]),285+a*160,225+a*170,pulse(a,.10,.19,.65)*.38)
 optics(f,'Burst',impact,205+a*145,205+a*145,burst)
 optics(f,'HeavySpray',(impact[0]+95+a*75,impact[1]-15),250+a*180,160,burst*.9)
 for j in range(26):
  ang=j*2.399;dist=a*(150+j%5*38);optics(f,'Mote',(impact[0]+math.cos(ang)*dist,impact[1]+math.sin(ang)*dist),22 if j%4==0 else 10,7 if j%4==0 else 10,burst*.9)

def attached_shield(f,kind,t,shield):
 c=attachment_center(kind,t);spawn_age=t-BIRTH;contact_age=t-BLOCK
 alpha=samples[(kind,round(t/.02))]['shieldOpacity']
 size=geo['diameter']*hs
 rotate_sprite(f,'RoundBarrier',c,size,size,min(1,alpha),add=False)
 for i in range(6):
  angle=t*1.25+i*2.399;r=size*.41;s=(9 if i%2==0 else 6)*hs
  # Same cyan optical core as the attached UIImageView, approximate tint.
  im=assets['Mote'].copy();rgb=np.asarray(im).copy();rgb[:,:,:3]=np.array([80,245,255]);im=Image.fromarray(rgb)
  compose(f,im,(c[0]+math.cos(angle)*r,c[1]+math.sin(angle)*r),(s,s),min(1,alpha)*.65,False)
 return c

def attached_recovery(f,kind,t,row):
 age=t-HEAL_START;power=row['recoveryPower'];_,_,tx,root=pose_state(kind,t);foot=(hx+tx+(root[0]+128)*hs,hy+(root[1]+214)*hs)
 if not 0<=age<1.8:return
 rotate_sprite(f,'HealShaft',(foot[0],foot[1]-82.5*hs),110*hs,185*hs,power*.50,add=False)
 core=assets['Burst'].copy();rgb=np.asarray(core).copy();rgb[:,:,:3]=[209,255,217];core=Image.fromarray(rgb)
 compose(f,core,(foot[0],foot[1]-64*hs),(110*hs,110*hs),pulse(age,.34,.47,.70)*.70,False)
 expand=.65+.65*smooth(age/1.1)
 rotate_sprite(f,'HealWave',(foot[0],foot[1]+2*hs),164*hs*expand,28*hs,power*.8,add=False)
 for i in range(2):
  q=row['wisps'][i];c=(foot[0]+q['x']*hs,foot[1]+q['y']*hs)
  rotate_sprite(f,'HealWisp',c,85*hs*q['scaleX'],180*hs,q['alpha'],q['rotation'],False)
 for q in row['recovery']:rotate_sprite(f,'HealStar',(foot[0]+q['x']*hs,foot[1]+q['y']*hs),q['size']*hs,q['size']*hs,q['alpha'],add=False)

# Clear, compact review captions; actual product cards retain their existing text.
def review_ui(scene,t,kind,hero_hp,enemy_hp,shield,stage):
 f=Image.new('RGBA',(W,H+UI),(15,24,22,255));f.alpha_composite(scene);d=ImageDraw.Draw(f)
 d.rectangle((0,0,W,38),fill=(12,23,22,235));d.text((16,5),'build44 · 连续技能 / 状态条',font=font,fill='#f5e8c7');d.text((W-190,8),f'离线 {t:.2f}s',font=small,fill='#bbc5bc')
 d.text((18,H-35),stage,font=small,fill='#ffe9b8')
 for x,name,v,m,col,width in [(18,'生命',hero_hp,12,'#79db95',210),(270,'护盾',shield,8,'#5ce4ff',210),(522,'行动',2,3,'#e8ca79',162)]:
  d.text((x,H+7),f'{name} {v}/{m}',font=font,fill='#fff1cd')
  d.rectangle((x,H+34,x+width,H+43),fill='#080f0b',outline='#8c8054')
  if v:d.rectangle((x+1,H+35,x+1+(width-2)*v/m,H+42),fill=col)
 for i,(title,detail) in enumerate([('强击 · 1 AP','造成5点伤害'),('喘息 · 1 AP','恢复4点生命'),('简易防护 · 1 AP','获得4点护盾')]):
  x=18+i*248
  d.rounded_rectangle((x,H+62,x+234,H+148),8,fill='#29372b',outline='#e4d1a0',width=1)
  d.text((x+12,H+71),title,font=font,fill='#ffe5b2');d.text((x+12,H+111),detail,font=small,fill='#c7d6bc')
 # Actor HP presentation is outside the camera transform, as in production.
 for x,y,name,v,m in [(W*.29-68,H*.69-H*.17-49,'P1',hero_hp,12),(W*.65-68,H*.685-H*.33-49,'鹿灵',enemy_hp,18)]:
  d.rounded_rectangle((x,y,x+136,y+43),5,fill='#13281e')
  d.text((x+7,y+1),f'{name} {v}/{m}',font=small,fill='#fff1cd')
  d.rectangle((x+7,y+29,x+129,y+36),fill='#07110b')
  if v:d.rectangle((x+7,y+29,x+7+122*v/m,y+36),fill='#79db95')
 if shield:
  d.rounded_rectangle((W-58,H+6,W-14,H+50),5,fill='#233e39',outline='#5ce4ff',width=2)
  d.text((W-49,H+13),'盾',font=font,fill='#7beaff')
  if kind=='shield' and 1.05<=t<1.4:
   d.rounded_rectangle((W-316,H-96,W-14,H-6),7,fill='#162b20',outline='#ecd492')
   d.text((W-305,H-88),f'防护 · 剩余 {shield} 点',font=font,fill='#fff1cd')
   d.text((W-305,H-49),'优先抵挡伤害，耗尽时破碎',font=small,fill='#b9e7e5')
 return f.convert('RGB')

reports={}
for kind,count in COUNTS.items():
 print('Rendering',kind,flush=True)
 frames=[];events=[]
 for i in range(count):
  t=i*.02;row=samples[(kind,i)];particles=row['particles'];clip,pr,tx,root=pose_state(kind,t);hero=render(clip,pr);fo=(W*.29,H*.69);ef=(W*.65,H*.685)
  dead=kind=='attack' and t>=HIT
  shield=(4 if BIRTH<=t<BLOCK else 0) if kind=='shield' else 0
  hit_at=HIT if kind=='attack' else SHIELD_HIT if kind=='shield' else 100
  age=t-hit_at;focus=kind=='attack' and 1.6<=t<2.6
  cast_start=2.6 if kind=='attack' else SHIELD_ATTACK if kind=='shield' else 100
  elapsed=t-cast_start
  dim=.45*smooth((t-1.6)/.28) if focus else (.45+(.64-.45)*smooth(elapsed/.44))*(1-smooth((elapsed-2)/1.36)) if elapsed>=0 else 0
  if kind=='heal':dim=.30*row['recoveryPower']
  if 0<=age<.225:dim=max(dim,.82*pulse(age,0,.035,.225))
  f=ImageEnhance.Brightness(plate).enhance(1-dim)
  if age>=0:strike_ground(f,age,ef)
  debris_ground(f,particles)
  if dead and age<1.4:
   colored_light(f,(impact[0]+age*95,ef[1]),180,42,.38*(1-smooth(age/1.4)))
   colored_light(f,(impact[0]+age*90,impact[1]),115,95,.18*(1-smooth(age/1.4)))
  if kind=='heal':
   power=row['recoveryPower'];colored_light(f,fo,135,42,power*.85,(38,255,133));colored_light(f,(fo[0],fo[1]-65),75,110,power*.28,(89,255,153))
  enemy_tx=0;monster=bodies[min(47,int(age*60))] if dead else enemy
  recoil=W*.025*pulse(age,-.02,.14,.52) if age>=0 else 0
  if kind=='shield' and 4<=t<5.44:
   ep=min(1,(t-4)/.96);monster=enemy_attack[min(7,int(ep*8))]
   enemy_tx=-max(0,ex+42*es-(hx+geo['contactX']*hs))*pulse(ep,.08,.48,.98)
  shadow(f,hero,hx+tx,hy,hs);shadow(f,monster,ex+enemy_tx+recoil,ey,es)
  f.alpha_composite(hero.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(hx+tx),round(hy)))
  center=attached_shield(f,kind,t,shield) if kind=='shield' else None
  if kind=='heal':attached_recovery(f,kind,t,row)
  f.alpha_composite(ImageEnhance.Brightness(monster).enhance(1-dim*.55).resize((round(384*es),round(256*es)),Image.Resampling.NEAREST),(round(ex+enemy_tx+recoil),round(ey)))
  if dead:f.alpha_composite(winds[min(115,int(age*60))].resize((round(448*es),round(320*es)),Image.Resampling.LANCZOS),(round(ex),round(ey-32*es)))
  f.alpha_composite(ImageEnhance.Brightness(foreground).enhance(1-dim))
  ring=.63*smooth((t-1.6)/.28) if focus else .65*(1-smooth((elapsed-.24)/.16)) if 0<=elapsed<.4 else 0
  optics(f,'Ring',fo,110,46,ring)
  strike_front(f,age);debris_front(f,particles)
  if kind=='shield' and 0<=t-BLOCK<.4:
   c=attachment_center(kind,t);a=t-BLOCK;size=80+a*150;optics(f,'WardHit',(c[0]+98.4*hs+size*.33,c[1]),size,size,pulse(a,-.02,.025,.38)*.9)
  if 0<=age<.5:f=camera(f,age,'attack')
  elif kind=='shield' and 0<=t-BLOCK<.22:f=camera(f,t-BLOCK,'shield')
  if 0<=age<.7:ImageDraw.Draw(f).text((impact[0]+20,impact[1]-40-age*30),'3' if dead else '5',font=large,fill='#fff3cd',stroke_width=2,stroke_fill='#463016')
  if kind=='heal' and HEAL_HIT<=t<HEAL_HIT+.7:ImageDraw.Draw(f).text((fo[0]+20,fo[1]-40-(t-HEAL_HIT)*30),'+4',font=large,fill='#c8ffbd',stroke_width=2,stroke_fill='#153b27')
  stage='扫动主弧 → 回声 → 余烬落地' if kind=='attack' else '圆盾随完整人物冲刺 / 返回，接触才破裂' if kind=='shield' else '绿金汇聚 → 盘旋上升 → 恢复 → 散光'
  hero_hp=8 if kind=='heal' and t<HEAL_HIT else 12;enemy_hp=0 if dead else 13 if kind=='shield' and t>=SHIELD_HIT else 3 if kind=='attack' else 18
  frames.append(review_ui(f,t,kind,hero_hp,enemy_hp,shield,stage))
  events.append({'frame':i,'timeMs':i*20,'heroHP':hero_hp,'enemyHP':enemy_hp,'shield':shield,'deathActive':dead,'damageVisible':0<=age<.7,'ringAlpha':ring,'actorRoot':[hx+tx+root[0]*hs,hy+root[1]*hs],'shieldCenter':center,'recoveryPower':row['recoveryPower']})
 palette_source=Image.new('RGB',(W*3,(H+UI)*3))
 for j,k in enumerate([0,count//5,count//3,count//2,min(count-1,int((HIT if kind=='attack' else BLOCK if kind=='shield' else HEAL_HIT)/.02)),count*2//3,count*3//4,count*4//5,count-1]):palette_source.paste(frames[k],(j%3*W,j//3*(H+UI)))
 pal=palette_source.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 name={'attack':'strike-death-normal.gif','shield':'shield-follow-normal.gif','heal':'recovery-normal.gif'}[kind]
 def encode(scale):
  size=(round(W*scale),round((H+UI)*scale));encoded=[f.resize(size,Image.Resampling.LANCZOS).quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
  encoded[0].save(OUT/name,save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=1,optimize=True)
 encode(.9);scale=.9
 # Lossless transparent-pixel delta optimization, preserving every 20ms frame.
 import subprocess
 import os,shutil
 binary=os.environ.get('GIFSICLE') or shutil.which('gifsicle') or '/workspace/gifsicle-1.96/src/gifsicle'
 if Path(binary).exists():
  subprocess.run([binary,'-O3',str(OUT/name),'-o',str(OUT/(name+'.tmp'))],check=True)
  (OUT/(name+'.tmp')).replace(OUT/name)
 while (OUT/name).stat().st_size>19500000:
  scale=round(scale-.1,2);assert scale>=.4
  encode(scale)
  if Path(binary).exists():
   subprocess.run([binary,'-O3',str(OUT/name),'-o',str(OUT/(name+'.tmp'))],check=True)
   (OUT/(name+'.tmp')).replace(OUT/name)
 gif=Image.open(OUT/name);assert gif.n_frames==count
 for page in range(math.ceil(count/40)):
  sheet=Image.new('RGB',(1520,2744),'#111a15')
  for j,k in enumerate(range(page*40,min(count,(page+1)*40))):
   gif.seek(k);assert gif.info['duration']==20;sheet.paste(gif.convert('RGB').resize((304,343)),(j%5*304,j//5*343))
  sheet.save(OUT/f'{kind}-decoded-{page+1:02}.jpg',quality=88)
 frames[0].save(OUT/f'{kind}-standing.png')
 print('Finished',kind,flush=True)
 keys=[(HIT+.04,'impact'),(HIT+.30,'sweep-tail'),(HIT+.82,'ground')] if kind=='attack' else [(1.1,'full-cover'),(2.35,'dash'),(3.0,'return'),(BLOCK+.08,'block'),(BLOCK+.3,'break')] if kind=='shield' else [(HEAL_START+.2,'gather'),(HEAL_HIT+.08,'recover'),(HEAL_START+.9,'spiral'),(HEAL_START+1.35,'tail')]
 for sec,label in keys:frames[min(count-1,round(sec/.02))].save(OUT/f'{kind}-{label}.png')
 (OUT/f'{kind}-trace.json').write_text(json.dumps(events,indent=2)+'\n');reports[kind]={'frames':count,'frameDurationMs':20,'durationMs':count*20,'file':name,'bytes':(OUT/name).stat().st_size,'exportScale':scale,'decodedDimensions':gif.size}
(OUT/'review-render.json').write_text(json.dumps({'scope':'shared assets, actor poses and production Swift fields; offline light approximation, no UIKit/device capture','animations':reports,'hitTime':HIT,'shieldHitTime':SHIELD_HIT,'shieldBreakTime':BLOCK,'healTime':HEAL_HIT,'shieldGeometry':geo,'artApproval':None},indent=2)+'\n');print(json.dumps(reports))
