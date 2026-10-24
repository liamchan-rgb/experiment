#!/usr/bin/env python3
"""Independent back hair/clothes/boots/back-carry on the unchanged up body and motion. Imagegen pigment, neutral-owned mattes/UVs, generic composition."""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageSequence
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/up/appearance-v1';T=R/'Art/Templates/P1-Wardrobe/up/v1-independent';D=R/'Art/Review/P1/modular-up-appearance-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
baseExp=mod('upbase',R/'scripts/export-up-layered-motion.py');compose=baseExp.compose;edit=baseExp.edit;preview=baseExp.preview;headEdit=mod('headEdit',R/'scripts/export-character-head-part.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def uv_sample(image,source,i,cfg):
 uv=np.array(Image.open(R/cfg['sourceUV']/f'{i:02}'/(source+'.png')).convert('RGBA'));a=np.array(image);out=a[uv[:,:,1],uv[:,:,0]].copy();out[uv[:,:,3]==0]=0;return Image.fromarray(out)
def visible_hands(B,f,i):
 transmission=np.ones((256,256));mask=np.zeros((256,256),bool)
 for slot in reversed(f['drawOrder']):
  alpha=np.array(Image.open(B/'layers'/f'{i:02}'/(slot+'.png')))[:,:,3]/255
  if slot.startswith('body.hand.'):mask|=(alpha>0)&(transmission>.99)
  transmission*=1-alpha
 return mask
mapping={'outfit.torso':'shirt','outfit.sleeve.left':'arm.left','outfit.sleeve.right':'arm.right','outfit.pants.left':'leg.left','outfit.pants.right':'leg.right','outfit.boot.left':'leg.left','outfit.boot.right':'leg.right'}

def main():
 cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['baseTemplate'];base=json.loads((B/'asset.json').read_text());motion=json.loads((B/'motion.json').read_text());assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256'];audit=json.loads((R/cfg['rigAudit']).read_text());T.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True);paints={};records=[]
 for n,v in cfg['paintSources'].items():
  raw=Image.open(P/v['image']).convert('RGBA');assert list(raw.size)==v['canvas'] and sha(P/v['image'])==v['sha256'];s=v['scale'];x,y=v['translation'];im=raw.transform(tuple(v['targetCanvas']),Image.Transform.AFFINE,(1/s,0,-x/s,0,1/s,-y/s),Image.Resampling.NEAREST);im.save(P/'source'/(n+'-registered.png'));paints[n]=im
 yy,xx=np.mgrid[:256,:256];sources={};bootSources={}
 for pack,slots in cfg['matteSources'].items():
  folder=P/pack;(folder/'source').mkdir(parents=True,exist_ok=True);sources[pack]={}
  for slot,path in slots.items():
   a=np.array(paints['forester' if pack=='lower' else pack]);mask=np.array(Image.open(P/path))[:,:,3]>128;valid=a[:,:,3]>=128;dist,nearest=distance_transform_edt(~valid,return_indices=True);missing=mask&~valid;assert dist[missing].max(initial=0)<=cfg['maxPaintGutterPixels'],(pack,slot,'RGB outside registered source',float(dist[missing].max(initial=0)));a[missing,:3]=a[nearest[0][missing],nearest[1][missing],:3]
   if slot.startswith('outfit.pants.'):
    r,g,b,al=[np.array(paints['forester'])[:,:,i].astype(float) for i in range(4)];grey=(al>=128)&(yy>=166)&(yy<=201)&(np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b])<35)&(np.maximum.reduce([r,g,b])>=35)&(np.maximum.reduce([r,g,b])<160);dd,nn=distance_transform_edt(~grey,return_indices=True);waist=mask&(yy<=167);assert dd[waist].max(initial=0)<=14;raw=np.array(paints['forester']);a[waist,:3]=raw[nn[0][waist],nn[1][waist],:3]
   a[~mask]=0;a[mask,3]=255;im=Image.fromarray(a);im.save(folder/'source'/(slot+'.png'));sources[pack][slot]=im;records.append({'pack':pack,'slot':slot,'alphaOwner':path,'gutterPixels':int(missing.sum()),'maxGutterDistance':float(dist[missing].max(initial=0)),'originalBodyGeometryChanged':False})
   if slot.startswith('outfit.boot.'):
    ref=np.array(paints['boot-roll']);valid=ref[:,:,3]>=128;dd,nn=distance_transform_edt(~valid,return_indices=True);bootSources[slot]={}
    for state,ymin in [('half-rolled',214),('rolled',208)]:
     out=a.copy();take=mask&(yy>=ymin)&(a[:,:,:3].max(2)>55)&(dd<=2);out[take,:3]=ref[nn[0][take],nn[1][take],:3];im=Image.fromarray(out);im.save(folder/'source'/(slot+'-'+state+'.png'));bootSources[slot][state]=im
 for n in ['hair-chestnut','hair-silver']:
  folder=P/n;(folder/'png').mkdir(parents=True,exist_ok=True);(folder/'source').mkdir(exist_ok=True);owner=cfg['hairMattePaintSource'][n];a=np.array(paints[n]);matte=np.array(paints[owner])[:,:,3]>=128;valid=a[:,:,3]>=128;dd,nn=distance_transform_edt(~valid,return_indices=True);missing=matte&~valid;assert dd[missing].max(initial=0)<=cfg['hairRGBGutterPixels'];a[missing,:3]=a[nn[0][missing],nn[1][missing],:3];a[~matte]=0;a[matte,3]=255;im=Image.fromarray(a);im.save(folder/'png/hair.front.png');headEdit.editable(folder,{'hair.front':im});sources[n]={'hair.front':im};shutil.copyfile(P/cfg['paintSources'][owner]['image'],folder/'source/shape-original.png');records.append({'pack':n,'slot':'hair.front','alphaOwner':owner,'RGBGutterPixels':int(missing.sum()),'maxRGBGutterDistance':float(dd[missing].max(initial=0)),'bodyHeadChanged':False})
 w=cfg['weapon'];raw=Image.open(P/w['source']).convert('RGBA');assert sha(P/w['source'])==w['sha256'];a,b=map(lambda v:np.array(v,float),w['sourceLandmarks']);A,Bb=map(lambda v:np.array(v,float),w['targetLandmarks']);u=(b-a)/np.linalg.norm(b-a);v=(Bb-A)/np.linalg.norm(Bb-A);linear=np.outer(v,u)*np.linalg.norm(Bb-A)/np.linalg.norm(b-a)+np.outer([-v[1],v[0]],[-u[1],u[0]])*w['transverseScale'];wm=np.eye(3);wm[:2,:2]=linear;wm[:2,2]=A-linear@a;weapon=compose.place(raw,baseExp.affine(wm),(256,256));a=np.array(weapon);a[a[:,:,3]<128]=0;a[a[:,:,3]>=128,3]=255;weapon=Image.fromarray(a);(P/'back-scabbard/source').mkdir(parents=True,exist_ok=True);weapon.save(P/'back-scabbard/source/weapon.back.png')
 slots={n:list(v) for n,v in sources.items()};slots['back-scabbard']=['weapon.back'];ids={n:'p1-up-'+n+'-v1' for n in slots};bindings={n:[] for n in slots};catalog=[{'id':base['id'],'manifest':str((B/'asset.json').relative_to(R))}]
 for i,f in enumerate(motion['frames']):
  mask=visible_hands(B,f,i)
  for pack in slots:
   head=pack.startswith('hair');out=P/pack/'png'/f'{i:02}';layers={};paths={}
   if not head:out.mkdir(parents=True,exist_ok=True)
   for slot in slots[pack]:
    if head:paths[slot]='png/'+slot+'.png';continue
    if pack=='back-scabbard':im=compose.place(weapon,audit['poses'][i]['partTransforms']['upper'],(256,256))
    else:
     src=sources[pack][slot]
     if slot.startswith('outfit.boot.'):
      side=slot.rsplit('.',1)[1];state=audit['poses'][i]['contacts'][side]['footArtState']
      if state!='flat':src=bootSources[slot][state]
     im=uv_sample(src,mapping[slot],i,cfg);a=np.array(im);a[mask]=0;im=Image.fromarray(a)
    im.save(out/(slot+'.png'));layers[slot]=im;paths[slot]=str((out/(slot+'.png')).relative_to(P/pack))
   if not head:(P/pack/'editable').mkdir(exist_ok=True);edit.editable(P/pack/'editable',f'{i:02}',layers)
   bindings[pack].append({'direction':'up','clip':f['clip'],'frame':f['frame'],'layers':paths})
  order=[]
  for slot in f['drawOrder']:
   if slot=='head.base':order.append('weapon.back')
   order.append(slot)
   if slot.startswith('body.arm.'):order.append(slot.replace('body.arm.','outfit.sleeve.'))
   if slot=='body.torso':order+=['outfit.pants.left','outfit.boot.left','outfit.pants.right','outfit.boot.right','outfit.torso']
   if slot=='head.base':order.append('hair.front')
  f['drawOrder']=order;f['artApproval']=None
 for pack in slots:
  folder=P/pack;(folder/'source').mkdir(exist_ok=True);tag=pack if pack in cfg['paintSources'] else 'forester';src=cfg['weapon']['source'] if pack=='back-scabbard' else cfg['paintSources'][tag]['image'];shutil.copyfile(P/src,folder/'source/original.png')
  prompt=cfg['paintSources'][tag]['prompt']
  if pack=='back-scabbard':(folder/'source/prompt.txt').write_text('Existing independent sword reused; fixed physical right-shoulder diagonal landmarks in parent authoring.json. No new sword drawing.\n')
  else:shutil.copyfile(P/prompt,folder/'source/prompt.txt')
  if pack=='lower':
   shutil.copyfile(P/cfg['paintSources']['boot-roll']['image'],folder/'source/boot-roll-original.png');shutil.copyfile(P/cfg['paintSources']['boot-roll']['prompt'],folder/'source/boot-roll-prompt.txt')
  (folder/'authoring.json').write_text(json.dumps({'id':ids[pack],'registrationOwner':'../authoring.json (parent bundle record)','baseBodyUnchanged':True,'artApproval':None,'authorAndReviewer':'root','sourcePaint':src},indent=2)+'\n')
  head=pack.startswith('hair');manifest={'schemaVersion':'1.0.0','id':ids[pack],'version':'1.0.0','part':'hair' if head else 'weapon' if pack=='back-scabbard' else 'outfit','compatibility':base['compatibility'],'mode':'head-local' if head else 'pose-map','slots':slots[pack],'directions':['up'],'clips':base['clips'],'bindings':bindings[pack],'sourceFiles':['authoring.json']+[str(q.relative_to(folder)) for sub in ['source','editable'] for q in sorted((folder/sub).rglob('*')) if q.is_file()]}
  if head:manifest['sourceFiles']+=['editable.ora','editable.svg']
  if pack=='back-scabbard':manifest['carryProfile']='back-scabbard'
  (folder/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n');catalog.append({'id':ids[pack],'manifest':str((folder/'asset.json').relative_to(R))})
 motion.update(status='up-independent-appearance-candidate',artApproval=None);(T/'motion.json').write_text(json.dumps(motion,indent=2)+'\n');(T/'catalog.json').write_text(json.dumps({'assets':catalog},indent=2)+'\n');(D/'paint-registration.json').write_text(json.dumps({'mattesOwnedByNeutral':True,'originalBodyOrRigChanged':False,'records':records},indent=2)+'\n');comp=compose.Compositor(R,T/'catalog.json',T/'motion.json');rendered={}
 for outfit,hair,sword in itertools.product(['forester','wayfarer'],['chestnut','silver'],[False,True]):
  key=f'{outfit}__{hair}__'+('back' if sword else 'empty');out=D/'combinations'/key;out.mkdir(parents=True,exist_ok=True);frames=[];selected=[ids[outfit],ids['lower'],ids['hair-'+hair]]+([ids['back-scabbard']] if sword else [])
  for i,f in enumerate(motion['frames']):im=comp.render(base['id'],selected,'up',f['clip'],f['frame']);im.save(out/f'{i:02}.png');frames.append(im)
  rendered[key]=frames
  if sword:
   board=Image.new('RGB',(1024,1024),'#17372c')
   for i,im in enumerate(frames):x,y=i%4*256,i//4*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white')
   board.save(out/'all-poses-fullbody-1x.png');board.resize((2048,2048),Image.Resampling.NEAREST).save(out/'all-poses-fullbody-2x.png')
 pairs=[]
 for i in range(13):
  im=Image.new('RGBA',(512,256));im.alpha_composite(rendered['forester__chestnut__back'][i]);im.alpha_composite(rendered['wayfarer__silver__back'][i],(256,0));pairs.append(im)
 preview.flatten(pairs[0],2).save(D/'outfits-idle-2x.png');preview.gif(pairs[1:9],D/'outfits-walk-120ms.gif');preview.gif([pairs[i] for i in [0,9,10]+list(range(1,9))*2+[11,12,0]],D/'outfits-start-stop-120ms.gif',[480]+[120]*20+[480]);board=Image.new('RGB',(2048,2048),'#17372c')
 with Image.open(D/'outfits-walk-120ms.gif') as gif:
  for i,im in enumerate(ImageSequence.Iterator(gif)):x,y=i%2*1024,i//2*512;board.paste(im.convert('RGB'),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'GIF {i+1}',fill='white')
 board.save(D/'actual-gif-frames-2x.png');print('Exported6 up appearance packages,8 combinations x13 actual poses')
if __name__=='__main__':main()
