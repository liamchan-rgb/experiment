#!/usr/bin/env python3
"""Transfer tool-painted fixed-light colours to reflected original source mattes.
No alpha/geometry/face ownership is transferred from generated references.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/down-right/appearance-v1';D=R/'Art/Review/P1/modular-down-right-appearance-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cfg=json.loads((P/'authoring.json').read_text());rel=cfg['relight'];refs={};masks={};yy,xx=np.mgrid[:256,:256];record=[]
 for n,s in rel['sources'].items():
  raw=Image.open(P/s['image']).convert('RGBA');assert list(raw.size)==s['canvas'] and sha(P/s['image'])==s['sha256'];scale=s['scale'];tx,ty=s['translation'];im=raw.transform((256,256),Image.Transform.AFFINE,(1/scale,0,-tx/scale,0,1/scale,-ty/scale),Image.Resampling.NEAREST);im.save(P/'source'/(n+'-relight-registered.png'));a=np.array(im);refs[n]=a;r,g,b,alpha=[a[:,:,i].astype(float) for i in range(4)];opaque=alpha>=128
  masks[n]={
   'hair':opaque&(yy<128)&((r>g+8)&(g>b+5) if n=='forester' else (np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b])<65)&(b>r*.7)),
   'cloth':opaque&(yy>=128)&(yy<=177)&((g>r*1.05)&(g>b*1.05) if n=='forester' else (b>r*1.15)&(b>g*1.02)),
   'gold':opaque&(yy>=128)&(yy<=177)&(r>g+8)&(g>b+30)&(r>120),
   'belt':opaque&(yy>=148)&(yy<=161)&(r>g*1.2)&(g>b*1.15)&(r<170),
   'pants':opaque&(yy>=157)&(yy<=204)&(np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b])<35)&(np.maximum.reduce([r,g,b])<150),
   'boots':opaque&(yy>=188)&(r>g*1.12)&(g>b*1.1)}
  for material,m in masks[n].items():assert m.any(),(n,material,'empty material reference')
 for name in ['hair-chestnut','hair-silver','forester','wayfarer','lower']:
  n='wayfarer' if name in ['hair-silver','wayfarer'] else 'forester';ref=refs[n];near={k:distance_transform_edt(~v,return_indices=True) for k,v in masks[n].items()};folder=P/name/'source';out=P/rel['textureRoot']/name;out.mkdir(parents=True,exist_ok=True)
  for path in sorted(folder.glob('*-mirrored.png')):
   a=np.array(Image.open(path).convert('RGBA'));hair=name.startswith('hair');origin=cfg['headLocalOrigin'] if hair else [0,0];y,x=np.mgrid[:a.shape[0],:a.shape[1]];Y=y+origin[1];X=x+origin[0];r,g,b,alpha=[a[:,:,i].astype(float) for i in range(4)];valid=(alpha>=128)&(np.maximum.reduce([r,g,b])>rel['outlineMaxRGB']);kind=np.full(alpha.shape,'hair' if hair else 'pants' if name=='lower' and '.pants.' in path.name else 'boots' if name=='lower' else 'cloth',dtype='<U5')
   if name in ['forester','wayfarer']:
    gold=(r>g+8)&(g>b+30)&(r>120);belt=(Y>=148)&(Y<=161)&(r>g*1.2)&(g>b*1.15)&(r<170)&~gold;kind[gold]='gold';kind[belt]='belt'
   painted=a.copy();counts={};maxDist=0
   for material in ['hair','cloth','gold','belt','pants','boots']:
    dist,idx=near[material];take=valid&(kind==material)&(dist[Y,X]<=rel['maxReferenceDistancePixels']);ys,xs=np.where(take);sy,sx=Y[ys,xs],X[ys,xs];painted[ys,xs,:3]=ref[idx[0,sy,sx],idx[1,sy,sx],:3];counts[material]=len(ys)
    if len(ys):maxDist=max(maxDist,float(dist[sy,sx].max()))
   assert np.array_equal(a[:,:,3],painted[:,:,3]);dst=out/path.name.replace('-mirrored','');Image.fromarray(painted).save(dst);record.append({'package':name,'slot':dst.stem,'alphaDifferencePixels':0,'rgbChangedPixels':int(np.any(a[:,:,:3]!=painted[:,:,:3],axis=2).sum()),'samplesByMaterial':counts,'maxReferenceDistance':maxDist,'outlinePixelsKept':int(((alpha>0)&~valid).sum()),'unmatchedOrHiddenSourceColoursRetained':True,'sha256':sha(dst)})
 cfg['relightEnabled']=True;(P/'authoring.json').write_text(json.dumps(cfg,indent=2)+'\n');(D/'lighting-bake.json').write_text(json.dumps({'status':'tool-colour-source-bake','authorAndReviewer':'root','subagentsUsed':False,'alphaOwner':'original reflected source mattes','sourceLight':'upper-left','noPerFrameRelight':True,'faceFeaturesNotRepainted':True,'records':record},indent=2)+'\n');print('Baked fixed-light source RGB:',len(record),'slots')
if __name__=='__main__':main()
