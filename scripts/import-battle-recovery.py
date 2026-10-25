#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'Art/Scenes/MeadowBattle/skill-flow-v1';A=R/'Sources/Resources/Assets.xcassets';src=D/'source/healing-atlas.png';im=Image.open(src).convert('RGBA');w,h=im.size;cuts={}
for n,(x,y) in {'HealStar':(0,0),'HealWisp':(1,0),'HealShaft':(0,1),'HealWave':(1,1)}.items():
 region=(x*w//2,y*h//2,(x+1)*w//2,(y+1)*h//2);tile=im.crop(region);box=tile.getchannel('A').point(lambda a:255 if a>3 else 0).getbbox();tile=tile.crop(box);data=np.asarray(tile).copy();data[data[:,:,3]==0,:3]=0;tile=Image.fromarray(data);tile.save(D/(n+'.png'));folder=A/('BattleVFX'+n+'.imageset');folder.mkdir(exist_ok=True);tile.save(folder/('BattleVFX'+n+'.png'))
 (folder/'Contents.json').write_text(json.dumps({'images':[{'filename':'BattleVFX'+n+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n');cuts[n]={'region':region,'contentCrop':box,'size':tile.size}
(D/'manifest.json').write_text(json.dumps({'source':'source/healing-atlas.png','sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'cuts':cuts,'shieldNativeCenter':[128,144],'shieldNativeDiameter':240,'shieldAttachment':'direct child of hero, non-animated layer transaction','healing':'26 staggered upward spiral motes, two winding ribbons, soft shaft and temporary expanding wave','cameraChanged':False,'artApproval':None},ensure_ascii=False,indent=2)+'\n');print(cuts)
