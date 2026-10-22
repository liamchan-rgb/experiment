#!/usr/bin/env python3
"""Export pose-specific painted garments, preserving source ink and cloth folds.

The generated sheets are art sources, not replacement body frames. Fixed whole-
sheet registration precedes explicit offline semantic masks. The runtime reads
only PNG/manifest data and keeps the existing body and motion.
"""
import hashlib,importlib.util,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,distance_transform_edt,label

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BODY=ROOT/'Art/Templates/P1-Neutral/left/walk-r3-complete-transitions'
SIZE=(256,256)
Y,X=np.mgrid[:256,:256]
SLOTS={'forester':['outfit.torso','outfit.sleeve.right','outfit.sleeve.left'],
       'lower':['outfit.pants.right','outfit.boot.right','outfit.pants.left','outfit.boot.left'],
       'wayfarer':['outfit.torso','outfit.sleeve.right','outfit.sleeve.left','outfit.hem.front']}
IDS={'forester':'p1-left-forester-v2','lower':'p1-left-traveler-lower-v2','wayfarer':'p1-left-wayfarer-coat-v2'}


def grow(mask,n=1):
 return binary_dilation(mask,structure=np.ones((3,3)),iterations=n)


def distance(mask):
 return distance_transform_edt(~mask)


def attached(mask,anchor):
 labels,count=label(mask,np.ones((3,3),dtype=np.uint8))
 keep=np.zeros_like(mask)
 for n in range(1,count+1):
  component=labels==n
  if np.any(component&grow(anchor,1)):keep|=component
 return keep


def painted(source,mask,core,material_seed,record):
 """Keep all original paint, including ink, then add a hidden material underlap."""
 rgba=np.array(source).copy()
 mask=attached(mask,core)
 rgba[:,:,3]=np.where(mask,255,0).astype(np.uint8)
 missing=core&~mask
 if missing.any():
  valid=material_seed&(np.array(source)[:,:,3]>=128)
  assert valid.any(),'No authored material for underlap'
  dist,indices=distance_transform_edt(~valid,return_indices=True)
  rgba[missing,:3]=rgba[indices[0][missing],indices[1][missing],:3]
  rgba[:,:,3][missing]=255
  record['underlapPixels']=int(missing.sum())
  record['maxSourceDistance']=float(dist[missing].max())
 else:record.update(underlapPixels=0,maxSourceDistance=0)
 return Image.fromarray(rgba)


