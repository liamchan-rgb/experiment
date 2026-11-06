#!/usr/bin/env python3
"""P1 head reshaping (applied 2026-11-06, user feedback).

- down-left/down-right jaw "turned too sharp": the chin ended in a single-pixel point (row 68) and narrowed from
  31 to 10 px in five rows. Remove the point and widen rows 63-67 (mostly on the cheek/ear side), moving the
  row's own outline and shading pixels outward, on every head.base frame of both directions.
- up-left/up-right "bald and too round": extend hair.front strands down over the bare temple (about 8 px,
  above the ear), repeating the strands above, slightly darker at the new hairline, irregular edge, outlined.
  Both hairstyles.
Then run rebake-p1-map-atlases.py and build-p1-head-split.py.
Usage: python3 -I scripts/reshape-p1-diagonal-heads.py --write
"""
import numpy as np
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True
R=Path('/home/user/experiment'); PARTS=R/'Art/Parts/P1-v1/eight-way-v1'
MOTION={(f['direction'],f['clip'],f['frame']):f for f in json.loads((R/'Art/Integration/P1-modular-eight-way-v1/motion.json').read_text())['frames']}
# Jaw: per local row, (extra px on screen-left, extra px on screen-right); None removes the row.
JAW={'down-left':{63:(1,1),64:(1,3),65:(2,3),66:(1,3),67:(1,3),68:None},
     'down-right':{63:(1,1),64:(3,1),65:(3,2),66:(3,1),67:(3,1),68:None}}
def bindings(pkg):
    a=json.loads((PARTS/pkg/'asset.json').read_text()); return a['bindings']
def round_jaw(write):
    out={}
    for b in bindings('base'):
        d=b['direction']
        if d not in JAW: continue
        p=PARTS/'base'/b['layers']['head.base']
        if p in out: continue
        f=MOTION[(d,b['clip'],b['frame'])]; tx,ty=f['headToCanvas'][4],f['headToCanvas'][5]
        a=np.array(Image.open(p).convert('RGBA')); n=a.copy()
        for yl,delta in JAW[d].items():
            y=int(round(ty))+yl; xs=np.where(a[y,:,3]>40)[0]
            if len(xs)==0: continue
            if delta is None:
                n[y,xs]=0; continue
            l,r=xs.min(),xs.max(); dl,dr=delta
            row=a[y].copy()
            for k in range(1,dl+1): n[y,l-k]=row[l]; n[y,l-k+1]=row[min(l+1,r)] if k<dl+1 else n[y,l-k+1]
            n[y,l-dl]=row[l]
            for x in range(l-dl+1,l+1): n[y,x]=row[min(l+1,r)]
            n[y,r+dr]=row[r]
            for x in range(r,r+dr): n[y,x]=row[max(r-1,l)]
        # the row above a removed tip becomes the bottom edge: keep its own outline colours (already dark)
        out[p]=n
        if write: Image.fromarray(n).save(p)
    return out
def extend_hair(pkg, d, write, rows=8, seed=1):
    rng=np.random.default_rng(seed)
    hb=[b for b in bindings(pkg) if b['direction']==d]
    p=PARTS/pkg/hb[0]['layers']['hair.front']; H=np.array(Image.open(p).convert('RGBA'))
    # local head silhouette from the idle head.base
    bb=[b for b in bindings('base') if b['direction']==d and b['clip']=='idle'][0]
    f=MOTION[(d,'idle',0)]; tx,ty=int(round(f['headToCanvas'][4])),int(round(f['headToCanvas'][5]))
    B=np.array(Image.open(PARTS/'base'/bb['layers']['head.base']).convert('RGBA'))[ty:ty+96,tx:tx+96,3]>40
    hair=H[...,3]>40; n=H.copy()
    lum=lambda c: c[0]*.2126+c[1]*.7152+c[2]*.0722
    dark=min((tuple(H[y,x,:3]) for y,x in zip(*np.where(hair))),key=lum)
    for x in range(96):
        col=np.where(hair[:,x])[0]
        if len(col)==0: continue
        bottom=col.max()
        if bottom>=60: continue                       # already covers this column low enough
        skin=np.where(B[bottom+1:bottom+1+rows,x])[0]
        if len(skin)==0: continue
        depth=min(rows+int(rng.integers(-1,2)), len(skin))
        src=[H[y,x] for y in range(max(col.min(),bottom-5),bottom+1) if H[y,x,3]>40]
        for k in range(depth):
            y=bottom+1+k
            if y>=93 or not B[y,x]: break
            c=src[(len(src)-1-k)%len(src)].astype(float)
            c[:3]*=1-0.05*k/max(1,depth)                 # slightly darker toward the hairline
            n[y,x]=c.round().clip(0,255).astype(np.uint8); n[y,x,3]=255
    # outline the new lower edge where it meets skin or nothing
    added=(n[...,3]>40)&~hair
    for y,x in zip(*np.where(added)):
        if y+1<96 and n[y+1,x,3]<=40: n[y,x,:3]=dark
    res={}
    for b in hb:
        q=PARTS/pkg/b['layers']['hair.front']; res[q]=n
        if write: Image.fromarray(n).save(q)
    return res
if __name__=='__main__':
    w='--write' in sys.argv
    print('jaw files',len(round_jaw(w)))
    for pkg in ['hair-chestnut','hair-silver']:
        for d,s in [('up-left',3),('up-right',5)]:
            print(pkg,d,len(extend_hair(pkg,d,w,seed=s)),'files')
