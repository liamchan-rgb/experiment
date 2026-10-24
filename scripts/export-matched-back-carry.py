#!/usr/bin/env python3
"""Register a right-view sword carry outside the shoulder swing envelope."""
from pathlib import Path
import importlib.util,json,math,hashlib
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/upper/back-carry-v6';T=R/'Art/Templates/P1-Wardrobe/upper/v6-matched-back-carry';D=R/'Art/Review/P1/modular-upper-wardrobe-v6'
s=importlib.util.spec_from_file_location('w',R/'scripts/export-upper-wardrobe.py');w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
def main():
 cfg=json.loads((P/'authoring.json').read_text());catalog=json.loads((R/'Art/Templates/P1-Wardrobe/upper/v4-nape-gradient/catalog.json').read_text());oldP=R/'Art/Parts/P1-v1/upper/wardrobe-v1/back-scabbard';asset=json.loads((oldP/'asset.json').read_text());bindings=[];audit=json.loads((R/'Art/Review/P1/neutral-upper-transitions-r6/up-left/rig-audit.json').read_text());F=np.array([[-1,0,255],[0,1,0],[0,0,1.]])
 for direction in ['up-left','up-right']:
  motion=json.loads((R/f'Art/Templates/P1-Wardrobe/upper/v4-nape-gradient/{direction}-motion.json').read_text());source=Image.open(oldP/'source'/(direction+'-weapon.back.png')).convert('RGBA');source.save(P/'source'/(direction+'-original.png'))
  for i,f in enumerate(motion['frames']):
   im=Image.open(oldP/'png/up-left'/f'{i:02}'/'weapon.back.png').convert('RGBA')
   if direction=='up-right':im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   out=P/'png'/direction/f'{i:02}';out.mkdir(parents=True,exist_ok=True);im.save(out/'weapon.back.png');bindings.append({'direction':direction,'clip':f['clip'],'frame':f['frame'],'layers':{'weapon.back':str((out/'weapon.back.png').relative_to(P))}});(P/'editable').mkdir(exist_ok=True);w.edit.editable(P/'editable',direction+f'-{i:02}',{'weapon.back':im})
  motion['status']='matched-back-carry-v6-candidate';(T/(direction+'-motion.json')).write_text(json.dumps(motion,indent=2)+'\n')
 asset.update(id='p1-upper-back-carry-v6',version='6.0.0',bindings=bindings,sourceFiles=['authoring.json']+[str(p.relative_to(P)) for sub in ['source','editable'] for p in sorted((P/sub).rglob('*')) if p.is_file()]);(P/'asset.json').write_text(json.dumps(asset,indent=2)+'\n')
 for e in catalog['assets']:
  if e['id']=='p1-upper-back-scabbard-v1':e.update(id=asset['id'],manifest=str((P/'asset.json').relative_to(R)))
 (T/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
 for direction in ['up-left','up-right']:
  C=w.compose.Compositor(R,T/'catalog.json',T/(direction+'-motion.json'));base='p1-neutral-'+direction+'-r8-nape-gradient'
  for outfit,hair in [('forester','hair-chestnut'),('wayfarer','hair-silver')]:
   out=D/direction/outfit;out.mkdir(parents=True,exist_ok=True);frames=[]
   for i,f in enumerate(C.motion['frames']):
    im=C.render(base,['p1-upper-'+outfit+'-v1','p1-upper-lower-v2','p1-upper-'+hair+'-v1',asset['id']],direction,f['clip'],f['frame']);im.save(out/f'{i:02}.png');frames.append(im)
   w.preview.gif(frames[1:9],out/'walk-120ms.gif');seq=[0,9,10]+list(range(1,9))*2+[11,12,0];w.preview.gif([frames[i] for i in seq],out/'start-stop-120ms.gif',[480]+[120]*20+[480]);w.preview.flatten(frames[0],2).save(out/'idle-2x.png')
 print('Exported v6 matched carry; original left unchanged, right exactly reflects the complete left pose')
if __name__=='__main__':main()
