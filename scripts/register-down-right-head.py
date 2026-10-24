#!/usr/bin/env python3
"""Register subpixel nearest-neighbour raster phase of reflected head sockets.
Pillow's affine rasterizer quantizes coefficients. The mathematical reflection
can otherwise select the adjacent source row at a pixel boundary. Calibrate
against source UV, keeping approved pose pixels and all body joints unchanged.
"""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/down-right/walk-r1-mirrored-down-left'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('mirror',R/'scripts/export-down-right-mirrored-motion.py');c=module('compose',R/'scripts/compose-character-parts.py');cfg=json.loads((P/'mirror-authoring.json').read_text());L=R/cfg['sourceTemplate'];frames=json.loads((L/'motion.json').read_text())['frames'];F=np.array([[-1,0,255],[0,1,0],[0,0,1.]]);G=np.array([[-1,0,95],[0,1,0],[0,0,1.]]);ox,oy=cfg['headLocalOriginMirrored'];yy,xx=np.mgrid[:96,:96];uv=np.zeros((96,96,4),np.uint8);uv[:,:,0]=xx+ox;uv[:,:,1]=yy+oy;uv[:,:,3]=np.array(Image.open(P/cfg['headLocalTexture']))[:,:,3];uv[uv[:,:,3]==0]=0;source=Image.fromarray(uv);records=[]
for i,f in enumerate(frames):
 target=np.array(Image.open(P/cfg['lighting']['uv']/f'{i:02}'/'head.base.png'))[:,::-1].copy();valid=target[:,:,3]>0;target[valid,0]=255-target[valid,0];target[~valid]=0;mat=F@m.mat(f['headToCanvas'])@G
 candidates=[(0.,0.)]+[(0.,float(v)) for v in sorted([v*.0005 for v in range(-16,17) if v],key=abs)]
 found=None
 for dx,dy in candidates:
  trial=mat.copy();trial[:2,2]+=[dx,dy];actual=np.array(c.place(source,m.affine(trial),(256,256)));actual[actual[:,:,3]==0]=0
  if np.array_equal(actual,target):found=[dx,dy];break
 assert found is not None,('head UV registration needs investigation',i)
 records.append({'pose':i,'translationPixels':found,'sourceUVReflectionDifferencePixels':0})
cfg['headRasterRegistration']={'method':'Source-UV phase calibration for Pillow affine coefficient quantization; fixed offline metadata, no pixel painting or runtime correction','maximumAllowedTranslationPixels':.01,'poses':records};(P/'mirror-authoring.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');print('Head UV registration:',[r for r in records if r['translationPixels']!=[0,0]])
