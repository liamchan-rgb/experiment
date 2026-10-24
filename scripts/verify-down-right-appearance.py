#!/usr/bin/env python3
"""Check actual assembly, anatomical ownership, original rig, reflected mattes and fixed-light source registration. Art review remains separate."""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json
import numpy as np
from PIL import Image,ImageSequence
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/down-right/appearance-v1';T=R/'Art/Templates/P1-Wardrobe/down-right/v1-independent';D=R/'Art/Review/P1/modular-down-right-appearance-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
exp=mod('rightappearance',R/'scripts/export-down-right-appearance.py');left=exp.left;compose=exp.compose
read=lambda p:np.array(Image.open(p).convert('RGBA'))
solid=lambda a:a[:,:,3]>128
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
flip=lambda a:a[:,::-1].copy()
cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['baseTemplate'];base=json.loads((B/'asset.json').read_text());old=json.loads((B/'motion.json').read_text());motion=json.loads((T/'motion.json').read_text());catalog=json.loads((T/'catalog.json').read_text());assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256']
for asset in catalog['assets']:assert not compose.contract.check_asset(R/asset['manifest']),asset['id']
for f,g in zip(old['frames'],motion['frames']):
 for key in set(f)-{'drawOrder','artApproval'}:assert f[key]==g[key],('body motion changed',key)
 assert [s for s in g['drawOrder'] if s in base['slots']]==f['drawOrder']
profile=json.loads((R/'Art/Standards/P1-Parts-v1/profile.json').read_text());baseline=json.loads((D/'baseline-profile.json').read_text());without=copy.deepcopy(profile);without['headLayouts'].pop('down-right');assert without==baseline,'existing profile fields modified'
comp=compose.Compositor(R,T/'catalog.json',T/'motion.json');LT=R/'Art/Templates/P1-Wardrobe/down-left/v1-independent';lcomp=compose.Compositor(R,LT/'catalog.json',LT/'motion.json');LB=R/'Art/Templates/P1-Neutral/down-left/walk-r1';lbase=json.loads((LB/'asset.json').read_text());lc=json.loads((R/cfg['wardrobeSource']/'authoring.json').read_text());yy,xx=np.mgrid[:256,:256]
def maskim(m):
 a=np.zeros((256,256,4),np.uint8);a[m]=255;return Image.fromarray(a)
required={'torso':maskim(solid(read(LB/'source/shirt.png'))&(yy>=130)),'shorts':maskim(solid(read(LB/'source/pants.png')))}
for side in ['left','right']:
 required['leg.'+side]=Image.open(LB/'source'/('leg.'+side+'.png')).convert('RGBA');required['arm.'+side]=maskim(solid(read(LB/'source'/('arm.'+side+'.png')))&(yy>=131)&(yy<=(165 if side=='left' else 159))&~solid(read(LB/'source'/('hand.'+side+'.png'))))
