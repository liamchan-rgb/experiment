#!/usr/bin/env python3
"""Rebuild fixed-registration left head resources from preserved imagegen sources."""
import base64, hashlib, json, math, zipfile
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
# The copied imagegen files are the canonical sources. The external path below
# is only a one-time bootstrap fallback for a missing package snapshot.
BOOTSTRAP_SOURCE=Path('/workspace/generated_images')
PROMPTS={
'hair-chestnut-left':('exec-de96875f-7524-431b-a293-f043f2a07fe6.png', '''Edit this exact 1254x1254 full-body source image. This is a constrained art edit: keep the character pose, complete body, head silhouette, skin, neck, clothing, limbs, feet, canvas and all registration exactly unchanged. Modify only the BARE HEAD area in place, at exactly its current pixel size and coordinates. Do not zoom, recenter, resize the head or body, crop, extend, or generate a larger portrait. Keep the whole same character visible in the same position from head to feet on the same transparent black-looking background. Add a short natural left-facing chestnut adventurer haircut fitted to the existing bald skull: compact skull cap, restrained slight tousle with 2-3 small asymmetric locks, warm copper highlights, fine dark-brown outline, short temple sideburn stopping before the ear; preserve ear and neck visibility. Add one visible blue eye looking LEFT on the face, small natural eyebrow clearly above it, a tiny subtle flat mid-face nose shading, and a separate tiny closed mouth lower down. Keep eye, nose, mouth distinctly separated top-to-bottom so all features read as a human profile at full-body scale. Do not change the head skin shape. Crisp pixel-art matching the source's existing cluster size and palette. No labels, accessories, props, shadows, or added pixels anywhere except hair and facial-feature pixels on the existing head. Keep source canvas transparency and full-body registration.'''),
'hair-silver-left':('exec-6105900e-0c8d-471c-abe3-9fa8db36a410.png', '''EDIT ONLY THE HAIR COLOR and small haircut details on this exact 1254x1254 full-body pixel-art reference. Preserve the exact canvas, full character position, head size, head silhouette, face, blue eye, eyebrows, nose, mouth, skin, ear, neck, body, clothing, limbs and feet. Change chestnut hair to natural SILVER short adventurer hair with cool graphite shadows, muted silver midtones and soft upper-left pale silver highlights. Keep the same tidy tousled side-part silhouette and short 2-3 locks, fitting the same skull, with temple hair stopping before the exposed ear. Keep face features and their coordinates untouched. No other edits, no new objects, no rescaling, no crop, transparent background.'''),
'hair-teal-left':('exec-55c3af48-3b34-4e99-a106-ea762a1fee6a.png', '''EDIT ONLY the haircut on this exact registered 1254-square full-body left-facing character image. Keep full body, pose, head position and scale, skull and face, blue eye, brow, nose, mouth, skin, ear, neck and everything below the head unchanged. Replace the short spiky hairstyle with a distinctly DIFFERENT compact dark teal side-part crop: closely tapered temples, smooth swept top with one broad low wave, tidy rounded skull-following silhouette, no spikes, no long central lock, no bangs over eye or eyebrow, short sideburn ending before ear. Deep blue-green shadows, muted teal midtones, restrained turquoise-grey upper-left highlights, fine dark navy outline. Preserve exact 1254x1254 canvas, character registration and transparent background. No other edits.'''),
'face-blue-left':('exec-71619629-9bce-43da-a886-192b1799cf67.png', '''On this exact left-facing full-body avatar image, edit only the facial features. Preserve the whole canvas, full character, hairstyle, head position and scale, skin/ear/neck silhouette, and existing eye and eyebrow. Improve the mid/lower face marks while keeping them delicate and natural: on the skin plane, draw a tiny but clearly visible flat profile nose mark about 2-3 final sprite pixels INSIDE the face from the left silhouette, centered vertically below the eye. It should read as a small nose bridge/tip shadow, never protrude as a bulb and never replace the skin outline. Draw a separate small closed mouth about 2-3 final sprite pixels, lower on the face and also inside the skin plane; leave visible skin space between nose and mouth. Keep the eye clearly upper, nose at mid-face, mouth below. Do not move eye/brow or change hair. Do not alter outer face contour, head shape, ear, skin fill, or anything below neck. Same fixed 1254x1254 source and transparent background.'''),
'face-amber-left':('exec-528bcd8c-198a-414a-b26e-1c534a7ac4a2.png', '''Edit only the visible iris on this exact 1254x1254 left-facing full-body pixel-art image. Preserve all hairstyle, face/head outline, skin, ear, neck, body, pose, canvas, eyebrow, nose and mouth exactly at the same coordinates. Change only the visible iris from blue to restrained warm amber/honey gold with a dark pupil and tiny pale highlight; keep the eye looking LEFT and its size unchanged. Keep the small separate profile nose mark and lower closed mouth as they are. No other edits, no rescaling or cropping. Transparent background.''')
}
# hair polygon in 1254-source coordinates. It traces only cap/fringe/short rear locks; face, eye, ear and neck are excluded.
HAIR_POLY=[(478,454),(483,431),(507,414),(506,401),(540,397),(544,383),(578,383),(590,376),(644,378),(653,385),(686,391),(700,405),(723,425),(741,458),(746,499),(740,530),(725,554),(704,574),(681,587),(667,581),(659,553),(647,535),(631,518),(615,498),(599,485),(584,475),(570,472),(561,482),(550,493),(541,501),(535,485),(527,473),(512,471),(505,486),(501,504),(495,509),(488,485)]
# The teal edit has a narrower close-cropped back and no spiky tips; cap boundary is traced independently.
TEAL_POLY=[(486,452),(490,430),(510,411),(523,402),(549,397),(557,390),(590,388),(600,381),(643,383),(664,392),(690,403),(710,422),(729,446),(739,475),(743,507),(735,534),(718,553),(697,566),(675,569),(662,550),(647,532),(632,515),(615,499),(601,485),(586,474),(571,470),(558,479),(545,487),(532,487),(518,478),(505,470),(494,466)]
# source-to-world registration from the common idle plate; head-local origin is world (76,61).
S=.194; TX=4.72; TY=6.4; OX=76; OY=61
AFF=(1/S,0,(OX-TX)/S,0,1/S,(OY-TY)/S)