def main():
 spec=importlib.util.spec_from_file_location('editable',ROOT/'scripts/export-wardrobe-part.py')
 helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 motion=json.loads((BODY/'motion.json').read_text())
 geometry=json.loads((BODY/'source/hidden-geometry.json').read_text())['poses']
 sheets={}
 for tag in ['green','blue']:
  source=Image.open(HERE/'source'/f'{tag}-13poses-generated.png').convert('RGBA')
  assert source.size==(1254,1254)
  sheets[tag]=source.resize((1024,1024),Image.Resampling.NEAREST)
 bindings={key:[] for key in SLOTS};records=[]
 for i,frame in enumerate(motion['frames']):
  body={slot:np.array(Image.open(BODY/'layers'/f'{i:02}'/f'{slot}.png').getchannel('A'))>=13
        for slot in ['body.torso','body.arm.left','body.arm.right','body.leg.left','body.leg.right','body.hand.left','body.hand.right']}
  visible={slot:np.array(Image.open(BODY/'source/visible-layers'/f'{i:02}'/f'{slot}.png').getchannel('A'))>=13 for slot in body}
  upper_anchor=(visible['body.torso']&(Y>=126)&(Y<=173))|visible['body.arm.left']|visible['body.arm.right']
  lower_anchor=visible['body.leg.left']|visible['body.leg.right']|(visible['body.torso']&(Y>=165))
  all_parts={key:{} for key in SLOTS}
  for tag in ['green','blue']:
   source=sheets[tag].crop((i%4*256,i//4*256,i%4*256+256,i//4*256+256))
   pixels=np.array(source);r,g,b,a=[pixels[:,:,j].astype(float) for j in range(4)]
   opaque=(a>=128)&~((r>190)&(g<45)&(b<45))
   cloth=(g>r*1.12)&(g>b*1.12)&(r<125) if tag=='green' else (b>r*1.25)&(b>g*1.12)&(b>30)
   cloth &= opaque&(Y>=126)&(Y<=198)
   # Keep complete source ink, gold trim and shaded cloth near painted cloth;
   # do not select only green/blue pixels and discard the outlines again.
   upper=opaque&grow(cloth,2)&(distance(upper_anchor)<5)&(Y>=126)&(Y<=175)
   skin=(r>g*1.13)&(g>b*1.08)&(r>100)&(b>80)
   # Skin colours and pale gold overlap numerically. Restrict skin exclusion
   # to the actual wrist/hand neighbourhood, preserving the front/collar ink.
   hand_neighbourhood=grow(visible['body.hand.left']|visible['body.hand.right'],4)
   upper &= ~(skin&hand_neighbourhood)
   nearest=np.argmin(np.stack([distance(visible['body.torso']&(Y<=173)),distance(visible['body.arm.right']),distance(visible['body.arm.left'])]),axis=0)
   package='forester' if tag=='green' else 'wayfarer'
   for j,slot in enumerate(['outfit.torso','outfit.sleeve.right','outfit.sleeve.left']):
    body_slot=['body.torso','body.arm.right','body.arm.left'][j]
    core=body[body_slot]&grow(visible[body_slot],1)
    if j==0:
     core &= (Y>=128)&(Y<=171)
     core[128:138,120:133]=False # existing anatomical neck opening
    rec={'storageIndex':i,'package':package,'slot':slot}
    all_parts[package][slot]=painted(source,upper&(nearest==j),core,cloth&(distance(visible[body_slot])<7),rec)
    records.append(rec)
   if tag=='blue':
    hem=opaque&grow(cloth,2)&(Y>=172)&(Y<=198)&(distance(lower_anchor)<17)&~(skin&hand_neighbourhood)
    hem=attached(hem,upper_anchor|lower_anchor)
    output=source.copy();output.putalpha(Image.fromarray((hem*255).astype('uint8')))
    all_parts['wayfarer']['outfit.hem.front']=output
   if tag=='green':
    neutral=(np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b])<27)&(r<120)&opaque&(Y>=164)
    brown=(r>g*1.2)&(g>b*1.1)&(r<215)&(g<145)&opaque&(Y>=177)
    # Source art for each actual pose supplies every fold and the tilted boot.
    side_dist=np.stack([distance(visible['body.leg.right']),distance(visible['body.leg.left'])])
    owner=np.argmin(side_dist,axis=0)
    # The painted boot opening determines the material boundary. A fixed
    # horizontal calf band would overpaint authored trouser fabric brown.
    boot_material=distance(brown)<=distance(neutral)+1.5
    for j,side in enumerate(['right','left']):
     leg='body.leg.'+side;sole=geometry[i]['soleMarkers'][side][1]
     leg_core=body[leg]&grow(visible[leg],1)
     boot_core=leg_core&boot_material&(Y>=sole-22)
     pant_core=leg_core&~boot_core
     # The shared waistband belongs once to the near leg, above safety shorts.
     if side=='left':pant_core |= body['body.torso']&(Y>=165)
     pant_mask=opaque&grow(neutral,1)&(owner==j)&(Y>=164)&(Y<=sole-10)&(distance(lower_anchor)<4)
     rec={'storageIndex':i,'package':'lower','slot':'outfit.pants.'+side}
     all_parts['lower']['outfit.pants.'+side]=painted(source,pant_mask,pant_core,neutral&(distance(visible[leg])<7),rec);records.append(rec)
     boot_mask=opaque&grow(brown,1)&(owner==j)&(Y>=sole-22)&(Y<=sole+2)&(distance(visible[leg])<5)
     rec={'storageIndex':i,'package':'lower','slot':'outfit.boot.'+side}
     all_parts['lower']['outfit.boot.'+side]=painted(source,boot_mask,boot_core,brown&(distance(visible[leg])<7),rec);records.append(rec)
  for package,parts in all_parts.items():
   # The existing visible knuckles belong exclusively to the shared body.
   # A longer coat or wider torso may not repaint the far hand after its slot.
   hand_guard=np.zeros(SIZE,dtype=bool)
   for side in ['left','right']:
    hand_guard |= np.array(Image.open(BODY/'source/visible-layers'/f'{i:02}'/f'body.hand.{side}.png').getchannel('A'))>=250
   head_guard=np.array(Image.open(BODY/'layers'/f'{i:02}'/'head.base.png').getchannel('A'))>=250
   for slot,image in parts.items():
    rgba=np.array(image).copy();rgba[:,:,3][hand_guard|head_guard]=0;parts[slot]=Image.fromarray(rgba)
   folder=HERE/package;dest=folder/'png'/f'{i:02}';dest.mkdir(parents=True,exist_ok=True)
   (folder/'editable').mkdir(exist_ok=True)
   ordered={slot:parts[slot] for slot in SLOTS[package]}
   for slot,image in ordered.items():image.save(dest/f'{slot}.png')
   helper.editable(folder/'editable',f'{i:02}',ordered)
   bindings[package].append({'direction':'left','clip':frame['clip'],'frame':frame['frame'],
     'layers':{slot:f'png/{i:02}/{slot}.png' for slot in SLOTS[package]}})
 for package in SLOTS:
  folder=HERE/package;(folder/'source').mkdir(exist_ok=True)
  tag='blue' if package=='wayfarer' else 'green';source=HERE/'source'/f'{tag}-13poses-generated.png'
  shutil.copyfile(source,folder/'source/garment-13poses.png')
  author={'id':IDS[package],'source':'source/garment-13poses.png','sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'sourceCanvas':[1254,1254],'fixedSheetRegistration':{'scale':1024/1254,'output':[1024,1024],'grid':[4,4],'cell':[256,256],'poses':13},
    'bodyTemplate':str(BODY.relative_to(ROOT)),'artMethod':'pose-specific imagegen paint; source ink retained; no idle texture warped across the gait',
    'underlap':'same material only, inside original body coverage; no body changes','slots':SLOTS[package]}
  (folder/'authoring.json').write_text(json.dumps(author,indent=2)+'\n')
  asset={'schemaVersion':'1.0.0','id':IDS[package],'version':'2.0.0','part':'outfit',
   'compatibility':{'rig':'p1-chibi-v1','bodyProfile':'p1-standard','actionSet':'locomotion-v1'},
   'mode':'pose-map','slots':SLOTS[package],'directions':['left'],'clips':['idle','walk','walk-start','walk-stop'],
   'sourceFiles':['source/garment-13poses.png','authoring.json']+[f'editable/{i:02}.{ext}' for i in range(13) for ext in ['ora','svg']],
   'bindings':bindings[package]}
  (folder/'asset.json').write_text(json.dumps(asset,indent=2)+'\n')
 (HERE/'underlap-records.json').write_text(json.dumps(records,indent=2)+'\n')
 print(json.dumps({'packages':3,'poses':13,'slotPNGs':13*sum(map(len,SLOTS.values())),'largestUnderlapDistance':max(row['maxSourceDistance'] for row in records)}))

if __name__=='__main__':main()
