#!/usr/bin/env python3
"""Only two upper-arm image replacements; numeric checks do not accept art."""
from pathlib import Path
import subprocess,json,io
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/armor-fit-r2';A=R/'Sources/Resources/Assets.xcassets';base='a919621b09fd2608b569a0e64592d8b1bde68909';bare='/workspace/left-transitions-publish.git'
def old(p):return subprocess.check_output(['git','-C',bare,'show',base+':'+str(p)])
p='Sources/Resources/hero-gait.json';assert (R/p).read_bytes()==old(p);rig=json.loads((R/p).read_text());changed=[];unchanged=[]
for item,value in rig['armorVisuals'].items():
 for slot,name in value['battleLayers'].items():
  p='Sources/Resources/Assets.xcassets/'+name+'.imageset/'+name+'.png';data=(R/p).read_bytes()
  if slot=='MeadowBattleHeroArmNearUpperWardrobe':
   assert data!=old(p),item;changed.append(p);image=Image.open(io.BytesIO(data)).convert('RGBA');a=np.array(image);yy,xx=np.mgrid[:256,:256];v=np.array([11.,17.]);v/=np.linalg.norm(v);n=np.array([-v[1],v[0]]);points=np.stack([xx-117,yy-141],-1);u=points@v;q=points@n;length=15.5 if item=='leatherArmor' else 20.7;radius=(6.5 if item=='leatherArmor' else 6.0)-1.2*np.clip(u/length,0,1)
   assert not np.any((a[:,:,3]>0)&((u<-1)|(u>length)|(abs(q)>radius))),item
   bodyName=value['battleLayers']['MeadowBattleHeroArmNearUpperBody'];body=np.asarray(Image.open(A/(bodyName+'.imageset')/(bodyName+'.png')).convert('RGBA'));region=(body[:,:,3]>0)&(u>3)&(u<length-1)
   assert np.all(a[:,:,3][region]>0),('upper-arm skin escapes fitted sleeve',item)
  else:assert data==old(p),p;unchanged.append(p)
 for n in [value['bowAtlas'],value['bowTorso']]:
  p='Sources/Resources/Assets.xcassets/'+n+'.imageset/'+n+'.png';assert (R/p).read_bytes()==old(p);unchanged.append(p)
for p in ['Sources/Game/MeadowBattleActorView.swift','Sources/Game/HeroFrames.swift']+['Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/'+n for n in ['BowRig.swift','GreatSwordRig.swift','LegendaryStaffRig.swift','Resources/reviewed-bow-r7.json','Resources/great-sword-v1.json','Resources/legendary-staff-v1.json']]:assert (R/p).read_bytes()==old(p),p
assert len(changed)==2
report={'baseline':base,'changedRuntimeImages':changed,'allOtherMappedArmorPartsAndBowTexturesByteExact':len(unchanged),'gaitManifestByteExact':True,'runtimeLayerOrderAndBonesByteExact':True,'weaponRigsAndJSONByteExact':True,'upperSkinInsideSleeveAlongBone':True,'noUpperSleevePixelsOutsideFittedArmSilhouette':True,'artApprovalSeparate':True}
(D/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
