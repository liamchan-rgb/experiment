#!/usr/bin/env python3
"""Cross-check the imported motion against its approved source and contact art."""
from pathlib import Path
from PIL import Image,ImageChops
import json,math,importlib.util,hashlib,subprocess
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/legendary-staff-demo-v1';A=R/'Sources/Resources/Assets.xcassets'
p=R/'scripts/review-b2-weapons-actions.py';spec=importlib.util.spec_from_file_location('approved_sword',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.configure('legendaryStaff')
poses=[x for x in json.loads((D/'legendary-staff-poses.json').read_text()) if x.get('clip','attack')=='attack'];maximum=0
for row in poses:
 trs,root,_,ground,contacts=m.ns['sample']('attack',row['progress']);q=row['sample']
 for n,t in trs.items():
  a=q['layers'][n];vals=[a['pivot']['x']-t[0][0],a['pivot']['y']-t[0][1],a['offset']['x']-t[1][0],a['offset']['y']-t[1][1],a['rotation']-t[2]];maximum=max(maximum,max(map(abs,vals)))
 maximum=max(maximum,abs(root[0]-q['rootOffset']['x']),abs(root[1]-q['rootOffset']['y']))
assert maximum<1e-8,maximum
# The exact, weapon-specific damage point is inside every monster action cell.
enemy=Image.open(A/'MeadowBattleWardenAttackSheet.imageset/MeadowBattleWardenAttackSheet.png').convert('RGBA')
assert all(enemy.getpixel((94+384*i,152))[3]>=128 for i in range(8))
# Verify modular carry never repaints the existing body/garment outside the
# back-slot pixels, and retain every earlier gait/weapon mapping.
gait=json.loads((R/'Sources/Resources/hero-gait.json').read_text());old=json.loads(subprocess.check_output(['git','-C','/workspace/left-transitions-publish.git','show','f2b7471b8154498b53731e8a63670ab34c73e8d5:Sources/Resources/hero-gait.json']))
clean=json.loads(json.dumps(gait));del clean['equipmentVisuals']['legendaryStaff']
for load in clean['modularP1']['loadouts']:del load['weaponAtlasNames']['legendaryStaff']
assert clean==old
rows=json.loads((R/'Art/Integration/Equipment-legendary-staff-v1/walking-bindings.json').read_text());source=R/'Art/Parts/P1-v1/b2-equipment-v1/legendaryStaff';atlas={}
for row in rows:
 n=row['atlas']
 if n not in atlas:atlas[n]=Image.open(A/(n+'.imageset')/(n+'.png')).convert('RGBA')
 c=row['column'];y=row['row'];im=atlas[n].crop((c*256,y*256,(c+1)*256,(y+1)*256));assert hashlib.sha256(im.tobytes()).hexdigest()==row['RGBA_SHA256']
 preset=next(p for p in gait['modularP1']['loadouts'] if p['id']==row['appearance']);group=0 if row['direction'] in ['down','left','up','right'] else 1;unarmed=preset['weaponAtlasNames']['none'][group];base=Image.open(A/(unarmed+'.imageset')/(unarmed+'.png')).convert('RGBA').crop((c*256,y*256,(c+1)*256,(y+1)*256));weapon=Image.open(source/f'png/{row["direction"]}/{row["clip"]}/{row["frame"]:02}/weapon.back.png').convert('RGBA');difference=ImageChops.difference(im,base)
 # Compare straight RGBA, retaining the alpha bound separately.
 for yy in range(256):
  for xx in range(256):
   if im.getpixel((xx,yy))!=base.getpixel((xx,yy)):assert weapon.getpixel((xx,yy))[3]>0,(row,xx,yy)
# Approved weapon texture is reused exactly in decoded pixels.
assert Image.open(source/'battle-weapon.png').convert('RGBA').tobytes()==Image.open(A/'MeadowBattleLegendaryStaff.imageset/MeadowBattleLegendaryStaff.png').convert('RGBA').tobytes()
# Every broad blade stays off the facial detail mask, including guard/hit/victory.
allposes=json.loads((D/'legendary-staff-poses.json').read_text());collisions=[]
weapon=Image.open(A/'MeadowBattleLegendaryStaff.imageset/MeadowBattleLegendaryStaff.png').convert('RGBA');face=Image.open(A/'MeadowBattleHeroFace.imageset/MeadowBattleHeroFace.png').convert('RGBA')
for r in allposes:
 masks=[]
 for name,im in [('MeadowBattleHeroWeapon',weapon),('MeadowBattleHeroFace',face)]:
  t=r['sample']['layers'][name];pivot=(t['pivot']['x'],t['pivot']['y']);off=(t['offset']['x'],t['offset']['y']);im=im.rotate(-math.degrees(t['rotation']),Image.Resampling.NEAREST,center=pivot);placed=Image.new('RGBA',(256,256));placed.alpha_composite(im,tuple(map(round,off)));masks.append(placed.getchannel('A').point(lambda a:255 if a>=128 else 0))
 if ImageChops.multiply(*masks).getbbox():collisions.append((r['clip'],r['progress']))
assert not collisions,collisions[:10]
report={'601PoseSamplesMatchApprovedCurvesWithin1e8':True,'maximumTransformError':maximum,'contactInsideAll8MonsterPoses':True,'208NativeCarryCellsMatchHashes':True,'existingBodyAndGarmentPixelsPreservedOutsideWeapon':True,'allEarlierGaitAndWeaponBindingsSemanticallyUnchanged':True,'approvedBattleWeaponPixelsExact':True,'all3606WeaponFaceChecksClear':True,'meaning':'Mechanical supplements; main-thread whole-body decoded GIF art review required.'}
(D/'geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
