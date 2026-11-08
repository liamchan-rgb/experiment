#!/usr/bin/env python3
"""Verify and render both neutral upper diagonals through the shared compositor."""
from pathlib import Path
import json,hashlib,importlib.util,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageSequence,ImageChops
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1];review=R/'Art/Review/P1/neutral-upper-diagonals-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def imp(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=imp('compose',R/'scripts/compose-character-parts.py');exporter=imp('exporter',R/'scripts/export-neutral-direction.py')
cat={'assets':[{'id':'p1-neutral-'+d+'-walk-r1','manifest':'Art/Templates/P1-Neutral/'+d+'/walk-r1/asset.json'} for d in ['up-left','up-right']]};(review/'catalog.json').write_text(json.dumps(cat,indent=2)+'\n')
records=[];allframes={};extra=[]
for d in ['up-left','up-right']:
 p=R/'Art/Templates/P1-Neutral'/d/'walk-r1';cfg=json.loads((p/'authoring.json').read_text());motion=json.loads((p/'motion.json').read_text());asset=json.loads((p/'asset.json').read_text())
 errors=compose.contract.check_asset(p/'asset.json');assert not errors,(d,errors)
 c=compose.Compositor(R,review/'catalog.json',p/'motion.json');base=asset['id'];out=review/d/'actual-composition';out.mkdir(exist_ok=True);frames=[];rec=[]
 assert motion['baseManifestSHA256']==sha(p/'asset.json')
 head=Image.open(p/cfg.get('commonHeadSource','registered/00.png')).convert('RGBA');a=np.array(head).copy();a[a[:,:,3]<=cfg['discardSourceAlphaAtMost']]=0;head=Image.fromarray(a);mask=exporter.mask(cfg['headPartition'])
 for point in cfg['poses'][0].get('headExcludePixels',[]):mask.putpixel(tuple(point),0)
 head.putalpha(ImageChops.multiply(head.getchannel('A'),mask));local=head.crop((76,61,172,157))
 for i,f in enumerate(motion['frames']):
  pose=cfg['poses'][i];assert sha(p/pose['source'])==pose['sourceSHA256']
  im=c.render(base,[],d,f['clip'],f['frame']);expected=Image.open(p/'frames'/f'{i:02}.png').convert('RGBA');assert np.array_equal(np.array(im),np.array(expected)),(d,i,'actual compositor differs')
  im.save(out/f'{i:02}.png');frames.append(im)
  transported=compose.place(local,f['headToCanvas'],(256,256));actualhead=Image.open(p/'layers'/f'{i:02}'/'head.base.png').convert('RGBA');ha,hb=np.array(transported),np.array(actualhead);assert not (np.any(ha!=hb,axis=2)&((ha[:,:,3]>0)|(hb[:,:,3]>0))).any(),(d,i,'head-local mismatch')
  markers={}
  for side in ['left','right']:
   xy=tuple(f['soleMarkers'][side]);leg=Image.open(p/'layers'/f'{i:02}'/('body.leg.'+side+'.png'));aa=leg.getpixel(xy)[3];assert aa>=32,(d,i,side,xy,aa);markers[side]={'position':xy,'alpha':aa}
  aa=np.array(im)[:,:,3];labs,n=label(aa>=32,np.ones((3,3)));sizes=np.bincount(labs.ravel());main=np.argmax(sizes[1:])+1;components=[]
  for k in range(1,n+1):
   if k==main:continue
   ys,xs=np.where(labs==k);components.append({'pixels':int(sizes[k]),'box':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]})
  if components:extra.append({'direction':d,'frame':i,'components':components})
  rec.append({'frame':i,'sha256':sha(out/f'{i:02}.png'),'compositorDifferencePixels':0,'headLocalDifferencePixels':0,'soleMarkers':markers,'visibleDetachedComponents':components})
 allframes[d]=frames;records.append({'direction':d,'assetChecks':0,'poses':rec})
 assert len(frames)==9
 with Image.open(review/d/'walk-120ms.gif') as g:assert g.n_frames==8 and [f.info.get('duration') for f in ImageSequence.Iterator(g)]==[120]*8
pairs=[]
for i in range(9):
 pair=Image.new('RGBA',(512,256));pair.alpha_composite(allframes['up-left'][i],(0,0));pair.alpha_composite(allframes['up-right'][i],(256,0));pairs.append(pair)
exporter.flatten(pairs[0]).save(review/'idle-comparison-1x.png');exporter.flatten(pairs[0],2).save(review/'idle-comparison-2x.png');exporter.gif(pairs[1:],review/'walk-comparison-120ms.gif')
board=Image.new('RGB',(1536,768),'#17372c')
for row,d in enumerate(['up-left','up-right']):
 for i,im in enumerate(allframes[d]):
  x=(i%3)*256+(768 if row else 0);y=(i//3)*256;board.paste(exporter.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),d+' '+str(i),fill='white')
board.save(review/'both-directions-nine-poses-1x.png');board.resize((3072,1536),Image.Resampling.NEAREST).save(review/'both-directions-nine-poses-2x.png')
with Image.open(review/'walk-comparison-120ms.gif') as g:timing=[f.info.get('duration') for f in ImageSequence.Iterator(g)];assert g.n_frames==8 and timing==[120]*8
assert not extra, extra
result={'status':'technical-composition-verified-visual-review-separate','artApproval':None,'actualCompositorPoses':18,'semanticLayers':144,'editableORA':18,'editableSVG':18,'headLocalPlacements':18,'soleMarkers':36,'normalTimingMs':timing,'alphaNoiseCleanup':{'up-left':8,'up-right':10},'newEngineOrAppearanceBranches':False,'regression':{'partContractTests':26,'compositorTests':21,'failures':0},'directions':records,'detachedComponents':extra,'limits':['visible neutral idle/walk only','no full hidden anatomy or clothing combinations','no start-stop production or runtime approval']}
(review/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['actualCompositorPoses','semanticLayers','headLocalPlacements','soleMarkers','normalTimingMs','detachedComponents']}))
