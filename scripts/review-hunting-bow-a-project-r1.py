#!/usr/bin/env python3
"""Pose A bow review using production Swift sleeve meshes and receipts.
Offline art composition; never UIKit/device/performance capture.
"""
from pathlib import Path
import sys,json,math,subprocess,functools
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/hunting-bow-a-project-r1'
old=R/'scripts/review-head-dice-demo.py';namespace={'__file__':str(old)}
source=old.read_text().replace('dice-party-demo-v1','hunting-bow-a-project-r1').replace('build47','pose A')
start=source.index(' for i,(die,pose) in enumerate(zip(row[\'dice\'],row[\'dicePose\'])):')
end=source.index('\n return f',start)
source=source[:start]+''' for i,(die,pose) in enumerate(zip(row['dice'],row['poly'])):
  im=die_image(die,pose);im.putalpha(im.getchannel('A').point(lambda a:round(a*pose['alpha'])))
  spacing=min(82,200/max(1,len(row['dice'])))
  cx=row['diceAnchor']['x']+(i-(len(row['dice'])-1)/2)*spacing
  cy=row['diceAnchor']['y']+43+oy+pose['offsetY']
  f.alpha_composite(im,(round(cx-128),round(cy-120)))
'''+source[end:]
source=source.replace("1.048 if kind=='attack'", "0.72 if kind=='ambush' else 1.048 if kind=='attack'")
source=source.replace("    if u['shield']>old['shield']", "    if row['action']=='ambush' and u['hp']>old['hp']:heals[uid]=time\n    if u['shield']>old['shield']")
# Whole living units retain original art and posture. Far strands are under the body.
source=source.replace("   im=render(u['clip'],u['progress']);", "   draw_ribbons(f,u,row,front=False)\n   im=render(u['clip'],u['progress']);")
source=source.replace(" dd=ImageDraw.Draw(f)", " draw_damage(f,row)\n dd=ImageDraw.Draw(f)")
source=source.replace(" f.alpha_composite(fg)", " f.alpha_composite(fg)\n draw_recovery_lights(f,row)\n if row['playing'] and row['action']=='ambush':draw_ambush(f,row)")
source=source.replace(" for uid in sorted(units", " draw_afterimages(f,row)\n for uid in sorted(units")
source=source.replace("[('普通攻击','1D6＋当前增伤'),('援护','恢复6 / 盾4'),('振奋','友方增伤2 / 1轮')]", "[('普通攻击','1D6＋当前增伤'),('突袭','2D8＋2 / 自身恢复3'),('援护','恢复6 / 盾4'),('振奋','友方增伤2 / 1轮')]")
source=source.replace("title+' · 1 AP'", "title+(' · 2 AP' if title=='突袭' else ' · 1 AP')")
source=source.replace("f'小队支援 · {row[\"current\"].upper()} 行动'", "(f'小队支援 · {row[\"current\"].upper()} 行动' if row['current'] else '小队胜利')")
source=source.replace("cur=ids.index(row['current'])", "cur=ids.index(row['current']) if row['current'] in ids else 0")
source=source.replace("u['id']==row['current']", "u['id']==(row['current'] or 'p1')")
# Lifecycle and shared AP panel match the current UIKit presentation.
source=source.replace(" for uid,u in units.items():\n  x,y=feet[uid]", " for uid,u in units.items():\n  if not u['vitalsVisible']:continue\n  x,y=feet[uid]")
a=source.index("  x=86+i*394;text(d,(x,862)")
b=source.index(" if u['buff']:",a)
source=source[:a]+'''  x=86+i*394;text(d,(x,862),title if title=='行动' else f'{title} {v}/{m}',18)
  if title=='行动':
   for j in range(m):
    cx=x+9+j*27;cy=900;h=9
    d.polygon([(cx,cy-h),(cx+h,cy),(cx,cy+h),(cx-h,cy)],fill=c if j<v else '#303c28',outline=c if j<v else '#8a8050')
  else:
   d.rectangle((x,891,x+370,900),fill='#07110b')
   if v:d.rectangle((x+1,892,x+1+368*min(1,v/m),899),fill=c)
'''+source[b:]
source=source.replace("im=render(u['clip'],u['progress']);", "im=gear_render(u['clip'],u['progress'],u.get('weaponID'));")
source=source.replace("if row['playing'] and row['action']=='attack':", "if row['playing'] and row['action'] in ['attack','heavyStrike']:")
source=source.replace("if not row['enemy']:compose", "if not row['enemy'] and not row.get('ranged'):compose")
source=source.replace(" f.alpha_composite(fg)", " f.alpha_composite(fg)\n draw_projectile(f,row)")
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
  size=round(min(30,h*.8))
  if die.get('value') is not None:text(('+' if die['color']=='yellow' and die['value']>0 else '')+str(die['value']),-size*.67,size)

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
 return im
