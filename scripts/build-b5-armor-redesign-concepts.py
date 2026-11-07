#!/usr/bin/env python3
"""Render six richer, project-body B5 armor concepts for user selection.

These are down-facing concept previews only. They deliberately do not create
production manifests or claim eight-way approval; after the user selects a
design it must be expanded and reviewed against the full 104-pose contract.
"""
from __future__ import annotations

import colorsys
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Art/Review/P1/b5-armor-redesign-concepts-v1"
PARTS = ROOT / "Art/Parts/P1-v1/b5-set-armors-v1"
MOTION = ROOT / "Art/Integration/P1-modular-eight-way-v1/motion.json"
CATALOG = ROOT / "Art/Review/P1/b5-set-armors-v1/catalog.json"
BACKGROUND = (31, 54, 42)
CANVAS = (256, 256)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load_module("b5_armor_builder", ROOT / "scripts/build-b5-set-armors.py")


OPTIONS = [
    {
        "id": "star-a-starforged",
        "family": "starlight",
        "label": "星辉甲 A · 星铸骑士",
        "material": "午夜蓝钢 · 银白星冠 · 明金纹章",
        "blueHue": 0.58,
        "sat": 1.24,
        "value": 0.96,
        "goldHue": 0.115,
        "motif": "starburst",
        "accent": "#f2ca63",
        "pauldron": "#385b87",
        "highlight": "#f0f2e3",
        "shadow": "#111b2c",
        "description": "加宽星钢胸甲、八芒徽、双层银肩甲",
    },
    {
        "id": "star-b-corona",
        "family": "starlight",
        "label": "星辉甲 B · 日冕圣卫",
        "material": "象牙白金属 · 皇家蓝衬 · 日轮金饰",
        "blueHue": 0.125,
        "sat": 0.24,
        "value": 1.0,
        "goldHue": 0.105,
        "motif": "sunburst",
        "accent": "#e2bb57",
        "pauldron": "#eee5c5",
        "highlight": "#fff0bf",
        "shadow": "#17213a",
        "description": "象牙金胸甲、日轮徽、蓝色侧嵌",
    },
    {
        "id": "star-c-eclipse",
        "family": "starlight",
        "label": "星辉甲 C · 星蚀守望",
        "material": "暮紫星钢 · 冷银边 · 暗金星图",
        "blueHue": 0.77,
        "sat": 1.30,
        "value": 0.93,
        "goldHue": 0.105,
        "motif": "crescent",
        "accent": "#d8b65e",
        "pauldron": "#4b3a72",
        "highlight": "#e5dff5",
        "shadow": "#1a1530",
        "description": "暮紫星钢、月蚀徽、非对称银肩",
    },
    {
        "id": "dragon-a-jade-scale",
        "family": "dragon",
        "label": "龙纹甲 A · 青玉龙鳞",
        "material": "翡翠鳞钢 · 古铜骨架 · 玉色龙徽",
        "redHue": 0.375,
        "sat": 1.25,
        "value": 0.94,
        "motif": "scales",
        "accent": "#d7ad58",
        "pauldron": "#167447",
        "highlight": "#a8d889",
        "shadow": "#14231c",
        "description": "青玉叠鳞、古铜边、分片护腰",
    },
    {
        "id": "dragon-b-ember-vanguard",
        "family": "dragon",
        "label": "龙纹甲 B · 赤焰龙骑",
        "material": "熔岩赤甲 · 黑铁边 · 炽金龙徽",
        "redHue": 0.025,
        "sat": 1.34,
        "value": 1.02,
        "motif": "flame",
        "accent": "#f0b947",
        "pauldron": "#8e2d30",
        "highlight": "#ff8b40",
        "shadow": "#1c1118",
        "description": "赤焰重甲、火棘肩甲、龙火胸徽",
    },
    {
        "id": "dragon-c-onyx-commander",
        "family": "dragon",
        "label": "龙纹甲 C · 玄金御龙",
        "material": "曜石黑甲 · 亮金骨线 · 赤玉龙眼",
        "redHue": 0.01,
        "sat": 0.18,
        "value": 0.63,
        "motif": "imperial",
        "accent": "#e0b953",
        "pauldron": "#211c22",
        "highlight": "#f3d97d",
        "shadow": "#100f13",
        "description": "玄铁黑金、龙翼肩甲、红玉徽眼",
    },
]


