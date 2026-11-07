#!/usr/bin/env python3
"""Offline VFX study. Existing poses, generated optical assets; no app execution.

Does not import legacy review modules with top-level file-writing side effects.
No character pixels are repainted. Dissolve masks and lighting are composition.
"""
from pathlib import Path
import hashlib, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art/Scenes/MeadowBattle/effects-v2'
SOURCE_ART = ROOT / 'Art/Scenes/MeadowBattle/effects-v1'
OUT = ROOT / 'Art/Review/Battle/effects-v2'
ASSETS = ROOT / 'Sources/Resources/Assets.xcassets'
W, H, UI, STEP, COUNT = 760, 697, 112, 40, 180
OUT.mkdir(parents=True, exist_ok=True)
source = ROOT / 'Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py'
namespace = {'__file__': str(source)}
exec(compile(source.read_text().split('\nfor clip,data in lib[\'clips\'].items():')[0], str(source), 'exec'), namespace)
namespace['lib']['clips']['attack'] = json.loads((SOURCE_ART / 'attack-clip.json').read_text())
render, sample = namespace['render'], namespace['sample']
fontfile = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font = ImageFont.truetype(fontfile, 17)
small = ImageFont.truetype(fontfile, 12)
large = ImageFont.truetype(fontfile, 23)
spec = json.loads((ART / 'effect.json').read_text())

def asset(name):
    folder = ASSETS / f'{name}.imageset'
    filename = json.loads((folder / 'Contents.json').read_text())['images'][0]['filename']
    return Image.open(folder / filename).convert('RGBA')

plate = Image.new('RGBA', (W, H))
for name, blur in [('MeadowCampFarForest', 3), ('MeadowCampGround', 1.5), ('MeadowCampMidground', 1.5)]:
    image = asset(name).filter(ImageFilter.GaussianBlur(blur))
    plate.alpha_composite(image.resize((W, H), Image.Resampling.LANCZOS))
foreground = asset('MeadowCampForeground').resize((W, H), Image.Resampling.LANCZOS)
enemy = asset('MeadowBattleForestWarden')
sprites = {name: Image.open(SOURCE_ART / f'{name}.png').convert('RGBA') for name in ['slash', 'burst', 'ring', 'mote']}
hs, es = H * .17 / 132, H * .33 / 232
hx, hy = W * .29 - 123 * hs, H * .69 - 214 * hs
ex, ey = W * .65 - 178.5 * es, H * .685 - 241 * es

