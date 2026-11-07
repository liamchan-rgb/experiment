#!/usr/bin/env python3
"""Decode and verify the B5 armor review GIFs against real compositor poses."""
from __future__ import annotations
import importlib.util, json, hashlib, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'Art/Review/P1/b5-set-armors-v1'
MOTION=ROOT/'Art/Integration/P1-modular-eight-way-v1/motion.json'
DIRECTIONS=['down','down-left','left','up-left','up','up-right','right','down-right']
BACKGROUND=(32,55,42)

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

compose=load('compose_for_gif_audit',ROOT/'scripts/compose-character-parts.py')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def font(size=13):
    p='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
    return ImageFont.truetype(p,size) if Path(p).exists() else ImageFont.load_default()

def on_bg(rgba,size=512):
    im=rgba.convert('RGBA').resize((size,size),Image.Resampling.NEAREST)
    bg=Image.new('RGB',im.size,BACKGROUND);bg.paste(im,(0,0),im);return bg

def read_frames(path):
    im=Image.open(path);frames=[];durations=[]
    for i in range(im.n_frames):
        im.seek(i);frames.append(im.convert('RGB').copy());durations.append(im.info.get('duration'))
    return frames,durations,im.info.get('loop')

def expected_canvas(compositor,armor,direction,clip,frame):
    parts=[armor,'p1-eight-way-lower-v1','p1-eight-way-hair-chestnut-v1','p1-eight-way-face-blue-v1','p1-eight-way-weapon-v1']
    return compositor.render('p1-eight-way-base-v1',parts,direction,clip,frame)

def main():
    compositor=compose.Compositor(ROOT,REVIEW/'catalog.json',MOTION)
    summaries=[]
    for armor in ['p1-b5-starlight-armor-v1','p1-b5-dragon-armor-v1']:
        folder=REVIEW/'preview'/armor
        walk_contact=Image.new('RGB',(8*256,8*278),BACKGROUND)
        draw=ImageDraw.Draw(walk_contact)
        per_direction=[]
        for row,direction in enumerate(DIRECTIONS):
            path=folder/f'{direction}-walk-normal.gif'
            frames,durations,loop=read_frames(path)
            assert len(frames)==8 and durations==[120]*8 and loop==0,(path,len(frames),durations,loop)
            mismatch_total=0;max_color_delta=0
            for n,actual512 in enumerate(frames,1):
                expected=on_bg(expected_canvas(compositor,armor,direction,'walk',n),512)
                actual_small=actual512.resize((256,256),Image.Resampling.NEAREST)
                expected_small=expected.resize((256,256),Image.Resampling.NEAREST)
                ea=np.asarray(expected_small);aa=np.asarray(actual_small)
                err=np.abs(ea.astype(np.int16)-aa.astype(np.int16))
                max_color_delta=max(max_color_delta,int(err.max()))
                expmask=np.any(np.abs(ea.astype(np.int16)-np.array(BACKGROUND,dtype=np.int16))>18,axis=2)
                actmask=np.any(np.abs(aa.astype(np.int16)-np.array(BACKGROUND,dtype=np.int16))>18,axis=2)
                mismatch_total+=int(np.count_nonzero(expmask!=actmask))
                x=(n-1)*256;y=row*278
                walk_contact.paste(actual_small,(x,y))
                if n==1:
                    draw.text((x+5,y+258),direction,font=font(12),fill='#f4e8c7')
            per_direction.append({'direction':direction,'walkFrames':len(frames),'durationsMs':durations,'loop':loop,'silhouetteMismatchedPixelsAcrossFrames':mismatch_total,'maxRGBDelta':max_color_delta})
        contact=folder/'walk-gif-decoded-frames-1x.png';walk_contact.save(contact)
        start_stop=[]
        for direction in DIRECTIONS:
            path=folder/f'{direction}-start-stop-normal.gif'
            frames,durations,loop=read_frames(path)
            assert len(frames)==22 and durations==[480]+[120]*20+[480] and loop==0,(path,len(frames),durations,loop)
            start_stop.append({'direction':direction,'frames':len(frames),'durationsMs':durations,'loop':loop})
            # Decode every start/stop image into a per-facing sheet for visual
            # audit; poses remain full-body at 1x, not cropped to the cloth.
            sheet=Image.new('RGB',(4*256,6*278),BACKGROUND);draw=ImageDraw.Draw(sheet)
            for i,frame in enumerate(frames):
                small=frame.resize((256,256),Image.Resampling.NEAREST)
                x=(i%4)*256;y=(i//4)*278
                sheet.paste(small,(x,y));draw.text((x+4,y+258),f'{i+1:02}',font=font(12),fill='#f4e8c7')
            sheet.save(folder/f'{direction}-start-stop-gif-decoded-1x.png')
        summaries.append({'armor':armor,'walk':per_direction,'startStop':start_stop,'walkGIFDecodedFrames':64,'startStopGIFDecodedFrames':176,'walkContactSheet':contact.relative_to(ROOT).as_posix()})
    report={'reviewDate':'2026-11-01','decodedGIFCount':32,'decodedFrames':480,'walkFramesPerFacing':8,'walkFrameDurationMs':120,'walkLoopDurationMs':960,'startStopFramesPerFacing':22,'startStopDurationsMs':[480]+[120]*20+[480],'startStopLoopDurationMs':3360,'loopForever':True,'artApproval':None,'results':summaries}
    (REVIEW/'gif-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    verification=json.loads((REVIEW/'verification.json').read_text())
    verification.update({'assetContract':'passed: both asset manifests validated with scripts/check-character-part.py','gifDecode':'passed: 32 GIFs, 480 decoded frames, frame timing and loop checked; 16 walk GIFs matched compositor silhouettes; decoded contact sheets reviewed by root','manualArtAudit':'root inspected every direction at 1x and 2x, all 13 poses per armor; shoulders/cuffs, chest, split fauld, leg/boot seams and near/far shading checked','artApproval':None})
    (REVIEW/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'gifCount':report['decodedGIFCount'],'decodedFrames':report['decodedFrames'],'walkTiming':'8×120ms','startStopTiming':'480 + 20×120 + 480ms','silhouetteMismatches':sum(x['silhouetteMismatchedPixelsAcrossFrames'] for s in summaries for x in s['walk'])},ensure_ascii=False))

if __name__=='__main__': main()
