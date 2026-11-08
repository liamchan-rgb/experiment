#!/usr/bin/env python3
"""Render the candidate through the actual v8 commonbase/outfit compositor.
Run from repository root; writes only this package's review directory.
"""
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/compose-character-parts.py'
spec = importlib.util.spec_from_file_location('p1_compositor', SCRIPT)
engine_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine_module)
CATALOG = ROOT / 'Art/Templates/P1-Wardrobe/down/v8-back-carry/catalog.json'
MOTION = ROOT / 'Art/Templates/P1-Wardrobe/down/v8-back-carry/motion.json'
engine = engine_module.Compositor(ROOT, CATALOG, MOTION)
base = 'p1-neutral-down-walk-r6-relaxed-arms'
assets = ['p1-hair-chestnut-v1', 'p1-face-blue-v1', 'p1-outfit-forester-cover-v2', 'p1-weapon-short-sword-back-v1']
without_weapon = assets[:-1]
background = Image.new('RGBA', (256,256), (23,55,44,255))
review = PACKAGE / 'review'
frames=[]; records=[]
for i in range(9):
    clip='idle' if i == 0 else 'walk'
    plain=engine.render(base,without_weapon,'down',clip,i)
    rendered=engine.render(base,assets,'down',clip,i)
    diff=np.any(np.array(plain)!=np.array(rendered),axis=2)
    ys,xs=np.where(diff)
    bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None
    records.append({'frame':i,'visibleWeaponPixelCount':int(diff.sum()),'visibleBoundsAfterComposition':bounds})
    canvas=background.copy(); canvas.alpha_composite(rendered)
    canvas.save(review/f'v8-relaxed-clothed-angle18-{i:02d}.png')
    frames.append(canvas)
board=Image.new('RGBA',(1536,1536),(23,55,44,255))
for i,frame in enumerate(frames):
    x=(i%3)*512; y=(i//3)*512
    board.alpha_composite(frame.resize((512,512),Image.Resampling.NEAREST),(x,y))
    ImageDraw.Draw(board).text((x+8,y+8),f'{i:02d}',fill=(255,255,255,255))
board.save(review/'v8-relaxed-clothed-angle18-nine-poses.png')
frames[1].save(review/'v8-relaxed-clothed-angle18-120ms.gif',save_all=True,append_images=frames[2:],duration=120,loop=0,disposal=2)
(review/'v8-relaxed-clothed-angle18-comparison.json').write_text(json.dumps({
    'renderedUsing':'scripts/compose-character-parts.py',
    'catalog':'Art/Templates/P1-Wardrobe/down/v8-back-carry/catalog.json',
    'motion':'Art/Templates/P1-Wardrobe/down/v8-back-carry/motion.json',
    'selectedAssets':[base,*assets],
    'comparison':'pixel differences versus the same actual v8 commonbase + hair + face + outfit composition with only weapon omitted',
    'frames':records
},indent=2)+'\n')
print(json.dumps({'frames':records,'review':str(review)},indent=2))
