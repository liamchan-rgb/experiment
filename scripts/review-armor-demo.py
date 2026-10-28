#!/usr/bin/env python3
"""Normal-speed assembled armor review using production Swift pose exports.
Offline layers, not UIKit capture or a game run.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,math,functools,subprocess
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Review/Battle/armor-demo-v1';D.mkdir(parents=True,exist_ok=True)
p=R/'scripts/review-bow-actions-r7-demo.py';N={'__file__':str(p)};exec(compile(p.read_text().split('# Check every registered frame')[0],str(p),'exec'),N)
base=N['base'];world=N['world'];rigdata=N['lib'];native_bow=N['composite'];origasset=N['asset'];oldtile=N['painted_tile'];gait=json.loads((R/'Sources/Resources/hero-gait.json').read_text());font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14)
weapons=['trainingSword','huntingBow','greatSword','legendaryStaff'];armors=['leatherArmor','runeArmor'];pauldron='MeadowBattleHeroPauldronNearWardrobe';names={'leatherArmor':'皮甲','runeArmor':'符文甲','trainingSword':'短剑','huntingBow':'猎弓','greatSword':'重剑','legendaryStaff':'权杖'}
poses={w:{(r.get('clip','attack'),round(r['progress']*600)):r['sample'] for r in json.loads((R/'Art/Review/Battle'/d/f).read_text())} for w,d,f in [('greatSword','great-sword-demo-v1','great-sword-poses.json'),('legendaryStaff','legendary-staff-demo-v1','legendary-staff-poses.json')]};stafforder=json.loads((R/'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/legendary-staff-v1.json').read_text())['layerOrder']
@functools.lru_cache(4096)
def actor(item,w,clip,p):
 v=gait['armorVisuals'][item]
 if w=='huntingBow':
  def asset(n):return origasset(v['bowTorso'] if n=='MeadowBattleBowReviewedTorso' else n)
  def tile(rig,group):
   t=rigdata['tiles'][rig['nativeTiles'][group]];im=Image.new('RGBA',(256,256));atlas=origasset(v['bowAtlas']);im.paste(atlas.crop((t['x'],t['y'],t['x']+t['width'],t['y']+t['height'])),(t['canvasX'],t['canvasY']));return im
  N['asset']=asset;N['painted_tile']=tile
  return native_bow(N['poses'][(clip,round(p*600))],clip,p)
 if w in poses:
  q=poses[w][(clip,round(p*600))];root=(q['rootOffset']['x'],q['rootOffset']['y']);ts={n:((t['pivot']['x'],t['pivot']['y']),(t['offset']['x'],t['offset']['y']),t['rotation']) for n,t in q['layers'].items()};order=list(stafforder) if w=='legendaryStaff' else list(base['ordered_layers'](clip))
 else:ts,root,*_=world['sample'](clip,p);order=list(base['ordered_layers'](clip))
 if pauldron not in order:order.insert(order.index('MeadowBattleHeroArmNearUpperWardrobe')+1,pauldron)
 a=ts.get('MeadowBattleHeroArmNearUpperWardrobe',((0,0),(0,0),0));b=ts.get('MeadowBattleHeroWardrobeCore',((0,0),(0,0),0));delta=math.atan2(math.sin(a[2]-b[2]),math.cos(a[2]-b[2]));ts[pauldron]=(a[0],a[1],b[2]+min(math.pi/15,max(-math.pi/15,delta*.38)))
 out=Image.new('RGBA',(256,256))
 for name in order:
  if name=='MeadowBattleHeroJointUnderlay' and clip=='idle' and w!='legendaryStaff':continue
  source=v['battleLayers'].get(name,name)
  if name=='MeadowBattleHeroWeapon':source={'greatSword':'MeadowBattleGreatSword','legendaryStaff':'MeadowBattleLegendaryStaff'}.get(w,name)
  if name==pauldron and name not in v['battleLayers']:continue
  im=origasset(source);pivot,off,angle=ts.get(name,((0,0),(0,0),0));im=im.rotate(-math.degrees(angle),Image.Resampling.NEAREST,center=pivot);out.alpha_composite(im,(round(off[0]+root[0]),round(off[1]+root[1])))
 return out

def board(item,clip,p):
 out=Image.new('RGB',(1024,280),'#20372a');d=ImageDraw.Draw(out)
 for col,w in enumerate(weapons):
  im=actor(item,w,clip,p);out.paste(im,(col*256,0),im);d.text((col*256+8,258),names[item]+' · '+names[w]+' · '+clip,font=font,fill='#f0e4b6')
 return out
reports=[]
def save(name,frames,durations):
 sample=Image.new('RGB',(frames[0].width*4,frames[0].height*4))
 for i in range(16):sample.paste(frames[round((len(frames)-1)*i/15)],(i%4*frames[0].width,i//4*frames[0].height))
 pal=sample.quantize(colors=256,method=Image.Quantize.MEDIANCUT);encoded=[im.quantize(palette=pal,dither=Image.Dither.NONE) for im in frames];path=D/(name+'-normal.gif');encoded[0].save(path,save_all=True,append_images=encoded[1:],duration=durations,loop=0,disposal=2,optimize=False)
 tool=Path('/workspace/gifsicle-1.96/src/gifsicle')
 if tool.exists():
  temp=path.with_suffix('.opt.gif');subprocess.run([str(tool),'-O3',str(path),'-o',str(temp)],check=True);temp.replace(path)
 gif=Image.open(path);decoded=[];total=0
 for i in range(gif.n_frames):gif.seek(i);decoded.append(gif.convert('RGB').copy());total+=gif.info['duration']
 assert total==sum(durations)
 for page in range(math.ceil(len(decoded)/8)):
  out=Image.new('RGB',(1024,8*300),'#20372a');dd=ImageDraw.Draw(out)
  for j,im in enumerate(decoded[page*8:page*8+8]):
   out.paste(im,(0,j*300));dd.text((4,j*300+280),f'{name} / decoded {page*8+j}',font=font,fill='#f0e4b6')
  out.save(D/f'{name}-decoded-{page+1:02}.png')
 reports.append({'file':path.name,'decodedFrames':gif.n_frames,'durationMs':total});return decoded
for item in armors:
 frames=[]
 for n in range(190):
  age=n*.02-1;progress=0 if age<0 else 1 if age>1.7 else (max(0,age)/.86*((.86-.4)/1.2) if age<=.86 else min(1,max(0,(age-.4-min(.1,max(0,age-1.048)))/1.2)))
  # Use each original weapon's production progress at the shared action age.
  im=Image.new('RGB',(1024,280),'#20372a');dd=ImageDraw.Draw(im)
  for col,w in enumerate(weapons):
   if w=='legendaryStaff':t=age*1.25/1.048 if age<=1.048 else 1.25 if age<=1.148 else 1.25+.52*min(1,(age-1.148)/.552);q=max(0,min(1,(t-.12)/1.65))
   elif w=='greatSword':t=age*1.0275/1.048 if age<=1.048 else 1.0275 if age<=1.148 else 1.0275+.7425*min(1,(age-1.148)/.552);q=max(0,min(1,(t-.12)/1.65))
   elif w=='huntingBow':q=progress
   else:q=max(0,min(1,(age-.4-min(.1,max(0,age-1.048)))/1.2))
   clip='idle' if age<0 or age>=1.7 else 'attack';sp=actor(item,w,clip,round(q*600)/600);im.paste(sp,(col*256,0),sp);dd.text((col*256+5,258),names[item]+' · '+names[w],font=font,fill='#f0e4b6')
  frames.append(im)
 frames[0].save(D/(item+'-standing.png'));save(item+'-attack',frames,[20]*len(frames))
 for wi,w in enumerate(weapons):
  board1=Image.new('RGB',(1280,1680),'#20372a')
  for ri,clip in enumerate(['idle','attack','guard','hit','victory','defeat']):
   for ci,q in enumerate([0,.25,.5,.75,1]):
    sp=actor(item,w,clip,q);x=ci*256;y=ri*280;board1.paste(sp,(x,y),sp);ImageDraw.Draw(board1).text((x+5,y+258),names[item]+' '+names[w]+' '+clip+f' {q:.2f}',font=font,fill='#f0e4b6')
  board1.save(D/f'{item}-{w}-states-1x.png');board1.resize((2560,3360),Image.Resampling.NEAREST).save(D/f'{item}-{w}-states-2x.png')
 # Original generic state durations for presentation; bow states retain own samples.
 frames=[]
 for clip in ['guard','hit','victory','defeat']:
  count={'guard':48,'hit':42,'victory':54,'defeat':54}[clip]
  for n in range(count):frames.append(board(item,clip,n/(count-1)))
 save(item+'-states',frames,[20]*len(frames))
 # For staff first and last cast whole image must equal idle, including clothing.
 assert actor(item,'legendaryStaff','idle',0).tobytes()==actor(item,'legendaryStaff','attack',0).tobytes()==actor(item,'legendaryStaff','attack',1).tobytes()
# Walking whole-body normal-speed eight-direction overview and all13 source poses.
W=R/'Art/Review/P1/armor-demo-v1';W.mkdir(parents=True,exist_ok=True)
for item in armors:
 for appearance in ['forester','wayfarer']:
  load=next(x for x in gait['modularP1']['loadouts'] if x['id']==appearance);atlases=load['armorAtlasNames'][item]['trainingSword'];frames=[]
  for n in range(1,9):
   out=Image.new('RGB',(1024,560),'#20372a')
   for row in range(8):
    sp=origasset(atlases[row//4]).crop((n*256,row%4*256,(n+1)*256,row%4*256+256));out.paste(sp,(row%4*256,row//4*280),sp)
   frames.append(out)
  frames[0].save(W/f'{item}-{appearance}-standing.png');frames[0].save(W/f'{item}-{appearance}-walk-normal.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=True)
  for half in range(4):
   out=Image.new('RGB',(1792,1120),'#20372a')
   for row in range(2):
    idx=half*2+row;atlas=origasset(atlases[idx//4])
    for n in range(13):
     sp=atlas.crop((n*256,idx%4*256,(n+1)*256,idx%4*256+256));x=n%7*256;y=(row*2+n//7)*280;out.paste(sp,(x,y),sp);ImageDraw.Draw(out).text((x+4,y+258),f'{idx} / {n}',font=font,fill='#f0e4b6')
   out.save(W/f'{item}-{appearance}-poses-{half+1}.png')
(D/'review.json').write_text(json.dumps({'animations':reports,'scope':'Production weapon pose exports; current armor atlas and layer mapping; offline, no device capture','walkingBindings':2080,'bowScope':'Material-only garment adaptation, original silhouette and grips retained','userApproval':None},indent=2)+'\n');print(reports,flush=True)
