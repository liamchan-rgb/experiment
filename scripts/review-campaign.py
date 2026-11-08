#!/usr/bin/env python3
"""Actual Swift campaign/pose/light data with existing PNGs. Offline composition;
lighting/UI approximate. Does not run UIKit, the app or a simulator."""
from pathlib import Path
import json,runpy,sys,math,os,shutil,subprocess,tempfile,functools
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageSequence
ROOT=Path(__file__).resolve().parents[1];OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'Art/Review/Map/campaign-v1';DATA=OUT/'data'
base=ROOT/'scripts/review-party-support-demo.py'
prefix=base.read_text().split('reports={};clips={}')[0]
prefix='\n'.join('rows=[];legacy=[];attached={}' if line.startswith('rows=json.loads') else 'REQUESTS={}' if line.startswith('REQUESTS=') else line for line in prefix.splitlines())
saved=sys.argv;sys.argv=['offline-review'];e={'__file__':str(base)};exec(compile(prefix,str(base),'exec'),e);sys.argv=saved
render,shadow,compose,glow,asset=[e[k] for k in ['render','shadow','compose','glow','asset']]
feet=e['feet'];hs=e['hs'];es=e['es'];font=e['font'];small=e['small'];large=e['large'];plate=e['plate'];foreground=e['foreground']

# Reuse the existing reviewed perspective faces and fixed-value plates.
projection=(ROOT/'scripts/review-upright-dice-hud-demo.py').read_text()
projection=projection[projection.index('@functools.lru_cache'):projection.index("namespace['die_image']=die_image")]
dice_env={'Image':Image,'ImageDraw':ImageDraw,'ImageFont':ImageFont,'functools':functools,'fontpath':e['fontfile'],'palette_colors':{'red':'#c72924','yellow':'#d9a129','green':'#219451','blue':'#1f70cc'}}
exec(compile(projection,'reviewed-die-projection','exec'),dice_env)
die_image=dice_env['die_image']

