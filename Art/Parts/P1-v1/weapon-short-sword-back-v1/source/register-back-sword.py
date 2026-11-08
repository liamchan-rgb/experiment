#!/usr/bin/env python3
"""Rebuild the back-carried sword from the entire generated source canvas.

No alpha threshold, alpha-derived crop, or alpha-derived scale is used.  One
fixed source-to-cell affine transform is applied to the full 1254x1254 source;
walk maps are integer y translations of the resulting idle map.
"""
import json, math, hashlib
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
SOURCE = HERE / 'source/imagegen-original.png'
OUT = HERE / 'png'
ROOT = HERE.parents[3]
REF = ROOT/'Art/Review/P1/modular-down-back-carry-v1/combinations/chestnut__blue__forester__empty'
REVIEW = HERE / 'review'
BOB = [(0,0),(0,0),(0,2),(0,-1),(0,-2),(0,0),(0,2),(0,-1),(0,-2)]
SCALE = 0.12
ANGLE_DEG = 18.0
OVERALL_TRANSLATION = (0, 0)  # final placement is expressed by the source anchor
COS = math.cos(math.radians(ANGLE_DEG))
SIN = math.sin(math.radians(ANGLE_DEG))
# Pillow positive angle convention requested by art direction.
a, b, c, d = SCALE*COS, -SCALE*SIN, SCALE*SIN, SCALE*COS
sx, sy, wx, wy = 460.0, 340.0, 90.0, 130.0
tx, ty = wx-a*sx-c*sy, wy-b*sx-d*sy
# Pillow's AFFINE expects inverse coefficients: source = inverse(world).
det = a*d-b*c
ia, ic = d/det, -c/det
ib, id_ = -b/det, a/det
itx = -(ia*tx+ic*ty)
ity = -(ib*tx+id_*ty)

raw = Image.open(SOURCE).convert('RGBA')
assert raw.size == (1254,1254), raw.size
idle = raw.transform((256,256), Image.Transform.AFFINE,
                     (ia,ic,itx,ib,id_,ity),
                     resample=Image.Resampling.NEAREST,
                     fillcolor=(0,0,0,0))
# Remove only disconnected single-alpha specks after the fixed full-canvas affine.
# This is an output cleanup, not source thresholding/cropping/fitting.
px = idle.load(); seen=set(); removed=[]
for yy in range(256):
    for xx in range(256):
        if (xx,yy) in seen or px[xx,yy][3] == 0: continue
        stack=[(xx,yy)]; seen.add((xx,yy)); comp=[]
        while stack:
            qx,qy=stack.pop(); comp.append((qx,qy))
            for ny in range(max(0,qy-1),min(256,qy+2)):
                for nx in range(max(0,qx-1),min(256,qx+2)):
                    if (nx,ny) not in seen and px[nx,ny][3] > 0:
                        seen.add((nx,ny)); stack.append((nx,ny))
        if len(comp)==1 and px[comp[0][0],comp[0][1]][3] < 8:
            removed.append([comp[0][0],comp[0][1],px[comp[0][0],comp[0][1]][3]])
            px[comp[0][0],comp[0][1]]=(0,0,0,0)
# Final source anchor was placed at (90,130) after direct review of actual v8 assembly; no additional global translation is applied.
registered = Image.new('RGBA',(256,256),(0,0,0,0))
registered.alpha_composite(idle, OVERALL_TRANSLATION)
idle = registered
# Register all nine maps from this identical 256-cell map, using only bob offsets.
for i,(dx,dy) in enumerate(BOB):
    frame = Image.new('RGBA',(256,256),(0,0,0,0))
    frame.alpha_composite(idle,(dx,dy))
    p=OUT/f'{i:02d}/weapon.back.png'
    p.parent.mkdir(parents=True,exist_ok=True)
    frame.save(p)

