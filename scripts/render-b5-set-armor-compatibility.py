#!/usr/bin/env python3
"""Render a batch sheet for hair/face/back-weapon wardrobe compatibility."""
import importlib.util, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'Art/Review/P1/b5-set-armors-v1'
MOTION=ROOT/'Art/Integration/P1-modular-eight-way-v1/motion.json'
catalog=REVIEW/'catalog.json'
spec=importlib.util.spec_from_file_location('compose_for_wardrobe_matrix',ROOT/'scripts/compose-character-parts.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
C=module.Compositor(ROOT,catalog,MOTION)
BG='#20372a'

def getfont(size=16):
    p='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
    return ImageFont.truetype(p,size) if Path(p).exists() else ImageFont.load_default()

def main():
    records=[]
    for armor in ['p1-b5-starlight-armor-v1','p1-b5-dragon-armor-v1']:
        folder=REVIEW/'preview'/armor
        page=Image.new('RGB',(4*512,4*554),BG)
        draw=ImageDraw.Draw(page)
        combos=[]
        n=0
        for hair in ['p1-eight-way-hair-chestnut-v1','p1-eight-way-hair-silver-v1']:
            for face in ['p1-eight-way-face-blue-v1','p1-eight-way-face-amber-v1']:
                for weapon in [False,True]:
                    label=f"{'棕发' if 'chestnut' in hair else '银发'} · {'蓝眼' if 'blue' in face else '琥珀眼'} · {'背剑' if weapon else '空背'}"
                    parts=[armor,'p1-eight-way-lower-v1',hair,face]
                    if weapon: parts.append('p1-eight-way-weapon-v1')
                    for j,direction in enumerate(['down','up']):
                        im=C.render('p1-eight-way-base-v1',parts,direction,'idle',0).resize((512,512),Image.Resampling.NEAREST)
                        x=(n%4)*512;y=(n//4)*554
                        page.paste(im,(x,y),im if im.mode=='RGBA' else None)
                        draw.text((x+6,y+512),f'{label} · {direction}',font=getfont(15),fill='#f4e8c7')
                        combos.append({'hair':hair,'face':face,'backWeapon':weapon,'direction':direction,'pose':'idle-00'})
                        n+=1
        out=folder/'compatibility-matrix-2x.png';page.save(out)
        records.append({'armor':armor,'loadouts':8,'fullBodyViews':16,'image':out.relative_to(ROOT).as_posix()})
    report={'compatibleDimensions':{'hair':2,'face':2,'backWeapon':2},'combinations':8,'posesRendered':32,'records':records,'artApproval':None}
    (REVIEW/'compatibility-matrix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
