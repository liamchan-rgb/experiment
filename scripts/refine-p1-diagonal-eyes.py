#!/usr/bin/env python3
"""P1 diagonal head refinement (applied 2026-11-06, user request).

Eyes: down-left/down-right eyes were 3-5 rows tall (squinting) with a 3-4 px dark far eye. Rebuild them
from the approved front-view eyes: near eye = same-side front eye minus its outer lid and one iris column
(10 cols at x 43-52, rows 52-59); far eye = 6 picked columns (outer lid, white, highlight, iris, inner lid)
at x 34-39, rows 51-58; 3 px gap. down-right is the exact mirror, as before. Both eye shapes (blue, amber).
Run: python3 -I scripts/refine-p1-diagonal-eyes.py --write, then rebake-p1-map-atlases.py and build-p1-head-split.py.
"""
import numpy as np
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True
R=Path('/home/user/experiment')
def pkg(name): return R/f'Art/Parts/P1-v1/eight-way-v1/{name}'
def paths(name,d,slot):
    a=json.load(open(pkg(name)/'asset.json')); return sorted({pkg(name)/b['layers'][slot] for b in a['bindings'] if b['direction']==d})
def load(name,d,slot): return np.array(Image.open(paths(name,d,slot)[0]).convert('RGBA'))
# column picks from the front-view eyes (front coords), rows 52..59
NEAR_COLS={'face-blue':[54,55,56,57,58,59,61,62,63,64],'face-amber':[54,55,56,57,58,59,61,62,63,64]}
FAR_COLS ={'face-blue':[32,35,37,38,39,41],'face-amber':[32,35,37,38,39,41]}
def build(name):
    front=load(name,'down','face.eyes'); out=np.zeros_like(front)
    rows=range(52,60)
    for i,x in enumerate(NEAR_COLS[name]):
        for y in rows: out[y,43+i]=front[y,x]
    for i,x in enumerate(FAR_COLS[name]):
        for y in rows: out[y-1,34+i]=front[y,x]
    return out
def write(name,dry):
    dl=build(name); dr=dl[:,::-1].copy()
    res={}
    for d,img in [('down-left',dl),('down-right',dr)]:
        for p in paths(name,d,'face.eyes'):
            res[p]=img
            if not dry: Image.fromarray(img).save(p)
    return res
if __name__=='__main__':
    dry='--write' not in sys.argv
    for n in ['face-blue','face-amber']: r=write(n,dry); print(n,len(r),'files', 'dry' if dry else 'written')
