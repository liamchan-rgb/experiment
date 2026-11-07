#!/usr/bin/env python3
"""Independent right-facing appearance maps on the approved unchanged neutral13pose body."""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageSequence
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/right/appearance-v1';T=R/'Art/Templates/P1-Wardrobe/right/v1-independent';D=R/'Art/Review/P1/modular-right-appearance-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
bodyexp=mod('rightBody',R/'scripts/export-right-neutral-mirror.py');compose=bodyexp.c;edit=bodyexp.edit;preview=bodyexp.preview;headedit=mod('rightHeadEdit',R/'scripts/export-character-head-part.py');side=bodyexp.side
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def board(items,path):
 out=Image.new('RGB',(1024,1024),'#17372c');draw=ImageDraw.Draw(out)
 for i,im in enumerate(items):x,y=i%4*256,i//4*256;out.paste(preview.flatten(im),(x,y));draw.text((x+4,y+4),f'{i:02}',fill='white')
 out.save(path);out.resize((2048,2048),Image.Resampling.NEAREST).save(path.with_name(path.stem.replace('1x','2x')+path.suffix))
def main():
 cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['baseTemplate'];a=json.loads((B/'asset.json').read_text());m=json.loads((B/'motion.json').read_text());assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256'];wm=json.loads((R/cfg['sourceWardrobeMotion']).read_text());catalog=[{'id':a['id'],'manifest':str((B/'asset.json').relative_to(R))}];ids={};headSources={}
 for name,path in cfg['sources'].items():
  src=R/path;old=json.loads((src/'asset.json').read_text());assert sha(src/'asset.json')==cfg['sourceManifestSHA256'][name];head=old['mode']=='head-local';folder=P/name;(folder/'source').mkdir(parents=True,exist_ok=True);shutil.copyfile(src/'asset.json',folder/'source/manifest-original.json');bindings=[]
  for i,f in enumerate(m['frames']):
   parts={};paths={}
   for slot,relative in old['bindings'][i]['layers'].items():
    newslot=side(slot);raw=Image.open(src/relative).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);q=folder/'png'/((newslot+'.png') if head else f'{i:02}/'+newslot+'.png');q.parent.mkdir(parents=True,exist_ok=True);raw.save(folder/'source'/((newslot+'-mirrored.png') if head else f'{i:02}-'+newslot+'-mirrored.png'))
    if cfg['relightEnabled'] and name not in ['face-blue','face-amber','back-scabbard']:
     texture=folder/'relit'/((newslot+'.png') if head else f'{i:02}/'+newslot+'.png');im=Image.open(texture).convert('RGBA');assert np.array_equal(np.array(im)[:,:,3],np.array(raw)[:,:,3]),(name,i,slot,'relight changed shape')
    else:im=raw
    clean=np.array(im);clean[clean[:,:,3]==0]=0;im=Image.fromarray(clean);im.save(q);parts[newslot]=im;paths[newslot]=str(q.relative_to(folder))
   if head:headSources[name]=parts;headedit.editable(folder,parts)
   else:(folder/'editable').mkdir(exist_ok=True);edit.editable(folder/'editable',f'{i:02}',parts)
   bindings.append({'direction':'right','clip':f['clip'],'frame':f['frame'],'layers':paths})
  ids[name]='p1-right-'+name+'-v1';new=copy.deepcopy(old);new.update(id=ids[name],version='1.0.0',directions=['right'],slots=[side(s) for s in old['slots']],bindings=bindings);write(folder/'authoring.json',{'sourceManifest':str((src/'asset.json').relative_to(R)),'sourceSHA256':sha(src/'asset.json'),'sourceReflection':True,'semanticSidesExchanged':True,'relightEnabled':cfg['relightEnabled'] and name not in ['face-blue','face-amber','back-scabbard'],'alphaOwner':'original reflected left part','authorAndReviewer':'root','artApproval':None});new['sourceFiles']=['authoring.json']+[str(p.relative_to(folder)) for root in ['source','editable'] for p in sorted((folder/root).rglob('*')) if p.is_file()]
  if head:new['sourceFiles']+=['editable.ora','editable.svg']
  write(folder/'asset.json',new);catalog.append({'id':ids[name],'manifest':str((folder/'asset.json').relative_to(R))})
 for i,f in enumerate(m['frames']):
  f['drawOrder']=[side(s) for s in wm['frames'][i]['drawOrder']];assert [s for s in f['drawOrder'] if s in a['slots']]==json.loads((B/'motion.json').read_text())['frames'][i]['drawOrder'];f['artApproval']=None
 m.update(status='right-independent-appearance-candidate',artApproval=None);write(T/'motion.json',m);write(T/'catalog.json',{'assets':catalog});c=compose.Compositor(R,T/'catalog.json',T/'motion.json');renders={}
 for style,hair,face,carry in itertools.product(['forester','wayfarer'],['chestnut','silver'],['blue','amber'],['empty','back']):
  key='__'.join([style,hair,face,carry]);out=D/'combinations'/key;out.mkdir(parents=True,exist_ok=True);sel=[ids[style],ids['lower'],ids['hair-'+hair],ids['face-'+face]]+([ids['back-scabbard']] if carry=='back' else []);items=[]
  for i,f in enumerate(m['frames']):im=c.render(a['id'],sel,'right',f['clip'],f['frame']);im.save(out/f'{i:02}.png');items.append(im)
  renders[key]=items
  if carry=='back':board(items,out/'all-poses-fullbody-1x.png')
 pairs=[]
 for i in range(13):
  im=Image.new('RGBA',(512,256));im.alpha_composite(renders['forester__chestnut__blue__back'][i]);im.alpha_composite(renders['wayfarer__silver__amber__back'][i],(256,0));pairs.append(im)
 preview.flatten(pairs[0],2).save(D/'outfits-idle-2x.png');preview.gif(pairs[1:9],D/'outfits-walk-120ms.gif');preview.gif([pairs[i] for i in cfg['sequence']],D/'outfits-start-stop-120ms.gif',cfg['durationsMs'])
 with Image.open(D/'outfits-walk-120ms.gif') as gif:
  out=Image.new('RGB',(2048,2048),'#17372c')
  for i,im in enumerate(ImageSequence.Iterator(gif)):out.paste(im.convert('RGB'),(i%2*1024,i//2*512))
  out.save(D/'actual-gif-frames-2x.png')
 if not cfg['relightEnabled']:
  guide=Image.new('RGBA',(512,512));guide.alpha_composite(pairs[0]);guide.resize((1254,1254),Image.Resampling.NEAREST).save(P/'source/outfits-light-guide-1254.png')
  for n in ['hair-chestnut','hair-silver']:headSources[n]['hair.front'].resize((1254,1254),Image.Resampling.NEAREST).save(P/'source'/(n+'-light-guide-1254.png'))
 print(json.dumps({'packages':8,'combinations':16,'actualPoses':208,'relightEnabled':cfg['relightEnabled'],'artApproval':None}))
if __name__=='__main__':main()
