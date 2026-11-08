#!/usr/bin/env python3
"""Offline appearance reflection with semantic sides, fixed-light RGB and a separately registered right-shoulder sword. Approved body/motion remain unchanged."""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageSequence
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/down-right/appearance-v1';T=R/'Art/Templates/P1-Wardrobe/down-right/v1-independent';D=R/'Art/Review/P1/modular-down-right-appearance-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
left=mod('leftwardrobe',R/'scripts/export-down-left-wardrobe.py');compose=left.compose;edit=left.edit;preview=left.preview
headedit=mod('headedit',R/'scripts/export-character-head-part.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
flip=lambda im:im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
def side(n):
 if n.endswith('.left'):return n[:-5]+'.right'
 if n.endswith('.right'):return n[:-6]+'.left'
 return n
mapping={'outfit.torso':'shirt','outfit.sleeve.left':'arm.left','outfit.sleeve.right':'arm.right','outfit.pants.left':'leg.left','outfit.boot.left':'leg.left','outfit.pants.right':'leg.right','outfit.boot.right':'leg.right'}
def main():
 cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['baseTemplate'];base=json.loads((B/'asset.json').read_text());motion=json.loads((B/'motion.json').read_text());assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256'];T.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True);catalog=[{'id':base['id'],'manifest':str((B/'asset.json').relative_to(R))}];records=[]
 LP=R/cfg['headSource'];WP=R/cfg['wardrobeSource'];wmotion=json.loads((R/'Art/Templates/P1-Wardrobe/down-left/v1-independent/motion.json').read_text());ids={};sources={};slots={};sourceManifests={}
 for name in ['hair-chestnut','hair-silver','face-blue','face-amber','forester','wayfarer','lower']:
  head=name.startswith(('hair','face'));src=(LP if head else WP)/name;old=json.loads((src/'asset.json').read_text());sourceManifests[name]=old;ids[name]=old['id'].replace('down-left','down-right');slots[name]=[side(s) for s in old['slots']];out=P/name;(out/'source').mkdir(parents=True,exist_ok=True);(out/'png').mkdir(exist_ok=True);sources[name]={}
  for s in old['slots']:
   im=flip(Image.open(src/('png' if head else 'source')/(s+'.png')).convert('RGBA'));newslot=side(s);im.save(out/'source'/(newslot+'-mirrored.png'))
   if cfg['relightEnabled'] and not name.startswith('face'):
    texture=P/cfg['relight']['textureRoot']/name/(newslot+'.png');col=Image.open(texture).convert('RGBA');assert np.array_equal(np.array(col)[:,:,3],np.array(im)[:,:,3]);im=col
   sources[name][newslot]=im
   if head:im.save(out/'png'/(newslot+'.png'))
   else:im.save(out/'source'/(newslot+'.png'))
  if head:headedit.editable(out,sources[name])
 # Same source sword: maintain anatomical shoulder rather than blindly reflecting the weapon.
 w=cfg['weapon'];assert sha(R/w['source'])==w['sha256'];raw=Image.open(R/w['source']).convert('RGBA');a,b=map(lambda v:np.array(v,float),w['sourceLandmarks']);A,Bb=map(lambda v:np.array(v,float),w['targetLandmarks']);u=(b-a)/np.linalg.norm(b-a);v=(Bb-A)/np.linalg.norm(Bb-A);linear=np.outer(v,u)*np.linalg.norm(Bb-A)/np.linalg.norm(b-a)+np.outer([-v[1],v[0]],[-u[1],u[0]])*w['transverseScale'];mat=np.eye(3);mat[:2,:2]=linear;mat[:2,2]=A-linear@a;weapon=compose.place(raw,left.affine(mat),(256,256));ar=np.array(weapon);ar[ar[:,:,3]<128]=0;ar[ar[:,:,3]>=128,3]=255;weapon=Image.fromarray(ar);name='back-scabbard';ids[name]='p1-down-right-back-scabbard-v1';slots[name]=['weapon.back'];(P/name/'source').mkdir(parents=True,exist_ok=True);weapon.save(P/name/'source/weapon.back.png');audit=json.loads((R/cfg['sourceRigAudit']).read_text());F=np.array([[-1,0,255],[0,1,0],[0,0,1.]])
 bindings={k:[] for k in ids}
 for i,f in enumerate(motion['frames']):
  for name in ids:
   head=name.startswith(('hair','face'));layers={};paths={};out=P/name/'png'/f'{i:02}'
   if not head:out.mkdir(parents=True,exist_ok=True)
   for s in slots[name]:
    if head:paths[s]='png/'+s+'.png';continue
    if name=='back-scabbard':im=compose.place(weapon,left.affine(F@left.mat(audit['poses'][i]['partTransforms']['upper'])@F),(256,256))
    else:
     oldslot=side(s);oldpath=WP/name/sourceManifests[name]['bindings'][i]['layers'][oldslot];im=flip(Image.open(oldpath).convert('RGBA'))
     if cfg['relightEnabled']:
      uv=np.array(flip(Image.open(R/cfg['sourceUV']/f'{i:02}'/(mapping[oldslot]+'.png')).convert('RGBA')));texture=np.array(sources[name][s]);aa=np.array(im);valid=aa[:,:,3]>0;assert np.all(uv[:,:,3][valid]>0),(name,s,i,'missing uv');cols=texture[uv[:,:,1],255-uv[:,:,0]];assert np.all(cols[:,:,3][valid]>0),(name,s,i,'texture misses reflected matte');aa[valid,:3]=cols[valid,:3];im=Image.fromarray(aa)
    im.save(out/(s+'.png'));layers[s]=im;paths[s]=str((out/(s+'.png')).relative_to(P/name))
   if not head:
    (P/name/'editable').mkdir(exist_ok=True);edit.editable(P/name/'editable',f'{i:02}',layers)
   bindings[name].append({'direction':'down-right','clip':f['clip'],'frame':f['frame'],'layers':paths})
  f['drawOrder']=[side(s) for s in wmotion['frames'][i]['drawOrder']];f['artApproval']=None
 for name in ids:
  head=name.startswith(('hair','face'));part='hair' if name.startswith('hair') else 'face' if name.startswith('face') else 'weapon' if name=='back-scabbard' else 'outfit';folder=P/name
  if name=='back-scabbard':
   shutil.copyfile(R/w['source'],folder/'source/original.png');(folder/'source/prompt.txt').write_text('Reuse the existing independent sword source; fixed right-shoulder projection is authored in parent authoring.json. No new generated sword.\n')
  elif name.startswith('face'):
   oldcfg=json.loads((LP/'authoring.json').read_text());src=oldcfg['sources'][oldcfg['packages'][name]['source']];shutil.copyfile(LP/src['image'],folder/'source/original.png');shutil.copyfile(LP/src['prompt'],folder/'source/prompt.txt')
  elif cfg.get('relight',{}).get('sources'):
   src=cfg['relight']['sources']['wayfarer' if name in ['hair-silver','wayfarer'] else 'forester'];shutil.copyfile(P/src['image'],folder/'source/original.png');shutil.copyfile(P/src['prompt'],folder/'source/prompt.txt')
  authors={'source':str(((LP if head else WP)/name).relative_to(R)) if name!='back-scabbard' else w['source'],'sourceReflection':name!='back-scabbard','semanticSidesExchanged':True,'light':'upper-left','relightEnabled':cfg['relightEnabled'] and not name.startswith('face'),'authorAndReviewer':'root','artApproval':None};(folder/'authoring.json').write_text(json.dumps(authors,indent=2)+'\n')
  sourceFiles=['authoring.json']+[str(q.relative_to(folder)) for sub in ['source','editable'] for q in sorted((folder/sub).rglob('*')) if q.is_file()]
  if head:sourceFiles+=['editable.ora','editable.svg']
  manifest={'schemaVersion':'1.0.0','id':ids[name],'version':'1.0.0','part':part,'compatibility':base['compatibility'],'mode':'head-local' if head else 'pose-map','slots':slots[name],'directions':['down-right'],'clips':base['clips'],'bindings':bindings[name],'sourceFiles':sourceFiles}
  if name=='back-scabbard':manifest['carryProfile']='back-scabbard'
  (folder/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n');catalog.append({'id':ids[name],'manifest':str((folder/'asset.json').relative_to(R))})
 motion.update(status='down-right-independent-appearance-candidate',artApproval=None);(T/'motion.json').write_text(json.dumps(motion,indent=2)+'\n');(T/'catalog.json').write_text(json.dumps({'assets':catalog},indent=2)+'\n');comp=compose.Compositor(R,T/'catalog.json',T/'motion.json');rendered={}
 for outfit,hair,face,sword in itertools.product(['forester','wayfarer'],['chestnut','silver'],['blue','amber'],[False,True]):
  key=f'{outfit}__{hair}__{face}__'+('back' if sword else 'empty');out=D/'combinations'/key;out.mkdir(parents=True,exist_ok=True);frames=[];selected=[ids[outfit],ids['lower'],ids['hair-'+hair],ids['face-'+face]]+([ids['back-scabbard']] if sword else [])
  for i,f in enumerate(motion['frames']):im=comp.render(base['id'],selected,'down-right',f['clip'],f['frame']);im.save(out/f'{i:02}.png');frames.append(im)
  rendered[key]=frames
  if sword:
   board=Image.new('RGB',(1024,1024),'#17372c')
   for i,im in enumerate(frames):x,y=i%4*256,i//4*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white')
   board.save(out/'all-poses-fullbody-1x.png');board.resize((2048,2048),Image.Resampling.NEAREST).save(out/'all-poses-fullbody-2x.png')
 for outfit,hair,face in [('forester','chestnut','blue'),('wayfarer','silver','amber')]:
  frames=rendered[f'{outfit}__{hair}__{face}__back'];out=D/outfit;out.mkdir(exist_ok=True);preview.gif(frames[1:9],out/'walk-120ms.gif');preview.gif([frames[i] for i in [0,9,10]+list(range(1,9))*2+[11,12,0]],out/'start-stop-120ms.gif',[480]+[120]*20+[480]);preview.flatten(frames[0],2).save(out/'idle-2x.png')
 pairs=[]
 for i in range(13):
  im=Image.new('RGBA',(512,256));im.alpha_composite(rendered['forester__chestnut__blue__back'][i]);im.alpha_composite(rendered['wayfarer__silver__amber__back'][i],(256,0));pairs.append(im)
 preview.flatten(pairs[0],2).save(D/'outfits-idle-2x.png');preview.gif(pairs[1:9],D/'outfits-walk-120ms.gif');preview.gif([pairs[i] for i in [0,9,10]+list(range(1,9))*2+[11,12,0]],D/'outfits-start-stop-120ms.gif',[480]+[120]*20+[480])
 board=Image.new('RGB',(2048,2048),'#17372c')
 with Image.open(D/'outfits-walk-120ms.gif') as gif:
  for i,im in enumerate(ImageSequence.Iterator(gif)):
   x,y=i%2*1024,i//2*512;board.paste(im.convert('RGB'),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'GIF {i+1}',fill='white')
 board.save(D/'actual-gif-frame-review-2x.png');print('Exported8 independent appearance packages;16combinations x13 actual poses')
if __name__=='__main__':main()
