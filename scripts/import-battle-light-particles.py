#!/usr/bin/env python3
"""Fixed optical cuts; original sheet and all previous assets remain intact."""
from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'Art/Scenes/MeadowBattle/particles-round-shield-v1';A=R/'Sources/Resources/Assets.xcassets'
src=D/'source/atlas.png';im=Image.open(src).convert('RGBA');assert im.width==im.height
regions={'RoundBarrier':(0,0,640,700),'CyanShard':(700,0,1280,700),'GoldEmber':(0,700,640,1280),'GroundSpark':(640,700,1280,1280)};cuts={}
for n,normalized in regions.items():
 region=tuple(round(v*im.width/1280) for v in normalized)
 tile=im.crop(region);box=tile.getchannel('A').point(lambda a:255 if a>3 else 0).getbbox();tile=tile.crop(box);data=np.asarray(tile).copy();data[data[:,:,3]==0,:3]=0;tile=Image.fromarray(data)
 tile.save(D/(n+'.png'));folder=A/('BattleVFX'+n+'.imageset');folder.mkdir(exist_ok=True);tile.save(folder/('BattleVFX'+n+'.png'))
 (folder/'Contents.json').write_text(json.dumps({'images':[{'filename':'BattleVFX'+n+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n');cuts[n]={'region':region,'contentCrop':box,'size':tile.size}
(D/'manifest.json').write_text(json.dumps({'artApproval':None,'status':'candidate','source':'source/atlas.png','sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'cuts':cuts,'packing':'circle glow extends below 640; explicit non-overlapping region to y700 preserves it; no neighboring sprite enters crop','shield':'round 132x132 world units, transparent center; saturated blue rim','physics':'production MeadowBattleLightField; analytic gravity, restitution and ground contacts'},indent=2)+'\n')
print(cuts)