namespace['die_image']=die_image
scene,old_ui=namespace['scene'],namespace['ui'];font=lambda n:ImageFont.truetype(fontpath,n)
poly=json.loads((D/'poly-frames.json').read_text())
def ui(row,world):
 f=old_ui(row,world);
 if row['scenario'].startswith('bow'):
  d=ImageDraw.Draw(f);d.rectangle((96,951,349,1005),fill='#293e2d');d.text((96,965),'1D8＋当前增伤',font=font(20),fill='#c6d6b7')
 ImageDraw.Draw(f).text((1300,1035),f'{row["time"]:.2f}s',font=font(16),fill='#c6d6b7');return f
def gallery(row):
 f=Image.new('RGBA',(1200,850),'#102319');d=ImageDraw.Draw(f)
 d.text((28,16),'build53 · 多面骰翻面与正向停骰' if row['group']=='types' else 'build53 · 多骰与固定加值分开表示',font=font(28),fill='#fff0c8')
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
 for t,label in [(0,'standing'),(.5,'rolling'),(2.06,'impact'),(2.3,'landed'),(1.8,'held'),(3.2,'retired')]:frames[min(len(frames)-1,round(t/.02))].save(D/(name+'-'+label+'.png'))
 info={'file':name+'-normal.gif','frames':len(frames),'frameDurationMs':20,'durationMs':len(frames)*20,'dimensions':size,'bytes':(D/(name+'-normal.gif')).stat().st_size};print(name,info,flush=True);return info
# Replace the prior attachment's long wisp sprites, retaining the round shield.
helpers=namespace['env'];helpers['REQUESTS']=namespace['reqs']
attachment_source=(R/'scripts/review-party-support-demo.py').read_text()
attachment_source=attachment_source[attachment_source.index('def attachments('):attachment_source.index('\nREQUESTS=')]
attachment_source=attachment_source.replace('if recovery_age is not None and 0<=recovery_age<1.8:', 'if False:')
exec(compile(attachment_source,'frozen-shield-only','exec'),helpers)
shield_only=helpers['attachments']
def add_layer(f,layer):
 bbox=layer.getchannel('A').getbbox()
 if not bbox:return
 np=helpers['np'];src=np.asarray(layer.crop(bbox)).astype(float)/255;dst=np.asarray(f.crop(bbox)).astype(float)/255
 alpha=np.maximum(src[:,:,3:4],dst[:,:,3:4]);premul=np.minimum(1,src[:,:,:3]*src[:,:,3:4]+dst[:,:,:3]*dst[:,:,3:4])
 rgb=np.divide(premul,alpha,out=np.zeros_like(premul),where=alpha>0)
 f.paste(Image.fromarray(np.round(np.concatenate((np.minimum(1,rgb),alpha),axis=2)*255).astype('uint8')),bbox[:2])
def actor_foot(u,row,overscan=True):
 x,y=helpers['hero_at'](u,{'action':{'actor':row['actor'],'travel':row['travel']} if row['playing'] else {}})
 root=helpers['sample'](u['clip'],u['progress'])[1]
 return x+(root[0]+128)*helpers['hs'],y+(root[1]+214)*helpers['hs']+(namespace['oy'] if overscan else 0)
def draw_ribbons(f,u,row,front=True,overscan=True):
 q=namespace['attached'][(row['scenario']+'-'+u['id'],row['frame'])];foot=actor_foot(u,row,overscan);hs=helpers['hs']
 layer=Image.new('RGBA',f.size);d=ImageDraw.Draw(layer)
 for strand in q['ribbons']:
  for start in range(0,max(0,len(strand)-1),3):
   end=min(len(strand)-1,start+3);segments=[];alphas=[]
   for j in range(start,end):
    a,b=strand[j],strand[j+1]
    if ((a['depth']+b['depth'])/2>=0)!=front:continue
    segments.append(((foot[0]+a['x']*hs,foot[1]+a['y']*hs),(foot[0]+b['x']*hs,foot[1]+b['y']*hs)));alphas.append((a['alpha']+b['alpha'])/2)
   if not segments:continue
   alpha=sum(alphas)/len(alphas)*(1 if front else .58)
   for width,color,weight in [(9,(20,242,102),.20),(3.2,(102,255,163),.9),(1.1,(219,255,207),.85)]:
    for seg in segments:d.line(seg,fill=(*color,round(alpha*weight*255)),width=max(1,round(width*hs)))
 add_layer(f,layer)
