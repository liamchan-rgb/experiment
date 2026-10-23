#!/usr/bin/env python3
"""Capture static source pixel coordinates from the existing offline mesh baker.
The approved template is copied to an isolated staging directory; never modified.
UV coordinates are metadata, not independently generated artwork.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,tempfile
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def arrayhash(im):return hashlib.sha256(np.array(im.convert('RGBA')).tobytes()).hexdigest()
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def capture(source,output):
 exp=module('coupled',R/'scripts/export-neutral-coupled-clothing.py');cfg=json.loads((source/'authoring.json').read_text());motion=json.loads((source/'motion.json').read_text());parts={arrayhash(Image.open(source/v['image'])):k for k,v in cfg['parts'].items()};sampler=exp.sampler;yy,xx=np.mgrid[:256,:256];a=np.zeros((256,256,4),np.uint8);a[:,:,0]=xx;a[:,:,1]=yy;a[:,:,3]=255;uv=Image.fromarray(a);state={'frame':-1};output.mkdir(parents=True,exist_ok=True)
 def wrap(src,dst):
  normal=sampler(src,dst);coordinates=normal(uv)
  def sample(im):
   name=parts.get(arrayhash(im))
   if name=='shirt':state['frame']+=1
   if name is not None and not name.startswith('junction'):
    p=output/f"{state['frame']:02}";p.mkdir(exist_ok=True);coordinates.save(p/(name+'.png'))
   return normal(im)
  return sample
 exp.sampler=wrap
 with tempfile.TemporaryDirectory(prefix='p1-approved-uv-') as temp:
  clone=Path(temp)/'template';review=Path(temp)/'review';shutil.copytree(source,clone);exp.export(clone,review)
  for i in range(9):assert sha(clone/'frames'/f'{i:02}.png')==sha(source/'frames'/f'{i:02}.png'),('capture changed approved pixels',i)
 assert state['frame']==8
 origin=cfg['headLocalOrigin'];base=Image.open(source/cfg['headSource']['image']).convert('RGBA');a=np.array(uv);a[:,:,3]=np.array(base)[:,:,3];headuv=Image.fromarray(a)
 for i,f in enumerate(motion['frames']):
  aa,b,c,d,x,y=f['headToCanvas'];full=np.array([[aa,c,x],[b,d,y],[0,0,1.]])@np.array([[1,0,-origin[0]],[0,1,-origin[1]],[0,0,1.]])
  exp.compose.place(headuv,exp.affine(full),(256,256)).save(output/f'{i:02}'/'head.base.png')
 (output/'capture.json').write_text(json.dumps({'sourceTemplate':str(source.relative_to(R)),'sourceManifestSHA256':sha(source/'asset.json'),'frames':9,'sourcePixelsUnchanged':True,'uvChannels':{'R':'source x pixel centre','G':'source y pixel centre','A':'valid coordinate'},'sampling':'nearest identical to approved offline exporter'},indent=2)+'\n');print('Captured approved pose UV coordinates')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();capture(a.source.resolve(),a.output.resolve())
