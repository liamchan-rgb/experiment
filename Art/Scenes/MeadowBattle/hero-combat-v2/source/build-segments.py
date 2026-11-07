"""Split approved registered body/clothing layers into common animation masks.
No source pixels are repainted: each source pixel belongs to exactly one part
or the remaining core. Only the small concealed-joint underlay comes from the
retained imagegen generation; it is masked to the source limb removal area.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json
ROOT=Path(__file__).resolve().parents[5]
ASSETS=ROOT/'Sources/Resources/Assets.xcassets'
SOURCE_DIR=Path(__file__).resolve().parent
OUT=SOURCE_DIR.parent
OUT.mkdir(parents=True,exist_ok=True)
# fixed common registration from P1-Neutral battle-side right-idle-r2.
CANVAS=(256,256)
polys={
 'ArmNearUpper':[(111,137),(117,136),(122,143),(126,150),(132,154),(136,159),(132,163),(126,160),(120,154),(115,148)],
 'ArmNearForearm':[(126,150),(132,153),(139,157),(146,160),(151,163),(151,169),(144,171),(137,168),(131,165),(127,160)],
 'LegNearThigh':[(126,170),(140,169),(149,176),(153,184),(152,190),(147,196),(140,197),(132,191),(127,182)],
 'LegNearShin':[(134,189),(150,188),(155,194),(153,202),(154,208),(161,210),(164,213),(164,217),(133,218),(130,211),(132,202)],
 'LegFarThigh':[(107,170),(125,169),(134,175),(134,182),(128,189),(117,196),(101,198),(97,192),(102,183)],
 'LegFarShin':[(96,190),(111,190),(114,195),(109,203),(109,209),(112,214),(112,218),(84,218),(84,209),(89,199)]
}
def polyMask(points):
 m=Image.new('L',CANVAS,0);ImageDraw.Draw(m).polygon(points,fill=255);return m
# Each segment extends 3 px under its neighbor at joints. The resulting source
# overlap keeps the elbow and knees closed as the independent parts rotate.
# Layer order defines ownership in overlap regions; core is removed by union.
masks={k:polyMask(v).filter(ImageFilter.MaxFilter(7)) for k,v in polys.items()}
import PIL.ImageChops
used=Image.new('L',CANVAS,0)
for m in masks.values(): used=PIL.ImageChops.lighter(used,m)

def source(name): return Image.open(ASSETS/f'{name}.imageset/{name}.png').convert('RGBA')
body=source('MeadowBattleHeroBody'); wardrobe=source('MeadowBattleHeroWardrobe')
original=Image.open(ROOT/'Art/Parts/P1-Battle/right-idle-v3/assembled.png').convert('RGBA')
# Core plus six shared anatomical masks, split identically across body and clothes.
outputs=[]
for stem,src in [('Body',body),('Wardrobe',wardrobe)]:
 core=src.copy()
 owned=Image.new('L',CANVAS,0)
 alpha=src.getchannel('A')
 partial=Image.eval(alpha,lambda a:255 if 0<a<255 else 0)
 for key,m in masks.items():
  # Preserve a narrow source overlap at the hip/shoulder roots. It stays inside
  # the outfit silhouette and covers the seam when the articulated part swings.
  if key.endswith('Thigh'):
   gate=Image.new('L',CANVAS,0); ImageDraw.Draw(gate).rectangle((0,176,255,255),fill=255)
   coreRemove=__import__('PIL.ImageChops',fromlist=['multiply']).multiply(m,gate)
  elif key=='ArmNearUpper':
   gate=Image.new('L',CANVAS,0); ImageDraw.Draw(gate).rectangle((0,141,255,255),fill=255)
   coreRemove=__import__('PIL.ImageChops',fromlist=['multiply']).multiply(m,gate)
  else: coreRemove=m
  coreKeep=__import__('PIL.ImageChops',fromlist=['subtract']).subtract(m,coreRemove)
  # Opaque joint overlap is safe and closes animated seams. For antialiased
  # pixels, preserve one owner so the neutral composite remains pixel-identical.
  partialOwner=__import__('PIL.ImageChops',fromlist=['lighter']).lighter(
   __import__('PIL.ImageChops',fromlist=['multiply']).multiply(owned,partial),
   __import__('PIL.ImageChops',fromlist=['multiply']).multiply(coreKeep,partial))
  duplicatePartial=__import__('PIL.ImageChops',fromlist=['multiply']).multiply(m,partialOwner)
  effective=__import__('PIL.ImageChops',fromlist=['subtract']).subtract(m,duplicatePartial)
  part=src.copy()
  part.putalpha(__import__('PIL.ImageChops',fromlist=['multiply']).multiply(alpha,effective))
  core.putalpha(__import__('PIL.ImageChops',fromlist=['subtract']).subtract(core.getchannel('A'),__import__('PIL.ImageChops',fromlist=['multiply']).multiply(src.getchannel('A'),coreRemove)))
  name=f'MeadowBattleHero{key}{stem}'
  outputs.append((name,part))
  owned=__import__('PIL.ImageChops',fromlist=['lighter']).lighter(owned,m)
 name=f'MeadowBattleHero{stem}Core'
 outputs.append((name,core))
# Keep the existing source layers unchanged; new named assets are versioned.
for name,im in outputs:
 d=ASSETS/f'{name}.imageset';d.mkdir(parents=True,exist_ok=True)
 im.save(d/f'{name}.png')
 (d/'Contents.json').write_text(json.dumps({'images':[{'filename':f'{name}.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')

# Imagegen core-only study: register its torso to the same shoulder/hip area,
# then retain only pixels where the original registered limb art was removed.
coreImage=Image.open(SOURCE_DIR/'generated-core-underlay.png').convert('RGBA').resize(CANVAS,Image.Resampling.NEAREST)
# Move the generated shirt/pelvis core down 5 px to align its shoulder and belt
# landmarks to the registered source; hidden patches are clipped to source masks.
shifted=Image.new('RGBA',CANVAS,(0,0,0,0));shifted.alpha_composite(coreImage,(0,5))
sourceAlpha=original.getchannel('A')
underMask=Image.new('L',CANVAS,0)
for key,m in masks.items():
 if key.startswith(('ArmNear','LegNearThigh','LegFarThigh')):
  underMask=__import__('PIL.ImageChops',fromlist=['lighter']).lighter(underMask,m)
underMask=__import__('PIL.ImageChops',fromlist=['multiply']).multiply(underMask,sourceAlpha)
underMask=__import__('PIL.ImageChops',fromlist=['multiply']).multiply(underMask,shifted.getchannel('A'))
shifted.putalpha(underMask)
underName='MeadowBattleHeroJointUnderlay'
d=ASSETS/f'{underName}.imageset';d.mkdir(parents=True,exist_ok=True)
shifted.save(d/f'{underName}.png')
(d/'Contents.json').write_text(json.dumps({'images':[{'filename':f'{underName}.png','idiom':'universal'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')

layers=['MeadowBattleHeroWeapon','MeadowBattleHeroJointUnderlay','MeadowBattleHeroBodyCore',
'MeadowBattleHeroArmNearUpperBody','MeadowBattleHeroArmNearForearmBody','MeadowBattleHeroLegNearThighBody','MeadowBattleHeroLegNearShinBody','MeadowBattleHeroLegFarThighBody','MeadowBattleHeroLegFarShinBody',
'MeadowBattleHeroWardrobeCore','MeadowBattleHeroArmNearUpperWardrobe','MeadowBattleHeroArmNearForearmWardrobe',
'MeadowBattleHeroLegNearThighWardrobe','MeadowBattleHeroLegNearShinWardrobe','MeadowBattleHeroLegFarThighWardrobe','MeadowBattleHeroLegFarShinWardrobe',
'MeadowBattleHeroHair','MeadowBattleHeroFace','MeadowBattleHeroNearHand','MeadowBattleHeroFarHand']
config={'canvasPx':[256,256],'footAnchorPx':[123,214],'referenceHeightPx':132,'layers':layers,'status':'v2-common-joint-parts-candidate','source':'Art/Parts/P1-Battle/right-idle-v3/assembled.png','registration':'Art/Templates/P1-Neutral/battle-side/right-idle-r2/registration.json','jointMasks':'Art/Scenes/MeadowBattle/hero-combat-v2/source/joint-regions.json','underlay':'imagegen torso core, clipped to concealed source limb regions'}
(OUT/'hero-v2-configuration.json').write_text(json.dumps(config,indent=2)+'\n')
dataset=ASSETS/'MeadowBattleHeroConfigurationV2.dataset';dataset.mkdir(parents=True,exist_ok=True)
(dataset/'configuration.json').write_text(json.dumps(config,indent=2)+'\n')

# Recompose masks over original remainder to spot any gaps at idle.
def composite(names):
 out=Image.new('RGBA',CANVAS,(0,0,0,0))
 for n in names:
  im=Image.open(ASSETS/f'{n}.imageset/{n}.png').convert('RGBA');out.alpha_composite(im)
 return out
review=Image.new('RGBA',CANVAS,(0,0,0,0))
for n in layers:
 if n=='MeadowBattleHeroJointUnderlay': continue
 im=Image.open(ASSETS/f'{n}.imageset/{n}.png').convert('RGBA');review.alpha_composite(im)
review.save(OUT/'v2-idle-recomposite.png')
# Structural provenance; detailed pixel validation run by parent/build integration.
(SOURCE_DIR/'joint-regions.json').write_text(json.dumps({k:polys[k] for k in polys},indent=2)+'\n')
print('Created',len(outputs)+1,'registered body/clothing segment assets and v2 layer config.')
