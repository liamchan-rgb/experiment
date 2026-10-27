#!/usr/bin/env python3
"""One native modular bow keyframe, using the existing project compositor.
No generated image, scene simulation, archive build, or animation expansion.
"""
from pathlib import Path
import functools,hashlib,json,math
from PIL import Image,ImageDraw,ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r1'
O=R/'Art/Review/Battle/hunting-bow-aim-project-r1';O.mkdir(parents=True,exist_ok=True)
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
 return Image.open(D/replacement).convert('RGBA') if replacement else source_asset(name)
namespace['asset']=asset
pose=json.loads((D/'pose.json').read_text())
bow_samples={('attack',198):pose,('attack',199):pose}
# Reuse the exact layered bow composition routine already used by the project review.
source= (R/'scripts/review-hunting-bow-a-project-r1.py').read_text()
exec(compile(source[source.index('def interpolate'):source.index('def draw_projectile')],'shared-bow-compositor','exec'),globals())
assembled=gear_render('attack',.33,'huntingBow')
assembled.save(D/'assembled.png')
bg=Image.new('RGBA',(256,256),'#20372a');bg.alpha_composite(assembled)
bg.convert('RGB').save(O/'first-frame-native.png')
bg.convert('RGB').resize((768,768),Image.Resampling.NEAREST).save(O/'first-frame-3x.png')
# Independently encoded native sleeve layers must match the surfaces the compositor uses.
for group in ['nearArm','farArm']:
 layer=Image.new('RGBA',(256,256));d=ImageDraw.Draw(layer)
 for surf in pose['surfaces']:
  if surf['group']==group:d.polygon([(q['x'],q['y']) for q in surf['points']],fill='#%06x'%surf['color'])
 assert layer.tobytes()==Image.open(D/(group+'.png')).convert('RGBA').tobytes()
# Native hand, cuff, and string contacts in this static pose.
assert pose['arrowTail']==pose['stringHand']=={'x':144,'y':139}
assert pose['parts']['farHand']['pivot']['x']+pose['parts']['farHand']['offset']['x']==189
assert pose['parts']['farHand']['pivot']['y']+pose['parts']['farHand']['offset']['y']==152
for file,size in [('nearArm.png',(256,256)),('farArm.png',(256,256)),('drawing-hand.png',(16,12)),('grip-hand.png',(14,12))]:
 im=Image.open(D/file);assert im.size==size and im.mode=='RGBA' and 0 in im.getchannel('A').getextrema()
manifest={'canvas':[256,256],'pose':'aim / fully drawn','poseContract':'BowRigSample','poseFile':'pose.json','sourceAssets':used,'replacementLayers':{'nearArm':'nearArm.png','farArm':'farArm.png','nearHand':'drawing-hand.png','farHand':'grip-hand.png'},'handDrawBounds':{'nearHand':[-14,-6,16,12],'farHand':[-8,-6,14,12]},'renderer':'scripts/review-hunting-bow-a-project-r1.py:gear_render','regenerate':'python scripts/review-bow-aim-project-r1.py','imageGenerationUsed':False,'runtimeImported':False,'userApproved':False}
(D/'assembly.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(O/'validation.json').write_text(json.dumps({'nativeCanvas':[256,256],'independentSleevePNGsMatchCompositedSurfaces':True,'nativeHandLayersHaveTransparency':True,'stringAndArrowMeetDrawingFinger':True,'farHandAnchoredAtBowGrip':True,'originalSourceAssetsListedWithSHA256':True,'imageGenerationUsed':False,'runtimeImported':False,'userApproved':False},indent=2)+'\n')
print('Rendered project resource keyframe:',O/'first-frame-3x.png')
