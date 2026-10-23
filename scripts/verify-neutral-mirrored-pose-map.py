#!/usr/bin/env python3
"""Verify reflected geometry, anatomical sides, attachment maps and fixed lighting."""
from pathlib import Path
import hashlib,importlib.util,json
from PIL import Image,ImageSequence
import numpy as np
from scipy.ndimage import label,binary_dilation
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/up-right/walk-r5-mirrored-up-left';D=R/'Art/Review/P1/neutral-up-right-r5-mirror'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
mirror=load('mirror',R/'scripts/export-neutral-mirrored-pose-map.py');compose=load('compose',R/'scripts/compose-character-parts.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return np.array(Image.open(p).convert('RGBA'))
def mat(v):a,b,c,d,x,y=v;return np.array([[a,c,x],[b,d,y],[0,0,1.]])
def white(a):
 r,g,b,alpha=[a[:,:,i].astype(float) for i in range(4)];return int(((r<b*1.15)&(g<b*1.15)&(b>70)&(alpha>128)).sum())
cfg=json.loads((P/'mirror-authoring.json').read_text());L=R/cfg['sourceTemplate'];asset=json.loads((P/'asset.json').read_text());motion=json.loads((P/'motion.json').read_text());leftAsset=json.loads((L/'asset.json').read_text());leftMotion=json.loads((L/'motion.json').read_text());approval=json.loads((R/cfg['sourceApproval']).read_text());assert approval['status']=='approved';assert sha(L/'asset.json')==cfg['sourceManifestSHA256'];assert sha(L/'motion.json')==cfg['sourceMotionSHA256']
for name,h in approval['artifacts'].items():assert sha(R/'Art/Review/P1/neutral-up-left-r5'/name)==h,('approved source changed',name)
assert not compose.contract.check_asset(P/'asset.json');(D/'catalog.json').write_text(json.dumps({'assets':[{'id':asset['id'],'manifest':str((P/'asset.json').relative_to(R))}]},indent=2)+'\n');comp=compose.Compositor(R,D/'catalog.json',P/'motion.json');(D/'actual-composition').mkdir(exist_ok=True);records=[];pants=[]
for idx,(old,new) in enumerate(zip(leftMotion['frames'],motion['frames'])):
 im=comp.render(asset['id'],[],'up-right',new['clip'],idx);a=np.array(im);assert np.array_equal(a,read(P/'frames'/f'{idx:02}.png')),(idx,'compositor mismatch');im.save(D/'actual-composition'/f'{idx:02}.png');left=read(L/'frames'/f'{idx:02}.png')[:,::-1];assert np.array_equal(a[:,:,3],left[:,:,3]),(idx,'whole geometry changed')
 assert new['facing']==[1,-1] and new['support']==mirror.side(old['support']);assert new['drawOrder']==[mirror.side(s) for s in old['drawOrder']];assert np.linalg.det(mat(new['headToCanvas'])[:2,:2])>0
 for joint,point in old['joints'].items():assert np.allclose(new['joints'][mirror.side(joint)],[255-point[0],point[1]],atol=1e-9),(idx,joint,'joint mapping')
 for side,point in old['soleMarkers'].items():assert new['soleMarkers'][mirror.side(side)]==[255-point[0],point[1]],(idx,side,'sole mapping')
 row={'frame':idx,'actualCompositorDifferencePixels':0,'alphaDifferenceFromApprovedReflection':0,'geometryAndSemanticLayerChecks':[],'support':new['support']}
 for oldslot,oldpath in leftAsset['bindings'][idx]['layers'].items():
  slot=mirror.side(oldslot);layer=read(P/'layers'/f'{idx:02}'/(slot+'.png'));source=read(L/oldpath)[:,::-1];assert np.array_equal(layer[:,:,3],source[:,:,3]),(idx,slot,'silhouette drift');assert label(layer[:,:,3]>128,np.ones((3,3)))[1]==1,(idx,slot,'orphan outline')
  if slot.startswith(('body.arm.','body.hand.')):assert white(layer)==0,(idx,slot,'white cloth on limb')
  row['geometryAndSemanticLayerChecks'].append({'slot':slot,'alphaDifferencePixels':0,'lightingRGBChangedPixels':int(((layer[:,:,:3]!=source[:,:,:3]).any(axis=2)&(layer[:,:,3]>128)).sum())})
 headLocal=Image.open(P/cfg['headLocalTexture']).convert('RGBA');head=compose.place(headLocal,new['headToCanvas'],(256,256));assert np.array_equal(np.array(head),read(P/'layers'/f'{idx:02}'/'head.base.png')),(idx,'head-local reflection/colour mismatch');row['headLocalAttachmentDifferencePixels']=0
 hm=read(P/'layers'/f'{idx:02}'/'head.base.png');ys,xs=np.where(hm[:,:,3]>128);bright=(hm[:,:,0]>240)&(hm[:,:,1]>185)&(hm[:,:,2]>110)&(hm[:,:,3]>128);by,bx=np.where(bright);assert len(bx)>0 and bx.mean()<(xs.min()+xs.max())/2-1 and by.mean()<(ys.min()+ys.max())/2,(idx,'light direction flipped');row['headHighlightCentre']=[float(bx.mean()),float(by.mean())]
 reference=read(P/'components'/f'{idx:02}'/'junction-reference.png');zone=read(P/'components'/f'{idx:02}'/'junction-zones.png')[:,:,3]>128;missing=(reference[:,:,3]>128)&zone&(a[:,:,3]<128);assert not missing.any(),(idx,'new joint holes');row['junctionReferenceMissingPixels']=0
 for side in ['left','right']:
  arm=read(P/'layers'/f'{idx:02}'/f'body.arm.{side}.png');hand=read(P/'layers'/f'{idx:02}'/f'body.hand.{side}.png');union=Image.fromarray(arm);union.alpha_composite(Image.fromarray(hand));assert np.array_equal(np.array(union),read(P/'components'/f'{idx:02}'/f'complete-arm.{side}.png')),(idx,side,'partition seam');assert (binary_dilation(arm[:,:,3]>128,np.ones((3,3)))&(hand[:,:,3]>128)).sum()>0,(idx,side,'wrist gap')
  if side=='right':assert np.all(a[hand[:,:,3]>128]==hand[hand[:,:,3]>128]),(idx,'near hand clipped')
 pants.append(sha(P/'components'/f'{idx:02}'/'pants.png'));records.append(row)
assert len(set(pants[1:]))==8
with Image.open(D/'walk-120ms.gif') as gif:assert gif.n_frames==8 and [f.info['duration'] for f in ImageSequence.Iterator(gif)]==[120]*8 and gif.info['loop']==0
bake=json.loads((P/'source/lighting-bake.json').read_text());assert all(v['maxReferenceSampleDistancePixels']<=2 for v in bake['textures']);result={'status':'mirrored-geometry-and-lighting-technical-checks-pass','artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'sourceApproval':cfg['sourceApproval'],'sourceApprovedArtifactsUnchanged':True,'actualCompositorPoses':9,'semanticLayerAlphaReflections':72,'headLocalAttachmentChecks':9,'anatomicalSideAndSupportMappingChecks':9,'newJunctionAlphaHoles':0,'completeArmPartitionChecks':18,'nearHandsPreserved':9,'independentPantsWalkFrames':8,'headHighlightsStayUpperLeft':9,'normalFrameDurationsMs':[120]*8,'poses':records,'limits':['Right-up artwork has no user approval','Main uses1x/2x complete frame review; no continuous-player viewing claimed','No wardrobe, complete hidden anatomy, start-stop, App/device or IPA acceptance']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['actualCompositorPoses','semanticLayerAlphaReflections','headLocalAttachmentChecks','newJunctionAlphaHoles','headHighlightsStayUpperLeft']}))