def local_point(p):
 x,y=p; return ((S*x+TX-OX),(S*y+TY-OY))
def mask_poly(poly):
 m=Image.new('L',(96,96),0); d=ImageDraw.Draw(m); d.polygon([local_point(p) for p in poly],fill=255); return m

def rgb_class(im,kind):
 arr=np.asarray(im.convert('RGBA')); r,g,b,a=[arr[:,:,i].astype(int) for i in range(4)]
 if kind=='hair-chestnut-left': return (r-b>28)&(g-b>8)&(b<138)
 # The source's pale silver highlights are valid hair. Keep neutral/high-value
 # grays; the fixed hair-only polygon, not a brightness cutoff, excludes skin.
 if kind=='hair-silver-left': return (np.abs(r-g)<54)&(b>=g-18)
 if kind=='hair-teal-left': return (g>=r-5)&(b>r*.8)&((r+g+b)<590)
 return np.zeros(r.shape,dtype=bool)

def register(full, kind, slot):
 src=Image.open(full).convert('RGBA')
 # Hard-alpha cleanup is restricted to the source's authored overlay pixels; no resizing by bounds.
 aa=np.asarray(src.getchannel('A'))
 if slot=='hair.front':
  poly=TEAL_POLY if kind=='hair-teal-left' else HAIR_POLY
  region=mask_poly(poly)
  keep=rgb_class(src,kind)
  keep_img=Image.fromarray((keep*255).astype('uint8'))
  source_mask=Image.new('L',src.size,0); ImageDraw.Draw(source_mask).polygon(poly,fill=255)
  keep_img=ImageChops.multiply(keep_img,source_mask)
  alpha=ImageChops.multiply(src.getchannel('A'),keep_img)
  layer=src.copy(); layer.putalpha(alpha)
  local=layer.transform((96,96),Image.Transform.AFFINE,AFF,Image.Resampling.NEAREST)
  # Keep only artwork colors that belong to this hair palette in the target region.
  la=np.array(local.getchannel('A')); la[la<96]=0; local.putalpha(Image.fromarray(la.astype('uint8')))
  return local
 # Feature polygons are disjoint in source coordinates so every shape lands at one shared face registration.
 boxes={'face.eyes':(532,520,566,564),'face.brows':(520,489,570,519),'face.nose':(511,560,530,582),'face.mouth':(513,589,535,611)}
 x0,y0,x1,y1=boxes[slot]
 arr=np.array(src); r,g,b,a=[arr[:,:,i].astype(int) for i in range(4)]
 if slot=='face.eyes':
  if kind=='face-blue-left': iris=(b>r*1.12)&(b>65)&(g>35)
  else: iris=(r>g*1.08)&(r>b*1.22)&(g>55)&(b<170)
  white=(r>185)&(g>185)&(b>185)
  dark=(r<76)&(g<76)&(b<76)
  keep=iris|white|dark
 elif slot=='face.mouth':
  # The authored lip is a warm horizontal mark on the face plane; the adjacent
  # dark pixels below/right are the jaw outline and are deliberately excluded.
  mouth=Image.new('L',src.size,0)
  ImageDraw.Draw(mouth).polygon([(520,593),(534,593),(536,594),(536,596),(533,597),(520,597)],fill=255)
  warm=(r>=100)&(r<=220)&(g>=10)&(g<=105)&(b<=45)&(r>g*1.45)
  pal=Image.fromarray((warm*255).astype('uint8')); pal=ImageChops.multiply(pal,mouth)
  alpha=ImageChops.multiply(src.getchannel('A'),pal)
  layer=src.copy();layer.putalpha(alpha)
  return layer.transform((96,96),Image.Transform.AFFINE,AFF,Image.Resampling.NEAREST)
 else:
  keep=(r<115)&(g<82)&(b<70)
 region=Image.new('L',src.size,0); ImageDraw.Draw(region).rectangle((x0,y0,x1,y1),fill=255)
 pal=Image.fromarray((keep*255).astype('uint8')); pal=ImageChops.multiply(pal,region)
 alpha=ImageChops.multiply(src.getchannel('A'),pal)
 layer=src.copy(); layer.putalpha(alpha)
 return layer.transform((96,96),Image.Transform.AFFINE,AFF,Image.Resampling.NEAREST)

