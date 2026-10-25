#!/usr/bin/env python3
"""Bake approved v3 UV fragments; runtime only crops registered flipbook cells."""
from pathlib import Path
import json,shutil,hashlib,math
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'Sources/Resources/Assets.xcassets';OUT=ROOT/'Art/Integration/Battle-effects-demo-v1';OUT.mkdir(exist_ok=True,parents=True)
source=ROOT/'scripts/review-battle-effects-v3.py';scope={'__file__':str(source)}
exec(compile(source.read_text().split('\nframes=[]; traces=[]')[0],str(source),'exec'),scope)

def image_asset(name,im):
 d=A/f'{name}.imageset';d.mkdir(exist_ok=True);im.save(d/f'{name}.png');(d/'Contents.json').write_text(json.dumps({'images':[{'filename':f'{name}.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')
for name in ['slash','burst','ring','mote']:image_asset('BattleVFX'+name.title(),scope['sprites'][name])
np=scope['np'];source_enemy=np.asarray(scope['enemy']);sy,sx=np.mgrid[:256,:384]
local=np.exp(-(((sx-110)*scope['es']/68)**2+((sy-184)*scope['es']/68)**2)*2)
mask=np.zeros_like(source_enemy);mask[:,:,:3]=[255,244,200];mask[:,:,3]=(source_enemy[:,:,3]*local).astype('uint8');mask[mask[:,:,3]==0,:3]=0
image_asset('BattleVFXHitMask',Image.fromarray(mask))

count=48;columns=8;body_size=(384,256);wind_size=(640,320);rows=math.ceil(count/columns)
body_sheet=Image.new('RGBA',(384*columns,256*rows));wind_sheet=Image.new('RGBA',(640*columns,320*rows))
np=scope['np'];ep=scope['ep'];threshold=scope['threshold'];smooth=scope['smooth'];stamp=scope['stamp'];spec=scope['spec'];enemy=scope['enemy'];particles=scope['particles'];es=scope['es'];ex=scope['ex'];ey=scope['ey'];W=scope['W'];recoil=scope['pulse'];duration=.76;birthhold=.032
for i in range(count):
 age=i*.04+birthhold;dissolve=.08+.92*smooth(age/duration);keep=threshold>=dissolve
 pixels=ep.copy();pixels[:,:,3]=(ep[:,:,3]*keep).astype('uint8');edge=keep&(threshold<dissolve+.065);pixels[edge,:3]=[255,244,195];pixels[pixels[:,:,3]==0,:3]=0
 body=Image.fromarray(pixels);wind=Image.new('RGBA',wind_size)
 for j,(px,py,birth,vx,vy,life,tile) in enumerate(particles):
  a=age-birth
  if 0<=a<life:
   # Convert the approved 760px scene trajectory into native monster coordinates.
   dx=(vx*a+55*a*a)/es;detach=W*.017*recoil(3.648+birth,3.628,3.788,4.168)/es
   center=(px+detach+dx,32+py+(vy*a+2*math.sin(a*9+j))/es)
   world_x=ex+center[0]*es;alpha=(1-smooth(a/life))*min(1,max(0,(W-10-world_x)/38))
   stamp(wind,tile,center,(tile.width,tile.height),alpha)
   if j%3==0:stamp(wind,scope['sprites']['mote'],center,((11+18*a)/es,4/es),alpha*.9)
 body_sheet.alpha_composite(body,((i%columns)*384,(i//columns)*256));wind_sheet.alpha_composite(wind,((i%columns)*640,(i//columns)*320))
image_asset('BattleVFXDeathBody',body_sheet);image_asset('BattleVFXDeathWind',wind_sheet)
# Preserve the previous runtime animation JSON before importing accepted contact posture.
p=A/'MeadowBattleHeroAnimationV2.dataset/animation.json';backup=OUT/'source/pre-vfx-animation.json'
if not backup.exists():shutil.copyfile(p,backup)
lib=json.loads(backup.read_text());lib['clips']['attack']=json.loads((ROOT/'Art/Scenes/MeadowBattle/effects-v1/attack-clip.json').read_text());p.write_text(json.dumps(lib,indent=2)+'\n')
config={'schemaVersion':1,'deathFrames':count,'deathColumns':columns,'deathFrameSeconds':.04,'bodyCell':[384,256],'windCell':[640,320],'windOffset':[0,-32],'deathInitialSampleSeconds':birthhold,'v3Source':'Art/Scenes/MeadowBattle/effects-v3/effect.json','skillPower':{'strike':.9,'heal':.28,'guard':.28},'previewDarken':.34,'castDarken':.56}
d=A/'BattleVFXConfig.dataset';d.mkdir(exist_ok=True);(d/'config.json').write_text(json.dumps(config,indent=2)+'\n');(d/'Contents.json').write_text(json.dumps({'data':[{'filename':'config.json','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n');(OUT/'selection.json').write_text(json.dumps(config,indent=2)+'\n')
print('Imported four optical sprites, registered 48-frame body/wind atlases, v3 contact posture and data config.')