def hex_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v * 255)))) for v in rgb)


def recolor(value: str, option: dict, family: str) -> str:
    red, green, blue = hex_rgb(value)
    hue, sat, val = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    if family == "starlight":
        # Re-map the blue metal/textile range while preserving authored shade
        # ordering. Solar ivory intentionally moves blue hues toward warm gold.
        if 0.52 <= hue <= 0.75 and sat >= 0.16:
            if option["motif"] == "sunburst":
                hue = option["blueHue"]
                # A pearl/ivory plate must lose most of the source blue
                # saturation; blue returns as a separately drawn accent.
                sat = max(0.06, sat * option["sat"])
                val = min(0.99, 0.46 + val * 0.54)
            else:
                hue = option["blueHue"]
                sat = min(1.0, sat * option["sat"])
                val = max(0.03, min(0.98, val * option["value"]))
        elif (0.08 <= hue <= 0.17 and sat >= 0.32):
            hue = option["goldHue"]
            sat = min(1.0, sat * 1.12)
    else:
        red_range = hue <= 0.045 or hue >= 0.96
        if red_range and sat >= 0.20:
            hue = option["redHue"]
            sat = min(1.0, sat * option["sat"])
            val = max(0.025, min(0.96, val * option["value"]))
        elif 0.075 <= hue <= 0.16 and sat >= 0.30:
            sat = min(1.0, sat * 1.10)
            val = min(0.98, val * 1.02)
    return rgb_hex(colorsys.hsv_to_rgb(hue % 1.0, sat, val))


