#!/usr/bin/env python3
"""Audit independent upper-diagonal outfit combinations using the public compositor."""
from pathlib import Path
import hashlib,importlib.util,itertools,json
import numpy as np
from PIL import Image,ImageDraw,ImageSequence
from scipy.ndimage import label,binary_dilation
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/upper/nape-v4';T=R/'Art/Templates/P1-Wardrobe/upper/v6-matched-back-carry';D=R/'Art/Review/P1/modular-upper-wardrobe-v6'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=module('compose',R/'scripts/compose-character-parts.py');preview=module('preview',R/'scripts/export-neutral-direction.py')
def asset_id(n):
 if n=='back-scabbard':return 'p1-upper-back-carry-v6'
 return 'p1-upper-lower-v2' if n=='lower' else 'p1-upper-'+n+'-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mask(im):return np.array(im)[:,:,3]>128
def visibility(layers):
 out={};trans=np.ones((256,256))
 for slot,im in layers[::-1]:
  a=np.array(im)[:,:,3]/255;out[slot]=a*trans;trans*=1-a
 return out
def main():
 entries=json.loads((T/'catalog.json').read_text())['assets'];checks=[]
 for entry in entries:
  errors=compose.contract.check_asset(R/entry['manifest']);assert not errors,(entry['id'],errors);checks.append({'id':entry['id'],'manifestSHA256':sha(R/entry['manifest'])})
 records=[];neutral=0;coverageChecks=0;handChecks=0;weaponChecks=0;crossing=[];yy,xx=np.mgrid[:256,:256];configs=list(itertools.product(['forester','wayfarer'],['hair-chestnut','hair-silver'],[False,True]))
 for direction in ['up-left','up-right']:
  B=R/f'Art/Templates/P1-Neutral/{direction}/walk-r6-transitions';base='p1-neutral-'+direction+'-r8-nape-gradient';comp=compose.Compositor(R,T/'catalog.json',T/(direction+'-motion.json'));original=json.loads((B/'motion.json').read_text());m=comp.motion
  for old,new in zip(original['frames'],m['frames']):
   assert {k:v for k,v in old.items() if k not in ['drawOrder','artApproval']}=={k:v for k,v in new.items() if k not in ['drawOrder','artApproval']};assert [s for s in new['drawOrder'] if s in old['drawOrder']]==old['drawOrder']
  for idx,f in enumerate(m['frames']):
   nude=comp.render(base,[],direction,f['clip'],f['frame']);assert np.array_equal(np.array(nude),np.array(Image.open(P/('base-'+direction)/'frames'/f'{idx:02}.png')))
   oldImage=np.array(Image.open(B/'frames'/f'{idx:02}.png'));newImage=np.array(nude);assert np.array_equal(oldImage[:,:,3],newImage[:,:,3]);assert np.array_equal(oldImage[134:],newImage[134:]);neutral+=1
   allowed=np.zeros((256,256),bool)
   for slot in original['frames'][idx]['drawOrder']:
    originalLayer=np.array(Image.open(B/'layers'/f'{idx:02}'/(slot+'.png')));currentLayer=np.array(Image.open(P/('base-'+direction)/'png'/f'{idx:02}'/(slot+'.png')));assert np.array_equal(originalLayer[:,:,3],currentLayer[:,:,3]);difference=np.any(originalLayer!=currentLayer,axis=2)
    if slot not in ['head.base','body.torso']:assert not difference.any()
    allowed|=difference
   originalLayers=comp.layers(base,[],direction,f['clip'],f['frame']);originalVis=visibility(originalLayers);baseLayers=dict(originalLayers)
   for outfit,hair,sword in configs:
    parts=[outfit,'lower',hair]+(['back-scabbard'] if sword else []);selected=[asset_id(n) for n in parts];layers=comp.layers(base,selected,direction,f['clip'],f['frame']);vis=visibility(layers);image=comp.render(base,selected,direction,f['clip'],f['frame']);a=np.array(image);solid=mask(image);assert label(solid,np.ones((3,3)))[1]==1,(direction,outfit,hair,sword,idx,'whole visible orphan')
    for slot,im in originalLayers:
     if not slot.startswith('body.') or slot.startswith('body.hand.'):continue
     uncovered=vis[slot]>.05
     if slot=='body.torso':
      # Only the anatomical neck is exposed; no undershirt white may remain.
      rgba=np.array(im).astype(float);r,g,b,al=[rgba[:,:,i] for i in range(4)];white=(r<b*1.15)&(g<b*1.15)&(b>70)&(al>128);assert not (uncovered&white).any(),(direction,outfit,idx,'undershirt edge')
      uncovered&=yy>=132
     assert not uncovered.any(),(direction,outfit,hair,sword,idx,slot,'uncovered body',np.argwhere(uncovered).tolist()[:12]);coverageChecks+=1
    for side in ['left','right']:
     slot='body.hand.'+side;hand=np.array(baseLayers[slot]);target=(originalVis[slot]>.99)&(hand[:,:,3]>128);assert np.array_equal(a[target],np.array(nude)[target]),(direction,outfit,idx,side,'original hand clipped');handChecks+=1
    # Clothing occlusion can split a layer. Any tiny residual must be completely hidden.
    for slot,im in layers:
     if not slot.startswith('outfit.'):continue
     labels,n=label(mask(im),np.ones((3,3)))
     if n>1:
      sizes=np.bincount(labels.ravel());sizes[0]=0;primary=int(sizes.argmax())
      for component in range(1,n+1):
       if component==primary:continue
       assert not (vis[slot][labels==component]>.05).any(),(direction,outfit,idx,slot,'visible detached clothing fragment');crossing.append({'direction':direction,'outfit':outfit,'index':idx,'slot':slot,'hiddenPixels':int(sizes[component])})
    if sword:
     plain=comp.render(base,[asset_id(n) for n in [outfit,'lower',hair]],direction,f['clip'],f['frame']);w=dict(layers)['weapon.back'];changed=np.any(a!=np.array(plain),axis=2);assert not (changed&~(np.array(w)[:,:,3]>0)).any();assert int(changed.sum())>45,(direction,idx,'back weapon not visible');weaponChecks+=1
    key=outfit+'-'+hair+'-'+('sword' if sword else 'empty');out=D/'combinations'/direction/key;out.mkdir(parents=True,exist_ok=True);path=out/f'{idx:02}.png';image.save(path)
    previous=np.array(Image.open(R/'Art/Review/P1/modular-upper-wardrobe-v4/combinations'/direction/key/f'{idx:02}.png'));oldWeapon=np.array(Image.open(R/'Art/Parts/P1-v1/upper/wardrobe-v1/back-scabbard/png'/direction/f'{idx:02}'/'weapon.back.png'))[:,:,3]>0;newWeapon=np.array(dict(layers)['weapon.back'])[:,:,3]>0 if sword else np.zeros((256,256),bool);allowedWeapon=oldWeapon|newWeapon
    assert not (np.any(previous!=a,axis=2)&~allowedWeapon).any(),(direction,idx,'Change escaped weapon footprint')
    if not sword or direction=='up-left':assert np.array_equal(previous,a)
    if sword and direction=='up-right':
     for side in ['right']:
      sleeve=np.array(dict(layers)['outfit.sleeve.'+side])[:,:,3]>128;assert not (sleeve&newWeapon).any(),(direction,idx,outfit,side,'Sword still intersects sleeve envelope')
     visible=vis['weapon.back']>.05;assert label(visible,np.ones((3,3)))[1]==1,(direction,idx,'Sheath visible discontinuity')
     leftWeapon=np.array(Image.open(R/'Art/Parts/P1-v1/upper/wardrobe-v1/back-scabbard/png/up-left'/f'{idx:02}'/'weapon.back.png'));assert np.array_equal(np.array(dict(layers)['weapon.back']),leftWeapon[:,::-1]),(idx,'Right carry differs from left reference')
    records.append({'direction':direction,'outfit':outfit,'hair':hair,'sword':sword,'index':idx,'path':str(path.relative_to(D)),'sha256':sha(path)})
  for outfit,hair in [('forester','hair-chestnut'),('wayfarer','hair-silver')]:
   out=D/direction/outfit;board=Image.new('RGB',(1024,1024),'#17372c');draw=ImageDraw.Draw(board)
   for idx,f in enumerate(m['frames']):
    image=Image.open(D/'combinations'/direction/(outfit+'-'+hair+'-sword')/f'{idx:02}.png').convert('RGBA');image.save(out/f'{idx:02}.png');x,y=idx%4*256,idx//4*256;board.paste(preview.flatten(image),(x,y));draw.text((x+5,y+5),f"{idx:02} {f['clip']}",fill='white')
   board.save(out/'all-poses-1x.png');board.resize((2048,2048),Image.Resampling.NEAREST).save(out/'all-poses-2x.png')
 # Four whole characters: outfit rows, direction columns. Same timing everywhere.
 frames=[]
 for idx in range(13):
  frame=Image.new('RGBA',(512,512))
  for row,outfit in enumerate(['forester','wayfarer']):
   for col,direction in enumerate(['up-left','up-right']):frame.alpha_composite(Image.open(D/direction/outfit/f'{idx:02}.png').convert('RGBA'),(col*256,row*256))
  frames.append(frame)
 preview.gif(frames[1:9],D/'outfits-walk-120ms.gif');sequence=[0,9,10]+list(range(1,9))*2+[11,12,0];preview.gif([frames[i] for i in sequence],D/'outfits-start-stop-120ms.gif',[480]+[120]*20+[480]);preview.flatten(frames[0],2).save(D/'outfits-idle-2x.png')
 # Crossed hair/outfit selections in full-body context.
 board=Image.new('RGB',(1024,512),'#17372c');draw=ImageDraw.Draw(board)
 for row,direction in enumerate(['up-left','up-right']):
  for col,(outfit,hair) in enumerate(itertools.product(['forester','wayfarer'],['hair-chestnut','hair-silver'])):
   image=Image.open(D/'combinations'/direction/(outfit+'-'+hair+'-sword')/'00.png').convert('RGBA');board.paste(preview.flatten(image),(col*256,row*256));draw.text((col*256+5,row*256+5),direction+' '+outfit+' '+hair,fill='white')
 board.save(D/'cross-combinations-1x.png');board.resize((2048,1024),Image.Resampling.NEAREST).save(D/'cross-combinations-2x.png')
 timing=[]
 for name,expected in [('outfits-walk-120ms.gif',[120]*8),('outfits-start-stop-120ms.gif',[480]+[120]*20+[480])]:
  with Image.open(D/name) as im:durations=[f.info['duration'] for f in ImageSequence.Iterator(im)];assert durations==expected and im.info['loop']==0
  timing.append({'file':name,'durationsMs':durations,'sha256':sha(D/name)})
 result={'status':'offline-combination-checks-pass','artApproval':None,'repairAndReviewOwner':'root','subagentsUsed':False,'assetManifests':checks,'combinations':16,'actualCompositorPoses':len(records),'neutralPosesWithUnchangedGeometry':neutral,'combinationsUnchangedOutsideWeapon':len(records),'coverageChecks':coverageChecks,'coverageFailures':0,'originalVisibleHandChecks':handChecks,'handPreservationFailures':0,'backWeaponToggleChecks':weaponChecks,'visibleClothingOrphans':0,'fullyHiddenOcclusionFragments':crossing,'normalGifTiming':timing,'records':records,'limits':['Main still-frame review does not imply continuous-player viewing','No user wardrobe approval or App/device/IPA test','Two upper rear directions; facial features are occluded, not invented','Existing neutral hidden anatomy is not claimed complete']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['combinations','actualCompositorPoses','neutralPosesWithUnchangedGeometry','coverageFailures','handPreservationFailures','visibleClothingOrphans']}))
if __name__=='__main__':main()
