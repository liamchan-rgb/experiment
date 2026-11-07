#!/usr/bin/env python3
"""Tailor the existing upper-arm garment material onto its registered bone.
No hand, arm, pauldron, lower garment, weapon or animation changes.
"""
from pathlib import Path
import json,math,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Parts/P1-Battle/armor-fit-r2';D.mkdir(parents=True,exist_ok=True)
S=np.array([117.,141.]);E=np.array([128.,158.]);axis=(E-S)/np.linalg.norm(E-S);normal=np.array([-axis[1],axis[0]]);yy,xx=np.mgrid[:256,:256];p=np.stack([xx,yy],-1);u=(p-S)@axis;q=(p-S)@normal
records=[]
for item,prefix in [('leatherArmor','MeadowLeatherArmor'),('runeArmor','MeadowRuneArmor')]:
 slot='MeadowBattleHeroArmNearUpperWardrobe';src=Image.open(R/'Art/Parts/P1-Battle/armor-fit-r1'/item/(slot+'.png')).convert('RGBA');source=np.asarray(src);visible=source[:,:,3]>=100
 # Registered texture cross sections, measured once on the actual old garment.
 # Center them on the same S/E axis as skin; do not fit to an assembled frame.
 sections=np.arange(4.,22.01,.5);centers=[];halves=[]
 for value in sections:
  ids=visible&(abs(u-value)<1.2);vals=q[ids]
  if len(vals):lo,hi=np.percentile(vals,[5,95]);centers.append((lo+hi)/2);halves.append(max(2.,(hi-lo)/2))
  else:centers.append(centers[-1] if centers else 0);halves.append(halves[-1] if halves else 5)
 length=15.5 if item=='leatherArmor' else 20.7
 radius=(6.5-1.2*np.clip(u/length,0,1)) if item=='leatherArmor' else (6.0-1.2*np.clip(u/length,0,1))
 mask=(u>=-1)&(u<=length)&(abs(q)<=radius)
 textureU=np.clip(4+np.clip(u/length,0,1)*(8.0 if item=='leatherArmor' else 16.4),4,21.5)
 center=np.interp(textureU,sections,centers);half=np.interp(textureU,sections,halves)
 textureQ=center+q/radius*half
 uv=S+textureU[:,:,None]*axis+textureQ[:,:,None]*normal
 sx=np.clip(np.rint(uv[:,:,0]),0,255).astype(int);sy=np.clip(np.rint(uv[:,:,1]),0,255).astype(int)
 # Fill only internal source sampling holes; the final sleeve silhouette comes
 # from the actual skin-aligned cylinder, so no old hanging blue tail survives.
 materialVisible=visible & (source[:,:,2]<source[:,:,0]*.65) if item=='leatherArmor' else visible
 _,nearest=distance_transform_edt(~materialVisible,return_indices=True);out=np.zeros_like(source);out[mask,:3]=source[nearest[0,sy,sx],nearest[1,sy,sx],:3][mask];out[mask,3]=255
 edge=mask&(abs(q)>radius-1)
 out[edge]=(67,36,20,255) if item=='leatherArmor' else (30,39,49,255)
 if item=='leatherArmor':
  # A closed cream short-sleeve cuff, perpendicular to the upper arm.
  cuff=mask&(u>length-2.4);out[cuff]=(231,214,179,255);out[cuff&(q<-1)]=(255,244,216,255);out[cuff&(q>1.8)]=(177,149,117,255);out[mask&(u>length-1)]=(81,47,28,255)
 else:
  # Retain the navy undersleeve only inside the arm, with a quiet elbow edge.
  seam=mask&(u>length-1);out[seam]=(15,30,48,255)
 image=Image.fromarray(out);folder=D/item;folder.mkdir(exist_ok=True);image.save(folder/(slot+'.png'));name=prefix+'ArmNearUpperWardrobe';image.save(A/(name+'.imageset')/(name+'.png'))
 records.append({'item':item,'source':'armor-fit-r1/'+item+'/'+slot+'.png','replacement':name,'sameShoulder':[117,141],'sameElbow':[128,158],'sleeveEndAlongUpperArm':length,'crossSectionAxisMatchesSkin':True,'onlyUpperGarmentPixelsChanged':True})
(D/'manifest.json').write_text(json.dumps({'repairs':records,'originalHandsHeadBodyWeaponMotionHemAndPauldronUnchanged':True,'userApproval':None},indent=2)+'\n');print('Two upper sleeves retargeted to existing skin axis.')
