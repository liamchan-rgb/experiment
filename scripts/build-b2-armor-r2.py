#!/usr/bin/env python3
"""Rebuild two rejected armor shapes from independent generated garment art.
Original body/motion/wardrobe and the four user-approved items are read-only.
"""
from pathlib import Path
import json,copy,math,hashlib,importlib.util,shutil,io,base64
import numpy as np
from PIL import Image,ImageDraw,ImageChops,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'Art/Review/Equipment/b2-batch-v1';D=R/'Art/Review/Equipment/b2-batch-v2';P=R/'Art/Parts/P1-v1/b2-armor-r2';I=R/'Art/Integration/Equipment-b2-batch-v2';A=R/'Sources/Resources/Assets.xcassets';S=R/'Art/Integration/P1-modular-eight-way-v1'
for p in [D,P,I]:p.mkdir(parents=True,exist_ok=True)
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=P/'armor-only.png'
if not source.exists():shutil.copyfile('/workspace/generated_images/exec-f86bf5b6-3ce3-42b3-97f1-133078525923.png',source)
sheet=Image.open(source).convert('RGBA');assert sheet.size==(1774,887)
motion=json.loads((S/'motion.json').read_text());poses=motion['frames'];rests={x['direction']:x for x in poses if x['clip']=='idle'}
directions=['down','down-left','left','up-left','up','up-right','right','down-right'];columns=[('idle',0)]+[('walk',i) for i in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]
spec=importlib.util.spec_from_file_location('compositor_r2',R/'scripts/compose-character-parts.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
place=module.place
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',14)
# Fixed complete-sheet registration, measured on the authoring guide. The same
# native scale is retained for all parts/frames, never alpha-bound auto-fitting.
guides=[{'neck':[270,155],'arms':[[176,193],[365,193]],'elbows':[[168,260],[375,260]],'cut':244,'belt':303},
 {'neck':[665,157],'arms':[[598,200],[709,194]],'elbows':[[595,261],[716,260]],'cut':248,'belt':304},
 {'neck':[1095,158],'arms':[[992,192],[1194,194]],'elbows':[[984,260],[1201,260]],'cut':246,'belt':304},
 {'neck':[1504,158],'arms':[[1425,195],[1606,194]],'elbows':[[1421,260],[1610,260]],'cut':246,'belt':304}]
scale=.205
def mask(points):
 im=Image.new('L',sheet.size);ImageDraw.Draw(im).polygon(points,fill=255);return im
def cut(points):
 im=sheet.copy();im.putalpha(ImageChops.multiply(im.getchannel('A'),mask(points)));return im
def angle(a,b):return math.atan2(b[1]-a[1],b[0]-a[0])
def transform(image,pivot,point,rotation=0,mirror=False,project=1):
 c,s=math.cos(rotation),math.sin(rotation);sx=scale*project*(-1 if mirror else 1)
 a,b,cc,d=sx*c,sx*s,-scale*s,scale*c
 tx=point[0]-a*pivot[0]-cc*pivot[1];ty=point[1]-b*pivot[0]-d*pivot[1]
 return place(image,[a,b,cc,d,tx,ty],(256,256))
def components(item,direction):
 row=0 if item=='leatherArmor' else 1;dy=0 if row==0 else 365
 index=0 if direction in ['down','down-left','down-right'] else 1 if direction in ['left','right'] else 2 if direction=='up' else 3
 q=copy.deepcopy(guides[index]);q['neck'][1]+=dy
 for field in ['arms','elbows']:
  for pt in q[field]:pt[1]+=dy
 q['cut']+=dy;q['belt']+=dy
 if row:
  q['cut']=303+dy
  for pt in q['elbows']:pt[1]+=33
 else:
  for pt in q['elbows']:pt[1]+=20
 cx=q['neck'][0];ny=q['neck'][1];mirror=direction in ['right','up-right'];project=.86 if direction in ['down-left','down-right'] else 1
 left=q['arms'][0][0]+28;right=q['arms'][1][0]-28
 if index==1:left=cx-85;right=cx+21
 # Cuirass includes the natural collar opening, shaped sides, and whole belt.
 torso=cut([(left-8,ny-14),(right+10,ny-14),(right+19,ny+65),(right+8,q['belt']+12),(left-7,q['belt']+12),(left-15,ny+65)])
 hem_left=cut([(left-16,q['belt']-2),(cx+5,q['belt']-2),(cx+5,q['belt']+104),(left-40,q['belt']+104)])
 hem_right=cut([(cx-5,q['belt']-2),(right+22,q['belt']-2),(right+45,q['belt']+104),(cx-5,q['belt']+104)])
 # Explicit source anatomy partitions. Ten source pixels of hidden overlap
 # keep the moving sleeve pieces connected, rather than eroding skin colours.
 sleeves=[]
 for i,(sx,sy) in enumerate(q['arms']):
  boundary=left+10 if i==0 else right-10
  x0,x1=(sx-85,boundary) if i==0 else (boundary,sx+85)
  if index==1 and i==0:x0,x1=cx-94,cx-38
  upper=cut([(x0,ny-16),(x1,ny-16),(x1,(q['cut']+12 if row else q['belt']+9)),(x0,(q['cut']+12 if row else q['belt']+9))])
  fore=cut([(x0,q['cut']-4),(x1,q['cut']-4),(x1,q['belt']+50),(x0,q['belt']+50)]) if row else Image.new('RGBA',sheet.size)
  if index==1 and i==0:
   # The profile's chest gem is not a far sleeve. Use the explicitly isolated
   # front-guide far sleeve behind the unchanged torso instead.
   fny=155+dy;fcut=(303 if row else 244)+dy;fbelt=303+dy
   upper=cut([(104,fny-16),(211,fny-16),(211,fcut+12 if row else fbelt+9),(104,fcut+12 if row else fbelt+9)])
   fore=cut([(104,fcut-4),(211,fcut-4),(211,fbelt+50),(104,fbelt+50)]) if row else Image.new('RGBA',sheet.size)
   q['arms'][0]=[176,193+dy];q['elbows'][0]=[150 if row else 168,(300 if row else 280)+dy]
  sleeves.append((upper,fore))
 return q,torso,[hem_left,hem_right],sleeves,mirror,project

cached={}
def garment(item,f):
 d=f['direction'];key=(item,d)
 if key not in cached:cached[key]=components(item,d)
 q,torso,hems,sleeves,mirror,projection=cached[key];j=f['joints'];rest=rests[d]['joints'];neck=j['neck'];hip=[sum(j['hip'+s][n] for s in ['Left','Right'])/2 for n in [0,1]];rh=[sum(rest['hip'+s][n] for s in ['Left','Right'])/2 for n in [0,1]]
 lean=angle(rest['neck'],rh)-angle(neck,hip)
 out={'outfit.torso':transform(torso,q['neck'],neck,-lean,mirror,projection),'outfit.hem.front':Image.new('RGBA',(256,256))}
 screen_sides=sorted(['Left','Right'],key=lambda side:rest['shoulder'+side][0])
 if mirror:screen_sides.reverse()
 for i,side in enumerate(screen_sides):
  sh=j['shoulder'+side];el=j['elbow'+side];rsh=rest['shoulder'+side];rel=rest['elbow'+side]
  source_vector=[q['elbows'][i][0]-q['arms'][i][0],q['elbows'][i][1]-q['arms'][i][1]]
  source_angle=math.atan2(source_vector[1],source_vector[0]*(-1 if mirror else 1))
  rotation=angle(sh,el)-source_angle
  upper,fore=sleeves[i]
  # Source shoulder registration is semantic, not an alpha crop or grip fit.
  a=transform(upper,q['arms'][i],sh,rotation,mirror)
  reference_elbow=(q['elbows'][i][0],q['elbows'][i][1])
  wr=j.get('wrist'+side);rw=rest.get('wrist'+side)
  fore_angle=(angle(el,wr) if wr else angle(sh,el))-math.pi/2
  b=transform(fore,reference_elbow,el,fore_angle,mirror)
  a.alpha_composite(b);out['outfit.sleeve.'+side.lower()]=a
 for i,part in enumerate(hems):
  side=screen_sides[i];h=j['hip'+side];hr=rest['hip'+side]
  knee=j.get('knee'+side,f['soleMarkers'][side.lower()]);kr=rest.get('knee'+side,rests[d]['soleMarkers'][side.lower()]);a=(angle(h,knee)-angle(hr,kr))*.32
  # Belt is one torso piece; only the corresponding lower tasset follows leg.
  pivot=[q['neck'][0]+(-35 if i==0 else 35),q['belt']]
  at=[neck[0]+(-7 if (i==0)!=mirror else 7),neck[1]+(q['belt']-q['neck'][1])*scale]
  at[0]+=(h[0]-hr[0])*.35;at[1]+=(h[1]-hr[1])*.35
  out['outfit.hem.front'].alpha_composite(transform(part,pivot,at,a,mirror,projection))
 return out

oldcat=json.loads((R/'Art/Integration/Equipment-b2-batch-v1/catalog.json').read_text());catalog=copy.deepcopy(oldcat)
for item in ['leatherArmor','runeArmor']:
 folder=P/item;folder.mkdir(exist_ok=True);shutil.copyfile(source,folder/'armor-only.png');template=json.loads((R/'Art/Parts/P1-v1/eight-way-v1/wayfarer/asset.json').read_text());template['id']='p1-b2-'+item.lower()+'-r2';bindings=[];sources=['authoring.json','armor-only.png']
 for f in poses:
  layers={}
  for slot,im in garment(item,f).items():
   relative=f"png/{f['direction']}/{f['clip']}/{f['frame']:02}/{slot}.png";path=folder/relative;path.parent.mkdir(parents=True,exist_ok=True);im.save(path);layers[slot]=relative
   ed=f"editable/{f['direction']}-{f['clip']}-{f['frame']:02}-{slot}.svg";p=folder/ed;p.parent.mkdir(exist_ok=True);p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><g id="'+slot+'"><image width="256" height="256" href="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"/></g></svg>');sources.append(ed)
  bindings.append({k:f[k] for k in ['direction','clip','frame']}|{'layers':layers})
 template.update(sourceFiles=sources,bindings=bindings);write(folder/'asset.json',template);write(folder/'authoring.json',{'generatedSourceSHA256':sha(source),'method':'independent shaped armor source, fixed .205 whole-guide scale, explicit shoulder/elbow segmentation, short tassets follow each original leg','sourceGuides':guides,'sourceRowOffset':365 if item=='runeArmor' else 0,'noExistingClothingRecolorOrAlphaReuse':True,'originalBodyMotionModified':False,'artApproval':None})
 catalog['assets'].append({'id':template['id'],'manifest':str((folder/'asset.json').relative_to(R))})
write(I/'catalog.json',catalog);C=module.Compositor(R,I/'catalog.json',S/'motion.json');selection=json.loads((R/'Art/Integration/P1-modular-demo-v1/selection.json').read_text())
manifest=json.loads((O/'manifest.json').read_text());manifest.update(id='b2-batch-v2',title='B2 护甲结构返修 · 第二轮',previousBatch='b2-batch-v1',previousResourceRevisionSHA256=manifest['resourceRevisionSHA256']);manifest['carriedApprovals']={x:{'status':'pass','sourceBatch':'b2-batch-v1','sourceRevision':manifest['previousResourceRevisionSHA256']} for x in ['greatSword','legendaryStaff','powerBadge','actionRing']}
for entry in manifest['items']:
 item=entry['id']
 if item not in ['leatherArmor','runeArmor']:
  entry['approvalSource']='../b2-batch-v1/user-approval.json';entry['sourceMediaDirectory']='../b2-batch-v1/'+item;continue
 entry['revision']='b2-armor-r2';entry['artApproval']=None;entry['scope']='独立胸背甲、叠层肩甲、内衬袖与短分片护裙；保留原人物与动作';entry['battleScope']='结构返修版护甲；沿原六动作检查独立衣物挂载，非新技能或实机运行'
 (D/item).mkdir(exist_ok=True);shutil.copyfile(O/item/'icon.png',D/item/'icon.png')
 for preset in selection['loadouts']:
  selected=[a for a in preset['assets'] if a not in ['p1-eight-way-forester-v1','p1-eight-way-wayfarer-v1']]+['p1-b2-'+item.lower()+'-r2'];atlas=Image.new('RGBA',(3328,2048))
  for row,direction in enumerate(directions):
   for col,(clip,n) in enumerate(columns):atlas.paste(C.render(selection['base'],selected,direction,clip,n),(col*256,row*256))
  atlas.save(D/item/(preset['id']+'-walk.png'))
 atlas=Image.open(D/item/'forester-walk.png');frames=[]
 for col in range(9):
  board=Image.new('RGB',(1024,560),'#20372a');dr=ImageDraw.Draw(board)
  for row,label in enumerate(manifest['directionLabels']):
   im=atlas.crop((col*256,row*256,(col+1)*256,(row+1)*256));x,y=row%4*256,row//4*280;board.paste(im,(x,y),im);dr.text((x+7,y+256),entry['name']+' · '+label,font=font,fill='#ffedc7')
  if col==0:board.save(D/item/'standing.png')
  else:frames.append(board)
 frames[0].save(D/item/'walk-normal.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=True)
 # Map the same new sleeve/torso sources to the existing registered battle rig.
 # Profile guide, single source scale; arms use the actor's actual rigid joints.
 q,torso,hems,sleeves,mir,projection=components(item,'right');bdir=P/item/'battle';bdir.mkdir(exist_ok=True)
 front,_,_,front_sleeves,_,_=components(item,'down')
 body=transform(front_sleeves[0][0],front['arms'][0],[109,145])
 body.alpha_composite(transform(front_sleeves[0][1],front['elbows'][0],[107,160]))
 body.alpha_composite(transform(torso,q['neck'],[128,132],mirror=True))
 # Waist tassets are attached to their corresponding thigh below, not baked into the torso.
 body.save(bdir/'MeadowBattleHeroWardrobeCore.png')
 upper,fore=sleeves[1]
 transform(upper,q['arms'][1],[117,141],rotation=math.atan2(17,11)-math.atan2(q['elbows'][1][1]-q['arms'][1][1],q['arms'][1][0]-q['elbows'][1][0]),mirror=True).save(bdir/'MeadowBattleHeroArmNearUpperWardrobe.png')
 transform(fore,q['elbows'][1],[128,158],rotation=math.atan2(5.7,17.6)-math.pi/2,mirror=True).save(bdir/'MeadowBattleHeroArmNearForearmWardrobe.png')
 # Preserve the original trouser layers byte-for-byte. These layers contain
 # the trousers themselves and must never be replaced with empty armor layers.
 for n in ['MeadowBattleHeroLegFarThighWardrobe','MeadowBattleHeroLegNearThighWardrobe']:
  pants=Image.open(A/(n+'.imageset')/(n+'.png')).convert('RGBA')
  # Retain all actual trouser pixels; retire the old coat's blue/white belt edge.
  ImageDraw.Draw(pants).rectangle((0,0,255,173),fill=(0,0,0,0))
  h=hems[0 if 'Near' in n else 1]
  pants.alpha_composite(transform(h,q['neck'],[128,132],mirror=True))
  pants.save(bdir/(n+'.png'))
 src=R/'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py';ns={'__file__':str(src)};exec(compile(src.read_text().split("\nfor clip,data in lib['clips'].items():")[0],str(src),'exec'),ns);ns['lib']=json.loads((A/'MeadowBattleHeroAnimationV2.dataset/animation.json').read_text())
 for p in bdir.glob('*.png'):ns['LAYERS'][p.stem]=Image.open(p).convert('RGBA')
 for clip in ['idle','attack','guard','hit','victory','defeat']:
  count=ns['lib']['clips'][clip]['durationMs']//20;atlas=Image.new('RGBA',(2560,math.ceil(count/10)*256));frames=[]
  for n in range(count):
   im=ns['render'](clip,n/(count-1));atlas.paste(im,(n%10*256,n//10*256));frame=Image.new('RGB',(512,512),'#20372a');im=im.resize((512,512),Image.Resampling.NEAREST);frame.paste(im,(0,0),im);frames.append(frame)
  atlas.save(D/item/('battle-'+clip+'.png'));entry['battle'][clip]['frames']=count
  if clip=='attack':frames[0].save(D/item/'battle-normal.gif',save_all=True,append_images=frames[1:],duration=20,loop=0,disposal=2,optimize=True)
# Clear hidden RGB in authored layers; leave original generated references intact.
for item in ['leatherArmor','runeArmor']:
 for root in [P/item/'png',P/item/'battle']:
  for p in root.rglob('*.png'):
   im=Image.open(p).convert('RGBA');ar=np.asarray(im).copy();ar[ar[:,:,3]==0,:3]=0;Image.fromarray(ar).save(p)
files={str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file() and p.relative_to(D).parts[0] in ['leatherArmor','runeArmor'] and p.suffix in ['.png','.gif']};write(D/'files.json',files);manifest['resourceRevisionSHA256']=sha(D/'files.json');write(D/'manifest.json',manifest)
print(json.dumps({'newArmorPackages':2,'newBindings':208,'oldApprovedArtModified':False,'revision':manifest['resourceRevisionSHA256']}))