def polygon_points(cx, cy, radius, inner, tips=8):
    points = []
    for i in range(tips * 2):
        r = radius if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / tips
        points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def crest_fragment(option: dict, view_name: str, outline):
    x0, y0, x1, y1 = builder.bounds(outline)
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    cy = y0 + h * (0.43 if option["family"] == "starlight" else 0.47)
    clip = f"{view_name}-torso"
    accent = option["accent"]
    light = option["highlight"]
    dark = option["shadow"]
    common = [f'<g clip-path="url(#{clip})">']
    motif = option["motif"]
    radius = w * (0.115 if view_name in ("profile", "front-quarter") else 0.13)

    if option["family"] == "starlight":
        # A broad, beveled cuirass outline gives the torso a plate silhouette
        # even at the game's native sprite scale. The core emblem stays clear.
        plate = [
            (cx-w*.36, y0+h*.20), (cx-w*.25, y0+h*.16),
            (cx+w*.25, y0+h*.16), (cx+w*.36, y0+h*.20),
            (cx+w*.30, y0+h*.59), (cx+w*.18, y0+h*.68),
            (cx-w*.18, y0+h*.68), (cx-w*.30, y0+h*.59),
        ]
        plate_str = " ".join(f"{x:.1f},{y:.1f}" for x,y in plate)
        common.append(f'<polygon points="{plate_str}" fill="none" stroke="{accent}" stroke-width="8" stroke-linejoin="miter"/>')
        common.append(f'<path d="M{cx-w*.31:.1f},{y0+h*.24:.1f} L{cx-w*.22:.1f},{y0+h*.31:.1f} M{cx+w*.31:.1f},{y0+h*.24:.1f} L{cx+w*.22:.1f},{y0+h*.31:.1f}" fill="none" stroke="{light}" stroke-width="6"/>')
        if motif == "sunburst":
            common.append(f'<path d="M{cx-w*.31:.1f},{y0+h*.38:.1f} L{cx-w*.26:.1f},{y0+h*.58:.1f} M{cx+w*.31:.1f},{y0+h*.38:.1f} L{cx+w*.26:.1f},{y0+h*.58:.1f}" fill="none" stroke="#355684" stroke-width="10"/>')
        if motif in ("starburst", "sunburst"):
            tips = 12 if motif == "sunburst" else 8
            common += [
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius*1.50:.1f}" fill="none" stroke="{accent}" stroke-width="6"/>',
                f'<polygon points="{polygon_points(cx,cy,radius, radius*.48,tips)}" fill="{accent}" stroke="{dark}" stroke-width="6" stroke-linejoin="miter"/>',
                f'<polygon points="{polygon_points(cx,cy,radius*.55, radius*.25,8)}" fill="{light}" stroke="{dark}" stroke-width="3" stroke-linejoin="miter"/>',
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{max(4,w*.018):.1f}" fill="{light}" stroke="{dark}" stroke-width="3"/>',
            ]
            for sign in (-1, 1):
                sx = cx + sign * w * .30
                sy = y0 + h * .24
                common.append(f'<polygon points="{polygon_points(sx,sy,w*.042,w*.018,4)}" fill="{light}" stroke="{accent}" stroke-width="3"/>')
        else:
            r = radius * 1.34
            common += [
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{accent}" stroke-width="6" stroke-dasharray="{r*.42:.1f} {r*.18:.1f}"/>',
                f'<path d="M{cx-r*.35:.1f},{cy-r*.72:.1f} Q{cx+r*.58:.1f},{cy-r*.48:.1f} {cx+r*.20:.1f},{cy+r*.12:.1f} Q{cx-r*.10:.1f},{cy+r*.48:.1f} {cx-r*.66:.1f},{cy+r*.55:.1f} Q{cx-r*.19:.1f},{cy+r*.08:.1f} {cx-r*.35:.1f},{cy-r*.72:.1f} Z" fill="{accent}" stroke="{dark}" stroke-width="5"/>',
                f'<polygon points="{polygon_points(cx+r*.54,cy-r*.40,r*.25,r*.10,4)}" fill="{light}" stroke="{dark}" stroke-width="3"/>',
                f'<polygon points="{polygon_points(cx-r*.52,cy-r*.28,r*.18,r*.08,4)}" fill="{light}" stroke="{dark}" stroke-width="3"/>',
            ]
        # Orbit ticks sit on the chestplate, not outside its silhouette.
        common.append(f'<path d="M{cx-w*.31:.1f},{cy+h*.12:.1f} L{cx-w*.23:.1f},{cy+h*.09:.1f} M{cx+w*.23:.1f},{cy+h*.09:.1f} L{cx+w*.31:.1f},{cy+h*.12:.1f}" fill="none" stroke="{light}" stroke-width="5"/>')
    else:
        shield_w, shield_h = w * .24, h * .23
        shield = [(cx,cy-shield_h*.62),(cx+shield_w*.62,cy-shield_h*.35),(cx+shield_w*.50,cy+shield_h*.38),(cx,cy+shield_h*.70),(cx-shield_w*.50,cy+shield_h*.38),(cx-shield_w*.62,cy-shield_h*.35)]
        shield_str = " ".join(f"{x:.1f},{y:.1f}" for x,y in shield)
        plate = [(cx-w*.37,y0+h*.20),(cx-w*.25,y0+h*.15),(cx+w*.25,y0+h*.15),(cx+w*.37,y0+h*.20),(cx+w*.31,y0+h*.60),(cx+w*.18,y0+h*.69),(cx-w*.18,y0+h*.69),(cx-w*.31,y0+h*.60)]
        plate_str = " ".join(f"{x:.1f},{y:.1f}" for x,y in plate)
        common += [
            f'<polygon points="{plate_str}" fill="none" stroke="{accent}" stroke-width="9" stroke-linejoin="miter"/>',
            f'<path d="M{cx-w*.32:.1f},{y0+h*.24:.1f} L{cx-w*.22:.1f},{y0+h*.31:.1f} M{cx+w*.32:.1f},{y0+h*.24:.1f} L{cx+w*.22:.1f},{y0+h*.31:.1f}" fill="none" stroke="{light}" stroke-width="6"/>',
            f'<polygon points="{shield_str}" fill="{dark}" stroke="{accent}" stroke-width="7" stroke-linejoin="miter"/>',
            f'<path d="M{cx-w*.065:.1f},{cy+h*.04:.1f} Q{cx-w*.005:.1f},{cy-h*.13:.1f} {cx+w*.06:.1f},{cy-h*.02:.1f} Q{cx+w*.13:.1f},{cy+h*.07:.1f} {cx+w*.035:.1f},{cy+h*.15:.1f} L{cx-w*.07:.1f},{cy+h*.14:.1f} Q{cx+w*.005:.1f},{cy+h*.06:.1f} {cx-w*.065:.1f},{cy+h*.04:.1f} Z" fill="{light}" stroke="{accent}" stroke-width="4"/>',
            f'<path d="M{cx-w*.075:.1f},{cy-h*.02:.1f} L{cx-w*.15:.1f},{cy-h*.12:.1f} L{cx-w*.105:.1f},{cy+h*.005:.1f} M{cx+w*.07:.1f},{cy-h*.02:.1f} L{cx+w*.15:.1f},{cy-h*.14:.1f} L{cx+w*.12:.1f},{cy+h*.01:.1f}" fill="none" stroke="{accent}" stroke-width="6" stroke-linejoin="miter"/>',
            f'<circle cx="{cx+w*.02:.1f}" cy="{cy-h*.015:.1f}" r="{max(4,w*.018):.1f}" fill="{accent}" stroke="{dark}" stroke-width="3"/>',
        ]
        if motif == "flame":
            common.append(f'<path d="M{cx-w*.22:.1f},{cy+h*.12:.1f} L{cx-w*.30:.1f},{cy-h*.02:.1f} L{cx-w*.25:.1f},{cy-h*.20:.1f} L{cx-w*.12:.1f},{cy-h*.04:.1f} M{cx+w*.22:.1f},{cy+h*.12:.1f} L{cx+w*.30:.1f},{cy-h*.02:.1f} L{cx+w*.25:.1f},{cy-h*.20:.1f} L{cx+w*.12:.1f},{cy-h*.04:.1f}" fill="none" stroke="{light}" stroke-width="8" stroke-linejoin="miter"/>')
        elif motif == "imperial":
            common.append(f'<path d="M{cx-w*.18:.1f},{cy+h*.16:.1f} Q{cx-w*.36:.1f},{cy+h*.05:.1f} {cx-w*.34:.1f},{cy-h*.16:.1f} L{cx-w*.19:.1f},{cy-h*.08:.1f} M{cx+w*.18:.1f},{cy+h*.16:.1f} Q{cx+w*.36:.1f},{cy+h*.05:.1f} {cx+w*.34:.1f},{cy-h*.16:.1f} L{cx+w*.19:.1f},{cy-h*.08:.1f}" fill="none" stroke="{accent}" stroke-width="9" stroke-linejoin="miter"/>')
            common.append(f'<circle cx="{cx+w*.02:.1f}" cy="{cy-h*.015:.1f}" r="{max(5,w*.028):.1f}" fill="#c94a42" stroke="{light}" stroke-width="4"/>')
        # A few articulated scale plates reinforce material without adding noise.
        scale_w, scale_h = w * .095, h * .075
        for row in range(2):
            yy = cy + h * (.24 + row * .105)
            for col in (-1, 0, 1):
                if col == 0:
                    continue
                xx = cx + col * w * .18 + (row % 2) * w * .035
                d = f"M{xx-scale_w:.1f},{yy:.1f} Q{xx:.1f},{yy+scale_h*1.7:.1f} {xx+scale_w:.1f},{yy:.1f} L{xx+scale_w*.68:.1f},{yy-scale_h*.25:.1f} Q{xx:.1f},{yy+scale_h*.45:.1f} {xx-scale_w*.68:.1f},{yy-scale_h*.25:.1f} Z"
                common.append(f'<path d="{d}" fill="{accent}" stroke="{dark}" stroke-width="3"/>')
    common.append('</g>')
    return "".join(common)