def attachments(f,u,q,row):
 shield_only(f,u,q,row)
 # Called in the unshifted 600-high attachment canvas, just like the runtime child.
 short={'scenario':row['scenario'],'frame':row['frame'],'actor':row['action'].get('actor',''),'travel':row['action'].get('travel',{}),'playing':bool(row['action'])}
 draw_ribbons(f,u,short,True,False)
 foot=actor_foot(u,short,False);hs=helpers['hs'];power=q['recoveryPower']

 namespace['compose'](f,helpers['assets']['HealShaft'],(foot[0],foot[1]-82.5*hs),(110*hs,185*hs),power*.1)
 for star in q['recovery']:namespace['compose'](f,helpers['assets']['HealStar'],(foot[0]+star['x']*hs,foot[1]+star['y']*hs),(star['size']*hs,star['size']*hs),star['alpha'])
helpers['attachments']=attachments
bow_rows=json.loads((D/'bow-poses.json').read_text())
bow_samples={(r['clip'],round(r['progress']*600)):r['sample'] for r in bow_rows}
part_map={'MeadowBattleHeroArmNearUpperBody':'nearUpper','MeadowBattleHeroArmNearUpperWardrobe':'nearUpper','MeadowBattleHeroArmNearForearmBody':'nearFore','MeadowBattleHeroArmNearForearmWardrobe':'nearFore','MeadowBattleHeroNearHand':'nearHand','MeadowBattleHeroWeapon':'bow','BowFarUpperBody':'farUpper','BowFarUpperWardrobe':'farUpper','BowFarForeBody':'farFore','BowFarForeWardrobe':'farFore','BowFarHand':'farHand'}
far_sources={'BowFarUpperBody':'MeadowBattleHeroArmNearUpperBody','BowFarUpperWardrobe':'MeadowBattleHeroArmNearUpperWardrobe','BowFarForeBody':'MeadowBattleHeroArmNearForearmBody','BowFarForeWardrobe':'MeadowBattleHeroArmNearForearmWardrobe','BowFarHand':'MeadowBattleHeroNearHand'}
def interpolate(a,b,t):
 if isinstance(a,str):return a
 if isinstance(a,list):return [interpolate(x,y,t) for x,y in zip(a,b)]
 if isinstance(a,dict):return {k:interpolate(v,b[k],t) for k,v in a.items()}
 if isinstance(a,bool):return a if t<.5 else b
 return a+(b-a)*t
