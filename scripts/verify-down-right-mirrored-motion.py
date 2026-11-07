#!/usr/bin/env python3
"""Verify actual right-down assembly, reflected anatomy, source UV and fixed light."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label,binary_dilation,binary_fill_holes
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/down-right/walk-r1-mirrored-down-left';D=R/'Art/Review/P1/neutral-down-right-r1-mirror'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
mirror=load('mirror',R/'scripts/export-down-right-mirrored-motion.py');compose=load('compose',R/'scripts/compose-character-parts.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return np.array(Image.open(p).convert('RGBA'))
def solid(a):return a[:,:,3]>128
def connected(m):return label(m,np.ones((3,3)))[1]
def mat(v):a,b,c,d,x,y=v;return np.array([[a,c,x],[b,d,y],[0,0,1.]])
def white(a):
 r,g,b,alpha=[a[:,:,i].astype(float) for i in range(4)];return int(((r<b*1.15)&(g<b*1.15)&(b>70)&(alpha>128)).sum())
cfg=json.loads((P/'mirror-authoring.json').read_text());L=R/cfg['sourceTemplate'];asset=json.loads((P/'asset.json').read_text());motion=json.loads((P/'motion.json').read_text());leftAsset=json.loads((L/'asset.json').read_text());leftMotion=json.loads((L/'motion.json').read_text());approval=json.loads((R/cfg['sourceApproval']).read_text());assert approval['status']=='approved';assert sha(L/'asset.json')==cfg['sourceManifestSHA256'];assert sha(L/'motion.json')==cfg['sourceMotionSHA256']
for name,h in approval['artifacts'].items():assert sha((R/cfg['sourceApproval']).parent/name)==h,('approved source changed',name)
assert not compose.contract.check_asset(P/'asset.json');assert len(motion['frames'])==len(asset['bindings'])==13
(D/'catalog.json').write_text(json.dumps({'assets':[{'id':asset['id'],'manifest':str((P/'asset.json').relative_to(R))}]},indent=2)+'\n');comp=compose.Compositor(R,D/'catalog.json',P/'motion.json');(D/'actual-composition').mkdir(exist_ok=True);records=[];pants=[]
F=np.array([[-1,0,255],[0,1,0],[0,0,1.]]);localF=np.array([[-1,0,95],[0,1,0],[0,0,1.]])
for idx,(old,new) in enumerate(zip(leftMotion['frames'],motion['frames'])):
 im=comp.render(asset['id'],[],'down-right',new['clip'],new['frame']);a=np.array(im);assert np.array_equal(a,read(P/'frames'/f'{idx:02}.png')),(idx,'compositor mismatch');im.save(D/'actual-composition'/f'{idx:02}.png');left=read(L/'frames'/f'{idx:02}.png')[:,::-1];assert np.array_equal(a[:,:,3],left[:,:,3]),(idx,'whole geometry changed');assert connected(solid(a))==1,(idx,'body disconnected')
 assert (new['clip'],new['frame'])==(old['clip'],old['frame']);assert new['facing']==[1,1] and new['support']==mirror.side(old['support']);assert new['drawOrder']==[mirror.side(s) for s in old['drawOrder']];registration=cfg['headRasterRegistration']['poses'][idx];delta=np.array(registration['translationPixels']);assert np.max(np.abs(delta))<.01;expectedHead=F@mat(old['headToCanvas'])@localF;expectedHead[:2,2]+=delta;assert np.allclose(mat(new['headToCanvas']),expectedHead,atol=1e-9)
 for joint,point in old['joints'].items():assert np.allclose(new['joints'][mirror.side(joint)],[255-point[0],point[1]],atol=1e-9),(idx,joint,'joint mapping')
 for side,point in old['soleMarkers'].items():assert new['soleMarkers'][mirror.side(side)]==[255-point[0],point[1]],(idx,side,'sole mapping')
 row={'pose':idx,'clip':new['clip'],'frame':new['frame'],'actualCompositorDifferencePixels':0,'alphaDifferenceFromApprovedReflection':0,'geometryAndSemanticLayerChecks':[],'support':new['support']}
 for oldslot,oldpath in leftAsset['bindings'][idx]['layers'].items():
  slot=mirror.side(oldslot);layer=read(P/'layers'/f'{idx:02}'/(slot+'.png'));source=read(L/oldpath)[:,::-1];assert np.array_equal(layer[:,:,3],source[:,:,3]),(idx,slot,'silhouette drift');assert connected(solid(layer))==1,(idx,slot,'orphan outline');assert not ((binary_fill_holes(solid(layer))&~solid(layer))&~solid(a)).any(),(idx,slot,'visible enclosed alpha hole')
  if slot.startswith(('body.arm.','body.hand.')):assert white(layer)==0,(idx,slot,'white cloth on limb')
  assert np.array_equal(np.array(mirror.retexture(Image.fromarray(source),oldslot,cfg,P,idx)),layer),(idx,slot,'unstable source texture registration')
  row['geometryAndSemanticLayerChecks'].append({'slot':slot,'alphaDifferencePixels':0,'lightingRGBChangedPixels':int(((layer[:,:,:3]!=source[:,:,:3]).any(axis=2)&solid(layer)).sum())})
 headLocal=Image.open(P/cfg['headLocalTexture']).convert('RGBA');head=compose.place(headLocal,new['headToCanvas'],(256,256));assert np.array_equal(np.array(head),read(P/'layers'/f'{idx:02}'/'head.base.png')),(idx,'head-local reflection/colour mismatch');row['headLocalAttachmentDifferencePixels']=0
 hm=read(P/'layers'/f'{idx:02}'/'head.base.png');ys,xs=np.where(solid(hm));bright=(hm[:,:,0]>240)&(hm[:,:,1]>185)&(hm[:,:,2]>110)&solid(hm);by,bx=np.where(bright);assert len(bx)>0 and bx.mean()<(xs.min()+xs.max())/2-1 and by.mean()<(ys.min()+ys.max())/2,(idx,'light direction flipped');row['headHighlightCentre']=[float(bx.mean()),float(by.mean())]
 reference=read(P/'components'/f'{idx:02}'/'junction-reference.png');zone=solid(read(P/'components'/f'{idx:02}'/'junction-zones.png'));missing=solid(reference)&zone&~solid(a);assert not missing.any(),(idx,'new joint holes');row['junctionReferenceMissingPixels']=0
 torso=solid(read(P/'layers'/f'{idx:02}'/'body.torso.png'))
 for side in ['left','right']:
  arm=read(P/'layers'/f'{idx:02}'/f'body.arm.{side}.png');hand=read(P/'layers'/f'{idx:02}'/f'body.hand.{side}.png');leg=solid(read(P/'layers'/f'{idx:02}'/f'body.leg.{side}.png'));union=Image.fromarray(arm);union.alpha_composite(Image.fromarray(hand));assert np.array_equal(np.array(union),read(P/'components'/f'{idx:02}'/f'complete-arm.{side}.png')),(idx,side,'partition seam');assert (binary_dilation(solid(arm),np.ones((3,3)))&solid(hand)).sum()>0,(idx,side,'wrist gap');assert (binary_dilation(solid(arm),np.ones((3,3)))&torso).sum()>0,(idx,side,'shoulder gap');assert (binary_dilation(leg,np.ones((3,3)))&torso).sum()>0,(idx,side,'hip gap')
  if side==cfg['nearSide']:assert np.all(a[solid(hand)]==hand[solid(hand)]),(idx,'near hand clipped')
 pants.append(sha(P/'components'/f'{idx:02}'/'pants.png'));records.append(row)
assert len(set(pants[1:9]))==8
for name,durations in [('walk-120ms.gif',[120]*8),('start-stop-120ms.gif',[480]+[120]*20+[480])]:
 with Image.open(D/name) as gif:assert gif.n_frames==len(durations) and [f.info['duration'] for f in ImageSequence.Iterator(gif)]==durations and gif.info['loop']==0,name
bake=json.loads((P/'source/lighting-bake.json').read_text());assert all(v['maxReferenceSampleDistancePixels']<=2 for v in bake['textures']),[(v['texture'],v['maxReferenceSampleDistancePixels']) for v in bake['textures']]
preserved=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/p)==h for p,h in preserved.items()),'old assets modified'
result={'status':'mirrored-geometry-and-lighting-technical-checks-pass','artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'sourceApproval':cfg['sourceApproval'],'sourceApprovedArtifactsUnchanged':True,'actualCompositorPoses':13,'semanticLayerAlphaReflections':104,'headLocalAttachmentChecks':13,'anatomicalSideAndSupportMappingChecks':13,'newJunctionAlphaHoles':0,'completeArmPartitionChecks':26,'nearHandsPreserved':13,'independentPantsWalkFrames':8,'headHighlightsStayUpperLeft':13,'preservedFiles':len(preserved),'normalFrameDurationsMs':[120]*8,'poses':records,'limits':['Right-down artwork has no user approval','Main uses1x/2x complete frame review; no continuous-player viewing claimed','No wardrobe, complete hidden anatomy, arbitrary phase interruption, App/device or IPA acceptance']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['actualCompositorPoses','semanticLayerAlphaReflections','headLocalAttachmentChecks','newJunctionAlphaHoles','headHighlightsStayUpperLeft','preservedFiles']}))
