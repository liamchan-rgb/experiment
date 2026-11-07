#!/usr/bin/env python3
"""P1 skin-tone fix (applied 2026-11-06): the four diagonals and the back view used an orange skin
ramp (#fdbf70) while front/left/right used peach (#fbcb9b). Rank-match skin pixels of head.base,
hands and arms in those five directions to the approved front/left/right ramp; outlines, eyes and
clothes are untouched. Then run rebake-p1-map-atlases.py and build-p1-head-split.py.
Usage: python3 -I scripts/fix-p1-skin-tone.py --write
"""
import json, sys
import numpy as np
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True
R=Path('/home/user/experiment'); P=R/'Art/Parts/P1-v1/eight-way-v1/base'
A=json.loads((P/'asset.json').read_text())
FIX=['down-right','down-left','up','up-left','up-right']
REF=['down','left','right']
SKIN_SLOTS=['head.base','body.hand.right','body.hand.left','body.arm.right','body.arm.left']
def hsv(px):
    px=px/255.0; mx=px.max(1); mn=px.min(1); d=np.maximum(mx-mn,1e-6)
    r,g,b=px[:,0],px[:,1],px[:,2]
    h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60
    s=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0); return h,s,mx
def skin_mask(px):
    h,s,v=hsv(px[:,:3].astype(float)); return (px[:,3]>0)&(h>=8)&(h<=48)&(s>0.12)&(v>0.55)
def lum(px): return px[:,:3].astype(float)@[.2126,.7152,.0722]
def files(direction):
    out=set()
    for b in A['bindings']:
        if b['direction']==direction:
            for slot in SKIN_SLOTS:
                if slot in b['layers']: out.add(P/b['layers'][slot])
    return sorted(out)
def reference():
    px=[]
    for d in REF:
        for f in files(d):
            a=np.array(Image.open(f).convert('RGBA')).reshape(-1,4); px.append(a[skin_mask(a)])
    ref=np.concatenate(px); order=np.argsort(lum(ref)); return ref[order][:,:3].astype(float)
def fix_direction(d, ref):
    fs=files(d); arrays=[np.array(Image.open(f).convert('RGBA')) for f in fs]
    allpx=np.concatenate([a.reshape(-1,4)[skin_mask(a.reshape(-1,4))] for a in arrays])
    Ls=np.sort(lum(allpx))
    out={}
    for f,a in zip(fs,arrays):
        flat=a.reshape(-1,4).copy(); m=skin_mask(flat)
        if m.any():
            rank=np.searchsorted(Ls,lum(flat[m]))/max(1,len(Ls)-1)
            idx=np.clip((rank*(len(ref)-1)).round().astype(int),0,len(ref)-1)
            flat[m,:3]=ref[idx].round().clip(0,255).astype(np.uint8)
        out[f]=flat.reshape(a.shape)
    return out
if __name__=='__main__':
    ref=reference(); print('reference skin px',len(ref))
    write='--write' in sys.argv; changed=0
    for d in FIX:
        res=fix_direction(d,ref)
        for f,a in res.items():
            if write:
                Image.fromarray(a).save(f); changed+=1
            else:
                (Path('preview')/f.relative_to(P)).parent.mkdir(parents=True,exist_ok=True); Image.fromarray(a).save(Path('preview')/f.relative_to(P))
    print('files', changed if write else 'preview only')