@functools.lru_cache(maxsize=2048)
def gear_render(clip,progress,weapon_id):
 render=namespace['render']
 if weapon_id=='huntingBow':
  base=render.__globals__;transforms,root,_,_,_=namespace['sample']('idle',0) if clip=='attack' else namespace['sample'](clip,progress)
  n=max(0,min(600,progress*600));lo=int(n);hi=min(600,lo+1);rig=interpolate(bow_samples[(clip,lo)],bow_samples[(clip,hi)],n-lo)
  names=list(base['config']['layers'])
  skip=['MeadowBattleHeroWeapon','MeadowBattleHeroFarHand','MeadowBattleHeroNearHand','MeadowBattleHeroArmNearUpperBody','MeadowBattleHeroArmNearForearmBody','MeadowBattleHeroArmNearUpperWardrobe','MeadowBattleHeroArmNearForearmWardrobe','MeadowBattleHeroJointUnderlay','MeadowBattleHeroWardrobeCore']
  torso=[n for n in names if n not in skip]
  insert=torso.index('MeadowBattleHeroHair');order=torso[:insert]+['torso','farArm','nearArm','head']+torso[insert:]+['MeadowBattleHeroWeapon','geometry','farHand','nearHand']
  out=Image.new('RGBA',(256,256))
  def geometry():
   d=ImageDraw.Draw(out);pts=[(round(rig[k]['x']+root[0]),round(rig[k]['y']+root[1])) for k in ['upperTip','stringHand','lowerTip']];d.line(pts,fill='#e1c78c',width=1)
   if rig['arrowVisible']:
    a,b=rig['arrowTail'],rig['arrowTip'];ax,ay=a['x']+root[0],a['y']+root[1];bx,by=b['x']+root[0],b['y']+root[1];d.line((ax,ay,bx,by),fill=(212,171,102,round(rig['arrowAlpha']*255)),width=1);d.polygon([(bx+2,by),(bx-3,by-2),(bx-3,by+2)],fill=(216,224,217,round(rig['arrowAlpha']*255)))
  for name in order:
   if name=='geometry':geometry();continue
   if name in ['nearHand','farHand']:
    pose=rig['parts'][name];x=round(pose['pivot']['x']+pose['offset']['x']);y=round(pose['pivot']['y']+pose['offset']['y'])
    assetname='MeadowBattleBowDrawingHand' if name=='nearHand' else 'MeadowBattleBowGripHand'
    layer=Image.new('RGBA',(256,256));layer.alpha_composite(namespace['asset'](assetname),(x-(14 if name=='nearHand' else 8),y-6))
    layer=layer.rotate(-math.degrees(pose['rotation']),resample=Image.Resampling.NEAREST,center=(x,y))
    out.alpha_composite(layer,(round(root[0]),round(root[1])));continue
   if name in ['torso','farArm','farHand','nearArm','nearHand']:
    d=ImageDraw.Draw(out)
    for surf in rig['surfaces']:
     if surf['group']!=name:continue
     c=round(surf['color']);color=((c>>16)&255,(c>>8)&255,c&255,255)
     d.polygon([(round(q['x']+root[0]),round(q['y']+root[1])) for q in surf['points']],fill=color)
    if name=='torso':
     # Retain the source collar and belt; exclude the old arm's stray fragments.
     im=namespace['asset']('MeadowBattleBowWardrobeCore').copy();mask=Image.new('L',(256,256));dd=ImageDraw.Draw(mask)
     for rect in [(104,125,147,142),(138,139,146,151),(104,158,145,175)]:dd.rectangle(rect,fill=255)
     import PIL.ImageChops
     im.putalpha(PIL.ImageChops.multiply(im.getchannel('A'),mask));pivot,offset,angle=transforms['MeadowBattleHeroWardrobeCore'];im=im.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=pivot);out.alpha_composite(im,(round(offset[0]+root[0]),round(offset[1]+root[1])))
    continue
   if name=='head':
    im=namespace['asset']('MeadowBattleBowBodyCore').copy();mask=Image.new('L',(256,256));ImageDraw.Draw(mask).rectangle((100,75,156,136),fill=255)
    import PIL.ImageChops
    im.putalpha(PIL.ImageChops.multiply(im.getchannel('A'),mask));pivot,offset,angle=transforms['MeadowBattleHeroBodyCore'];im=im.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=pivot);out.alpha_composite(im,(round(offset[0]+root[0]),round(offset[1]+root[1])));continue
   assetname='MeadowBattleHuntingBow'  if name=='MeadowBattleHeroWeapon' else 'MeadowBattleBowBodyCore' if name=='MeadowBattleHeroBodyCore' else 'MeadowBattleBowWardrobeCore' if name=='MeadowBattleHeroWardrobeCore' else 'MeadowBattleBowLegFarThighWardrobe' if name=='MeadowBattleHeroLegFarThighWardrobe' else name
   im=namespace['asset'](assetname).copy()
   if name=='MeadowBattleHeroBodyCore':
    mask=Image.new('L',(256,256));dd=ImageDraw.Draw(mask);dd.rectangle((100,174,152,190),fill=255)
    import PIL.ImageChops
    im.putalpha(PIL.ImageChops.multiply(im.getchannel('A'),mask))
   if name=='MeadowBattleHeroWeapon':
    q=rig['parts']['bow'];pivot=(q['pivot']['x'],q['pivot']['y']);offset=(q['offset']['x'],q['offset']['y']);angle=q['rotation']
   else:pivot,offset,angle=transforms.get(name,((0,0),(0,0),0))
   im=im.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=pivot)
   out.alpha_composite(im,(round(offset[0]+root[0]),round(offset[1]+root[1])))

  return out
 if weapon_id is not None:return render(clip,progress)
 layers=render.__globals__['LAYERS'];saved=layers['MeadowBattleHeroWeapon']
 try:
  layers['MeadowBattleHeroWeapon']=Image.new('RGBA',(256,256));return render(clip,progress)
 finally:layers['MeadowBattleHeroWeapon']=saved

