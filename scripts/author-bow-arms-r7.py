#!/usr/bin/env python3
"""Shorten this native keyframe's two arms about their existing shoulder roots."""
from pathlib import Path
import json,math,shutil
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
old=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r6';D=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r7';D.mkdir(exist_ok=True)
for name in ['drawing-hand.png','grip-hand.png','torso.png']:shutil.copyfile(old/name,D/name)
p=json.loads((old/'pose.json').read_text());baseline=json.loads((old/'pose.json').read_text())
roots={'near':117,'far':138};scale=.90
# Shorten horizontal reach, retaining the shoulder locations, sleeve height,
# skin silhouettes and the approved depth order. No whole-character resize.
def nx(x,prefix):return math.floor(roots[prefix]+(x-roots[prefix])*scale+.5)
for surf in p['surfaces']:
 prefix='near' if surf['group'] in ['nearUpperArm','nearForeArm'] else 'far' if surf['group']=='farArm' else None
 if prefix:
  for q in surf['points']:q['x']=nx(q['x'],prefix)
for prefix in ['near','far']:
 for suffix in ['Upper','Fore']:
  pose=p['parts'][prefix+suffix];pose['pivot']['x']=nx(pose['pivot']['x'],prefix)
 hand=p['parts'][prefix+'Hand'];oldhand=baseline['parts'][prefix+'Hand'];x=oldhand['pivot']['x']+oldhand['offset']['x'];hand['offset']['x']=nx(x,prefix)-hand['pivot']['x']
 shoulder=p['parts'][prefix+'Upper']['pivot'];elbow=p['parts'][prefix+'Fore']['pivot'];q=p['parts'][prefix+'Hand'];hx=q['pivot']['x']+q['offset']['x'];hy=q['pivot']['y']+q['offset']['y']
 p['parts'][prefix+'Upper']['rotation']=math.atan2(elbow['y']-shoulder['y'],elbow['x']-shoulder['x'])
 p['parts'][prefix+'Fore']['rotation']=math.atan2(hy-elbow['y'],hx-elbow['x'])
# Translate the same bow along with the holding hand; fingertips retain the nock.
oldfar=baseline['parts']['farHand'];newfar=p['parts']['farHand'];shift=newfar['offset']['x']-oldfar['offset']['x']
p['parts']['bow']['offset']['x']+=shift
for key in ['upperTip','lowerTip','arrowTip']:p[key]['x']+=shift
near=p['parts']['nearHand'];contact=near['pivot']['x']+near['offset']['x']
for key in ['stringHand','arrowTail']:p[key]['x']=contact
(D/'pose.json').write_text(json.dumps(p,indent=2)+'\n')
for group in ['nearUpperArm','nearForeArm','farArm']:
 im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im)
 for surf in p['surfaces']:
  if surf['group']==group:d.polygon([(q['x'],q['y']) for q in surf['points']],fill='#%06x'%surf['color'])
 im.save(D/(group+'.png'))
(D/'authoring.json').write_text(json.dumps({'method':'shorten native arm reach about fixed shoulder roots; preserve sleeve height, hands, torso and layer order','nominalHorizontalScale':scale,'fixedShoulders':{k:baseline['parts'][k+'Upper']['pivot'] for k in ['near','far']},'script':'scripts/author-bow-arms-r7.py','frozenFrom':str(old.relative_to(R)),'frozenFiles':['drawing-hand.png','grip-hand.png','torso.png'],'holdingHandAndBowTranslationX':shift,'runtimeImported':False,'userApproved':False},indent=2)+'\n')
print('Fixed shoulder roots; drawing hand:',contact,'holding hand:',newfar['pivot']['x']+newfar['offset']['x'])
