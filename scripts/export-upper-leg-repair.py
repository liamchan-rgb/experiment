#!/usr/bin/env python3
"""Register new ankle-boot garments to the accepted leg coordinates, without reshaping the body."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,distance_transform_edt
R=Path(__file__).resolve().parents[1]
P=R/'Art/Parts/P1-v1/upper/lower-v2';T=R/'Art/Templates/P1-Wardrobe/upper/v2-leg-repair';D=R/'Art/Review/P1/modular-upper-wardrobe-v2';OLD=R/'Art/Parts/P1-v1/upper/wardrobe-v1'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=module('wardrobe',R/'scripts/export-upper-wardrobe.py');compose=old.compose;edit=old.edit;preview=old.preview

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cfg=json.loads((P/'authoring.json').read_text());raw=Image.open(P/cfg['rawSource']).convert('RGBA');assert raw.width==raw.height
 size=cfg.get('sheetSize',512);sheet=raw.resize((size,size),Image.Resampling.NEAREST);sheet.save(P/'source/registered.png')
 (P/'source/registration.json').write_text(json.dumps({'rawSize':list(raw.size),'registeredSize':[size,size],'method':'uniform full-canvas resize and fixed tile/paint translations; final anatomical matte unchanged','paintOffsets':cfg['paintOffsets'],'anatomicalFits':False,'alphaBoundsFit':False,'sourceSHA256':sha(P/cfg['rawSource'])},indent=2)+'\n')
 slots=['outfit.pants.left','outfit.pants.right','outfit.boot.left','outfit.boot.right'];bindings=[];T.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True)
 for folder in ['source','png','editable']:(P/folder).mkdir(exist_ok=True)
 common={'sourceUV':'source/common-left-uv'}
 for di,direction in enumerate(['up-left','up-right']):
  B=R/f'Art/Templates/P1-Neutral/{direction}/walk-r6-transitions';motion=json.loads((R/f'Art/Templates/P1-Wardrobe/upper/v1-independent/{direction}-motion.json').read_text());sources={}
  for side in ['left','right']:
   col=0 if side=='left' else 1;tile=size//2;piece=sheet.crop((col*tile,di*tile,(col+1)*tile,(di+1)*tile));im=Image.new('RGBA',(256,256));origin=cfg.get('tileOrigin',[0,0]);offset=cfg.get('paintOffsets',{}).get(direction,{}).get(side,[0,0]);im.alpha_composite(piece,(origin[0]+offset[0],origin[1]+offset[1]))
   ar=np.array(im)
   if cfg.get('anatomicalMatte'):
    srcside=side if di==0 else ('right' if side=='left' else 'left')
    anatomy=Image.open(R/f'Art/Templates/P1-Neutral/up-left/walk-r6-transitions/source/leg.{srcside}.png').convert('RGBA')
    if di:anatomy=anatomy.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    matte=binary_dilation(np.array(anatomy)[:,:,3]>12,iterations=cfg['matteAllowancePixels'])
    pelvis=Image.open(R/'Art/Templates/P1-Neutral/up-left/walk-r6-transitions/source/pants.png').convert('RGBA')
    pelvisMask=binary_dilation(np.array(pelvis)[:,:,3]>12,iterations=1);yy,xx=np.mgrid[:256,:256];pelvisMask&=(yy<=cfg['pelvisRootLastY'])&((xx<=129) if srcside=='left' else (xx>=130))
    if di:pelvisMask=pelvisMask[:,::-1].copy()
    matte|=pelvisMask
    # Cut artist-painted bleed to the unchanged anatomical silhouette plus cloth thickness.
    missing=matte&(ar[:,:,3]<128)
    # Standard texture gutter clamp: keep artist RGB, never sample transparency into the cut matte.
    distance,nearest=distance_transform_edt(ar[:,:,3]<128,return_indices=True)
    assert float(distance[missing].max(initial=0))<=cfg['maxTextureGutterPixels'],(direction,side,'Texture registration drift exceeds gutter limit')
    ar[missing,:3]=ar[nearest[0][missing],nearest[1][missing],:3]
    ar[~matte]=0;ar[:,:,3][matte]=255
   else:
    ar[ar[:,:,3]<128]=0;ar[:,:,3][ar[:,:,3]>=128]=255
   im=Image.fromarray(ar)
   for garment in ['pants','boot']:
    a=np.array(im);yy,xx=np.mgrid[:256,:256];boundary=cfg['bootTopY'][direction][side];valid=yy<=boundary if garment=='pants' else yy>=boundary
    a[~valid]=0;source=Image.fromarray(a);slot=f'outfit.{garment}.{side}';source.save(P/'source'/(direction+'-'+slot+'.png'));sources[slot]=source
  for idx,f in enumerate(motion['frames']):
   out=P/'png'/direction/f'{idx:02}';out.mkdir(parents=True,exist_ok=True);layers={};paths={}
   for slot in slots:
    side=slot.rsplit('.',1)[1];source='leg.'+side
    im=old.uv_sample(sources[slot],source,idx,direction,common)
    # Retain original hand precedence exactly as the existing outfit package.
    neutral=json.loads((B/'motion.json').read_text())['frames'][idx];handmask=np.zeros((256,256),bool);trans=np.ones((256,256))
    for s in neutral['drawOrder'][::-1]:
     a=np.array(Image.open(B/'layers'/f'{idx:02}'/(s+'.png')))[:,:,3]/255
     if s.startswith('body.hand.'):handmask|=(a>0)&(trans>.99)
     trans*=1-a
    a=np.array(im);a[handmask]=0;im=Image.fromarray(a);path=out/(slot+'.png');im.save(path);layers[slot]=im;paths[slot]=str(path.relative_to(P))
   bindings.append({'direction':direction,'clip':f['clip'],'frame':f['frame'],'layers':paths});edit.editable(P/'editable',direction+f'-{idx:02}',layers)
  motion['status']='upper-wardrobe-leg-repair-v2-candidate';(T/(direction+'-motion.json')).write_text(json.dumps(motion,indent=2)+'\n')
 asset={'schemaVersion':'1.0.0','id':'p1-upper-lower-v2','version':'2.0.0','part':'outfit','compatibility':motion['compatibility'],'mode':'pose-map','slots':slots,'directions':['up-left','up-right'],'clips':['idle','walk','walk-start','walk-stop'],'bindings':bindings,'sourceFiles':['authoring.json']+[str(p.relative_to(P)) for sub in ['source','editable'] for p in sorted((P/sub).rglob('*')) if p.is_file()]};(P/'asset.json').write_text(json.dumps(asset,indent=2)+'\n')
 catalog=json.loads((R/'Art/Templates/P1-Wardrobe/upper/v1-independent/catalog.json').read_text())
 for e in catalog['assets']:
  if e['id']=='p1-upper-lower-v1':e.update(id=asset['id'],manifest=str((P/'asset.json').relative_to(R)))
 (T/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
 for direction in ['up-left','up-right']:
  c=compose.Compositor(R,T/'catalog.json',T/(direction+'-motion.json'));motion=c.motion;base='p1-neutral-'+direction+'-r6-transitions'
  for outfit,hair in [('forester','hair-chestnut'),('wayfarer','hair-silver')]:
   out=D/direction/outfit;out.mkdir(parents=True,exist_ok=True);frames=[]
   for idx,f in enumerate(motion['frames']):
    im=c.render(base,['p1-upper-'+outfit+'-v1','p1-upper-lower-v2','p1-upper-'+hair+'-v1','p1-upper-back-scabbard-v1'],direction,f['clip'],f['frame']);im.save(out/f'{idx:02}.png');frames.append(im)
   preview.gif(frames[1:9],out/'walk-120ms.gif');seq=[0,9,10]+list(range(1,9))*2+[11,12,0];preview.gif([frames[i] for i in seq],out/'start-stop-120ms.gif',[480]+[120]*20+[480]);preview.flatten(frames[0],2).save(out/'idle-2x.png')
 print('Exported independently repainted lower-v2; original body, motion and five upper appearance packs unchanged')
if __name__=='__main__':main()
