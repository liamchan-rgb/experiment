#!/usr/bin/env python3
"""Check static apparel master files; never approves art or creates pose frames."""
import argparse,json,re
from pathlib import Path
import numpy as np
from PIL import Image
VIEWS={'front':'down','front-quarter-left':'down-left','profile-left':'left','rear-quarter-left':'up-left','back':'up','front-quarter-right':'down-right','profile-right':'right','rear-quarter-right':'up-right'}
REQUIRED=set(list(VIEWS)[:5])
SLOTS={'outfit.torso','outfit.sleeve.left','outfit.sleeve.right','outfit.hem.front'}
def check(path,partial=False):
 path=Path(path).resolve();data=json.loads(path.read_text());errors=[];files=set();seen=set();layers=0
 def file(relative):
  p=Path(relative)
  if p.is_absolute() or '..' in p.parts:raise ValueError('path must stay inside package')
  target=(path.parent/p).resolve()
  if not target.is_relative_to(path.parent) or not target.is_file():raise ValueError('missing or escaping path')
  return target
 if data.get('schemaVersion')!='1.0.0' or data.get('kind')!='p1-apparel-masters':errors.append('wrong master schemaVersion/kind; this is not runtime asset.json')
 if data.get('canvas')!=[256,256] or data.get('baseId')!='p1-eight-way-base-v1':errors.append('wrong canvas/baseId')
 if not re.fullmatch('[a-z][a-z0-9-]*',data.get('id','')):errors.append('invalid id')
 for row in data.get('views',[]):
  view=row.get('view');direction=VIEWS.get(view)
  if not direction or view in seen:errors.append(f'unknown/duplicate view: {view}')
  seen.add(view)
  if row.get('referencePose')!={'direction':direction,'clip':'idle','frame':0}:errors.append(f'{view}: wrong idle reference')
  if set(row.get('layers',{}))!=SLOTS:errors.append(f'{view}: four exact clothing slots required')
  for slot,relative in row.get('layers',{}).items():
   layers+=1
   try:
    p=file(relative);files.add(p)
    with Image.open(p) as im:
     if im.format!='PNG' or im.mode!='RGBA' or im.size!=(256,256):raise ValueError('must be 256x256 PNG/RGBA')
     a=np.asarray(im)
     if np.any(a[:,:,:3][a[:,:,3]==0]):raise ValueError('RGB must be zero where alpha=0')
     if np.any(a[0,:,3]) or np.any(a[-1,:,3]) or np.any(a[:,0,3]) or np.any(a[:,-1,3]):raise ValueError('art touches canvas edge')
     if not np.any(a[:,:,3]):
      if slot!='outfit.hem.front' or not row.get('transparentLayers',{}).get(slot):raise ValueError('empty layer without legal hem explanation')
   except (ValueError,OSError,TypeError) as e:errors.append(f'{view}/{slot}: {e}')
 if not seen or (not partial and not REQUIRED<=seen):errors.append('five default static views required; use --partial only for declared samples')
 if not data.get('sourceFiles'):errors.append('real editable/palette sourceFiles required')
 for value in data.get('sourceFiles',[]):
  try:
   if file(value).stat().st_size==0:raise ValueError('empty source file')
  except (ValueError,OSError,TypeError) as e:errors.append(f'source {value}: {e}')
 return {'id':data.get('id'),'views':len(seen),'layerReferences':layers,'uniquePNGFiles':len(files),'completeDefaultViewCoverage':REQUIRED<=seen,'fileChecksPassed':not errors,'artApproved':False,'poseFramesGenerated':False,'errors':errors}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--partial',action='store_true');a=p.parse_args()
 result=check(a.manifest,a.partial);print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['fileChecksPassed'] else 1)
