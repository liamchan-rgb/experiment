#!/usr/bin/env python3
"""Verify reflected sides/rig/alpha and deterministic tool-colour sources; artwork review remains separate."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label,binary_fill_holes
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('rightExport',R/'scripts/export-right-neutral-mirror.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e);B,D=e.B,e.D
read=lambda p:np.array(Image.open(p).convert('RGBA'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
solid=lambda a:a[:,:,3]>128
def main():
 cfg=json.loads((B/'mirror-authoring.json').read_text());L=R/cfg['sourceTemplate'];oldA=json.loads((L/'asset.json').read_text());a=json.loads((B/'asset.json').read_text());old=json.loads((L/'motion.json').read_text());motion=json.loads((B/'motion.json').read_text());comp=e.c.Compositor(R,D/'catalog.json',B/'motion.json');assert not e.c.contract.check_asset(B/'asset.json');assert len(a['bindings'])==len(motion['frames'])==13 and motion['durationMs']==120;assert sha(L/'asset.json')==cfg['sourceManifestSHA256'] and sha(L/'motion.json')==cfg['sourceMotionSHA256'];approval=json.loads((R/cfg['sourceApproval']).read_text());assert approval['status']=='approved'
 for name,h in approval['artifacts'].items():assert sha(R/'Art/Review/P1/neutral-left-complete-transitions-v1'/name)==h,('left approved source changed',name)
 oldRight=json.loads((R/cfg['oldRightApprovedReference']).read_text())
 for name in ['strip.png','walk.gif']:assert sha(B/'source/approved-right-reference'/name)==oldRight['artifacts'][name],('old right approved strip/normal GIF reference changed',name)
 F=np.array([[-1,0,255],[0,1,0],[0,0,1]],float);H=np.array([[-1,0,95],[0,1,0],[0,0,1]],float);head=Image.open(B/'source/head-local-relit.png').convert('RGBA');ref=Image.open(B/'source/relight-registered-atlas.png').crop((0,0,256,256));rows=[];layers=bodyPalette=headChecks=rig=chains=changedPixels=0
 for i,(f,g,binding,oldBinding) in enumerate(zip(motion['frames'],old['frames'],a['bindings'],oldA['bindings'])):
  k=('right',f['clip'],f['frame']);actual=np.array(comp.render(a['id'],[],*k));assert np.array_equal(actual,read(B/'frames'/f'{i:02}.png')),(i,'actual composition differs');source=read(L/'frames'/f'{i:02}.png')[:,::-1];assert np.array_equal(actual[:,:,3],source[:,:,3]),(i,'whole geometry differs');assert f['drawOrder']==[e.side(n) for n in g['drawOrder']] and f['facing']==[1,0] and f['support']==e.side(g['support']);assert np.allclose(e.mat(f['headToCanvas']),F@e.mat(g['headToCanvas'])@H);assert np.linalg.det(e.mat(f['headToCanvas'])[:2,:2])>0
  for j,p in g['joints'].items():assert f['joints'][e.side(j)]==[255-p[0],p[1]]
  for j,p in g['soleMarkers'].items():assert f['soleMarkers'][e.side(j)]==[255-p[0],p[1]]
  rig+=1;projected=np.array(e.c.place(head,f['headToCanvas'],(256,256)));assert np.array_equal(projected,read(B/binding['layers']['head.base'])),(i,'head is not one common local art');headChecks+=1;layerMap={}
  anchors=e.skin_anchors(L,oldBinding)
  for slot,path in oldBinding['layers'].items():
   newslot=e.side(slot);src=Image.open(L/path).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);dst=read(B/binding['layers'][newslot]);srcArray=np.array(src);assert np.array_equal(srcArray[:,:,3],dst[:,:,3]),(i,slot,'semantic alpha changed');layers+=1;layerMap[newslot]=dst
   if slot!='head.base':
    expected,_=e.palette_paint(src,ref,newslot,e.anchor_for(slot,anchors));assert np.array_equal(dst,np.array(expected)),(i,slot,'inconsistent material palette');skin=e.skin_mask(srcArray);assert np.array_equal(dst[~skin],srcArray[~skin]),(i,slot,'changed source cloth/ink/low-alpha boundary');bodyPalette+=1
   changedPixels+=int((np.any(srcArray[:,:,:3]!=dst[:,:,:3],2)&solid(dst)).sum())
  # Every near/far arm-hand and leg alpha retains exactly the approved chain geometry.
  for side in ['left','right']:
   arm=solid(layerMap['body.arm.'+side])|solid(layerMap['body.hand.'+side]);oldside=e.side(side);oldarm=solid(read(L/oldBinding['layers']['body.arm.'+oldside]))|solid(read(L/oldBinding['layers']['body.hand.'+oldside]));assert np.array_equal(arm,oldarm[:,::-1]);assert label(arm,np.ones((3,3)))[1]==label(oldarm,np.ones((3,3)))[1];leg=solid(layerMap['body.leg.'+side]);oldleg=solid(read(L/oldBinding['layers']['body.leg.'+oldside]));assert np.array_equal(leg,oldleg[:,::-1]);chains+=2
  holes=binary_fill_holes(solid(actual))&~solid(actual);oldholes=binary_fill_holes(solid(source))&~solid(source);assert np.array_equal(holes,oldholes),(i,'new junction holes');rows.append({'index':i,'clip':f['clip'],'frame':f['frame'],'actualCompositionMatches':True,'semanticAlphaReflections':8,'headLocalMatches':True,'newJunctionHoles':0,'support':f['support']})
 for name,durations in [('walk-120ms.gif',[120]*8),('walk-comparison-120ms.gif',[120]*8),('start-stop-120ms.gif',[480]+[120]*20+[480])]:
  with Image.open(D/name) as gif:assert gif.n_frames==len(durations) and gif.info['loop']==0 and [im.info['duration'] for im in ImageSequence.Iterator(gif)]==durations
 tone={}
 for side in ['left','right']:
  values=[]
  for i in range(13):
   leg=read(B/'layers'/f'{i:02}'/('body.leg.'+side+'.png'));mask=e.skin_mask(leg);values.append(round(float(np.median(leg[mask,:3]@np.array([.2126,.7152,.0722]))),3))
  assert max(values)-min(values)<.5,(side,'base skin tone flickers');tone[side]=values
 assert np.mean(tone['right'])>np.mean(tone['left']),'near/far depth lost'
 oldfiles=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/p)==h for p,h in oldfiles.items()),'old art changed'
 assert changedPixels>1000,'light reference not applied';result={'status':'technical-checks-pass','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'actualCompositorPoses':13,'semanticLayerAlphaReflections':layers,'headLocalAttachmentChecks':headChecks,'anatomicalRigAndSupportChecks':rig,'retainedLimbChainChecks':chains,'deterministicBodyPaletteChecks':bodyPalette,'legMaterialToneChecks':26,'legMedianLuminanceBySide':tone,'newJunctionAlphaHoles':0,'relitVisibleLayerPixels':changedPixels,'preservedFiles':len(oldfiles),'sourceApprovedArtifactsUnchanged':True,'oldRightApprovedArtifactsUnchanged':True,'safetyClothingInkAndBoundaryPixelsUnchanged':True,'records':rows,'limits':['New right neutral candidate only; old right whole-character artwork preserved, not inherited approval','Static tool head RGB and common per-side tool skin palettes; generated reference shapes ignored','Main reviews whole13 poses and normal GIF decoded frames; no continuous playback claim','Independent right appearances, full8direction integration and arbitrary phase interruptions remain; no App/device/IPA']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['records','limits','legMedianLuminanceBySide']}))
if __name__=='__main__':main()