def shoulder_fragment(option: dict, view_name: str, sleeve, side: int):
    x0, y0, x1, y1 = builder.bounds(sleeve)
    w, h = x1 - x0, y1 - y0
    x = x0 + w * (.28 if side == 0 else .72)
    y = y0 + h * .20
    clip = f"{view_name}-sleeve-{side}"
    accent, light, dark = option["accent"], option["highlight"], option["shadow"]
    # A short raised plate and two rivets create a readable shoulder silhouette
    # while staying within the existing sleeve attachment and body outline.
    pts = [(x-w*.39,y-h*.08),(x+w*.32,y-h*.02),(x+w*.40,y+h*.25),(x+w*.04,y+h*.38),(x-w*.36,y+h*.20)]
    points = " ".join(f"{px:.1f},{py:.1f}" for px,py in pts)
    plate=option['pauldron']
    out=[f'<g clip-path="url(#{clip})"><polygon points="{points}" fill="{plate}" stroke="{accent}" stroke-width="8" stroke-linejoin="miter"/>']
    motif=option['motif']
    if motif == 'sunburst':
        out.append(f'<path d="M{x-w*.28:.1f},{y+h*.15:.1f} L{x-w*.15:.1f},{y-h*.015:.1f} L{x:.1f},{y+h*.12:.1f} L{x+w*.15:.1f},{y-h*.015:.1f} L{x+w*.28:.1f},{y+h*.15:.1f}" fill="none" stroke="{light}" stroke-width="6" stroke-linejoin="miter"/>')
    elif motif == 'crescent':
        out.append(f'<path d="M{x+w*.10:.1f},{y-h*.005:.1f} Q{x-w*.25:.1f},{y+h*.07:.1f} {x-w*.10:.1f},{y+h*.30:.1f} Q{x-w*.22:.1f},{y+h*.08:.1f} {x+w*.10:.1f},{y-h*.005:.1f} Z" fill="{light}" stroke="{dark}" stroke-width="4"/>')
    elif motif == 'scales':
        for k in (-1,0,1):
            xx=x+k*w*.18
            out.append(f'<path d="M{xx-w*.10:.1f},{y+h*.06:.1f} Q{xx:.1f},{y+h*.28:.1f} {xx+w*.10:.1f},{y+h*.06:.1f} L{xx+w*.06:.1f},{y-h*.005:.1f} Z" fill="{light}" stroke="{dark}" stroke-width="4"/>')
    elif motif == 'flame':
        out.append(f'<path d="M{x-w*.22:.1f},{y+h*.20:.1f} L{x-w*.12:.1f},{y-h*.03:.1f} L{x-w*.015:.1f},{y+h*.18:.1f} L{x+w*.12:.1f},{y-h*.02:.1f} L{x+w*.24:.1f},{y+h*.21:.1f}" fill="none" stroke="{light}" stroke-width="6" stroke-linejoin="miter"/>')
    elif motif == 'imperial':
        out.append(f'<path d="M{x-w*.23:.1f},{y+h*.18:.1f} L{x-w*.15:.1f},{y-h*.03:.1f} L{x:.1f},{y+h*.10:.1f} L{x+w*.17:.1f},{y-h*.02:.1f} L{x+w*.25:.1f},{y+h*.18:.1f}" fill="none" stroke="{light}" stroke-width="6" stroke-linejoin="miter"/>')
    else:
        out.append(f'<path d="M{x-w*.13:.1f},{y+h*.05:.1f} L{x:.1f},{y-h*.015:.1f} L{x+w*.15:.1f},{y+h*.10:.1f}" fill="none" stroke="{light}" stroke-width="6"/>')
    out.append(f'<path d="M{x-w*.26:.1f},{y+h*.16:.1f} L{x:.1f},{y+h*.06:.1f} L{x+w*.25:.1f},{y+h*.16:.1f} M{x-w*.24:.1f},{y+h*.25:.1f} L{x:.1f},{y+h*.32:.1f} L{x+w*.23:.1f},{y+h*.25:.1f}" fill="none" stroke="{light}" stroke-width="5" stroke-linejoin="miter"/><circle cx="{x:.1f}" cy="{y+h*.19:.1f}" r="{max(3,w*.026):.1f}" fill="{accent}" stroke="{dark}" stroke-width="2"/></g>')
    return ''.join(out)


