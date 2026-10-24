#!/usr/bin/env python3
"""Bake independently authored garments through the unchanged common body UVs."""
from pathlib import Path
import copy,hashlib,importlib.util,json
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/upper/wardrobe-v1';T=R/'Art/Templates/P1-Wardrobe/upper/v1-independent';D=R/'Art/Review/P1/modular-upper-wardrobe-v1'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=module('compose',R/'scripts/compose-character-parts.py');edit=module('edit',R/'scripts/export-wardrobe-part.py');mirror=module('mirror',R/'scripts/export-neutral-mirrored-pose-map.py');preview=module('preview',R/'scripts/export-neutral-direction.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def poly(im,points):
 mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in points],fill=255);a=np.array(im);a[(np.array(mask)==0)|(a[:,:,3]<128)]=0;a[:,:,3][a[:,:,3]>=128]=255;return Image.fromarray(a)
def uv_sample(image,source,idx,direction,cfg):
 if direction=='up-right':source=mirror.side(source)
 uv=np.array(Image.open(P/cfg['sourceUV']/f'{idx:02}'/(source+'.png')).convert('RGBA'))
 if direction=='up-right':uv=uv[:,::-1].copy();uv[:,:,0]=255-uv[:,:,0]
 a=np.array(image);out=a[uv[:,:,1],uv[:,:,0]].copy();out[uv[:,:,3]==0]=0;return Image.fromarray(out)
