#!/usr/bin/env python3
"""UNREVIEWED recovery candidate. Not a production importer or accepted asset.
Run only after recovering the workspace, then personally inspect whole-body GIFs.
Rest input: Art/Parts/P1-Battle/armor-fit-r1 (Build62).
Only the two ArmNearUpperWardrobe PNGs are written; no rig or other part changes.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[4]
A=R/'Sources/Resources/Assets.xcassets'
D=R/'Art/Parts/P1-Battle/armor-fit-r2'
D.mkdir(parents=True,exist_ok=True)
S=np.array([117.,141.]);E=np.array([128.,158.])
axis=(E-S)/np.linalg.norm(E-S)
normal=np.array([-axis[1],axis[0]])
yy,xx=np.mgrid[:256,:256]
p=np.stack([xx,yy],-1)
u=(p-S)@axis;q=(p-S)@normal
records=[]
for item,prefix in [('leatherArmor','MeadowLeatherArmor'),('runeArmor','MeadowRuneArmor')]:
    slot='MeadowBattleHeroArmNearUpperWardrobe'
    src=Image.open(R/'Art/Parts/P1-Battle/armor-fit-r1'/item/(slot+'.png')).convert('RGBA')
    source=np.asarray(src);visible=source[:,:,3]>=100
    sections=np.arange(4.,22.01,.5);centers=[];halves=[]
    for value in sections:
        vals=q[visible&(abs(u-value)<1.2)]
        if len(vals):
            lo,hi=np.percentile(vals,[5,95])
            centers.append((lo+hi)/2);halves.append(max(2.,(hi-lo)/2))
        else:
            centers.append(centers[-1] if centers else 0)
            halves.append(halves[-1] if halves else 5)
    length=15.5 if item=='leatherArmor' else 20.7
    radius=(6.5-1.2*np.clip(u/length,0,1)) if item=='leatherArmor' else (6.0-1.2*np.clip(u/length,0,1))
    mask=(u>=-1)&(u<=length)&(abs(q)<=radius)
    textureU=np.clip(4+np.clip(u/length,0,1)*(13.0 if item=='leatherArmor' else 16.4),4,21.5)
    center=np.interp(textureU,sections,centers);half=np.interp(textureU,sections,halves)
    textureQ=center+q/radius*half
    uv=S+textureU[:,:,None]*axis+textureQ[:,:,None]*normal
    sx=np.clip(np.rint(uv[:,:,0]),0,255).astype(int)
    sy=np.clip(np.rint(uv[:,:,1]),0,255).astype(int)
    _,nearest=distance_transform_edt(~visible,return_indices=True)
    out=np.zeros_like(source)
    out[mask,:3]=source[nearest[0,sy,sx],nearest[1,sy,sx],:3][mask]
    out[mask,3]=255
    edge=mask&(abs(q)>radius-1)
    out[edge]=(67,36,20,255) if item=='leatherArmor' else (30,39,49,255)
    if item=='leatherArmor':
        cuff=mask&(u>length-2.4)
        out[cuff]=(231,214,179,255)
        out[cuff&(q<-1)]=(255,244,216,255)
        out[cuff&(q>1.8)]=(177,149,117,255)
        out[mask&(u>length-1)]=(81,47,28,255)
    else:
        out[mask&(u>length-1)]=(15,30,48,255)
    image=Image.fromarray(out)
    folder=D/item;folder.mkdir(exist_ok=True)
    image.save(folder/(slot+'.png'))
    name=prefix+'ArmNearUpperWardrobe'
    image.save(A/(name+'.imageset')/(name+'.png'))
    records.append({'item':item,'replacement':name,'sameShoulder':[117,141],
                    'sameElbow':[128,158],'sleeveEndAlongUpperArm':length,
                    'onlyUpperGarmentPixelsChanged':True})
(D/'manifest.json').write_text(json.dumps({
    'repairs':records,'userApproval':None,'rootArtReviewCompleted':False,
    'status':'UNREVIEWED candidate; no Build63 IPA'
},indent=2)+'\n')
print('Unreviewed upper-sleeve candidates generated. Art inspection required.')
