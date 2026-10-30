#!/usr/bin/env python3
"""Native modular bow preparation, followed by the approved r7-v3 release.
No generated character image, runtime import or device execution.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFont,ImageFilter
import copy,json,math,hashlib,shutil
R=Path(__file__).resolve().parents[1]
NAME='hunting-bow-full-cycle-r7-v1'
D=R/'Art/Parts/P1-Battle'/NAME;O=R/'Art/Review/Battle'/NAME
D.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
(D/'frames').mkdir(exist_ok=True);(O/'frames').mkdir(exist_ok=True)
APP=R/'Art/Parts/P1-Battle/hunting-bow-followthrough-r7-v3'
APP_REVIEW=R/'Art/Review/Battle/hunting-bow-followthrough-r7-v3'
# Reuse only the existing native compositor and sleeve construction helpers.
# Redirect their output to this new candidate: approved assets remain untouched.
helper=R/'scripts/author-bow-followthrough-r7-v3.py'
code=helper.read_text().split('for i in range(85):')[0]
code=code.replace("hunting-bow-followthrough-r7-v3",NAME)
code=code.replace('for yy in range(132,169):','for yy in range(mask.getbbox()[1],mask.getbbox()[3]):')
code=code.replace('for xx in range(103,125):','for xx in range(mask.getbbox()[0],mask.getbbox()[2]):')
H={'__file__':str(helper)};exec(compile(code,str(helper),'exec'),H)
N=H['N'];baseline=H['baseline'];smooth=H['smooth'];rotate=H['rotate'];add=H['add'];sub=H['sub'];coord=H['coord'];q=H['q'];bodypoint=H['bodypoint'];center=H['center']
near_sh=H['near_sh'];near_el=H['near_el'];near_h=H['near_h'];far_sh=H['far_sh'];far_h=H['far_h']
reference=Image.open(APP/'frames/000/assembled.png').convert('RGBA')
rest=json.loads((APP/'frames/084/pose.json').read_text())
rest_hand=center(rest['parts']['nearHand']);rest_el=coord(rest['parts']['nearFore']['pivot'])
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14)
def mix(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
def curve(a,c,b,t):return tuple((1-t)**2*x+2*(1-t)*t*y+t*t*z for x,y,z in zip(a,c,b))
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def place(p,name,at,angle):
 part=p['parts'][name];part['offset']=q(sub(at,coord(part['pivot'])));part['rotation']=angle
def surface(p,group):
 im=Image.new('RGBA',(256,256));dd=ImageDraw.Draw(im)
 for s in p['surfaces']:
  if s['group']==group:dd.polygon([coord(z) for z in s['points']],fill='#%06x'%s['color'])
 return im
frames=[];records=[];poses=[];pre_count=58
for i in range(pre_count):
 t=i*.02;reach=smooth((t-.28)/.38);draw=smooth((t-.76)/.40)
 raised=.45*reach+.55*draw;far_angle=.27*(1-raised);bow_angle=.09*(1-raised)
 moved_far=bodypoint(far_h,far_sh,far_angle)
 neutral=bodypoint((174,139),far_h,bow_angle,moved_far)
 dock_el=(137,157)
 if t<=.76:
  elbow=curve(rest_el,(118,165),dock_el,reach)
  hand=mix(rest_hand,neutral,reach)
  relax=1-.30*reach
 else:
  elbow=curve(dock_el,(112,163),near_el,draw)
  hand=mix(neutral,near_h,draw)
  relax=.70*(1-draw)
 # Registered palm follows the sleeve at the wrist, not a torso-only rotation.
 hand_angle=math.atan2(hand[1]-elbow[1],hand[0]-elbow[0])-H['near_fore_start']
 if reach==0:hand_angle=.12
 cuff=add(hand,rotate((-11,0),hand_angle))
 old_upper=sub(near_el,near_sh);new_upper=sub(elbow,near_sh)
 upper_angle=(math.atan2(new_upper[1],new_upper[0])-H['near_upper_start']+math.pi)%(2*math.pi)-math.pi
 # Map the native sleeve along its cuff axis; widths and elbow bulb are
 # independently controlled, preserving the jacket's source palette.
 old_cuff=sub((130,139),near_el);old_len=math.hypot(*old_cuff);ou=tuple(v/old_len for v in old_cuff);on=(-ou[1],ou[0])
 new_cuff=sub(cuff,elbow);new_len=math.hypot(*new_cuff);nu=tuple(v/new_len for v in new_cuff);nn=(-nu[1],nu[0])
 p=copy.deepcopy(baseline)
 for s in p['surfaces']:
  group=s['group']
  if group=='nearUpperArm':
   ov=sub(near_el,near_sh);ol=math.hypot(*ov);unit=tuple(v/ol for v in ov);normal=(-unit[1],unit[0]);nl=math.dist(near_sh,elbow)
   def f(v):
    rel=sub(v,near_sh);ax=sum(a*b for a,b in zip(rel,unit))*nl/ol;ay=sum(a*b for a,b in zip(rel,normal))
    return add(near_sh,rotate(add(tuple(z*ax for z in unit),tuple(z*ay for z in normal)),upper_angle))
  elif group=='nearForeArm':
   def f(v):
    rel=sub(v,near_el);ax=sum(a*b for a,b in zip(rel,ou));ay=sum(a*b for a,b in zip(rel,on))
    ax*=new_len/old_len if ax>=0 else 1-.50*relax;ay*=1-.13*relax
    return add(elbow,add(tuple(z*ax for z in nu),tuple(z*ay for z in nn)))
  elif group=='farArm':f=lambda v:bodypoint(v,far_sh,far_angle)
  else:continue
  s['points']=[q(tuple(round(k) for k in f(coord(z)))) for z in s['points']]
 place(p,'nearUpper',near_sh,H['near_upper_start']+upper_angle)
 p['parts']['nearFore']['pivot']=q(elbow);p['parts']['nearFore']['offset']=q((0,0));p['parts']['nearFore']['rotation']=math.atan2(hand[1]-elbow[1],hand[0]-elbow[0])
 place(p,'nearHand',hand,hand_angle)
 place(p,'farUpper',far_sh,baseline['parts']['farUpper']['rotation']+far_angle)
 old_far_el=coord(baseline['parts']['farFore']['pivot']);p['parts']['farFore']['pivot']=q(bodypoint(old_far_el,far_sh,far_angle))
 p['parts']['farFore']['rotation']=baseline['parts']['farFore']['rotation']+far_angle
 place(p,'farHand',moved_far,bow_angle);place(p,'bow',moved_far,bow_angle)
 for key in ['upperTip','lowerTip']:p[key]=q(bodypoint(coord(baseline[key]),far_h,bow_angle,moved_far))
 p['stringHand']=q(hand if t>=.66 else neutral)
 p['arrowTail']=q(hand)
 # The arrow is carried visibly at waist height, brought to the straight string,
 # then pulled back with the drawing fingers. No quiver retrieval is invented.
 arrow_angle=-.16*(1-reach)
 p['arrowTip']=q(add(hand,rotate((73,0),arrow_angle)))
 p['arrowVisible']=True;p['arrowAlpha']=1
 if t>=.66:assert p['stringHand']==p['arrowTail']==q(hand),('drawing-finger/string/arrow contact',i)
 variant='relaxed' if reach==0 else 'held'
 H['current_hand']=H[variant]
 sleeve,upper,fore=H['make_sleeve'](p,relax,elbow)
 if reach==0:
  # Exact approved resting arm before preparation; only the carried arrow is new.
  sleeve=Image.open(APP/'frames/084/nearSleeveConnected.png').convert('RGBA')
 N['current_sleeve']=sleeve;N['bow_samples']={('attack',198):p,('attack',199):p};N['gear_render'].cache_clear()
 actor=N['gear_render']('attack',.33,'huntingBow')
 fd=D/'frames'/f'{i:03}';fd.mkdir(exist_ok=True)
 dump(fd/'pose.json',p);sleeve.save(fd/'nearSleeveConnected.png');actor.save(fd/'assembled.png')
 for group in ['nearUpperArm','nearForeArm','farArm']:surface(p,group).save(fd/(group+'.png'))
 upper.save(fd/'nearShoulderUpper.png')
 # Verify actual sleeve-to-palm contact after deformation.
 for mask,at,hand_image,angle,origin in [(sleeve,hand,H[variant],hand_angle,(-14,-6)),(surface(p,'farArm'),moved_far,H['asset']('MeadowBattleBowGripHand'),bow_angle,(-8,-6))]:
  x,y=map(round,at);hl=Image.new('RGBA',(256,256));hl.alpha_composite(hand_image,(x+origin[0],y+origin[1]));hl=hl.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=(x,y))
  assert ImageChops.multiply(mask.getchannel('A'),hl.getchannel('A')).getbbox(),('sleeve wrist gap',i)
 assert actor.crop((100,75,158,126)).tobytes()==reference.crop((100,75,158,126)).tobytes(),('head change',i)
 for x,y in H['face_pixels']:assert actor.getpixel((x,y))==reference.getpixel((x,y)),('face change',i,x,y)
 assert p['parts']['nearUpper']['pivot']==baseline['parts']['nearUpper']['pivot']
 record={'frame':i,'time':round(t,2),'phase':'ready' if t<.28 else 'nock' if t<.76 else 'draw','pose':f'frames/{i:03}/pose.json','nearSleeve':f'frames/{i:03}/nearSleeveConnected.png','handVariant':variant,'projectile':None}
 records.append(record);poses.append(p)
 actor.save(O/'frames'/f'{i:03}.png');bg=Image.new('RGBA',(256,256),'#20372a');bg.alpha_composite(actor);frames.append(bg.convert('RGB'))
# Append every approved release frame and layer without changing its bytes.
approved=json.loads((APP/'animation.json').read_text())
for old in approved['frames']:
 j=old['frame'];i=pre_count+j;src=APP/'frames'/f'{j:03}';fd=D/'frames'/f'{i:03}'
 shutil.copytree(src,fd,dirs_exist_ok=True)
 for f in src.iterdir():
  if f.is_file():assert f.read_bytes()==(fd/f.name).read_bytes()
 record=copy.deepcopy(old);record.update(frame=i,time=round(i*.02,2),pose=f'frames/{i:03}/pose.json',nearSleeve=f'frames/{i:03}/nearSleeveConnected.png',phase='approved-followthrough',sourceFrame=j)
 records.append(record);poses.append(json.loads((fd/'pose.json').read_text()))
 im=Image.open(APP_REVIEW/'frames'/f'{j:03}.png').convert('RGBA');im.save(O/'frames'/f'{i:03}.png')
 bg=Image.new('RGBA',(256,256),'#20372a');bg.alpha_composite(im);frames.append(bg.convert('RGB'))
assert (D/'frames/058/assembled.png').read_bytes()==(APP/'frames/000/assembled.png').read_bytes()
dump(D/'animation.json',{'frameDurationMs':20,'durationMs':len(frames)*20,'releaseSeconds':round(pre_count*.02+.18,2),'newPreparationFrames':pre_count,'approvedFollowthroughFrames':85,'playback':'once','frames':records,'runtimeImported':False,'userApproved':False})
dump(D/'authoring.json',{'baseline':'Art/Parts/P1-Battle/hunting-bow-aim-project-r7','approvedFollowthrough':str(APP.relative_to(R)),'script':str(Path(__file__).relative_to(R)),'frameLayerOrder':['farArm','nearUpperArm','torso','nearSleeveConnected','head','hair','face','bow','stringAndArrow','farHand','nearHand'],'nearSleeveConstruction':'sleeve-construction.json','interchangeableWeaponAnchors':['parts.bow','parts.farHand','upperTip','lowerTip','stringHand','arrowTail','arrowTip'],'imageGenerationUsed':False,'runtimeImported':False})
dump(D/'weapon-binding.json',{'weaponID':'huntingBow','assetName':'MeadowBattleHuntingBow','referenceGrip':q(far_h),'referenceUpperTip':baseline['upperTip'],'referenceLowerTip':baseline['lowerTip'],'referenceStraightStringNock':q((174,139)),'referenceDrawnStringNock':q(near_h),'arrowLength':73,'bindingScope':'Offline native art candidate. Other bows need their own grip/tip registration; runtime importer is not implemented in this iteration.'})
dump(D/'sleeve-construction.json',{'readyElbow':q(rest_el),'nockElbow':q((137,157)),'drawElbowControl':q((112,163)),'drawnElbow':q(near_el),'nockHand':'straight string center, bow-local (174,139)','drawnHand':q(near_h),'nearShoulder':q(near_sh),'readyArrow':'already carried in drawing hand; this clip does not depict quiver retrieval','approachSeconds':[.28,.66],'contactHoldSeconds':[.66,.76],'drawSeconds':[.76,1.16],'baselineSurfaces':str(H['BASE'].relative_to(R))+'/pose.json'})
# One global palette prevents face colors changing while the arms move.
paletteboard=Image.new('RGB',(256*12,256*12),'#20372a')
for i,im in enumerate(frames):paletteboard.paste(im,(i%12*256,i//12*256))
palette=paletteboard.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
encoded=[im.resize((768,768),Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
encoded[0].save(O/'bow-full-cycle-normal.gif',save_all=True,append_images=encoded[1:],duration=20,disposal=2,optimize=False)
gif=Image.open(O/'bow-full-cycle-normal.gif');assert 'loop' not in gif.info
decoded=[];elapsed=0
for i in range(gif.n_frames):
 gif.seek(i);im=gif.convert('RGB');dur=gif.info['duration'];decoded.append((im.copy(),elapsed,dur));elapsed+=dur
 assert im.crop((300,225,474,378)).tobytes()==encoded[0].convert('RGB').crop((300,225,474,378)).tobytes(),('decoded head flicker',i)
 for x,y in H['face_pixels']:assert im.getpixel((x*3+1,y*3+1))==encoded[0].convert('RGB').getpixel((x*3+1,y*3+1))
assert elapsed==len(frames)*20
for page in range(math.ceil(len(decoded)/12)):
 b=Image.new('RGB',(1024,840),'#20372a');dd=ImageDraw.Draw(b)
 for j,(im,t,dur) in enumerate(decoded[page*12:page*12+12]):
  x=j%4*256;y=j//4*280;b.paste(im.resize((256,256),Image.Resampling.NEAREST),(x,y));dd.text((x+6,y+258),f'{t/1000:.2f}s / {dur}ms',font=font,fill='#f0e4b6')
 b.save(O/f'decoded-{page+1:02}.jpg',quality=98)
for i,label in [(0,'ready'),(24,'approach'),(34,'nocked'),(45,'drawing'),(58,'drawn'),(84,'recovered'),(118,'rest')]:frames[i].resize((768,768),Image.Resampling.NEAREST).save(O/(label+'.png'))
board=Image.new('RGB',(1536,1104),'#20372a');dd=ImageDraw.Draw(board)
for j,(i,label) in enumerate([(0,'持箭待发'),(34,'搭箭'),(45,'拉弦'),(58,'满弓'),(84,'收手'),(118,'收势')]):
 x=j%3*512;y=j//3*552;board.paste(frames[i].resize((512,512),Image.Resampling.NEAREST),(x,y+40));dd.text((x+20,y+10),label,font=font,fill='#f0e4b6')
board.save(O/'keyframes.png')
for page in range(math.ceil(pre_count/12)):
 b=Image.new('RGB',(1024,840),'#20372a');dd=ImageDraw.Draw(b)
 for j,i in enumerate(range(page*12,min(pre_count,(page+1)*12))):
  x=j%4*256;y=j//4*280;b.paste(frames[i],(x,y));dd.text((x+6,y+258),f'{i:03} / {i*.02:.2f}s',font=font,fill='#f0e4b6')
 b.save(O/f'preparation-native-{page+1:02}.jpg',quality=98)
dump(O/'validation.json',{'nativeSamples':len(frames),'decodedFrames':len(decoded),'durationMs':elapsed,'approvedFollowthroughLayersAndPosesByteExact':True,'headFaceStableNativeAndDecoded':True,'allPreparationSleeveWristOverlaps':True,'shoulderPivotsFixed':True,'firstFullDrawExactlyR7':True,'drawingFingerStringAndArrowCoincideAfterNocking':True,'globalPalette':True,'singlePlayback':True,'imageGenerationUsed':False,'runtimeImported':False,'deviceRunPerformed':False,'userApproved':False})
print(json.dumps({'samples':len(frames),'decodedFrames':len(decoded),'durationMs':elapsed,'gif':str(O/'bow-full-cycle-normal.gif')}))