def main():
 for tag in ['forester','wayfarer']:
  raw=Image.open(P/'source'/(tag+'-generated.png')).convert('RGBA');assert raw.size==(1774,887);raw.resize((512,256),Image.Resampling.NEAREST).save(P/'source'/(tag+'-registered.png'))
 raw=Image.open(P/'source/independent-lower-generated.png').convert('RGBA');assert raw.size==(1254,1254);raw.resize((512,512),Image.Resampling.NEAREST).save(P/'source/independent-lower-registered.png')
 cfg=json.loads((P/'authoring.json').read_text());T.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True)
 slots={'forester':['outfit.torso','outfit.sleeve.left','outfit.sleeve.right'],'wayfarer':['outfit.torso','outfit.sleeve.left','outfit.sleeve.right'],'lower':['outfit.pants.left','outfit.pants.right','outfit.boot.left','outfit.boot.right'],'hair-chestnut':['hair.front'],'hair-silver':['hair.front'],'back-scabbard':['weapon.back']};ids={k:'p1-upper-'+k+'-v1' for k in slots};bindings={k:[] for k in slots};catalog=[];sourceParts={};mapping={'outfit.torso':'shirt','outfit.sleeve.left':'arm.left','outfit.sleeve.right':'arm.right','outfit.pants.left':'leg.left','outfit.boot.left':'leg.left','outfit.pants.right':'leg.right','outfit.boot.right':'leg.right'}
 for pack in slots:
  for name in ['png','editable','source']:(P/pack/name).mkdir(parents=True,exist_ok=True)
 for di,direction in enumerate(cfg['directions']):
  B=R/f'Art/Templates/P1-Neutral/{direction}/walk-r6-transitions';asset=json.loads((B/'asset.json').read_text());motion=json.loads((B/'motion.json').read_text());catalog.append({'id':asset['id'],'manifest':str((B/'asset.json').relative_to(R))})
  sources={name:Image.open(P/path).convert('RGBA').crop((di*256,0,(di+1)*256,256)) for name,path in cfg['sourceFrames'].items()};near,far=('left','right') if direction=='up-left' else ('right','left')
  for pack in ['forester','wayfarer','lower','hair-chestnut','hair-silver']:
   source=sources['wayfarer' if pack in ['wayfarer','hair-silver'] else 'forester'];parts={}
   for slot in slots[pack]:
    oldslot=mirror.side(slot) if direction=='up-right' else slot;points=cfg['wayfarerTorsoPolygon'] if pack=='wayfarer' and slot=='outfit.torso' else cfg['leftPolygons'][oldslot]
    if direction=='up-right':points=[[255-x,y] for x,y in points]
    im=poly(source,points)
    if slot=='outfit.torso':
     scale=cfg.get('torsoWidthScale',1);centre=128 if direction=='up-left' else 127;sy=cfg.get('torsoVerticalScale',1);im=compose.place(im,[scale,0,0,sy,centre*(1-scale),160*(1-sy)],(256,256))
    if pack=='lower' and cfg.get('independentLowerSource'):
     sheet=Image.open(P/cfg['independentLowerSource']).convert('RGBA');si=0 if slot.endswith('.left') else 1;im=sheet.crop((si*256,di*256,(si+1)*256,(di+1)*256));side=slot.rsplit('.',1)[1];im=compose.place(im,cfg['independentLowerFits'][direction][side],(256,256));ar=np.array(im);yy,xx=np.mgrid[:256,:256];valid=yy<=196 if '.pants.' in slot else yy>=195;ar[(ar[:,:,3]<128)|~valid]=0;ar[:,:,3][ar[:,:,3]>=128]=255;im=Image.fromarray(ar)
    elif slot.startswith(('outfit.pants.','outfit.boot.')):
     ar=np.array(im);yy,xx=np.mgrid[:256,:256];boundary=np.interp(yy,cfg['lowerSemanticBoundary']['y'],cfg['lowerSemanticBoundary']['x']);lx=255-xx if direction=='up-right' else xx;left=oldslot.endswith('.left');valid=lx<=boundary if left else lx>boundary;ar[~valid]=0;im=Image.fromarray(ar)
     centre=123 if left else 139;centre=255-centre if direction=='up-right' else centre;scale=cfg['lowerWidthScale'];im=compose.place(im,[scale,0,0,1,centre*(1-scale),0],(256,256))
    if slot in cfg['staticPartFits']:
     fit=cfg['staticPartFits'][oldslot];a,b=map(lambda v:np.array(v,float),fit['source']);A,Bb=map(lambda v:np.array(v,float),fit['target']);u=(b-a)/np.linalg.norm(b-a);v=(Bb-A)/np.linalg.norm(Bb-A);linear=np.outer(v,u)*np.linalg.norm(Bb-A)/np.linalg.norm(b-a)+np.outer([-v[1],v[0]],[-u[1],u[0]])*fit['transverseScale'];mm=np.eye(3);mm[:2,:2]=linear;mm[:2,2]=A-linear@a
     if direction=='up-right':F=np.array([[-1,0,255],[0,1,0],[0,0,1.]]);mm=F@mm@F
     im=compose.place(im,mirror.affine(mm),(256,256))
    if slot=='hair.front':
     x,y=cfg['hairLocalOrigin'][direction];im=im.crop((x,y,x+96,y+96))
    im.save(P/pack/'source'/(direction+'-'+slot+'.png'));parts[slot]=im
   sourceParts[direction,pack]=parts
  # Same physical shoulder for both views, registered by explicit endpoints.
  raw=Image.open(P/cfg['sourceWeapon']).convert('RGBA');a,b=map(np.array,cfg['weaponSourceLandmarks']);A,Bt=map(np.array,cfg['weaponTargetLandmarks'][direction]);u=(b-a)/np.linalg.norm(b-a);v=(Bt-A)/np.linalg.norm(Bt-A);linear=np.outer(v,u)*np.linalg.norm(Bt-A)/np.linalg.norm(b-a)+np.outer([-v[1],v[0]],[-u[1],u[0]])*cfg.get('weaponTransverseScale',.045);mat=np.eye(3);mat[:2,:2]=linear;mat[:2,2]=A-linear@a;weapon=compose.place(raw,mirror.affine(mat),(256,256));wa=np.array(weapon);wa[wa[:,:,3]<128]=0;wa[:,:,3][wa[:,:,3]>=128]=255;weapon=Image.fromarray(wa);weapon.save(P/'back-scabbard/source'/(direction+'-weapon.back.png'))
  leftAudit=json.loads((R/'Art/Review/P1/neutral-upper-transitions-r6/up-left/rig-audit.json').read_text());F=np.array([[-1,0,255],[0,1,0],[0,0,1.]])
  for idx,f in enumerate(motion['frames']):
   handmask=np.zeros((256,256),bool);transmission=np.ones((256,256))
   for neutralSlot in reversed(f['drawOrder']):
    alpha=np.array(Image.open(B/'layers'/f'{idx:02}'/(neutralSlot+'.png')))[:,:,3]/255
    if neutralSlot.startswith('body.hand.'):handmask|=(alpha>0)&(transmission>.99)
    transmission*=1-alpha
   # Ordering extends the common neutral motion; neutral relative order unchanged.
   order=[f'body.leg.{far}',f'body.leg.{near}',f'body.arm.{far}',f'outfit.sleeve.{far}',f'body.hand.{far}','body.torso',f'outfit.pants.{far}',f'outfit.boot.{far}',f'outfit.pants.{near}',f'outfit.boot.{near}','outfit.torso','weapon.back',f'body.arm.{near}',f'outfit.sleeve.{near}',f'body.hand.{near}','head.base','hair.front'];f['drawOrder']=order;f['artApproval']=None
   for pack in slots:
    out=P/pack/'png'/direction/f'{idx:02}';out.mkdir(parents=True,exist_ok=True);layers={};paths={}
    for slot in slots[pack]:
     if pack=='back-scabbard':
      upper=mirror.mat(leftAudit['poses'][idx]['partTransforms']['upper']);upper=F@upper@F if direction=='up-right' else upper;im=compose.place(weapon,mirror.affine(upper),(256,256))
     elif pack.startswith('hair-'):im=sourceParts[direction,pack][slot]
     else:im=uv_sample(sourceParts[direction,pack][slot],mapping[slot],idx,direction,cfg)
     if slot.startswith('outfit.'):
      # The hand owns its silhouette. Bake an occlusion window, never copy a hand into clothing.
      ar=np.array(im)
      ar[handmask]=0;im=Image.fromarray(ar)
     path=out/(slot+'.png');im.save(path);paths[slot]=str(path.relative_to(P/pack));layers[slot]=im
    bindings[pack].append({'direction':direction,'clip':f['clip'],'frame':f['frame'],'layers':paths});edit.editable(P/pack/'editable',direction+f'-{idx:02}',layers)
  motion.update(status='upper-independent-wardrobe-candidate',artApproval=None);(T/(direction+'-motion.json')).write_text(json.dumps(motion,indent=2)+'\n')
 for pack in slots:
  manifest={'schemaVersion':'1.0.0','id':ids[pack],'version':'1.0.0','part':'hair' if pack.startswith('hair-') else 'weapon' if pack=='back-scabbard' else 'outfit','compatibility':motion['compatibility'],'mode':'head-local' if pack.startswith('hair-') else 'pose-map','slots':slots[pack],'directions':cfg['directions'],'clips':['idle','walk','walk-start','walk-stop'],'bindings':bindings[pack],'sourceFiles':[str(q.relative_to(P/pack)) for sub in ['source','editable'] for q in sorted((P/pack/sub).rglob('*')) if q.is_file()]}
  if pack=='back-scabbard':manifest['carryProfile']='back-scabbard'
  (P/pack/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n');catalog.append({'id':ids[pack],'manifest':str((P/pack/'asset.json').relative_to(R))})
 (T/'catalog.json').write_text(json.dumps({'assets':catalog},indent=2)+'\n');print('Exported six independent packages, both directions, 13 poses each')
 for direction in cfg['directions']:
  comp=compose.Compositor(R,T/'catalog.json',T/(direction+'-motion.json'));m=json.loads((T/(direction+'-motion.json')).read_text());base='p1-neutral-'+direction+'-r6-transitions'
  for outfit,hair in [('forester','hair-chestnut'),('wayfarer','hair-silver')]:
   out=D/direction/outfit;out.mkdir(parents=True,exist_ok=True);frames=[]
   for idx,f in enumerate(m['frames']):
    im=comp.render(base,[ids[outfit],ids['lower'],ids[hair],ids['back-scabbard']],direction,f['clip'],f['frame']);im.save(out/f'{idx:02}.png');frames.append(im)
   preview.gif(frames[1:9],out/'walk-120ms.gif');seq=[0,9,10]+list(range(1,9))*2+[11,12,0];preview.gif([frames[i] for i in seq],out/'start-stop-120ms.gif',[480]+[120]*20+[480]);preview.flatten(frames[0],2).save(out/'idle-2x.png')
 rows=[]
 for outfit in ['forester','wayfarer']:
  pair=Image.new('RGBA',(512,256))
  for i,direction in enumerate(cfg['directions']):pair.alpha_composite(Image.open(D/direction/outfit/'00.png'),(i*256,0))
  rows.append(pair)
 board=Image.new('RGBA',(512,512));board.alpha_composite(rows[0],(0,0));board.alpha_composite(rows[1],(0,256));preview.flatten(board,2).save(D/'outfits-idle-2x.png')
if __name__=='__main__':main()
