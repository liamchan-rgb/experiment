"""Offline preview of the director camera (close-up -> swing -> pull back), damage-scaled shake, a pane-wide dim and the large
spring-in floating numbers. The shot/number maths mirror MeadowSkillProcedural.shot/scaled and MeadowBattleNumber (hand-ported,
the Swift versions are checked by the regression scripts). Approximation of the game's drawing, not a device capture."""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
sys.argv_backup = sys.argv[:]
OUT = Path(sys.argv[1]); sel = sys.argv[2].split(',') if len(sys.argv) > 2 else ['dragonFlame', 'dragonScaleWard']
sys.argv = [sys.argv[0], str(OUT / '_tmp'), 'none']
src = (ROOT / 'scripts/review-skill-procedural-v1.py').read_text().split("CROP = ")[0]
env = {'__file__': str(ROOT / 'scripts/review-skill-procedural-v1.py')}
exec(compile(src, 'rv1', 'exec'), env)
OUT.mkdir(parents=True, exist_ok=True)
procfx, scene, draw, bloom, CASES, CROP = env['procfx'], env['scene'], env['draw'], env['bloom'], env['CASES'], None
hx, hy = env['hx'], env['hy']
CROP = (int(hx - 90), int(hy - 110), int(min(env["W"], hx + 700)), int(hy + 330)); PW, PH = CROP[2] - CROP[0], CROP[3] - CROP[1]
FPS = 40
fontfile = env['env']['fontfile'] if 'env' in env and 'fontfile' in env['env'] else None
def font(sz):
    for f in ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        try: return ImageFont.truetype(f, int(sz))
        except Exception: pass
    return ImageFont.load_default()
sm = lambda x: (lambda u: u * u * (3 - 2 * u))(min(1, max(0, x)))
def thump(t, t0, a, k, w, ph=0.0):
    r = t - t0; return 0.0 if r < 0 else a * math.exp(-r * k) * math.cos(r * w + ph)
def number_scale(a, dmg, rank):
    if a < 0: return 0
    return (1 - math.exp(-15 * a) * math.cos(26 * a)) * (1 + ((0.16 + .08 * rank) * math.exp(-7 * a) if dmg else 0))
def number_alpha(a): return 0 if a < 0 or a >= 1.8 else sm(a / .06) * (1 - sm((a - 1.2) / .6))
def number_rise(a, big): return (70 if big else 48) * (1 - (1 - min(1, max(0, a / 1.8))) ** 3)
SIZE = {'dmg': (50, 62, 74), 'heal': 42, 'shield': 36, 'buff': 34}
def shot(t, rel, dur, caster, targets):
    if t < 0 or t >= dur: return 0, 0, 0, 0
    tx = sum(x for x, y in targets) / len(targets); ty = sum(y for x, y in targets) / len(targets)
    spread = max(abs(x - tx) for x, y in targets)
    hold = rel + .9; w = sm(t / (rel * .45)) * (1 - sm((t - hold) / min(1.0, max(.5, dur - hold))))
    sw = sm((t - rel * .55) / (rel * .6 + .12))
    fx = caster[0] + (tx - caster[0]) * sw; fy = caster[1] + (ty - caster[1]) * sw
    wide = 1 - min(1, spread / (420 * PW / 1000)); close, at = .30, .13 + .08 * wide
    return fx, fy, w, w * (close + (at - close) * sw)
def flame_cam(t, power, rel=.46, d=1):
    c = [d * thump(t, rel, 7, 7, 28), -thump(t, rel, 4, 8, 36, .6), max(0, thump(t, rel, .045, 6, 0)), d * thump(t, rel, .008, 8, 26)]
    r = t - .9
    if 0 <= r < 1: c[1] += .9 * math.sin(t * 47) * (1 - r)
    k = 1 + (power - 1) * sm((t - rel) / .12)
    return [v * k for v in c]
def ward_cam(t, power, rel=.56):
    k = 1 + (power - 1) * sm((t - rel) / .12)
    return [0, -thump(t, rel, 3.2, 10, 30, .6) * k, max(0, thump(t, rel, .032, 9, 0)) * k, 0]