def draw_projectile(f,row):
 q=row.get('projectile')
 if not q:return
 d=ImageDraw.Draw(f);a,b=q['tail'],q['tip'];points=[(a['x'],a['y']+namespace['oy']),(b['x'],b['y']+namespace['oy'])];d.line(points,fill='#d8a94d',width=5);d.line(points,fill='#fff0c8',width=2)
def draw_damage(f,row):
 d=ImageDraw.Draw(f)
 for m in row['damageLabels']:
  age=row['time']-m['at'];alpha=1-namespace['env']['smooth']((age-.65)/.35)
  ft=font(24);box=d.textbbox((0,0),m['text'],font=ft);w,h=box[2]-box[0],box[3]-box[1]
  d.text((m['x']-w/2-box[0],m['y']+namespace['oy']-h/2-box[1]-age*26),m['text'],font=ft,fill=(255,240,210,round(alpha*255)),stroke_width=2,stroke_fill=(15,20,12,round(alpha*255)))
def draw_recovery_lights(f,row):
 for u in row['units']:
  if not u['id'].startswith('p'):continue
  q=namespace['attached'][(row['scenario']+'-'+u['id'],row['frame'])];foot=actor_foot(u,row)
  namespace['glow'](f,foot,105,27,q['recoveryPower']*.65,(40,240,110))
def draw_afterimages(f,row):
 if not row['afterimages']:return
 x,y=namespace['feet'][row['actor']];hs=namespace['hs']
 for trail in row['afterimages']:
  im=namespace['render']('attack',trail['progress']);root=namespace['sample']('attack',trail['progress'])[1]
  im=im.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST);im.putalpha(im.getchannel('A').point(lambda a:round(a*trail['alpha'])))
  f.alpha_composite(im,(round(x+trail['offset']['x']+(root[0]-123)*hs),round(y+trail['offset']['y']+(root[1]-214)*hs+namespace['oy'])))
def draw_ambush(f,row):
 foot=namespace['feet'][row['target']];at=(foot[0]-80,foot[1]-72+namespace['oy']);power=helpers['pulse'](row['age'],.72,.755,1.14)
 namespace['glow'](f,at,128,115,power*.52,(255,220,30));namespace['glow'](f,(foot[0],foot[1]+namespace['oy']),170,27,power*.7,(40,240,110))
 namespace['compose'](f,namespace['asset']('BattleVFXBurst'),at,(130,130),power*.72,True)
 layer=Image.new('RGBA',f.size);d=ImageDraw.Draw(layer)
 for slash in row['ambushSlashes']:
  pts=[(p['x'],p['y']+namespace['oy']) for p in slash['points']]
  d.line(pts,fill=(40,240,110,round(slash['alpha']*.35*255)),width=12);d.line(pts,fill=(255,239,200,round(slash['alpha']*255)),width=3)
 add_layer(f,layer)
namespace.update(draw_projectile=draw_projectile,gear_render=gear_render,draw_damage=draw_damage,draw_recovery_lights=draw_recovery_lights,draw_ribbons=draw_ribbons,draw_afterimages=draw_afterimages,draw_ambush=draw_ambush)
if '--stills' in sys.argv:
 for kind in ['bow','bow-heavy','bow-lethal']:
  for t,label in [(0,'standing'),(.5,'selected'),(1.5,'dash'),(1.78 if kind=='ambush' else 2.1,'impact'),(2.4,'recovery'),(2.9,'settled')]:
   row=min((r for r in rows if r['scenario']==kind),key=lambda r:abs(r['time']-t));ui(row,scene(row)).save(D/f'{kind}-{label}.png')
 sys.exit(0)
reports=json.loads((D/'review-render.json').read_text())['animations'] if (D/'review-render.json').exists() else {}
for group in ['bow','bow-heavy','bow-lethal']:
 if '--only' in sys.argv and group not in sys.argv[sys.argv.index('--only')+1:]:continue
 rs=[r for r in rows if r['scenario']==group];reports[group]=save(group,[ui(r,scene(r)) for r in rs])
(D/'review-render.json').write_text(json.dumps({'scope':'production Swift ambush/helix/dice and core receipts; offline composition, not UIKit/device','animations':reports,'newArtApproval':None},indent=2)+'\n')
