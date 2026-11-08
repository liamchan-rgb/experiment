#!/usr/bin/env python3
"""Bake imagegen RGB onto unchanged reflected appearance mattes; fixed ramps prevent source-pose tone flashes."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,binary_erosion
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/right/appearance-v1';D=R/'Art/Review/P1/modular-right-appearance-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def mask(a,material):
 r,g,b,alpha=[a[:,:,i].astype(float) for i in range(4)];mx=np.maximum.reduce([r,g,b]);base=(alpha>=128)&(mx>35)
 if material=='green':return base&(g>r*1.05)&(g>b*1.05)&(g>25)
 if material=='blue':return base&(b>r*1.2)&(b>g*1.05)&(b>30)
 if material=='pants':return base&(mx-np.minimum.reduce([r,g,b])<40)&(mx<180)
 return base&(r>g*1.12)&(g>b*1.1)&(r>55)
def palette(ref,material,near):
 a=np.array(ref);m=mask(a,material);y,x=np.mgrid[:256,:256]
 if material in ['green','blue']:m&=(y>=125)&(y<194)
 elif material=='pants':m&=(y>=160)&(y<=225)
 else:m&=y>=185
 yy,xx=np.where(m);col=a[yy,xx,:3];assert len(col)>20,(material,'reference too small');order=np.argsort(col@np.array([.2126,.7152,.0722]),kind='stable');qs=[.05,.18,.32,.46,.6,.74,.88,.97] if near else [.025,.12,.23,.34,.45,.57,.69,.82];indices=[order[int(v*(len(order)-1))] for v in qs];return col[indices],[[int(xx[j]),int(yy[j])] for j in indices]
def main():
 cfg=json.loads((P/'authoring.json').read_text());records=[];sources={}
 for n,size in [('hair-chestnut',96),('hair-silver',96),('outfits',512)]:
  p=P/'source'/(n+'-relight-original.png');raw=Image.open(p).convert('RGBA');assert raw.size==(1254,1254);im=raw.resize((size,size),Image.Resampling.NEAREST);im.save(P/'source'/(n+'-relight-registered.png'));sources[n]=im
 for n in ['hair-chestnut','hair-silver']:
  folder=P/n;raw=np.array(Image.open(folder/'source/hair.front-mirrored.png').convert('RGBA'));ref=np.array(sources[n]);r,g,b,a=[ref[:,:,i].astype(float) for i in range(4)];mx=np.maximum.reduce([r,g,b]);valid=(a>=128)&(mx>40)
  if n=='hair-chestnut':valid&=(r>g*1.15)&(g>b*1.1)&(r<245)&(g>12)&(b>3)
  else:valid&=(mx-np.minimum.reduce([r,g,b])<55)&(b>r*.75)
  dist,nn=distance_transform_edt(~valid,return_indices=True);take=(raw[:,:,3]>0)&(raw[:,:,:3].max(2)>45)&(dist<=6);out=raw.copy();out[take,:3]=ref[nn[0][take],nn[1][take],:3];out[out[:,:,3]==0]=0;(folder/'relit').mkdir(exist_ok=True);Image.fromarray(out).save(folder/'relit/hair.front.png');shutil.copyfile(P/'source'/(n+'-relight-original.png'),folder/'source/relight-original.png');shutil.copyfile(P/'source'/(n+'-prompt.txt'),folder/'source/relight-prompt.txt');records.append({'package':n,'method':'one static96 tool RGB field on original hair alpha','changedPixels':int(np.any(out[:,:,:3]!=raw[:,:,:3],2).sum()),'maxSampleDistance':float(dist[take].max(initial=0)),'alphaDifferencePixels':0})
 refs={'forester':sources['outfits'].crop((0,0,256,256)),'wayfarer':sources['outfits'].crop((256,0,512,256))};lowerAnchors={}
 for kind,side in [(k,s) for k in ['pants','boots'] for s in ['left','right']]:
  colours=[]
  for i in range(13):
   a=np.array(Image.open(P/'lower/source'/f'{i:02}-outfit.{"boot" if kind=="boots" else "pants"}.{side}-mirrored.png'));m=mask(a,kind)&binary_erosion(a[:,:,3]>=128,np.ones((3,3)));colours.extend(a[m,:3])
  assert colours,(kind,side,'no material source across13');lowerAnchors[(kind,side)]=np.median(colours,axis=0)
 for name in ['forester','wayfarer','lower']:
  folder=P/name;sourceManifest=json.loads((R/cfg['sources'][name]/'asset.json').read_text());slots=[s.replace('.left','.TEMP').replace('.right','.left').replace('.TEMP','.right') for s in sourceManifest['slots']];ref=refs['forester' if name=='lower' else name]
  for i in range(13):
   originals={s:np.array(Image.open(folder/'source'/f'{i:02}-{s}-mirrored.png')) for s in slots};clothColours=[]
   if name!='lower':
    for a in originals.values():clothColours.extend(a[mask(a,'green' if name=='forester' else 'blue'),:3])
    clothAnchor=np.median(clothColours,axis=0)
   for slot,a in originals.items():
    near=not slot.endswith('.left');material=('pants' if '.pants.' in slot else 'boots') if name=='lower' else ('green' if name=='forester' else 'blue');eligible=mask(a,material);take=eligible&binary_erosion(a[:,:,3]>=128,np.ones((3,3)));pal,xy=palette(ref,material,near);anchor=(lowerAnchors[(material,slot.rsplit('.',1)[1])] if material=='boots' or not eligible.any() else np.median(a[eligible,:3],axis=0)) if name=='lower' else clothAnchor;assert np.isfinite(anchor).all();rgb=a[:,:,:3].astype(float);normalised=rgb-anchor+pal[4];chosen=((normalised[:,:,None,:]-pal[None,None,:,:])**2).sum(3).argmin(2);out=a.copy();out[take,:3]=pal[chosen[take]];out[out[:,:,3]==0]=0;q=folder/'relit'/f'{i:02}'/(slot+'.png');q.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(out).save(q);records.append({'package':name,'pose':i,'slot':slot,'material':material,'nearSide':near,'paletteRGB':pal.tolist(),'paletteXY':xy,'sourceAnchorRGB':anchor.tolist(),'anchorScope':'all13 same-side boots; preserve drawn sole contrast' if material=='boots' else 'shared whole outfit torso/sleeves' if name!='lower' else 'same-side pants per pose; all13 anchor if no exposed material','colouredInteriorPixels':int(take.sum()),'originalBoundaryTrimAndInkPreserved':True,'alphaDifferencePixels':0})
  shutil.copyfile(P/'source/outfits-relight-original.png',folder/'source/relight-original.png');shutil.copyfile(P/'source/outfits-prompt.txt',folder/'source/relight-prompt.txt')
 cfg['relightEnabled']=True;cfg['relight']={'tool':'image_gen.imagegen','sourceLight':'upper-left','head':'one static96 hair RGB source, max6px material gutter','clothes':'static8colour material ramps; whole outfit shares source median anchor','lower':'same-side pants source median; fixed all13 boot anchor preserves painted soles','alphaGeometryChanged':False,'sources':{n:{'image':'source/'+n+'-relight-original.png','sha256':sha(P/'source'/(n+'-relight-original.png')),'canvas':[1254,1254],'targetCanvas':[96,96] if n.startswith('hair') else [512,512],'scale':96/1254 if n.startswith('hair') else 512/1254,'prompt':'source/'+n+'-prompt.txt'} for n in sources}};(P/'authoring.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');(D/'lighting-bake.json').write_text(json.dumps({'status':'tool-RGB-source-bake','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'referenceGeometryImported':False,'sourceLight':'upper-left','records':records},indent=2)+'\n');print('Authored right appearance lighting:',len(records),'source layers')
if __name__=='__main__':main()
