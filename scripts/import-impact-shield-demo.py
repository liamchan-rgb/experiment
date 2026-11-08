#!/usr/bin/env python3
"""Import original optical sprites and a registered chest-contact/light response."""
from pathlib import Path
import json,hashlib,shutil,math
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'Art/Scenes/MeadowBattle/impact-shield-v1';A=ROOT/'Sources/Resources/Assets.xcassets'
raw=ART/'source/atlas-clean.png';im=Image.open(raw).convert('RGBA');w,h=im.size;cuts={}
def output(name,img):
 data=np.asarray(img).copy();data[data[:,:,3]==0,:3]=0;img=Image.fromarray(data)
 folder=A/f'{name}.imageset';folder.mkdir(exist_ok=True);img.save(folder/f'{name}.png')
 (folder/'Contents.json').write_text(json.dumps({'images':[{'filename':f'{name}.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')
 return img
for name,(cx,cy) in {'HeavyArc':(0,0),'HeavySpray':(1,0),'Barrier':(0,1),'WardHit':(1,1)}.items():
 rect=(cx*w//2,cy*h//2,(cx+1)*w//2,(cy+1)*h//2);tile=im.crop(rect);bbox=tile.getchannel('A').point(lambda a:255 if a>3 else 0).getbbox();tile=tile.crop(bbox)
 tile=output('BattleVFX'+name,tile);tile.save(ART/f'{name}.png');cuts[name]={'gridCell':rect,'contentCrop':bbox,'size':tile.size}
# Read only the original V3 UV definitions; do not execute its export loop.
src=ROOT/'scripts/review-battle-effects-v3.py';scope={'__file__':str(src)};exec(compile(src.read_text().split('\nframes=[]; traces=[]')[0],str(src),'exec'),scope)
ep=scope['ep'];es=scope['es'];ex=scope['ex'];W=scope['W'];smooth=scope['smooth'];stamp=scope['stamp'];pulse=scope['pulse']
sy,sx=np.mgrid[:256,:384];local=np.exp(-(((sx-125)*es/68)**2+((sy-164)*es/68)**2)*2);mask=np.zeros_like(ep);mask[:,:,:3]=[255,247,215];mask[:,:,3]=(ep[:,:,3]*local).astype('uint8');output('BattleVFXHeavyHitMask',Image.fromarray(mask))
# Same accepted rightward disintegration; align fragment detach offsets with heavier recoil.
sheet=Image.new('RGBA',(640*8,320*6))
for i in range(48):
 age=i*.04+.032;wind=Image.new('RGBA',(640,320))
 for j,(px,py,birth,vx,vy,life,tile) in enumerate(scope['particles']):
  a=age-birth
  if 0<=a<life:
   dx=(vx*a+55*a*a)/es;detach=W*.025*pulse(3.648+birth,3.628,3.788,4.168)/es
   center=(px+detach+dx,32+py+(vy*a+2*math.sin(a*9+j))/es)
   alpha=(1-smooth(a/life))*min(1,max(0,(W-10-ex-center[0]*es)/38))
   stamp(wind,tile,center,(tile.width,tile.height),alpha)
   if j%3==0:stamp(wind,scope['sprites']['mote'],center,((11+18*a)/es,4/es),alpha*.9)
 sheet.alpha_composite(wind,((i%8)*640,(i//8)*320))
output('BattleVFXDeathWindHeavy',sheet)
manifest={'status':'candidate','artApproval':None,'sourceAtlas':'source/atlas-clean.png','sourceSHA256':hashlib.sha256(raw.read_bytes()).hexdigest(),'cuts':cuts,'strikeContactNativeEnemy':[125,164],'previewDarken':.45,'castDarken':.64,'impactDarkenPeak':.82,'hitHoldMs':100,'shieldStages':['generation','sustain','contact-ripple','last-point-break'],'noChargeTiers':True,'deathTiming':'same impact event as HP0 and number','oldVersionsPreserved':True}
(ART/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('Imported 4 optical sprites, local hit mask and recoil-aligned wind; original artwork retained.')