records=[];hands=faces=coverage=swordChecks=bodyLayers=reflectedLayers=0;light=json.loads((D/'lighting-bake.json').read_text());assert cfg['relightEnabled'] and all(v['alphaDifferencePixels']==0 and v['rgbChangedPixels']>0 for v in light['records'])
for i,f in enumerate(motion['frames']):
 assert np.array_equal(np.array(comp.render(base['id'],[],'down-right',f['clip'],f['frame'])),read(B/'frames'/f'{i:02}.png'))
 needed={k:flip(solid(np.array(left.uv_sample(im,'shirt' if k in ['torso','shorts'] else k,i,lc)))) for k,im in required.items()};handmask=left.visible_hands(B,old['frames'][i],i)
 for outfit,hair,face,sword in itertools.product(['forester','wayfarer'],['chestnut','silver'],['blue','amber'],[False,True]):
  selected=['p1-down-right-'+outfit+'-v1','p1-down-right-lower-v1','p1-hair-'+hair+'-down-right-v1','p1-face-'+face+'-down-right-v1']+(['p1-down-right-back-scabbard-v1'] if sword else []);layers=dict(comp.layers(base['id'],selected,'down-right',f['clip'],f['frame']));a=np.array(comp.render(base['id'],selected,'down-right',f['clip'],f['frame']));key=f'{outfit}__{hair}__{face}__'+('back' if sword else 'empty');assert np.array_equal(a,read(D/'combinations'/key/f'{i:02}.png')),(i,key,'saved pose differs');assert label(solid(a),np.ones((3,3)))[1]==1,(i,key,'disconnected character')
  outfitAlpha=np.zeros((256,256),bool);lsel=[v.replace('down-right','down-left') for v in selected if 'scabbard' not in v];llayers=dict(lcomp.layers(lbase['id'],lsel,'down-left',f['clip'],f['frame']))
  for slot,im in layers.items():
   part=np.array(im)
   if slot in base['slots']:assert np.array_equal(part,read(B/'layers'/f'{i:02}'/(slot+'.png'))),(i,key,slot,'original body changed');bodyLayers+=1
   elif slot!='weapon.back':
    original=np.array(llayers[exp.side(slot)]);assert np.array_equal(part[:,:,3],flip(original[:,:,3])),(i,key,slot,'reflected alpha differs');reflectedLayers+=1
    if slot.startswith('face.'):assert np.array_equal(part,flip(original)),(i,key,slot,'features changed beyond reflection')
   if slot.startswith('outfit.'):outfitAlpha|=solid(part)
  for part,m in needed.items():
   missing=m&~outfitAlpha&~handmask;assert not missing.any(),(i,key,part,'clothing hole',np.argwhere(missing).tolist());coverage+=1
  for side in ['left','right']:
   hand=np.array(layers['body.hand.'+side]);visible=solid(hand)&handmask;assert np.array_equal(a[visible],hand[visible]),(i,key,side,'hand clipped');hands+=1
  for slot in ['face.eyes','face.nose','face.mouth']:
   part=np.array(layers[slot]);m=solid(part);assert m.any() and np.array_equal(a[m],part[m]),(i,key,slot,'feature lost');faces+=1
  if sword:
   empty=np.array(comp.render(base['id'],selected[:-1],'down-right',f['clip'],f['frame']));changed=np.any(a!=empty,axis=2);weapon=solid(np.array(layers['weapon.back']));assert changed.any() and not (changed&~weapon).any();assert not (changed&handmask).any() and not (changed&solid(np.array(layers['head.base']))).any(),(i,key,'sword changes head or hand');assert not (changed&(yy>=140)).any(),(i,key,'known rejected thigh-side sword tip');swordChecks+=1
  records.append({'pose':i,'combination':key,'actualCompositorDifferencePixels':0,'clothingCoverageGaps':0,'bodyLayersUnchanged':True,'mirroredSemanticMattesPreserved':True,'faceAndHandsPreserved':True})
for name,durations in [('outfits-walk-120ms.gif',[120]*8),('outfits-start-stop-120ms.gif',[480]+[120]*20+[480])]:
 with Image.open(D/name) as g:assert g.n_frames==len(durations) and [im.info['duration'] for im in ImageSequence.Iterator(g)]==durations and g.info['loop']==0
lightingMeasurements=[]
for name in ['hair-chestnut','hair-silver']:
 a=read(P/cfg['relight']['textureRoot']/name/'hair.front.png');m=solid(a);brightness=a[:,:,:3].mean(2);ys,xs=np.where(m&(brightness>=np.quantile(brightness[m],.85)));center=float(np.where(m)[1].mean());assert xs.mean()<center-3,(name,'fixed left highlight not retained');lightingMeasurements.append({'part':name,'brightest15PercentCenterX':float(xs.mean()),'hairCenterX':center})
for name in ['forester','wayfarer']:
 brightness={}
 for side in ['right','left']:
  a=read(P/cfg['relight']['textureRoot']/name/('outfit.sleeve.'+side+'.png'));m=solid(a)&(yy>=133)&(yy<=147)&(a[:,:,:3].max(2)>55);brightness[side]=float(a[:,:,:3].mean(2)[m].mean())
 assert brightness['right']>brightness['left'],(name,'near-left-screen shoulder should catch upper-left light');lightingMeasurements.append({'part':name,'nearRightSleeveMean':brightness['right'],'farLeftSleeveMean':brightness['left']})
(D/'lighting-measurements.json').write_text(json.dumps({'scope':'Source highlight/shoulder sanity checks supplement visual review; no artwork approval','measurements':lightingMeasurements},indent=2)+'\n')
preserved=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/p)==h for p,h in preserved.items()),'old artwork/source changed'
result={'status':'technical-checks-pass','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'manifestsChecked':len(catalog['assets']),'combinations':16,'actualCompositorPoses':len(records),'bareBodyPosesUnchanged':13,'unchangedBodyLayerChecks':bodyLayers,'reflectedAppearanceAlphaChecks':reflectedLayers,'coverageChecks':coverage,'handPreservationChecks':hands,'facePreservationChecks':faces,'weaponToggleChecks':swordChecks,'preservedFiles':len(preserved),'sourceLight':'upper-left','profileChange':'Only new down-right head layout data','poses':records,'limits':['Whole-body visual frame review is separate from technical checks','Still viewer: no continuous playback claim','Current right-down appearance only; no female, other missing modules, App/device or IPA approval']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['poses','limits']}))
