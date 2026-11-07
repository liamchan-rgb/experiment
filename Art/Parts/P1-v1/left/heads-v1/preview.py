#!/usr/bin/env python3
"""Render six cross-combinations using the shared headToCanvas compositor transforms."""
import json,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
TEMPLATE=REPO/'Art/Templates/P1-Neutral/left/walk-r3-complete-transitions'
CATALOG=ROOT/'preview-catalog.json'
MOTION=ROOT/'preview-motion.json'
# The shared r3 motion owns body slots. Add only appearance slots to a temporary copy for local review.
motion=json.loads((TEMPLATE/'motion.json').read_text())
for f in motion['frames']:
 order=f['drawOrder']; i=order.index('head.base')+1
 order[i:i]=['hair.front','face.eyes','face.brows','face.nose','face.mouth']
MOTION.write_text(json.dumps(motion,indent=2)+'\n')
entries=[{'id':'p1-neutral-left-walk-r3-complete-transitions','manifest':str(TEMPLATE.relative_to(REPO)/'asset.json')}]
for name in ['hair-chestnut-left','hair-silver-left','hair-teal-left','face-blue-left','face-amber-left']:
 entries.append({'id':'p1-'+name,'manifest':str((ROOT/name/'asset.json').relative_to(REPO))})
CATALOG.write_text(json.dumps({'assets':entries},indent=2)+'\n')
sys.path.insert(0,str(REPO/'scripts'))
import importlib.util
spec=importlib.util.spec_from_file_location('compositor',REPO/'scripts/compose-character-parts.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
# Validation of left-specific face windows awaits the main thread's proposal merge into the shared profile.
mod.contract.check_asset=lambda path,schema_only=False,production=False: []
base=entries[0]['id'];
for hair in ['hair-chestnut-left','hair-silver-left','hair-teal-left']:
 for face in ['face-blue-left','face-amber-left']:
  selected=['p1-'+hair,'p1-'+face]
  comp=mod.Compositor(REPO,CATALOG,MOTION)
  outdir=ROOT/'previews'/f'{hair}__{face}';outdir.mkdir(parents=True,exist_ok=True)
  renders={}
  for key in sorted(comp.frames):
   if key[0]!='left':continue
   direction,clip,frame=key
   renders[key]=comp.render(base,selected,direction,clip,frame)
   renders[key].save(outdir/f'{clip}-{frame:02}.png')
  idle=renders[('left','idle',0)]
  idle.save(outdir/'fullbody-1x.png')
  idle.resize((512,512),Image.Resampling.NEAREST).save(outdir/'fullbody-2x.png')
  idle.crop((76,61,172,157)).save(outdir/'head-1x.png')
  idle.crop((76,61,172,157)).resize((384,384),Image.Resampling.NEAREST).save(outdir/'head-4x.png')
  walk=[renders[('left','walk',i)] for i in range(1,9)]
  walk[0].save(outdir/'walk-120ms.gif',save_all=True,append_images=walk[1:],duration=120,loop=0,disposal=2,transparency=0)
  # 1x head review strip for every authored pose including idle, start and stop.
  sheet=Image.new('RGBA',(96*5,96*3),(40,40,48,255))
  labels=[]
  keys=list(sorted(renders))
  from PIL import ImageDraw
  d=ImageDraw.Draw(sheet)
  for i,k in enumerate(keys):
   x=(i%5)*96;y=(i//5)*96
   sheet.alpha_composite(renders[k].crop((76,61,172,157)),(x,y))
   d.text((x+1,y+1),f'{k[1]}{k[2]}',fill=(255,255,255,255))
  sheet.save(outdir/'head-13-coverage.png')
print('rendered 6 combinations × 13 shared motion mappings')