# local import to keep image utility dependencies minimal above.
from PIL import ImageChops

def save_ora(folder, slots):
 mimetype='image/openraster'; composite=Image.new('RGBA',(96,96),(0,0,0,0)); names=[]
 for slot in slots:
  im=Image.open(folder/'png'/f'{slot}.png').convert('RGBA'); composite.alpha_composite(im); names.append(slot)
 stack=''.join(f'<layer name="{escape(s)}" src="data/layer{s}.png" opacity="1.0" visibility="visible" composite-op="svg:src-over" x="0" y="0" />' for s in reversed(names))
 with zipfile.ZipFile(folder/'editable.ora','w') as z:
  def add(path, payload, compression=zipfile.ZIP_DEFLATED):
   info=zipfile.ZipInfo(path,date_time=(1980,1,1,0,0,0))
   info.compress_type=compression
   info.create_system=3
   info.external_attr=0o100644 << 16
   z.writestr(info,payload,compress_type=compression,compresslevel=9)
  add('mimetype',mimetype,zipfile.ZIP_STORED)
  add('stack.xml',f'<image version="0.0.1" w="96" h="96" name="{folder.name}"><stack>{stack}</stack></image>')
  add('mergedimage.png',_png_bytes(composite))
  for s in names:add(f'data/layer{s}.png',_png_bytes(Image.open(folder/'png'/f'{s}.png')))

def _png_bytes(im):
 from io import BytesIO
 b=BytesIO();im.save(b,format='PNG');return b.getvalue()

