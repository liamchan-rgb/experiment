#!/usr/bin/env python3
"""Native front SVG authoring helpers for the selected B clothes.

No concept-board pixels, old garment pixels, body edits, or motion edits are
used to paint the clothes. The eight-way exporter handles true layer order,
registration, master PNGs, pose maps and reviews.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = Path('Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2')
PARTS = ROOT / 'Art/Parts/P1-v1/chat-apparel-v2'
REVIEW = ROOT / 'Art/Review/P1/chat-apparel-v2-b-front-r1'
SLOTS = ['outfit.sleeve.right', 'outfit.sleeve.left',
         'outfit.hem.front', 'outfit.torso']
SOURCE = '615c229737ed3f4381b47a860ae8069854fba634'
MOTION_SHA = 'f1926c10a4eb1cb8f1935157663bd22155e8444eae37ce64562453fc075e96ba'
PALETTES = {
    'starlightArmor': {
        'ink':'#111822', 'clothShadow':'#1c253c', 'cloth':'#29374f',
        'clothLight':'#394c68', 'metalShadow':'#3e536c', 'metal':'#708da7',
        'metalLight':'#b4d1de', 'metalEdge':'#e3eeeb', 'goldShadow':'#715038',
        'gold':'#b99856', 'goldLight':'#e5cb85', 'gemShadow':'#1d4c7a',
        'gem':'#3793ba', 'gemLight':'#a1e3e9',
    },
    'dragonArmor': {
        'ink':'#1b191b', 'clothShadow':'#30262a', 'cloth':'#52333b',
        'clothLight':'#89515a', 'metalShadow':'#303138', 'metal':'#484b50',
        'metalLight':'#68696b', 'metalEdge':'#92918a', 'goldShadow':'#795235',
        'gold':'#b98b55', 'goldLight':'#e1b978', 'gemShadow':'#39212a',
        'gem':'#854c4e', 'gemLight':'#ac6a5c',
    },
}


class Paint:
    def __init__(self, palette):
        self.palette = palette
        self.shapes = []

    def color(self, key):
        return self.palette.get(key, key)

    def poly(self, points, color):
        points = ' '.join(f'{x},{y}' for x, y in points)
        self.shapes.append(f'<polygon points="{points}" fill="{self.color(color)}"/>')

    def rect(self, x, y, w, h, color):
        self.shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{self.color(color)}"/>')

    def line(self, points, color, width=1):
        points = ' '.join(f'{x},{y}' for x, y in points)
        self.shapes.append(f'<polyline points="{points}" fill="none" stroke="{self.color(color)}" stroke-width="{width}" stroke-linejoin="miter"/>')

    def result(self):
        return ''.join(self.shapes)


def torso(item):
    p = Paint(PALETTES[item])
    p.poly([(118,128),(120,129),(120,132),(125,135),(132,135),
            (138,132),(138,128),(141,130),(141,133),(145,135),
            (146,143),(143,152),(143,158),(145,162),(145,167),
            (113,167),(113,162),(115,157),(114,150),(112,143),
            (112,136),(116,133),(116,130)], 'ink')
    p.poly([(118,131),(123,136),(134,136),(140,131),(140,135),
            (144,137),(144,143),(141,152),(141,159),(143,164),
            (115,164),(117,157),(116,149),(114,142),(114,137)], 'cloth')
    p.poly([(115,139),(119,138),(122,147),(121,159),(117,161),
            (118,155)], 'clothLight')
    p.poly([(138,138),(143,137),(143,143),(140,153),(141,160),
            (136,160),(136,148)], 'clothShadow')
    if item == 'starlightArmor':
        # A fitted pair of vertical metal facings, not a barrel breastplate.
        p.poly([(119,134),(124,139),(124,144),(127,150),(126,160),
                (122,160),(121,150),(118,144),(116,137)], 'metalShadow')
        p.poly([(119,136),(122,140),(122,145),(125,151),(124,159),
                (122,149),(119,144),(117,137)], 'metalLight')
        p.line([(119,136),(122,140),(122,145),(125,151)], 'metalEdge')
        p.poly([(138,134),(134,139),(134,144),(131,150),(131,160),
                (135,160),(136,150),(139,144),(141,137)], 'metalShadow')
        p.line([(138,136),(135,140),(135,145),(132,151),(132,159)], 'metal')
        # Astrolabe collar is connected to the facings and collar itself.
        p.line([(118,130),(119,133),(123,136),(134,136),(138,133),(139,130)], 'metalLight')
        p.line([(119,130),(120,133),(124,135)], 'metalEdge')
        p.line([(121,135),(124,138),(125,141),(132,141),(134,138),(137,135)], 'goldShadow')
        p.line([(125,136),(132,136),(135,139),(135,142),(132,145),
                (125,145),(122,142),(122,139),(125,136)], 'gold')
        p.line([(125,136),(131,136),(133,138)], 'goldLight')
        p.line([(128,134),(128,146)], 'gold')
        p.line([(122,140),(135,140)], 'gold')
        p.poly([(128,137),(130,140),(128,143),(126,140)], 'gemShadow')
        p.poly([(128,138),(129,140),(128,142),(127,140)], 'gem')
        p.rect(128,138,1,2,'gemLight')
        p.line([(128,147),(128,160)], 'ink')
        for y in [151,156]:
            p.rect(126,y,5,2,'goldShadow')
            p.rect(126,y,4,1,'gold')
            p.rect(126,y,1,1,'goldLight')
        # Two narrow straps; buckle remains part of the torso layer.
        p.rect(114,160,30,3,'ink')
        p.rect(115,160,28,1,'gold')
        p.rect(115,161,28,1,'clothLight')
        p.rect(114,164,30,3,'ink')
        p.rect(115,164,28,1,'goldShadow')
        p.rect(115,165,28,1,'gold')
        p.rect(126,160,6,6,'goldShadow')
        p.rect(126,160,5,1,'goldLight')
        p.rect(126,160,1,5,'gold')
        p.rect(130,161,1,4,'gold')
        p.rect(127,164,3,1,'gold')
        p.rect(128,162,2,1,'clothShadow')
    else:
        # Dark cast plate, burgundy side inserts and an inset dragon sign.
        p.poly([(119,134),(127,137),(131,137),(139,134),(141,140),
                (138,149),(129,154),(119,149),(117,140)], 'ink')
        p.poly([(120,135),(127,138),(131,138),(138,135),(139,141),
                (136,148),(129,152),(121,148),(119,141)], 'metal')
        p.poly([(129,139),(138,136),(139,141),(136,148),(129,151)], 'metalShadow')
        p.poly([(120,137),(124,138),(125,141),(121,145),(119,141)], 'metalLight')
        p.line([(119,135),(127,138),(131,138),(138,135)], 'gold')
        p.line([(120,136),(123,137)], 'goldLight')
        p.line([(120,147),(129,152),(137,147)], 'goldShadow')
        p.line([(120,147),(129,152)], 'goldLight')
        p.poly([(121,151),(129,155),(137,151),(137,158),(130,162),
                (121,158)], 'metalShadow')
        p.poly([(122,152),(128,155),(128,160),(122,157)], 'metal')
        p.line([(120,151),(119,155),(120,160)], 'goldShadow')
        p.line([(138,151),(139,155),(138,159)], 'goldShadow')
        p.line([(118,130),(119,133),(125,136),(132,136),(138,133),(139,130)], 'gold')
        p.line([(119,130),(120,132),(124,134)], 'goldLight')
        # Seven-pixel head, nose, swept horn and neck: no detached badge.
        p.poly([(127,140),(131,139),(130,141),(133,141),(132,142),
                (133,144),(132,146),(130,147),(131,144),(129,143),
                (126,144),(125,143),(126,142),(124,142)], 'gold')
        p.rect(127,141,2,1,'goldLight')
        p.rect(128,142,1,1,'ink')
        p.line([(129,146),(128,148)], 'goldShadow')
        # Slanted leather belt, continuous at sides, not an enlarged abdomen.
        p.poly([(113,162),(143,157),(145,161),(114,167)], 'ink')
        p.poly([(114,163),(143,158),(144,160),(114,166)], 'goldShadow')
        p.line([(115,163),(141,159)], 'gold')
        p.poly([(134,158),(140,157),(141,162),(135,163)], 'gold')
        p.poly([(135,159),(139,158),(140,161),(136,162)], 'clothShadow')
        p.rect(137,160,2,1,'goldLight')
    return p.result()


def sleeve(item, side):
    p = Paint(PALETTES[item])
    # This is the character's RIGHT chain: (114,136) -> (108,153) -> (106,167).
    # Own-left uses a separate SVG group and a darker palette under fixed light.
    p.poly([(113,131),(119,133),(121,140),(117,145),(115,153),
            (113,158),(112,165),(110,168),(102,166),(102,161),
            (103,155),(105,150),(107,143),(107,137)], 'ink')
    p.poly([(113,133),(118,135),(119,140),(115,146),(113,153),
            (111,157),(110,165),(104,164),(104,159),(106,151),
            (109,144),(109,138)], 'cloth')
    p.poly([(111,139),(115,139),(112,149),(110,154),(106,157),
            (108,149)], 'clothLight')
    p.poly([(117,140),(118,142),(115,149),(114,154),(112,156),
            (111,153),(114,144)], 'clothShadow')
    if item == 'starlightArmor':
        p.poly([(113,131),(117,132),(121,136),(120,142),
                (107,142),(106,140),(108,135)], 'ink')
        p.poly([(113,132),(117,133),(120,136),(119,140),
                (108,141),(108,138),(110,135)], 'metalShadow')
        p.poly([(113,133),(116,134),(117,137),(109,139),
                (110,136)], 'metal')
        p.line([(109,137),(113,133),(116,134),(119,136)], 'metalLight')
        p.line([(108,140),(119,139)], 'metalLight')
        p.line([(114,134),(115,138),(115,140)], 'metalShadow')
        # Sleeve etching follows its arm instead of remaining in the torso.
        p.line([(107,147),(113,149),(112,152),(106,150),(107,147)], 'metal')
        p.line([(108,148),(112,149)], 'metalLight')
        p.poly([(105,154),(112,156),(112,163),(110,166),(102,164),
                (103,158)], 'ink')
        p.poly([(105,155),(111,157),(110,164),(103,163),(104,158)], 'metalShadow')
        p.poly([(105,156),(107,156),(106,162),(104,162)], 'metalLight')
        p.line([(108,157),(110,158),(109,163)], 'metal')
        p.line([(103,164),(110,166)], 'metalLight')
        p.line([(104,165),(109,166)], 'goldShadow')
    else:
        # Folded short armor fins, bounded to the shoulder/upper arm.
        p.poly([(113,131),(118,133),(121,136),(120,141),
                (109,142),(106,145),(107,139),(105,140),(108,135)], 'ink')
        p.poly([(113,132),(117,134),(120,136),(118,140),
                (110,140),(108,142),(109,137),(107,138),(110,135)], 'metalShadow')
        p.poly([(111,135),(117,135),(118,138),(110,139)], 'metal')
        p.line([(107,138),(110,135),(113,133),(117,134),(120,136)], 'gold')
        p.line([(109,136),(113,133),(115,134)], 'goldLight')
        p.line([(110,140),(118,139)], 'goldShadow')
        p.poly([(110,140),(117,140),(116,144),(112,146),
                (108,149)], 'ink')
        p.poly([(111,141),(116,141),(114,144),(110,147)], 'clothLight')
        p.line([(111,141),(110,146)], 'gold')
        p.line([(107,149),(113,151)], 'goldShadow')
        p.poly([(105,154),(112,156),(111,163),(110,166),
                (102,164),(103,158)], 'ink')
        p.poly([(105,155),(111,157),(110,164),(103,163),(104,158)], 'metal')
        p.poly([(108,157),(111,157),(110,163),(108,163)], 'metalShadow')
        p.line([(105,155),(104,159),(104,162)], 'gold')
        p.line([(104,164),(110,166)], 'gold')
    body = p.result()
    if side == 'left':
        # Geometric mirroring of this symmetric front only; upper-left lighting
        # is explicitly repainted through shade substitution, never flipped.
        replacements = [('metalEdge','metalLight'),('metalLight','metal'),
                        ('metal','metalShadow'),('clothLight','cloth'),
                        ('goldLight','gold'),('gold','goldShadow')]
        for n, (a,b) in enumerate(replacements):
            body = body.replace(p.palette[a], f'@@SHADE{n}@@')
        for n, (a,b) in enumerate(replacements):
            body = body.replace(f'@@SHADE{n}@@', p.palette[b])
        body = '<g transform="translate(258 0) scale(-1 1)">'+body+'</g>'
    return body


def hem(item):
    p=Paint(PALETTES[item])
    if item == 'starlightArmor':
        pieces=[([(115,164),(125,165),(123,180),(120,182),(111,178)],
                 [(116,166),(123,166),(121,179),(119,180),(113,177)]),
                ([(132,165),(142,164),(147,178),(138,182),(134,180)],
                 [(134,166),(141,166),(145,177),(139,180),(136,179)]),
                ([(125,164),(133,164),(135,180),(129,184),(123,180)],
                 [(127,166),(131,166),(133,179),(129,182),(125,179)])]
        for i,(outer,inner) in enumerate(pieces):
            p.poly(outer,'ink');p.poly(inner,'cloth' if i!=1 else 'clothShadow')
        p.line([(115,167),(112,177),(120,181),(122,179)],'metal')
        p.line([(116,167),(114,176),(119,178)],'clothLight')
        p.line([(142,167),(146,177),(138,181),(136,179)],'metalShadow')
        p.line([(125,167),(124,180),(129,183),(134,180),(133,167)],'metal')
        p.line([(126,167),(125,179),(129,182)],'metalLight')
        p.line([(129,166),(129,177)],'goldShadow')
        p.poly([(129,175),(130,178),(132,179),(130,180),(129,182),
                (128,180),(126,179),(128,178)],'gold')
        p.rect(129,177,1,2,'goldLight')
        for x,y in [(117,175),(140,175)]:
            p.rect(x,y,1,3,'goldShadow');p.rect(x-1,y+1,3,1,'gold')
    else:
        # Two short independent side tassets, with a short dark central plate.
        for outer,inner in [
            ([(114,164),(126,166),(121,178),(118,181),(111,176)],
             [(115,166),(124,167),(120,177),(118,179),(113,175)]),
            ([(132,166),(143,163),(147,175),(140,180),(136,178)],
             [(134,167),(142,165),(145,174),(140,178),(138,176)])]:
            p.poly(outer,'ink');p.poly(inner,'cloth')
        p.poly([(115,166),(119,167),(116,174),(113,175)],'clothLight')
        p.line([(114,166),(112,175),(118,180)],'gold')
        p.line([(119,168),(117,176)],'goldShadow')
        p.line([(142,166),(146,175),(140,179)],'goldShadow')
        p.line([(138,168),(142,174)],'goldShadow')
        p.poly([(124,165),(134,164),(135,174),(130,178),(124,175)],'ink')
        p.poly([(126,166),(132,166),(133,173),(130,176),(126,174)],'metalShadow')
        p.line([(125,167),(125,174),(130,177)],'goldShadow')
    return p.result()


def write_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')



if __name__ == '__main__':
    print('Front artwork helper. Export every direction with scripts/build-chat-apparel-b-eight-way.py')
