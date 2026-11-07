#!/usr/bin/env python3
"""Actual right appearances: preserved body/alpha, coverage, features, hands and back carry. Art approval separate."""
from pathlib import Path
import hashlib,importlib.util,itertools,json
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('rightAppearance',R/'scripts/export-right-appearance.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e);P,T,D=e.P,e.T,e.D
read=lambda p:np.array(Image.open(p).convert('RGBA'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['baseTemplate'];a=json.loads((B/'asset.json').read_text());old=json.loads((B/'motion.json').read_text());m=json.loads((T/'motion.json').read_text());cat=json.loads((T/'catalog.json').read_text());assert cfg['relightEnabled'];assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256'];profile=json.loads((R/'Art/Standards/P1-Parts-v1/profile.json').read_text());assert 'right' in profile['headLayouts'];profile['headLayouts'].pop('right');assert profile==json.loads((D/'baseline-profile.json').read_text());assert len(cat['assets'])==9
 for v in cat['assets']:assert not e.compose.contract.check_asset(R/v['manifest']),v['id']
 for f,g in zip(m['frames'],old['frames']):
  assert {k:v for k,v in f.items() if k not in ['drawOrder','artApproval']}=={k:v for k,v in g.items() if k not in ['drawOrder','artApproval']};assert [s for s in f['drawOrder'] if s in a['slots']]==g['drawOrder']
 c=e.compose.Compositor(R,T/'catalog.json',T/'motion.json');leftComp=e.compose.Compositor(R,R/'Art/Templates/P1-Wardrobe/left/v2-painted-poses/catalog.json',R/cfg['sourceWardrobeMotion']);sourceIDs={n:json.loads((R/p/'asset.json').read_text())['id'] for n,p in cfg['sources'].items()};counts={'manifestsChecked':9,'actualCompositorPoses':0,'bareBodyPosesUnchanged':0,'bodyLayerPreservationChecks':0,'appearanceAlphaReflectionChecks':0,'wholeAlphaReflectionChecks':0,'clothingCoverageChecks':0,'handPreservationChecks':0,'weaponToggleChecks':0,'weaponPoseReflectionChecks':0,'headFeatureChecks':0};records=[]
 for name,src in cfg['sources'].items():
  source=R/src;left=json.loads((source/'asset.json').read_text());right=json.loads((P/name/'asset.json').read_text())
  for b,g in zip(left['bindings'],right['bindings']):
   for slot,path in b['layers'].items():
    original=read(source/path)[:,::-1];out=read(P/name/g['layers'][e.side(slot)]);assert np.array_equal(original[:,:,3],out[:,:,3]),(name,b['clip'],b['frame'],slot,'changed garment/head alpha');assert not out[out[:,:,3]==0].any(),(name,'latent face/body RGB under empty alpha');counts['appearanceAlphaReflectionChecks']+=1
    if name.startswith('face') or name=='back-scabbard':mask=out[:,:,3]>0;assert np.array_equal(original[mask],out[mask]),(name,'changed feature ink/weapon');counts['weaponPoseReflectionChecks']+=int(name=='back-scabbard')
 for i,f in enumerate(m['frames']):
  k=('right',f['clip'],f['frame']);bare=np.array(c.render(a['id'],[],*k));assert np.array_equal(bare,read(B/'frames'/f'{i:02}.png')),(i,'bare body changed');counts['bareBodyPosesUnchanged']+=1;bodyLayers=c.layers(a['id'],[],*k);visibleHands=np.zeros((256,256),bool)
  for j,(slot,im) in enumerate(bodyLayers):
   if slot.startswith('body.hand.'):
    contribution=np.array(im.getchannel('A'),float)/255
    for _,above in bodyLayers[j+1:]:contribution*=1-np.array(above.getchannel('A'),float)/255
    visibleHands|=contribution>=.99
  for style,hair,face,carry in itertools.product(['forester','wayfarer'],['chestnut','silver'],['blue','amber'],['empty','back']):
   key='__'.join([style,hair,face,carry]);sel=['p1-right-'+n+'-v1' for n in [style,'lower','hair-'+hair,'face-'+face]]+(['p1-right-back-scabbard-v1'] if carry=='back' else []);ordered=c.layers(a['id'],sel,*k);layers=dict(ordered);out=np.array(c.render(a['id'],sel,*k));assert np.array_equal(out,read(D/'combinations'/key/f'{i:02}.png')),(i,key,'actual composition differs');counts['actualCompositorPoses']+=1
   for slot,im in ordered:
    if slot in a['slots']:assert np.array_equal(np.array(im),read(B/'layers'/f'{i:02}'/(slot+'.png'))),(i,key,slot,'appearance changed body');counts['bodyLayerPreservationChecks']+=1
   for slot in ['body.arm.left','body.arm.right','body.leg.left','body.leg.right','body.torso']:
    j=next(j for j,(s,_) in enumerate(ordered) if s==slot);contribution=np.array(ordered[j][1].getchannel('A'),float)/255
    for _,above in ordered[j+1:]:contribution*=1-np.array(above.getchannel('A'),float)/255
    if slot=='body.torso':contribution[128:138,123:136]=0  # exact reflected anatomical collar opening
    assert not (contribution>.05).any(),(i,key,slot,'clothing leak',int((contribution>.05).sum()));counts['clothingCoverageChecks']+=1
   assert np.array_equal(out[visibleHands],bare[visibleHands]),(i,key,'visible original hand occluded/changed');counts['handPreservationChecks']+=1
   for slot in ['face.eyes','face.brows','face.nose','face.mouth']:
    j=next(j for j,(s,_) in enumerate(ordered) if s==slot);contribution=np.array(ordered[j][1].getchannel('A'),float)/255
    for _,above in ordered[j+1:]:contribution*=1-np.array(above.getchannel('A'),float)/255
    assert contribution.max()>.3 and (contribution>.1).any(),(i,key,slot,'feature lost/covered');counts['headFeatureChecks']+=1
   if carry=='back':
    empty=np.array(c.render(a['id'],sel[:-1],*k));changed=np.any(out!=empty,2);weapon=np.array(layers['weapon.back'])[:,:,3]>0;assert changed.any() and not (changed&~weapon).any() and not (changed&visibleHands).any(),(i,key,'weapon changes body or hands');counts['weaponToggleChecks']+=1
   oldSel=[sourceIDs[n] for n in [style,'lower','hair-'+hair,'face-'+face]]+([sourceIDs['back-scabbard']] if carry=='back' else []);original=np.array(leftComp.render('p1-neutral-left-walk-r3-complete-transitions',oldSel,'left',f['clip'],f['frame']))[:,::-1];assert np.array_equal(out[:,:,3],original[:,:,3]),(i,key,'new gaps/fragments against reflected projection');counts['wholeAlphaReflectionChecks']+=1;records.append({'pose':i,'combination':key,'compositionMatches':True,'bodyUnchanged':True,'clothingLeakPixelsAbove5Percent':0,'handsPreserved':True,'fourFaceFeatureLayersVisible':True,'alphaMatchesReflectedSource':True})
 for name,timings in [('outfits-walk-120ms.gif',[120]*8),('outfits-start-stop-120ms.gif',cfg['durationsMs'])]:
  with Image.open(D/name) as gif:assert gif.n_frames==len(timings) and gif.info['loop']==0 and [im.info['duration'] for im in ImageSequence.Iterator(gif)]==timings
 oldfiles=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/p)==v for p,v in oldfiles.items()),'old artwork changed'
 result={'status':'technical-checks-pass','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,**counts,'combinations':16,'poses':13,'preservedFiles':len(oldfiles),'profileChange':'Only right head layout added; old profile data unchanged','records':records,'limits':['Numerical pass does not replace main1x/2x full-body review or user art approval','Only right candidate and specified start/stop; no arbitrary phase interrupts or full8direction/runtime approval','Still viewer only, no continuous playback claim','No App/device/IPA']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['records','limits']}))
if __name__=='__main__':main()
