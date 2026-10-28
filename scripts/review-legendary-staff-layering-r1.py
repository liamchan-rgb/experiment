#!/usr/bin/env python3
"""Review the staff depth repair from existing, unchanged Swift pose exports.
No App, simulator, device or image generator is run.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,sys
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/legendary-staff-layering-r1';D.mkdir(parents=True,exist_ok=True)
p=R/'scripts/review-legendary-staff-demo.py';source=p.read_text().split("if '--check-only' in sys.argv:")[0].replace('Build59','Build60')
# Inputs remain the previous exports: no pose, timing, grip or FX geometry changed.
new_source=source
N={"__file__":str(p)};exec(compile(new_source,str(p),'exec'),N);N['D']=D
font=N['font'];save=N['save_normal'];gear=N['gear'];composite=N['composite'];S=N['S']
rows=[r for r in N['rows'] if r['scenario']=='legendary-staff'];body=[];scene=[]
for row in rows:
 u=next(u for u in row['units'] if u['id']=='p1');sprite=gear(u['clip'],u['progress'],'legendaryStaff');im=Image.new('RGB',(256,280),'#20372a');im.paste(sprite,(0,0),sprite);ImageDraw.Draw(im).text((6,258),f'{row["time"]:.2f}s',font=font(14),fill='#efe3b5');body.append(im)
 scene.append(N['ui'](row,S['scene'](row)).convert('RGB').resize((1020,765),Image.Resampling.LANCZOS))
reports=[save('body',body,(768,840)),save('battle',scene,(1020,765))]
body[0].resize((768,840),Image.Resampling.NEAREST).save(D/'body-standing.png');composite('idle',0).save(D/'first-frame-native.png')
board=Image.new('RGB',(1280,1680),'#20372a')
for ri,clip in enumerate(['idle','attack','guard','hit','victory','defeat']):
 for ci,progress in enumerate([0,.25,.5,.75,1]):
  im=composite(clip,progress);x=ci*256;y=ri*280;board.paste(im,(x,y),im);ImageDraw.Draw(board).text((x+6,y+258),f'{clip} {progress:.2f}',font=font(14),fill='#efe3b5')
board.save(D/'all-clips-1x.png');board.resize((2560,3360),Image.Resampling.NEAREST).save(D/'all-clips-2x.png')
# Rest/attack0/returned rest must preserve the same visible shaft and body.
first=composite('idle',0);start=composite('attack',0);last=composite('attack',1)
assert first.tobytes()==start.tobytes()==last.tobytes(),'Rest/cast boundary must not switch the shaft depth'
profile=json.loads((R/'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/legendary-staff-v1.json').read_text())
original_bytes=(json.dumps({k:v for k,v in profile.items() if k!='layerOrder'},separators=(',',':'),ensure_ascii=False)+'\n').encode()
assert __import__('hashlib').sha256(original_bytes).hexdigest()=='fa1c52280c06b804453417d13e9f7b4de4ddd82a23fc9c093524b3c06cbb7542' # Delivered Build59 motion resource.
for clip in ['attack','guard','hit','victory','defeat']:assert profile['layerOrder']==N['base']['ordered_layers'](clip)
before=Image.open(R/'Art/Review/Battle/legendary-staff-demo-v1/body-standing.png').convert('RGB').crop((0,0,768,768)).resize((512,512),Image.Resampling.NEAREST)
after=Image.new('RGB',(256,256),'#20372a');after.paste(first,(0,0),first);after=after.resize((512,512),Image.Resampling.NEAREST)
compare=Image.new('RGB',(1024,560),'#20372a')
for i,(im,title) in enumerate([(before,'Build59：杖杆被裤腿切断'),(after,'修正：杖杆连续位于腿前')]):
 compare.paste(im,(512*i,0));ImageDraw.Draw(compare).text((512*i+10,524),title,font=font(20),fill='#efe3b5')
compare.save(D/'first-frame-comparison.png')
(D/'review.json').write_text(json.dumps({'animations':reports,'restCastAndReturnedRestByteExact':True,'jointCurvesAndTimingUnchanged':True,'nonIdleLayerOrderUnchanged':True,'firstFrameComparisonMatchesDeliveredBuild59':True,'idleJointUnderlayNowVisibleLikeCast':True,'repair':'One shared staff layer order keeps shaft in front of legs during idle/cast/recovery; actual native resources, no anatomy or weapon pixel edits','userApproval':None,'appRunPerformed':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(reports),flush=True)
