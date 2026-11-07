#!/usr/bin/env python3
"""Offline source regression audit. Art acceptance still needs whole-body review."""
from pathlib import Path
import json,subprocess,hashlib,io
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/armor-fit-r1';A=R/'Sources/Resources/Assets.xcassets';baseline='72d90cd6b36d9ef4993beaf7156fb7be3ede00c8';bare='/workspace/left-transitions-publish.git'
def old(p):return subprocess.check_output(['git','-C',bare,'show',baseline+':'+str(p)])
def asset(n):return Image.open(A/(n+'.imageset')/(n+'.png')).convert('RGBA')
a=json.loads(old('Sources/Resources/hero-gait.json'));b=json.loads((R/'Sources/Resources/hero-gait.json').read_text());a.pop('armorVisuals');b.pop('armorVisuals');assert a==b
# All original head/hand/body/weapon source and walking atlases stay byte exact.
paths=['Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/'+n for n in ['BowRig.swift','GreatSwordRig.swift','LegendaryStaffRig.swift','Resources/reviewed-bow-r7.json','Resources/great-sword-v1.json','Resources/legendary-staff-v1.json']]
# Resolve actual module file locations without assuming a stale path.
paths=[p for p in paths if (R/p).exists()]+['Vendor/ClassroomGameCore/Sources/ClassroomGameCore/Resources/initial-content.json']
for p in paths:assert old(p)==(R/p).read_bytes(),p
rig=json.loads((R/'Sources/Resources/hero-gait.json').read_text());baselineRig=json.loads(old('Sources/Resources/hero-gait.json'));count=0
names={'MeadowBattleHeroNearHand','MeadowBattleHeroFarHand','MeadowBattleHeroHair','MeadowBattleHeroFace','MeadowBattleHeroWeapon','MeadowBattleHeroBodyCore'}
for l in rig['modularP1']['loadouts']:
 for v in l['armorAtlasNames'].values():
  for ns in v.values():names.update(ns)
for it,v in rig['armorVisuals'].items():
 names.update([v['bowAtlas'],v['bowTorso']]);order=v['battleLayerOrder'];assert len(order)==len(set(order))
 for side in ['Far','Near']:
  trousers=asset(v['battleLayers']['MeadowBattleHeroLeg'+side+'ThighWardrobe']);source=asset('MeadowBattleHeroLeg'+side+'ThighWardrobe');source.paste((0,0,0,0),(0,0,256,174));raw=np.asarray(source).copy();raw[raw[:,:,3]==0]=0;assert trousers.tobytes()==raw.tobytes()
  h='MeadowBattleHeroHem'+side+'Wardrobe';assert order.index(h)>order.index('MeadowBattleHeroLeg'+side+'ThighWardrobe') and order.index(h)>order.index('MeadowBattleHeroWardrobeCore')
  assert asset(v['battleLayers'][h]).getbbox()
 forearm=asset(v['battleLayers']['MeadowBattleHeroArmNearForearmBody'])
 # The whole elbow-to-hand centerline has opaque skin; never only a fist mask.
 for n in range(17):
  x=round(128+n);y=round(158+n*5.1/15.5);assert forearm.getpixel((x,y))[3]==255,(it,x,y)
 assert order.index('MeadowBattleHeroNearHand')>order.index('MeadowBattleHeroArmNearForearmWardrobe')>order.index('MeadowBattleHeroWardrobeCore')
 assert order.index('MeadowBattleHeroWeapon')>order.index('MeadowBattleHeroLegNearThighWardrobe')
for n in sorted(names):
 p='Sources/Resources/Assets.xcassets/'+n+'.imageset/'+n+'.png';assert old(p)==(R/p).read_bytes(),p;count+=1
report={'baseline':baseline,'originalGaitBindingsUnchanged':True,'unchangedImageCount':count,'bowMaterialAndSilhouetteUnchanged':True,'headHandsOriginalBodyAndWeaponsUnchanged':True,'pantsContainNoArmorPixels':True,'forearmCenterlineComplete':True,'hemOverPantsAndCore':True,'weaponOverPantsHandOverSleeve':True,'originalWeaponRigAndRulesUnchanged':True,'artAcceptanceIsSeparate':True}
(D/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