def gif(frames,name):
 sample=Image.new('RGB',(frames[0].width*3,frames[0].height*3))
 for j in range(9):sample.paste(frames[min(len(frames)-1,j*(len(frames)-1)//8)],(j%3*frames[0].width,j//3*frames[0].height))
 palette=sample.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
 encoded[0].save(OUT/name,save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=1,optimize=True)
 with Image.open(OUT/name) as im:assert im.n_frames==len(frames)
 if not Path(name).is_absolute():
  for i in [0,len(frames)//4,len(frames)//2,len(frames)*3//4,len(frames)-1]:frames[i].save(OUT/f'{name[:-4]}-{i:04d}.png')
 print(name,len(frames),(OUT/name).stat().st_size,flush=True)

def statusbar(frame,units,y):
 d=ImageDraw.Draw(frame)
 for i,u in enumerate(units):
  x=12+i*236
  if x+224>frame.width:break
  d.rounded_rectangle((x,y,x+224,y+74),5,fill='#1b3025',outline='#93804d')
  d.text((x+8,y+4),u.get('name',f"P{u.get('index',0)+1}"),font=small,fill='#f5e8bc')
  hp,mx=u['hp'],u['maxHP'];d.rectangle((x+8,y+36,x+132,y+47),fill='#06150a',outline='#6f784d')
  if hp:d.rectangle((x+9,y+37,x+9+122*hp/mx,y+46),fill='#50c976')
  d.text((x+140,y+33),f'{hp}/{mx}',font=small,fill='#e5edca')
  for j in range(max(3,u['ap'])):
   cx=x+14+j*19;cy=y+61;d.polygon([(cx,cy-6),(cx+6,cy),(cx,cy+6),(cx-6,cy)],fill='#f3cf66' if j<u['ap'] else '#3a4430',outline='#a99555')

m=runpy.run_path(str(ROOT/'scripts/review-random-map-v3.py'),run_name='review');m['prepare'].__globals__['OUT']=OUT
prepared=m['prepare'](10,31827);walk=json.loads((DATA/'walking.json').read_text());frames=[]
first,last=walk[0]['heroes'][0],walk[-1]['heroes'][0];left=max(0,min(320,round((first['x']+last['x'])/2-480)));top=max(0,min(round(prepared[0]['coordinateHeight'])-500,round((first['y']+last['y'])/2-295)))
for row in walk:
 world=m['draw_map'](prepared,row['heroes']).crop((left,top,left+960,top+500))
 f=Image.new('RGB',(960,622),'#15291e');f.paste(world,(0,40));d=ImageDraw.Draw(f)
 d.text((14,7),'正式行程 · 三倍移动 · 门前停步与遇敌',font=font,fill='#f8e3aa');d.text((870,10),f"{row['time']:.2f}s",font=small,fill='#d7d6b6')
 statusbar(f,row['heroes'],543)
 d.text((505,550),f"已探索 {len(row['revealed'])}/10 · 金币 {row['coins']}",font=small,fill='#f6e4b5')
 d.text((505,581),'到达敌人地点，进入战斗' if row['battle'] else '正常速度离线合成 · 光影近似',font=small,fill='#c9d9b6')
 frames.append(f)
gif(frames,'travel-normal.gif');del frames

battle=json.loads((DATA/'battle-frames.json').read_text());frames=[]
for row in battle:
 a=row['action'];age=a.get('age',0);dim=.58*e['smooth'](age/.4)*(1-e['smooth']((age-1.2)/.6)) if a else 0
 f=ImageEnhance.Brightness(plate).enhance(1-dim)
 for u in sorted(row['units'],key=lambda u:feet[u['id']][1]):
  x,y=feet[u['id']];v=a.get('travel',{}) if a.get('actor')==u['id'] else {};dx,dy=v.get('x',0),v.get('y',0)
  if u['id'].startswith('p'):
   im=render(u['clip'],u['progress']);xx,yy=x+dx-123*hs,y+dy-214*hs
   shadow(f,im,xx,yy,hs);f.alpha_composite(im.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(xx),round(yy)))
  else:
   death=u['deathAge'];motion=u['monster'];xx=x+dx-178.5*es;yy=y+dy-240*es
   if death is not None:
    shadow(f,e['enemy'],xx,yy,es,1-e['smooth'](death/.75))
    if death<116/60:
     im=e['bodies'][min(47,int(death*60))];f.alpha_composite(im.resize((round(384*es),round(256*es)),Image.Resampling.NEAREST),(round(xx),round(yy)))
     f.alpha_composite(e['winds'][min(115,int(death*60))].resize((round(448*es),round(320*es)),Image.Resampling.NEAREST),(round(x-178.5*es),round(y-272*es)))
   else:
    im=e['enemy_attacks'][min(7,int(motion['progress']*8))];sy=motion['scaleY'];xx+=motion['recoil'];yy=y+dy-240*es*sy
    shadow(f,e['enemy'],xx,yy,es);f.alpha_composite(im.resize((round(384*es),round(256*es*sy)),Image.Resampling.NEAREST),(round(xx),round(yy)))
 f.alpha_composite(foreground)
 if a and a['visual']=='attack':
  elapsed=age-a['impact'];target=next(u for u in row['units'] if u['id']==a['target']);p=feet[target['id']]
  at=(p[0]+(10 if a['enemy'] else -80),p[1]-(65 if a['enemy'] else 72));power=e['pulse'](elapsed,-.035,.035,.52)
  glow(f,at,140,140,power*.48,(255,175,45));glow(f,p,170,30,power*.65,(255,175,45))
  if 0<=elapsed<.7:compose(f,e['assets']['Burst'],at,(150+elapsed*140,150+elapsed*140),power,True)
 for q in row['particles']:
  col=(30,200,255) if q['cyan'] else (255,175,45);at=(q['x'],q['y'])
  if q['id']%6==0:glow(f,at,22,20,q['alpha']*.2,col)
  if q['groundAge'] is not None and q['groundAge']<.24:glow(f,(q['groundX'],q['groundY']),34,10,(1-q['groundAge']/.24)*q['alpha']*.6,col)
  compose(f,asset('BattleVFXCyanShard') if q['cyan'] else e['assets']['GoldEmber'],at,(q['size'],q['size']*.67),q['alpha'],True,q['angle'])
 for i,(die,pose) in enumerate(zip(a.get('dice',[]),a.get('poly',[]))):
  im=die_image(die,pose);im.putalpha(im.getchannel('A').point(lambda alpha:round(alpha*pose['alpha'])))
  cx=a['diceAnchor']['x']+(i-(len(a['dice'])-1)/2)*min(82,200/max(1,len(a['dice'])))
  cy=a['diceAnchor']['y']+43+pose['offsetY']
  f.alpha_composite(im,(round(cx-128),round(cy-120)))
 d=ImageDraw.Draw(f)
 for msg in row['messages']:
  d.text((msg['x'],msg['y']-(row['time']-msg['at'])*26),msg['text'],font=large,fill='#ffead5',stroke_width=2,stroke_fill='#272214',anchor='mm')
 for u in row['units']:
  if u['id'].startswith('m') and u['hp']==0:continue
  x,y=feet[u['id']];y-=170 if u['id'].startswith('p') else 224
  d.rounded_rectangle((x-88,y,x+88,y+39),4,fill='#17291e',outline='#9f935b')
  d.text((x-80,y+2),u['name'],font=small,fill='#fff2c9');d.rectangle((x-80,y+27,x+80,y+33),fill='#06100a')
  if u['hp']:d.rectangle((x-79,y+28,x-79+158*u['hp']/u['maxHP'],y+32),fill='#59cf7c')
 out=Image.new('RGB',(1000,730),'#162a20');out.paste(f,(0,40));d=ImageDraw.Draw(out)
 d.text((14,7),('正式行程 · 战斗胜利' if row['terminal'] else f"正式行程遭遇 · 第{row['round']}轮 · 同一规则回执"),font=font,fill='#f9e4b2')
 d.text((905,10),f"{row['time']:.2f}s",font=small,fill='#d7d6b6')
 statusbar(out,[u for u in row['units'] if u['id'].startswith('p')],644)
 if row['frame'] in [0,50,100,160,230,340,470,620,800,947]:out.save(OUT/f"encounter-whole-frame-{row['frame']:04d}.png")
 out=out.resize((720,526),Image.Resampling.LANCZOS);frames.append(out)
# Keep the complete encounter as video. A lossless GIF of every dimming frame
# is >100 MB; the normal-speed GIF deliberately covers the final 5.96 seconds.
with tempfile.TemporaryDirectory(prefix='meadow-campaign-review-') as temporary:
 full=Path(temporary)/'encounter-full.gif'
 gif(frames,str(full))
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(full),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'encounter-full.mp4')],check=True)
 optimizer=os.environ.get('GIFSICLE') or shutil.which('gifsicle')
 if not optimizer:raise SystemExit('Install gifsicle or set GIFSICLE; no lossy optimization is used.')
 clip=Path(temporary)/'victory.gif'
 gif(frames[650:],str(clip)) # decode/rebase first frame; never select a delta GIF without its canvas
 subprocess.run([optimizer,'-O3',str(clip),'--resize-width=640','-o',str(OUT/'encounter-normal.gif')],check=True)
 with Image.open(OUT/'encounter-normal.gif') as check:
  assert check.n_frames==298
  for i in range(check.n_frames):
   check.seek(i);assert check.info.get('duration')==20

(OUT/'review.json').write_text(json.dumps({'offline':True,'lightingAndUIApproximate':True,'notUIKitOrDevice':True,'walkFrames':len(walk),'battleFrames':len(battle),'battleFullVideo':'encounter-full.mp4','battleGifSourceStartFrame':650,'battleGifSourceEndFrame':947,'battleGifFrames':298,'battleGifMs':20,'battleGifScope':'last 5.96s, lethal contact and complete victory dissolve','frameMs':20,'gameplayData':'actual MeadowCampaignSession / shared PartyEncounter engine / production pose+light fields','artApproval':None},ensure_ascii=False,indent=2)+'\n')
