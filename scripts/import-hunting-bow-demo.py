from pathlib import Path
import json,math,hashlib,importlib.util,shutil,base64,io
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];A=R/'Sources/Resources/Assets.xcassets';D=R/'Art/Integration/Equipment-hunting-bow-v1';D.mkdir(parents=True,exist_ok=True)
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def asset(n,im):
 d=A/(n+'.imageset');d.mkdir(exist_ok=True);im.save(d/(n+'.png'));write(d/'Contents.json',{'images':[{'filename':n+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}})
icon=Image.open(R/'Art/Parts/P1-v1/hunting-bow-v1/source/item_hunting_bow.png').convert('RGBA');asset('MeadowPartyHuntingBow',icon)
# Pixel production drawing: curved wooden limbs, brass ferrules, leather grip.
# String/arrow are separately driven by the shared bow rig; no baked stretched string.
wood=Image.new('RGBA',(256,256));draw=ImageDraw.Draw(wood);cx,cy=145.6,163.7
points=[]
for i in range(73):
 y=-36+i; x=-10+10*math.cos(y/36*math.pi/2)
 points.append((round(cx+x),round(cy+y)))
draw.line(points,fill='#33271c',width=6,joint='curve');draw.line([(x,y) for x,y in points],fill='#84502a',width=4,joint='curve');draw.line([(x-1,y) for x,y in points],fill='#c68d49',width=2,joint='curve')
for yy in [-32,-25,25,32]:
 x=round(cx-10+10*math.cos(yy/36*math.pi/2));y=round(cy+yy);draw.line((x-2,y,x+2,y),fill='#f0c56b',width=2)
draw.line((round(cx),round(cy-5),round(cx),round(cy+5)),fill='#49372a',width=5)
for y in range(round(cy-4),round(cy+5),3):draw.line((round(cx-2),y,round(cx+2),y+1),fill='#a47b4c',width=1)
asset('MeadowBattleHuntingBow',wood)
# Dedicated semantic body copy retires only the old rear-arm skin; original source is untouched.
for source,target in [('MeadowBattleHeroBodyCore','MeadowBattleBowBodyCore'),('MeadowBattleHeroWardrobeCore','MeadowBattleBowWardrobeCore')]:
 im=Image.open(A/(source+'.imageset')/(source+'.png')).convert('RGBA');ImageDraw.Draw(im).polygon([(98,150),(112,150),(115,156),(114,161),(111,167),(108,175),(98,175)],fill=(0,0,0,0));asset(target,im)
im=Image.open(A/'MeadowBattleHeroLegFarThighWardrobe.imageset/MeadowBattleHeroLegFarThighWardrobe.png').convert('RGBA')
ImageDraw.Draw(im).rectangle((95,150,112,173),fill=(0,0,0,0));asset('MeadowBattleBowLegFarThighWardrobe',im)
# Back-carry uses the existing actual neck/shoulder registration and original draw order.
S=R/'Art/Integration/P1-modular-eight-way-v1';motion=json.loads((S/'motion.json').read_text());part=R/'Art/Parts/P1-v1/hunting-bow-v1';bindings=[];editable=[]
# A bow in its local carrying plane, from the same wooden limb drawing.
local=wood.crop((126,121,153,205)); dr=ImageDraw.Draw(local);dr.line((10,7,10,79),fill='#e1c18a',width=1)
for f in motion['frames']:
 neck=f['joints']['neck'];l=f['joints']['shoulderLeft'];r=f['joints']['shoulderRight'];fx,fy=f['facing'];dx=(r[0]-l[0])/30*13
 # View-dependent projection; fixed upper-left lighting stays on the source colour bands.
 cy=neck[1]+22;cx=(l[0]+r[0])/2-fx*8
 vx=-dx/36;vy=1;hx=(0.36+0.64*abs(fy));hy=0
 # Local pivot registered to the grip of the native source, not alpha bounds.
 pivot=(145.6-126,163.7-121)
 aa,bb,cc,dd=hx,hy,vx,vy;tx=cx-aa*pivot[0]-cc*pivot[1];ty=cy-bb*pivot[0]-dd*pivot[1];det=aa*dd-bb*cc
 inv=(dd/det,-cc/det,(cc*ty-dd*tx)/det,-bb/det,aa/det,(bb*tx-aa*ty)/det)
 im=local.transform((256,256),Image.Transform.AFFINE,inv,Image.Resampling.NEAREST)
 rel=f"png/{f['direction']}/{f['clip']}/{f['frame']:02}/weapon.back.png";p=part/rel;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
 svg=f"editable/{f['direction']}-{f['clip']}-{f['frame']:02}.svg";q=part/svg;q.parent.mkdir(exist_ok=True);buf=io.BytesIO();wood.save(buf,format='PNG');data=base64.b64encode(buf.getvalue()).decode()
 q.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="256" height="256" viewBox="0 0 256 256"><g id="registered-weapon-plane"><image id="weapon-back" width="256" height="256" xlink:href="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"/></g></svg>');editable.append(svg)
 bindings.append({k:f[k] for k in ['direction','clip','frame']}|{'layers':{'weapon.back':rel}})
base=json.loads((R/'Art/Parts/P1-v1/eight-way-v1/weapon/asset.json').read_text());base.update(id='p1-hunting-bow-v1',sourceFiles=['authoring.json','source/item_hunting_bow.png']+editable,bindings=bindings,carryProfile='back-bow')
write(part/'asset.json',base);write(part/'authoring.json',{'sourceIcon':'classroom-boardgame item_hunting_bow.png','method':'native wooden curve and separate string; carried plane projected from actual neck/shoulders per pose','pivotPx':[145.6,163.7],'newArtApproval':None})
cat=json.loads((S/'catalog.json').read_text());cat['assets'].append({'id':'p1-hunting-bow-v1','manifest':str((part/'asset.json').relative_to(R))});write(D/'catalog.json',cat)
spec=importlib.util.spec_from_file_location('bow_compositor',R/'scripts/compose-character-parts.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);C=m.Compositor(R,D/'catalog.json',S/'motion.json');config=json.loads((R/'Art/Integration/P1-modular-demo-v1/selection.json').read_text());rigfile=R/'Sources/Resources/hero-gait.json';rig=json.loads(rigfile.read_text());records=[]
dirs=['down','left','up','right','down-right','down-left','up-left','up-right'];keys=[('idle',0)]+[('walk',i) for i in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]
for p in config['loadouts']:
 names=['P1'+p['id'].title()+'BowDirections','P1'+p['id'].title()+'BowDiagonals']
 for group,name in enumerate(names):
  atlas=Image.new('RGBA',(13*256,4*256));selected=[a for a in p['assets'] if a!='p1-eight-way-weapon-v1']+['p1-hunting-bow-v1']
  for row,d in enumerate(dirs[group*4:group*4+4]):
   for col,(clip,n) in enumerate(keys):
    im=C.render(config['base'],selected,d,clip,n);atlas.paste(im,(col*256,row*256));records.append({'appearance':p['id'],'direction':d,'clip':clip,'frame':n,'itemID':'huntingBow','atlas':name,'row':row,'column':col,'RGBA_SHA256':hashlib.sha256(im.tobytes()).hexdigest()})
  asset(name,atlas)
 for x in rig['modularP1']['loadouts']:
  if x['id']==p['id']:x['weaponAtlasNames']['huntingBow']=names
rig['equipmentVisuals']['huntingBow']={'itemID':'huntingBow','walkingAsset':'p1-hunting-bow-v1','battleAsset':'MeadowBattleHuntingBow','iconAsset':'MeadowPartyHuntingBow'}
rigfile.write_text(json.dumps(rig,separators=(',',':'))+'\n');write(D/'walking-bindings.json',records);write(D/'binding.json',{'itemID':'huntingBow','walkingAsset':'p1-hunting-bow-v1','bindingCountPerAppearance':104,'appearances':2,'battleAsset':'MeadowBattleHuntingBow','battleRig':'BowRig.swift','originalIconSHA256':hashlib.sha256((R/'Art/Parts/P1-v1/hunting-bow-v1/source/item_hunting_bow.png').read_bytes()).hexdigest(),'newArtApproval':None})
print('Generated208 original-body bow carry cells and dedicated bow geometry source')
