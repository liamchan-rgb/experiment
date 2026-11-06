#!/usr/bin/env python3
"""P1 silver hair colour fix (applied 2026-11-06): the four diagonals were darker and tinted (blue-grey in
front diagonals, red-brown in back diagonals). Rank-match their brightness to the front/back/side palette
of the same style, keeping the light/shade structure. Chestnut is consistent and unchanged.
Run: python3 -I scripts/fix-p1-silver-hair-diagonals.py --write
"""
import numpy as np
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True
R=Path('/home/user/experiment')
def files(pkg,d):
    P=R/f'Art/Parts/P1-v1/eight-way-v1/{pkg}'; a=json.load(open(P/'asset.json'))
    return sorted({P/b['layers'][s] for b in a['bindings'] if b['direction']==d for s in b['layers']})
def lum(px): return px[:,:3].astype(float)@[.2126,.7152,.0722]
def fix(pkg, targets, refs, write):
    ref=np.concatenate([np.array(Image.open(f).convert('RGBA')).reshape(-1,4) for d in refs for f in files(pkg,d)])
    ref=ref[ref[:,3]>0]; ref=ref[np.argsort(lum(ref))][:,:3].astype(float)
    n=0
    for d in targets:
        fs=files(pkg,d); arrs=[np.array(Image.open(f).convert('RGBA')) for f in fs]
        pool=np.concatenate([a.reshape(-1,4) for a in arrs]); pool=pool[pool[:,3]>0]; Ls=np.sort(lum(pool))
        for f,a in zip(fs,arrs):
            flat=a.reshape(-1,4).copy(); m=flat[:,3]>0
            rank=np.searchsorted(Ls,lum(flat[m]))/max(1,len(Ls)-1)
            flat[m,:3]=ref[np.clip((rank*(len(ref)-1)).round().astype(int),0,len(ref)-1)].round().clip(0,255).astype(np.uint8)
            if write: Image.fromarray(flat.reshape(a.shape)).save(f)
            n+=1
    return n
if __name__=='__main__':
    print(fix('hair-silver',['down-left','down-right','up-left','up-right'],['down','left','right','up'],'--write' in sys.argv),'files')
