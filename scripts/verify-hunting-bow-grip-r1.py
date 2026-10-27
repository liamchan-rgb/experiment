from pathlib import Path
from PIL import Image,ImageDraw
import json,math,numpy as np
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Review/Battle/hunting-bow-grip-r1'
rows=json.loads((D/'bow-poses.json').read_text());hand=Image.open(A/'MeadowBattleHeroNearHand.imageset/MeadowBattleHeroNearHand.png').convert('RGBA');bow=Image.open(A/'MeadowBattleHuntingBow.imageset/MeadowBattleHuntingBow.png').convert('RGBA')
def layer(im,q):
 p=q['pivot'];o=q['offset'];v=im.rotate(-math.degrees(q['rotation']),Image.Resampling.NEAREST,center=(p['x'],p['y']));z=Image.new('RGBA',(256,256));z.alpha_composite(v,(round(o['x']),round(o['y'])));return np.array(z.getchannel('A'))>64
issue1=[];issue2=[];counts=[];spans=[]
for row in rows:
 s=row['sample'];p=row['progress'];a=layer(hand,s['parts']['nearHand']);b=layer(bow,s['parts']['bow']);n=int((a&b).sum());counts.append(n)
 if n==0:issue1.append((p,n))
 if s['arrowVisible']:
  fh=layer(hand,s['parts']['farHand']);line=Image.new('1',(256,256));d=ImageDraw.Draw(line);pts=[(round(s[k]['x']),round(s[k]['y'])) for k in ('upperTip','stringHand','lowerTip')];d.line(pts,fill=1,width=1);n2=int((fh & np.asarray(line,dtype=bool)).sum());spans.append(n2)
  if n2==0:issue2.append((p,n2))
result={'clips':6,'samples':len(counts),'nearGripOverlapMin':min(counts),'nearGripNoOverlap':len(issue1),'nearGripSamples':issue1[:10],'engagedSamples':len(spans),'drawingHandStringOverlapMin':min(spans),'drawingHandStringNoOverlap':len(issue2),'drawSamples':issue2[:10],'scope':'Offline source sprite alpha and exported rig pose checks; not a substitute for visual or device review.'}
print(json.dumps(result,indent=2))
assert not issue1 and not issue2
(D/'grip-geometry.json').write_text(json.dumps(result,indent=2)+'\n')
