#!/usr/bin/env python3
"""Offline full-body/scene review from the exact production Swift weapon poses.
No game, simulator, device, or browser game run.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,math,functools,sys,copy
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/legendary-staff-demo-v1';A=R/'Sources/Resources/Assets.xcassets'
p=R/'scripts/review-bow-actions-r7-demo.py';N={'__file__':str(p)}
code=p.read_text().split('# Check every registered frame')[0].replace("NAME='bow-actions-r7-demo-v1'","NAME='legendary-staff-demo-v1'").replace('Build57 · 猎弓','Build59 · 传奇权杖')
exec(compile(code,str(p),'exec'),N)
S=N['S'];world=N['world'];base=N['base'];asset=N['asset'];oldgear=N['gear_render'];font=S['font'];rows=S['rows'];samples={(r.get('clip','attack'),round(r['progress']*600)):r['sample'] for r in json.loads((D/'legendary-staff-poses.json').read_text())}
# Render the same independent source layers and their Swift transforms. Every
# row's actual attack sample is included, beyond the static601-pose gallery.
actual={round(u['progress'],12):u['weaponPose'] for row in rows for u in row['units'] if u.get('weaponID')=='legendaryStaff' and u.get('weaponPose') and u['clip']=='attack'}
def state_sample(clip,p):
 if clip=='attack' and round(p,12) in actual:return actual[round(p,12)]
 return samples[(clip,round(max(0,min(1,p))*600))]

def composite(clip,p,weapon='legendaryStaff'):
 q=state_sample(clip,p);root=q['rootOffset'];out=Image.new('RGBA',(256,256))
 for n in json.loads((R/'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/legendary-staff-v1.json').read_text())['layerOrder']:
  im=asset('MeadowBattleLegendaryStaff' if n=='MeadowBattleHeroWeapon' else n);t=q['layers'].get(n)
  pivot=(t['pivot']['x'],t['pivot']['y']) if t else (0,0);off=(t['offset']['x'],t['offset']['y']) if t else (0,0);a=t['rotation'] if t else 0
  im=im.rotate(-math.degrees(a),Image.Resampling.NEAREST,center=pivot);out.alpha_composite(im,(round(off[0]+root['x']),round(off[1]+root['y'])))
 return out
@functools.lru_cache(2048)
def gear(clip,p,weapon):return composite(clip,p) if weapon=='legendaryStaff' else oldgear(clip,p,weapon)
S['gear_render']=gear;world['gear_render']=gear
helpers=world['env']
def draw_projectile(f,row):
 q=row.get('staff')
 if not q:return
 s=q['scale'];p=q['impactPower'];oy=world['oy']
 def pt(p):return (p['x'],p['y']+oy)
 def glow(point,rx,ry,a):world['glow'](f,pt(point),rx,ry,min(1,a),(50,210,255))
 glow(q['gem'],48*s,40*s,q['charge']*.36)
 overlay=Image.new('RGBA',f.size);dd=ImageDraw.Draw(overlay)
 if q.get('head'):
  glow(q['head'],40*s,30*s,.45)
  for w,a in [(13,.41),(5,.73),(2,.98)]:dd.line([pt(v) for v in q['trail']],fill=(255,255,255,round(a*255)) if w==2 else (50,210,255,round(a*255)),width=max(1,round(w*s)),joint='curve')
  x,y=pt(q['head']);r=5*s;dd.ellipse((x-r,y-r,x+r,y+r),fill=(255,255,255,240))
 glow(q['impact'],108*s,100*s,p*.58);glow(q['ground'],112*s,22*s,p*.52)
 if p>0:
  r=q['burstRadius'];x,y=pt(q['impact'])
  dd.polygon([(x,y-r*1.4),(x+r*.23,y-r*.2),(x+r,y),(x+r*.23,y+r*.2),(x,y+r*1.4),(x-r*.23,y+r*.2),(x-r,y),(x-r*.23,y-r*.2)],fill=(50,210,255,round(min(.8,p*.78)*255)))
  dd.ellipse((x-r*.18,y-r*.18,x+r*.18,y+r*.18),fill=(255,255,255,round(min(1,p)*255)))
 for ray in q['rays']:dd.line([pt(v) for v in ray['points']],fill=(50,210,255,round(ray['alpha']*255)),width=max(1,round(2*s)),joint='curve')
 for m in q['motes']:
  x,y=pt(m);r=m['size']/2;dd.ellipse((x-r,y-r,x+r,y+r),fill=(*( (255,255,255) if m['id']%3==0 else (50,210,255)),round(m['alpha']*255)))
  if m['id']%6==0:glow(m,18*s,14*s,m['alpha']*.2)
  if abs(m['y']-q['ground']['y'])<5*s:glow(m,24*s,6*s,m['alpha']*.25)
 S['add_layer'](f,overlay)
world['draw_projectile']=draw_projectile
# Exclude the common golden melee flash for staff attacks, matching UIKit.
original_scene=S['scene']
def staff_scene(row):
 if row.get('staff'):
  row=dict(row,action='staffAttack')
 return original_scene(row)
S['scene']=staff_scene
old_ui=S['ui']
def ui(row,scene):
 im=old_ui(row,scene)
 if row['scenario'].startswith('legendary-staff'):
  dd=ImageDraw.Draw(im);dd.rectangle((96,951,349,1005),fill='#293e2d');dd.text((96,965),'1D20＋当前增伤',font=font(20),fill='#c6d6b7')
 return im
# Reuse only the lossless GIF writer and decode-sheet routine.
src=(R/'scripts/review-bow-actions-r7-demo.py').read_text();fn=src[src.index('def save_normal('):src.index('\nreports=[]',src.index('def save_normal('))]
import subprocess
exec(fn,globals())
if '--check-only' in sys.argv:sys.exit(0)
if '--states-only' in sys.argv:
 rows=[]
reports=[]
for scenario in ['legendary-staff','legendary-staff-heavy','legendary-staff-lethal','legendary-staff-natural20']:
 group=[r for r in rows if r['scenario']==scenario];body=[];scene=[]
 if not group:continue
 for row in group:
  u=next(u for u in row['units'] if u['id']=='p1');sprite=gear(u['clip'],u['progress'],'legendaryStaff');im=Image.new('RGB',(256,280),'#20372a');im.paste(sprite,(0,0),sprite);ImageDraw.Draw(im).text((6,258),f'{scenario} {row["time"]:.2f}s',font=font(14),fill='#f0e4b6');body.append(im)
  im=ui(row,S['scene'](row)).convert('RGB');scene.append(im.resize((1020,765),Image.Resampling.LANCZOS))
 if scenario=='legendary-staff':
  reports.append(save_normal('body',body,(768,840)));body[0].resize((768,840),Image.Resampling.NEAREST).save(D/'body-standing.png')
 reports.append(save_normal(scenario,scene,(1020,765)))
 for tm,label in [(0,'standing'),(1.55,'approach'),(2.04,'contact'),(2.15,'impact'),(2.5,'return'),(3.0,'rest')]:
  row=min(group,key=lambda r:abs(r['time']-tm));ui(row,S['scene'](row)).save(D/(scenario+'-'+label+'.png'))
# The six-state mount uses one weapon layer on the same original common rig.
board=Image.new('RGB',(1280,1680),'#20372a')
for row,c in enumerate(['idle','attack','guard','hit','victory','defeat']):
 for col,p in enumerate([0,.25,.5,.75,1]):
  im=composite(c,p);x=col*256;y=row*280;board.paste(im,(x,y),im);ImageDraw.Draw(board).text((x+6,y+258),f'{c} {p:.2f}',font=font(14),fill='#f0e4b6')
board.save(D/'all-clips-1x.png');board.resize((2560,3360),Image.Resampling.NEAREST).save(D/'all-clips-2x.png')
if '--states-only' not in sys.argv:(D/'review-render.json').write_text(json.dumps({'scope':'Exact production Swift poses and rules receipts, offline independent-layer art composition; not UIKit or device capture','animations':reports,'newRuntimeArtApproval':None},indent=2)+'\n');print(json.dumps(reports),flush=True)
