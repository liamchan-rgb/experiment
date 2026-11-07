#!/usr/bin/env python3
"""Add four shared-motion transition poses to retained down r6 art; preserve old nine poses."""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json,math,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageSequence
R=Path(__file__).resolve().parents[1];B=R/'Art/Templates/P1-Neutral/down/walk-r7-transitions';P=R/'Art/Parts/P1-v1/down/transitions-v1';T=R/'Art/Templates/P1-Wardrobe/down/v10-transitions';D=R/'Art/Review/P1/modular-down-transitions-v1'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=mod('downcompose',R/'scripts/compose-character-parts.py');edit=mod('downedit',R/'scripts/export-wardrobe-part.py');preview=mod('downpreview',R/'scripts/export-neutral-direction.py')
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def blend(a,b,t):return (np.asarray(a)*(1-t)+np.asarray(b)*t).tolist()
def arm_matrix(arms,side,k,w):
 angle=math.radians(arms[f'{side}AngleDeg'][k]*w);a,b,c,d=math.cos(angle),-math.sin(angle),math.sin(angle),math.cos(angle);dx,dy=np.asarray(arms[f'{side}RelativeXY'][k])*w;dy+=arms['bodyBobY'][k]*w;px,py=arms['shoulderPivots'][side];return [a,b,c,d,px-a*px-c*py+dx,py-b*px-d*py+dy]
def point(m,p):a,b,c,d,x,y=m;return [a*p[0]+c*p[1]+x,b*p[0]+d*p[1]+y]
def leg_uv(cfg,old,k,w,side):
 f0,f=old['frames'][0],old['frames'][k];S=side.title();row=np.array(cfg['legSourceRows'],float);bob=f['bodyTranslation'][1]*w
 target=[row[0]+bob,row[1]+bob,blend(f0['joints']['hip'+S],f['joints']['hip'+S],w)[1],blend(f0['joints']['knee'+S],f['joints']['knee'+S],w)[1],blend(f0['joints']['ankle'+S],f['joints']['ankle'+S],w)[1],blend(f0['soleMarkers'][side],f['soleMarkers'][side],w)[1],255+(f['soleMarkers'][side][1]-f0['soleMarkers'][side][1])*w]
 assert np.all(np.diff(target)>0),'leg warp folded'
 tx=[cfg['legSourceX'][side][0],cfg['legSourceX'][side][1],blend(f0['joints']['hip'+S],f['joints']['hip'+S],w)[0],blend(f0['joints']['knee'+S],f['joints']['knee'+S],w)[0],blend(f0['joints']['ankle'+S],f['joints']['ankle'+S],w)[0],blend(f0['soleMarkers'][side],f['soleMarkers'][side],w)[0],blend(f0['soleMarkers'][side],f['soleMarkers'][side],w)[0]]
 yy,xx=np.mgrid[:256,:256];sy=np.interp(yy,target,row);dx=np.interp(sy,row,np.array(tx)-np.array(cfg['legSourceX'][side]));sx=xx-dx;valid=(sx>=0)&(sx<256)&(sy>=0)&(sy<256);uv=np.zeros((256,256,4),np.uint8);uv[:,:,0]=np.clip(np.floor(sx+.5),0,255);uv[:,:,1]=np.clip(np.floor(sy+.5),0,255);uv[:,:,3]=valid*255
 return uv,{'sourceRows':row.tolist(),'targetRows':target,'sourceX':cfg['legSourceX'][side],'targetX':tx,'minimumRowGap':float(np.diff(target).min())}
def sample(im,uv):
 a=np.array(im);out=a[uv[:,:,1],uv[:,:,0]].copy();out[uv[:,:,3]==0]=0;return Image.fromarray(out)
def tails(idle,tailcfg,k,w,bob):
 out=Image.new('RGBA',(256,256))
 for side,box in [('right',(0,0,125,256)),('left',(125,0,256,256))]:
  part=Image.new('RGBA',(256,256));part.paste(idle.crop(box),box[:2]);theta=math.radians((tailcfg[f'{side}AngleDeg'][k]-tailcfg[f'{side}AngleDeg'][0])*w);a,b,c,d=math.cos(theta),-math.sin(theta),math.sin(theta),math.cos(theta);px,py=tailcfg['pivots'][side];out.alpha_composite(compose.place(part,[a,b,c,d,px-a*px-c*py,py-b*px-d*py+bob],(256,256)))
 return out
