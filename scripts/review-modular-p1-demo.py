#!/usr/bin/env python3
"""Review actual demo atlas cells sampled by the production Swift controller trace."""
from pathlib import Path
import hashlib,importlib.util,json
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
I=ROOT/'Art/Integration/P1-modular-demo-v1';D=ROOT/'Art/Review/P1/modular-demo-v1'
ASSETS=ROOT/'Sources/Resources/Assets.xcassets'
NAMES=['down','left','up','right','down-right','down-left','up-left','up-right']
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 preview=mod('demo_preview','export-neutral-direction.py')
 trace=json.loads((D/'controller-trace.json').read_text());assert trace['status']=='pass'
 cfg=json.loads((I/'selection.json').read_text());presets=cfg['loadouts'];cache={}
 def cell(preset,sample):
  facing=sample['facing'];name=preset['atlasNames'][facing//4]
  if name not in cache:cache[name]=Image.open(ASSETS/(name+'.imageset')/(name+'.png')).convert('RGBA')
  col=sample['column'];row=facing%4
  return cache[name].crop((col*256,row*256,(col+1)*256,(row+1)*256))
 def pair(sample,caption=''):
  out=Image.new('RGBA',(512,256));draw=ImageDraw.Draw(out)
  for j,preset in enumerate(presets):
   out.alpha_composite(cell(preset,sample),(j*256,0))
   draw.text((j*256+5,5),preset['id']+' / '+NAMES[sample['facing']]+' '+caption,fill='white')
  return out
 all_frames=[];durations=[]
 for path in trace['directions']:
  frames=[pair(sample) for sample in path['specifiedStartStop']]
  assert len(frames)==22 and len({x['facing'] for x in path['specifiedStartStop']})==1
  all_frames+=frames;durations += [480]+[120]*20+[480]
  # Thirteen distinct authored poses, in actual controller order, full bodies.
  order=[0,1,2]+list(range(3,11))+[19,20]
  out=Image.new('RGBA',(2048,1024));draw=ImageDraw.Draw(out)
  for j,idx in enumerate(order):
   out.alpha_composite(frames[idx],(j%4*512,j//4*256))
   draw.text((j%4*512+5,j//4*256+18),path['specifiedStartStop'][idx]['state'],fill='white')
  for scale in [1,2]:preview.flatten(out,scale).save(D/f"demo-{NAMES[path['direction']]}-all13-{scale}x.png")
 preview.gif(all_frames,D/'demo-eight-way-start-stop-120ms.gif',durations)
 turn=[pair(sample) for sample in trace['phasePreservingTurns']]
 preview.gif(turn,D/'demo-turn-120ms.gif')
 road=[pair(sample,f"t={sample['time']:.2f}") for sample in trace['mapTrace']]
 preview.gif(road,D/'demo-road-controller-120ms.gif')
 # Runtime still view in clockwise order.
 idle=Image.new('RGBA',(1024,1024));draw=ImageDraw.Draw(idle)
 order=[0,5,1,6,2,7,3,4]
 for style,preset in enumerate(presets):
  for j,d in enumerate(order):
   idle.alpha_composite(cell(preset,{'facing':d,'column':0}),(j%4*256,style*512+j//4*256))
   draw.text((j%4*256+5,style*512+j//4*256+5),preset['id']+' / '+NAMES[d],fill='white')
 for scale in [1,2]:preview.flatten(idle,scale).save(D/f'demo-idle-{scale}x.png')
 # Compare actual decoded import cell hashes, rather than a source-only preview.
 expected=json.loads((I/'atlas-cells.json').read_text());checked=0
 for x in expected:
  im=cell(next(p for p in presets if p['id']==x['loadout']),{'facing':NAMES.index(x['direction']),'column':x['column']})
  assert hashlib.sha256(im.tobytes()).hexdigest()==x['rgbaSHA256'];checked+=1
 old=json.loads((I/'source/hero-gait.json').read_text());new=json.loads((ROOT/'Sources/Resources/hero-gait.json').read_text())
 assert old['heroes'][1:]==new['heroes'][1:]
 preserved=json.loads((D/'preserved-art.json').read_text());assert all(sha(ROOT/p)==h for p,h in preserved.items())
 gif_records=[];decoded=D/'decoded';decoded.mkdir(exist_ok=True)
 for name,count in [('demo-eight-way-start-stop-120ms.gif',176),('demo-turn-120ms.gif',64),('demo-road-controller-120ms.gif',100)]:
  g=Image.open(D/name);assert g.n_frames==count and g.info['loop']==0
  frames=[];timing=[]
  for n in range(count):g.seek(n);frames.append(g.convert('RGB'));timing.append(g.info['duration'])
  assert timing==durations if count==176 else timing==[120]*count
  if count==176:
   for d in range(8):
    page=Image.new('RGB',(2048,1536))
    for n in range(22):page.paste(frames[d*22+n].resize((512,256),Image.Resampling.NEAREST),(n%4*512,n//4*256))
    page.save(decoded/f'start-stop-{d}.png')
  else:
   for page in range((count+15)//16):
    out=Image.new('RGB',(2048,1024))
    for n in range(16):
     at=page*16+n
     if at<count:out.paste(frames[at].resize((512,256),Image.Resampling.NEAREST),(n%4*512,n//4*256))
    out.save(decoded/f'{"turn" if count==64 else "road"}-{page}.png')
  gif_records.append({'file':name,'frames':count,'durationsMs':timing,'sha256':sha(D/name)})
 write(D/'validation.json',{'status':'technical-pass-main-art-review-pending','artApproval':None,'authorAndReviewer':'root','subagentsUsed':False,'actualImportedCells':checked,'pixelChangesDuringImport':0,'preservedExistingArt':len(preserved),'legacyP2P3FootDataUnchanged':True,'controllerTrace':{'file':'controller-trace.json','sha256':sha(D/'controller-trace.json'),'specifiedPaths':trace['specifiedPaths'],'stopCommandPhases':trace['stopCommandPhases'],'cadenceCases':trace['renderCadenceCases'],'realRoadSimulationSteps':trace['mapSimulationSteps']},'gifs':gif_records,'deviceExecuted':False,'simulatorExecuted':False,'continuousPlaybackClaimed':False})
 print(json.dumps({'actualImportedCells':checked,'preservedExistingArt':len(preserved),'gifCounts':[r['frames'] for r in gif_records]}))
if __name__=='__main__':main()
