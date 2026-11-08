#!/usr/bin/env python3
"""Composite the five supplied skill atlases over the production battle art.

This is a normal-speed offline art review. It uses the existing attack/guard
clips, battle backgrounds, heroes and monster poses; it does not run UIKit or
simulate a device.
"""
from __future__ import annotations

import json, math, shutil, subprocess
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'Sources/Resources/Assets.xcassets'
VFX=ROOT/'Art/Parts/BattleVFX'
OUT=ROOT/'Art/Review/Battle/skill-vfx-v1'
OUT.mkdir(parents=True,exist_ok=True)
W,H=1000,600
FPS=50
STEP=1/FPS
DURATION=2.8
FRAMES=round(DURATION*FPS)
OUTPUT_SCALE=.72
OW,OH=round(W*OUTPUT_SCALE),round(H*OUTPUT_SCALE)
HERO_SCALE=.83
ENEMY_SCALE=.82
FEET={'p1':(165.,420.),'p2':(315.,505.),'m1':(650.,395.),'m2':(835.,510.)}

def image_asset(name:str)->Image.Image:
    folder=ASSETS/f'{name}.imageset'
    contents=json.loads((folder/'Contents.json').read_text())
    return Image.open(folder/contents['images'][0]['filename']).convert('RGBA')

hero_renderer=ROOT/'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py'
env={'__file__':str(hero_renderer)}
exec(compile(hero_renderer.read_text().split("for clip,data in lib['clips'].items():")[0],str(hero_renderer),'exec'),env)
hero=env['render']

