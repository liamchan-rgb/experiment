from pathlib import Path
import importlib.util,math,json
ROOT=Path(__file__).resolve().parents[1]
import numpy as np
from PIL import Image
p=ROOT/'scripts/review-b2-weapons-actions.py';s=importlib.util.spec_from_file_location('study',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);enemy=np.asarray(m.enemy)[:,:,3]>128;ex=round(m.ENEMY_FOOT[0]-178.5*m.ES);ey=round(m.ENEMY_FOOT[1]-240*m.ES);impact=m.impact;alpha=enemy[round(impact[1])-ey,round(impact[0])-ex];print('contact alpha',int(alpha),'impact',impact);assert alpha
problems=[];face=[]
for item in ['greatSword','legendaryStaff']:
 for n in range(144):
  t=n/60;m.configure(item);trs,root,*_=m.ns['sample']('attack',m.motion(t));P=m.sword_foot(t) if item=='greatSword' else m.HERO_FOOT;x=round(P[0]-123*m.HS);y=round(P[1]-214*m.HS)
  # Draw original whole body without weapon to check actor/monster overlap.
  saved=m.ns['LAYERS']['MeadowBattleHeroWeapon'];m.ns['LAYERS']['MeadowBattleHeroWeapon']=Image.new('RGBA',(256,256));hero=m.ns['render']('attack',m.motion(t)).resize((round(256*m.HS),round(256*m.HS)),Image.Resampling.NEAREST);m.ns['LAYERS']['MeadowBattleHeroWeapon']=saved
  h=np.asarray(hero)[:,:,3]>128;x0,y0=max(x,ex),max(y,ey);x1,y1=min(x+hero.width,ex+m.enemy.width),min(y+hero.height,ey+m.enemy.height)
  if x0<x1 and y0<y1:
   ov=h[y0-y:y1-y,x0-x:x1-x]&enemy[y0-ey:y1-ey,x0-ex:x1-ex]
   if ov.any():problems.append([item,n,round(t,3),int(ov.sum())])
  # Weapon should not cover face pixels at any angle.
  masks=[]
  for name in ['MeadowBattleHeroWeapon','MeadowBattleHeroFace']:
   im=m.ns['LAYERS'][name];pivot,off,angle=trs.get(name,((0,0),(0,0),0));im=im.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=pivot);layer=Image.new('RGBA',(256,256));layer.alpha_composite(im,(round(off[0]+root[0]),round(off[1]+root[1])));masks.append(np.asarray(layer)[:,:,3]>128)
  overlap=masks[0]&masks[1]
  if overlap.any():face.append([item,n,round(t,3),int(overlap.sum())])
result={'impactOnEnemyAlphaMask':bool(alpha),'impactPoint':list(impact),'sampleRate':60,'durationSeconds':2.4,'samplesPerAction':144,'heroEnemyBodyIntersections':problems,'weaponFaceIntersections':face,'meaning':'Geometry supplement only; does not replace visual review or device testing.'}
print(json.dumps(result,ensure_ascii=False,indent=2))
assert not problems and not face, 'Visual geometry must be fixed before delivery'
(ROOT/'Art/Review/Battle/b2-weapons-v1/geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