def main():
 cfg=json.loads((B/'authoring.json').read_text());old=json.loads((R/cfg['oldMotion']).read_text());arms=json.loads((R/cfg['armAuthoring']).read_text());assert sha(R/cfg['oldMotion'])==cfg['oldMotionSHA256'];sources={n:R/p for n,p in cfg['sources'].items()};assert sha(sources['base']/'asset.json')==cfg['baseManifestSHA256'];manifests={n:json.loads((p/'asset.json').read_text()) for n,p in sources.items()};dest={n:B if n=='base' else P/n for n in sources};ids={n:'p1-neutral-down-walk-r7-transitions' if n=='base' else 'p1-down-'+n+'-transitions-v1' for n in sources};bindings={n:[] for n in sources};motion=copy.deepcopy(old);motion.update(status='down-authored-transition-candidate',artApproval=None,canvas=[256,256]);motion.pop('socketAngles',None);motion['frames']=[];audit=[]
 for tag,folder in dest.items():
  folder.mkdir(parents=True,exist_ok=True);(folder/'source').mkdir(exist_ok=True);shutil.copyfile(sources[tag]/'asset.json',folder/'source/manifest-original.json');write(folder/'source/provenance.json',{'source':cfg['sources'][tag],'manifestSHA256':sha(sources[tag]/'asset.json'),'operation':'old9 artwork byte-copy; four transition bindings share authored transforms','newArtworkApproval':None})
 for tag in sources:
  if manifests[tag]['mode']=='head-local':
   for slot,path in manifests[tag]['bindings'][0]['layers'].items():
    q=dest[tag]/'png'/(slot+'.png');q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sources[tag]/path,q)
 for i in range(13):
  transition=i>=9;recipe=cfg['transitionPoses'][i-9] if transition else None;k=recipe['walkPose'] if transition else i;w=recipe['walkWeight'] if transition else 1;bob=old['frames'][k]['bodyTranslation'][1]*w;clip=recipe['clip'] if transition else ('idle' if i==0 else 'walk');frame=recipe['frame'] if transition else i;f=copy.deepcopy(old['frames'][i if not transition else 0]);f.update(direction='down',clip=clip,frame=frame,artApproval=None)
  if transition:
   f['bodyTranslation']=[0,bob];f['headToCanvas']=blend(old['frames'][0]['headToCanvas'],old['frames'][k]['headToCanvas'],w);f['joints']={j:blend(v,old['frames'][k]['joints'][j],w) for j,v in old['frames'][0]['joints'].items()};f['soleMarkers']={s:blend(old['frames'][0]['soleMarkers'][s],old['frames'][k]['soleMarkers'][s],w) for s in ['left','right']};f['support']='right';f['sockets']={}
  # Replace stale gripping-era metadata with actual natural-arm source anchors.
  matrices={s:arm_matrix(arms,s,k,w) for s in ['left','right']}
  for side in ['left','right']:
   for joint,p in cfg['armIdleJoints'][side].items():f['joints'][joint+side.title()]=point(matrices[side],p)
  if not transition and i in [4,8]:f['support']='left' if i==4 else 'right'
  uv={};legAudit={}
  if transition:
   for side in ['left','right']:
    uv[side],legAudit[side]=leg_uv(cfg,old,k,w,side);q=B/'source-uv'/f'{i:02}'/('leg.'+side+'.png');q.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(uv[side]).save(q)
  for tag,source in sources.items():
   folder=dest[tag];head=manifests[tag]['mode']=='head-local';parts={};paths={};slots=manifests[tag]['slots']
   for slot in slots:
    if head:paths[slot]='png/'+slot+'.png';continue
    q=folder/('layers' if tag=='base' else 'png')/f'{i:02}'/(slot+'.png');q.parent.mkdir(parents=True,exist_ok=True)
    if not transition:
     path=manifests[tag]['bindings'][i]['layers'][slot];shutil.copyfile(source/path,q);im=Image.open(q).convert('RGBA')
    else:
     idle=Image.open(source/manifests[tag]['bindings'][0]['layers'][slot]).convert('RGBA')
     if slot.startswith(('body.leg.','outfit.pants.','outfit.boot.')):im=sample(idle,uv[slot.rsplit('.',1)[1]])
     elif slot.startswith(('body.arm.','body.hand.','outfit.sleeve.')):im=compose.place(idle,matrices[slot.rsplit('.',1)[1]],(256,256))
     elif tag=='wayfarer' and slot=='outfit.hem.front':im=tails(idle,json.loads((source/'authoring.json').read_text())['coatTailMotion'],k,w,bob)
     else:im=compose.place(idle,[1,0,0,1,0,bob],(256,256))
     im.save(q)
    parts[slot]=im;paths[slot]=str(q.relative_to(folder))
   if not head:
    (folder/'editable').mkdir(exist_ok=True);edit.editable(folder/'editable',f'{i:02}',{s:parts[s] for s in f['drawOrder'] if s in parts})
   bindings[tag].append({'direction':'down','clip':clip,'frame':frame,'layers':paths})
  motion['frames'].append(f);audit.append({'index':i,'oldPosePixelsCopied':not transition,'transitionRecipe':recipe,'bodyBob':bob,'armMatrices':matrices,'legUV':legAudit,'sourcePoseForNewArt':0 if transition else i})
 catalog=[]
 for tag,folder in dest.items():
  a=copy.deepcopy(manifests[tag]);a.update(id=ids[tag],version='1.0.0',clips=['idle','walk','walk-start','walk-stop'],bindings=bindings[tag]);a['sourceFiles']=[str(p.relative_to(folder)) for root in ['source','editable'] for p in sorted((folder/root).rglob('*')) if p.is_file()]+(['authoring.json'] if tag=='base' else []);write(folder/'asset.json',a);catalog.append({'id':ids[tag],'manifest':str((folder/'asset.json').relative_to(R))})
 motion['baseManifestSHA256']=sha(B/'asset.json');motion['transitionScope']='specified idle->walk01,walk08->idle; no arbitrary phase interruptions';write(T/'catalog.json',{'assets':catalog});write(T/'motion.json',motion);write(D/'rig-audit.json',{'authorAndReviewer':'root','subagentsUsed':False,'artApproval':None,'poses':audit,'metadataCorrections':cfg['metadataCorrections']});write(D/'sequence.json',{'indices':cfg['sequence'],'durationsMs':cfg['durationsMs'],'arbitraryPhaseInterrupts':False,'artApproval':None})
 c=compose.Compositor(R,T/'catalog.json',T/'motion.json');renders={}
 for hair,face,style,carry in itertools.product(['chestnut','silver','teal-crop'],['blue','amber'],['plain','forester','wayfarer'],['empty','back']):
  name='__'.join([hair,face,style,carry]);selected=[ids['hair-'+hair],ids['face-'+face]]+([ids[style]] if style!='plain' else [])+([ids['back-scabbard']] if carry=='back' else []);out=D/'combinations'/name;out.mkdir(parents=True,exist_ok=True);items=[]
  for i,f in enumerate(motion['frames']):
   im=c.render(ids['base'],selected,'down',f['clip'],f['frame']);im.save(out/f'{i:02}.png');items.append(im)
  renders[name]=items
  if face=='blue' and style!='plain' and carry=='back':board(items,out/'all-poses-fullbody-1x.png')
 bare=[]
 for i,f in enumerate(motion['frames']):
  im=c.render(ids['base'],[],'down',f['clip'],f['frame']);q=B/'frames'/f'{i:02}.png';q.parent.mkdir(exist_ok=True);im.save(q);bare.append(im)
 board(bare,D/'neutral-all-poses-fullbody-1x.png')
 pair=[]
 for i in range(13):
  im=Image.new('RGBA',(512,256));im.alpha_composite(renders['chestnut__blue__forester__back'][i],(0,0));im.alpha_composite(renders['chestnut__blue__wayfarer__back'][i],(256,0));pair.append(im)
 preview.gif(pair[1:9],D/'outfits-walk-120ms.gif');preview.gif([pair[i] for i in cfg['sequence']],D/'outfits-start-stop-120ms.gif',cfg['durationsMs']);preview.flatten(pair[0],2).save(D/'outfits-idle-2x.png');order=[0,9,10,1,8,11,12,0];board([pair[i] for i in order],D/'transitions-fullbody-1x.png',names=['idle00','start01','start02','walk01','walk08','stop01','stop02','idle00'])
 with Image.open(D/'outfits-start-stop-120ms.gif') as gif:
  decoded=[f.convert('RGB').copy() for f in ImageSequence.Iterator(gif)]
  sel=[0,1,2,3,18,19,20,21];board(decoded,D/'actual-gif-boundaries-1x.png',indices=sel,names=[str(i) for i in sel],double=False)
 print(json.dumps({'poses':13,'combinations':len(renders),'actualCompositions':len(renders)*13,'old9Pixels':'copied unchanged','newPoses':4,'artApproval':None}))
def board(items,path,indices=None,names=None,double=True):
 indices=indices or list(range(len(items)));w,h=items[0].size;cols=4 if w==256 else 2;rows=math.ceil(len(indices)/cols);out=Image.new('RGB',(w*cols,h*rows),'#17372c');draw=ImageDraw.Draw(out)
 for n,i in enumerate(indices):
  x,y=n%cols*w,n//cols*h;out.paste(preview.flatten(items[i].convert('RGBA')),(x,y));draw.text((x+5,y+5),names[n] if names else f'{i:02}',fill='white')
 out.save(path)
 if double:out.resize((out.width*2,out.height*2),Image.Resampling.NEAREST).save(path.with_name(path.stem.replace('1x','2x')+path.suffix))
if __name__=='__main__':main()
