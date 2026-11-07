#!/usr/bin/env python3
"""Offline review from production Swift samples and imported native layer atlases.
Does not run UIKit, an app, simulator or device.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFont
import sys,json,math,functools,subprocess
R=Path(__file__).resolve().parents[1];NAME='bow-actions-r7-demo-v1';D=R/'Art/Review/Battle'/NAME;A=R/'Sources/Resources/Assets.xcassets'
old=R/'scripts/review-hunting-bow-a-project-r1.py';S={'__file__':str(old)}
code=old.read_text().split("if '--stills' in sys.argv:")[0].replace('hunting-bow-a-project-r1',NAME).replace('pose A','Build57 · 猎弓')
exec(compile(code,str(old),'exec'),S)
world=S['namespace'];base=world['render'].__globals__
lib=json.loads((R/'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/reviewed-bow-r7.json').read_text())
poses={(r['clip'],round(r['progress']*600)):r['sample'] for r in json.loads((D/'bow-poses.json').read_text())}
@functools.lru_cache(None)
def asset(name):
 p=A/(name+'.imageset');desc=json.loads((p/'Contents.json').read_text());return Image.open(p/next(x['filename'] for x in desc['images'] if x.get('filename'))).convert('RGBA')
atlas=asset('MeadowBattleBowReviewedSleeves')
skip={'MeadowBattleHeroWeapon','MeadowBattleHeroFarHand','MeadowBattleHeroNearHand','MeadowBattleHeroJointUnderlay','MeadowBattleHeroWardrobeCore','MeadowBattleHeroArmNearUpperBody','MeadowBattleHeroArmNearForearmBody','MeadowBattleHeroArmNearUpperWardrobe','MeadowBattleHeroArmNearForearmWardrobe'}
names=[n for n in base['config']['layers'] if n not in skip];insert=names.index('MeadowBattleHeroHair')
order=names[:insert]+['farArm','nearUpperArm','torso','nearSleeveConnected','head']+names[insert:]+['MeadowBattleHeroWeapon','geometry','farHand','nearHand']
def painted_tile(rig,group):
 tile=lib['tiles'][rig['nativeTiles'][group]];im=Image.new('RGBA',(256,256))
 im.paste(atlas.crop((tile['x'],tile['y'],tile['x']+tile['width'],tile['y']+tile['height'])),(tile['canvasX'],tile['canvasY']));return im
def composite(rig,clip,p):
 transforms,root,_,_,_=world['sample']('idle',0) if clip in ['attack','idle'] else world['sample'](clip,p)
 if rig.get('canvasBaked'):
  root=(rig['rootOffset']['x'],rig['rootOffset']['y'])
 out=Image.new('RGBA',(256,256))
 for name in order:
  if name=='geometry':
   dd=ImageDraw.Draw(out);dd.line([(round(rig[k]['x']+root[0]),round(rig[k]['y']+root[1])) for k in ['upperTip','stringHand','lowerTip']],fill='#e1c78c',width=1)
   if rig['arrowVisible']:
    a=rig['arrowTail'];b=rig['arrowTip'];ax=a['x']+root[0];ay=a['y']+root[1];bx=b['x']+root[0];by=b['y']+root[1]
    dd.line((ax,ay,bx,by),fill='#d4ab66',width=1);dd.polygon([(bx+2,by),(bx-3,by-2),(bx-3,by+2)],fill='#d8e0d9')
   continue
  if name in rig['nativeTiles']:
   im=painted_tile(rig,name);t=rig['parts']['torso'];pivot=(t['pivot']['x'],t['pivot']['y']);offset=(0,0) if rig.get('canvasBaked') else (t['offset']['x'],t['offset']['y']);angle=0 if rig.get('canvasBaked') else t['rotation']
  elif name in ['torso','head']:
   im=asset('MeadowBattleBowReviewedTorso' if name=='torso' else 'MeadowBattleBowReviewedBodyCore').copy();t=rig['parts']['torso'];pivot=(t['pivot']['x'],t['pivot']['y']);offset=(t['offset']['x'],t['offset']['y']);angle=t['rotation']
   if name=='head':
    mask=Image.new('L',(256,256));dd=ImageDraw.Draw(mask);dd.rectangle((100,75,156,132),fill=255);dd.polygon([(121,126),(135,130),(134,138),(125,138),(119,134)],fill=255);im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
  else:
   target={'MeadowBattleHeroBodyCore':'MeadowBattleBowReviewedBodyCore','MeadowBattleHeroLegNearThighWardrobe':'MeadowBattleBowReviewedLegNearThighWardrobe','MeadowBattleHeroLegFarThighWardrobe':'MeadowBattleBowReviewedLegFarThighWardrobe','MeadowBattleHeroWeapon':'MeadowBattleHuntingBow'}.get(name,name)
   im=asset(target).copy();pivot,offset,angle=transforms.get(name,((0,0),(0,0),0))
   if name=='MeadowBattleHeroBodyCore':
    mask=Image.new('L',(256,256));ImageDraw.Draw(mask).rectangle((100,174,152,190),fill=255);im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
   if name=='MeadowBattleHeroWeapon':
    t=rig['parts']['bow'];pivot=(t['pivot']['x'],t['pivot']['y']);offset=(t['offset']['x'],t['offset']['y']);angle=t['rotation']
  im=im.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=pivot)
  out.alpha_composite(im,(round(offset[0]+root[0]),round(offset[1]+root[1])))
 return out
original_render=world['render']
@functools.lru_cache(2048)
def gear_render(clip,progress,weapon_id):
 if weapon_id!='huntingBow':return S['gear_render_original'](clip,progress,weapon_id)
 i=round(max(0,min(1,progress))*600);return composite(poses[(clip,i)],clip,progress)
S['gear_render_original']=S['gear_render'];S['gear_render']=gear_render;world['gear_render']=gear_render
# Check every registered frame, beyond only those selected by gameplay timing.
SOURCE=R/'Art/Parts/P1-Battle/hunting-bow-full-cycle-r7-v1'
for rig in lib['frames'][:143]:
 actual=composite(rig,'attack',0);expected=Image.open(SOURCE/'frames'/f'{rig["nativeFrame"]:03}'/'assembled.png').convert('RGBA')
 assert actual.tobytes()==expected.tobytes(),('native import composite mismatch',rig['nativeFrame'])
print('143/143 imported full composites match approved native source pixels.',flush=True)
C=R/'Art/Parts/P1-Battle/hunting-bow-actions-r7-v1'
for clip,desc in json.loads((C/'animation.json').read_text())['clips'].items():
 for record,index in zip(desc['frames'],lib['clips'][clip]):
  rig=lib['frames'][index];actual=composite(rig,clip,record['progress']);expected=Image.open((C/record['pose']).parent/'assembled.png').convert('RGBA')
  
  if actual.tobytes()!=expected.tobytes():
   actual.save('/workspace/actions-import-actual.png');expected.save('/workspace/actions-import-expected.png');print('diffbbox',ImageChops.difference(actual,expected).getbbox());raise AssertionError((clip,index))
print('202/202 new modular state composites match authored pixels.',flush=True)
font=S['font'];rows=S['rows']
def save_normal(name,frames,size):
 pal=Image.new('RGB',(frames[0].width*6,frames[0].height*6))
 for j in range(36):pal.paste(frames[min(len(frames)-1,j*(len(frames)-1)//35)],(j%6*frames[0].width,j//6*frames[0].height))
 palette=pal.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 encoded=[im.resize(size,Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
 encoded[0].save(D/(name+'-normal.gif'),save_all=True,append_images=encoded[1:],duration=20,disposal=2,optimize=False)
 optimizer=Path('/workspace/gifsicle-1.96/src/gifsicle')
 if optimizer.exists():
  path=D/(name+'-normal.gif');temporary=path.with_suffix('.optimized.gif')
  subprocess.run([str(optimizer),'-O3',str(path),'-o',str(temporary)],check=True);temporary.replace(path)
 gif=Image.open(D/(name+'-normal.gif'));total=0;decoded=[]
 for i in range(gif.n_frames):
  gif.seek(i);dur=gif.info['duration'];decoded.append((gif.convert('RGB').copy(),total,dur));total+=dur
 assert total==len(frames)*20
 for page in range(math.ceil(len(decoded)/20)):
  board=Image.new('RGB',(1280,1216),'#20372a');dd=ImageDraw.Draw(board)
  for j,(im,t,dur) in enumerate(decoded[page*20:page*20+20]):
   x=j%5*256;y=j//5*304;im.thumbnail((256,280));board.paste(im,(x,y));dd.text((x+4,y+282),f'{t/1000:.2f}s / {dur}ms',font=font(12),fill='#f0e4b6')
  board.save(D/f'{name}-decoded-{page+1:02}.jpg',quality=97)
 return {'file':name+'-normal.gif','nativeSamples':len(frames),'decodedFrames':len(decoded),'durationMs':total}
reports=[]
if '--check-only' in sys.argv:sys.exit(0)
# All new states plus the actual reverse trajectory used by revival. Explicit
# timestamps preserve the duration of held pixel poses in the decoded GIF.
action_report=[];montage=[]
for clip,duration in [('guard',1400),('hit',700),('victory',1080),('defeat',600),('revive',600)]:
 frames=[];count=duration//20
 for i in range(count+1):
  p=i/count;source='defeat' if clip=='revive' else clip
  if clip=='revive':p=1-p*p*(3-2*p)
  elif clip=='defeat':p=p*p*(3-2*p)
  sprite=gear_render(source,p,'huntingBow');im=Image.new('RGB',(256,280),'#20372a');im.paste(sprite,(0,0),sprite);ImageDraw.Draw(im).text((6,258),f'{clip} {i*.02:.2f}s',font=font(14),fill='#f0e4b6');frames.append(im)
 action_report.append(save_normal(clip,frames,(768,840)));montage.extend(frames)
 montage.extend([frames[-1]]*10)
reports.append(save_normal('all-actions',montage,(768,840)))
reports.extend(action_report)
if '--states-only' in sys.argv:
 (D/'state-review-render.json').write_text(json.dumps(reports,indent=2)+'\n');sys.exit(0)

for scenario in ['bow','bow-lethal']:
 rs=[r for r in rows if r['scenario']==scenario];body=[]
 for row in rs:
  u=next(u for u in row['units'] if u['id']=='p1');sprite=gear_render(u['clip'],u['progress'],'huntingBow');im=Image.new('RGB',(256,280),'#20372a');im.paste(sprite,(0,0),sprite);ImageDraw.Draw(im).text((6,258),f'{row["time"]:.2f}s',font=font(14),fill='#f0e4b6');body.append(im)
 if scenario=='bow':reports.append(save_normal('body',body,(768,840)))
 if scenario=='bow':body[0].resize((768,840),Image.Resampling.NEAREST).save(D/'body-standing.png')
 rendered=[]
 for row in rs:
  im=S['ui'](row,S['scene'](row)).convert('RGB');rendered.append(im.resize((1020,math.floor(im.height*1020/im.width)),Image.Resampling.LANCZOS))
 reports.append(save_normal(scenario,rendered,(1020,math.floor(rendered[0].height*1020/rendered[0].width))))
 for t,label in [(0,'standing'),(1.5,'nocking'),(1.78,'drawn'),(1.86,'release'),(2.10,'impact'),(2.90,'rest')]:
  row=min(rs,key=lambda r:abs(r['time']-t));S['ui'](row,S['scene'](row)).save(D/(scenario+'-'+label+'.png'))
for page in range(2):
 board=Image.new('RGB',(1024,1120),'#20372a');dd=ImageDraw.Draw(board)
 poseset=[(clip,p) for clip in ['idle','attack','guard','hit','victory','defeat'] for p in [0,.25,.5,.75,1]]
 for j,(clip,p) in enumerate(poseset[page*15:page*15+15]):
  im=gear_render(clip,p,'huntingBow');x=j%4*256;y=j//4*280;board.paste(im,(x,y),im);dd.text((x+6,y+258),f'{clip} / {p:.2f}',font=font(14),fill='#f0e4b6')
 board.save(D/f'all-clips-{page+1:02}-1x.png');board.resize((2048,2240),Image.Resampling.NEAREST).save(D/f'all-clips-{page+1:02}-2x.png')
(D/'review-render.json').write_text(json.dumps({'scope':'Production Swift samples plus imported independent layers; offline art composition, not UIKit/device capture','all143NativeCompositesByteExact':True,'all202NewModularCompositesByteExact':True,'animations':reports,'appRunPerformed':False},indent=2)+'\n')
print(json.dumps(reports),flush=True)
