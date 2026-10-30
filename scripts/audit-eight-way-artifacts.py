#!/usr/bin/env python3
"""Check preservation and decode the exact normal-rate delivery GIFs for review."""
from pathlib import Path
import hashlib,json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'Art/Review/P1/modular-eight-way-v1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    original=json.loads((D/'preserved-files.json').read_text())
    assert all(digest(ROOT/p)==h for p,h in original.items()),'existing art changed'
    out=D/'decoded';out.mkdir(exist_ok=True)
    records=[]
    for name,count,timing in [(s+'-eight-way-walk-120ms.gif',8,[120]*8) for s in ['forester','wayfarer']]+[(s+'-specified-start-stop-120ms.gif',22,[480]+[120]*20+[480]) for s in ['forester','wayfarer']]+[('turn-comparison-120ms.gif',64,[120]*64)]:
        p=D/name;g=Image.open(p);assert g.n_frames==count and g.info['loop']==0
        durations=[]
        frames=[]
        for n in range(count):g.seek(n);durations.append(g.info['duration']);frames.append(g.convert('RGB'))
        assert durations==timing,(name,durations)
        records.append({'path':str(p.relative_to(ROOT)),'frames':count,'durationsMs':durations,'sha256':digest(p)})
        if 'eight-way-walk' in name:
            for page in range(4):
                canvas=Image.new('RGB',(1024,1024))
                for n in range(2):canvas.paste(frames[page*2+n].resize((1024,512),Image.Resampling.NEAREST),(0,n*512))
                canvas.save(out/f'{name.split("-")[0]}-walk-{page}.png')
        elif name.startswith('turn-'):
            for page in range(4):
                canvas=Image.new('RGB',(2048,1024))
                for n in range(16):canvas.paste(frames[page*16+n].resize((512,256),Image.Resampling.NEAREST),(n%4*512,n//4*256))
                canvas.save(out/f'turn-{page}.png')
    idle=Image.new('RGB',(2048,2048))
    for j,s in enumerate(['forester','wayfarer']):idle.paste(Image.open(D/f'{s}-idle-2x.png').convert('RGB'),(0,j*1024))
    idle.save(D/'outfits-idle-2x.png')
    report={'preservedExistingFiles':len(original),'gifChecks':records,
            'mainHumanReview':'root viewed both main loadouts all8directions13poses at1x/2x; actual decoded walk8frames each and turn64frames, static viewer only',
            'continuousPlaybackClaimed':False,'deviceExecuted':False,'artApproval':None}
    (D/'artifact-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'preservedExistingFiles':len(original),'normalGifs':len(records)}))
if __name__=='__main__':main()
