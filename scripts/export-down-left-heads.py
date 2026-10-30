#!/usr/bin/env python3
"""Register authored independent hair/features on the unchanged left-down head.
All source components/landmarks are author data; no runtime fit or ID branches.
"""
from pathlib import Path
import copy,hashlib,importlib.util,itertools,json,shutil
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/down-left/heads-v1';T=R/'Art/Templates/P1-Heads/down-left/v1-independent';D=R/'Art/Review/P1/modular-down-left-heads-v1'
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
compose=mod('compose',R/'scripts/compose-character-parts.py');helper=mod('helper',R/'scripts/export-character-head-part.py');preview=mod('preview',R/'scripts/export-neutral-direction.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def register(cfg,pack):
 src=cfg['sources'][pack['source']];assert sha(P/src['image'])==src['sha256'];raw=Image.open(P/src['image']).convert('RGBA');assert list(raw.size)==src['canvas'];h=raw.height;panel=raw.crop((pack['panel']*h,0,(pack['panel']+1)*h,h));a=np.array(panel);a[a[:,:,3]<cfg['sourceAlphaThreshold']]=0;a[a[:,:,3]>=cfg['sourceAlphaThreshold'],3]=255;l,n=label(a[:,:,3]>0,np.ones((3,3)));parts={}
 for slot,transfers in pack['slots'].items():
  out=Image.new('RGBA',(96,96))
  for transfer in transfers:
   b=a.copy()
   if transfer['components']!='all':b[~np.isin(l,transfer['components'])]=0
   s=transfer['scale'];x,y=transfer['translation'];im=Image.fromarray(b).transform((96,96),Image.Transform.AFFINE,(1/s,0,-x/s,0,1/s,-y/s),Image.Resampling.NEAREST);out.alpha_composite(im)
  assert out.getbbox(),(slot,'empty feature after registration');parts[slot]=out
 return parts

def main():
 cfg=json.loads((P/'authoring.json').read_text());B=R/cfg['bodyTemplate'];asset=json.loads((B/'asset.json').read_text());motion=json.loads((B/'motion.json').read_text());assert sha(B/'asset.json')==cfg['baseManifestSHA256'] and sha(B/'motion.json')==cfg['baseMotionSHA256'];T.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True);catalog=[{'id':asset['id'],'manifest':str((B/'asset.json').relative_to(R))}]
 for name,pack in cfg['packages'].items():
  folder=P/name;(folder/'png').mkdir(parents=True,exist_ok=True);(folder/'source').mkdir(exist_ok=True);src=cfg['sources'][pack['source']];shutil.copyfile(P/src['image'],folder/src['image']);shutil.copyfile(P/src['prompt'],folder/'source/prompt.txt');parts=register(cfg,pack)
  for slot,im in parts.items():im.save(folder/'png'/(slot+'.png'))
  helper.editable(folder,parts)
  (folder/'authoring.json').write_text(json.dumps({'id':pack['id'],'source':{**cfg['sources'][pack['source']],'prompt':'source/prompt.txt'},'panel':pack['panel'],'registration':pack['slots'],'headLocalOrigin':cfg['headLocalOrigin'],'authorAndReviewer':'root','subagentsUsed':False,'artApproval':None},indent=2)+'\n')
  manifest={'schemaVersion':'1.0.0','id':pack['id'],'version':'1.0.0','part':pack['part'],'compatibility':asset['compatibility'],'mode':'head-local','slots':list(parts),'directions':['down-left'],'clips':asset['clips'],'sourceFiles':['authoring.json',src['image'],'source/prompt.txt','editable.ora','editable.svg'],'bindings':[{'direction':'down-left','clip':f['clip'],'frame':f['frame'],'layers':{slot:'png/'+slot+'.png' for slot in parts}} for f in motion['frames']]};(folder/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n');catalog.append({'id':pack['id'],'manifest':str((folder/'asset.json').relative_to(R))})
 for f in motion['frames']:f['drawOrder']+=['face.eyes','face.brows','face.nose','face.mouth','hair.front'];f['artApproval']=None
 motion['status']='down-left-independent-head-resources-candidate';motion['artApproval']=None;(T/'motion.json').write_text(json.dumps(motion,indent=2)+'\n');(T/'catalog.json').write_text(json.dumps({'assets':catalog},indent=2)+'\n')
 comp=compose.Compositor(R,T/'catalog.json',T/'motion.json');rendered={}
 for hair,face in itertools.product(['hair-chestnut','hair-silver'],['face-blue','face-amber']):
  out=D/'combinations'/(hair+'__'+face);out.mkdir(parents=True,exist_ok=True);frames=[]
  for i,f in enumerate(motion['frames']):
   im=comp.render(asset['id'],[cfg['packages'][hair]['id'],cfg['packages'][face]['id']],'down-left',f['clip'],f['frame']);im.save(out/f'{i:02}.png');frames.append(im)
  preview.gif(frames[1:9],out/'walk-120ms.gif');preview.gif([frames[i] for i in [0,9,10]+list(range(1,9))*2+[11,12,0]],out/'start-stop-120ms.gif',[480]+[120]*20+[480]);preview.flatten(frames[0],2).save(out/'idle-2x.png');board=Image.new('RGB',(1024,1024),'#17372c')
  for i,im in enumerate(frames):x,y=i%4*256,i//4*256;board.paste(preview.flatten(im),(x,y));ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white')
  board.save(out/'all-poses-fullbody-1x.png');board.resize((2048,2048),Image.Resampling.NEAREST).save(out/'all-poses-fullbody-2x.png');rendered[hair,face]=frames
 paired=[]
 for i in range(13):
  pair=Image.new('RGBA',(512,256));pair.alpha_composite(rendered['hair-chestnut','face-blue'][i]);pair.alpha_composite(rendered['hair-silver','face-amber'][i],(256,0));paired.append(pair)
 preview.flatten(paired[0],2).save(D/'idle-comparison-2x.png');preview.gif(paired[1:9],D/'walk-comparison-120ms.gif');preview.gif([paired[i] for i in [0,9,10]+list(range(1,9))*2+[11,12,0]],D/'start-stop-comparison-120ms.gif',[480]+[120]*20+[480])
 board=Image.new('RGBA',(512,512))
 for i,key in enumerate(rendered):board.alpha_composite(rendered[key][0],(i%2*256,i//2*256))
 preview.flatten(board,2).save(D/'cross-combinations-2x.png');print('Exported four independent head packages and four13-pose actual combinations')
if __name__=='__main__':main()