def smooth(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def pulse(t, start, peak, end):
    return smooth((t-start)/(peak-start)) if t <= peak else 1-smooth((t-peak)/(end-peak))

def opacity(image, amount):
    image = image.copy(); image.putalpha(image.getchannel('A').point(lambda a: round(a * max(0, min(1, amount)))))
    return image

def stamp(frame, image, center, size, alpha=1):
    if alpha <= 0 or size[0] < 1 or size[1] < 1: return
    image = opacity(image.resize((max(1, round(size[0])), max(1, round(size[1]))), Image.Resampling.LANCZOS), alpha)
    frame.alpha_composite(image, (round(center[0]-image.width/2), round(center[1]-image.height/2)))

yy, xx = np.mgrid[:H, :W]
def light(frame, center, radii, strength):
    if strength <= 0: return
    falloff = np.exp(-(((xx-center[0])/radii[0])**2+((yy-center[1])/radii[1])**2)*2)
    glow = np.zeros((H, W, 4), dtype=np.uint8)
    glow[:, :, :3] = [255, 192, 70]
    glow[:, :, 3] = np.clip(falloff * strength * 160, 0, 255).astype('uint8')
    frame.alpha_composite(Image.fromarray(glow))

def shadow(frame, image, x, y, scale, alpha=1):
    # Same ground projection registration as the existing offline scene review.
    sole=214 if image.width == 256 else 241
    mask=image.getchannel('A').point(lambda a: round(a*.34*alpha))
    sh=Image.new('RGBA', image.size, (9,11,6,0)); sh.putalpha(mask)
    a=1/scale; b=-.38/(.15*scale); c=-x/scale+.38*y/(.15*scale)+.38*sole/.15
    e=-1/(.15*scale); f=y/(.15*scale)+1.15*sole/.15
    projected=sh.transform((W,H),Image.Transform.AFFINE,(a,b,c,0,e,f),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(2.5*scale))
    frame.alpha_composite(projected)

def point(q, part):
    pivot, offset, angle=part; dx,dy=q[0]-pivot[0],q[1]-pivot[1]
    return pivot[0]+offset[0]+dx*math.cos(angle)-dy*math.sin(angle), pivot[1]+offset[1]+dx*math.sin(angle)+dy*math.cos(angle)

contact=sample('attack',.54)
tip=point((191,142),contact[0]['MeadowBattleHeroWeapon'])
travel=min(W*.22,max(0,ex+110*es-(hx+(tip[0]+contact[1][0])*hs)))
impact=(hx+travel+(tip[0]+contact[1][0])*hs,hy+(tip[1]+contact[1][1])*hs)
ep=np.asarray(enemy).copy(); rng=np.random.default_rng(7641)
# One fixed, repeatable threshold field; never new random noise per frame.
gh,gw=math.ceil(enemy.height/3),math.ceil(enemy.width/3)
noise=rng.random((gh,gw)); field=np.repeat(np.repeat(noise,3,0),3,1)[:enemy.height,:enemy.width]
threshold=.52*field+.48*np.linspace(0,1,enemy.height)[:,None]
valid=np.argwhere(ep[:,:,3]>180)
chosen=valid[rng.choice(len(valid), 150, replace=False)]
particles=[]
for py,px in chosen:
    particles.append((float(px),float(py),float(threshold[py,px]),float(rng.uniform(-35,55)),float(rng.uniform(30,94)),float(rng.uniform(2,5))))

frames=[]; traces=[]
for i in range(COUNT):
    t=i*STEP/1000
    focus='ordinary' if .6 <= t < 1.6 else 'heavy' if 1.6 <= t < 2.6 else None
    power=spec['skills'][focus]['visualPower'] if focus else 0
    focus_start=.6 if focus=='ordinary' else 1.6
    focus_envelope=smooth((t-focus_start)/(spec['focusFadeInMs']/1000)) if focus else 0
    hover_dim=spec['skills'][focus]['previewDarken']*focus_envelope if focus else 0
    # The floor marker belongs only to selection / anticipation, never travel.
    ring_alpha=power*.7*focus_envelope if focus else .65*(1-smooth((t-2.84)/.16)) if 2.6<=t<3 else 0
    action=max(0,t-3)
    # Fixed 80ms contact hold, shared by all motion/effect timing; no charge tiers.
    motion=max(0,action-min(.08,max(0,action-.648)))
    p=min(1,motion/1.2)
    clip='attack' if 3<=t<4.28 else 'victory' if 4.28<=t<5.36 else 'idle'
    progress=p if clip=='attack' else (t-4.28)/1.08 if clip=='victory' else (t%2.4)/2.4
    hero=render(clip,progress)
    approach=0 if not 3<=t<4.28 else smooth((p-.12)/.28) if p<.4 else 1 if p<=.66 else smooth((1-p)/.34)
    tx=travel*approach
    hit=3.648
    hit_age=t-hit
    flash=pulse(t,hit-.04,hit+.04,hit+.22)
    burst=pulse(t,hit-.04,hit+.04,hit+.40)
    # Smooth attack / plateau / release; no discontinuity at the plateau boundary.
    selected_dim=spec['skills']['heavy']['previewDarken']
    cast_dim=(selected_dim+(spec['castDarken']-selected_dim)*smooth((t-2.6)/.44))*(1-smooth((t-4.6)/1.36)) if t>=2.6 else 0
    dim=hover_dim if t<2.6 else cast_dim
    dissolve=smooth((t-4.28)/1.12)
    keep=threshold>=dissolve if t>=4.28 else np.ones_like(threshold,dtype=bool)
    enemy_pixels=ep.copy(); enemy_pixels[:,:,3]=(ep[:,:,3]*keep).astype('uint8')
    if 4.28<=t<5.4:
        edge=keep & (threshold<dissolve+.065)
        enemy_pixels[edge,:3]=[255,244,195]
    monster=Image.fromarray(enemy_pixels)
    recoil=W*.017*pulse(t,hit-.02,hit+.14,hit+.52)
    scene=ImageEnhance.Brightness(plate).enhance(1-dim)
    light(scene,impact,(170,190),burst*.65)
    light(scene,(impact[0]+15,H*.685),(170,42),burst*.95)
    light(scene,(W*.29,H*.69),(95,28),power*.35*focus_envelope)
    shadow(scene,hero,hx+tx,hy,hs)
    shadow(scene,monster,ex+recoil,ey,es)
    # Non-participating monster darkens during release; caster remains readable.
    monster=ImageEnhance.Brightness(monster).enhance(1-dim*.55)
    scene.alpha_composite(hero.resize((round(256*hs),round(256*hs)),Image.Resampling.NEAREST),(round(hx+tx),round(hy)))
    scene.alpha_composite(monster.resize((round(enemy.width*es),round(enemy.height*es)),Image.Resampling.NEAREST),(round(ex+recoil),round(ey)))
    if flash>0:
        white=Image.new('RGBA',monster.size,(255,244,200,0));white.putalpha(monster.getchannel('A'))
        sy,sx=np.mgrid[:monster.height,:monster.width]
        local=np.exp(-(((ex+recoil+sx*es-impact[0])/68)**2+((ey+sy*es-impact[1])/68)**2)*2)
        white.putalpha(Image.fromarray((np.asarray(monster.getchannel('A'))*local).astype('uint8')))
        stamp(scene,white,(ex+recoil+enemy.width*es/2,ey+enemy.height*es/2),(enemy.width*es,enemy.height*es),flash*.55)
    if focus:
        # Fixed amplitude for each skill; periodic motion never increases power.
        for j in range(7 if focus=='heavy' else 3):
            angle=j*2.399+t*1.7
            center=(W*.29+math.cos(angle)*(18+power*15),H*.69-58+math.sin(angle)*24)
            stamp(scene,sprites['mote'],center,(12,12),power*.9*focus_envelope)
    if ring_alpha>0:
        stamp(scene,sprites['ring'],(W*.29,H*.69),(110,46),ring_alpha)
    if burst>0:
        stamp(scene,sprites['slash'],(impact[0]-6,impact[1]),(155,155),pulse(t,hit-.08,hit,hit+.28))
        stamp(scene,sprites['burst'],impact,(160+max(0,hit_age)*180,160+max(0,hit_age)*180),burst)
        for j in range(14):
            angle=j*2.399; dist=max(0,hit_age)*(80+(j%4)*24)
            stamp(scene,sprites['mote'],(impact[0]+math.cos(angle)*dist,impact[1]+math.sin(angle)*dist),(10,10),burst*.9)
    if t>=4.28:
        for px,py,birth,vx,vy,size in particles:
            # Actual reveal uses smoothstep, so invert it for exact particle births.
            lo,hi=0.,1.
            for _ in range(14):
                mid=(lo+hi)/2
                if smooth(mid)<birth:lo=mid
                else:hi=mid
            age=t-(4.28+(lo+hi)*.56)
            if 0<=age<.85:
                center=(ex+px*es+vx*age,ey+py*es-vy*age)
                stamp(scene,sprites['mote'],center,(size*3,size*3),(1-age/.85)*.95)
    scene.alpha_composite(ImageEnhance.Brightness(foreground).enhance(1-dim))
    # UI stays outside the battlefield lighting and camera transform.
    frame=Image.new('RGBA',(W,H+UI),(15,24,22,255));frame.alpha_composite(scene)
    dr=ImageDraw.Draw(frame)
    dr.rectangle((0,0,W,35),fill=(12,23,22,235))
    dr.text((16,6),'林地遭遇 · 战斗光效样片 v2',font=font,fill='#f5e8c7')
    dr.text((W-232,10),f'离线合成 / 非实机  {t:04.2f}s',font=small,fill='#bbc5bc')
    stage='强技能预示 · 发光并压暗' if focus=='heavy' else '选择技能' if t<2.6 else '发动 · 裂光斩' if t<hit else '命中 · 局部爆光' if t<4.28 else '击败 · 粒子消散' if t<6.4 else '演出结束 · 即将重播'
    dr.text((18,H-37),stage,font=font,fill='#ffedbf')
    if hit<=t<hit+.7:dr.text((impact[0]+24,impact[1]-40-(t-hit)*30),'18',font=large,fill='#fff3cd',stroke_width=2,stroke_fill='#463016')
    dr.text((18,H+8),'技能固有强度预示；悬浮时长不增加威力',font=small,fill='#becbbf')
    for key,x,title,subtitle in [('ordinary',18,'普通斩击','轻量光效'),('heavy',270,'裂光斩','强技能 · 更强光效')]:
        active=focus==key; selected=key=='heavy' and 2.6<=t<4.28
        strength=spec['skills'][key]['visualPower']
        border='#ffe3a1' if active or selected else '#586858'
        if active:
            glow=Image.new('RGBA',frame.size);gd=ImageDraw.Draw(glow)
            gd.rounded_rectangle((x-3,H+31,x+237,H+100),10,fill=(255,195,69,round(85*strength*focus_envelope)))
            frame.alpha_composite(glow.filter(ImageFilter.GaussianBlur(7)));dr=ImageDraw.Draw(frame)
        dr.rounded_rectangle((x,H+34,x+234,H+96),8,fill='#29372b',outline=border,width=2 if active or selected else 1)
        dr.text((x+13,H+39),title,font=font,fill='#ffe5b2' if active or selected else '#e1e5d4')
        dr.text((x+13,H+68),subtitle,font=small,fill='#aabb9f')
        if active:dr.polygon([(x+206,H+51),(x+206,H+74),(x+212,H+68),(x+219,H+78),(x+223,H+75),(x+216,H+65),(x+224,H+63)],fill='white',outline='#26312a')
    dr.text((530,H+43),'P1  /  鹿灵',font=font,fill='#d3ddcc')
    dr.text((530,H+72),'确认后播放固定技能演出',font=small,fill='#aabb9f')
    frames.append(frame.convert('RGB'))
    traces.append({'frame':i,'timeMs':i*STEP,'focus':focus,'visualPower':power,'focusEnvelope':round(focus_envelope,6),'hoverDarken':round(hover_dim,6),'groundRingAlpha':round(ring_alpha,6),'heroTravelPx':round(tx,6),'clip':clip,'poseProgress':round(progress,6),'darken':round(dim,6),'dissolve':round(dissolve,6),'impact':list(impact)})

# A single shared palette sampled across all phases preserves the bright cores.
palette_source=Image.new('RGB',(W*3,(H+UI)*3))
for j,k in enumerate([0,25,50,70,88,92,108,125,147]):palette_source.paste(frames[k],((j%3)*W,(j//3)*(H+UI)))
palette=palette_source.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
encoded=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
encoded[0].save(OUT/'battle-effects-v2.gif',save_all=True,append_images=encoded[1:],duration=STEP,loop=0,disposal=1,optimize=True)
frames[0].save(OUT/'standing.png');frames[92].save(OUT/'impact.png')
(OUT/'trace.json').write_text(json.dumps(traces,ensure_ascii=False,indent=2)+'\n')
# Contact sheets come from the final decoded GIF, not the pre-encoding images.
gif=Image.open(OUT/'battle-effects-v2.gif')
assert gif.n_frames==COUNT
decoded=[]
for k in range(gif.n_frames):
    gif.seek(k);assert gif.info['duration']==STEP;decoded.append(gif.convert('RGB'))
for page in range(math.ceil(COUNT/24)):
    sheet=Image.new('RGB',(W//2*4,(H+UI)//2*6),'#111a15')
    for j,f in enumerate(decoded[page*24:(page+1)*24]):
        sheet.paste(f.resize((W//2,(H+UI)//2)),((j%4)*(W//2),(j//4)*((H+UI)//2)))
    sheet.save(OUT/f'decoded-{page+1:02}.jpg',quality=88)
assert {r['visualPower'] for r in traces if r['focus']=='ordinary'}=={spec['skills']['ordinary']['visualPower']}
assert {r['visualPower'] for r in traces if r['focus']=='heavy'}=={spec['skills']['heavy']['visualPower']}
assert all(r['groundRingAlpha']==0 for r in traces if r['timeMs']>=3000)
assert all(r['groundRingAlpha']==0 for r in traces if r['heroTravelPx']>0)
assert all(r['hoverDarken']==spec['skills']['heavy']['previewDarken'] for r in traces if 1880<=r['timeMs']<2600)
report={'scope':'offline composited art study; not runtime input or GPU/device capture','frames':COUNT,'frameDurationMs':STEP,'totalDurationMs':COUNT*STEP,'hoverPowerIsTimeIndependent':True,'oldArtModified':False,'artApproval':None,'deviceExecution':False,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,ART/'effect.json',SOURCE_ART/'attack-clip.json',*[SOURCE_ART/f'{n}.png' for n in sprites]]}}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for page in range(4):
    sheet=Image.new('RGB',(2048,790),'#203627');draw=ImageDraw.Draw(sheet)
    for j in range(4):
        progress=(page*4+j)/15; actor=render('attack',progress)
        sheet.paste(actor,(j*512+128,20),actor)
        doubled=actor.resize((512,512),Image.Resampling.NEAREST)
        sheet.paste(doubled,(j*512,278),doubled)
        draw.text((j*512+12,4),f'attack {progress:.4f}  1x / 2x',fill='white')
    sheet.save(OUT/f'actor-poses-{page+1}.png')
print(json.dumps({'frames':COUNT,'durationMs':COUNT*STEP,'gifBytes':(OUT/'battle-effects-v2.gif').stat().st_size,'out':str(OUT)}))
