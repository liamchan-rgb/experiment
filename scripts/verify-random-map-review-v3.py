from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageSequence
import json,hashlib,math,runpy
r=Path(__file__).resolve().parents[1];o=r/'Art/Review/Map/random-map-v3';frames=[];dur=[]
with Image.open(o/'walk-normal.gif') as gif:
 for f in ImageSequence.Iterator(gif):frames.append(f.convert('RGB').copy());dur.append(f.info.get('duration'))
 loop=gif.info.get('loop')
assert len(frames)==400 and set(dur)=={20} and loop==0
folder=o/'decoded-contact';folder.mkdir(exist_ok=True);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
for start in range(0,400,40):
 page=Image.new('RGB',(1200,1232),'#182a1f');d=ImageDraw.Draw(page)
 for j,f in enumerate(frames[start:start+40]):
  x=j%5*240;y=j//5*154;page.paste(f.resize((240,135)),(x,y+19));d.text((x+5,y+3),f'{start+j:03d} {(start+j)*20}ms',font=font,fill='white')
 page.save(folder/f'page-{start//40+1:02d}.jpg',quality=92)
for i in [0,25,60,120,180,240,300,360,399]:frames[i].save(o/f'walk-key-{i:03d}.png')
checks=[]
for p in sorted((o/'data').glob('*-geometry.json')):
 data=json.loads(p.with_name(p.name.replace('-geometry','')).read_text());geometry=json.loads(p.read_text());badges={x['nodeID']:x for x in geometry['landmarkBadges']}
 for prop in data['props']:
  if 'nodeID' not in prop:continue
  im=Image.open(r/'Sources/Resources/Assets.xcassets'/f"{prop['asset']}.imageset"/f"{prop['asset']}.png").convert('RGBA')
  top=im.getbbox()[1];anchor=.10 if prop['asset']=='CampTent' else .08
  visibleTop=prop['y']-prop['width']*((1-anchor)*im.height-top)/im.width
  badge=badges[prop['nodeID']];assert abs(visibleTop-badge['y']-14)<1e-6
  assert badge['x']==prop['x']
 checks.append({'map':p.name,'landmarks':len(badges),'badgeToOpaqueTop':14,'verified':True})
review=runpy.run_path(str(r/'scripts/review-random-map-v3.py'),run_name='review')
board=Image.new('RGB',(1290,1620),'#1c3023')
for row,n in enumerate([4,10,30]):
 for col,seed in enumerate([1,31827,98765]):
  prepared=review['prepare'](n,seed);heroes=json.loads((o/'data'/f'map-{n}-{seed}-geometry.json').read_text())['initialHeroes']
  im=review['caption'](review['draw_map'](prepared,heroes),f'{n}节点 / 种子{seed} / 离线')
  im.save(o/f'map-{n}-{seed}-overview.png');im.thumbnail((430,540));board.paste(im,(col*430+(430-im.width)//2,row*540+(540-im.height)//2))
board.save(o/'sizes-seeds.png')
up=r/'Vendor/ClassroomGameCore';manifest=json.loads((up/'UPSTREAM.json').read_text());assert all(hashlib.sha256((up/p).read_bytes()).hexdigest()==sha for p,sha in manifest['sourceSHA256'].items())
result={'swiftTests':182,'quotaSeedMaps':648,'extremeQuotaCases':24,'headingRegressionMaps':36,'productionGeometryCases':78,'opaqueTopBadgeChecks':checks,'originalCoreFilesUnchanged':13,'gif':{'frames':400,'frameMs':20,'loop':0},'artApproval':None,'appSimulatorDeviceRun':False}
(o/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('400 GIF frames;10 contact sheets;9 layout variants; all badge/opaque-top alignments exact;13 upstream files unchanged')
