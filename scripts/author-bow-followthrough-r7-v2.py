#!/usr/bin/env python3
"""Continue the accepted r7 native bow pose: release, 0.32 s recovery, lower bow.
All poses use independent existing project layers; no image generation or app run.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFont,ImageSequence
import json,math,copy,shutil,hashlib
R=Path(__file__).resolve().parents[1]
BASE=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r7'
D=R/'Art/Parts/P1-Battle/hunting-bow-followthrough-r7-v2';D.mkdir(exist_ok=True)
O=R/'Art/Review/Battle/hunting-bow-followthrough-r7-v2';O.mkdir(exist_ok=True)
(O/'frames').mkdir(exist_ok=True);(D/'frames').mkdir(exist_ok=True)
for name in ['torso.png','drawing-hand.png','grip-hand.png']:shutil.copyfile(BASE/name,D/name)
baseline=json.loads((BASE/'pose.json').read_text())
# Use the exact project-resource compositor from the accepted first pose.
script=R/'scripts/review-bow-aim-project-r7.py';N={'__file__':str(script)}
exec(compile(script.read_text().split('assembled=gear_render')[0],str(script),'exec'),N)
N['D']=D
composition=N['composition']
assert composition.count("['farArm','nearUpperArm','torso','nearForeArm','head']")==1
composition=composition.replace("['farArm','nearUpperArm','torso','nearForeArm','head']", "['farArm','nearUpperArm','torso','nearShoulderUpper','nearForeArm','head']")
composition=composition.replace("['torso','farArm','farHand','nearUpperArm','nearForeArm','nearHand']", "['torso','farArm','farHand','nearUpperArm','nearShoulderUpper','nearForeArm','nearHand']")
exec(compile(composition,'r7-recovery-visible-shoulder','exec'),N)
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
# A short upper arm points back at full draw. Its elbow lowers as the forearm
# drops, rather than using an IK branch that raises the elbow above the head.
near_upper_start=math.atan2(near_el[1]-near_sh[1],near_el[0]-near_sh[0])
near_fore_start=math.atan2(near_h[1]-near_el[1],near_h[0]-near_el[0])
near_upper_end=-3.85;near_fore_end=.42
# Complete front-facing upper sleeve. At full draw this capsule is wholly
# hidden by the accepted foreground forearm, so the starting frame is unchanged.
shoulder_surfaces=[]
def shoulder_poly(color,points):
 shoulder_surfaces.append({'group':'nearShoulderUpper','color':int(color.strip('#'),16),'points':[q(v) for v in points]})
def shoulder_disc(color,c,r):
 shoulder_poly(color,[(c[0]+r*math.cos(a*math.pi/4),c[1]+r*math.sin(a*math.pi/4)) for a in range(8)])
u=sub(near_el,near_sh);length=math.hypot(*u);normal=(-u[1]/length,u[0]/length)
def shoulder_strip(color,r,shift=0,a=near_sh,b=near_el):
 shoulder_poly(color,[add(a,(normal[0]*(r+shift),normal[1]*(r+shift))),add(b,(normal[0]*(r+shift),normal[1]*(r+shift))),add(b,(normal[0]*(-r+shift),normal[1]*(-r+shift))),add(a,(normal[0]*(-r+shift),normal[1]*(-r+shift)))])
shoulder_strip('#243953',4)
for c in [near_sh,near_el]:shoulder_disc('#243953',c,4)
shoulder_strip('#315b94',3)
shoulder_disc('#315b94',near_sh,4)
shoulder_disc('#315b94',near_el,3)
shoulder_strip('#274a7d',.75,-2)
shoulder_strip('#497bb6',.6,1.3,a=add(near_sh,(u[0]*.2,u[1]*.2)),b=add(near_sh,(u[0]*.75,u[1]*.75)))
(D/'shoulder-upper-source.json').write_text(json.dumps({'shoulder':q(near_sh),'elbow':q(near_el),'surfaces':shoulder_surfaces},indent=2)+'\n')
release=.18;recover_start=.20;recover_duration=.32
frames=[];records=[]
asset('MeadowBattleBowBodyCore').save(D/'body-core-clean.png')
for i in range(85):
 t=i*.02;r=smooth((t-recover_start)/recover_duration)
 ua=(near_upper_end-near_upper_start)*r;fa=(near_fore_end-near_fore_start)*r
 moved_el=bodypoint(near_el,near_sh,ua)
 moved_hand=bodypoint(near_h,near_el,fa,moved_el)
 lower=smooth((t-.56)/.52);far_angle=.27*lower;bow_angle=.09*lower
 moved_far_hand=bodypoint(far_h,far_sh,far_angle)
 p=copy.deepcopy(baseline)
 p['surfaces'].extend(copy.deepcopy(shoulder_surfaces))
 for surf in p['surfaces']:
  group=surf['group']
  if group=='torso':continue
  if group in ['nearUpperArm','nearShoulderUpper']:f=lambda v:bodypoint(v,near_sh,ua)
  elif group=='nearForeArm':f=lambda v:bodypoint(v,near_el,fa,moved_el)
  elif group=='farArm':f=lambda v:bodypoint(v,far_sh,far_angle)
  else:continue
  surf['points']=[q(tuple(round(k) for k in f(coord(point)))) for point in surf['points']]
 def place(name,at,angle):
  part=p['parts'][name];part['offset']=q(sub(at,coord(part['pivot'])));part['rotation']=angle
 place('nearUpper',near_sh,near_upper_start+ua)
 p['parts']['nearFore']['pivot']=q(moved_el);p['parts']['nearFore']['offset']=q((0,0));p['parts']['nearFore']['rotation']=near_fore_start+fa
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
 N['bow_samples']={('attack',198):p,('attack',199):p};N['gear_render'].cache_clear()
 actor=N['gear_render']('attack',.33,'huntingBow')
 # The first frame must literally be the accepted native composite.
 if i==0:assert actor.tobytes()==Image.open(BASE/'assembled.png').convert('RGBA').tobytes()
 layer_dir=D/'frames'/f'{i:03}';layer_dir.mkdir(exist_ok=True)
 layer_masks={}
 for group in ['nearUpperArm','nearShoulderUpper','nearForeArm','farArm']:
  layer=Image.new('RGBA',(256,256));dd=ImageDraw.Draw(layer)
  for surf in p['surfaces']:
   if surf['group']==group:dd.polygon([(z['x'],z['y']) for z in surf['points']],fill='#%06x'%surf['color'])
  layer.save(layer_dir/(group+'.png'));layer_masks[group]=layer
 # The held hand and recovery hand are always covered by a matching sleeve cuff.
 for group,at,hand,angle,origin in [('nearForeArm',moved_hand,current_hand,fa,(-14,-6)),('farArm',moved_far_hand,Image.open(D/'grip-hand.png').convert('RGBA'),bow_angle,(-8,-6))]:
  x,y=map(round,at);hl=Image.new('RGBA',(256,256));hl.alpha_composite(hand,(x+origin[0],y+origin[1]));hl=hl.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=(x,y))
  assert ImageChops.multiply(layer_masks[group].getchannel('A'),hl.getchannel('A')).getbbox(),('cuff gap',i,group)
 # Both source sleeve parts meet around the same elbow through all poses.
 assert ImageChops.multiply(layer_masks['nearShoulderUpper'].getchannel('A'),layer_masks['nearForeArm'].getchannel('A')).getbbox(),('elbow gap',i)
 # Verify the proximal upper sleeve is actually visible in the final image,
 # rather than merely present in an occluded source layer.
 if t>=.40:
  shoulder_pixel=layer_masks['nearShoulderUpper'].getpixel((117,139))
  assert shoulder_pixel[3]==255,('missing proximal sleeve',i)
  assert actor.getpixel((117,139))==shoulder_pixel,('shoulder hidden in composite',i)
  for step in range(21):
   pos=tuple(round(a+(b-a)*step/20) for a,b in zip(near_sh,moved_el))
   color=actor.getpixel(pos)
   assert color[3]==255 and color[2]>color[0]*1.1 and color[2]>color[1]*1.03,('upper sleeve path interrupted',i,pos)
 previous_pose=json.loads((R/'Art/Parts/P1-Battle/hunting-bow-followthrough-r7-v1/frames'/f'{i:03}'/'pose.json').read_text())
 assert p['parts']==previous_pose['parts'],('unrequested pose change',i)
 for key in ['upperTip','lowerTip','stringHand','arrowTail','arrowTip','arrowVisible']:
  assert p[key]==previous_pose[key],('unrequested bow or arrow change',i,key)
 # Source head/hair and lower body remain static; preserve the accepted arm lengths.
 assert actor.crop((100,75,158,126)).tobytes()==Image.open(BASE/'assembled.png').convert('RGBA').crop((100,75,158,126)).tobytes()
 for fx,fy in face_pixels:
  assert actor.getpixel((fx,fy))==reference_actor.getpixel((fx,fy)),('opaque face change',i,fx,fy)
 assert [s for s in p['surfaces'] if s['group']=='torso']==[s for s in baseline['surfaces'] if s['group']=='torso']
 assert abs(math.dist(near_sh,moved_el)-math.dist(near_sh,near_el))<1e-8
 assert abs(math.dist(moved_el,moved_hand)-math.dist(near_el,near_h))<1e-8
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
 records.append({'frame':i,'time':round(t,2),'pose':f'frames/{i:03}/pose.json','handVariant':variant,'projectile':projectile,'nearHand':q(moved_hand),'nearElbow':q(moved_el),'farHand':q(moved_far_hand),'nearForeRotation':fa,'bowRotation':bow_angle})
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
(D/'animation.json').write_text(json.dumps({'schemaVersion':1,'baseline':'Art/Parts/P1-Battle/hunting-bow-aim-project-r7','frameDurationMs':20,'durationMs':len(frames)*20,'releaseSeconds':release,'recoverySeconds':recover_duration,'playback':'once','frames':records,'runtimeImported':False,'userApproved':False},indent=2)+'\n')
(O/'validation.json').write_text(json.dumps({'nativeFrameCount':len(frames),'durationMs':elapsed,'decodedGIFFrames':len(decoded),'firstNativeFrameExactlyMatchesR7':True,'headNativeAndDecodedPixelsStable':True,'torsoSurfacesUnchanged':True,'constantBothArmLengths':True,'opaqueFaceAndMouthNativeAndDecodedPixelsStable':True,'allFramesSleeveWristOverlap':True,'allFramesElbowOverlap':True,'recoveredShoulderActuallyVisibleInComposite':True,'shoulderToElbowVisibleSleevePathContinuous':True,'motionAndBowPosesUnchangedFromV1':True,'globalGIFPalette':True,'singlePlaybackNoLoopSnap':True,'releaseRecoverySeconds':recover_duration,'imageGenerationUsed':False,'runtimeImported':False,'deviceRunPerformed':False,'userApproved':False},indent=2)+'\n')
(D/'authoring.json').write_text(json.dumps({'baseline':str(BASE.relative_to(R)),'baselinePoseSHA256':hashlib.sha256((BASE/'pose.json').read_bytes()).hexdigest(),'baselineCompositeSHA256':hashlib.sha256((BASE/'assembled.png').read_bytes()).hexdigest(),'sharedLayers':{'torso':'torso.png','bodyCore':'body-core-clean.png','farHand':'grip-hand.png'},'nearHandVariants':['drawing-hand-held.png','drawing-hand-open.png','drawing-hand-relaxed.png'],'nearHandDrawBounds':[-14,-6,16,12],'farHandDrawBounds':[-8,-6,14,12],'layerOrder':['farArm','nearUpperArm','torso','nearShoulderUpper','nearForeArm','head','hair','face','bow','stringAndArrow','farHand','nearHand'],'sourceClothingCleanup':'same legacy waist fragment masks as r7; neutral undershirt pixels completely hidden by the baseline drawing palm removed for recovery exposure','script':'scripts/author-bow-followthrough-r7-v2.py','imageGenerationUsed':False,'runtimeImported':False,'userApproved':False},indent=2)+'\n')
print(json.dumps({'nativeFrames':len(frames),'decodedGIFFrames':len(decoded),'durationMs':elapsed,'gif':str(O/'bow-release-normal.gif')}))
