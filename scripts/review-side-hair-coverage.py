#!/usr/bin/env python3
"""Review revised side hair on unchanged characters; no App execution."""
from pathlib import Path
import importlib.util,sys,json,subprocess,os,io,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
D=R/'Art/Review/P1/side-hair-coverage-r2'
BASELINE='ec0cf30811054c1e883841894914afdb43c07593'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
b=load('side_coverage_battle',R/'scripts/build-chat-apparel-b-battle.py')
a=load('side_coverage_choice',R/'scripts/appearance-scene-binding.py')
sync=load('side_coverage_sync_review',R/'scripts/review-synchronized-appearance.py')
check=load('side_coverage_contract',R/'scripts/check-character-part.py')
def old_bytes(rel):
 p=subprocess.run(['git','-c','gc.auto=0','show',BASELINE+':'+rel],cwd=R,env=dict(os.environ,GIT_NO_LAZY_FETCH='1'),capture_output=True)
 if p.returncode:raise ValueError('Before source unavailable: '+BASELINE+':'+rel)
 return p.stdout
def run():
 D.mkdir(parents=True,exist_ok=True);bindings=a.SceneBindings()
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
 old=b.art.Compositor(R,bindings.file(bindings.data['walkingCatalog']),bindings.file(bindings.data['walkingMotion']))
 new=b.art.Compositor(R,bindings.file(bindings.data['walkingCatalog']),bindings.file(bindings.data['walkingMotion']))
 oldheads={};checks=[];changed=[]
 for row in bindings.data['hair']:
  manifest=bindings.file(row['locomotionManifest']);errors=check.check_asset(manifest);assert not errors,(manifest,errors)
  for direction in ['down','down-left','left','up-left','up','up-right','right','down-right']:
   path=manifest.parent/f'masters/{direction}/hair.front.png';rel=path.relative_to(R).as_posix()
   prev=old_bytes(rel);current=path.read_bytes()
   before=np.asarray(Image.open(io.BytesIO(prev)).convert('RGBA'));after=np.asarray(Image.open(path).convert('RGBA'))
   assert after.shape==(96,96,4) and not np.any(after[:,:,:3][after[:,:,3]==0])
   if direction in ['left','right','down-left','down-right']:
    assert np.count_nonzero(after[:,:,3]>128)>np.count_nonzero(before[:,:,3]>128),(row['id'],direction)
    old.images[path.resolve()]=Image.fromarray(before)
    for face in bindings.data['faces']:
     fp=bindings.file(face['locomotionManifest']).parent/f'masters/{direction}/face.eyes.png';eyes=np.asarray(Image.open(fp).convert('RGBA'))[:,:,3]
     assert not np.any((after[:,:,3]>128)&(eyes>128)),(row['id'],direction,face['id'])
   else:assert prev==current,('unrequested view changed',rel)
   if prev!=current:changed.append({'path':rel,'beforeSHA256':hashlib.sha256(prev).hexdigest(),'afterSHA256':hashlib.sha256(current).hexdigest()})
   checks.append({'hair':row['id'],'direction':direction,'beforeHairPixels':int(np.count_nonzero(before[:,:,3]>128)),'afterHairPixels':int(np.count_nonzero(after[:,:,3]>128)),'visibleEyePixelsCovered':0})
  path=bindings.file(row['battleLayers']['MeadowBattleHeroHair'])
  oldheads[row['id']]=Image.open(io.BytesIO(old_bytes(path.relative_to(R).as_posix()))).convert('RGBA')
 previous=json.loads((R/'Art/Integration/Appearance-battle-custom-heads-v1/verification.json').read_text());kept=[]
 for row in previous['PNGFiles']:
  rel=row['path'];hair='/custom-heads-v1/hair-' in rel
  affected=hair and ('/battle/hair.png' in rel or any('/masters/'+d+'/' in rel for d in ['left','right','down-left','down-right']))
  if not affected:assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==row['sha256'],rel;kept.append(rel)
 assert len(kept)==196
 board=Image.new('RGB',(1024,1680),'#1e3428');dr=ImageDraw.Draw(board)
 for row,name in enumerate(bindings.data['presets']):
  choice=bindings.preset(name);parts=bindings.walking_parts(choice)
  current=b.Renderer.for_appearance(bindings,choice);before=b.Renderer.for_appearance(bindings,choice)
  before.head=dict(before.head);before.head['MeadowBattleHeroHair']=oldheads[choice.hair]
  figures=[old.render(bindings.data['baseID'],parts,'right','idle',0),new.render(bindings.data['baseID'],parts,'right','idle',0),before.actor('huntingBow','idle',0),current.actor('huntingBow','idle',0)]
  for col,im in enumerate(figures):
   board.paste(im,(col*256,row*280),im);dr.text((col*256+5,row*280+258),name+' '+['walk BEFORE','walk AFTER','bow BEFORE','bow AFTER'][col],font=font,fill='#f3e1b8')
 board.save(D/'side-before-after-whole-body-1x.png');board.resize((2048,3360),Image.Resampling.NEAREST).save(D/'side-before-after-whole-body-2x.png')
 for direction in ['left','right','down-left','down-right']:
  board=Image.new('RGB',(1536,280),'#1e3428');dr=ImageDraw.Draw(board)
  for col,name in enumerate(bindings.data['presets']):
   choice=bindings.preset(name);im=new.render(bindings.data['baseID'],bindings.walking_parts(choice),direction,'idle',0)
   board.paste(im,(col*256,0),im);dr.text((col*256+5,258),name+' '+direction,font=font,fill='#f3e1b8')
  board.save(D/(direction+'-all-six-whole-body-1x.png'))
 for name in bindings.data['presets']:
  choice=bindings.preset(name);frames=[]
  for frame_index in range(1,9):
   frame=Image.new('RGB',(1024,560),'#1e3428')
   for i,direction in enumerate(['down','down-left','left','up-left','up','up-right','right','down-right']):
    im=new.render(bindings.data['baseID'],bindings.walking_parts(choice),direction,'walk',frame_index)
    frame.paste(b.art.cell(im,direction),(i%4*256,i//4*280))
   frames.append(frame)
  b.art.gif(frames,D/(name+'-eight-way-normal.gif'),120)
 b.review(destination=D,statesheets=False,decode_pages=False)
 sync.D=D;sync.run()
 proof=json.loads((D/'sync-verification.json').read_text());proof['artInputCommit']=BASELINE;proof['hairRevision']='side-hair-coverage-r2'
 (D/'sync-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
 for path in D.glob('*-eight-way-normal.gif'):
  with Image.open(path) as im:
   durations=[]
   for i in range(im.n_frames):im.seek(i);im.convert('RGB').load();durations.append(im.info['duration'])
   assert durations==[120]*8
 (D/'coverage-verification.json').write_text(json.dumps({'beforeSourceCommit':BASELINE,'sixStylesFourRepairedViews':True,'coverage':checks,'changedDirectionalHairPNGs':changed,'battleHairPNGsUpdated':6,'eyesFaceSkinBodyClothingUnchanged':True,'unchangedResourcePNGCount':len(kept),'unchangedPNGPaths':kept,'unchangedFrontAndThreeBackViews':True,'walkingGIFs':6,'walkingCadenceMs':120,'newArtApproval':None,'runtimeImported':False,'appSimulatorOrDeviceRun':False},ensure_ascii=False,indent=2)+'\n')
 print('PASS: 24 revised side/diagonal hair masters + 6 battle hairs; eyes clear; 196 other PNGs unchanged.',flush=True)
if __name__=='__main__':run()