PLAN = {
 'dragonFlame': dict(cam=flame_cam, power=1.45, numbers=[('-14', 'dmg', 2, 0, (255, 226, 130)), ('-9', 'dmg', 1, .07, (255, 255, 255))]),
 'dragonScaleWard': dict(cam=ward_cam, power=1.0, numbers=[('盾 ＋6', 'shield', 0, 0, (130, 230, 255)), ('盾 ＋6', 'shield', 0, .07, (130, 230, 255))]),
}
for sid in sel:
    spec = procfx.SPEC[sid]; dur, rel = spec[0], spec[1]; geo = CASES[sid]; plan = PLAN[sid]
    chest_pts = [c for c, f in geo['targets']]; foot_pts = [f for c, f in geo['targets']]
    frames = []
    for k in range(int((dur + .15) * FPS)):
        t = k / FPS; buf = scene(t)
        lit = procfx.smooth(t / .15) * (1 - procfx.smooth((t - dur + .25) / .4))
        dm, dt = procfx.DIM[sid]
        buf *= 1 - dm * lit * np.array(dt)           # one uniform grade over the whole frame: no edge anywhere
        draw(buf, procfx.GENERATORS[sid](t, geo)); buf = bloom(buf)
        pane = Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8)).crop(CROP)
        d = ImageDraw.Draw(pane)
        for i, (txt, kind, rank, delay, col) in enumerate(plan['numbers']):
            a = t - rel - delay
            al, sc = number_alpha(a), number_scale(a, kind == 'dmg', rank)
            if al <= .01 or sc <= .01: continue
            size = (SIZE['dmg'][rank] if kind == 'dmg' else SIZE[kind]) * PW / 1000
            f = font(size); cx, cy = chest_pts[i][0] - CROP[0], chest_pts[i][1] - CROP[1]
            if kind == 'dmg': cy -= number_rise(a, True) * PW / 1000 + 6
            else: cx = foot_pts[i][0] - CROP[0] - 14 - size; cy = foot_pts[i][1] - CROP[1] - 86 * PW / 1000 - number_rise(a, False) * PW / 1000
            layer = Image.new('RGBA', (int(size * 4), int(size * 2)), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            ld.text((layer.width // 2, layer.height // 2), txt, font=f, fill=col + (int(255 * al),), anchor='mm', stroke_width=max(2, int(size / 12)), stroke_fill=(26, 18, 10, int(255 * al)))
            layer = layer.resize((max(1, int(layer.width * sc)), max(1, int(layer.height * sc))), Image.BICUBIC)
            pane.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2))) if False else pane.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)
        # camera
        fx, fy, w, z = shot(t, rel, dur, (hero := env['hero_chest']), chest_pts)
        fx -= CROP[0]; fy -= CROP[1]
        cam = plan['cam'](t, plan['power']) if t < dur else [0, 0, 0, 0]
        unit = PW / 760; zoom = z + cam[2]; S = 1 + zoom
        rot = cam[3]; maxX = max(5 * unit, PW / 2 * zoom - abs(rot) * PW / 2); maxY = 12 * unit
        tx = -(fx - PW / 2) * .9 * w * S + cam[0] * unit; ty = -(fy - PH / 2) * .6 * w * S + cam[1] * unit
        tx = max(-maxX, min(maxX, tx)); ty = max(-maxY, min(maxY, ty))
        c, s = math.cos(rot), math.sin(rot); cxp, cyp = PW / 2, PH / 2
        # output o -> input i = c + R^-1 (o - c - T) / S
        a_ = c / S; b_ = s / S; d_ = -s / S; e_ = c / S
        ox = cxp + tx; oy = cyp + ty
        coeff = (a_, b_, cxp - a_ * ox - b_ * oy, d_, e_, cyp - d_ * ox - e_ * oy)
        frames.append(pane.transform((PW, PH), Image.AFFINE, coeff, Image.BICUBIC))
    im = [f.resize((f.width // 2, f.height // 2), Image.LANCZOS).quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    im[0].save(OUT / f'{sid}-director.gif', save_all=True, append_images=im[1:], duration=25, loop=0, optimize=True)
    for tag, tt in (('closeup', rel * .5), ('release', rel + .12), ('number', rel + .3)):
        frames[min(len(frames) - 1, int(tt * FPS))].save(OUT / f'{sid}-director-{tag}.png')
    print(sid, len(frames))
