#!/usr/bin/env python3
"""Build editable technical guides; reference artwork is embedded unchanged."""
import base64
import json
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / 'Art/Standards/P1-Parts-v1'
SVG = 'http://www.w3.org/2000/svg'
INK = 'http://www.inkscape.org/namespaces/inkscape'


def element(parent, tag, **attrs):
    return ET.SubElement(parent, f'{{{SVG}}}{tag}', {k.replace('_', '-'): str(v) for k, v in attrs.items()})


def group(parent, name):
    g = element(parent, 'g', id=name)
    g.set(f'{{{INK}}}groupmode', 'layer')
    g.set(f'{{{INK}}}label', name)
    return g


def label(g, x, y, text, size=3, color='#193a42'):
    el = element(g, 'text', x=x, y=y, font_size=size, fill=color,
                 font_family='sans-serif', stroke='none')
    el.text = text


def write(path, root):
    path.write_text(ET.tostring(root, encoding='unicode')+'\n')


def main():
    ET.register_namespace('', SVG)
    ET.register_namespace('inkscape', INK)
    out = STANDARD/'guides'
    out.mkdir(exist_ok=True)
    profile = json.loads((STANDARD/'profile.json').read_text())
    head = profile['headLayouts']['down']
    root = ET.Element(f'{{{SVG}}}svg', width='768', height='768', viewBox='0 0 96 96')
    guide = group(root, 'GUIDES - proposed, not approved head art')
    element(guide, 'rect', width=96, height=96, fill='#eaf0ed')
    for x in range(0, 97, 8):
        element(guide, 'path', d=f'M{x} 0 V96 M0 {x} H96', stroke='#ccdbd5', stroke_width='.15', fill='none')
    element(guide, 'ellipse', cx=48, cy=48, rx=24, ry=24, fill='none', stroke='#789187', stroke_width='.5')
    for slot, boxes in head['faceRegions'].items():
        for x0,y0,x1,y1 in boxes:
            element(guide, 'rect', x=x0,y=y0,width=x1-x0,height=y1-y0,fill='none',stroke='#518caa',stroke_width='.35')
    for x0,y0,x1,y1 in head['hairFrontKeepClear']:
        element(guide,'rect',x=x0,y=y0,width=x1-x0,height=y1-y0,fill='#d68d66',fill_opacity='.35',stroke='none')
    for name,(x,y) in [('eye.R',(38,56)),('eye.L',(58,56)),('neck',(48,72))]:
        element(guide,'circle',cx=x,cy=y,r='.7',fill='#9b4436')
        label(guide,x+1.5,y-1,name)
    label(guide,3,5,'HEAD LOCAL 96 x 96 / DOWN')
    label(guide,3,10,'PROPOSED GUIDE / NOT A BODY ASSET')
    label(guide,3,87,'Face: features only. Hair: no skin or ears.',2.5)
    label(guide,3,92,'Keep shaded eye windows clear for EVERY face.',2.5)
    group(root,'DRAW - separate hair OR facial feature layers')
    write(out/'head-down.svg',root)
    motion=json.loads((STANDARD/'motion-down.draft.json').read_text())
    for f in motion['frames']:
        root=ET.Element(f'{{{SVG}}}svg',width='768',height='768',viewBox='0 0 256 256')
        refs=group(root,'REFERENCE - approved pose unchanged, not a neutral body')
        path=ROOT/'Art/Review/P1/directions/down/revisions/r1/frames'/f'{f["frame"]:02}.png'
        uri='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
        element(refs,'image',width=256,height=256,href=uri,opacity='.28')
        g=group(root,'GUIDES - calibration required')
        _,_,_,_,tx,ty=f['headToCanvas']
        element(g,'rect',x=tx,y=ty,width=96,height=96,fill='none',stroke='#3495b3',stroke_width='.5')
        for name,pt in [('grip.R',f['sockets']['grip.right']['position']),('grip.L',f['sockets']['grip.left']['position']),*f['joints'].items()]:
            x,y=pt
            element(g,'circle',cx=x,cy=y,r=1.2,fill='#bd6442')
            label(g,x+2,y,name,3)
        label(g,7,12,f'DOWN / {f["clip"]} / {f["frame"]:02} - DRAFT GUIDE',5)
        label(g,7,245,'Neutral full body, shoulders/elbows and draw order are NOT complete.',3.5)
        group(root,'DRAW - new independent part, preserve canvas and anchors')
        write(out/f'down-{f["frame"]:02}.svg',root)
    print('Created 10 editable SVG guide sheets; no production artwork generated.')


if __name__=='__main__':
    main()
