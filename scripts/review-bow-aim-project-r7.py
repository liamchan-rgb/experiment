#!/usr/bin/env python3
"""One native modular bow keyframe, using the existing project compositor.
No generated image, scene simulation, archive build, or animation expansion.
"""
from pathlib import Path
import functools,hashlib,json,math
from PIL import Image,ImageDraw,ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r7'
O=R/'Art/Review/Battle/hunting-bow-aim-project-r7';O.mkdir(parents=True,exist_ok=True)
A=R/'Sources/Resources/Assets.xcassets'
renderer=R/'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py'
namespace={'__file__':str(renderer)}
exec(compile(renderer.read_text().split("\nfor clip,data in lib['clips'].items():")[0],str(renderer),'exec'),namespace)
namespace['lib']=json.loads((A/'MeadowBattleHeroAnimationV2.dataset/animation.json').read_text())
used={}
def source_asset(name):
 p=A/(name+'.imageset');desc=json.loads((p/'Contents.json').read_text());p=p/next(x['filename'] for x in desc['images'] if x.get('filename'))
 used[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return Image.open(p).convert('RGBA')
def asset(name):
 replacement={'MeadowBattleBowDrawingHand':'drawing-hand.png','MeadowBattleBowGripHand':'grip-hand.png'}.get(name)
 if replacement:return Image.open(D/replacement).convert('RGBA')
 im=source_asset(name)
 # Narrowing the jacket exposes an old duplicated belt edge in this thigh crop.
 # Clear only that clothing fragment, above the unchanged leg artwork.
 if name in ['MeadowBattleHeroLegNearThighWardrobe','MeadowBattleBowLegFarThighWardrobe']:
  ImageDraw.Draw(im).rectangle((109,159,145,169),fill=(0,0,0,0))
  # Keep neutral trouser pixels at the hip; remove only colorful old coat/hem fragments.
  for y in range(170,175):
   for x in range(109,146):
    c=im.getpixel((x,y))
    if c[3] and max(c[:3])-min(c[:3])>18:im.putpixel((x,y),(0,0,0,0))
 return im
namespace['asset']=asset
pose=json.loads((D/'pose.json').read_text())
bow_samples={('attack',198):pose,('attack',199):pose}
# Reuse the exact layered bow composition routine already used by the project review.
source= (R/'scripts/review-hunting-bow-a-project-r1.py').read_text()
composition=source[source.index('def interpolate'):source.index('def draw_projectile')]
composition=composition.replace("['torso','farArm','nearArm','head']", "['farArm','nearUpperArm','torso','nearForeArm','head']")
composition=composition.replace("['torso','farArm','farHand','nearArm','nearHand']", "['torso','farArm','farHand','nearUpperArm','nearForeArm','nearHand']")
# Only the neckline and belt are reused; the jacket panel covers the old front opening.
composition=composition.replace("[(104,125,147,142),(138,139,146,151),(104,158,145,175)]", "[(104,125,147,142),(104,158,145,175)]")
# Exclude the undershirt/shoulder pixels carried in BodyCore's rectangular head crop.
composition=composition.replace("ImageDraw.Draw(mask).rectangle((100,75,156,136),fill=255)", "ImageDraw.Draw(mask).rectangle((100,75,156,132),fill=255);ImageDraw.Draw(mask).polygon([(121,126),(135,130),(134,138),(125,138),(119,134)],fill=255)")
composition=composition.replace("    import PIL.ImageChops\n     im.putalpha", "    ImageDraw.Draw(mask).rectangle((138,143,146,169),fill=0)\n     import PIL.ImageChops\n     im.putalpha",1)
# The native torso PNG/surfaces already include all collar and belt pixels.
# Do not paste the unposed original torso over this fitted garment a second time.
composition=composition.replace("if name=='torso':","if False: # native torso already contains its original trim")
exec(compile(composition,'project-keyframe-r7-layer-order','exec'),globals())
assembled=gear_render('attack',.33,'huntingBow')
assembled.save(D/'assembled.png')
bg=Image.new('RGBA',(256,256),'#20372a');bg.alpha_composite(assembled)
bg.convert('RGB').save(O/'first-frame-native.png')
bg.convert('RGB').resize((768,768),Image.Resampling.NEAREST).save(O/'first-frame-3x.png')
# Independently encoded native sleeve layers must match the surfaces the compositor uses.
for group in ['nearUpperArm','nearForeArm','farArm','torso']:
 layer=Image.new('RGBA',(256,256));d=ImageDraw.Draw(layer)
 for surf in pose['surfaces']:
  if surf['group']==group:d.polygon([(q['x'],q['y']) for q in surf['points']],fill='#%06x'%surf['color'])
 assert layer.tobytes()==Image.open(D/(group+'.png')).convert('RGBA').tobytes()
# Native hand, cuff, and string contacts in this static pose.
assert pose['arrowTail']==pose['stringHand']=={'x':141,'y':139}
assert pose['parts']['farHand']['pivot']['x']+pose['parts']['farHand']['offset']['x']==184
assert pose['parts']['farHand']['pivot']['y']+pose['parts']['farHand']['offset']['y']==152
for file,size in [('nearUpperArm.png',(256,256)),('nearForeArm.png',(256,256)),('torso.png',(256,256)),('farArm.png',(256,256)),('drawing-hand.png',(16,12)),('grip-hand.png',(14,12))]:
 im=Image.open(D/file);assert im.size==size and im.mode=='RGBA' and 0 in im.getchannel('A').getextrema()
manifest={'canvas':[256,256],'pose':'aim / fully drawn','poseContract':'BowRigSample','poseFile':'pose.json','layerOrder':['farArm','nearUpperArm','torso','nearForeArm','head','hair','face','bow','stringAndArrow','farHand','nearHand'],'sourceAssets':used,'replacementLayers':{'nearUpperArm':'nearUpperArm.png','nearForeArm':'nearForeArm.png','torso':'torso.png','farArm':'farArm.png','nearHand':'drawing-hand.png','farHand':'grip-hand.png'},'handDrawBounds':{'nearHand':[-14,-6,16,12],'farHand':[-8,-6,14,12]},'renderer':'scripts/review-bow-aim-project-r7.py:project-keyframe-r7-layer-order','regenerate':'python scripts/review-bow-aim-project-r7.py','imageGenerationUsed':False,'runtimeImported':False,'userApproved':False}
(D/'assembly.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(O/'validation.json').write_text(json.dumps({'nativeCanvas':[256,256],'independentSleevePNGsMatchCompositedSurfaces':True,'nativeHandLayersHaveTransparency':True,'stringAndArrowMeetDrawingFinger':True,'farHandAnchoredAtBowGrip':True,'originalSourceAssetsListedWithSHA256':True,'imageGenerationUsed':False,'runtimeImported':False,'userApproved':False},indent=2)+'\n')
previous=Image.open(R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r6/assembled.png').convert('RGBA')
checks=json.loads((O/'validation.json').read_text())
for label,box in [('faceAndHairAboveNeck',(100,75,158,126)),('legsAndBoots',(80,176,165,216))]:
 same=previous.crop(box).tobytes()==assembled.crop(box).tobytes();assert same,label;checks[label+'Unchanged']=same

reference=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r6'
old_pose=json.loads((reference/'pose.json').read_text())
for file in ['drawing-hand.png','grip-hand.png','torso.png']:
 assert (D/file).read_bytes()==(reference/file).read_bytes(),file
assert [s for s in pose['surfaces'] if s['group']=='torso']==[s for s in old_pose['surfaces'] if s['group']=='torso']
lengths={}
for prefix in ['near','far']:
 assert pose['parts'][prefix+'Upper']['pivot']==old_pose['parts'][prefix+'Upper']['pivot']
 def segments(rig):
  sh=rig['parts'][prefix+'Upper']['pivot'];el=rig['parts'][prefix+'Fore']['pivot'];h=rig['parts'][prefix+'Hand'];hp={'x':h['pivot']['x']+h['offset']['x'],'y':h['pivot']['y']+h['offset']['y']}
  return [math.hypot(a['x']-b['x'],a['y']-b['y']) for a,b in [(sh,el),(el,hp)]]
 before,after=segments(old_pose),segments(pose)
 assert all(.80<a/b<.97 for a,b in zip(after,before)),(prefix,before,after)
 lengths[prefix]={'before':before,'after':after}
shift=pose['parts']['bow']['offset']['x']-old_pose['parts']['bow']['offset']['x']
assert shift==pose['parts']['farHand']['offset']['x']-old_pose['parts']['farHand']['offset']['x']
assert pose['upperTip']['x']-old_pose['upperTip']['x']==shift
assert pose['lowerTip']['x']-old_pose['lowerTip']['x']==shift
# The independent native torso and waist are untouched.
assert previous.crop((110,159,148,175)).tobytes()==assembled.crop((110,159,148,175)).tobytes()
checks.update({'shoulderRootsUnchanged':True,'torsoFileAndSurfacesUnchanged':True,'handSpriteFilesUnchanged':True,'waistPixelsUnchanged':True,'bothArmsShorter':True,'limbLengths':lengths,'bowMovesWithHoldingHand':True,'bowTranslationX':shift})

(O/'validation.json').write_text(json.dumps(checks,indent=2)+'\n')
print('Rendered project resource keyframe:',O/'first-frame-3x.png')
