#!/usr/bin/env python3
"""F1 ear-cover consistency: preserve the front reference and repair side views."""
from pathlib import Path
import importlib.util,sys,json,hashlib,subprocess,os,io,itertools
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/P1/purple-ear-cover-r4';BEFORE='71a6aaa38d0e39ca1d96ba4133eb8c7fea9abe0f';ID='p1-custom-hair-f1-bob-v1'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
b=load('purple_bob_battle',R/'scripts/build-chat-apparel-b-battle.py');a=load('purple_bob_binding',R/'scripts/appearance-scene-binding.py');timing=load('purple_bob_clock',R/'scripts/review-synchronized-appearance.py');contract=load('purple_bob_contract',R/'scripts/check-character-part.py')
def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def old_bytes(rel):return subprocess.check_output(['git','-c','gc.auto=0','show',BEFORE+':'+rel],cwd=R,env=dict(os.environ,GIT_NO_LAZY_FETCH='1'))
def save_gif(frames,path,ms):
 # Fixed palette from eight full-frame samples, avoiding the old giant strip.
 # This preserves the original clock and avoids per-frame colour flicker.
 sample=Image.new('RGB',(frames[0].width*4,frames[0].height*2))
 for j,i in enumerate(np.linspace(0,len(frames)-1,8).astype(int)):sample.paste(frames[i],(j%4*frames[0].width,j//4*frames[0].height))
 palette=sample.quantize(colors=256);encoded=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
 encoded[0].save(path,save_all=True,append_images=encoded[1:],duration=ms,loop=0,disposal=1,optimize=True)
def run():
 D.mkdir(parents=True,exist_ok=True);s=a.SceneBindings();font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12);part=R/'Art/Parts/P1-v1/custom-heads-v1/hair-f1-bob';assert not contract.check_asset(part/'asset.json')
 previous=json.loads((D/'input-pngs.json').read_text());kept=[];changed=[]
 for row in previous['files']:
  p=R/row['path'];current=sha(p.read_bytes())
  if '/hair-f1-bob/' in row['path']:assert current!=row['sha256'];changed.append({'path':row['path'],'beforeSHA256':row['sha256'],'afterSHA256':current})
  else:assert current==row['sha256'],row['path'];kept.append(row)
 assert len(changed)==9 and len(kept)==217
 reference='42df0a0a3c2b15f8e67bf3787d47e7d8ae6564f5';reference_files=[];ear_checks=[]
 def ref_bytes(rel):return subprocess.check_output(['git','-c','gc.auto=0','show',reference+':'+rel],cwd=R,env=dict(os.environ,GIT_NO_LAZY_FETCH='1'))
 for direction in b.art.DIRECTIONS:
  image=part/f'masters/{direction}/hair.front.png';hair=np.asarray(Image.open(image).convert('RGBA'));assert not np.any(hair[:,:,:3][hair[:,:,3]==0]);_,components=label(hair[:,:,3]>128,np.ones((3,3)));assert components==1,(direction,components)
  if direction not in ['left','right']:
   for path in [image,part/f'editable/{direction}.svg']:
    rel=path.relative_to(R).as_posix();assert path.read_bytes()==ref_bytes(rel),rel;reference_files.append({'path':rel,'sha256':sha(path.read_bytes())})
  else:
   x0,x1=(39,51) if direction=='right' else (45,57);area=hair[48:65,x0:x1,3];assert np.all(area>128),(direction,'ear still visible')
   before=np.asarray(Image.open(io.BytesIO(old_bytes(image.relative_to(R).as_posix()))).convert('RGBA'))[48:65,x0:x1,3]
   ear_checks.append({'direction':direction,'localEarBox':[x0,48,x1,65],'opaqueHairPixels':int((area>128).sum()),'totalEarBoxPixels':int(area.size),'previousOpaqueHairPixels':int((before>128).sum())})
   for face in s.faces:
    p=s.file(s.faces[face]['locomotionManifest']).parent/f'masters/{direction}/face.eyes.png';eyes=np.asarray(Image.open(p).convert('RGBA'))[:,:,3];assert not np.any((hair[:,:,3]>128)&(eyes>128)),(direction,face)
 battle_hair=np.asarray(Image.open(part/'battle/hair.png').convert('RGBA'));assert np.all(battle_hair[110:125,114:128,3]>128),'battle ear still visible'
 assert (part/'palette.json').read_bytes()==ref_bytes((part/'palette.json').relative_to(R).as_posix())
 c=b.art.Compositor(R,s.file(s.data['walkingCatalog']),s.file(s.data['walkingMotion']));old=b.art.Compositor(R,s.file(s.data['walkingCatalog']),s.file(s.data['walkingMotion']))
 for p in part.rglob('*.png'):old.images[p.resolve()]=Image.open(io.BytesIO(old_bytes(p.relative_to(R).as_posix()))).convert('RGBA')
 base=s.preset('f1-bob');blue=a.Appearance(list(s.outfits)[0],ID,base.face);board=Image.new('RGB',(1024,1120),'#1e3428');dr=ImageDraw.Draw(board)
 for i,direction in enumerate(b.art.DIRECTIONS):
  for current,comp in enumerate([old,c]):
   x=i%4*256;y=(i//4*2+current)*280;im=comp.render(s.data['baseID'],s.walking_parts(blue),direction,'idle',0);board.paste(im,(x,y),im);dr.text((x+5,y+258),('OLD short' if current==0 else 'R4 ref match')+' '+direction,font=font,fill='#f3e1b8')
 board.save(D/'before-after-eight-directions-1x.png');board.resize((2048,2240),Image.Resampling.NEAREST).save(D/'before-after-eight-directions-2x.png')
 strip=Image.new('RGB',(1280,280),'#1e3428');dr=ImageDraw.Draw(strip);stripfont=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
 figures=[c.render(s.data['baseID'],s.walking_parts(base),'down','idle',0),old.render(s.data['baseID'],s.walking_parts(base),'right','idle',0),c.render(s.data['baseID'],s.walking_parts(base),'left','idle',0),c.render(s.data['baseID'],s.walking_parts(base),'right','idle',0),b.Renderer.for_appearance(s,base).actor('huntingBow','idle',0)]
 for i,(figure,caption) in enumerate(zip(figures,['FRONT reference','OLD wrong side','R4 left','R4 right','R4 battle'])):
  strip.paste(figure,(i*256,0),figure);dr.text((i*256+5,258),caption,font=stripfont,fill='#f3e1b8')
 strip.save(D/'front-side-battle-1x.png');strip.resize((2560,560),Image.Resampling.NEAREST).save(D/'front-side-battle-2x.png')
 walking=0;battles=0;combos=[]
 for face,outfit in itertools.product(s.faces,s.outfits):
  choice=a.Appearance(outfit,ID,face);digest=hashlib.sha256()
  for direction,clip,frame in sorted(c.frames):digest.update(c.render(s.data['baseID'],s.walking_parts(choice),direction,clip,frame).tobytes());walking+=1
  renderer=b.Renderer.for_appearance(s,choice)
  for weapon,clip,p in itertools.product(b.WEAPONS,['idle','attack','guard','hit','victory','defeat','revive'],[0,.5,1]):digest.update(renderer.actor(weapon,clip,p).tobytes());battles+=1
  combos.append({'face':face,'outfit':outfit,'walkingAndBattleRGBA':digest.hexdigest()})
 assert walking==832 and battles==672
 print('PASS: all four face sets x two clothes, 832 walk poses and 672 battle poses.',flush=True)
 # New F1 only, all eight directions at the existing 120ms gait.
 frames=[]
 for frame in range(1,9):
  image=Image.new('RGB',(1024,560),'#1e3428')
  for i,direction in enumerate(b.art.DIRECTIONS):
   im=c.render(s.data['baseID'],s.walking_parts(base),direction,'walk',frame);image.paste(b.art.cell(im,direction),(i%4*256,i//4*280))
  frames.append(image)
 save_gif(frames,D/'ear-cover-eight-way-normal.gif',120)
 choices=[a.Appearance(outfit,ID,base.face) for outfit in s.outfits];renderers=[b.Renderer.for_appearance(s,x) for x in choices];frames=[]
 for i in range(135):
  frame=Image.new('RGB',(1280,560),'#1e3428');dr=ImageDraw.Draw(frame)
  for row,(choice,renderer) in enumerate(zip(choices,renderers)):
   im=c.render(s.data['baseID'],s.walking_parts(choice),'right','walk',i//6%8+1);frame.paste(im,(0,row*280),im);dr.text((5,row*280+258),'R4 walking',font=font,fill='#f3e1b8')
   for col,weapon in enumerate(b.WEAPONS,1):
    clip,p=timing.attack(i*.02,weapon);im=renderer.actor(weapon,clip,p);frame.paste(im,(col*256,row*280),im);dr.text((col*256+5,row*280+258),weapon+' '+clip,font=font,fill='#f3e1b8')
  frames.append(frame)
 save_gif(frames,D/'ear-cover-walk-battle-normal.gif',20);frames[0].save(D/'standing-and-battle-1x.png');frames[0].resize((2560,1120),Image.Resampling.NEAREST).save(D/'standing-and-battle-2x.png')
 for row,(choice,renderer) in enumerate(zip(choices,renderers)):
  board=Image.new('RGB',(1024,1960),'#1e3428');dr=ImageDraw.Draw(board)
  for y,clip in enumerate(['idle','attack','guard','hit','victory','defeat','revive']):
   for col,weapon in enumerate(b.WEAPONS):
    im=renderer.actor(weapon,clip,.5);board.paste(im,(col*256,y*280),im);dr.text((col*256+5,y*280+258),weapon+' '+clip,font=font,fill='#f3e1b8')
  board.save(D/f'battle-states-{row+1}-1x.png')
 media=[]
 for p in D.glob('*.gif'):
  with Image.open(p) as im:
   total=0
   for i in range(im.n_frames):im.seek(i);im.convert('RGB').load();total+=im.info['duration']
   assert total==(960 if 'eight-way' in p.name else 2700)
   for index in [0,im.n_frames//2,im.n_frames-1]:im.seek(index);im.convert('RGB').save(D/f'{p.stem}-decoded-{index:03}.png')
   media.append({'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'frames':im.n_frames,'durationMs':total})
 write(D/'verification.json',{'beforeSourceCommit':BEFORE,'changedHairPNGs':changed,'unchanged217PNGFiles':kept,'frontReferenceCommit':reference,'sixReferenceViewsByteExact':reference_files,'earCoverage':ear_checks,'orthogonalSideEyePixelsClear':True,'battleEarCoreCovered':True,'noDetachedHairPixels':True,'motionSHA256':sha(s.file(s.data['walkingMotion']).read_bytes()),'walkPoses':walking,'battlePoses':battles,'combinations':combos,'media':media,'newArtApproval':None,'runtimeImported':False,'appSimulatorOrDeviceRun':False})
 print(json.dumps({'earCoverage':ear_checks,'walkPoses':walking,'battlePoses':battles,'unchangedPNG':len(kept),'media':media}),flush=True)
if __name__=='__main__':run()
