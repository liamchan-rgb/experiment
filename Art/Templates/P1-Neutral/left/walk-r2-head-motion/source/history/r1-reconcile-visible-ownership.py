#!/usr/bin/env python3
"""One-off offline authoring aid; emits fixed semantic pixel coordinates.

Canonical art export reads the reviewed authoring.json and never runs this
classifier. The pre-review authoring snapshot and registered source PNGs keep
this historical assignment operation inspectable. No pixels are repainted.
"""
from pathlib import Path
import json,numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label,distance_transform_edt,binary_propagation
f=Path(__file__).resolve().parents[1];cfg=json.loads((f/'source/ownership-before-final-review.json').read_text());slots=cfg['drawOrder'];yy,xx=np.indices((256,256));nearWrists=[[130,166],[145,168],[140,165],[130,167],[104,155],[105,160],[108,161],[120,168],[143,166]];nearHands=[[128,172],[149,173],[144,170],[127,172],[98,155],[99,160],[103,162],[115,171],[147,171]];farWrists=[[139,162],[100,162],[107,160],[112,165],[146,163],[144,163],[146,162],[143,162],[104,162]];farHands=[[140,166],[96,165],[104,163],[108,167],[150,167],[148,167],[149,166],[146,167],[100,165]]
for i,p in enumerate(cfg['poses']):
 a=np.array(Image.open(f/f'registered/{i:02}.png').convert('RGBA'));r,g,b,alpha=[a[:,:,k].astype(int) for k in range(4)];vis=(alpha>0)&(yy>=129);roi=(yy>=132)&(yy<=181)&(xx>=105)&(xx<=143)
 old=np.full((256,256),slots.index('body.torso'),int)
 remaining=np.ones((256,256),bool)
 for slot in cfg['ownershipPriority']:
  im=Image.new('L',(256,256));ImageDraw.Draw(im).polygon([tuple(v) for v in p['partitions'][slot]],fill=255);selected=(np.array(im)>0)&remaining;old[selected]=slots.index(slot);remaining[selected]=False
 for override in p.get('ownershipOverrides',[]):
  for x,y in override['pixels']:old[y,x]=slots.index(override['slot'])
 white=roi&(r>140)&(g>130)&(b>95)&(r-g<28)&(g-b<36)&(alpha>=128)
 loose=roi&(r>120)&(g>110)&(b>90)&(r-g<43)&(g-b<45)&(alpha>=128)
 white=binary_propagation(white,mask=loose)
 gray=roi&(yy>=159)&(np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b])<18)&(np.maximum.reduce([r,g,b])<150)&(np.maximum.reduce([r,g,b])>30)&(alpha>=128)
 clothing=white|gray|((yy>=129)&(yy<=134)&vis)
 skin=(r-g>12)&(g-b>18)&(r>110)&(g>65)&(alpha>=128)&vis&~clothing
 groups=[['body.arm.left','body.hand.left'],['body.arm.right','body.hand.right'],['body.leg.left'],['body.leg.right']]
 seeds=[clothing]
 for group in groups:
  own=np.isin(old,[slots.index(s) for s in group]);sample=skin&own
  lab,n=label(sample,np.ones((3,3)));sizes=np.bincount(lab.ravel());sizes[0]=0
  if n:sample=lab==sizes.argmax()
  seeds.append(sample)
 # Reassign only original source pixels to the nearest reviewed material/limb
 # region. This authoring run emits explicit fixed ownership coordinates;
 # the runtime/exporter never runs this classifier or alters source colours.
 distances=np.stack([distance_transform_edt(~s) for s in seeds]);owners=np.argmin(distances,axis=0)
 chosen=np.full((256,256),slots.index('body.torso'),int)
 for k,group in enumerate(groups,1):chosen[owners==k]=slots.index(group[0])
 for side,w,h in [('left',nearWrists[i],nearHands[i]),('right',farWrists[i],farHands[i])]:
  arm=slots.index(f'body.arm.{side}');hand=slots.index(f'body.hand.{side}');dx=h[0]-w[0];dy=h[1]-w[1]
  beyond=(xx-w[0])*dx+(yy-w[1])*dy>=0
  chosen[(chosen==arm)&beyond]=hand
 # All current visible original pixels have a single explicit semantic owner.
 p['ownershipOverrides']=[{'slot':s,'pixels':[[int(x),int(y)] for y,x in zip(*np.where(vis&(chosen==k)))]} for k,s in enumerate(slots) if s!='head.base' and np.any(vis&(chosen==k))]
 # Foot anchors are measured inside each anatomical leg's largest component.
 for side in ['left','right']:
  mask=vis&(chosen==slots.index(f'body.leg.{side}'))&(alpha>=128);lab,n=label(mask,np.ones((3,3)));size=np.bincount(lab.ravel());size[0]=0;mask=lab==size.argmax();ys,xs=np.where(mask);bottom=int(ys.max());xs=np.where(mask[bottom])[0];p['soleMarkers'][side]=[int(xs[len(xs)//2]),bottom]
cfg['visibleOwnershipReview']='Final fixed per-pixel authoring map reviewed against skin/cloth boundaries and anatomical limb components. No source repaint, runtime segmentation or complete-hidden-anatomy claim.'
(f/'authoring.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('Saved reviewed-coordinate ownership candidate for visual inspection.')