def write_package(name,part,slots):
 folder=ROOT/name; (folder/'source').mkdir(parents=True,exist_ok=True);(folder/'png').mkdir(exist_ok=True)
 genfile,prompt=PROMPTS[name];packed=folder/'source'/'imagegen-full-reference.png';generated=BOOTSTRAP_SOURCE/genfile
 if not packed.exists():
  if not generated.exists():
   raise FileNotFoundError(f'Missing canonical source {packed}; bootstrap source unavailable at {generated}')
  packed.write_bytes(generated.read_bytes())
 src=packed
 (folder/'source'/'prompt.txt').write_text(prompt+'\n')
 reference=ROOT.parents[4]/'Art/Templates/P1-Neutral/left/walk-r3-complete-transitions/source/00.png'
 author={'tool':'image_gen.imagegen','imagegenArtifact':genfile,'bootstrapPath':str(generated),'source':'source/imagegen-full-reference.png','sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'prompt':'source/prompt.txt','sharedReference':str(reference.relative_to(ROOT.parents[4])),'sharedReferenceSHA256':hashlib.sha256(reference.read_bytes()).hexdigest(),'sourceCanvas':[1254,1254], 'sourceToCanvas':[.194,0,0,.194,4.72,6.4], 'headLocalOrigin':[76,61], 'registration':'fixed affine from full source plate; no alpha-bbox crop or fit','headLocalCanvas':[96,96],'directions':['left'],'poseCoverage':'same local art on idle 00, walk 01-08, walk-start 01-02, walk-stop 01-02; headToCanvas from common motion'}
 (folder/'authoring.json').write_text(json.dumps(author,indent=2)+'\n')
 for slot in slots:
  out=register(src,name,slot)
  out.save(folder/'png'/f'{slot}.png')
  with open(folder/'png'/f'{slot}.png','rb') as f: b64=base64.b64encode(f.read()).decode()
  (folder/f'{slot}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><image width="96" height="96" href="data:image/png;base64,{b64}" /></svg>\n')
 save_ora(folder,slots)
 bindings=[]
 for clip,frames in [('idle',[0]),('walk',list(range(1,9))),('walk-start',[1,2]),('walk-stop',[1,2])]:
  for frame in frames:bindings.append({'direction':'left','clip':clip,'frame':frame,'layers':{s:f'png/{s}.png' for s in slots}})
 asset={'schemaVersion':'1.0.0','id':'p1-'+name,'version':'1.0.0','part':part,'compatibility':{'rig':'p1-chibi-v1','bodyProfile':'p1-standard','actionSet':'locomotion-v1'},'mode':'head-local','slots':slots,'directions':['left'],'clips':['idle','walk','walk-start','walk-stop'],'sourceFiles':['authoring.json','source/imagegen-full-reference.png','source/prompt.txt','editable.ora',*[f'{s}.svg' for s in slots]],'bindings':bindings}
 (folder/'asset.json').write_text(json.dumps(asset,indent=2)+'\n')

# explicit, narrow draft coordinates derived from the registered left profile head; awaiting standard-owner review.
proposal={'direction':'left','status':'proposal-not-standard','headCanvas':[96,96],'headLocalOriginOnIdleCanvas':[76,61],'sourceRegistration':{'canvas':[1254,1254],'sourceToCanvas':[.194,0,0,.194,4.72,6.4]},'anatomyGuide':{'skullAndFaceContour':'Inherited entirely from shared head.base; overlays own no skin, ear, neck or contour.','visibleEyeCentre':[34,51],'browRegion':[29,40,40,46],'eyeRegion':[31,46,40,55],'noseRegion':[25,53,31,59],'mouthRegion':[28,60,33,65]},'measuredOpaqueArtwork':{'face.brows':[30,40,39,45],'face.eyes':{'blue':[33,46,39,54],'amber':[32,46,39,55]},'face.nose':[28,58,29,59],'face.mouth':{'blue':[30,60,33,61],'amber':[30,60,33,61]},'hair.front':{'chestnut':[24,19,73,59],'silver':[22,19,73,59],'teal':[25,22,73,56]}},'allowedRegions':{'hair.front':[[18,17,76,60]],'face.brows':[[29,40,40,46]],'face.eyes':[[31,46,40,55]],'face.nose':[[25,53,31,59]],'face.mouth':[[28,60,33,65]]},'hairFrontKeepClear':[[31,46,40,55]],'faceShapeSkinEarNeckPixelsAllowed':False,'notes':'One side-profile eye only. The complete eye including upper lid is preserved; eye/brow are upper face, nose is a tiny mid-face contour accent and mouth is lower with a pixel of separation. Head shape/skin are owned only by base. The one-pixel region updates match measured generated feature pixels and never permit skin, head outline, ear or neck.'}
(ROOT/'layout-proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
for name,part,slots in [('hair-chestnut-left','hair',['hair.front']),('hair-silver-left','hair',['hair.front']),('hair-teal-left','hair',['hair.front']),('face-blue-left','face',['face.eyes','face.brows','face.nose','face.mouth']),('face-amber-left','face',['face.eyes','face.brows','face.nose','face.mouth'])]:write_package(name,part,slots)
print('wrote 5 packages and layout proposal')