font_path=next((Path(p) for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/System/Library/Fonts/PingFang.ttc','/System/Library/Fonts/AppleSDGothicNeo.ttc'] if Path(p).exists()),None)
if not font_path: raise RuntimeError('Chinese font is required for the review GIF')
font=ImageFont.truetype(str(font_path),21)
small=ImageFont.truetype(str(font_path),15)

def bg_layer(name:str)->Image.Image:
    im=image_asset(name).resize((1000,917),Image.Resampling.LANCZOS)
    stage=Image.new('RGBA',(W,H),(0,0,0,0));stage.alpha_composite(im,(0,-159))
    return stage

plate=Image.new('RGBA',(W,H),(12,25,18,255))
for name in ['MeadowCampFarForest','MeadowCampGround','MeadowCampMidground']:
    plate.alpha_composite(bg_layer(name))
foreground=bg_layer('MeadowCampForeground')
warden=image_asset('MeadowBattleForestWarden')
attack_atlas=image_asset('MeadowBattleWardenAttackSheet')
monster_attacks=[attack_atlas.crop((i*384,0,(i+1)*384,256)) for i in range(8)]

catalog=json.loads((VFX/'skill-effects-v1/manifest.json').read_text())
specs={x['skill']:x for x in catalog['sourceArchives']}
NAMES={'starlightPulse':'星辉脉冲','rally':'振奋','sweep':'横扫','dragonSoulWard':'龙魂庇护','dragonScaleWard':'龙鳞庇护'}
CLIP_NOTE={'starlightPulse':'既有远程攻击姿态','rally':'既有防护姿态','sweep':'既有近身攻击姿态','dragonSoulWard':'既有防护姿态','dragonScaleWard':'既有防护姿态'}
parser=argparse.ArgumentParser()
parser.add_argument('--skill',choices=['starlightPulse','rally','sweep','dragonSoulWard','dragonScaleWard'])
ARGS=parser.parse_args()

def smooth(v):
    t=max(0.,min(1.,v));return t*t*(3-2*t)

def pulse(t,start,peak,end):
    return smooth((t-start)/(peak-start)) if t<peak else 1-smooth((t-peak)/(end-peak))

def alpha_image(im,alpha):
    cp=im.copy();cp.putalpha(cp.getchannel('A').point(lambda a:round(a*max(0.,min(1.,alpha)))));return cp

def additive(dst,im,center,size,alpha=1.0):
    if alpha<=0:return
    width=max(1,round(size[0]));height=max(1,round(size[1]))
    im=alpha_image(im.resize((width,height),Image.Resampling.LANCZOS),alpha)
    x=round(center[0]-width/2);y=round(center[1]-height/2)
    l=max(0,x);t=max(0,y);r=min(dst.width,x+width);b=min(dst.height,y+height)
    if l>=r or t>=b:return
    src=im.crop((l-x,t-y,r-x,b-y));old=dst.crop((l,t,r,b))
    rgb=ImageChops.add(old.convert('RGB'),ImageChops.multiply(src.convert('RGB'),src.getchannel('A').convert('RGB')))
    dst.paste(rgb,(l,t))

def glow(dst,center,rx,ry,alpha,color):
    if alpha<=0:return
    radius=max(1,round(max(rx,ry)*1.3));size=radius*2+1
    y,x=np.mgrid[-radius:radius+1,-radius:radius+1]
    fall=np.exp(-2.1*((x/max(rx,1))**2+(y/max(ry,1))**2))
    layer=np.zeros((size,size,4),dtype=np.uint8)
    layer[:,:,:3]=color;layer[:,:,3]=np.clip(fall*alpha*130,0,255).astype(np.uint8)
    src=Image.fromarray(layer,'RGBA');dst.alpha_composite(src,(round(center[0]-radius),round(center[1]-radius)))

def make_shade(dim):
    layer=Image.new('RGBA',(W,H),(0,0,0,round(255*dim)))
    return layer

def hero_at(unit,offset=(0.,0.)):
    x,y=FEET[unit];return x+offset[0]-123*HERO_SCALE,y+offset[1]-214*HERO_SCALE

def projected_shadow(dst,im,x,y,scale,sole):
    mask=im.getchannel('A').point(lambda a:round(a*.31))
    silhouette=Image.new('RGBA',im.size,(8,10,6,0));silhouette.putalpha(mask)
    a=1/scale;b=-.38/(.15*scale);c=-x/scale+.38*y/(.15*scale)+.38*sole/.15
    e=-1/(.15*scale);f=y/(.15*scale)+1.15*sole/.15
    projected=silhouette.transform((W,H),Image.Transform.AFFINE,(a,b,c,0,e,f),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(2.5*scale))
    dst.alpha_composite(projected)

def hero_motion(skill,age):
    if skill in ('rally','dragonSoulWard','dragonScaleWard'):
        if age<0:return 'idle',0.
        return 'guard',min(1.,max(0.,age/1.4))
    if skill=='starlightPulse':
        if age<0:return 'idle',0.
        action=max(0.,age-.4-min(.1,max(0.,age-.648)))
        return 'attack',min(1.,max(0.,action/1.2))
    return 'idle',0.

def enemy_motion(age,skill):
    if skill!='sweep' or age<0:return (0.,0.),0
    move=pulse(age,.08,.46,.96)
    p1=FEET['p1'];fromp=FEET['m1']
    dx=(p1[0]+(178.5-42)*ENEMY_SCALE-fromp[0])*move
    dy=(p1[1]-fromp[1])*move
    return (dx,dy),min(7,max(0,int(min(1,age/.96)*8)))

def actor_and_world(skill,t,action_start):
    scene=plate.copy()
    action_age=t-action_start
    move,enemy_frame=enemy_motion(action_age,skill)
    # Existing ground projection and actor feet are kept fixed to the battle layout.
    draw_units=[('p1','P1'),('p2','P2'),('m1','鹿灵甲'),('m2','鹿灵乙')]
    poses={}
    for unit,_ in draw_units:
        if unit.startswith('p'):
            clip,progress=hero_motion(skill,action_age if unit=='p2' else -1)
            im=hero(clip,progress)
            off=(0.,0.)
            x,y=hero_at(unit,off)
            poses[unit]=(im,x,y,off)
        else:
            off=move if unit=='m1' else (0.,0.)
            im=monster_attacks[enemy_frame] if skill=='sweep' and unit=='m1' and action_age>=0 else warden
            x,y=FEET[unit][0]+off[0]-178.5*ENEMY_SCALE,FEET[unit][1]+off[1]-240*ENEMY_SCALE
            poses[unit]=(im,x,y,off)
    for unit,_, in draw_units:
        im,x,y,_=poses[unit]
        if unit.startswith('p'):
            s=HERO_SCALE;size=(256*s,256*s);sole=214
        else:
            s=ENEMY_SCALE;size=(384*s,256*s);sole=240
        projected_shadow(scene,im,x,y,s,sole)
        resized=im.resize((round(size[0]),round(size[1])),Image.Resampling.NEAREST)
        scene.alpha_composite(resized,(round(x),round(y)))
    scene.alpha_composite(foreground)
    return scene,poses,action_age

def load_frames(spec):
    sheet=image_asset(spec['asset']);w,h=spec['width'],spec['height'];cols=spec['columns']
    return [sheet.crop(((i%cols)*w,(i//cols)*h,(i%cols+1)*w,(i//cols+1)*h)) for i in range(spec['count'])]

def render_one(skill):
    spec=specs[skill];sprites=load_frames(spec);action_start=.42
    draw_units=[('p1','P1'),('p2','P2'),('m1','鹿灵甲'),('m2','鹿灵乙')]
    hit_age=.46 if skill=='sweep' else 1.048 if skill=='starlightPulse' else .56
    peak=spec['peak_frame']/spec['fps']
    effect_start=action_start+hit_age if skill in ('rally','dragonSoulWard','dragonScaleWard') else action_start+max(0.,hit_age-peak)
    status_reveal_time=(action_start+hit_age if skill=='starlightPulse' else effect_start+spec['count']/spec['fps']*.58 if skill in ('dragonSoulWard','dragonScaleWard') else None)
    frames=[]
    names=['m1','m2'] if skill=='starlightPulse' else ['p1','p2']
    pivot_points=[]
    for unit in names:
        foot=FEET[unit]
        if unit.startswith('m'):
            pivot_points.append((foot[0]+13.5*ENEMY_SCALE,foot[1]-112*ENEMY_SCALE))
        else:
            pivot_points.append((foot[0]+5*HERO_SCALE,foot[1]-86*HERO_SCALE))
    center=(sum(p[0] for p in pivot_points)/len(pivot_points),sum(p[1] for p in pivot_points)/len(pivot_points))
    ground_y=sum(FEET[u][1] for u in names)/len(names)
    for index in range(FRAMES):
        t=index*STEP
        scene,poses,age=actor_and_world(skill,t,action_start)
        action_duration=1.10 if skill=='sweep' else 1.70 if skill=='starlightPulse' else 1.80
        dim_age=t-action_start
        maxdim=.58 if skill in ('sweep','starlightPulse') else .32 if skill!='rally' else .36
        dim=maxdim*smooth(dim_age/.4)*(1-smooth((dim_age-1.2)/.6)) if dim_age>=0 else 0
        scene.alpha_composite(make_shade(dim))
        # Rule changes are committed on hit; the positive HP/shield art waits
        # until its spell animation is in the later half.
        status_age=t-(action_start+hit_age)
        if skill=='starlightPulse' and status_age>=0:
            p=FEET['p2'];standard=image_asset('BattleVFXHealingStandardSheet')
            frame_index=min(19,max(0,int(status_age*20)))
            tile=standard.crop(((frame_index%5)*614,(frame_index//5)*512,(frame_index%5+1)*614,(frame_index//5+1)*512))
            fade=smooth(status_age/.12)
            additive(scene,tile,(p[0],p[1]-104),(206,173),.46*fade)
            barrier=image_asset('BattleVFXRoundBarrier');additive(scene,barrier,(p[0]+4,p[1]-87),(199,199),.34*fade)
        elif skill in ('dragonSoulWard','dragonScaleWard') and t>=effect_start+spec['count']/spec['fps']*.58:
            status_age=t-(effect_start+spec['count']/spec['fps']*.58)
            frame_index=min(19,max(0,int(status_age*20)))
            fade=smooth(status_age/.12)
            barrier=image_asset('BattleVFXRoundBarrier')
            for unit in ('p1','p2'):
                # Existing receipt-dependent healing is shown at its actual tier:
                # P1 gains 10/12; P2 is capped at +6 by the training HP state.
                tier='strong' if unit=='p1' else 'standard'
                sheet_name='BattleVFXHealingStrongSheet' if tier=='strong' else 'BattleVFXHealingStandardSheet'
                cell=512 if tier=='strong' else 614
                tile=image_asset(sheet_name).crop(((frame_index%5)*cell,(frame_index//5)*cell,(frame_index%5+1)*cell,(frame_index//5+1)*cell))
                p=FEET[unit];additive(scene,tile,(p[0],p[1]-112),(214,214),.43*fade);additive(scene,barrier,(p[0]+4,p[1]-87),(199,199),.27*fade)
        local=t-effect_start
        if 0<=local<spec['count']/spec['fps']:
            pos=local*spec['fps'];lower=min(spec['count']-1,max(0,int(pos)));upper=min(spec['count']-1,lower+1);mix=smooth(pos-lower)
            light=pulse(local,0,peak,spec['count']/spec['fps'])
            colors={'starlightPulse':(92,80,255),'rally':(255,191,53),'sweep':(96,193,255),'dragonSoulWard':(71,155,255),'dragonScaleWard':(255,131,38)}
            color=colors[skill]
            glow(scene,center,spec['width']*.34,spec['height']*.29,light*.13,color)
            glow(scene,(center[0],ground_y-5),spec['width']*.31,15,light*.24,color)
            origin=(center[0]-spec.get('anchor_x',spec['width']/2),center[1]-spec.get('anchor_y',spec['height']/2))
            additive(scene,sprites[lower],(origin[0]+spec['width']/2,origin[1]+spec['height']/2),(spec['width'],spec['height']),1-mix)
            if upper!=lower and mix>0:additive(scene,sprites[upper],(origin[0]+spec['width']/2,origin[1]+spec['height']/2),(spec['width'],spec['height']),mix)
        # Nameplates and vitals sit over effects just as in the production scene.
        draw=ImageDraw.Draw(scene)
        for unit,label in draw_units:
            im,x,y,_=poses[unit]
            foot=FEET[unit]
            fy=foot[1]+(0 if unit.startswith('p') else 0)
            box_y=fy-(170 if unit.startswith('p') else 242)
            bx=foot[0]
            draw.rounded_rectangle((bx-76,box_y,bx+76,box_y+30),5,fill=(19,40,27,235),outline=(190,170,104,220),width=1)
            draw.text((bx-68,box_y+3),label,font=small,fill=(255,241,203,255))
            hp_y=box_y+32
            draw.rounded_rectangle((bx-47,hp_y,bx+47,hp_y+12),3,fill=(6,12,8,245),outline=(148,137,92,230),width=1)
            draw.rounded_rectangle((bx-45,hp_y+2,bx+35,hp_y+10),2,fill=(75,207,118,255))
        # Minimal review banner is deliberately outside the battlefield art.
        draw=ImageDraw.Draw(scene)
        draw.rounded_rectangle((16,12,354,51),8,fill=(16,35,24,220),outline=(202,182,113,235),width=1)
        draw.text((29,18),f'{NAMES[skill]} · {CLIP_NOTE[skill]}',font=font,fill=(255,239,198,255))
        frames.append(scene.resize((OW,OH),Image.Resampling.LANCZOS).convert('RGB'))
        del scene
    name=f'{skill}-normal.gif';palette_source=Image.new('RGB',(OW*3,OH*3),'#112217')
    sample_indices=[0,20,35,48,60,75,90,105,120,139]
    for i,k in enumerate(sample_indices):palette_source.paste(frames[min(k,len(frames)-1)],((i%3)*OW,(i//3)*OH))
    palette=palette_source.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    target=OUT/name
    encoded[0].save(target,save_all=True,append_images=encoded[1:],duration=20,loop=0,disposal=1,optimize=True)
    opt=shutil.which('gifsicle') or '/workspace/gifsicle-1.96/src/gifsicle'
    if Path(opt).exists():
        tmp=OUT/(name+'.tmp');subprocess.run([opt,'-O3',str(target),'-o',str(tmp)],check=True);tmp.replace(target)
    gif=Image.open(target)
    durations=[]
    for i in range(gif.n_frames):
        gif.seek(i);durations.append(gif.info.get('duration',20))
    assert sum(durations)==round(DURATION*1000), (skill,sum(durations))
    # Decoded contact page samples every frame for a complete normal-speed visual scan.
    page=Image.new('RGB',(5*200,math.ceil(FRAMES/5)*126),'#13251b')
    decoded=0;elapsed=0;gif.seek(0)
    for i in range(FRAMES):
        sample_ms=i*20
        while decoded+1<len(durations) and elapsed+durations[decoded]<=sample_ms:
            elapsed+=durations[decoded];decoded+=1;gif.seek(decoded)
        thumb=gif.convert('RGB').resize((200,120),Image.Resampling.LANCZOS)
        page.paste(thumb,((i%5)*200,(i//5)*126))
    page.save(OUT/f'{skill}-decoded-all-frames.jpg',quality=90)
    for sec,label in [(0,'idle'),(.8,'windup'),(1.1,'impact'),(1.55,'tail'),(2.5,'settled')]:
        frames[min(FRAMES-1,round(sec*FPS))].save(OUT/f'{skill}-{label}.png')
    cue_frame=None
    if status_reveal_time is not None:
        cue_frame=min(FRAMES-1,round(status_reveal_time*FPS))
        frames[cue_frame].save(OUT/f'{skill}-status-cue.png')
        frames[min(FRAMES-1,round((status_reveal_time+.12)*FPS))].save(OUT/f'{skill}-status-cue-plus-120ms.png')
    return {'gif':name,'decodedFrames':gif.n_frames,'totalDurationMs':sum(durations),'sampledAtMs':20,'sizeBytes':target.stat().st_size,'motion':CLIP_NOTE[skill],'sourceFPS':spec['fps'],'statusCueAtSceneMs':round(status_reveal_time*1000) if status_reveal_time is not None else None,'statusCueFrame':cue_frame}

selected=[ARGS.skill] if ARGS.skill else ['starlightPulse','rally','sweep','dragonSoulWard','dragonScaleWard']
report={skill:render_one(skill) for skill in selected}
review={'scope':'normal-speed offline scene composition using original battle art, skill atlas frames and the existing attack/guard motions; not UIKit/simulator/device capture','outputDimensions':[OW,OH],'sourceFramesPreserved':True,'authoredCharacterMotionAdded':False,'animations':{},'userArtApproval':None}
path=OUT/'review.json'
if path.exists():
    try:review=json.loads(path.read_text())
    except json.JSONDecodeError:pass
review['animations'].update(report)
review['statusRevealTiming']={
    'starlightPulse':'1.048s receipt at 60% of the 1.25s authored VFX; healing and round shield begin on the hit cue, in the latter half.',
    'dragonSoulWard':'Begin recovery and shield at VFX age 0.967s / 58% of 1.667s.',
    'dragonScaleWard':'Begin recovery and shield at VFX age 0.580s / 58% of 1.0s.',
    'rally':'No positive HP or shield receipt.',
    'sweep':'No positive HP or shield receipt.'
}
path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
