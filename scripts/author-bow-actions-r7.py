#!/usr/bin/env python3
"""Author bow-only guard/recoil/celebration/kneeling clips from registered project layers.
Every limb, hand, garment and weapon remains independent. No image generation.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter,ImageFont
import ast,json,math,copy,functools,subprocess
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets'
D=R/'Art/Parts/P1-Battle/hunting-bow-actions-r7-v1';O=R/'Art/Review/Battle/hunting-bow-actions-r7-v1'
D.mkdir(parents=True,exist_ok=True);O.mkdir(parents=True,exist_ok=True)
BASE=R/'Art/Parts/P1-Battle/hunting-bow-aim-project-r7';REST=R/'Art/Parts/P1-Battle/hunting-bow-full-cycle-r7-v1/frames/142'
baseline=json.loads((BASE/'pose.json').read_text());rest=json.loads((REST/'pose.json').read_text())
def coord(p):return (p['x'],p['y'])
def q(p):return dict(x=p[0],y=p[1])
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def mul(a,t):return (a[0]*t,a[1]*t)
def mix(a,b,t):return add(a,mul(sub(b,a),t))
def rotate(v,a):return (v[0]*math.cos(a)-v[1]*math.sin(a),v[0]*math.sin(a)+v[1]*math.cos(a))
def smooth(t):t=min(1,max(0,t));return t*t*(3-2*t)
def at(p):return add(coord(p['pivot']),coord(p['offset']))
def angle(a,b):v=sub(b,a);return math.atan2(v[1],v[0])
def part(pivot,moved,rot):return dict(pivot=q(pivot),offset=q(sub(moved,pivot)),rotation=rot)
@functools.lru_cache(None)
def asset(n):
 d=A/(n+'.imageset');j=json.loads((d/'Contents.json').read_text());return Image.open(d/next(i['filename'] for i in j['images'] if i.get('filename'))).convert('RGBA')
def blank():return Image.new('RGBA',(256,256))
def transformed(im,pivot=(132,167),offset=(0,0),rotation=0):
 im=im.rotate(-math.degrees(rotation),Image.Resampling.NEAREST,center=pivot);out=blank();out.alpha_composite(im,tuple(map(round,offset)));return out
near_sh=(117,141);near_el=(104,136);near_h=(141,139);far_sh=(138,148);far_el=(159,152);far_h=(184,152)
cuff_source=(130,139);cuff_vector=sub(cuff_source,near_el);cuff_length=math.hypot(*cuff_vector);cuff_unit=mul(cuff_vector,1/cuff_length);cuff_normal=(-cuff_unit[1],cuff_unit[0])
# Reuse the accepted continuous-sleeve construction, extending its shading bounds
# to the actual capsule instead of a fixed old shoulder rectangle.
source=(R/'scripts/author-bow-followthrough-r7-v3.py').read_text();tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='make_sleeve')
fn=ast.get_source_segment(source,node).replace('range(132,169)','range(max(0,mask.getbbox()[1]),min(256,mask.getbbox()[3]))').replace('range(103,125)','range(max(0,mask.getbbox()[0]),min(256,mask.getbbox()[2]))').replace('range(130,172)','range(max(0,union.getbbox()[1]),min(256,union.getbbox()[3]))').replace('range(94,146)','range(max(0,union.getbbox()[0]),min(256,union.getbbox()[2]))')
exec(fn,globals())
renderer=R/'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py';N={'__file__':str(renderer)};exec(renderer.read_text().split("\nfor clip,data in lib['clips'].items():")[0],N);N['lib']=json.loads((A/'MeadowBattleHeroAnimationV2.dataset/animation.json').read_text())
config=N['config'];skip={'MeadowBattleHeroWeapon','MeadowBattleHeroFarHand','MeadowBattleHeroNearHand','MeadowBattleHeroJointUnderlay','MeadowBattleHeroWardrobeCore','MeadowBattleHeroArmNearUpperBody','MeadowBattleHeroArmNearForearmBody','MeadowBattleHeroArmNearUpperWardrobe','MeadowBattleHeroArmNearForearmWardrobe'}
names=[n for n in config['layers'] if n not in skip];idx=names.index('MeadowBattleHeroHair');order=names[:idx]+['farArm','nearUpperArm','torso','nearSleeveConnected','head']+names[idx:]+['MeadowBattleHeroWeapon','geometry','farHand','nearHand']
rest_images={n:asset({'MeadowBattleHeroBodyCore':'MeadowBattleBowReviewedBodyCore','MeadowBattleHeroLegNearThighWardrobe':'MeadowBattleBowReviewedLegNearThighWardrobe','MeadowBattleHeroLegFarThighWardrobe':'MeadowBattleBowReviewedLegFarThighWardrobe'}.get(n,n)).copy() for n in names}
mask=Image.new('L',(256,256));ImageDraw.Draw(mask).rectangle((100,174,152,190),fill=255);rest_images['MeadowBattleHeroBodyCore'].putalpha(ImageChops.multiply(rest_images['MeadowBattleHeroBodyCore'].getchannel('A'),mask))
mask=Image.new('L',(256,256));dd=ImageDraw.Draw(mask);dd.rectangle((100,75,156,132),fill=255);dd.polygon([(121,126),(135,130),(134,138),(125,138),(119,134)],fill=255)
head=asset('MeadowBattleBowReviewedBodyCore').copy();head.putalpha(ImageChops.multiply(head.getchannel('A'),mask));rest_images['head']=head
rest_images['torso']=asset('MeadowBattleBowReviewedTorso')
for n in ['nearUpperArm','nearSleeveConnected','farArm']:rest_images[n]=Image.open(REST/(n+'.png')).convert('RGBA')
def hand_layer(group,target,rot,variant='relaxed'):
 im=blank();file='grip-hand.png' if group=='farHand' else 'drawing-hand-'+variant+'.png';origin=(-8,-6) if group=='farHand' else (-14,-6);p=tuple(map(round,target));im.alpha_composite(Image.open(REST.parent.parent/file).convert('RGBA'),(p[0]+origin[0],p[1]+origin[1]));return im.rotate(-math.degrees(rot),Image.Resampling.NEAREST,center=p)
for name in ['nearHand','farHand']:rest_images[name]=hand_layer(name,at(rest['parts'][name]),rest['parts'][name]['rotation'])
def bone_point(z,a,b,aa,bb):
 u=sub(b,a);l=math.hypot(*u);u=mul(u,1/l);n=(-u[1],u[0]);v=sub(bb,aa);ll=math.hypot(*v);v=mul(v,1/ll);nn=(-v[1],v[0]);rel=sub(z,a);along=sum(x*y for x,y in zip(rel,u));across=sum(x*y for x,y in zip(rel,n));return add(aa,add(mul(v,along*ll/l),mul(nn,across)))
def warp_bone(im,a,b,aa,bb):
 # Backward nearest sampling avoids the pinholes of forward pixel splatting.
 out=blank();u=sub(b,a);l=math.hypot(*u);u=mul(u,1/l);n=(-u[1],u[0]);v=sub(bb,aa);ll=math.hypot(*v);v=mul(v,1/ll);nn=(-v[1],v[0]);box=im.getbbox()
 if not box:return out
 corners=[bone_point(p,a,b,aa,bb) for p in [(box[0],box[1]),(box[2],box[1]),(box[0],box[3]),(box[2],box[3])]]
 for y in range(max(0,math.floor(min(z[1] for z in corners))-1),min(256,math.ceil(max(z[1] for z in corners))+2)):
  for x in range(max(0,math.floor(min(z[0] for z in corners))-1),min(256,math.ceil(max(z[0] for z in corners))+2)):
   rel=sub((x,y),aa);along=sum(z*k for z,k in zip(rel,v));across=sum(z*k for z,k in zip(rel,nn));sx,sy=map(round,add(a,add(mul(u,along*l/ll),mul(n,across))))
   if 0<=sx<256 and 0<=sy<256:out.putpixel((x,y),im.getpixel((sx,sy)))
 return out

def frame(clip,p):
 global near_sh
 # Closed guard and hit actions return exactly to the approved rest pose.
 if clip=='guard':w=smooth(p/.23)*(1-smooth((p-.72)/.28));lean=-.025*w;crouch=2*w;dx=-1*w;target_el=(108,154);target_hand=(143,149);target_grip=(179,149);ba=-.12
 elif clip=='hit':w=smooth(p/.16)*(1-smooth((p-.23)/.70));lean=-.10*w;crouch=3*w;dx=-4*w;target_el=(108,155);target_hand=(136,158);target_grip=(171,158);ba=.29
 elif clip=='victory':w=smooth((p-.08)/.60);lean=.015*w;crouch=-1*w;dx=0;target_el=(111,157);target_hand=(142,158);target_grip=(180,141);ba=-.23
 else:w=smooth(p/.88);lean=.20*w;crouch=23*w;dx=-2*w;target_el=(126,186);target_hand=(149,211);target_grip=(181,194);ba=1.25
 def bp(z):return add(add((132,167),rotate(sub(z,(132,167)),lean)),(dx,crouch))
 sh=bp(near_sh);fsh=bp(far_sh)
 # For the grounded collapse targets are world/canvas coordinates. Other target
 # arm relationships are authored around the moving torso's coordinate system.
 def target(z):return z if clip=='defeat' else bp(z)
 el=mix(bp((112,159)),target(target_el),w);nh=mix(bp(at(rest['parts']['nearHand'])),target(target_hand),w);fh=mix(bp(at(rest['parts']['farHand'])),target(target_grip),w)
 bow_angle=rest['parts']['bow']['rotation']+(ba-rest['parts']['bow']['rotation'])*w+lean*(clip!='defeat')
 # Solve the sleeve cuff from the hand registration, preserving the accepted
 # hand-to-cuff vector and transverse sleeve width.
 hdelta=sub(near_h,cuff_source);ha=angle(el,nh)-angle((0,0),sub(near_h,near_el));cuff=sub(nh,rotate(hdelta,ha))
 surfaces=[]
 for surf in baseline['surfaces']:
  if surf['group']!='nearForeArm':continue
  s=copy.deepcopy(surf);s['points']=[q(tuple(map(round,bone_point(coord(z),near_el,cuff_source,el,cuff)))) for z in s['points']];surfaces.append(s)
 # make_sleeve is expressed in canvas coordinates and must use the moved root.
 old_sh=near_sh;near_sh=sh;near_sleeve,upper,fore=make_sleeve({'surfaces':surfaces},1,el);near_sh=old_sh
 # Far sleeve: two contiguous segments with a smooth shared elbow deformation.
 old_fel=coord(rest['parts']['farFore']['pivot']);old_fh=at(rest['parts']['farHand']);fel=mix(bp(old_fel),mix(fsh,fh,.50),w)
 far=blank();dd=ImageDraw.Draw(far)
 for s in rest['surfaces']:
  if s['group']!='farArm':continue
  pts=[]
  for z in s['points']:
   z=coord(z);axis=sub(old_fh,far_sh);u=max(0,min(1,sum(a*b for a,b in zip(sub(z,far_sh),axis))/sum(a*a for a in axis)));blend=smooth((u-.34)/.32)
   a=bone_point(z,far_sh,old_fel,fsh,fel);b=bone_point(z,old_fel,old_fh,fel,fh);pts.append(tuple(map(round,mix(a,b,blend))))
  dd.polygon(pts,fill='#%06x'%s['color'])
 images={}
 if clip!='defeat':
  tr,_,_,_,_=N['sample'](clip,p)
  for n,im in rest_images.items():
   if n in ['nearUpperArm','nearSleeveConnected','farArm','nearHand','farHand']:continue
   if 'Leg' in n:
    pivot,off,a=tr[n];images[n]=transformed(im,pivot,off,a)
   else:images[n]=transformed(im,(132,167),(dx,crouch),lean)
 else:
  for n,im in rest_images.items():
   if n in ['nearUpperArm','nearSleeveConnected','farArm','nearHand','farHand'] or 'Leg' in n:continue
   images[n]=transformed(im,(132,167),(dx,crouch),lean)
  for side,hip,knee,ankle,tk,ta in [('Near',(134,175),(141,187),(150,206),(144,201),(127,206)),('Far',(115,176),(104,192),(96,206),(104,205),(96,206))]:
   mh=bp(hip);mk=mix(knee,tk,w);ma=mix(ankle,ta,w)
   for kind in ['Body','Wardrobe']:
    n='MeadowBattleHeroLeg'+side+'Thigh'+kind;images[n]=warp_bone(rest_images[n],hip,knee,mh,mk)
    n='MeadowBattleHeroLeg'+side+'Shin'+kind;im=rest_images[n];pants=im.copy();boots=im.copy();cut=197
    ImageDraw.Draw(pants).rectangle((0,cut,255,255),fill=(0,0,0,0));ImageDraw.Draw(boots).rectangle((0,0,255,cut-1),fill=(0,0,0,0))
    # Bent trouser tube ends inside an upright boot collar. Grounded boots do
    # not rotate 120 degrees when the knee folds behind the seated hip.
    images[n]=warp_bone(pants,knee,(ankle[0],197),mk,(ma[0],197));images[n].alpha_composite(transformed(boots,(0,0),sub(ma,ankle),0))
 if clip=='defeat':
  for n,im in images.items():
   if 'Leg' in n:ImageDraw.Draw(im).rectangle((0,215,255,255),fill=(0,0,0,0))
 images.update(nearUpperArm=upper,nearSleeveConnected=near_sleeve,farArm=far,nearHand=hand_layer('nearHand',nh,ha,'open' if clip=='defeat' and w>.6 else 'relaxed'),farHand=hand_layer('farHand',fh,bow_angle))
 rig=copy.deepcopy(rest);rig['surfaces']=[];rig['parts']['torso']=part((132,167),(132+dx,167+crouch),lean)
 for name,pivot,moved,a in [('nearUpper',(117,141),sh,angle(sh,el)),('nearFore',el,el,angle(el,nh)),('nearHand',(145.6,163.7),nh,ha),('farUpper',(138,148),fsh,angle(fsh,fel)),('farFore',fel,fel,angle(fel,fh)),('farHand',(145.6,163.7),fh,bow_angle),('bow',(145.6,163.7),fh,bow_angle)]:rig['parts'][name]=part(pivot,moved,a)
 for key,z in [('upperTip',(174,116)),('lowerTip',(174,188)),('stringHand',(174,139))]:rig[key]=q(add(fh,rotate(sub(z,far_h),bow_angle)))
 rig['arrowVisible']=False;rig['arrowAlpha']=1;rig['canvasBaked']=True
 if w==0:
  images={n:im.copy() for n,im in rest_images.items()};rig=copy.deepcopy(rest);rig['surfaces']=[];rig['canvasBaked']=True
 # Derive boot contacts from the actual native alpha rows, not upright proxies.
 boot=blank()
 for n,im in images.items():
  if 'Shin' in n:boot.alpha_composite(im)
 box=boot.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox();ground=box[3]-1
 contacts=[]
 for side in ['Far','Near']:
  im=blank()
  for kind in ['Body','Wardrobe']:im.alpha_composite(images['MeadowBattleHeroLeg'+side+'Shin'+kind])
  xs=[x for x in range(256) if any(im.getpixel((x,y))[3]>=128 for y in range(max(0,ground-1),ground+1))]
  if xs:contacts.append(q((sum(xs)/len(xs),ground)))
 rig.update(rootOffset=q((0,214-ground)),groundY=ground,contacts=contacts)
 images={n:Image.alpha_composite(blank(),im) for n,im in images.items()}
 out=blank()
 for n in order:
  if n=='geometry':ImageDraw.Draw(out).line([tuple(map(round,coord(rig[k]))) for k in ['upperTip','stringHand','lowerTip']],fill='#e1c78c',width=1)
  elif n=='MeadowBattleHeroWeapon':out.alpha_composite(transformed(asset('MeadowBattleHuntingBow'),coord(rig['parts']['bow']['pivot']),coord(rig['parts']['bow']['offset']),rig['parts']['bow']['rotation']))
  else:out.alpha_composite(images[n])
 out=transformed(out,(0,0),(0,214-ground),0)
 return rig,images,out

if __name__=='__main__':
 clips={};font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14)
 for ci,(clip,duration) in enumerate([('guard',960),('hit',840),('victory',1080),('defeat',1080)]):
  records=[];frames=[];count=duration//20
  for i in range(count+1):
   p=i/count;rig,layers,out=frame(clip,p);folder=D/clip/f'{i:03}';folder.mkdir(parents=True,exist_ok=True)
   for n,im in layers.items():im.save(folder/(n+'.png'))
   (folder/'pose.json').write_text(json.dumps(rig,separators=(',',':'))+'\n');out.save(folder/'assembled.png');records.append(dict(progress=p,pose=str((folder/'pose.json').relative_to(D))))
   bg=Image.new('RGB',(256,280),'#20372a');bg.paste(out,(0,0),out);ImageDraw.Draw(bg).text((6,258),f'{clip} {i*20/1000:.2f}s',font=font,fill='#f0e4b6');frames.append(bg)
  clips[clip]=dict(durationMs=duration,frames=records)
  if clip=='defeat':
   # The same authored trajectory in reverse supports the existing revival.
   reverse=list(reversed(frames));reverse[0].save(O/'revive-native.gif',save_all=True,append_images=reverse[1:],duration=20)
  palboard=Image.new('RGB',(256*8,280*7))
  for i,im in enumerate(frames):palboard.paste(im,(i%8*256,i//8*280))
  pal=palboard.quantize(colors=256);enc=[im.resize((768,840),Image.Resampling.NEAREST).quantize(palette=pal,dither=Image.Dither.NONE) for im in frames]
  enc[0].save(O/(clip+'-normal.gif'),save_all=True,append_images=enc[1:],duration=20,disposal=2)
  sheet=Image.new('RGB',(1280,840),'#20372a')
  for j,p in enumerate([0,.25,.5,.75,1]):sheet.paste(frames[round(p*count)],(j*256,0))
  sheet.crop((0,0,1280,280)).save(O/(clip+'-keys.png'))
 (D/'animation.json').write_text(json.dumps(dict(schemaVersion=1,frameDurationMs=20,clips=clips,source='approved r7 modular project layers',imageGenerationUsed=False),indent=2)+'\n')
 board=Image.new('RGB',(1280,1120),'#20372a')
 for row,clip in enumerate(clips):
  im=Image.open(O/(clip+'-keys.png'));board.paste(im,(0,row*280))
 board.save(O/'all-keys.png');print('Authored',sum(len(c['frames']) for c in clips.values()),'modular samples',flush=True)
