#!/usr/bin/env python3
"""Fresh 60 Hz UV samples, never frame duplication or painted monster changes."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Scenes/MeadowBattle/smooth-status-v1';src=R/'scripts/review-battle-effects-v3.py';e={'__file__':str(src)};exec(compile(src.read_text().split('\nframes=[]; traces=[]')[0],str(src),'exec'),e)
def output(name,im):
 p=np.asarray(im).copy();p[p[:,:,3]==0,:3]=0;folder=A/(name+'.imageset');folder.mkdir(exist_ok=True);Image.fromarray(p).save(folder/(name+'.png'));(folder/'Contents.json').write_text(json.dumps({'images':[{'filename':name+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')
fps=60;body_count=48;wind_count=116;columns=8;wind_width=448;body=Image.new('RGBA',(384*columns,256*6));wind=Image.new('RGBA',(wind_width*columns,320*15));ep=e['ep'];threshold=e['threshold'];smooth=e['smooth'];pulse=e['pulse'];stamp=e['stamp'];es=e['es'];W=e['W'];ex=e['ex'];wind_valid=[];body_alpha=[]
for i in range(wind_count):
 age=i/fps+.012
 if i<body_count:
  dissolve=.08+.92*smooth(age/.76);keep=threshold>=dissolve;p=ep.copy();p[:,:,3]=(ep[:,:,3]*keep).astype('uint8');edge=keep&(threshold<dissolve+.065);p[edge,:3]=[255,244,195];p[p[:,:,3]==0,:3]=0;cell=Image.fromarray(p);body.alpha_composite(cell,((i%8)*384,(i//8)*256));body_alpha.append(int(p[:,:,3].sum()))
 cell=Image.new('RGBA',(wind_width,320))
 for j,(px,py,birth,vx,vy,life,tile) in enumerate(e['particles']):
  t=age-birth
  if 0<=t<life:
   dx=(vx*t+55*t*t)/es;detach=W*.025*pulse(3.648+birth,3.628,3.788,4.168)/es;c=(px+detach+dx,32+py+(vy*t+2*math.sin(t*9+j))/es);alpha=(1-smooth(t/life))*min(1,max(0,(W-10-ex-c[0]*es)/38));stamp(cell,tile,c,tile.size,alpha)
   if j%3==0:stamp(cell,e['sprites']['mote'],c,((11+18*t)/es,4/es),alpha*.9)
 wind.alpha_composite(cell,((i%8)*wind_width,(i//8)*320));wind_valid.append(cell.getbbox() is not None)
output('BattleVFXDeathBody60',body);output('BattleVFXDeathWind60',wind)
config={'fps':60,'bodyCount':48,'windCount':116,'columns':8,'bodyCell':[384,256],'windCell':[448,320],'windOffset':[0,-32],'firstSampleSeconds':.012,'durationSeconds':116/60,'windCrop':'760-reference viewport clips at native x~448; only offscreen transparent tail margin removed','sameMonsterUVsAnd650Particles':True,'bodyAlphaMonotonic':all(x>=y for x,y in zip(body_alpha,body_alpha[1:])),'lastBodyAndWindEmpty':body_alpha[-1]==0 and not wind_valid[-1],'firstWindNonempty':wind_valid[0],'decodedAtlasBytes':body.width*body.height*4+wind.width*wind.height*4,'artApproval':None}
assert config['bodyAlphaMonotonic'] and config['lastBodyAndWindEmpty'] and config['firstWindNonempty'];(D/'smooth-death.json').write_text(json.dumps(config,indent=2)+'\n');print(json.dumps(config))