def add_ornaments(svg: str, option: dict) -> str:
    parts = ['<g id="selection-ornaments">']
    for view_name, data in builder.VIEWS.items():
        parts.append(crest_fragment(option, view_name, data["body"]))
        for side, sleeve in enumerate(data["sleeves"]):
            parts.append(shoulder_fragment(option, view_name, sleeve, side))
    parts.append('</g>')
    return svg.replace('</svg>', ''.join(parts) + '</svg>')


def recolored_svg(option: dict) -> str:
    source = builder.make_svg(option["family"])
    pattern = re.compile(r'#[0-9a-fA-F]{6}')
    source = pattern.sub(lambda m: recolor(m.group(0), option, option["family"]), source)
    return add_ornaments(source, option)


def export_template(svg: str, option_id: str) -> Image.Image:
    source_dir = OUT / 'source'
    source_dir.mkdir(parents=True, exist_ok=True)
    svg_path = source_dir / f'{option_id}.svg'
    png_path = source_dir / f'{option_id}-sheet.png'
    svg_path.write_text(svg + '\n')
    subprocess.run([
        'inkscape', str(svg_path), '--export-filename=' + str(png_path),
        f'--export-width={builder.SIZE[0]}', f'--export-height={builder.SIZE[1]}'
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with Image.open(png_path) as im:
        return im.convert('RGBA')


def compose_pose(compositor, surface, frame):
    outfit = surface.render('leatherArmor', frame)
    base_parts = [
        'p1-eight-way-lower-v1',
        'p1-eight-way-hair-chestnut-v1',
        'p1-eight-way-face-blue-v1',
        'p1-eight-way-weapon-v1',
    ]
    base_layers = dict(compositor.layers('p1-eight-way-base-v1', base_parts,
                                         frame['direction'], frame['clip'], frame['frame']))
    base_layers.update(outfit)
    result = Image.new('RGBA', tuple(compositor.canvas))
    for slot in frame['drawOrder']:
        if slot in base_layers:
            result.alpha_composite(base_layers[slot])
    return result


def background_preview(image: Image.Image, scale=2):
    sprite = image.resize((CANVAS[0]*scale, CANVAS[1]*scale), Image.Resampling.NEAREST)
    bg = Image.new('RGBA', sprite.size, (*BACKGROUND, 255))
    bg.alpha_composite(sprite)
    return bg


def load_font(size: int):
    for path in [
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_board(entries):
    cell_w, cell_h = 400, 560
    board = Image.new('RGB', (cell_w*3, cell_h*2), '#17251d')
    draw = ImageDraw.Draw(board)
    title_font = load_font(22)
    sub_font = load_font(15)
    note_font = load_font(14)
    for index, entry in enumerate(entries):
        row, col = divmod(index, 3)
        x, y = col*cell_w, row*cell_h
        draw.rounded_rectangle((x+8,y+8,x+cell_w-8,y+cell_h-8), radius=10,
                               fill='#20372a', outline='#b59a57', width=2)
        title = entry['option']['label']
        material = entry['option']['material']
        draw.text((x+18,y+16),title,font=title_font,fill='#f3e8c4')
        draw.text((x+18,y+48),material,font=sub_font,fill='#c8d3c9')
        sprite = entry['idle'].convert('RGBA')
        bbox = sprite.getchannel('A').getbbox()
        sprite = sprite.crop(bbox)
        # Fit the same entire body crop to every cell; never clip sword, boots,
        # or the lower edge of the armor when comparing the designs.
        scale = min(3.0, 232 / sprite.width, 390 / sprite.height)
        sprite = sprite.resize((round(sprite.width*scale),round(sprite.height*scale)),Image.Resampling.NEAREST)
        px = x + (cell_w-sprite.width)//2
        py = y + 80 + (390-sprite.height)//2
        board_rgba = board.convert('RGBA')
        board_rgba.alpha_composite(sprite,(px,py))
        board = board_rgba.convert('RGB')
        draw = ImageDraw.Draw(board)
        description = entry['option']['description']
        # Split long Chinese copy at a stable character count for the 3×2 board.
        lines = [description[i:i+22] for i in range(0,len(description),22)]
        for line_no,line in enumerate(lines[:2]):
            draw.text((x+18,y+cell_h-50+line_no*20),line,font=note_font,fill='#e3d6ad')
    return board


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    motion = json.loads(MOTION.read_text())
    down_idle = next(f for f in motion['frames'] if (f['direction'],f['clip'],f['frame']) == ('down','idle',0))
    walk_frames = [next(f for f in motion['frames'] if (f['direction'],f['clip'],f['frame']) == ('down','walk',n)) for n in range(1,9)]
    compositor = builder.compose_module.Compositor(ROOT, CATALOG, MOTION)
    rendered=[]
    option_dir=OUT/'options';option_dir.mkdir(parents=True,exist_ok=True)
    for option in OPTIONS:
        template=export_template(recolored_svg(option),option['id'])
        surface=builder.surface_module.ArmorSurface(ROOT)
        surface.sheet=template
        surface.patterns={}
        idle=compose_pose(compositor,surface,down_idle)
        rendered.append({'option':option,'idle':idle})
        # Individual 2x stills are the selection source; the GIFs show the
        # selected pattern moving on the existing real down-facing gait.
        background_preview(idle,2).save(option_dir/f"{option['id']}-idle-2x.png")
        frames=[]
        for motion_frame in walk_frames:
            pose=compose_pose(compositor,surface,motion_frame)
            frames.append(background_preview(pose,2).convert('P',palette=Image.Palette.ADAPTIVE,colors=256))
        frames[0].save(option_dir/f"{option['id']}-walk-120ms.gif",save_all=True,
                       append_images=frames[1:],duration=[120]*8,loop=0,optimize=False,disposal=2)
    board=make_board(rendered)
    board.save(OUT/'selection-board.png')
    descriptions={
        'status':'concept selection only; no production outfit package or user art approval',
        'scope':'Each option uses the same current P1 base body, lower outfit, hair, face, back sword and down-facing motion. Only the new armor surface design changes.',
        'motionPreview':'Down-facing walk; 8 frames × 120ms, rendered from the existing registered motion sampler. Full 8-direction/104-pose packages are not included until a design is selected.',
        'source':'Editable SVG concepts rasterized through the project armor surface sampler and composed using the real P1 compositor.',
        'options':[{'id':o['id'],'family':o['family'],'label':o['label'],'material':o['material'],'description':o['description'],'idle':f"options/{o['id']}-idle-2x.png",'walkGIF':f"options/{o['id']}-walk-120ms.gif",'sourceSVG':f"source/{o['id']}.svg"} for o in OPTIONS],
    }
    (OUT/'concepts.json').write_text(json.dumps(descriptions,ensure_ascii=False,indent=2)+'\n')
    readme='''# B5盔甲新造型候选 · 先选造型，再扩完整方向\n\n上一版星辉甲和龙纹甲过于朴素，用户要求重新出几款供选择。本页用项目当前P1人物、比例、下装、发型、五官、背剑和动作，只替换盔甲设计，不引入新人物或改变步态。\n\n![六款造型选择板](selection-board.png)\n\n## 六款正常速度预览\n\n每段GIF均为真实P1合成，正下行走8帧×120ms。它们是正面风格候选，不代表完整八向资源已经制作；用户选定后，再为选中的款式扩展104个姿势并检查八向。\n\n| 选项 | 造型方向 | 正下正常速度GIF | 放大站姿 |\n| --- | --- | --- | --- |\n'''
    for option in OPTIONS:
        readme += f"| {option['label']} | {option['material']} | [GIF](options/{option['id']}-walk-120ms.gif) | [2×站姿](options/{option['id']}-idle-2x.png) |\n"
    readme += '\n认可状态仍为待选择；六款均不自动替换正式资源。可按字母告诉我保留哪些，例如“星辉选C、龙纹选A”。\n'
    (OUT/'README.md').write_text(readme)
    print(json.dumps({'options':len(OPTIONS),'board':str(OUT/'selection-board.png'),'gifs':len(OPTIONS),'gifFramesPerOption':8,'status':'concept-only'},ensure_ascii=False))


if __name__ == '__main__':
    main()
