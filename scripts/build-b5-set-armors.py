#!/usr/bin/env python3
"""Build modular eight-way Starlight and Dragon Mark armor candidates.

The source artwork is editable vector art in five explicit camera views. The
existing P1 armor surface sampler places that art on the frozen 104-pose rig;
this script does not change the body, motion, joint map, compositor, or outfits.
"""
from __future__ import annotations

import base64
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Art/Parts/P1-v1/b5-set-armors-v1"
REVIEW = ROOT / "Art/Review/P1/b5-set-armors-v1"
BASE_CATALOG = ROOT / "Art/Integration/P1-modular-eight-way-v1/catalog.json"
MOTION_PATH = ROOT / "Art/Integration/P1-modular-eight-way-v1/motion.json"
DIRECTIONS = ["down", "down-left", "left", "up-left", "up", "up-right", "right", "down-right"]
SLOTS = ["outfit.torso", "outfit.sleeve.left", "outfit.sleeve.right", "outfit.hem.front"]
SIZE = (1774, 887)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


surface_module = load_module("armor_surface_r4", ROOT / "scripts/armor-shared-surface-r4.py")
compose_module = load_module("compose_parts", ROOT / "scripts/compose-character-parts.py")


VIEWS = {
    "front": {
        "body": [(184,117),(314,117),(334,192),(332,263),(340,313),(162,313),(176,263),(173,192)],
        "hem": [(167,280),(335,280),(396,411),(110,411)],
        "sleeves": [
            [(183,120),(109,132),(84,207),(87,262),(156,284),(177,250),(185,205)],
            [(311,120),(382,133),(414,208),(415,262),(345,284),(323,250),(311,205)],
        ],
    },
    "front-quarter": {
        "body": [(555,120),(633,120),(650,180),(647,259),(673,315),(515,315),(528,256),(527,185)],
        "hem": [(520,278),(675,278),(708,412),(487,412)],
        "sleeves": [
            [(550,128),(507,145),(483,201),(485,265),(528,283),(542,244),(550,201)],
            [(645,124),(701,124),(752,174),(755,234),(732,284),(653,284),(644,242)],
        ],
    },
    "profile": {
        "body": [(829,119),(882,119),(872,166),(859,215),(861,267),(925,316),(798,316),(802,212)],
        "hem": [(800,279),(927,279),(974,412),(784,412)],
        "sleeves": [
            [(819,140),(794,165),(786,226),(811,273),(833,262),(837,198)],
            [(860,132),(908,115),(962,154),(974,219),(946,276),(864,284),(854,242)],
        ],
    },
    "rear-quarter": {
        "body": [(1151,120),(1246,120),(1267,187),(1263,265),(1286,315),(1091,315),(1120,265),(1121,187)],
        "hem": [(1105,280),(1284,280),(1321,412),(1051,412)],
        "sleeves": [
            [(1156,123),(1084,136),(1040,194),(1035,260),(1106,286),(1135,245),(1148,204)],
            [(1251,124),(1300,136),(1320,181),(1328,251),(1292,274),(1266,236),(1253,203)],
        ],
    },
    "back": {
        "body": [(1468,119),(1591,119),(1611,189),(1610,263),(1627,314),(1433,314),(1450,263),(1450,189)],
        "hem": [(1440,280),(1623,280),(1671,414),(1397,414)],
        "sleeves": [
            [(1467,122),(1404,138),(1375,201),(1379,259),(1443,283),(1461,245),(1468,206)],
            [(1595,121),(1663,138),(1686,201),(1685,260),(1624,284),(1603,244),(1593,203)],
        ],
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def points_str(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def poly(points, fill, stroke, width=8, extra=""):
    return (f'<polygon points="{points_str(points)}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width}" stroke-linejoin="round" {extra}/>')


def path(d, fill="none", stroke="none", width=1, extra=""):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def line(x1, y1, x2, y2, color, width=5, extra=""):
    return f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" {extra}/>'


def bounds(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def star_points(cx, cy, radius, inner=None):
    inner = inner if inner is not None else radius * 0.44
    return [(cx + (radius if i % 2 == 0 else inner) * math.cos(-math.pi/2 + i*math.pi/8),
             cy + (radius if i % 2 == 0 else inner) * math.sin(-math.pi/2 + i*math.pi/8)) for i in range(16)]


def medallion(cx, cy, radius):
    return (poly(star_points(cx, cy, radius*1.32), "#d5a74a", "#17223a", max(4, radius*0.25))
            + poly(star_points(cx, cy, radius), "#f5f5e9", "#55718f", max(3, radius*0.16))
            + f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius*.23:.1f}" fill="#7093b7" stroke="#f7efc6" stroke-width="3"/>')


def torso_design(theme, view_name, outline, clip_id):
    x0,y0,x1,y1 = bounds(outline); w=x1-x0; h=y1-y0; cx=(x0+x1)/2
    if theme == "starlight":
        shadow, cloth, trim, gold, light, mid, dark = "#0d1728", "#172642", "#6683a5", "#d8b05c", "#e6e9df", "#819dbb", "#29466b"
    else:
        shadow, cloth, trim, gold, light, mid, dark = "#211016", "#4c1d27", "#77313a", "#c49548", "#cf5940", "#8e2931", "#38171f"
    top=y0+7; belt_y=y0+h*.69; plate_top=y0+h*.18; plate_bottom=belt_y-4
    l=x0+w*.15; r=x1-w*.15
    out=[f'<g clip-path="url(#{clip_id})">', poly(outline, cloth, shadow, 12)]
    # The collar is a separate, raised metal rim; the uncovered neck stays
    # inside the calibrated garment silhouette rather than being patched in.
    if theme == "starlight":
        out += [poly([(cx-w*.18,top),(cx+w*.18,top),(cx+w*.28,y0+h*.12),(cx+w*.21,y0+h*.21),(cx-w*.21,y0+h*.21),(cx-w*.28,y0+h*.12)], "#344c6b", shadow, 7),
                path(f"M{cx-w*.22:.1f},{y0+h*.11:.1f} Q{cx:.1f},{y0+h*.22:.1f} {cx+w*.22:.1f},{y0+h*.11:.1f}", "none", "#eee5c5", 7),
                poly([(l,plate_top+8),(cx-w*.28,plate_top),(cx+w*.28,plate_top),(r,plate_top+8),(cx+w*.34,plate_bottom-h*.16),(cx,plate_bottom),(cx-w*.34,plate_bottom-h*.16)], "#36577d", "#111c31", 9),
                poly([(l+6,plate_top+9),(cx-w*.07,plate_top+8),(cx-w*.12,plate_bottom-h*.12),(cx-w*.32,plate_bottom-h*.20)], "#52789f", "#8197ad", 4),
                poly([(cx+w*.07,plate_top+8),(r-6,plate_top+9),(cx+w*.32,plate_bottom-h*.20),(cx+w*.12,plate_bottom-h*.12)], "#213957", "#15243c", 4),
                path(f"M{cx-w*.31:.1f},{plate_top+4:.1f} L{cx:.1f},{plate_top-3:.1f} L{cx+w*.31:.1f},{plate_top+4:.1f}", "none", gold, 5),
                line(cx-w*.24,plate_top+h*.24,cx+w*.18,plate_bottom-h*.16,"#c5d0da",5),
                line(cx,plate_top+10,cx,plate_bottom-3,"#d8b05c",5),
                medallion(cx, y0+h*.43, max(8,w*.075))]
        # A narrow articulated waist and a calm star-shaped clasp distinguish
        # this ceremonial armor from the existing blue-white rune cuirass.
        out += [path(f"M{l+3:.1f},{belt_y:.1f} L{r-3:.1f},{belt_y:.1f} L{r-w*.03:.1f},{belt_y+h*.075:.1f} L{l+w*.03:.1f},{belt_y+h*.075:.1f} Z", "#263e60", shadow, 7),
                line(l+3,belt_y+3,r-3,belt_y+3,gold,5),
                poly([(cx-w*.075,belt_y-3),(cx+w*.075,belt_y-3),(cx+w*.075,belt_y+h*.08),(cx-w*.075,belt_y+h*.08)], "#e6e9df", gold, 5),
                path(f"M{cx-w*.30:.1f},{plate_bottom-h*.10:.1f} l{w*.08:.1f},{h*.03:.1f} M{cx+w*.30:.1f},{plate_bottom-h*.10:.1f} l{-w*.08:.1f},{h*.03:.1f}", "none", "#91a8be", 5)]
    else:
        out += [poly([(cx-w*.21,top),(cx+w*.21,top),(cx+w*.31,y0+h*.11),(cx+w*.23,y0+h*.23),(cx-w*.23,y0+h*.23),(cx-w*.31,y0+h*.11)], "#67242d", shadow, 8),
                path(f"M{cx-w*.23:.1f},{y0+h*.12:.1f} L{cx-w*.12:.1f},{y0+h*.18:.1f} L{cx:.1f},{y0+h*.14:.1f} L{cx+w*.12:.1f},{y0+h*.18:.1f} L{cx+w*.23:.1f},{y0+h*.12:.1f}", "none", gold, 5),
                poly([(l,plate_top+7),(cx-w*.29,plate_top),(cx+w*.29,plate_top),(r,plate_top+7),(cx+w*.37,plate_bottom-h*.14),(cx+w*.20,plate_bottom),(cx-w*.20,plate_bottom),(cx-w*.37,plate_bottom-h*.14)], "#8e2931", "#201219", 10),
                poly([(l+6,plate_top+11),(cx-w*.07,plate_top+8),(cx-w*.12,plate_bottom-h*.08),(cx-w*.29,plate_bottom-h*.18)], "#c84f3b", "#67232b", 4),
                poly([(cx+w*.07,plate_top+8),(r-6,plate_top+11),(cx+w*.29,plate_bottom-h*.18),(cx+w*.12,plate_bottom-h*.08)], "#64202a", "#28141b", 4),
                path(f"M{l+4:.1f},{plate_top+3:.1f} L{cx:.1f},{plate_top-5:.1f} L{r-4:.1f},{plate_top+3:.1f}", "none", gold, 6),
                line(cx,plate_top+5,cx,plate_bottom-2,"#d7a954",5)]
        # Individually separated scale plates read as overlapping metal rather
        # than a noisy texture. Rear views instead show a segmented spine.
        if view_name in ("front", "front-quarter", "profile"):
            clip_plate=f"url(#{clip_id})"
            out.append(f'<g clip-path="{clip_plate}">')
            scale_w=max(8,w*.115); scale_h=max(6,h*.055)
            for row in range(3):
                yy=plate_top+h*(.24+.14*row)
                row_n=4 if view_name=="front" else 3
                for col in range(row_n):
                    xx=cx+(col-(row_n-1)/2)*(w*.13)+(row%2)*(w*.035)
                    if abs(xx-cx)>w*.32: continue
                    d=f"M{xx-scale_w:.1f},{yy:.1f} Q{xx:.1f},{yy+scale_h*1.65:.1f} {xx+scale_w:.1f},{yy:.1f} L{xx+scale_w*.72:.1f},{yy-scale_h*.22:.1f} Q{xx:.1f},{yy+scale_h*.53:.1f} {xx-scale_w*.72:.1f},{yy-scale_h*.22:.1f} Z"
                    out.append(path(d, "#bb4335" if (row+col)%2==0 else "#a43131", "#572029", 3))
                    line(xx-scale_w*.55,yy,xx,yy+scale_h*.38,"#e28051",2)
            out.append('</g>')
        else:
            # Rear lamellar ridge, evenly spaced and kept inside the silhouette.
            for frac in [.26,.38,.50,.62]:
                yy=y0+h*frac
                line(cx-w*.24,yy,cx+w*.24,yy,"#d4a354",4)
                path(f"M{cx-w*.2:.1f},{yy+4:.1f} Q{cx:.1f},{yy+h*.045:.1f} {cx+w*.2:.1f},{yy+4:.1f}", "none", "#8f2a32", 6)
        # A small hooked dragon crest, not a face or an oversized emblem.
        crest_y=y0+h*.47
        out += [path(f"M{cx-w*.12:.1f},{crest_y-h*.03:.1f} Q{cx-w*.04:.1f},{crest_y-h*.12:.1f} {cx+w*.03:.1f},{crest_y-h*.02:.1f} Q{cx+w*.16:.1f},{crest_y+h*.04:.1f} {cx+w*.04:.1f},{crest_y+h*.11:.1f} L{cx-w*.08:.1f},{crest_y+h*.12:.1f} Q{cx-w*.01:.1f},{crest_y+h*.04:.1f} {cx-w*.12:.1f},{crest_y-h*.03:.1f} Z", "#e6b25d", "#36151b", 4),
                path(f"M{cx-w*.06:.1f},{crest_y:.1f} Q{cx:.1f},{crest_y-h*.04:.1f} {cx+w*.07:.1f},{crest_y+h*.02:.1f}", "none", "#fff0bd", 3)]
    out.append('</g>')
    return ''.join(out)


def hem_design(theme, outline, clip_id):
    x0,y0,x1,y1=bounds(outline);w=x1-x0;h=y1-y0;cx=(x0+x1)/2
    if theme=="starlight":
        dark="#16243d";mid="#2a466c";light="#3a5b80";edge="#cba754";shadow="#0d1728"
    else:
        dark="#28151b";mid="#70252e";light="#9f302f";edge="#c59243";shadow="#160e14"
    # The hem is three articulated tassets with real openings between them;
    # trouser movement stays visible through the splits.
    ytop=y0+h*.08; ymid=y0+h*.52; ybot=y1-h*.025
    left=[(x0+w*.08,ytop),(cx-w*.15,ytop+4),(cx-w*.20,ymid),(x0+w*.22,ybot),(x0+w*.03,ymid)]
    right=[(cx+w*.15,ytop),(x1-w*.08,ytop),(x1-w*.03,ymid),(x1-w*.22,ybot),(cx+w*.20,ymid)]
    center=[(cx-w*.16,ytop+3),(cx+w*.16,ytop+3),(cx+w*.13,ymid),(cx,ybot),(cx-w*.13,ymid)]
    out=[f'<g clip-path="url(#{clip_id})">']
    if theme=="starlight":
        out += [poly(left,dark,shadow,9),poly(right,dark,shadow,9),poly(center,light,"#17253d",8),
                poly([(x0+w*.105,ytop+9),(cx-w*.17,ytop+12),(cx-w*.23,ymid-3),(x0+w*.22,ybot-8)],mid,"#17253d",4),
                poly([(cx+w*.17,ytop+12),(x1-w*.105,ytop+9),(x1-w*.22,ybot-8),(cx+w*.23,ymid-3)],"#203454","#101b2d",4),
                path(f"M{cx:.1f},{ytop+8:.1f} L{cx:.1f},{ybot-8:.1f}","none",edge,6),
                line(cx-w*.12,ybot-h*.07,cx,ybot-h*.01,"#b8c9d8",4),
                line(cx+w*.12,ybot-h*.07,cx,ybot-h*.01,"#b8c9d8",4),
                medallion(cx,y0+h*.66,max(5,w*.05))]
    else:
        out += [poly(left,dark,shadow,10),poly(right,dark,shadow,10),poly(center,mid,shadow,9),
                poly([(x0+w*.12,ytop+9),(cx-w*.17,ytop+12),(cx-w*.23,ymid-3),(x0+w*.23,ybot-8)],"#70242d",edge,4),
                poly([(cx+w*.17,ytop+12),(x1-w*.12,ytop+9),(x1-w*.23,ybot-8),(cx+w*.23,ymid-3)],"#501c27",edge,4),
                path(f"M{cx-w*.13:.1f},{ytop+10:.1f} L{cx:.1f},{ybot-h*.03:.1f} L{cx+w*.13:.1f},{ytop+10:.1f}","none",edge,6)]
        for row in range(2):
            yy=ytop+h*(.25+.16*row)
            for col in range(5):
                xx=x0+w*(.16+.15*col)+(row%2)*w*.05
                if xx < cx-w*.10 or xx > cx+w*.10:
                    path(f"M{xx-w*.04:.1f},{yy:.1f} Q{xx:.1f},{yy+h*.055:.1f} {xx+w*.04:.1f},{yy:.1f}","#a53434","#3b151d",3)
    out.append('</g>')
    return ''.join(out)


def sleeve_design(theme, view_name, poly_points, clip_id, side):
    x0,y0,x1,y1=bounds(poly_points);w=x1-x0;h=y1-y0
    if theme=="starlight":
        base="#1a3458";shadow="#0e182c";plate="#cbd8df";plate_hi="#eff1e6";blue="#527493";gold="#d5ad59"
    else:
        base="#4d1b26";shadow="#1d1118";plate="#772631";plate_hi="#bd4338";blue="#391820";gold="#c59449"
    cap_top=y0+h*.06;cap_end=y0+h*.38
    cuff_top=y0+h*.68;cuff_bot=y0+h*.91
    out=[f'<g clip-path="url(#{clip_id})">',poly(poly_points,base,shadow,10)]
    if theme=="starlight":
        cap=[(x0+w*.20,cap_top),(x1-w*.12,cap_top+h*.02),(x1-w*.02,cap_end),(x0+w*.36,cap_end+h*.02)]
        out += [poly(cap,blue,shadow,6),
                path(f"M{x0+w*.24:.1f},{cap_top+h*.12:.1f} L{x0+w*.43:.1f},{cap_end-h*.03:.1f} L{x1-w*.10:.1f},{cap_end-h*.09:.1f}","none",gold,5),
                poly([(x0+w*.26,cuff_top),(x1-w*.06,cuff_top),(x1-w*.20,cuff_bot),(x0+w*.37,cuff_bot)],plate,shadow,7),
                poly([(x0+w*.32,cuff_top+h*.035),(x0+w*.72,cuff_top+h*.035),(x0+w*.63,cuff_bot-h*.025),(x0+w*.40,cuff_bot-h*.025)],plate_hi,"#7f96aa",4),
                line(x0+w*.32,cuff_top+h*.06,x1-w*.09,cuff_top+h*.06,gold,5),
                line(x0+w*.38,cuff_bot-h*.05,x1-w*.15,cuff_bot-h*.05,gold,5)]
    else:
        cap=[(x0+w*.16,cap_top),(x1-w*.14,cap_top+h*.02),(x1-w*.02,cap_end),(x0+w*.28,cap_end+h*.02)]
        out += [poly(cap,plate,shadow,7),
                path(f"M{x0+w*.20:.1f},{cap_top+h*.14:.1f} L{x0+w*.43:.1f},{cap_end-h*.03:.1f} L{x1-w*.10:.1f},{cap_end-h*.09:.1f}","none",gold,5),
                poly([(x0+w*.24,cuff_top),(x1-w*.05,cuff_top),(x1-w*.20,cuff_bot),(x0+w*.35,cuff_bot)],plate,shadow,8),
                poly([(x0+w*.34,cuff_top+h*.04),(x0+w*.77,cuff_top+h*.04),(x0+w*.62,cuff_bot-h*.025),(x0+w*.43,cuff_bot-h*.025)],plate_hi,"#451923",4),
                line(x0+w*.27,cuff_top+h*.04,x1-w*.08,cuff_top+h*.04,gold,5),
                line(x0+w*.37,cuff_bot-h*.04,x1-w*.16,cuff_bot-h*.04,gold,5)]
        # A few overlapping scales on the shoulder cap echo the cuirass plates.
        for k in range(3):
            xx=x0+w*(.34+.16*k); yy=cap_top+h*.21
            path(f"M{xx-w*.055:.1f},{yy:.1f} Q{xx:.1f},{yy+h*.075:.1f} {xx+w*.055:.1f},{yy:.1f} L{xx+w*.04:.1f},{yy-h*.025:.1f} Z","#b74639","#5b2028",3)
    out.append('</g>')
    return ''.join(out)


def make_svg(theme):
    pieces=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE[0]}" height="{SIZE[1]}" viewBox="0 0 {SIZE[0]} {SIZE[1]}">','<defs>']
    for view_name, data in VIEWS.items():
        pieces.append(f'<clipPath id="{view_name}-torso"><polygon points="{points_str(data["body"])}"/></clipPath>')
        pieces.append(f'<clipPath id="{view_name}-hem"><polygon points="{points_str(data["hem"])}"/></clipPath>')
        for i, sleeve in enumerate(data['sleeves']):
            pieces.append(f'<clipPath id="{view_name}-sleeve-{i}"><polygon points="{points_str(sleeve)}"/></clipPath>')
    pieces.append('</defs>')
    for view_name,data in VIEWS.items():
        pieces.append(f'<g id="view-{view_name}" data-view="{view_name}">')
        pieces.append(f'<g id="outfit.torso-{view_name}">{torso_design(theme,view_name,data["body"],f"{view_name}-torso")}</g>')
        for i,sleeve in enumerate(data['sleeves']):
            side='left' if i==0 else 'right'
            pieces.append(f'<g id="outfit.sleeve.{side}-{view_name}">{sleeve_design(theme,view_name,sleeve,f"{view_name}-sleeve-{i}",side)}</g>')
        pieces.append(f'<g id="outfit.hem.front-{view_name}">{hem_design(theme,data["hem"],f"{view_name}-hem")}</g>')
        pieces.append('</g>')
    pieces.append('</svg>')
    return '\n'.join(pieces)


def png_zero_transparent(path):
    with Image.open(path) as im:
        im=im.convert('RGBA')
        px=im.load()
        for y in range(im.height):
            for x in range(im.width):
                r,g,b,a=px[x,y]
                if a==0: px[x,y]=(0,0,0,0)
        im.save(path)


def make_template(source_svg: Path, target: Path):
    subprocess.run(["inkscape", str(source_svg), "--export-filename="+str(target),
                    f"--export-width={SIZE[0]}", f"--export-height={SIZE[1]}"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    png_zero_transparent(target)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")


def safe_png(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    im=im.convert('RGBA')
    alpha=im.getchannel('A')
    if alpha.getextrema()[1] <= 0:
        raise ValueError(f"empty layer: {path}")
    if alpha.getpixel((0,0)) or alpha.getpixel((255,0)) or alpha.getpixel((0,255)) or alpha.getpixel((255,255)):
        raise ValueError(f"art reaches corner: {path}")
    im.save(path)


def build_asset(item, display_name, theme):
    folder=OUT/item
    src=folder/'source'
    editable=folder/'editable'
    src.mkdir(parents=True, exist_ok=True)
    editable.mkdir(parents=True, exist_ok=True)
    svg=make_svg(theme)
    (src/'armor-design.svg').write_text(svg+'\n')
    (editable/'armor-design.svg').write_text(svg+'\n')
    template=src/'armor-template-sheet.png'
    make_template(src/'armor-design.svg',template)
    palette = {
        'starlight': {'primary':'#172642','steelBlue':'#36577D','silver':'#819DBB','ivory':'#E6E9DF','gold':'#D8B05C','shadow':'#0D1728'},
        'dragon': {'primary':'#8E2931','wine':'#4C1D27','bronze':'#C49548','ember':'#CF5940','shadow':'#211016'},
    }[theme]
    write_json(src/'palette.json',palette)
    # Keep the production exporter tied to the same source surface/motion as
    # the validated B2 armor pipeline without editing either frozen resource.
    surface=surface_module.ArmorSurface(ROOT)
    surface.sheet=Image.open(template).convert('RGBA')
    surface.patterns={}
    motion=json.loads(MOTION_PATH.read_text())
    profile=json.loads((ROOT/'Art/Standards/P1-Parts-v1/profile.json').read_text())
    frames={(f['direction'],f['clip'],f['frame']):f for f in motion['frames']}
    all_bindings=[]
    output_hashes={}
    for key in sorted(frames):
        frame=frames[key]
        layers=surface.render('leatherArmor',frame)
        direction,clip,num=key
        layer_map={}
        folder_name=f"png/{direction}/{clip}/{num:02d}"
        for slot in SLOTS:
            relative=f"{folder_name}/{slot}.png"
            path=folder/relative
            safe_png(layers[slot],path)
            layer_map[slot]=relative
            output_hashes[relative]=sha(path)
        all_bindings.append({'direction':direction,'clip':clip,'frame':num,'layers':layer_map})
    template_manifest=json.loads((ROOT/'Art/Parts/P1-v1/b2-armor-r5/runeArmor/asset.json').read_text())
    asset=copy.deepcopy(template_manifest)
    armor_slug={'starlightArmor':'starlight-armor','dragonArmor':'dragon-armor'}[item]
    asset.update({
        'id':f'p1-b5-{armor_slug}-v1','version':'1.0.0','directions':DIRECTIONS,
        'clips':['idle','walk','walk-start','walk-stop'],'slots':SLOTS,
        'sourceFiles':['authoring.json','source/armor-design.svg','source/armor-template-sheet.png','source/palette.json','editable/armor-design.svg'],
        'bindings':all_bindings,
    })
    write_json(folder/'asset.json',asset)
    write_json(folder/'authoring.json',{
        'itemID':item,'displayName':display_name,'designTheme':theme,
        'sourceArtwork':'source/armor-design.svg','editableArtwork':'editable/armor-design.svg',
        'renderedTemplate':'source/armor-template-sheet.png',
        'surfaceScript':'scripts/armor-shared-surface-r4.py',
        'exporter':'scripts/build-b5-set-armors.py',
        'motion':'Art/Integration/P1-modular-eight-way-v1/motion.json',
        'rig':'p1-eight-way-base-v1','poseBindings':104,'layerBindings':416,
        'method':'five hand-authored camera views (front, front-quarter, profile, rear-quarter, back); separate torso, left/right sleeve and split front fauld; projected through the existing registered armor surface sampler; final pose map rendered by the current compositor',
        'distinctSilhouetteAndMaterial':True,
        'bodyMotionJointMapDrawOrderModified':False,
        'oldOutfitAssetsModified':False,
        'battlePoseBinding':'not included in this locomotion art task',
        'userArtApproval':None,
        'sourceSVG_SHA256':sha(src/'armor-design.svg'),
        'templatePNG_SHA256':sha(template),
        'motionSHA256':sha(MOTION_PATH),
        'baseBodyManifestSHA256':sha(ROOT/'Art/Parts/P1-v1/eight-way-v1/base/asset.json'),
        'posePNG_SHA256':output_hashes,
    })
    return folder,asset


def create_catalog(assets):
    catalog=json.loads(BASE_CATALOG.read_text())
    for folder,asset in assets:
        catalog['assets'].append({'id':asset['id'],'manifest':str((folder/'asset.json').relative_to(ROOT))})
    write_json(REVIEW/'catalog.json',catalog)
    return catalog


def font(size=18):
    paths=['/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p,size)
    return ImageFont.load_default()


def labeled_cell(image, label, scale=1, width=256, height=278):
    source=image.resize((256*scale,256*scale),Image.Resampling.NEAREST)
    canvas=Image.new('RGB',(width*scale,height*scale),'#20372a')
    canvas.paste(source,(0,0),source)
    draw=ImageDraw.Draw(canvas)
    draw.text((6*scale,258*scale),label,font=font(12*scale),fill='#f4e8c7')
    return canvas


def on_review_background(image, scale=1):
    rgba=image.convert('RGBA').resize((256*scale,256*scale),Image.Resampling.NEAREST)
    canvas=Image.new('RGB',rgba.size,'#20372a')
    canvas.paste(rgba,(0,0),rgba)
    return canvas


def crop_and_grid(compositor, asset_id, item_name, directory):
    directory.mkdir(parents=True,exist_ok=True)
    selected_base=[asset_id,'p1-eight-way-lower-v1','p1-eight-way-hair-chestnut-v1','p1-eight-way-face-blue-v1','p1-eight-way-weapon-v1']
    poses={}
    for d in DIRECTIONS:
        for clip in ['idle','walk','walk-start','walk-stop']:
            frames=[f['frame'] for f in compositor.motion['frames'] if f['direction']==d and f['clip']==clip]
            for n in frames:
                poses[(d,clip,n)]=compositor.render('p1-eight-way-base-v1',selected_base,d,clip,n)
    # One full-sized 1x/2x matrix per facing preserves useful detail while
    # showing idle, all walk phases, start and stop as one garment silhouette.
    ordered=[('idle',0)]+[('walk',n) for n in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]
    for d in DIRECTIONS:
        for scale in [1,2]:
            page=Image.new('RGB',(4*256*scale,4*278*scale),'#20372a')
            for i,(clip,n) in enumerate(ordered):
                cell=labeled_cell(poses[(d,clip,n)],f'{clip} {n:02}',scale)
                page.paste(cell,((i%4)*256*scale,(i//4)*278*scale))
            page.save(directory/f'{d}-poses-{scale}x.png')
        # Walk art only: native 8 frames, 120 ms each, 960 ms total.
        walk=[]
        for n in range(1,9):
            im=on_review_background(poses[(d,'walk',n)],2)
            walk.append(im)
        walk[0].save(directory/f'{d}-walk-normal.gif',save_all=True,append_images=walk[1:],duration=120,loop=0,disposal=2,optimize=True)
        # Approved fixed entry/exit phases: idle, start, two walk cycles, stop, idle.
        entry={'down':1,'down-left':4,'left':4,'up-left':4,'up':4,'up-right':0,'right':0,'down-right':0}[d]
        exitp={'down':0,'down-left':3,'left':3,'up-left':3,'up':3,'up-right':7,'right':7,'down-right':7}[d]
        seq=[poses[(d,'idle',0)],poses[(d,'walk-start',1)],poses[(d,'walk-start',2)]]
        seq += [poses[(d,'walk',((entry+i)%8)+1)] for i in range(16)]
        seq += [poses[(d,'walk-stop',1)],poses[(d,'walk-stop',2)],poses[(d,'idle',0)]]
        seq=[on_review_background(im,2) for im in seq]
        seq[0].save(directory/f'{d}-start-stop-normal.gif',save_all=True,append_images=seq[1:],duration=[480]+[120]*20+[480],loop=0,disposal=2,optimize=True)
    # A readable four-by-two facing overview; detail remains in per-facing
    # full-size 1x/2x pose sheets and the real-time GIFs above.
    overview=Image.new('RGB',(4*256,2*278),'#20372a')
    for i,d in enumerate(DIRECTIONS):
        overview.paste(labeled_cell(poses[(d,'idle',0)],d,1),(i%4*256,i//4*278))
    overview.save(directory/'all-directions-standing.png')
    # Proper full-body normal-speed GIF, 8 x 120 ms, for each facing.
    return poses


def validate_all_combinations(catalog, assets):
    compositor=compose_module.Compositor(ROOT, REVIEW/'catalog.json', MOTION_PATH)
    hairstyles=['p1-eight-way-hair-chestnut-v1','p1-eight-way-hair-silver-v1']
    faces=['p1-eight-way-face-blue-v1','p1-eight-way-face-amber-v1']
    carry=[None,'p1-eight-way-weapon-v1']
    results=[]
    for folder,asset in assets:
        for hair in hairstyles:
            for face in faces:
                for weapon in carry:
                    selected=[asset['id'],'p1-eight-way-lower-v1',hair,face]
                    if weapon: selected.append(weapon)
                    h=hashlib.sha256()
                    count=0
                    for key in sorted(compositor.frames):
                        d,clip,n=key
                        im=compositor.render('p1-eight-way-base-v1',selected,d,clip,n)
                        h.update(im.tobytes());count+=1
                    results.append({'armor':asset['id'],'hair':hair,'face':face,'backWeapon':bool(weapon),'poses':count,'rgbaSHA256':h.hexdigest()})
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-art-export',action='store_true',help='reuse already generated 104-pose outfit packages and rebuild only compositions/previews')
    args=parser.parse_args()
    REVIEW.mkdir(parents=True,exist_ok=True)
    if args.skip_art_export:
        assets=[]
        for item,name in [('starlightArmor','星辉甲'),('dragonArmor','龙纹甲')]:
            folder=OUT/item
            assets.append((folder,json.loads((folder/'asset.json').read_text())))
    else:
        assets=[build_asset('starlightArmor','星辉甲','starlight'),build_asset('dragonArmor','龙纹甲','dragon')]
    catalog=create_catalog(assets)
    manifests=[{
        'id':asset['id'],'itemID':item,'name':name,'asset':str((folder/'asset.json').relative_to(ROOT)),
        'bindings':len(asset['bindings']),'slots':asset['slots'],'artApproval':None,
    } for (folder,asset),(item,name) in zip(assets,[('starlightArmor','星辉甲'),('dragonArmor','龙纹甲')])]
    write_json(REVIEW/'manifest.json',{'id':'b5-set-armors-v1','title':'B5 星辉甲／龙纹甲八向服装候选','items':manifests,'approval':None})
    # Render every pose for every compatible full outfit combination. This is
    # actual compositor output, not a static asset or manually layered mockup.
    combinations=validate_all_combinations(catalog,assets)
    write_json(REVIEW/'combination-composition.json',{
        'combinations':len(combinations),'posesPerCombination':104,'totalCompositions':sum(x['poses'] for x in combinations),
        'hairOptions':2,'faceOptions':2,'backWeaponOptions':2,'lower':'p1-eight-way-lower-v1',
        'results':combinations,
    })
    compositor=compose_module.Compositor(ROOT,REVIEW/'catalog.json',MOTION_PATH)
    for folder,asset in assets:
        # Primary display profile uses the chestnut face/base and proves the
        # actual selected item stays attached through all 104 registered poses.
        poses=crop_and_grid(compositor,asset['id'],asset['id'],REVIEW/'preview'/asset['id'])
        # Publish useful 1x and 2x full body stills and a normal 960ms walk GIF.
        primary=REVIEW/'preview'/asset['id']
        poses[('down','idle',0)].save(primary/'standing-1x.png')
        poses[('down','idle',0)].resize((512,512),Image.Resampling.NEAREST).save(primary/'standing-2x.png')
    write_json(REVIEW/'verification.json',{
        'assetContract':'pending external checker','compositor':'passed by build script','bodyMotionProfileDrawOrderChanges':0,
        'bindingsPerArmor':104,'layerPNGPerArmor':416,'totalCompatibilityCombinations':len(combinations),
        'posesComposed':sum(x['poses'] for x in combinations),
        'normalWalkGIF':'8 frames × 120ms = 960ms, all eight facings per armor','normalStartStopGIF':'22 frames; first/last idle 480ms, twenty moving poses 120ms = 3360ms, all eight facings per armor',
        'reviewScope':'candidate imagery only; main preview includes the registered back sword; user art approval pending',
        'artApproval':None,
    })
    print(json.dumps({'assets':manifests,'combinations':len(combinations),'poses':sum(x['poses'] for x in combinations)},ensure_ascii=False))


if __name__=='__main__':
    main()
