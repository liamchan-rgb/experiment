#!/usr/bin/env python3
"""Bake registered clothing through the unchanged left-down body source UV.
Artist RGB and authored anatomical mattes are separate. No per-part fitting,
runtime body replacement, per-frame artwork generation or ID-specific engine.
"""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json,shutil
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/down-left/wardrobe-v1';T=R/'Art/Templates/P1-Wardrobe/down-left/v1-independent';D=R/'Art/Review/P1/modular-down-left-wardrobe-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=mod('compose',R/'scripts/compose-character-parts.py');edit=mod('edit',R/'scripts/export-wardrobe-part.py');preview=mod('preview',R/'scripts/export-neutral-direction.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def affine(m):return [float(m[0,0]),float(m[1,0]),float(m[0,1]),float(m[1,1]),float(m[0,2]),float(m[1,2])]
def mat(a):a,b,c,d,x,y=a;return np.array([[a,c,x],[b,d,y],[0,0,1.]])
def uv_sample(im,source,index,cfg):
 uv=np.array(Image.open(P/cfg['sourceUV']/f'{index:02}'/(source+'.png')).convert('RGBA'));a=np.array(im);out=a[uv[:,:,1],uv[:,:,0]].copy();out[uv[:,:,3]==0]=0;return Image.fromarray(out)
def visible_hands(B,f,index):
 trans=np.ones((256,256));mask=np.zeros((256,256),bool)
 for slot in reversed(f['drawOrder']):
  alpha=np.array(Image.open(B/'layers'/f'{index:02}'/(slot+'.png')))[:,:,3]/255
  if slot.startswith('body.hand.'):mask|=(alpha>0)&(trans>.99)
  trans*=1-alpha
 return mask

def main():
 cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['baseTemplate'];base=json.loads((B/'asset.json').read_text());motion=json.loads((B/'motion.json').read_text());assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256'];T.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True)
 paints={};paintRecords=[]
 for name,v in cfg['paintSources'].items():
  raw=Image.open(P/v['image']).convert('RGBA');assert list(raw.size)==v['canvas'] and sha(P/v['image'])==v['sha256'];s=v['scale'];x,y=v['translation'];im=raw.transform((256,256),Image.Transform.AFFINE,(1/s,0,-x/s,0,1/s,-y/s),Image.Resampling.NEAREST);im.save(P/'source'/(name+'-registered.png'));paints[name]=im
 sources={}
 for pack,slots in cfg['matteSources'].items():
  folder=P/pack;(folder/'source').mkdir(parents=True,exist_ok=True);(folder/'png').mkdir(exist_ok=True);(folder/'editable').mkdir(exist_ok=True);sources[pack]={}
  for slot,path in slots.items():
   name='forester' if pack=='lower' else pack;ar=np.array(paints[name]);mask=np.array(Image.open(P/path))[:,:,3]>128;valid=ar[:,:,3]>=128;distance,nearest=distance_transform_edt(~valid,return_indices=True);missing=mask&~valid;maximum=float(distance[missing].max(initial=0));assert maximum<=cfg['maxPaintGutterPixels'],(pack,slot,'paint registration outside gutter',maximum)
   ar[missing,:3]=ar[nearest[0][missing],nearest[1][missing],:3];ar[~mask]=0;ar[mask,3]=255;im=Image.fromarray(ar);sources[pack][slot]=im;im.save(folder/'source'/(slot+'.png'));paintRecords.append({'pack':pack,'slot':slot,'textureGutterPixelsFilled':int(missing.sum()),'maxTextureGutterDistance':maximum,'bodyGeometryRescaled':False})
 # Same sword model, projected from physical right shoulder behind front-facing body.
 weaponSpec=cfg['weapon'];raw=Image.open(P/weaponSpec['source']).convert('RGBA');assert sha(P/weaponSpec['source'])==weaponSpec['sha256'];a,b=map(lambda v:np.array(v,float),weaponSpec['sourceLandmarks']);A,Bb=map(lambda v:np.array(v,float),weaponSpec['targetLandmarks']);u=(b-a)/np.linalg.norm(b-a);v=(Bb-A)/np.linalg.norm(Bb-A);linear=np.outer(v,u)*np.linalg.norm(Bb-A)/np.linalg.norm(b-a)+np.outer([-v[1],v[0]],[-u[1],u[0]])*weaponSpec['transverseScale'];wm=np.eye(3);wm[:2,:2]=linear;wm[:2,2]=A-linear@a;weapon=compose.place(raw,affine(wm),(256,256));ar=np.array(weapon);ar[ar[:,:,3]<128]=0;ar[ar[:,:,3]>=128,3]=255;weapon=Image.fromarray(ar);(P/'back-scabbard/source').mkdir(parents=True,exist_ok=True);weapon.save(P/'back-scabbard/source/weapon.back.png')
 slots={k:list(v) for k,v in cfg['matteSources'].items()};slots['back-scabbard']=['weapon.back'];ids={k:'p1-down-left-'+k+'-v1' for k in slots};bindings={k:[] for k in slots};audit=json.loads((R/cfg['sourceRigAudit']).read_text());assert sha(R/cfg['sourceRigAudit'])==cfg['sourceRigAuditSHA256']
 mapping={'outfit.torso':'shirt','outfit.sleeve.left':'arm.left','outfit.sleeve.right':'arm.right','outfit.pants.left':'leg.left','outfit.boot.left':'leg.left','outfit.pants.right':'leg.right','outfit.boot.right':'leg.right'}
 for i,f in enumerate(motion['frames']):
  handmask=visible_hands(B,f,i)
  for pack in slots:
   out=P/pack/'png'/f'{i:02}';out.mkdir(parents=True,exist_ok=True);layers={};paths={}
   for slot in slots[pack]:
    im=compose.place(weapon,audit['poses'][i]['partTransforms']['upper'],(256,256)) if pack=='back-scabbard' else uv_sample(sources[pack][slot],mapping[slot],i,cfg)
    if pack!='back-scabbard':a=np.array(im);a[handmask]=0;im=Image.fromarray(a)
    q=out/(slot+'.png');im.save(q);layers[slot]=im;paths[slot]=str(q.relative_to(P/pack))
   (P/pack/'editable').mkdir(exist_ok=True);edit.editable(P/pack/'editable',f'{i:02}',layers);bindings[pack].append({'direction':'down-left','clip':f['clip'],'frame':f['frame'],'layers':paths})
  f['drawOrder']=['weapon.back','body.leg.right','body.leg.left','body.arm.right','outfit.sleeve.right','body.hand.right','body.torso','outfit.pants.right','outfit.boot.right','outfit.pants.left','outfit.boot.left','outfit.torso','body.arm.left','outfit.sleeve.left','body.hand.left','head.base','face.eyes','face.brows','face.nose','face.mouth','hair.front'];f['artApproval']=None
 catalog=json.loads((R/'Art/Templates/P1-Heads/down-left/v1-independent/catalog.json').read_text())
 for pack in slots:
  p=P/pack;manifest={'schemaVersion':'1.0.0','id':ids[pack],'version':'1.0.0','part':'weapon' if pack=='back-scabbard' else 'outfit','compatibility':base['compatibility'],'mode':'pose-map','slots':slots[pack],'directions':['down-left'],'clips':base['clips'],'bindings':bindings[pack],'sourceFiles':[]}
  manifest['sourceFiles']=[str(q.relative_to(p)) for sub in ['source','editable'] for q in sorted((p/sub).rglob('*')) if q.is_file()]
  if pack=='back-scabbard':manifest['carryProfile']='back-scabbard'
  (p/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n');catalog['assets'].append({'id':ids[pack],'manifest':str((p/'asset.json').relative_to(R))})
 motion.update(status='down-left-independent-wardrobe-candidate',artApproval=None);(T/'motion.json').write_text(json.dumps(motion,indent=2)+'\n');(T/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n');(D/'paint-registration.json').write_text(json.dumps({'registration':cfg['sourceRegistration'],'mattesDetermineGeometry':True,'records':paintRecords},indent=2)+'\n')
 comp=compose.Compositor(R,T/'catalog.json',T/'motion.json');rendered={}
 for outfit,hair,face,sword in itertools.product(['forester','wayfarer'],['chestnut','silver'],['blue','amber'],[False,True]):
  key=f'{outfit}__{hair}__{face}__'+('back' if sword else 'empty');out=D/'combinations'/key;out.mkdir(parents=True,exist_ok=True);frames=[];selected=[ids[outfit],ids['lower'],'p1-hair-'+hair+'-down-left-v1','p1-face-'+face+'-down-left-v1']+([ids['back-scabbard']] if sword else [])
  for i,f in enumerate(motion['frames']):
   im=comp.render(base['id'],selected,'down-left',f['clip'],f['frame']);im.save(out/f'{i:02}.png');frames.append(im)
  rendered[key]=frames
 for outfit,hair,face in [('forester','chestnut','blue'),('wayfarer','silver','amber')]:
  frames=rendered[f'{outfit}__{hair}__{face}__back'];out=D/outfit;out.mkdir(exist_ok=True);board=Image.new('RGB',(1024,1024),'#17372c')
  for i,im in enumerate(frames):x,y=i%4*256,i//4*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white')
  board.save(out/'all-poses-fullbody-1x.png');board.resize((2048,2048),Image.Resampling.NEAREST).save(out/'all-poses-fullbody-2x.png');preview.gif(frames[1:9],out/'walk-120ms.gif');preview.gif([frames[i] for i in [0,9,10]+list(range(1,9))*2+[11,12,0]],out/'start-stop-120ms.gif',[480]+[120]*20+[480]);preview.flatten(frames[0],2).save(out/'idle-2x.png')
 pairs=[]
 for i in range(13):
  im=Image.new('RGBA',(512,256));im.alpha_composite(rendered['forester__chestnut__blue__back'][i]);im.alpha_composite(rendered['wayfarer__silver__amber__back'][i],(256,0));pairs.append(im)
 preview.flatten(pairs[0],2).save(D/'outfits-idle-2x.png');preview.gif(pairs[1:9],D/'outfits-walk-120ms.gif');preview.gif([pairs[i] for i in [0,9,10]+list(range(1,9))*2+[11,12,0]],D/'outfits-start-stop-120ms.gif',[480]+[120]*20+[480]);print('Exported4 wardrobe packages;16combinations x13 actual poses')
if __name__=='__main__':main()
