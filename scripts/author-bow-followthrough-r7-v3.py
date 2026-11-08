#!/usr/bin/env python3
"""Repair the r7 follow-through's projected shoulder/elbow and connected sleeve.
Retain the accepted native drawing pose, far arm, bow, face and release timing.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFont,ImageSequence,ImageFilter
import json,math,copy,shutil,hashlib
R=Path(__file__).resolve().parents[1]
BASE=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r7'
D=R/'Art/Parts/P1-Battle/hunting-bow-followthrough-r7-v3';D.mkdir(exist_ok=True)
O=R/'Art/Review/Battle/hunting-bow-followthrough-r7-v3';O.mkdir(exist_ok=True)
(O/'frames').mkdir(exist_ok=True);(D/'frames').mkdir(exist_ok=True)
for name in ['torso.png','drawing-hand.png','grip-hand.png']:shutil.copyfile(BASE/name,D/name)
baseline=json.loads((BASE/'pose.json').read_text())
# Use the exact project-resource compositor from the accepted first pose.
script=R/'scripts/review-bow-aim-project-r7.py';N={'__file__':str(script)}
exec(compile(script.read_text().split('assembled=gear_render')[0],str(script),'exec'),N)
N['D']=D
composition=N['composition']
assert composition.count("['farArm','nearUpperArm','torso','nearForeArm','head']")==1
composition=composition.replace("['farArm','nearUpperArm','torso','nearForeArm','head']", "['farArm','nearUpperArm','torso','nearSleeveConnected','head']")
composition=composition.replace("   if name=='geometry':geometry();continue", "   if name=='geometry':geometry();continue\n   if name=='nearSleeveConnected':\n    out.alpha_composite(current_sleeve,(round(root[0]),round(root[1])));continue")
exec(compile(composition,'r7-recovery-connected-sleeve','exec'),N)
old_asset=N['namespace']['asset'];current_hand=None
def asset(name):
 if name=='MeadowBattleBowDrawingHand' and current_hand is not None:return current_hand.copy()
 im=old_asset(name)
 if name=='MeadowBattleBowBodyCore':
  # Repair only neutral undershirt pixels that were completely hidden under
  # the accepted drawing palm; retain all exposed r7 pixels and neck skin.
  for y in range(135,139):
   for x in range(127,143):
    c=im.getpixel((x,y))
    if held.getpixel((x-127,y-133))[3]==255 and c[3] and (c[0]-c[1]<35 or c[1]-c[2]<16):
     im.putpixel((x,y),(0,0,0,0))
 return im
N['namespace']['asset']=asset
held=Image.open(D/'drawing-hand.png').convert('RGBA')
opened=held.copy();hd=ImageDraw.Draw(opened)
# Two fingers loosen at release, within the same registered hand canvas.
hd.point((15,2),fill='#55301e');hd.line((12,3,15,3),fill='#ffd2a4');hd.point((15,4),fill='#a65e37')
hd.line((12,6,15,6),fill='#ffc28c');hd.point((15,7),fill='#a65e37')
relaxed=held.copy();hd=ImageDraw.Draw(relaxed)
hd.point((14,3),fill='#ffc993');hd.point((14,6),fill='#eea36e')
for name,im in [('drawing-hand-held.png',held),('drawing-hand-open.png',opened),('drawing-hand-relaxed.png',relaxed)]:im.save(D/name)
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def coord(p):return (p['x'],p['y'])
def center(p):return (p['pivot']['x']+p['offset']['x'],p['pivot']['y']+p['offset']['y'])
def rotate(v,a):return (v[0]*math.cos(a)-v[1]*math.sin(a),v[0]*math.sin(a)+v[1]*math.cos(a))
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def q(p):return {'x':p[0],'y':p[1]}
def bodypoint(p,pivot,a,destination=None):return add(destination or pivot,rotate(sub(p,pivot),a))
reference_actor=Image.open(BASE/'assembled.png').convert('RGBA')
reference_body=old_asset('MeadowBattleBowBodyCore')
face_pixels=[(x,y) for y in range(96,133) for x in range(125,154) if reference_body.getpixel((x,y))[3]==255]
near_sh=coord(baseline['parts']['nearUpper']['pivot']);near_el=coord(baseline['parts']['nearFore']['pivot']);near_h=center(baseline['parts']['nearHand'])
far_sh=coord(baseline['parts']['farUpper']['pivot']);far_h=center(baseline['parts']['farHand'])
# The drawing-pose upper arm is foreshortened. Unfold its projection during
# lowering; keeping that short projection rigid produced the missing shoulder.
near_upper_start=math.atan2(near_el[1]-near_sh[1],near_el[0]-near_sh[0])
near_fore_start=math.atan2(near_h[1]-near_el[1],near_h[0]-near_el[0])
near_el_end=(112,159)
cuff_source=(130,139)
cuff_vector=sub(cuff_source,near_el)
cuff_length=math.hypot(*cuff_vector)
cuff_unit=tuple(v/cuff_length for v in cuff_vector)
cuff_normal=(-cuff_unit[1],cuff_unit[0])
fore_rotation_end=.12
fore_cuff_length_end=21
(D/'sleeve-construction.json').write_text(json.dumps({'shoulder':q(near_sh),'drawnElbow':q(near_el),'loweredElbow':q(near_el_end),'drawnCuff':q(cuff_source),'loweredProjectedElbowToCuffLength':fore_cuff_length_end,'foreRotationDelta':fore_rotation_end,'upperRadius':[4,6],'elbowRadius':[4,5.2],'projectedForeWidthScale':[1,.87],'proximalForeBulbLengthScale':[1,.5],'foregroundLayer':'nearSleeveConnected.png','sourceSurfaces':'r7 nearForeArm','reason':'The upper arm unfolds out of the foreshortened drawing pose; a single continuous outline replaces overlapping cutout seams.'},indent=2)+'\n')
release=.18;recover_start=.20;recover_duration=.32
frames=[];records=[]
asset('MeadowBattleBowBodyCore').save(D/'body-core-clean.png')
def make_sleeve(p,r,el):
 # A complete upper sleeve changes its projected shape as the arm comes down.
 # The drawing-pose forearm's oversized elbow bulb is not rotated as a rigid tube.
 fore=Image.new('RGBA',(256,256));dd=ImageDraw.Draw(fore)
 for surf in p['surfaces']:
  if surf['group']=='nearForeArm':dd.polygon([coord(z) for z in surf['points']],fill='#%06x'%surf['color'])
 upper=Image.new('RGBA',(256,256));ud=ImageDraw.Draw(upper)
 v=sub(el,near_sh);ln=math.hypot(*v);unit=tuple(z/ln for z in v);normal=(-unit[1],unit[0])
 rs=4+2*r;re=4+1.2*r
 points=[]
 for c,rad,start in [(near_sh,rs,math.atan2(-unit[1],-unit[0])-math.pi/2),(el,re,math.atan2(unit[1],unit[0])-math.pi/2)]:
  points.extend([(c[0]+rad*math.cos(start+math.pi*j/12),c[1]+rad*math.sin(start+math.pi*j/12)) for j in range(13)])
 ud.polygon(points,fill='#315b94')
 mask=upper.getchannel('A')
 # Light follows the existing upper-left lighting; it is not a second round cap.
 for yy in range(132,169):
  for xx in range(103,125):
   if not mask.getpixel((xx,yy)):continue
   along=(xx-near_sh[0])*unit[0]+(yy-near_sh[1])*unit[1]
   across=(xx-near_sh[0])*normal[0]+(yy-near_sh[1])*normal[1]
   if across< -1.8:color='#254979'
   elif across>2.2:color='#426fa9'
   else:color='#315b94'
   ud.point((xx,yy),fill=color)
 connected=upper.copy();connected.alpha_composite(fore)
 union=connected.getchannel('A')
 # Only the outside silhouette gets an outline. The elbow is continuous fabric,
 # not two outlined sleeve pieces pasted over one another.
 interior=union.filter(ImageFilter.MinFilter(3))
 outline=ImageChops.subtract(union,interior)
 if r>0:
  cd=ImageDraw.Draw(connected)
  both=ImageChops.multiply(mask.filter(ImageFilter.MinFilter(3)),fore.getchannel('A'))
  for yy in range(130,172):
   for xx in range(94,146):
    c=connected.getpixel((xx,yy))
    if both.getpixel((xx,yy)) and c[:3]==(25,42,61):cd.point((xx,yy),fill='#315b94')
  connected.paste(Image.new('RGBA',(256,256),'#192a3d'),(0,0),outline)
 return connected,upper,fore
for i in range(85):
 t=i*.02;r=smooth((t-recover_start)/recover_duration)
 moved_el=tuple(a+(b-a)*r for a,b in zip(near_el,near_el_end))
 ua=(math.atan2(moved_el[1]-near_sh[1],moved_el[0]-near_sh[0])-near_upper_start+math.pi)%(2*math.pi)-math.pi
 fa=fore_rotation_end*r
 sleeve_length=cuff_length+(fore_cuff_length_end-cuff_length)*r
 cuff_end=add(moved_el,rotate(tuple(z*sleeve_length for z in cuff_unit),fa))
 moved_hand=add(cuff_end,rotate(sub(near_h,cuff_source),fa))
 lower=smooth((t-.56)/.52);far_angle=.27*lower;bow_angle=.09*lower
 moved_far_hand=bodypoint(far_h,far_sh,far_angle)
 p=copy.deepcopy(baseline)
 for surf in p['surfaces']:
  group=surf['group']
  if group=='torso':continue
  if group=='nearUpperArm':
   old_v=sub(near_el,near_sh);old_l=math.hypot(*old_v);ou=tuple(z/old_l for z in old_v);on=(-ou[1],ou[0]);new_l=math.dist(near_sh,moved_el)
   def f(v):
    rel=sub(v,near_sh);ax=sum(a*b for a,b in zip(rel,ou))*new_l/old_l;ay=sum(a*b for a,b in zip(rel,on))
    return add(near_sh,rotate(add(tuple(z*ax for z in ou),tuple(z*ay for z in on)),ua))
  elif group=='nearForeArm':
   def f(v):
    rel=sub(v,near_el);ax=sum(a*b for a,b in zip(rel,cuff_unit));ay=sum(a*b for a,b in zip(rel,cuff_normal))
    ax*=sleeve_length/cuff_length if ax>=0 else 1-.50*r
    ay*=1-.13*r
    return add(moved_el,rotate(add(tuple(z*ax for z in cuff_unit),tuple(z*ay for z in cuff_normal)),fa))
  elif group=='farArm':f=lambda v:bodypoint(v,far_sh,far_angle)
  else:continue
  surf['points']=[q(tuple(round(k) for k in f(coord(point)))) for point in surf['points']]
 def place(name,at,angle):
  part=p['parts'][name];part['offset']=q(sub(at,coord(part['pivot'])));part['rotation']=angle
 place('nearUpper',near_sh,near_upper_start+ua)
 p['parts']['nearFore']['pivot']=q(moved_el);p['parts']['nearFore']['offset']=q((0,0));p['parts']['nearFore']['rotation']=math.atan2(moved_hand[1]-moved_el[1],moved_hand[0]-moved_el[0])
 place('nearHand',moved_hand,fa)
 place('farUpper',far_sh,baseline['parts']['farUpper']['rotation']+far_angle)
 old_far_el=coord(baseline['parts']['farFore']['pivot']);p['parts']['farFore']['pivot']=q(bodypoint(old_far_el,far_sh,far_angle));p['parts']['farFore']['offset']=q((0,0));p['parts']['farFore']['rotation']=baseline['parts']['farFore']['rotation']+far_angle
 place('farHand',moved_far_hand,bow_angle);place('bow',moved_far_hand,bow_angle)
 for key in ['upperTip','lowerTip']:
  p[key]=q(bodypoint(coord(baseline[key]),far_h,bow_angle,moved_far_hand))
 neutral=bodypoint((baseline['upperTip']['x'],baseline['arrowTail']['y']),far_h,bow_angle,moved_far_hand)
 if t<release:
  p['stringHand']=q(near_h);p['arrowVisible']=True
 else:
  snap=min(1,(t-release)/.02)
  p['stringHand']=q(tuple(a+(b-a)*snap for a,b in zip(near_h,neutral)));p['arrowVisible']=False
 p['arrowAlpha']=1
 variant='held' if t<release else 'open' if t<.28 else 'relaxed'
 current_hand={'held':held,'open':opened,'relaxed':relaxed}[variant]
 current_sleeve,upper,fore=make_sleeve(p,r,moved_el)
 N['current_sleeve']=current_sleeve
 N['bow_samples']={('attack',198):p,('attack',199):p};N['gear_render'].cache_clear()
 actor=N['gear_render']('attack',.33,'huntingBow')
 # The first frame must literally be the accepted native composite.
 if i==0:assert actor.tobytes()==Image.open(BASE/'assembled.png').convert('RGBA').tobytes()
 layer_dir=D/'frames'/f'{i:03}';layer_dir.mkdir(exist_ok=True)
 layer_masks={}
 for group in ['nearUpperArm','nearForeArm','farArm']:
  layer=Image.new('RGBA',(256,256));dd=ImageDraw.Draw(layer)
  for surf in p['surfaces']:
   if surf['group']==group:dd.polygon([(z['x'],z['y']) for z in surf['points']],fill='#%06x'%surf['color'])
  layer.save(layer_dir/(group+'.png'));layer_masks[group]=layer
 current_sleeve.save(layer_dir/'nearSleeveConnected.png')
 upper.save(layer_dir/'nearShoulderUpper.png');layer_masks['nearShoulderUpper']=upper
 # The held hand and recovery hand are always covered by a matching sleeve cuff.
 for group,at,hand,angle,origin in [('nearForeArm',moved_hand,current_hand,fa,(-14,-6)),('farArm',moved_far_hand,Image.open(D/'grip-hand.png').convert('RGBA'),bow_angle,(-8,-6))]:
  x,y=map(round,at);hl=Image.new('RGBA',(256,256));hl.alpha_composite(hand,(x+origin[0],y+origin[1]));hl=hl.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=(x,y))
  check_layer=current_sleeve if group=='nearForeArm' else layer_masks[group]
  assert ImageChops.multiply(check_layer.getchannel('A'),hl.getchannel('A')).getbbox(),('cuff gap',i,group)
 # These are mechanical guards, not a substitute for the whole-body art review.
 assert ImageChops.multiply(layer_masks['nearShoulderUpper'].getchannel('A'),layer_masks['nearForeArm'].getchannel('A')).getbbox(),('elbow gap',i)
 # Verify the proximal upper sleeve is actually visible in the final image,
 # rather than merely present in an occluded source layer.
 if t>=.40:
  for step in range(21):
   pos=tuple(round(a+(b-a)*step/20) for a,b in zip(near_sh,moved_el))
   color=actor.getpixel(pos)
   assert color[3]==255 and color[2]>color[0]*1.1 and color[2]>color[1]*1.03,('upper sleeve path interrupted',i,pos)
 previous_pose=json.loads((R/'Art/Parts/P1-Battle/hunting-bow-followthrough-r7-v2/frames'/f'{i:03}'/'pose.json').read_text())
 for name in ['farUpper','farFore','farHand','bow','torso']:
  assert p['parts'][name]==previous_pose['parts'][name],('far-side pose change',i,name)
 for key in ['upperTip','lowerTip','stringHand','arrowTail','arrowTip','arrowVisible']:
  assert p[key]==previous_pose[key],('unrequested bow or arrow change',i,key)
 # The head, clothing source and far arm remain; the near arm's 2D projection
 # intentionally unfolds instead of preserving the defective v2 projected lengths.
 assert actor.crop((100,75,158,126)).tobytes()==Image.open(BASE/'assembled.png').convert('RGBA').crop((100,75,158,126)).tobytes()
 for fx,fy in face_pixels:
  assert actor.getpixel((fx,fy))==reference_actor.getpixel((fx,fy)),('opaque face change',i,fx,fy)
 assert [s for s in p['surfaces'] if s['group']=='torso']==[s for s in baseline['surfaces'] if s['group']=='torso']
 assert p['parts']['nearUpper']['pivot']==baseline['parts']['nearUpper']['pivot']
 new_far_el=coord(p['parts']['farFore']['pivot'])
 assert abs(math.dist(far_sh,new_far_el)-math.dist(far_sh,old_far_el))<1e-8
 assert abs(math.dist(new_far_el,moved_far_hand)-math.dist(old_far_el,far_h))<1e-8
 projectile=None;frame=actor.copy()
 if t>=release:
  age=t-release;travel=min(age,.02)/.02*(neutral[0]-near_h[0])+max(0,age-.02)*800
  tail=(near_h[0]+travel,near_h[1]);tip=(baseline['arrowTip']['x']+travel,near_h[1])
  if tail[0]<258:
   projectile={'tail':q(tail),'tip':q(tip)}
   dd=ImageDraw.Draw(frame);dd.line((*tail,*tip),fill='#d4ab66',width=1);dd.polygon([(tip[0]+2,tip[1]),(tip[0]-3,tip[1]-2),(tip[0]-3,tip[1]+2)],fill='#d8e0d9')
 actor.save(layer_dir/'assembled.png');frame.save(O/'frames'/f'{i:03}.png')
 (layer_dir/'pose.json').write_text(json.dumps(p,separators=(',',':'))+'\n')
 records.append({'frame':i,'time':round(t,2),'pose':f'frames/{i:03}/pose.json','nearSleeve':f'frames/{i:03}/nearSleeveConnected.png','handVariant':variant,'projectile':projectile,'nearHand':q(moved_hand),'nearElbow':q(moved_el),'farHand':q(moved_far_hand),'nearForeRotation':fa,'bowRotation':bow_angle})
 bg=Image.new('RGBA',(256,256),'#20372a');bg.alpha_composite(frame);frames.append(bg.convert('RGB'))
# Global palette: stationary face colors cannot fluctuate from frame to frame.
paletteboard=Image.new('RGB',(256*10,256*9),'#20372a')
for i,im in enumerate(frames):paletteboard.paste(im,(i%10*256,i//10*256))
palette=paletteboard.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
encoded=[im.resize((768,768),Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
encoded[0].save(O/'bow-release-normal.gif',save_all=True,append_images=encoded[1:],duration=20,disposal=2,optimize=False)
# Omit the loop extension: the relaxed ending must not jump back to full draw.
gif=Image.open(O/'bow-release-normal.gif');assert 'loop' not in gif.info
elapsed=0;decoded=[]
for j in range(gif.n_frames):
 gif.seek(j);im=gif.convert('RGB');duration=gif.info['duration'];decoded.append((im.copy(),elapsed,duration));elapsed+=duration
 assert im.crop((300,225,474,378)).tobytes()==encoded[0].convert('RGB').crop((300,225,474,378)).tobytes(),('decoded head change',j)
 for fx,fy in face_pixels:
  pos=(fx*3+1,fy*3+1)
  assert im.getpixel(pos)==encoded[0].convert('RGB').getpixel(pos),('decoded opaque face/mouth change',j,fx,fy)
assert elapsed==len(frames)*20
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14)
for page in range((len(decoded)+11)//12):
 board=Image.new('RGB',(1024,840),'#20372a');dd=ImageDraw.Draw(board)
 for j,(im,tm,dur) in enumerate(decoded[page*12:page*12+12]):
  x=j%4*256;y=j//4*280;board.paste(im.resize((256,256),Image.Resampling.NEAREST),(x,y));dd.text((x+6,y+258),f'{tm/1000:.2f}s / {dur}ms',font=font,fill='#f0e4b6')
 board.save(O/f'decoded-{page+1:02}.jpg',quality=97)
for i,label in [(0,'drawn'),(10,'release'),(18,'recovering'),(26,'recovered'),(42,'lowering'),(60,'rest')]:
 frames[i].resize((768,768),Image.Resampling.NEAREST).save(O/(label+'.png'))
for page in range(6):
 board=Image.new('RGB',(1280,888),'#20372a');dd=ImageDraw.Draw(board)
 for j,i in enumerate(range(page*15,min(85,(page+1)*15))):
  x=j%5*256;y=j//5*296;board.paste(frames[i],(x,y));dd.text((x+8,y+260),f'{i:03} / {i*.02:.2f}s',font=font,fill='#f0e4b6')
 board.save(O/f'native-frames-{page+1:02}.jpg',quality=98)
board=Image.new('RGB',(1024,1104),'#20372a');dd=ImageDraw.Draw(board)
for row,(label,title) in enumerate([('recovering','收手中'),('rest','放下后')]):
 for col,version in enumerate(['v2','v3']):
  path=R/'Art/Review/Battle'/('hunting-bow-followthrough-r7-'+version)/(label+'.png')
  im=Image.open(path).convert('RGB').resize((512,512),Image.Resampling.NEAREST)
  board.paste(im,(col*512,row*552+40));dd.text((col*512+20,row*552+10),f'{version} · {title}',font=font,fill='#f0e4b6')
board.save(O/'arm-comparison.png')
# No angle wrap at +/- pi in exported joint metadata.
angles=[json.loads((D/z['pose']).read_text())['parts']['nearUpper']['rotation'] for z in records]
assert max(abs(a-b) for a,b in zip(angles,angles[1:]))<.25
(D/'animation.json').write_text(json.dumps({'schemaVersion':1,'baseline':'Art/Parts/P1-Battle/hunting-bow-aim-project-r7','frameDurationMs':20,'durationMs':len(frames)*20,'releaseSeconds':release,'recoverySeconds':recover_duration,'playback':'once','frames':records,'runtimeImported':False,'userApproved':False},indent=2)+'\n')
(O/'validation.json').write_text(json.dumps({'nativeFrameCount':len(frames),'durationMs':elapsed,'decodedGIFFrames':len(decoded),'firstNativeFrameExactlyMatchesR7':True,'headNativeAndDecodedPixelsStable':True,'torsoSurfacesUnchanged':True,'shoulderPivotsUnchanged':True,'nearArm2DProjectionUnfolds':True,'opaqueFaceAndMouthNativeAndDecodedPixelsStable':True,'allFramesSleeveWristOverlap':True,'allFramesElbowOverlap':True,'shoulderToElbowVisibleSleevePathContinuous':True,'farArmAndBowPosesUnchangedFromV2':True,'globalGIFPalette':True,'singlePlaybackNoLoopSnap':True,'releaseRecoverySeconds':recover_duration,'imageGenerationUsed':False,'runtimeImported':False,'deviceRunPerformed':False,'userApproved':False},indent=2)+'\n')
(D/'authoring.json').write_text(json.dumps({'baseline':str(BASE.relative_to(R)),'baselinePoseSHA256':hashlib.sha256((BASE/'pose.json').read_bytes()).hexdigest(),'baselineCompositeSHA256':hashlib.sha256((BASE/'assembled.png').read_bytes()).hexdigest(),'sharedLayers':{'torso':'torso.png','bodyCore':'body-core-clean.png','farHand':'grip-hand.png'},'nearHandVariants':['drawing-hand-held.png','drawing-hand-open.png','drawing-hand-relaxed.png'],'nearHandDrawBounds':[-14,-6,16,12],'farHandDrawBounds':[-8,-6,14,12],'layerOrder':['farArm','nearUpperArm','torso','nearSleeveConnected','head','hair','face','bow','stringAndArrow','farHand','nearHand'],'nearSleeveComposition':'Use the connected foreground PNG. Component PNGs/polygons are construction references; separately outlining them recreates the elbow seam.','projection':'near shoulder is fixed; the foreshortened upper arm unfolds and sleeve cuff projection shortens during lowering; this is not a rigid v2 rotation.','sourceClothingCleanup':'same legacy waist fragment masks as r7; neutral undershirt pixels completely hidden by the baseline drawing palm removed for recovery exposure','script':'scripts/author-bow-followthrough-r7-v3.py','imageGenerationUsed':False,'runtimeImported':False,'userApproved':False},indent=2)+'\n')
print(json.dumps({'nativeFrames':len(frames),'decodedGIFFrames':len(decoded),'durationMs':elapsed,'gif':str(O/'bow-release-normal.gif')}))
