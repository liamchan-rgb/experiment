#!/usr/bin/env python3
"""Bake data-selected modular P1 presets into the demo's shared sprite/shadow atlases.

No painting, content fitting, body switching or runtime appearance-ID branches.
"""
import hashlib,importlib.util,json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Art/Integration/P1-modular-eight-way-v1'
RECORD=ROOT/'Art/Integration/P1-modular-demo-v1'
ASSETS=ROOT/'Sources/Resources/Assets.xcassets'
DIRECTIONS=['down','left','up','right','down-right','down-left','up-left','up-right']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def load_module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 cfg=json.loads((RECORD/'selection.json').read_text())
 assert cfg['userAuthorization']=='开始下一项工作'
 compositor=load_module('modular_demo_compositor','compose-character-parts.py').Compositor(ROOT,SOURCE/'catalog.json',SOURCE/'motion.json')
 body=cfg['base'];info=json.loads((SOURCE/'authoring.json').read_text());outputs={};cells=[];loadouts=[]
 source_keys=[('idle',0)]+[('walk',n) for n in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]
 for preset in cfg['loadouts']:
  names=preset['atlasNames'];loadouts.append({k:preset[k] for k in ['id','title','atlasNames']})
  rendered={}
  for d in DIRECTIONS:
   for clip,n in source_keys:rendered[d,clip,n]=compositor.render(body,preset['assets'],d,clip,n)
  for group,name in enumerate(names):
   atlas=Image.new('RGBA',(13*256,4*256))
   for row,d in enumerate(DIRECTIONS[group*4:group*4+4]):
    for column,(clip,n) in enumerate(source_keys):atlas.paste(rendered[d,clip,n],(column*256,row*256))
   folder=ASSETS/(name+'.imageset');folder.mkdir(exist_ok=True)
   p=folder/(name+'.png');atlas.save(p)
   write(folder/'Contents.json',{'images':[{'filename':name+'.png','idiom':'universal'}],'info':{'author':'xcode','version':1}})
   decoded=Image.open(p).convert('RGBA')
   for row,d in enumerate(DIRECTIONS[group*4:group*4+4]):
    for column,(clip,n) in enumerate(source_keys):
     cell=decoded.crop((column*256,row*256,(column+1)*256,(row+1)*256))
     assert cell.tobytes()==rendered[d,clip,n].tobytes()
     cells.append({'loadout':preset['id'],'direction':d,'clip':clip,'frame':n,'atlas':name,'row':row,'column':column,'rgbaSHA256':hashlib.sha256(cell.tobytes()).hexdigest()})
   outputs[str(p.relative_to(ROOT))]=sha(p)
 rig=json.loads((RECORD/'source/hero-gait.json').read_text())
 # Existing P2/P3 data remain exact. Shared distance sampling is still24ticks.
 feet=[]
 for d in DIRECTIONS:
  row=[]
  for tick in range(29):
   column=0 if tick==0 else 1+(tick-1)*8//24 if tick<=24 else 9+tick-25
   clip,n=source_keys[column];f=compositor.frames[d,clip,n]
   # Authored 2D sole markers, with no invented physical lift. The native caster
   # and foreground consume the same registered pose and source alpha.
   row.append({'feet':[[f['soleMarkers'][side][0]/256,f['soleMarkers'][side][1]/256,0] for side in ['left','right']]})
  feet.append(row)
 rig.update(authoredFrames=[8,24,24],reviewFrameMs=120)
 rig['heroes'][0]=feet
 rig['modularP1']={'rasterColumns':13,'walkPhaseCount':8,'frameMs':120,'finishSpeed':25,
                   'startFrames':[25,26],'stopFrames':[27,28],
                   'directions':[{'entryPhase':info['directions'][d]['entryPhase'],'exitPhase':info['directions'][d]['exitPhase']} for d in DIRECTIONS],
                   'loadouts':loadouts,'base':body,'sourceMotionSHA256':sha(SOURCE/'motion.json')}
 p=ROOT/'Sources/Resources/hero-gait.json';p.write_text(json.dumps(rig,separators=(',',':'))+'\n');outputs[str(p.relative_to(ROOT))]=sha(p)
 write(RECORD/'atlas-cells.json',cells)
 write(RECORD/'integration.json',{'date':'2026-10-25','status':'imported-for-offline-review','artApproval':None,'source':'Art/Integration/P1-modular-eight-way-v1','body':body,'loadouts':loadouts,'actualComposedCells':len(cells),'rasterColumns':13,'distanceClockTicks':24,'transitionVirtualFrames':[25,26,27,28],'directionOrder':DIRECTIONS,'pixelChangesDuringImport':0,'contentFit':False,'originalAtlasBackup':'source/','outputs':outputs,'deviceExecuted':False})
 print(json.dumps({'loadouts':len(loadouts),'actualComposedCells':len(cells),'pixelChangesDuringImport':0}))
if __name__=='__main__':main()