# Editable wrapper and minimal OpenRaster with one transparent layer.
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256"><title>weapon.back, down idle pose; full-source fixed affine</title><image href="../png/00/weapon.back.png" x="0" y="0" width="256" height="256" image-rendering="pixelated"/></svg>\n'''
(HERE/'editable/00.svg').write_text(svg)
# Make a simple one-layer ORA using the registered PNG, without modifying pixel data.
import zipfile
ora=HERE/'editable/00.ora'
with zipfile.ZipFile(ora,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    z.writestr('stack.xml','''<?xml version="1.0" encoding="UTF-8"?><image version="0.0.1" w="256" h="256" name="weapon.back">< stack><layer name="weapon.back idle00" src="data/layer0.png" x="0" y="0" opacity="1.0" visibility="visible" composite-op="svg:src-over"/></stack></image>'''.replace('< stack>','<stack>'))
    import io
    buf=io.BytesIO(); Image.open(OUT/'00/weapon.back.png').save(buf,format='PNG'); z.writestr('data/layer0.png',buf.getvalue())
    z.writestr('mergedimage.png',buf.getvalue())

# Full-body local reviews, preserving parent-owned bases read-only.
REVIEW.mkdir(exist_ok=True)
comps=[]
for i in range(9):
    key='idle-00.png' if i==0 else f'walk-{i:02d}.png'
    base=Image.open(REF/key).convert('RGBA')
    under=Image.new('RGBA',(256,256),(0,0,0,0))
    under.alpha_composite(Image.open(OUT/f'{i:02d}/weapon.back.png').convert('RGBA'))
    under.alpha_composite(base)
    base=under
    base.save(REVIEW/f'{i:02d}-back-carry-over-existing-empty-forester.png')
    comps.append(base)
# Grid, 3 columns, each character at 2x.
sheet=Image.new('RGBA',(3*512,3*512),(238,238,238,255))
for i,img in enumerate(comps):
    x=(i%3)*512; y=(i//3)*512
    sheet.alpha_composite(img.resize((512,512),Image.Resampling.NEAREST),(x,y))
    ImageDraw.Draw(sheet).text((x+8,y+7),f'{i:02d}',fill=(220,35,35,255),stroke_width=1,stroke_fill=(255,255,255,255))
sheet.convert('RGB').save(REVIEW/'nine-poses-back-carry-fullbody.png')
# 8 walk maps at 120 ms.
walk=[Image.open(REVIEW/f'{i:02d}-back-carry-over-existing-empty-forester.png').convert('RGBA') for i in range(1,9)]
walk[0].save(REVIEW/'walk-back-carry-120ms.gif',save_all=True,append_images=walk[1:],duration=120,loop=0,disposal=2)
# idle review; crop only as a detail presentation, never used for registration.
weapon=Image.open(OUT/'00/weapon.back.png').convert('RGBA')
weapon.crop(weapon.getbbox()).resize((weapon.getbbox()[2]-weapon.getbbox()[0],weapon.getbbox()[3]-weapon.getbbox()[1]),Image.Resampling.NEAREST).save(REVIEW/'weapon-back-00-pixel-detail.png')
# Visual side-by-side idle reference and candidate (1x full-body views).
ref=Image.open(REF/'idle-00.png').convert('RGBA')
candidate=Image.open(REVIEW/'00-back-carry-over-existing-empty-forester.png').convert('RGBA')
compare=Image.new('RGBA',(512,256),(238,238,238,255)); compare.alpha_composite(ref,(0,0)); compare.alpha_composite(candidate,(256,0))
compare.convert('RGB').save(REVIEW/'idle-empty-reference-vs-back-carry.png')
# Exact geometry record.
point=lambda x,y:(a*x+c*y+tx,b*x+d*y+ty)
reg={
 'canvas':[256,256],
 'reference':'Art/Review/P1/modular-down-back-carry-v1/combinations/chestnut__blue__forester__empty; actual v8 compositor outputs',
 'source':'source/imagegen-original.png',
 'sourceCanvas':[1254,1254],
 'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'registrationMethod':'Apply one fixed affine transform to the entire original 1254x1254 RGBA source canvas. No source alpha threshold, alpha-bound crop, connected-solid crop, alpha-bounds resize, or content-dependent fit. Pillow nearest-neighbor sampling. After transform, remove only disconnected one-pixel components with alpha < 8.',
 'postTransformCleanup':{'removedIsolatedPixels':removed,'purpose':'four disconnected low-alpha output specks only; source image and main connected sword structure are retained without alpha-bound fitting'},
 'sourceToCellAffine':{'convention':'x_cell=a*x_source+c*y_source+tx; y_cell=b*x_source+d*y_source+ty','a':a,'b':b,'c':c,'d':d,'tx':tx,'ty':ty,'scale':SCALE,'pillowPositiveAngleDegrees':ANGLE_DEG},
 'overallTranslationAfterAffine':list(OVERALL_TRANSLATION),
 'effectiveSourceToCellAffine':{'a':a,'b':b,'c':c,'d':d,'tx':tx+OVERALL_TRANSLATION[0],'ty':ty+OVERALL_TRANSLATION[1]},
 'inverseCoefficientsUsedByPillow':[ia,ic,itx,ib,id_,ity],
 'landmarkAnchor':{'source':[sx,sy],'baseAffineCell':[wx,wy],'finalCell':[wx+OVERALL_TRANSLATION[0],wy+OVERALL_TRANSLATION[1]],'baseAffineMapped':[point(sx,sy)]},
 'tipLandmarkApprox':{'source':[790,920],'baseAffineCell':[point(790,920)[0],point(790,920)[1]],'finalCell':[point(790,920)[0]+OVERALL_TRANSLATION[0],point(790,920)[1]+OVERALL_TRANSLATION[1]],'targetIntent':[149,184]},
 'bodyTranslationByPose':{str(i):list(v) for i,v in enumerate(BOB)},
 'poseRegistration':'One fixed 18-degree full-source affine anchored at (90,130), selected by actual v8 composition review; no added translation after the affine. Other pose maps use integer body-bob translations only; no per-pose rotate, scale, crop, or fit.',
 'rejectedPriorRegistration':'source/registration-rejected-bbox-fit-v1.json (retained only as rejected history; not used to build current PNGs)',
 'editable':'editable/00.svg and editable/00.ora are registered-output wrappers; source image remains the editable artwork origin.'
}
(HERE/'source/registration.json').write_text(json.dumps(reg,indent=2)+'\n')
print(json.dumps({'coefficients':[a,b,c,d,tx,ty],'anchor':point(460,340),'tip':point(790,920),'idleBounds':idle.getbbox()},indent=2))
