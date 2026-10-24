#!/usr/bin/env python3
"""Verify actual outfit combinations, coverage, anatomical ownership, back-hair clearance, attachment and original rig preservation. Art review is separate."""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json
import numpy as np
from PIL import Image,ImageSequence,ImageDraw
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/up/appearance-v1';T=R/'Art/Templates/P1-Wardrobe/up/v1-independent';D=R/'Art/Review/P1/modular-up-appearance-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
exp=mod('upAppearance',R/'scripts/export-up-appearance.py');compose=exp.compose
read=lambda p:np.array(Image.open(p).convert('RGBA'))
solid=lambda a:a[:,:,3]>128
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def maskim(mask):
 a=np.zeros((256,256,4),np.uint8);a[mask]=255;return Image.fromarray(a)
def main():
 cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['baseTemplate'];base=json.loads((B/'asset.json').read_text());old=json.loads((B/'motion.json').read_text());motion=json.loads((T/'motion.json').read_text());catalog=json.loads((T/'catalog.json').read_text());assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256'];assert len(catalog['assets'])==7
 for v in catalog['assets']:assert not compose.contract.check_asset(R/v['manifest']),v['id']
 for f,g in zip(old['frames'],motion['frames']):
  for k in set(f)-{'drawOrder','artApproval'}:assert f[k]==g[k],('motion changed',k)
  assert [s for s in g['drawOrder'] if s in base['slots']]==f['drawOrder']
 profile=json.loads((R/'Art/Standards/P1-Parts-v1/profile.json').read_text());baseline=json.loads((D/'baseline-profile.json').read_text());profile['headLayouts'].pop('up');assert profile==baseline,'existing head layouts/profile changed'
 comp=compose.Compositor(R,T/'catalog.json',T/'motion.json');yy,xx=np.mgrid[:256,:256];neck=Image.new('L',(256,256));ImageDraw.Draw(neck).polygon([(121,125),(134,125),(134,130),(132,133),(124,133),(121,130)],fill=255);neck=np.array(neck)>0
 required={'torso':maskim(solid(read(B/'source/shirt.png'))&(yy>=130)&~neck),'shorts':Image.open(B/'source/pants.png').convert('RGBA')}
 for side in ['left','right']:
  required['leg.'+side]=Image.open(B/'source'/('leg.'+side+'.png')).convert('RGBA');required['arm.'+side]=maskim(solid(read(B/'source'/('arm.'+side+'.png')))&(yy>=131)&(yy<=166)&~solid(read(B/'source'/('hand.'+side+'.png'))))
 head=read(B/'source/head.base.png')[61:157,80:176];hy,hx=np.mgrid[:96,:96];region=np.zeros((96,96),bool)
 for x0,y0,x1,y1 in cfg['rearScalpCoverageRegions']:region[y0:y1,x0:x1]=True
 core=solid(head)&region;coreImage=np.zeros((96,96,4),np.uint8);coreImage[core]=255;coreImage=Image.fromarray(coreImage)
 for name in ['hair-chestnut','hair-silver']:assert not (core&~solid(read(P/name/'png/hair.front.png'))).any(),(name,'rear-crown bald holes')
 for side in ['left','right']:
  q=P/'lower/source'/('outfit.boot.'+side+'.png');flat=read(q)
  for state in ['half-rolled','rolled']:
   a=read(P/'lower/source'/('outfit.boot.'+side+'-'+state+'.png'));assert np.array_equal(a[:,:,3],flat[:,:,3]);assert np.array_equal(a[:208],flat[:208]);assert np.any(a!=flat),(side,state,'boot roll source has no effect')
 guardImage=np.zeros((256,256,4),np.uint8);x0,y0,x1,y1=cfg['weapon']['guardVisibilityBox'];guardImage[y0:y1,x0:x1]=255;guardImage=Image.fromarray(guardImage);rigAudit=json.loads((R/cfg['rigAudit']).read_text());rows=[];coverage=hands=bodyChecks=headChecks=weaponChecks=guardChecks=0
 for i,f in enumerate(motion['frames']):
  assert np.array_equal(np.array(comp.render(base['id'],[],'up',f['clip'],f['frame'])),read(B/'frames'/f'{i:02}.png')),(i,'bare body differs');handmask=exp.visible_hands(B,old['frames'][i],i);needed={n:solid(np.array(exp.uv_sample(im,'shirt' if n in ['torso','shorts'] else n,i,cfg))) for n,im in required.items()};crown=solid(np.array(compose.place(coreImage,f['headToCanvas'],(256,256))))
  for outfit,hair,sword in itertools.product(['forester','wayfarer'],['chestnut','silver'],[False,True]):
   key=f'{outfit}__{hair}__'+('back' if sword else 'empty');selected=['p1-up-'+outfit+'-v1','p1-up-lower-v1','p1-up-hair-'+hair+'-v1']+(['p1-up-back-scabbard-v1'] if sword else []);layers=dict(comp.layers(base['id'],selected,'up',f['clip'],f['frame']));a=np.array(comp.render(base['id'],selected,'up',f['clip'],f['frame']));assert np.array_equal(a,read(D/'combinations'/key/f'{i:02}.png')),(i,key,'actual assembly differs');assert label(solid(a),np.ones((3,3)))[1]==1,(i,key,'whole body disconnected');cloth=np.zeros((256,256),bool)
   for slot,im in layers.items():
    if slot in base['slots']:assert np.array_equal(np.array(im),read(B/'layers'/f'{i:02}'/(slot+'.png'))),(i,key,slot,'base layer changed');bodyChecks+=1
    if slot.startswith('outfit.'):cloth|=solid(np.array(im))
   for n,m in needed.items():
    missing=m&~cloth&~handmask;assert not missing.any(),(i,key,n,'clothing gap',np.argwhere(missing).tolist());coverage+=1
   for side in ['left','right']:
    hand=np.array(layers['body.hand.'+side]);m=solid(hand)&handmask;assert np.array_equal(a[m],hand[m]),(i,key,side,'hand clipped or changed');hands+=1
   h=np.array(layers['hair.front']);assert not (crown&~solid(h)).any() and np.array_equal(a[crown],h[crown]),(i,key,'scalp exposed/hair occluded');headChecks+=1
   if sword:
    empty=np.array(comp.render(base['id'],selected[:-1],'up',f['clip'],f['frame']));changed=np.any(empty!=a,axis=2);weapon=solid(np.array(layers['weapon.back']));assert changed.any() and not (changed&~weapon).any();assert not (changed&handmask).any() and not (changed&solid(np.array(layers['head.base']))).any() and not (changed&solid(h)).any(),(i,key,'weapon changes hand/head');weaponChecks+=1
    guard=solid(np.array(compose.place(guardImage,rigAudit['poses'][i]['partTransforms']['upper'],(256,256))))&weapon;assert guard.any() and np.array_equal(a[guard],np.array(layers['weapon.back'])[guard]),(i,key,'sleeve cuts guard/weapon upper chain');guardChecks+=1
   rows.append({'pose':i,'combination':key,'actualCompositorDifferencePixels':0,'clothingCoverageGaps':0,'handsPreserved':True,'crownExposedPixels':0,'bodyLayersUnchanged':True})
 for name,durations in [('outfits-walk-120ms.gif',[120]*8),('outfits-start-stop-120ms.gif',[480]+[120]*20+[480])]:
  with Image.open(D/name) as gif:assert gif.n_frames==len(durations) and [im.info['duration'] for im in ImageSequence.Iterator(gif)]==durations and gif.info['loop']==0
 oldfiles=json.loads((D/'preserved-files.json').read_text());assert all(sha(R/k)==h for k,h in oldfiles.items()),'old artwork changed'
 result={'status':'technical-checks-pass','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'manifestsChecked':7,'combinations':8,'actualCompositorPoses':len(rows),'bareBodyPosesUnchanged':13,'bodyLayerPreservationChecks':bodyChecks,'clothingCoverageChecks':coverage,'handPreservationChecks':hands,'crownCoverageChecks':headChecks,'weaponToggleChecks':weaponChecks,'guardVisibilityChecks':guardChecks,'preservedFiles':len(oldfiles),'profileChange':'Only new up back-head guide data; all old entries unchanged','footRollSourceAlphaUnchanged':True,'records':rows,'limits':['Main full-body artwork review is separate; numerical pass is not user art approval','Two colourways share one short back-hair silhouette; generated silver RGB is independently registered','Still viewer: complete images/GIF timing only, no continuous playback claim','Current up appearance candidate only; down sync gap/right adaptation/eight-direction integration/App/device/IPA not completed']};(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['records','limits']}))
if __name__=='__main__':main()
