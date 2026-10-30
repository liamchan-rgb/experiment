#!/usr/bin/env python3
"""Reflect the retained left body/attachments together and transfer tool-painted lighting RGB only."""
from pathlib import Path
import copy,hashlib,importlib.util,json,math,re
import numpy as np
from PIL import Image,ImageDraw,ImageSequence
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[1];B=R/'Art/Templates/P1-Neutral/right/walk-r1-mirror';D=R/'Art/Review/P1/neutral-right-r1-mirror'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=mod('rightcompose',R/'scripts/compose-character-parts.py');edit=mod('rightedit',R/'scripts/export-wardrobe-part.py');preview=mod('rightpreview',R/'scripts/export-neutral-direction.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def side(s):
 s=s.replace('Left','TEMP_SIDE').replace('Right','Left').replace('TEMP_SIDE','Right');return re.sub(r'\b(left|right)\b',lambda m:'right' if m[0]=='left' else 'left',s)
def mat(v):a,b,c,d,x,y=v;return np.array([[a,c,x],[b,d,y],[0,0,1]],float)
def affine(m):return [float(m[0,0]),float(m[1,0]),float(m[0,1]),float(m[1,1]),float(m[0,2]),float(m[1,2])]
def paint(original,ref,slot):
 src=np.array(original);rgb=src[:,:,:3].astype(float);ref=np.array(ref);r,g,b,a=[ref[:,:,i].astype(float) for i in range(4)];cr,cg,cb=[rgb[:,:,i] for i in range(3)];valid=src[:,:,3]>=128;ink=(rgb.max(2)<65)|((cg<80)&(cb<65));skin=(cr>cg+20)&(cg>cb+15)&(cr>110)&(cg>80)
 masks={'skin':(a>=128)&(r>g+25)&(g>b+25)&(r>140)&(g>90)};records=[]
 for material,region in [('skin',skin)]:
  dd,nn=distance_transform_edt(~masks[material],return_indices=True);take=valid&region&~ink&(dd<=6);src[take,:3]=ref[nn[0][take],nn[1][take],:3];records.append({'material':material,'toolRGBTransferredPixels':int(take.sum()),'oldRGBRetainedOutside6pxOrInk':int((valid&region&~take).sum()),'maximumToolSampleDistance':float(dd[take].max(initial=0))})
 return Image.fromarray(src),records
def skin_mask(a):
 r,g,b=[a[:,:,i].astype(float) for i in range(3)];return (a[:,:,3]>=128)&(r>g+20)&(g>b+15)&(r>110)&(g>80)
def skin_anchors(folder,binding):
 groups={'body.torso':['body.torso'],**{'arm.'+s:['body.arm.'+s,'body.hand.'+s] for s in ['left','right']},**{'leg.'+s:['body.leg.'+s] for s in ['left','right']}};out={}
 for group,slots in groups.items():
  colours=[]
  for slot in slots:
   a=np.array(Image.open(folder/binding['layers'][slot]).convert('RGBA'));colours.extend(a[skin_mask(a),:3])
  out[group]=np.median(colours,axis=0).tolist() if colours else [253,202,146]
 return out
def anchor_for(slot,anchors):
 if slot=='body.torso':return anchors[slot]
 prefix='arm.' if slot.startswith(('body.arm.','body.hand.')) else 'leg.'
 return anchors[prefix+slot.rsplit('.',1)[1]]
def palette_paint(original,idleRef,newslot,anchor):
 src=np.array(original);raw=np.array(idleRef);r,g,b,a=[raw[:,:,i].astype(float) for i in range(4)];valid=(a>=128)&(r>g+25)&(g>b+25)&(r>140)&(g>90);region=np.zeros((256,256),bool);near=newslot.endswith('.right') or newslot=='body.torso';box=(116,134,135,175) if near else (108,135,124,173);x,y,X,Y=box;region[y:Y,x:X]=True;yy,xx=np.where(valid&region);col=raw[yy,xx,:3];assert len(col)>20;order=np.argsort(col@np.array([.2126,.7152,.0722]),kind='stable');q=[.1,.3,.7,.9] if near else [.1,.25,.4,.65];idx=[order[int(v*(len(order)-1))] for v in q];palette=col[idx];rgb=src[:,:,:3].astype(float);take=skin_mask(src);normalised=rgb-np.array(anchor)+palette[2];dist=((normalised[:,:,None,:]-palette[None,None,:,:])**2).sum(3);chosen=dist.argmin(2);src[take,:3]=palette[chosen[take]]
 return Image.fromarray(src),[{'material':'skin','method':'static tool-sampled ramp, source median anchored to common midtone; arm and hand share anchor','sourceMedianRGB':anchor,'sourcePaletteXY':[[int(xx[j]),int(yy[j])] for j in idx],'paletteRGB':palette.tolist(),'nearSide':near,'toolRGBTransferredPixels':int(take.sum()),'originalSafetyClothingAndInkPreserved':True}]
def board(items,path,names=None):
 out=Image.new('RGB',(1024,1024),'#17372c');draw=ImageDraw.Draw(out)
 for i,im in enumerate(items):x,y=i%4*256,i//4*256;out.paste(preview.flatten(im),(x,y));draw.text((x+4,y+4),names[i] if names else f'{i:02}',fill='white')
 out.save(path);out.resize((2048,2048),Image.Resampling.NEAREST).save(path.with_name(path.stem.replace('1x','2x')+path.suffix))
def main():
 cfg=json.loads((B/'mirror-authoring.json').read_text());L=R/cfg['sourceTemplate'];a=json.loads((L/'asset.json').read_text());m=json.loads((L/'motion.json').read_text());assert sha(L/'asset.json')==cfg['sourceManifestSHA256'] and sha(L/'motion.json')==cfg['sourceMotionSHA256'];assert json.loads((R/cfg['sourceApproval']).read_text())['status']=='approved';raw=Image.open(B/cfg['lightReference']).convert('RGBA');reg=cfg['lightRegistration'];assert list(raw.size)==reg['canvas'] and sha(B/cfg['lightReference'])==cfg['lightReferenceSHA256'];s=reg['scale'];ref=raw.resize((1024,1024),Image.Resampling.NEAREST);ref.save(B/'source/relight-registered-atlas.png');F=np.array([[-1,0,255],[0,1,0],[0,0,1]],float);localF=np.array([[-1,0,95],[0,1,0],[0,0,1]],float);headRaw=Image.open(L/'layers/00/head.base.png').convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);headPaint,headRecords=paint(headRaw,ref.crop((0,0,256,256)),'head.base');headlocal=headPaint.crop((84,61,180,157));headlocal.save(B/'source/head-local-relit.png');bindings=[];poses=[];items=[];audit=[]
 for i,(binding,old) in enumerate(zip(a['bindings'],m['frames'])):
  f=copy.deepcopy(old);f.update(direction='right',facing=[1,0],drawOrder=[side(s) for s in old['drawOrder']],headToCanvas=affine(F@mat(old['headToCanvas'])@localF),joints={side(j):[255-p[0],p[1]] for j,p in old['joints'].items()},soleMarkers={side(j):[255-p[0],p[1]] for j,p in old['soleMarkers'].items()},support=side(old['support']),artApproval=None,sockets={})
  for name,v in old['sockets'].items():
   v=copy.deepcopy(v);v['position']=[255-v['position'][0],v['position'][1]]
   if 'angleDeg' in v:v['angleDeg']=(180-v['angleDeg'])%360
   f['sockets'][side(name)]=v
  parts={};paths={};transfers=[];anchors=skin_anchors(L,binding)
  for slot,p in binding['layers'].items():
   im=Image.open(L/p).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);newslot=side(slot)
   if slot=='head.base':painted=c.place(headlocal,f['headToCanvas'],(256,256));record=headRecords
   else:painted,record=palette_paint(im,ref.crop((0,0,256,256)),newslot,anchor_for(slot,anchors))
   assert np.array_equal(np.array(im)[:,:,3],np.array(painted)[:,:,3]),(i,slot,'tool changed geometry');q=B/'layers'/f'{i:02}'/(newslot+'.png');q.parent.mkdir(parents=True,exist_ok=True);painted.save(q);parts[newslot]=painted;paths[newslot]=str(q.relative_to(B));transfers.append({'slot':newslot,'method':'static head-local source' if slot=='head.base' else 'static tool-sampled skin palette; original material shading boundaries','records':record,'alphaDifferencePixels':0})
  parts={slot:parts[slot] for slot in f['drawOrder']};(B/'editable').mkdir(exist_ok=True);whole=edit.editable(B/'editable',f'{i:02}',parts);(B/'frames').mkdir(exist_ok=True);whole.save(B/'frames'/f'{i:02}.png');items.append(whole);poses.append(f);bindings.append({'direction':'right','clip':f['clip'],'frame':f['frame'],'layers':paths});audit.append({'index':i,'sourceClip':old['clip'],'sourceFrame':old['frame'],'semanticSidesExchanged':True,'allLayerAlphaDifferencePixels':0,'support':f['support'],'lightTransfers':transfers})
 asset=copy.deepcopy(a);asset.update(id=cfg['id'],version='1.0.0',directions=['right'],slots=[side(s) for s in a['slots']],bindings=bindings,sourceFiles=['mirror-authoring.json']+[str(p.relative_to(B)) for root in ['source','editable'] for p in sorted((B/root).rglob('*')) if p.is_file()]);write(B/'asset.json',asset);motion=copy.deepcopy(m);motion.update(status='right-neutral-mirror-candidate',artApproval=None,baseManifestSHA256=sha(B/'asset.json'),canvas=[256,256],frames=poses);write(B/'motion.json',motion);write(D/'catalog.json',{'assets':[{'id':cfg['id'],'manifest':str((B/'asset.json').relative_to(R))}]});write(D/'mirror-audit.json',{'authorAndReviewer':'root','subagentsUsed':False,'artApproval':None,'geometryOwner':cfg['sourceTemplate'],'toolReference':cfg['lightReference'],'referenceAlphaIgnored':True,'headSource':'single static relit96 source on unchanged head transforms','poses':audit});write(D/'sequence.json',{'indices':cfg['sequence'],'durationsMs':cfg['durationsMs'],'arbitraryPhaseInterrupts':False,'artApproval':None});board(items,D/'all-poses-fullbody-1x.png');preview.flatten(items[0],2).save(D/'idle-review-2x.png');preview.gif(items[1:9],D/'walk-120ms.gif');preview.gif([items[i] for i in cfg['sequence']],D/'start-stop-120ms.gif',cfg['durationsMs']);pair=[]
 for i,im in enumerate(items):
  p=Image.new('RGBA',(512,256));p.alpha_composite(Image.open(L/'frames'/f'{i:02}.png').convert('RGBA'));p.alpha_composite(im,(256,0));pair.append(p)
 preview.flatten(pair[0],2).save(D/'idle-comparison-2x.png');preview.gif(pair[1:9],D/'walk-comparison-120ms.gif')
 with Image.open(D/'walk-120ms.gif') as gif:decoded=[im.convert('RGBA') for im in ImageSequence.Iterator(gif)]
 out=Image.new('RGB',(2048,1024),'#17372c')
 for i,im in enumerate(decoded):out.paste(im.convert('RGB'),(i%4*512,i//4*512))
 out.save(D/'actual-gif-frames-2x.png');print('Right neutral mirrored13 poses; original alpha/rig preserved, tool RGB-only lighting')
if __name__=='__main__':main()
