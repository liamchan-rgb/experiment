#!/usr/bin/env python3
"""Render both scenes from exactly the same per-player appearance record.
Existing original motion/heads/clothing are composed; no game execution.
"""
from pathlib import Path
import importlib.util,sys,json,itertools,hashlib,dataclasses,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
binding=load('synchronized_appearance_binding',R/'scripts/appearance-scene-binding.py')
b=load('synchronized_appearance_battle',R/'scripts/build-chat-apparel-b-battle.py')
D=R/'Art/Review/Battle/appearance-synchronized-v1';D.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def digest(im):return hashlib.sha256(im.tobytes()).hexdigest()

def attack(age,weapon):
 t=age-.5;c='idle' if t<0 or t>=1.7 else 'attack'
 if weapon=='greatSword':a=t*1.0275/1.048 if t<=1.048 else 1.0275 if t<=1.148 else 1.0275+.7425*min(1,(t-1.148)/.552);q=np.clip((a-.12)/1.65,0,1)
 elif weapon=='legendaryStaff':a=t*1.25/1.048 if t<=1.048 else 1.25 if t<=1.148 else 1.25+.52*min(1,(t-1.148)/.552);q=np.clip((a-.12)/1.65,0,1)
 elif weapon=='huntingBow':q=0 if t<0 else 1 if t>1.7 else (max(0,t)/.86*((.86-.4)/1.2) if t<=.86 else np.clip((t-.4-min(.1,max(0,t-1.048)))/1.2,0,1))
 else:q=np.clip((t-.4-min(.1,max(0,t-1.048)))/1.2,0,1)
 return c,float(q)

