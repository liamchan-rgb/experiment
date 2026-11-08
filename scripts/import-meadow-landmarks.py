#!/usr/bin/env python3
"""Register generated atlas cells as transparent map props. Preserve source;
normalize image size, remove invalid red-matte spill on transparent boundaries,
and retain the outpost's intended cloth/shield red. No character art is edited.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/Map/meadow-locations-v1'; A=R/'Sources/Resources/Assets.xcassets'
source=P/'source/retouch-atlas.png';im=Image.open(source).convert('RGBA');cell=im.width//2
assert im.width==im.height and im.width%2==0
items=[('NodeCombatOutpost','combat',0,0),('NodeBossSanctum','boss',1,0),('NodeRewardCache','reward',0,1),('NodeWaystone','empty',1,1)]
records=[];preview=Image.new('RGBA',(1024,1024),'#233c2c')
for name,kind,c,r in items:
 raw=im.crop((c*cell,r*cell,(c+1)*cell,(r+1)*cell));a=np.array(raw)
 # Neon-red matte contamination is distinct from the muted red painted cloth.
 # Only the narrow alpha boundary is repaired, never the object's interior.
 boundary=ndimage.binary_dilation(a[:,:,3]<=8,iterations=5)
 bad=(a[:,:,0]>210)&(a[:,:,1]<45)&(a[:,:,2]<45)&boundary&(a[:,:,3]>0)
 valid=(a[:,:,3]>=128)&~bad
 distance,indices=ndimage.distance_transform_edt(~valid,return_indices=True)
 repaired=a.copy();repaired[bad,:3]=a[indices[0][bad],indices[1][bad],:3]
 repaired[bad&(distance>3)]=0
 labels,count=ndimage.label(repaired[:,:,3]>0)
 sizes=np.bincount(labels.ravel());small=sizes<9;small[0]=False;repaired[small[labels]]=0
 repaired[repaired[:,:,3]==0]=0
 art=Image.fromarray(repaired).resize((480,480),Image.Resampling.NEAREST)
 out=Image.new('RGBA',(512,512));out.alpha_composite(art,(16,16))
 p=P/(name+'.png');out.save(p)
 folder=A/(name+'.imageset');folder.mkdir(parents=True,exist_ok=True);out.save(folder/(name+'.png'))
 (folder/'Contents.json').write_text(json.dumps({'images':[{'filename':name+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')
 preview.alpha_composite(out,(c*512,r*512))
 records.append({'asset':name,'nodeKind':kind,'canvas':[512,512],'anchorY':0.08,'sourceCell':[c*cell,r*cell,cell,cell],'matteSpillPixelsRepaired':int(bad.sum()),'fixedCellTransform':{'scale':480/cell,'translation':[16,16]},'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
preview.convert('RGB').save(P/'buildings-on-green.png')
(P/'assets.json').write_text(json.dumps({'originalSHA256':hashlib.sha256((P/'source/original-atlas.png').read_bytes()).hexdigest(),'retouchSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'items':records,'artApproval':None,'method':'image generation + image-tool retouch; fixed atlas slicing and technical matte decontamination; source retained'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(records,ensure_ascii=False))
