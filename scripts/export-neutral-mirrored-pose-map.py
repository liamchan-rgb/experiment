#!/usr/bin/env python3
"""Offline reflection of an approved pose map and its attachment coordinates.
No runtime appearance branches or new body rig. Semantic sides swap together.
"""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
preview=module('preview',R/'scripts/export-neutral-direction.py');editable=module('editable',R/'scripts/export-wardrobe-part.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def side(name):
 for a,b in [('.left','.right'),('.right','.left'),('Left','Right'),('Right','Left')]:
  if name.endswith(a):return name[:-len(a)]+b
 return {'left':'right','right':'left'}.get(name,name)
def mat(v):a,b,c,d,x,y=v;return np.array([[a,c,x],[b,d,y],[0,0,1]],float)
def affine(m):return [float(m[0,0]),float(m[1,0]),float(m[0,1]),float(m[1,1]),float(m[0,2]),float(m[1,2])]
def retexture(image, oldname, cfg, folder, idx):
 lighting=cfg.get('lighting')
 if not lighting:return image
 sourceName=oldname;textureName=side(oldname)
 if oldname.startswith('body.'):
  sourceName=oldname[len('body.'):];textureName=side(sourceName)
 if oldname=='body.torso':sourceName='shirt';textureName='body.torso'
 if oldname.startswith('complete-arm.'):
  sourceName='arm.'+oldname.rsplit('.',1)[1];textureName=side(sourceName)
 uvpath=folder/lighting['uv']/f'{idx:02}'/(sourceName+'.png');texturepath=folder/lighting['textures']/(textureName+'.png')
 if not uvpath.exists() or not texturepath.exists():return image
 uv=np.array(Image.open(uvpath).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT));texture=np.array(Image.open(texturepath).convert('RGBA'));a=np.array(image);visible=a[:,:,3]>0;assert np.all(uv[:,:,3][visible]>0),(idx,oldname,'missing UV')
 colour=texture[uv[:,:,1],255-uv[:,:,0]];assert np.all(colour[:,:,3][visible]>0),(idx,oldname,'UV outside source part');a[visible,:3]=colour[visible,:3];return Image.fromarray(a)

def export(folder,review):
 cfg=json.loads((folder/'mirror-authoring.json').read_text());src=R/cfg['sourceTemplate'];asset=json.loads((src/'asset.json').read_text());motion=json.loads((src/'motion.json').read_text());assert sha(src/'asset.json')==cfg['sourceManifestSHA256'];assert sha(src/'motion.json')==cfg['sourceMotionSHA256'];approval=json.loads((R/cfg['sourceApproval']).read_text());assert approval['status']=='approved'
 canvas=motion['canvas'];assert canvas==[256,256];F=np.array([[-1,0,canvas[0]-1],[0,1,0],[0,0,1]],float);localF=np.array([[-1,0,cfg['headLocalCanvas'][0]-1],[0,1,0],[0,0,1]],float)
 review.mkdir(parents=True,exist_ok=True)
 for sub in ['layers','frames','editable','components']:(folder/sub).mkdir(exist_ok=True)
 frames=[];bindings=[];poses=[];audit=[]
 for binding,old in zip(asset['bindings'],motion['frames']):
  assert binding['frame']==old['frame'];idx=old['frame'];layers={};paths={};directory=folder/'layers'/f'{idx:02}';directory.mkdir(exist_ok=True)
  for slot,path in binding['layers'].items():
   im=Image.open(src/path).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);im=retexture(im,slot,cfg,folder,idx);newslot=side(slot);q=directory/(newslot+'.png');im.save(q);layers[newslot]=im;paths[newslot]=str(q.relative_to(folder))
  order=[side(slot) for slot in old['drawOrder']];layers={slot:layers[slot] for slot in order};whole=editable.editable(folder/'editable',f'{idx:02}',layers);whole.save(folder/'frames'/f'{idx:02}.png');frames.append(whole)
  components=src/'components'/f'{idx:02}';out=folder/'components'/f'{idx:02}';out.mkdir(exist_ok=True)
  if components.is_dir():
   for p in sorted(components.glob('*.png')):
    im=Image.open(p).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);retexture(im,p.stem,cfg,folder,idx).save(out/(side(p.stem)+'.png'))
  pose=copy.deepcopy(old);pose['direction']=cfg['direction'];pose['facing']=[-old['facing'][0],old['facing'][1]];pose['drawOrder']=order;pose['artApproval']=None;pose['headToCanvas']=affine(F@mat(old['headToCanvas'])@localF);pose['joints']={side(k):[canvas[0]-1-v[0],v[1]] for k,v in old['joints'].items()};pose['soleMarkers']={side(k):[canvas[0]-1-v[0],v[1]] for k,v in old['soleMarkers'].items()};pose['support']=side(old['support']);pose['sockets']={}
  for name,socket in old['sockets'].items():
   v=copy.deepcopy(socket);v['position']=[canvas[0]-1-v['position'][0],v['position'][1]]
   if v.get('angleDeg') is not None:v['angleDeg']=(180-v['angleDeg'])%360
   pose['sockets'][side(name)]=v
  poses.append(pose);bindings.append({'direction':cfg['direction'],'clip':old['clip'],'frame':idx,'layers':paths});audit.append({'frame':idx,'sourceDirection':old['direction'],'sourceFrame':idx,'unchangedFrameTimingMs':motion['durationMs'],'geometryMirrorAxisX':127.5,'semanticSidesExchanged':True,'relightingRGBOnly':bool(cfg.get('lighting')),'alphaDifferenceFromApprovedReflection':0,'support':pose['support'],'headLocalReflection':affine(localF)})
 new=copy.deepcopy(asset);new.update(id=cfg['id'],version='5.1.0',directions=[cfg['direction']],slots=[side(s) for s in asset['slots']],bindings=bindings,sourceFiles=['mirror-authoring.json']+[str(p.relative_to(folder)) for sub in ['source','editable'] for p in sorted((folder/sub).rglob('*')) if p.is_file()]);(folder/'asset.json').write_text(json.dumps(new,indent=2)+'\n');newmotion=copy.deepcopy(motion);newmotion.update(status='main-only-mirror-repair-candidate',artApproval=None,baseManifestSHA256=sha(folder/'asset.json'),frames=poses);(folder/'motion.json').write_text(json.dumps(newmotion,indent=2)+'\n')
 board=Image.new('RGB',(768,768),'#17372c');strip=Image.new('RGBA',(2304,256))
 for i,im in enumerate(frames):x,y=i%3*256,i//3*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white');strip.alpha_composite(im,(i*256,0))
 board.save(review/'nine-poses-fullbody-1x.png');board.resize((1536,1536),Image.Resampling.NEAREST).save(review/'nine-poses-fullbody-2x.png');strip.save(folder/'strip.png');preview.flatten(frames[0],2).save(review/'idle-review-2x.png');preview.gif(frames[1:],review/'walk-120ms.gif');(review/'mirror-audit.json').write_text(json.dumps({'repairAndReviewOwner':'root','subagentsUsed':False,'artApproval':None,'sourceTemplate':cfg['sourceTemplate'],'sourceApproval':cfg['sourceApproval'],'sourceApprovalScope':approval['scope'],'poses':audit},indent=2)+'\n');print('Mirrored pose map exported:',cfg['direction'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--review',type=Path,required=True);a=p.parse_args();export(a.folder,a.review)