def run():
 bindings=binding.SceneBindings();c=b.art.Compositor(R,bindings.file(bindings.data['walkingCatalog']),bindings.file(bindings.data['walkingMotion']))
 presets=list(bindings.data['presets']);players=[f'preview-{i+1}' for i in range(6)]
 for pid,name in zip(players,presets):bindings.set_player(pid,bindings.preset(name))
 before=bindings.player(players[0]);other=bindings.player(players[1]);a=dataclasses.replace(before,face=other.face)
 bindings.set_player(players[0],a);assert bindings.player(players[1])==other and bindings.player(players[0]).hair==before.hair
 try:bindings.set_player(players[0],dataclasses.replace(a,face='missing-face'))
 except ValueError:pass
 else:raise AssertionError('invalid face silently fell back')
 assert bindings.player(players[0])==a
 try:bindings.player('unconfigured-player')
 except ValueError:pass
 else:raise AssertionError('unknown player borrowed another head')
 bindings.set_player(players[0],before)
 # Deliberate cross-style/cross-outfit combinations, all weapon paths and states.
 combinations=[];count=0
 for hair in bindings.hair:
  for face,outfit in itertools.product(bindings.faces,bindings.outfits):
   choice=binding.Appearance(outfit,hair,face);bindings.set_player('cross-combination',choice)
   battle=b.Renderer.for_appearance(bindings,bindings.player('cross-combination'))
   expected=bindings.battle(choice)[1]
   assert set(battle.head)==set(expected)
   assert all(np.array_equal(np.asarray(battle.head[k]),np.asarray(Image.open(v).convert('RGBA'))) for k,v in expected.items())
   hashes={}
   for weapon,clip,p in itertools.product(b.WEAPONS,['idle','attack','guard','hit','victory','defeat','revive'],[0,.5,1]):
    im=battle.actor(weapon,clip,p);assert im.mode=='RGBA' and im.size==(256,256) and im.getbbox();hashes[f'{weapon}/{clip}/{p}']=digest(im);count+=1
   # Both scenes resolve the exact same chosen IDs, without deriving from gender,
   # wardrobe, weapon, player index or the previous actor's cached head.
   selected=bindings.walking_parts(choice);assert selected[2:]==[hair,face]
   for direction in ['down','right','up']:
    c.render(bindings.data['baseID'],selected,direction,'idle',0)
   combinations.append({'outfit':outfit,'hair':hair,'face':face,'battleHeadFiles':{k:str(v.relative_to(R)) for k,v in expected.items()},'battlePoseHashes':hashes})
  print('Verified walking + all battle weapons/states: '+hair,flush=True)
 # Six identities, two scenes side by side, both from player(pid). Left walks;
 # right uses the unchanged attack clock. No per-weapon identity fallback.
 weapons=['trainingSword','greatSword','huntingBow','legendaryStaff','huntingBow','greatSword']
 renderers={pid:b.Renderer.for_appearance(bindings,bindings.player(pid)) for pid in players};frames=[]
 def paired_frame(i):
  age=i*.02;frame=Image.new('RGB',(1536,560),'#1e3428');dr=ImageDraw.Draw(frame)
  for n,(pid,name,weapon) in enumerate(zip(players,presets,weapons)):
   choice=bindings.player(pid);x=n%3*512;y=n//3*280
   walking=c.render(bindings.data['baseID'],bindings.walking_parts(choice),'right','walk',int((i*20)//120)%8+1)
   clip,p=attack(age,weapon);battle=renderers[pid].actor(weapon,clip,p)
   frame.paste(walking,(x,y),walking);frame.paste(battle,(x+256,y),battle)
   label=bindings.hair[choice.hair]['label']+' / '+bindings.faces[choice.face]['label']
   dr.text((x+5,y+258),label,font=font,fill='#f3e1b8');dr.text((x+260,y+258),weapon+' / '+clip,font=font,fill='#f3e1b8')
  return frame
 for i in range(135):frames.append(paired_frame(i))
 b.art.gif(frames,D/'walking-battle-same-head-normal.gif',20)
 frames[0].save(D/'walking-battle-same-head-1x.png');frames[0].resize((3072,1120),Image.Resampling.NEAREST).save(D/'walking-battle-same-head-2x.png')
 board=Image.new('RGB',(1536,8*280),'#1e3428');dr=ImageDraw.Draw(board)
 for row,i in enumerate([0,25,42,59,69,79,99,134]):
  sample=frames[i];board.paste(sample.crop((0,0,1536,280)),(0,row*280))
 board.save(D/'male-paired-attack-phases-1x.png')
 board=Image.new('RGB',(1536,8*280),'#1e3428')
 for row,i in enumerate([0,25,42,59,69,79,99,134]):board.paste(frames[i].crop((0,280,1536,560)),(0,row*280))
 board.save(D/'female-paired-attack-phases-1x.png')
 # Compare all 24 hair/face combinations at rest, keeping entire figures.
 for sex,hairs in [('male',list(bindings.hair)[:3]),('female',list(bindings.hair)[3:])]:
  board=Image.new('RGB',(3*512,4*280),'#1e3428');dr=ImageDraw.Draw(board)
  for col,hair in enumerate(hairs):
   for row,face in enumerate(bindings.faces):
    outfit=list(bindings.outfits)[0 if sex=='male' else 1];choice=binding.Appearance(outfit,hair,face);x=col*512;y=row*280
    walk=c.render(bindings.data['baseID'],bindings.walking_parts(choice),'right','idle',0);actor=b.Renderer.for_appearance(bindings,choice).actor('huntingBow','idle',0)
    board.paste(walk,(x,y),walk);board.paste(actor,(x+256,y),actor);dr.text((x+5,y+258),bindings.hair[hair]['label']+' / '+bindings.faces[face]['label'],font=font,fill='#f3e1b8')
  board.save(D/(sex+'-all-faces-two-scenes-1x.png'))
 media=[]
 assert {p.name for p in D.glob('*.gif')}=={'walking-battle-same-head-normal.gif','both-armors-attack-normal.gif','both-armors-states-normal.gif'},'export both battle GIFs before checking synchronization'
 for path in D.glob('*.gif'):
  with Image.open(path) as im:
   duration=0
   for i in range(im.n_frames):im.seek(i);im.convert('RGB').load();duration+=im.info['duration']
   expected=2700 if 'attack' in path.name or 'same-head' in path.name else 4380;assert duration==expected
   media.append({'path':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':im.n_frames,'durationMs':duration})
 with Image.open(D/'walking-battle-same-head-normal.gif') as im:
  for index in [0,im.n_frames//3,im.n_frames*2//3,im.n_frames-1]:
   im.seek(index);im.convert('RGB').save(D/f'paired-actual-decoded-{index:03}.png')
 write(D/'sync-verification.json',{'artInputCommit':'067e019e7c03b20975ea99365390e81bdcf41333','singleAppearancePerPlayer':True,'hairAndFaceIndependent':True,'invalidSelectionKeepsPreviousIdentity':True,'missingPlayerRejected':True,'otherPlayerNotAffectedByEdit':True,'noOldHeadOverlayOrWeaponDefault':True,'combinations':combinations,'battlePosesRendered':count,'walkingWholeFiguresChecked':len(combinations)*3,'allNormalGIFsDecoded':media,'newArtApproval':None,'appRuntimeIntegrated':False,'appSimulatorOrDeviceRun':False})
 print(json.dumps({'combinations':len(combinations),'battlePoses':count,'walkingFigures':len(combinations)*3,'GIFs':media}),flush=True)

if __name__=='__main__':run()
