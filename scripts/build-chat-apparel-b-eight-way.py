#!/usr/bin/env python3
"""Selected B clothes: camera-aware SVG masters, then the existing walk surface.

Native front SVG remains hand authored. Other cameras project separately built
front/side/back garment surfaces; no flattened front, raster concept cutout, or
repainted person is used. Original rig, body, head, hands and gait are read-only.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import maximum_filter

ROOT=Path(__file__).resolve().parents[1]
PARTS=ROOT/'Art/Parts/P1-v1/chat-apparel-v2'
REVIEW=ROOT/'Art/Review/P1/chat-apparel-v2-b-eight-way-r1'
MOTION=ROOT/'Art/Integration/P1-modular-eight-way-v1/motion.json'
BASE='p1-eight-way-base-v1'
DIRECTIONS=['down','down-left','left','up-left','up','up-right','right','down-right']
VIEWS=['front','front-quarter-left','profile-left','rear-quarter-left','back',
       'rear-quarter-right','profile-right','front-quarter-right']
WAIST=dict(zip(DIRECTIONS,[164,161,164,159,159,159,164,161]))
SLOTS=['outfit.torso','outfit.sleeve.left','outfit.sleeve.right','outfit.hem.front']
PROFILE=ROOT/'Art/Standards/P1-Parts-v1/profile.json'
SOURCE='615c229737ed3f4381b47a860ae8069854fba634'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
    return m


front=load('chat_b_front',ROOT/'scripts/build-chat-apparel-b-front.py')
surface_module=load('chat_b_existing_surface',ROOT/'scripts/armor-shared-surface-r4.py')
compose=load('chat_b_existing_compositor',ROOT/'scripts/compose-character-parts.py')


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(im,path,profile=True):
    path.parent.mkdir(parents=True,exist_ok=True)
    a=np.asarray(im.convert('RGBA')).copy();a[a[:,:,3]==0]=0
    args={'icc_profile':Path('/usr/share/color/icc/sRGB.icc').read_bytes()} if profile else {}
    Image.fromarray(a).save(path,**args)


class Surface(surface_module.ArmorSurface):
    """Same published kinematics; replace only the registered garment input."""
    def __init__(self):
        self.root=ROOT
        self.motion=json.loads(MOTION.read_text())
        self.rests={f['direction']:f for f in self.motion['frames'] if f['clip']=='idle'}
        self.base=ROOT/'Art/Parts/P1-v1/eight-way-v1/base'
        base=json.loads((self.base/'asset.json').read_text())
        self.body={(b['direction'],b['clip'],b['frame']):b['layers'] for b in base['bindings']}
        self.marker_cache={};self.patterns={}
        y,x=np.mgrid[115:196:2,88:170:2]
        self.grid=np.c_[x.ravel(),y.ravel()].astype(float)
        self.waist=WAIST

    def fit(self,item,direction):
        key=item,direction
        if key not in self.patterns:
            view=VIEWS[DIRECTIONS.index(direction)]
            self.patterns[key]={slot:Image.open(PARTS/item/f'masters/{view}/{slot}.png').convert('RGBA') for slot in SLOTS}
        return self.patterns[key]

    def render(self,item,frame):
        result=super().render(item,frame)
        # The old profile rig's hidden arm silhouette changes independently
        # of its sparse joint markers. Register a cloth allowance to that
        # existing semantic silhouette in every pose, under the moving plates.
        # RGB is freshly painted cloth; no skin or old costume RGB is sampled.
        for slot in ['outfit.torso','outfit.sleeve.left','outfit.sleeve.right']:
            lining=pose_lining(item,frame,slot,self)
            lining.alpha_composite(result[slot])
            result[slot]=lining
        # The original rig draws the hands/head last. Keep that order when
        # composing; do not erase hand-shaped holes from the clothing master.
        return result


class Compositor(compose.Compositor):
    def asset(self,identifier):
        if identifier not in self.assets:
            path=self.entries[identifier]
            # Original reference layer PNGs are pinned and checked against Git
            # blob SHAs by the hydration receipt. Their historical ORA sources
            # are not needed to render them. New outfits get the full check.
            errors=compose.contract.check_asset(path,schema_only=not identifier.startswith('p1-chat-'))
            if errors:raise ValueError((identifier,errors))
            data=json.loads(path.read_text())
            self.assets[identifier]=(data,path,{compose.key(b):b for b in data['bindings']})
        return self.assets[identifier]


class Camera:
    def __init__(self,item,direction,joints):
        self.item=item;self.direction=direction;self.joints=joints
        self.p=front.Paint(front.PALETTES[item])
        self.angle=DIRECTIONS.index(direction)*math.pi/4
        self.c=math.cos(self.angle);self.s=math.sin(self.angle)
        self.cx=float(joints['neck'][0]);self.cy=float(joints['neck'][1])
        self.h=WAIST[direction]-self.cy

    def project(self,x,y,z):
        return (round(self.cx+x*self.c-z*self.s),round(self.cy+y-z*.08))

    def poly(self,xyz,color):
        self.p.poly([self.project(*v) for v in xyz],color)

    def line(self,xyz,color,width=1):
        self.p.line([self.project(*v) for v in xyz],color,width)

    def cross(self,w,f,b):
        return [(-w*.70,f),(w*.70,f),(w,f*.45),(w,-b*.45),
                (w*.70,-b),(-w*.70,-b),(-w,-b*.45),(-w,f*.45)]

    def visible(self,index):
        ring=self.cross(14,10,8);a=np.array(ring[index]);b=np.array(ring[(index+1)%8])
        dx,dz=b-a
        return -dz*self.s+dx*self.c>1e-5

    def ring(self,y,w,f,b):
        return [(x,y,z) for x,z in self.cross(w,f,b)]

    def bands(self,y,width,color):
        a=self.ring(y,14.2,9,8);b=self.ring(y+width,14.4,9,8)
        for i in range(8):
            if self.visible(i):self.poly([a[i],a[(i+1)%8],b[(i+1)%8],b[i]],color)

    def torso(self):
        p=self.p;h=self.h
        rings=[self.ring(3,10.8,7,7),self.ring(11,14,10,8),
               self.ring(h-6,11.8,8,7),self.ring(h+3,14.5,9,8)]
        faces=[]
        for i in range(8):
            if not self.visible(i):continue
            for k in range(len(rings)-1):
                q=[rings[k][i],rings[k][(i+1)%8],rings[k+1][(i+1)%8],rings[k+1][i]]
                depth=sum(x*self.s+z*self.c for x,y,z in q)
                faces.append((depth,i,k,q))
        for _,i,k,q in sorted(faces):
            points=[self.project(*v) for v in q]
            left=sum(v[0] for v in points)/4<self.cx
            material=('clothLight' if left else 'cloth') if i in [1,2,3,5,6,7] else 'cloth'
            if self.item=='dragonArmor' and i in [0,4]:material='metal' if left else 'metalShadow'
            p.poly(points,'ink')
            p.poly(points,material)
        # Side seams/longitudinal trim are distinct projected side surfaces.
        for sign in [-1,1]:
            x=sign*12.1
            side=[(x,8,5),(sign*11.1,h-7,5),(sign*13.2,h+1,5)]
            self.line(side,'metalShadow' if self.item=='starlightArmor' else 'goldShadow')
        # Collar ring: short guard, no skin/face pixels inside a garment layer.
        top=self.ring(-1,8.5,4,4);low=self.ring(4,9.2,5,4.5)
        for i in range(8):
            if self.visible(i):
                self.poly([top[i],top[(i+1)%8],low[(i+1)%8],low[i]],'ink')
                self.line([top[i],top[(i+1)%8]],'metalLight' if self.item=='starlightArmor' else 'gold')
                self.line([low[i],low[(i+1)%8]],'clothLight')
        if self.c>0.05:
            # These details live only on the FRONT face; they disappear in
            # true profile and cannot turn into a badge on the character back.
            z=10.2
            if self.item=='starlightArmor':
                for sign in [-1,1]:
                    self.poly([(sign*8,5,7.5),(sign*6,11,z),(sign*3,h-9,8.4),
                               (sign*3,h-2,8.7),(sign*6,h-2,8.7),(sign*7,16,9.4)],'metalShadow')
                    self.line([(sign*8,5,7.6),(sign*6,11,z+.2),(sign*3,h-9,8.6),
                               (sign*3,h-2,9)],'metalLight' if sign==-1 else 'metal')
                ring=[(-3,4,8), (3,4,8),(5,7,9),(5,10,z),
                      (3,12,z),(-3,12,z),(-5,10,z),(-5,7,9),(-3,4,8)]
                self.line(ring,'gold')
                self.line([(0,3,8),(0,13,z)],'gold')
                self.line([(-5,8,z),(5,8,z)],'gold')
                self.poly([(0,5,z+.1),(2,8,z+.1),(0,11,z+.1),(-2,8,z+.1)],'gem')
                self.line([(-1,7,z+.2),(0,6,z+.2)],'gemLight')
                self.line([(0,14,9.5),(0,h-2,9)],'ink')
                for y in [h-13,h-8]:
                    self.line([(-2,y,9),(2,y,9)],'gold')
            else:
                self.poly([(-8,5,8),(0,8,z),(8,5,8),(8,13,z),
                           (0,20,9),(-8,13,z)],'metalShadow')
                self.poly([(-8,6,8),(-2,9,z),(-2,17,9),(-7,13,z)],'metal')
                self.line([(-8,5,8),(0,8,z),(8,5,8)],'gold')
                self.line([(-7,14,z),(0,20,9),(7,14,z)],'goldShadow')
                self.poly([(-1,9,z+.4),(3,8,z+.4),(2,10,z+.4),(4,11,z+.4),
                           (2,12,z+.4),(3,14,z+.4),(1,16,z+.4),(2,13,z+.4),
                           (0,12,z+.4),(-3,13,z+.4),(-4,12,z+.4),(-2,11,z+.4),(-4,11,z+.4)],'gold')
                self.line([(-1,10,z+.6),(0,10,z+.6)],'goldLight')
        elif self.c<-.05:
            # Short back yoke and flexible centre panel; no front emblem.
            z=-8.2
            self.line([(-9,7,z),(-5,10,z),(5,10,z),(9,7,z)],
                      'metal' if self.item=='starlightArmor' else 'goldShadow')
            for x in [-5,5]:
                self.line([(x,11,z),(x*.70,h-3,z)],
                          'metalShadow' if self.item=='starlightArmor' else 'goldShadow')
            self.line([(0,12,z),(0,h-3,z)],'clothShadow')
            if self.item=='starlightArmor':
                self.line([(-2,11,z),(0,13,z),(2,11,z)],'goldShadow')
        if self.item=='starlightArmor':
            self.bands(h-1,2,'ink');self.bands(h-1,1,'goldShadow')
            self.bands(h+2,2,'ink');self.bands(h+2,1,'gold')
            if self.c>0.05:
                self.poly([(-2,h-1,9.4),(2,h-1,9.4),(2,h+4,9.4),(-2,h+4,9.4)],'gold')
                self.poly([(-1,h,9.5),(1,h,9.5),(1,h+2,9.5),(-1,h+2,9.5)],'clothShadow')
        else:
            # Continuous tilted belt, including the actual side/back planes.
            a=self.ring(h+1,14.4,9.1,8.1);b=self.ring(h+5,14.4,9.1,8.1)
            a=[(x,y-x*.12,z) for x,y,z in a];b=[(x,y-x*.12,z) for x,y,z in b]
            for i in range(8):
                if self.visible(i):
                    self.poly([a[i],a[(i+1)%8],b[(i+1)%8],b[i]],'goldShadow')
                    self.line([a[i],a[(i+1)%8]],'gold')
            if self.c>.05:
                self.poly([(5,h,9.4),(9,h-.5,9.4),(9,h+3,9.4),(5,h+3.5,9.4)],'gold')
                self.poly([(6,h+.5,9.5),(8,h,9.5),(8,h+2,9.5),(6,h+2.5,9.5)],'clothShadow')
        return p.result()

    def hem(self):
        self.p=front.Paint(front.PALETTES[self.item]);p=self.p;h=self.h
        # Separate short tassets around a shallow volume, with slits. The front
        # central star panel is longer, but never becomes a new cape/back slot.
        r=self.cross(14.5,9,8);panels=[]
        for i in range(8):
            if not self.visible(i):continue
            ax,az=r[i];bx,bz=r[(i+1)%8]
            inset=.10
            x0=ax*(1-inset)+bx*inset;z0=az*(1-inset)+bz*inset
            x1=bx*(1-inset)+ax*inset;z1=bz*(1-inset)+az*inset
            length=(18 if i==0 else 15) if self.item=='starlightArmor' else (10 if i==0 else 14)
            q=[(x0,h+1,z0),(x1,h+1,z1),(x1*1.10,h+length-2,z1*1.10),
               ((x0+x1)*.55,h+length,(z0+z1)*.55),(x0*1.10,h+length-2,z0*1.10)]
            depth=sum(x*self.s+z*self.c for x,y,z in q)
            panels.append((depth,i,q))
        for _,i,q in sorted(panels):
            self.poly(q,'ink')
            inner=[(x*.97,y if y<h+5 else y-1,z*.97) for x,y,z in q]
            self.poly(inner,'cloth' if self.item=='starlightArmor' else ('metalShadow' if i in [0,4] else 'cloth'))
            trim='metal' if self.item=='starlightArmor' else 'goldShadow'
            self.line(q[1:]+q[:1],trim)
            if self.item=='starlightArmor' and i==0:
                z=10.2
                self.line([(0,h+4,z),(0,h+13,z)],'goldShadow')
                self.poly([(0,h+11,z),(1,h+13,z),(3,h+14,z),(1,h+15,z),
                           (0,h+17,z),(-1,h+15,z),(-3,h+14,z),(-1,h+13,z)],'gold')
        return p.result()


def sleeve(item,direction,joints,side):
    p=front.Paint(front.PALETTES[item]);side=side.title()
    S,E,W=[np.array(joints[n+side],float) for n in ['shoulder','elbow','wrist']]
    screen_left=S[0]<joints['neck'][0]
    near=side==('Right' if direction in ['right','up-right','down-right'] else 'Left')
    far_profile=direction in ['left','right'] and not near
    upper=(E-S)/np.linalg.norm(E-S);lower=(W-E)/np.linalg.norm(W-E)
    def normal(v):return np.array([-v[1],v[0]])
    n1=normal(upper);n2=normal(lower)
    def points(items):return [tuple(np.rint(v).astype(int)) for v in items]
    width=4.9 if near else 4.3
    outline=[S-upper*2-n1*width,S-upper*2+n1*width,E+n1*4.4,
             W+n2*3.8,W+lower*.6-n2*3.8,E-n1*4.4]
    p.poly(points(outline),'ink')
    core=[S-n1*(width-1),S+n1*(width-1),E+n1*3.4,
          W-lower*.6+n2*2.8,W-lower*.6-n2*2.8,E-n1*3.4]
    p.poly(points(core),'cloth' if near else 'clothShadow')
    p.line(points([S+np.array([-2,1]),E+np.array([-2,-1]),W-lower*3+np.array([-2,0])]),
           'clothLight' if near else 'cloth')
    # Elbow remains flexible; bracer is a continuous tapered piece below it.
    a=E+lower*3;b=W-lower*1.2
    bracer=[a-n2*4,a+n2*4,b+n2*3.8,b+lower-n2*3.8]
    p.poly(points(bracer),'ink')
    p.poly(points([a-n2*3,a+n2*3,b+n2*2.8,b-n2*2.8]),'metalShadow' if item=='starlightArmor' else 'metal')
    tint='metalLight' if item=='starlightArmor' else 'gold'
    if not screen_left:tint='metal' if item=='starlightArmor' else 'goldShadow'
    leading=-n2 if n2[0]>0 else n2
    p.line(points([a+leading*2.5,b+leading*2.4]),tint)
    p.line(points([b-n2*3.5,b+n2*3.5]),'metal' if item=='starlightArmor' else 'goldShadow')
    # Each cap belongs to this sleeve and moves with this actual arm chain.
    outer=-1 if screen_left else 1;ox,oy=S
    if item=='starlightArmor':
        cap=[(ox-5,oy-3),(ox+2,oy-4),(ox+6,oy),(ox+6,oy+5),
             (ox-6,oy+6),(ox-7,oy+2)]
        p.poly(cap,'ink')
        p.poly([(ox-4,oy-2),(ox+2,oy-3),(ox+5,oy),(ox+5,oy+4),
                (ox-5,oy+5),(ox-6,oy+2)],'metalShadow')
        p.poly([(ox-4,oy-1),(ox+1,oy-2),(ox+3,oy),(ox-4,oy+2)],
               'metal' if screen_left else 'metalShadow')
        p.line([(ox-5,oy+1),(ox-3,oy-2),(ox+1,oy-3),(ox+4,oy-1)],tint)
        p.line([(ox-5,oy+4),(ox+5,oy+3)],'metal' if near else 'metalShadow')
        a=S+upper*11;b=a+upper*3
        p.line(points([a-n1*3,a+n1*3,b+n1*3]),'metal' if near else 'metalShadow')
    else:
        cap=[(ox-outer*4,oy-3),(ox+outer*2,oy-4),(ox+outer*7,oy),
             (ox+outer*9,oy+4),(ox+outer*5,oy+3),(ox+outer*7,oy+10),
             (ox+outer*1,oy+7),(ox-outer*4,oy+5)]
        p.poly(cap,'ink')
        p.poly([(ox-outer*3,oy-2),(ox+outer*2,oy-3),(ox+outer*6,oy+1),
                (ox+outer*4,oy+2),(ox+outer*5,oy+8),(ox,oy+6),(ox-outer*3,oy+4)],'clothLight' if near else 'cloth')
        p.poly([(ox-outer*3,oy-2),(ox+outer*2,oy-3),(ox+outer*6,oy+1),
                (ox,oy+2),(ox-outer*3,oy+3)],'metalShadow')
        p.line([(ox-outer*3,oy-2),(ox+outer*2,oy-3),(ox+outer*7,oy+1)],tint)
        p.line([(ox,oy+2),(ox+outer*5,oy+8)],'goldShadow')
    if not near and direction not in ['down','up']:
        # Distant face materials are darker, while highlights still enter from
        # screen upper left; this is a fresh camera source, not a flipped PNG.
        for k in ['metalLight','goldLight']:
            p.shapes=[s.replace(p.palette[k],p.palette['metal' if k=='metalLight' else 'gold']) for s in p.shapes]
    return p.result()


def underlining(item,direction,slot,surface):
    """A new cloth allowance traced from the rig's semantic anatomical region.

    These are editable horizontal SVG runs, never copied skin/undershirt RGB.
    The body silhouette supplies fit; garment surface artwork supplies material.
    Hidden shoulder and armpit fabric stays in the corresponding sleeve group.
    """
    r=surface.joints(surface.rests[direction])
    source_slot='body.torso' if slot=='outfit.torso' else 'body.arm.'+slot.split('.')[-1]
    path=surface.base/surface.body[direction,'idle',0][source_slot]
    alpha=np.asarray(Image.open(path).getchannel('A'))
    # Original profile rasters contain remote alpha=1 interpolation sentinels.
    # They are not garment geometry and must never become opaque cloth specks.
    # This reads the anatomical alpha only; no garment trim/color is thresholded.
    core=alpha>8
    if slot=='outfit.torso':
        # The existing safety shirt begins above the neck marker in oblique
        # views. A fitted high guard collar must cover that actual upper edge.
        core[:int(r['neck'][1])-3]=False
        core[WAIST[direction]+7:]=False
    outline=maximum_filter(core,size=3)
    if slot=='outfit.torso':outline[:int(r['neck'][1])-3]=False
    p=front.Paint(front.PALETTES[item])
    def runs(mask,color):
        for y in np.where(mask.any(1))[0]:
            xs=np.where(mask[y])[0]
            starts=np.r_[0,np.where(np.diff(xs)>1)[0]+1]
            ends=np.r_[starts[1:]-1,len(xs)-1]
            for a,b in zip(starts,ends):p.rect(int(xs[a]),int(y),int(xs[b]-xs[a]+1),1,color)
    runs(outline,'ink')
    runs(core,'cloth' if slot=='outfit.torso' else 'clothShadow')
    # Profile cloth panel follows the actual abdomen, not a guessed box width.
    if slot=='outfit.torso' and direction in ['left','right']:
        edge=[]
        for y in range(int(r['neck'][1])+7,WAIST[direction]):
            x=np.where(core[y])[0]
            if len(x):edge.append((int(x.min()+1 if direction=='left' else x.max()-1),y))
        if edge:p.line(edge,'metalShadow' if item=='starlightArmor' else 'goldShadow')
    return p.result()


def pose_lining(item,frame,slot,surface):
    d=frame['direction'];j=surface.joints(frame);r=surface.joints(surface.rests[d])
    source_slot='body.torso' if slot=='outfit.torso' else 'body.arm.'+slot.split('.')[-1]
    path=surface.base/surface.body[compose.key(frame)][source_slot]
    core=np.asarray(Image.open(path).getchannel('A'))>8
    if slot=='outfit.torso':
        shift=(j['hipLeft'][1]+j['hipRight'][1]-r['hipLeft'][1]-r['hipRight'][1])/2
        core[:round(j['neck'][1])-3]=False
        core[round(WAIST[d]+shift)+7:]=False
    outer=maximum_filter(core,size=3)
    if slot=='outfit.torso':outer[:round(j['neck'][1])-3]=False
    a=np.zeros((256,256,4),dtype=np.uint8)
    def rgba(key):
        h=front.PALETTES[item][key].lstrip('#')
        return [int(h[i:i+2],16) for i in [0,2,4]]+[255]
    a[outer]=rgba('ink')
    a[core]=rgba('cloth' if slot=='outfit.torso' else 'clothShadow')
    return Image.fromarray(a)


def export_masters(item,surface):
    dest=PARTS/item;views=[];sources=[]
    for direction,view in zip(DIRECTIONS,VIEWS):
        joints=surface.joints(surface.rests[direction])
        if direction=='down':
            # The front hand-authored source is the selected C2 construction.
            groups={'outfit.torso':front.torso(item),'outfit.hem.front':front.hem(item),
                    'outfit.sleeve.left':front.sleeve(item,'left'),
                    'outfit.sleeve.right':front.sleeve(item,'right')}
        else:
            c=Camera(item,direction,joints)
            groups={'outfit.torso':c.torso(),'outfit.hem.front':c.hem(),
                    'outfit.sleeve.left':sleeve(item,direction,joints,'left'),
                    'outfit.sleeve.right':sleeve(item,direction,joints,'right')}
            for slot in ['outfit.torso','outfit.sleeve.left','outfit.sleeve.right']:
                groups[slot]=underlining(item,direction,slot,surface)+groups[slot]
        source=dest/f'editable/{view}.svg';source.parent.mkdir(parents=True,exist_ok=True)
        order=[s for s in surface.rests[direction]['drawOrder'] if s in groups]
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" '
                         'viewBox="0 0 256 256" shape-rendering="crispEdges">'
                         +''.join(f'<g id="{s}">{groups[s]}</g>' for s in order)+'</svg>\n')
        paths={}
        for slot in SLOTS:
            path=dest/f'masters/{view}/{slot}.png';path.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(['inkscape',str(source),'--export-id='+slot,'--export-id-only',
                            '--export-area-page','--export-png-antialias=0','--export-width=256',
                            '--export-height=256','--export-filename='+str(path)],check=True,
                           stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            with Image.open(path) as im:save(im,path)
            paths[slot]=path.relative_to(dest).as_posix()
        views.append({'view':view,'referencePose':{'direction':direction,'clip':'idle','frame':0},
                      'layers':paths,'referenceLayerOrder':order})
        sources.append(source.relative_to(dest).as_posix())
    front.write_json(dest/'source/palette.json',{'light':'fixed upper left','colors':front.PALETTES[item]})
    shutil.copyfile('/usr/share/color/icc/sRGB.icc',dest/'source/sRGB.icc')
    (dest/'source/authoring-notes.txt').write_text(
        'Both B designs selected by user; user then requested every direction in one round. '
        'Front is manually authored in integer pixel SVG on project joints. Other cameras '
        'have projected front/side/back surfaces and separate arm-chain-aware sleeves. '
        'Three right views are explicit source SVGs with fixed upper-left lighting. '
        'No concept pixels pasted or body/head/hands/gait edited. Full layer groups '
        'remain editable geometric objects. Inkscape PNG antialias=0; only invisible '
        'alpha-zero RGB is normalized, with explicit sRGB. Existing ArmorSurface '
        'kinematics export the poses; original compositor order handles hands/head.\n'
        'Pose fitting also paints a cloth allowance on each original semantic arm/torso silhouette under the warped plates. Original alpha=1 distant interpolation sentinels are not promoted to opaque cloth; original source alpha/RGB remain unchanged. This is one shared offline adapter, not per-frame manual redraw or a new engine branch.\n')
    manifest={
        'schemaVersion':'1.0.0','kind':'p1-apparel-masters',
        'id':f'p1-chat-{"starlight" if item=="starlightArmor" else "dragon"}-armor-v2',
        'baseId':BASE,'canvas':[256,256],'referenceMotionSHA256':sha(MOTION),
        'selectedDesign':'B','stage':'C3-eight-static-views','status':'pending_user_art_review',
        'designSelection':{'userStatement':'两个都选择b','scope':'shown front concept B',
                           'sourceCommit':SOURCE},
        'allDirectionAuthorization':'你一路做完所有方向的',
        'artApproval':None,'runtimeImported':False,'views':views,
        'sourceFiles':sources+['source/palette.json','source/sRGB.icc','source/authoring-notes.txt'],
        'extraRightViewsReason':'Explicit geometry and fixed-light highlights on each actual right-facing rest rig, avoiding blind raster mirroring.',
    }
    write(dest/'master-manifest.json',manifest)
    return manifest


def export_poses(item,manifest,surface):
    dest=PARTS/item
    template=json.loads((ROOT/'Art/Parts/P1-v1/b5-set-armors-v1/starlightArmor/asset.json').read_text())
    asset=copy.deepcopy(template);bindings=[];hashes={}
    for f in sorted(surface.motion['frames'],key=compose.key):
        paths={};direction,clip,num=compose.key(f)
        layers=surface.render(item,f)
        for slot in SLOTS:
            path=dest/f'png/{direction}/{clip}/{num:02}/{slot}.png'
            save(layers[slot],path);paths[slot]=path.relative_to(dest).as_posix();hashes[paths[slot]]=sha(path)
        bindings.append({'direction':direction,'clip':clip,'frame':num,'layers':paths})
        if num==0:print(item,direction,'exported',flush=True)
    asset.update(id=manifest['id'],version='1.0.0',directions=DIRECTIONS,
                 clips=['idle','walk','walk-start','walk-stop'],slots=SLOTS,
                 sourceFiles=['master-manifest.json','authoring.json']+manifest['sourceFiles'],
                 bindings=bindings)
    write(dest/'asset.json',asset)
    write(dest/'authoring.json',{
        'selectedDesign':'B','sourceCommit':SOURCE,'staticMasterViews':8,
        'poseBindings':len(bindings),'layerReferences':len(hashes),
        'motionSHA256':sha(MOTION),'baseManifestSHA256':sha(ROOT/'Art/Parts/P1-v1/eight-way-v1/base/asset.json'),
        'surfaceScript':'scripts/armor-shared-surface-r4.py','exporter':'scripts/build-chat-apparel-b-eight-way.py',
        'runtimeImported':False,'userArtApproval':None,'bodyMotionJointMapDrawOrderModified':False,
        'registeredClothAllowance':{
            'source':'unchanged semantic body.torso/body.arm.left/body.arm.right in each original rig pose',
            'method':'paint cloth RGB on the actual anatomical silhouette before overlaying the original-motion-warped plates',
            'sourceAlphaVisibilityFloor':8,
            'reason':'do not promote original alpha=1 interpolation sentinel pixels to opaque clothing',
            'originalBodyRGBResampledOrRecolored':False,
        },
        'posePNG_SHA256':hashes,
    })
    return asset


def cell(im,label,scale=1):
    out=Image.new('RGB',(256*scale,280*scale),'#1e3428')
    im=im.resize((256*scale,256*scale),Image.Resampling.NEAREST)
    out.paste(im,(0,0),im)
    ImageDraw.Draw(out).text((6*scale,259*scale),label,font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11*scale),fill='#f3e1b8')
    return out


def gif(frames,path,durations):
    # One common palette per clip, so quantization cannot invent color flicker.
    palette_board=Image.new('RGB',(frames[0].width*len(frames),frames[0].height))
    for i,im in enumerate(frames):palette_board.paste(im,(i*im.width,0))
    palette=palette_board.quantize(colors=256)
    encoded=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
    encoded[0].save(path,save_all=True,append_images=encoded[1:],duration=durations,
                    loop=0,disposal=1,optimize=True)


def reviews(assets):
    REVIEW.mkdir(parents=True,exist_ok=True)
    cat=json.loads((ROOT/'Art/Integration/P1-modular-eight-way-v1/catalog.json').read_text())
    cat['assets'] += [{'id':a['id'],'manifest':(PARTS/item/'asset.json').relative_to(ROOT).as_posix()} for item,a in assets.items()]
    write(REVIEW/'catalog.json',cat)
    compositor=Compositor(ROOT,REVIEW/'catalog.json',MOTION)
    ordered=[('idle',0)]+[('walk',n) for n in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]
    for item,a in assets.items():
        dest=REVIEW/item;dest.mkdir(parents=True,exist_ok=True)
        choices=['p1-eight-way-lower-v1','p1-eight-way-hair-chestnut-v1','p1-eight-way-face-blue-v1',a['id']]
        allposes={}
        for direction in DIRECTIONS:
            for clip,n in ordered:
                allposes[direction,clip,n]=compositor.render(BASE,choices,direction,clip,n)
        overview=Image.new('RGB',(4*256,2*280),'#1e3428')
        for i,direction in enumerate(DIRECTIONS):
            overview.paste(cell(allposes[direction,'idle',0],direction),(i%4*256,i//4*280))
            # Full canvases at 1x/2x; includes all 13 authored poses per facing.
            for scale in [1,2]:
                board=Image.new('RGB',(4*256*scale,4*280*scale),'#1e3428')
                for j,(clip,n) in enumerate(ordered):
                    board.paste(cell(allposes[direction,clip,n],f'{direction} {clip}{n:02}',scale),
                                (j%4*256*scale,j//4*280*scale))
                board.save(dest/f'{direction}-poses-{scale}x.png')
            walk=[cell(allposes[direction,'walk',n],direction,2) for n in range(1,9)]
            gif(walk,dest/f'{direction}-walk-normal.gif',120)
            entry={'down':1,'down-left':4,'left':4,'up-left':4,'up':4,'up-right':0,'right':0,'down-right':0}[direction]
            seq=[('idle',0),('walk-start',1),('walk-start',2)]
            seq += [('walk',(entry+n)%8+1) for n in range(16)]
            seq += [('walk-stop',1),('walk-stop',2),('idle',0)]
            gif([cell(allposes[direction,c,n],direction,2) for c,n in seq],
                dest/f'{direction}-start-stop-normal.gif',[480]+[120]*20+[480])
        overview.save(dest/'all-directions-standing-1x.png')
        overview.resize((overview.width*2,overview.height*2),Image.Resampling.NEAREST).save(dest/'all-directions-standing-2x.png')
        walk_frames=[];sword_frames=[]
        for n in range(1,9):
            frame=Image.new('RGB',(4*256,2*280),'#1e3428')
            sword=frame.copy()
            for i,d in enumerate(DIRECTIONS):
                frame.paste(cell(allposes[d,'walk',n],d),(i%4*256,i//4*280))
                armed=compositor.render(BASE,choices+['p1-eight-way-weapon-v1'],d,'walk',n)
                sword.paste(cell(armed,d),(i%4*256,i//4*280))
            walk_frames.append(frame);sword_frames.append(sword)
        gif(walk_frames,dest/'eight-way-walk-normal.gif',120)
        gif(sword_frames,dest/'eight-way-back-sword-normal.gif',120)
        print(item,'review clips exported',flush=True)
    return compositor


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--masters-only',action='store_true')
    p.add_argument('--poses-only',action='store_true')
    p.add_argument('--reviews-only',action='store_true')
    args=p.parse_args();surface=Surface();assets={}
    for item in front.PALETTES:
        if args.reviews_only:
            assets[item]=json.loads((PARTS/item/'asset.json').read_text());continue
        master=json.loads((PARTS/item/'master-manifest.json').read_text()) if args.poses_only else export_masters(item,surface)
        print(item,'8 static views complete',flush=True)
        if not args.masters_only:assets[item]=export_poses(item,master,surface)
    if args.masters_only:return
    reviews(assets)


if __name__=='__main__':main()
