#!/usr/bin/env python3
"""Technical evidence for shared down transition fields and exact old-art preservation; artwork acceptance stays separate."""
from pathlib import Path
import hashlib,importlib.util,itertools,json
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label,binary_dilation
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('downexp',R/'scripts/export-down-transitions.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
B,P,T,D=e.B,e.P,e.T,e.D
read=lambda p:np.array(Image.open(p).convert('RGBA'))
solid=lambda a:a[:,:,3]>128
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cfg=json.loads((B/'authoring.json').read_text());catalog=json.loads((T/'catalog.json').read_text());motion=json.loads((T/'motion.json').read_text());old=json.loads((R/cfg['oldMotion']).read_text());base='p1-neutral-down-walk-r7-transitions';ids={n:'p1-down-'+n+'-transitions-v1' for n in cfg['sources'] if n!='base'};comp=e.compose.Compositor(R,T/'catalog.json',T/'motion.json');oldcomp=e.compose.Compositor(R,R/cfg['oldCatalog'],R/cfg['oldMotion']);oldids={n:json.loads((R/p/'asset.json').read_text())['id'] for n,p in cfg['sources'].items()};checks={'manifestsChecked':0,'actualCompositorPoses':0,'oldCompositePosesUnchanged':0,'oldLayerFilesByteUnchanged':0,'bodyLayerPreservationChecks':0,'clothingCoverageChecks':0,'weaponToggleChecks':0,'armHandChains':0,'legChains':0,'sharedLegUVChecks':0,'transitionPoseDistinctChecks':0};records=[]
 for entry in catalog['assets']:
  assert not e.compose.contract.check_asset(R/entry['manifest']),entry['id'];checks['manifestsChecked']+=1
 for i,f in enumerate(motion['frames']):
  k=(f['direction'],f['clip'],f['frame']);bare=np.array(comp.render(base,[] ,*k));assert np.array_equal(bare,read(B/'frames'/f'{i:02}.png'))
  if i<9:
   assert f['headToCanvas']==old['frames'][i]['headToCanvas'] and f['drawOrder']==old['frames'][i]['drawOrder']
   for tag,path in cfg['sources'].items():
    source=R/path;manifest=json.loads((source/'asset.json').read_text());folder=B if tag=='base' else P/tag;new=json.loads((folder/'asset.json').read_text())
    for slot,src in manifest['bindings'][i]['layers'].items():assert (source/src).read_bytes()==(folder/new['bindings'][i]['layers'][slot]).read_bytes(),(i,tag,slot);checks['oldLayerFilesByteUnchanged']+=1
  layers=dict(comp.layers(base,[],*k))
  for side in ['left','right']:
   arm=solid(np.array(layers['body.arm.'+side]));hand=solid(np.array(layers['body.hand.'+side]));leg=solid(np.array(layers['body.leg.'+side]));torso=solid(np.array(layers['body.torso']));assert label(arm|hand,np.ones((3,3)))[1]==1,(i,side,'detached arm/hand');assert (binary_dilation(arm)&torso).any(),(i,side,'shoulder gap');assert label(leg,np.ones((3,3)))[1]==1,(i,side,'leg fragments');assert (binary_dilation(leg)&torso).any(),(i,side,'hip gap');checks['armHandChains']+=1;checks['legChains']+=1
   if i>=9:
    uv=np.array(Image.open(B/'source-uv'/f'{i:02}'/('leg.'+side+'.png')))
    for tag,slot in [('base','body.leg.'+side),('forester','outfit.pants.'+side),('forester','outfit.boot.'+side),('wayfarer','outfit.pants.'+side),('wayfarer','outfit.boot.'+side)]:
     source=R/cfg['sources'][tag];a=json.loads((source/'asset.json').read_text());expected=e.sample(Image.open(source/a['bindings'][0]['layers'][slot]).convert('RGBA'),uv);folder=B if tag=='base' else P/tag;actual=folder/('layers' if tag=='base' else 'png')/f'{i:02}'/(slot+'.png');assert np.array_equal(np.array(expected),read(actual)),(i,tag,slot,'body/clothes UV differs');checks['sharedLegUVChecks']+=1
  for hair,face,style,carry in itertools.product(['chestnut','silver','teal-crop'],['blue','amber'],['plain','forester','wayfarer'],['empty','back']):
   name='__'.join([hair,face,style,carry]);tags=['hair-'+hair,'face-'+face]+([style] if style!='plain' else [])+(['back-scabbard'] if carry=='back' else []);selected=[ids[t] for t in tags];ordered=comp.layers(base,selected,*k);a=np.array(comp.render(base,selected,*k));assert np.array_equal(a,read(D/'combinations'/name/f'{i:02}.png')),(i,name,'saved actual composition differs');checks['actualCompositorPoses']+=1
   for slot,im in ordered:
    if slot.startswith(('body.','head.base')):assert np.array_equal(np.array(im),np.array(layers[slot])),(i,name,'appearance changed body');checks['bodyLayerPreservationChecks']+=1
   if i<9:
    expected=np.array(oldcomp.render(oldids['base'],[oldids[t] for t in tags],'down',f['clip'],f['frame']));assert np.array_equal(a,expected),(i,name,'old9 composite pixels changed');checks['oldCompositePosesUnchanged']+=1
   if style!='plain':
    for slot in ['body.arm.right','body.arm.left','body.leg.right','body.leg.left','body.torso']:
     index=next(n for n,(s,_) in enumerate(ordered) if s==slot);contribution=np.array(ordered[index][1].getchannel('A'),float)/255
     for _,im in ordered[index+1:]:contribution*=1-np.array(im.getchannel('A'),float)/255
     if slot=='body.torso':contribution[:int(round(136+f['bodyTranslation'][1]))]=0
     assert not (contribution>.05).any(),(i,name,slot,'visible safety clothing/skin leakage',int((contribution>.05).sum()));checks['clothingCoverageChecks']+=1
   if carry=='back':
    empty=np.array(comp.render(base,selected[:-1],*k));layerMap=dict(ordered);weapon=np.array(layerMap['weapon.back'])[:,:,3]>0;changed=np.any(a!=empty,axis=2);assert changed.any() and not (changed&~weapon).any(),(i,name,'weapon toggle changed other pixels');protected=np.zeros((256,256),bool)
    for slot in ['head.base','hair.front','face.eyes','face.brows','face.nose','face.mouth','body.hand.left','body.hand.right']:
     if slot in layerMap:protected|=np.array(layerMap[slot])[:,:,3]>=250
    assert not (changed&protected).any(),(i,name,'weapon changes opaque head/face/hands');checks['weaponToggleChecks']+=1
   records.append({'pose':i,'combination':name,'actualCompositionMatches':True,'oldPoseUnchanged':True if i<9 else None})
 for recipe in cfg['transitionPoses']:
  i=recipe['index'];a=read(B/'frames'/f'{i:02}.png');assert not np.array_equal(a,read(B/'frames/00.png')) and not np.array_equal(a,read(B/'frames'/f'{recipe["walkPose"]:02}.png'));checks['transitionPoseDistinctChecks']+=1
  uvrec=json.loads((D/'rig-audit.json').read_text())['poses'][i]['legUV'];assert all(v['minimumRowGap']>0 for v in uvrec.values())
 for name,durations in [('outfits-walk-120ms.gif',[120]*8),('outfits-start-stop-120ms.gif',cfg['durationsMs'])]:
  with Image.open(D/name) as gif:assert gif.n_frames==len(durations) and [im.info['duration'] for im in ImageSequence.Iterator(gif)]==durations and gif.info['loop']==0
 oldfiles=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/k)==v for k,v in oldfiles.items()),'old artwork/source changed'
 result={'status':'technical-checks-pass','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,**checks,'combinations':36,'poses':13,'newTransitionPoses':4,'preservedFiles':len(oldfiles),'records':records,'limits':['Actual468 poses checked numerically; whole-body visual review recorded separately','Only idle->walk01 and walk08->idle; arbitrary phase interruption not tested','Old records synced as historical evidence, new current checks distinguished','No continuous playback/device/runtime/IPA approval']};write=D/'validation.json';write.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['records','limits']}))
if __name__=='__main__':main()
