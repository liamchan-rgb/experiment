#!/usr/bin/env python3
"""Bake one imagegen relighting reference onto approved mirrored source surfaces.
Only tool-generated colours are transferred. Original source alpha, positions,
outline pixels, and approved baked geometry remain owned by the approved rig.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def side(name):
 if name.endswith('.left'):return name[:-5]+'.right'
 if name.endswith('.right'):return name[:-6]+'.left'
 return name

def author(folder):
 cfg=json.loads((folder/'mirror-authoring.json').read_text());left=R/cfg['sourceTemplate'];lc=json.loads((left/'authoring.json').read_text());registration=json.loads((folder/'source/relight-registration.json').read_text());rawpath=folder/'source'/registration['image'];assert sha(rawpath)==registration['inputSHA256'];scale=registration['scale'];tx,ty=registration['translation'];Image.open(rawpath).convert('RGBA').transform((256,256),Image.Transform.AFFINE,(1/scale,0,-tx/scale,0,1/scale,-ty/scale),Image.Resampling.NEAREST).save(folder/'source/relight-registered.png');ref=np.array(Image.open(folder/'source/relight-registered.png').convert('RGBA'));r,g,b,a=[ref[:,:,i].astype(float) for i in range(4)];yy,xx=np.mgrid[:256,:256]
 masks={'skin':(a>=128)&(r>g+6)&(g>b+4)&(r>90),'white':(a>=128)&(b>=r*.86)&(b>=g*.92)&(np.maximum.reduce([r,g,b])>=110),'gray':(a>=128)&(b>=r*.82)&(b>=g*.88)&(np.maximum.reduce([r,g,b])>25)&(np.maximum.reduce([r,g,b])<160)&(yy>=155)}
 nearest={k:distance_transform_edt(~v,return_indices=True) for k,v in masks.items()};idle=np.array(Image.open(left/'frames/00.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT));out=folder/'source/relit-textures';out.mkdir(exist_ok=True);record=[]
 sources={k:v['image'] for k,v in lc['parts'].items() if not k.startswith('junction')};sources['head.base']=lc['headSource']['image']
 for oldname,path in sources.items():
  name=side(oldname);image=Image.open(left/path).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);src=np.array(image);cr,cg,cb,ca=[src[:,:,i].astype(float) for i in range(4)];visible=(ca>=128)&np.all(src==idle,axis=2)
  pureSkin=oldname.startswith(('arm.','hand.','leg.','head.'));skin=np.ones((256,256),bool) if pureSkin else ((cr>cg+8)&(cr>cb+8));outline=(np.maximum.reduce([cr,cg,cb])<45)|(skin&(cr<95));valid=visible&~outline
  kind=np.full((256,256),'gray',dtype='<U5')
  if oldname=='shirt':kind[yy<162]='white'
  kind[(np.maximum.reduce([cr,cg,cb])>=155)&~skin]='white';kind[skin]='skin';paint=src.copy();counts={};maximum=0.0
  for material in ['skin','white','gray']:
   take=valid&(kind==material);distance,indices=nearest[material];ys,xs=np.where(take);paint[ys,xs,:3]=ref[indices[0,ys,xs],indices[1,ys,xs],:3];counts[material]=len(ys)
   if len(ys):maximum=max(maximum,float(distance[ys,xs].max()))
  assert np.array_equal(paint[:,:,3],src[:,:,3]);p=out/(name+'.png');Image.fromarray(paint).save(p);record.append({'texture':name,'file':str(p.relative_to(folder)),'sha256':sha(p),'visibleSourcePixels':int(visible.sum()),'keptOriginalOutlinePixels':int((visible&outline).sum()),'toolColourSamplesByMaterial':counts,'maxReferenceSampleDistancePixels':maximum,'alphaDifferencePixels':0})
 # One shared body texture uses the exact same layer order as the approved base.
 body=Image.open(out/'pants.png').convert('RGBA');body.alpha_composite(Image.open(out/'shirt.png').convert('RGBA'));body.save(out/'body.torso.png')
 localSize=cfg['headLocalCanvas'];origin=[255-lc['headLocalOrigin'][0]-(localSize[0]-1),lc['headLocalOrigin'][1]];Image.open(out/'head.base.png').crop((origin[0],origin[1],origin[0]+localSize[0],origin[1]+localSize[1])).save(out/'head-local.png');cfg['headLocalOriginMirrored']=origin;cfg['headLocalTexture']='source/relit-textures/head-local.png'
 data={'status':'single-reference-tool-colour-bake-review-pending','sourceReference':'source/relight-generated.png','registration':'source/relight-registration.json','uvMaps':'source/approved-left-uv','shapeOwner':'approved up-left r5 reflected','scope':'visible source pixels only; hidden skin/outline retained; no per-frame image generation or silhouette changes','textures':record};(folder/'source/lighting-bake.json').write_text(json.dumps(data,indent=2)+'\n');cfg['lighting']={'mode':'static-source-uv-colours','textures':'source/relit-textures','uv':'source/approved-left-uv','bakeRecord':'source/lighting-bake.json','reference':'source/relight-generated.png','alphaOwner':'approved reflection'};cfg['status']='main-only-mirror-lighting-candidate';(folder/'mirror-authoring.json').write_text(json.dumps(cfg,indent=2)+'\n');print('Mirrored source lighting authored')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);author(p.parse_args().folder)
