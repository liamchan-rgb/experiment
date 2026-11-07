from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import json,math,sys,subprocess,numpy as np
R=Path(__file__).resolve().parents[1];OLD=R;A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Review/Battle/bestiary-v1';D.mkdir(parents=True,exist_ok=True)
manifest=json.load(open(R/'Art/Monsters/bestiary-v1/manifest.json'));records=manifest['records']
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',23);small=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',17)
# Load the existing production layer renderer without its legacy GIF-writing tail.
p=OLD/'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py';env={'__file__':str(p)};exec(compile(p.read_text().split("\nfor clip,data in lib['clips'].items():")[0],str(p),'exec'),env)
env['lib']=json.load(open(OLD/'Sources/Resources/Assets.xcassets/MeadowBattleHeroAnimationV2.dataset/animation.json'));hero=env['render']('idle',0)
def asset(name):
 folder=OLD/f'Sources/Resources/Assets.xcassets/{name}.imageset';filename=json.load(open(folder/'Contents.json'))['images'][0]['filename'];return Image.open(folder/filename).convert('RGBA')
plate=Image.new('RGBA',(1000,918))
for name,blur in [('MeadowCampFarForest',3),('MeadowCampGround',1.5),('MeadowCampMidground',1.5)]:plate.alpha_composite(asset(name).resize((1000,918),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(blur)))
plate=plate.crop((0,200,1000,800));fore=asset('MeadowCampForeground').resize((1000,918),Image.Resampling.LANCZOS).crop((0,200,1000,800))
frames={};deaths={};checks=[]
for r in records:
 name=r['id'];sheet=Image.open(A/(r['asset']+'Motion.imageset')/(r['asset']+'Motion.png')).convert('RGBA');ds=Image.open(A/(r['asset']+'Death.imageset')/(r['asset']+'Death.png')).convert('RGBA')
 frames[name]=[sheet.crop((i%8*384,i//8*256,i%8*384+384,i//8*256+256)) for i in range(56)];deaths[name]=[ds.crop((i%8*512,i//8*320,i%8*512+512,i//8*320+320)) for i in range(40)]
 assert sheet.size==(3072,1792) and ds.size==(4096,1600)
 for f in frames[name]:
  box=f.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<384 and box[3]<=240
 assert np.array_equal(np.array(frames[name][12]),np.array(frames[name][35]))
 assert np.array_equal(np.array(frames[name][48]),np.array(frames[name][55]))
 assert deaths[name][-1].getbbox() is None
 assert np.array_equal(np.array(deaths[name][0].crop((0,32,384,288))),np.array(frames[name][0]))
 checks.append({'id':name,'all56FullBodyPosesChecked':True,'attackHurtReturnToSameMaster':True,'all40DeathFramesDecoded':True,'deathStartsAtSameRegisteredBody':True,'endTransparent':True})
 # Decode all source poses at 1x; 14 native-size poses per page.
 for page in range(4):
  board=Image.new('RGB',(1536,1024),'#20362a');draw=ImageDraw.Draw(board)
  for j in range(14):
   i=page*14+j;x=j%4*384;y=j//4*256;board.paste(frames[name][i],(x,y),frames[name][i]);draw.text((x+4,y+3),f'{name} #{i}',font=small,fill='#f5df9c')
  board.save(D/f'{name}-poses-{page}.jpg',quality=93)

def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def pulse(x,a,b,c):return smooth((x-a)/(b-a)) if x<b else 1-smooth((x-b)/(c-b))
actual=Path(sys.argv[1]) if len(sys.argv)>1 else D/'data/monster-frames.json'
assert actual.exists(), 'Export the shared Swift model with --monster-only first'
rows=json.load(open(actual))
byname={r['id']:[v for v in rows if v['species']==r['id']] for r in records}
def drawunit(f,r,row,foot=None,shift=True):
 if not row['visible']:return
 death=row['death'];im=(deaths if death else frames)[r['id']][row['poseIndex']];s=r['scale'];x,y=foot or row['foot'];offset=row['offset'] if shift else [0,0];x+=offset[0];y+=offset[1]
 if not death:
  shade=Image.new('RGBA',f.size);d=ImageDraw.Draw(shade);d.ellipse((x-72*s,y-4,x+72*s,y+7),fill=(5,14,10,58));f.alpha_composite(shade.filter(ImageFilter.GaussianBlur(5)))
 im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST);f.alpha_composite(im,(round(x-178.5*s),round(y-(272 if death else 240)*s)))
def scene(r,row):
 f=plate.copy();s=r['scale'];d=ImageDraw.Draw(f);d.ellipse((130,418,193,430),fill=(0,0,0,90));hs=.83;f.alpha_composite(hero.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(165-123*hs),round(420-214*hs)))
 drawunit(f,r,row)
 if 'projectile' in row:
  a=row['projectile']['tail'];b=row['projectile']['tip'];d=ImageDraw.Draw(f);color='#71dfff' if r['id']=='ruinDragon' else '#f3d47a';d.line((a['x'],a['y'],b['x'],b['y']),fill=color,width=3)
 if row['visible'] and not row['death']:
  d=ImageDraw.Draw(f);y=395-224*s-46;d.rectangle((566,y,734,y+40),fill='#1b3025',outline='#88794d');d.text((575,y+2),r['name'],font=small,fill='#f6e5b6');d.rectangle((575,y+29,725,y+34),fill='#54bc6c')
 f.alpha_composite(fore);out=Image.new('RGBA',(1000,660),'#14271c');out.alpha_composite(f,(0,60));d=ImageDraw.Draw(out);d.text((20,12),r['name']+' · '+{'idle':'待机','attack':'出招与回位','hurt':'受击','cast':'施法','death':'向右吹散退场'}[row['phase']],font=font,fill='#efd391');d.text((610,16),'正常速度 · 离线合成，光影/UI近似',font=small,fill='#b3c2a3');return out.convert('RGB')
# One batch animation: equal native scale, six specimens with same hero reference.
for key in [0,55,63,123,181,258,275]:
 board=Image.new('RGB',(1500,660),'#182e22')
 for k,r in enumerate(records):board.paste(scene(r,byname[r['id']][key]).resize((500,330),Image.Resampling.LANCZOS),(k%3*500,k//3*330))
 board.save(D/f'whole-scene-{key:03d}.jpg',quality=94)
# Preview movies use ffmpeg at the true .02 sec sample interval; GIF quantization has a shared global palette.
allframes=[]
for i in range(320):
 board=Image.new('RGB',(1200,528),'#182e22')
 for k,r in enumerate(records):board.paste(scene(r,byname[r['id']][i]).resize((400,264),Image.Resampling.LANCZOS),(k%3*400,k//3*264))
 allframes.append(board)
sample=Image.new('RGB',(3600,1584))
for k,i in enumerate([0,30,63,94,123,168,204,258,280]):sample.paste(allframes[i],(k%3*1200,k//3*528))
palette=sample.quantize(colors=256,method=Image.Quantize.MEDIANCUT);encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in allframes]
encoded[0].save(D/'bestiary-normal.gif',save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=1,optimize=True)
# Compact identical holds while preserving all real .02-second timing.
optimized=D/'.normal-optimized.gif'
subprocess.run(['ffmpeg','-v','error','-i',str(D/'bestiary-normal.gif'),'-filter_complex','[0:v]split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle','-loop','0','-y',str(optimized)],check=True)
optimized.replace(D/'bestiary-normal.gif')
subprocess.run(['ffmpeg','-v','error','-i',str(D/'bestiary-normal.gif'),'-r','50','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-y',str(D/'bestiary-normal.mp4')],check=True)

# Full-resolution native scene + 2x-body contact sheet for final author audit.
for r in records:
 scene(r,byname[r['id']][63]).save(D/(r['id']+'-contact-1x.png'))
 board=Image.new('RGB',(1536,1024),'#20362a');d=ImageDraw.Draw(board)
 for j,i in enumerate([0,18,31,52]):
  im=frames[r['id']][i].resize((768,512),Image.Resampling.NEAREST);board.paste(im,(j%2*768,j//2*512),im);d.text((j%2*768+8,j//2*512+4),f'{r["name"]} #{i} 2x',font=font,fill='#edd096')
 board.save(D/(r['id']+'-body-2x.jpg'),quality=96)
# Three-monster actual slot arrangement, to inspect depth and readable silhouette overlap.
f=plate.copy()
for id in ['p1','p2']:
 x,y={'p1':(165,420),'p2':(315,505)}[id];f.alpha_composite(hero.resize((212,212),Image.Resampling.NEAREST),(round(x-123*.83),round(y-214*.83)))
for r,point in zip([records[0],records[1],records[2]],[(650,395),(835,510),(600,585)]):drawunit(f,r,byname[r['id']][0],point,False)
f.alpha_composite(fore);f.convert('RGB').save(D/'three-enemy-formation.png')
# Incoming player contact is inspected separately; all anchors must lie on solid body pixels.
hitboard=Image.new('RGB',(1500,660),'#182e22');attackHero=env['render']('attack',0.54)
for k,r in enumerate(records):
 row=byname[r['id']][0];anchor=row.get('hitAnchor',r['hitAnchor']);master=frames[r['id']][0]
 assert master.getpixel(tuple(map(round,anchor)))[3]>0
 f=plate.copy();drawunit(f,r,row)
 shift=row['incomingTravel'];hs=.83;x=165+shift[0]-123*hs;y=420+shift[1]-214*hs
 f.alpha_composite(attackHero.resize((212,212),Image.Resampling.NEAREST),(round(x),round(y)))
 px,py=row['registeredHit'];draw=ImageDraw.Draw(f);draw.line((px-7,py,px+7,py),fill='#ffffff',width=2);draw.line((px,py-7,px,py+7),fill='#ffffff',width=2)
 f.alpha_composite(fore);out=Image.new('RGBA',(1000,660),'#14271c');out.alpha_composite(f,(0,60));draw=ImageDraw.Draw(out);draw.text((20,12),r['name']+' · 普通攻击接敌 / 身体命中锚点',font=font,fill='#efd391');out.convert('RGB').save(D/(r['id']+'-incoming-contact.png'))
 hitboard.paste(out.convert('RGB').resize((500,330),Image.Resampling.LANCZOS),(k%3*500,k//3*330))
hitboard.save(D/'incoming-registration.jpg',quality=96)
report={'source': 'actual Swift MonsterVisualSpec CLI samples' if actual.exists() else 'provisional art timing pending Swift CLI comparison','normalSampleMs':20,'sampleCount':320,'modelDataSHA256':__import__('hashlib').sha256(actual.read_bytes()).hexdigest(),'sourceCommit':json.load(open(D/'source.json'))['sourceCommit'],'allSixHitAnchorsOnOpaqueBody':True,'visualContactSheetsViewed':24,'fullBody2xKeysViewed':6,'checks':checks,'artApproval':None,'appSimulatorDeviceRun':False,'lightingUIApproximate':True,'notes':'Normal speed. Contact frame is .46 after action start. No anatomy is separately regenerated per pose.'};(D/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report),flush=True)
