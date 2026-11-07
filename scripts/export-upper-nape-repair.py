#!/usr/bin/env python3
"""Repair the tiny head/neck overlap in source coordinates; retain exact original geometry."""
from pathlib import Path
import hashlib,importlib.util,json,shutil
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/upper/nape-v3';T=R/'Art/Templates/P1-Wardrobe/upper/v3-nape-repair';D=R/'Art/Review/P1/modular-upper-wardrobe-v3'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=module('wardrobe',R/'scripts/export-upper-wardrobe.py');compose=old.compose;edit=old.edit;preview=old.preview

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cfg=json.loads((P/'authoring.json').read_text());raw=Image.open(P/cfg['rawSource']).convert('RGBA');assert raw.width==raw.height*2
 registered=raw.resize((192,96),Image.Resampling.NEAREST);registered.save(P/'source/registered-paint.png');catalog=json.loads((R/'Art/Templates/P1-Wardrobe/upper/v2-leg-repair/catalog.json').read_text());audit=[]
 for col,direction in enumerate(['up-left','up-right']):
  B=R/f'Art/Templates/P1-Neutral/{direction}/walk-r6-transitions';F=P/('base-'+direction);F.mkdir(parents=True,exist_ok=True);(F/'source').mkdir(exist_ok=True);(F/'editable').mkdir(exist_ok=True);bm=json.loads((B/'motion.json').read_text());m=json.loads((R/f'Art/Templates/P1-Wardrobe/upper/v2-leg-repair/{direction}-motion.json').read_text());origin=bm['frames'][0]['headToCanvas'][4:];origin=list(map(int,origin));baseId='p1-neutral-'+direction+'-r7-nape';sourceLayers={s:Image.open(B/'layers/00'/(s+'.png')).convert('RGBA') for s in ['head.base','body.torso']};yy,xx=np.mgrid[:256,:256];x0,y0,x1,y1=cfg['repairROI'][direction];roi=(xx>=x0)&(xx<=x1)&(yy>=y0)&(yy<=y1)
  paint=Image.new('RGBA',(256,256));paint.alpha_composite(registered.crop((col*96,0,(col+1)*96,96)),(80,64));pa=np.array(paint);dx,dy=cfg['paintSampleOffset'][direction];sample=np.zeros_like(pa);yy0,xx0=np.mgrid[:256,:256];sx=np.clip(xx0+dx,0,255);sy=np.clip(yy0+dy,0,255);pa=pa[sy,sx];patches={};origHead=sourceLayers['head.base'];headArray=np.array(origHead)
  for slot,im in sourceLayers.items():
   a=np.array(im);dark=a[:,:,:3].max(axis=2)<cfg['darkEdgeMax'];selection=roi&(a[:,:,3]>128)&dark
   if slot=='head.base':selection&=np.array(sourceLayers['body.torso'])[:,:,3]>128
   assert selection.any(),(direction,slot,'No seam pixels selected')
   assert (pa[:,:,3][selection]>128).all(),(direction,slot,'Paint not registered to seam')
   assert ((pa[:,:,0][selection]>90)&(pa[:,:,0][selection]>pa[:,:,1][selection]*1.05)&(pa[:,:,1][selection]>pa[:,:,2][selection]*1.1)).all(),(direction,slot,'Nape patch is not warm skin')
   patch=np.zeros((256,256,4),np.uint8);patch[selection,:3]=pa[selection,:3];patch[selection,3]=255;patches[slot]=Image.fromarray(patch);patches[slot].save(F/'source'/(slot+'-patch.png'));a[selection,:3]=pa[selection,:3]
   if slot=='head.base':headArray=a
   audit.append({'direction':direction,'slot':slot,'sourcePixels':int(selection.sum()),'sourceCoordinates':np.argwhere(selection).tolist()})
  newHead=Image.fromarray(headArray).crop((origin[0],origin[1],origin[0]+96,origin[1]+96));newHead.save(F/'source/head-local.png');bindings=[]
  for idx,f in enumerate(bm['frames']):
   out=F/'png'/f'{idx:02}';out.mkdir(parents=True,exist_ok=True);layers={};paths={}
   torsoPatch=old.uv_sample(patches['body.torso'],'shirt',idx,direction,{'sourceUV':'source/common-left-uv'})
   for slot in f['drawOrder']:
    original=Image.open(B/'layers'/f'{idx:02}'/(slot+'.png')).convert('RGBA');a=np.array(original)
    if slot=='head.base':im=compose.place(newHead,f['headToCanvas'],(256,256))
    elif slot=='body.torso':
     patch=np.array(torsoPatch);selected=(patch[:,:,3]>128)&(a[:,:,3]>0);a[selected,:3]=patch[selected,:3];im=Image.fromarray(a)
    else:im=original
    assert np.array_equal(np.array(im)[:,:,3],np.array(original)[:,:,3]),(direction,idx,slot,'Geometry changed')
    path=out/(slot+'.png');im.save(path);layers[slot]=im;paths[slot]=str(path.relative_to(F))
   edit.editable(F/'editable',f'{idx:02}',layers);whole=Image.new('RGBA',(256,256))
   for im in layers.values():whole.alpha_composite(im)
   (F/'frames').mkdir(exist_ok=True);whole.save(F/'frames'/f'{idx:02}.png');bindings.append({'direction':direction,'clip':f['clip'],'frame':f['frame'],'layers':paths})
  (F/'source/provenance.json').write_text(json.dumps({'originalBase':str(B.relative_to(R)),'originalManifestSHA256':sha(B/'asset.json'),'paintSHA256':sha(P/cfg['rawSource']),'repairROI':cfg['repairROI'][direction],'paintSampleOffset':cfg['paintSampleOffset'][direction],'geometryAndAlphaUnchanged':True,'artApproval':None},indent=2)+'\n')
  asset=json.loads((B/'asset.json').read_text());asset.update(id=baseId,version='7.0.0',bindings=bindings,sourceFiles=[str(p.relative_to(F)) for sub in ['source','editable'] for p in sorted((F/sub).rglob('*')) if p.is_file()]);(F/'asset.json').write_text(json.dumps(asset,indent=2)+'\n')
  for entry in catalog['assets']:
   if entry['id']=='p1-neutral-'+direction+'-r6-transitions':entry.update(id=baseId,manifest=str((F/'asset.json').relative_to(R)))
  m.update(status='nape-seam-repair-v3-candidate',baseManifestSHA256=sha(F/'asset.json'));(T/(direction+'-motion.json')).write_text(json.dumps(m,indent=2)+'\n')
 (T/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n');(D/'source-repair.json').write_text(json.dumps({'status':'source-neck-seam-colour-repair','geometryAndAlphaUnchanged':True,'artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'sourcePaintSHA256':sha(P/cfg['rawSource']),'repairs':audit},indent=2)+'\n')
 for direction in ['up-left','up-right']:
  comp=compose.Compositor(R,T/'catalog.json',T/(direction+'-motion.json'));base='p1-neutral-'+direction+'-r7-nape'
  for outfit,hair in [('forester','hair-chestnut'),('wayfarer','hair-silver')]:
   out=D/direction/outfit;out.mkdir(parents=True,exist_ok=True);frames=[]
   for idx,f in enumerate(comp.motion['frames']):
    im=comp.render(base,['p1-upper-'+outfit+'-v1','p1-upper-lower-v2','p1-upper-'+hair+'-v1','p1-upper-back-scabbard-v1'],direction,f['clip'],f['frame']);im.save(out/f'{idx:02}.png');frames.append(im)
   preview.gif(frames[1:9],out/'walk-120ms.gif');seq=[0,9,10]+list(range(1,9))*2+[11,12,0];preview.gif([frames[i] for i in seq],out/'start-stop-120ms.gif',[480]+[120]*20+[480]);preview.flatten(frames[0],2).save(out/'idle-2x.png')
 print('Exported two isolated nape-repair bases; original body/motion geometry, wardrobe and lower-v2 retained')
if __name__=='__main__':main()
