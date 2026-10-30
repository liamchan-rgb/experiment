#!/usr/bin/env python3
"""Import approved modular layers; never bake a full character into runtime frames."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math
R=Path(__file__).resolve().parents[1];D=R/'Art/Parts/P1-Battle/hunting-bow-full-cycle-r7-v1';A=R/'Sources/Resources/Assets.xcassets'
O=R/'Art/Integration/Battle-reviewed-bow-r7-v1';O.mkdir(parents=True,exist_ok=True)
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,separators=(',',':'))+'\n')
def asset(name,im):
 p=A/(name+'.imageset');p.mkdir(exist_ok=True);im.save(p/(name+'.png'));dump(p/'Contents.json',{'images':[{'filename':name+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}})
def read_asset(name):
 p=A/(name+'.imageset');d=json.loads((p/'Contents.json').read_text());return Image.open(p/next(i['filename'] for i in d['images'] if i.get('filename'))).convert('RGBA')
for source,target in [('torso.png','Torso'),('body-core-clean.png','BodyCore'),('grip-hand.png','GripHand'),('drawing-hand-held.png','DrawingHandHeld'),('drawing-hand-open.png','DrawingHandOpen'),('drawing-hand-relaxed.png','DrawingHandRelaxed')]:asset('MeadowBattleBowReviewed'+target,Image.open(D/source).convert('RGBA'))
for source,target in [('MeadowBattleHeroLegNearThighWardrobe','LegNearThighWardrobe'),('MeadowBattleBowLegFarThighWardrobe','LegFarThighWardrobe')]:
 im=read_asset(source);ImageDraw.Draw(im).rectangle((109,159,145,169),fill=(0,0,0,0))
 for y in range(170,175):
  for x in range(109,146):
   c=im.getpixel((x,y))
   if c[3] and max(c[:3])-min(c[:3])>18:im.putpixel((x,y),(0,0,0,0))
 asset('MeadowBattleBowReviewed'+target,im)
records=json.loads((D/'animation.json').read_text())['frames'];frames=[];tiles=[];unique={};images=[]
def register(layer):
 key=hashlib.sha256(layer.tobytes()).hexdigest()
 if key not in unique:
  index=len(tiles);box=layer.getbbox();assert box and box[2]-box[0]<=96 and box[3]-box[1]<=96
  unique[key]=index;tiles.append({'x':index%8*96,'y':index//8*64,'width':box[2]-box[0],'height':box[3]-box[1],'canvasX':box[0],'canvasY':box[1]});images.append(layer.crop(box))
 return unique[key]
for f in records:
 p=json.loads((D/f['pose']).read_text());native={}
 for group,source in [('nearSleeveConnected',D/f['nearSleeve']),('nearUpperArm',D/f['pose'].replace('pose.json','nearUpperArm.png')),('farArm',D/f['pose'].replace('pose.json','farArm.png'))]:native[group]=register(Image.open(source).convert('RGBA'))
 for group,filename,origin in [('nearHand','drawing-hand-'+f['handVariant']+'.png',(-14,-6)),('farHand','grip-hand.png',(-8,-6))]:
  part=p['parts'][group];x=round(part['pivot']['x']+part['offset']['x']);y=round(part['pivot']['y']+part['offset']['y'])
  layer=Image.new('RGBA',(256,256));layer.alpha_composite(Image.open(D/filename).convert('RGBA'),(x+origin[0],y+origin[1]));layer=layer.rotate(-math.degrees(part['rotation']),resample=Image.Resampling.NEAREST,center=(x,y));native[group]=register(layer)
 # The torso is a shared native PNG. Its hundreds of pixel-run polygons
 # must not be repeated in every frame or repainted each display tick.
 p['surfaces']=[s for s in p['surfaces'] if s['group'] in ['nearUpperArm','farArm']]
 p.update(nativeFrame=f['frame'],sleeveTile=native['nearSleeveConnected'],nativeTiles=native,drawingHandVariant=f['handVariant']);frames.append(p)
# Additional bow-specific states are canvas-posed independent project parts.
C=R/'Art/Parts/P1-Battle/hunting-bow-actions-r7-v1'
actions=json.loads((C/'animation.json').read_text());clips={}
for clip,desc in actions['clips'].items():
 indices=[]
 for record in desc['frames']:
  folder=(C/record['pose']).parent;p=json.loads((folder/'pose.json').read_text());native={}
  for file in sorted(folder.glob('*.png')):
   if file.stem=='assembled':continue
   native[file.stem]=register(Image.open(file).convert('RGBA'))
  index=len(frames);p.update(nativeFrame=index,sleeveTile=native['nearSleeveConnected'],nativeTiles=native,drawingHandVariant='open' if clip=='defeat' and record['progress']>.6 else 'relaxed')
  frames.append(p);indices.append(index)
 clips[clip]=indices
# Tight shelf packing keeps the decoded atlas small even with independent
# head/garment/limb tiles. Tile IDs are stable; no full-character frames imported.
width=768;x=y=rowh=0
for i in sorted(range(len(tiles)),key=lambda j:-tiles[j]['height']):
 tile=tiles[i]
 if x+tile['width']>width:y+=rowh;x=0;rowh=0
 tile['x']=x;tile['y']=y;x+=tile['width'];rowh=max(rowh,tile['height'])
atlas=Image.new('RGBA',(width,y+rowh))
for tile,im in zip(tiles,images):atlas.paste(im,(tile['x'],tile['y']))
asset('MeadowBattleBowReviewedSleeves',atlas)
library={'schemaVersion':1,'frameDurationMs':20,'releaseArtTime':1.34,'recoveredArtTime':1.68,'restArtTime':2.24,'tiles':tiles,'frames':frames,'clips':clips}
resource=R/'Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources/reviewed-bow-r7.json';dump(resource,library)
dump(O/'import.json',{'approvedCommit':'737ba88a861a85019672e49a3fb2fd2ec849999e','approval':str((R/'Art/Review/Battle/hunting-bow-full-cycle-r7-v1/approval.json').relative_to(R)),'frames':len(frames),'approvedShootingFrames':143,'newActionSamples':len(frames)-143,'newActions':list(clips),'newActionsUserApproved':False,'uniqueNativePartTiles':len(tiles),'atlasSize':list(atlas.size),'independentLayers':True,'fullCharacterFramesImported':False,'resourceSHA256':hashlib.sha256(resource.read_bytes()).hexdigest()})
# Atlas reconstruction is exact, with no palette changes or resampling.
for f,p in zip(records,frames):
 tile=tiles[p['sleeveTile']];im=Image.new('RGBA',(256,256));im.paste(atlas.crop((tile['x'],tile['y'],tile['x']+tile['width'],tile['y']+tile['height'])),(tile['canvasX'],tile['canvasY']))
 assert im.tobytes()==Image.open(D/f['nearSleeve']).convert('RGBA').tobytes()
print(json.dumps({'frames':len(frames),'uniqueSleeveTiles':len(tiles),'atlas':atlas.size,'libraryBytes':resource.stat().st_size}))

for clip,desc in actions['clips'].items():
 for record,index in zip(desc['frames'],clips[clip]):
  folder=(C/record['pose']).parent
  for group,tid in frames[index]['nativeTiles'].items():
   tile=tiles[tid];im=Image.new('RGBA',(256,256));im.paste(atlas.crop((tile['x'],tile['y'],tile['x']+tile['width'],tile['y']+tile['height'])),(tile['canvasX'],tile['canvasY']))
   assert im.tobytes()==Image.open(folder/(group+'.png')).convert('RGBA').tobytes(),(clip,index,group)
print('All additional independent native tiles reconstruct exactly.')
