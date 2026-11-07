#!/usr/bin/env python3
"""Offline design preview of the battle hit feel: old (build43/66 formulas) vs new (scripts/battle-hitfeel).

Same scene, hero pose clock, monster art, debris field and contact point as the production offline review
(`review-battle-effects-demo.py`). Not UIKit, not a device capture: lighting is an approximation.
Usage: python3 -I scripts/review-hit-feel-v1.py
"""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFont

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/battle-hitfeel'))
import hitfeel as hf

OUT = ROOT / 'Art/Review/Battle/hit-feel-v1'
OUT.mkdir(parents=True, exist_ok=True)
base = ROOT / 'scripts/review-battle-effects-demo.py'
env = {'__file__': str(base)}
# The base review looks for Noto CJK; on this machine only the WenQuanYi font exists, so patch the path list in memory.
source = base.read_text().replace("'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',", "'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',")
exec(compile(source.split('\nframes=[]; traces=[]')[0], str(base), 'exec'), env)
W, H = env['W'], env['H']
plate, foreground, render, sample, asset = env['plate'], env['foreground'], env['render'], env['sample'], env['asset']
hs, es, hx, hy, ex, ey = [env[k] for k in ['hs', 'es', 'hx', 'hy', 'ex', 'ey']]
shadow, light, enemy, impact, travel = env['shadow'], env['light'], env['enemy'], env['impact'], env['travel']
font_file = next(p for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                             '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'] if Path(p).exists())
SPR = {n: asset('BattleVFX' + n) for n in ['Slash', 'HeavyArc', 'HeavySpray', 'Burst', 'Mote', 'GoldEmber', 'GroundSpark', 'HeavyHitMask']}
CONTACT = 1.048          # MeadowBattleImpactClock.strikeContact
DURATION = 1.70


def pose_time(e):
    a = max(0, e - 0.4)
    return max(0, a - min(0.10, max(0, a - 0.648)))


def approach(p):
    if p < 0.12 or p >= 1: return 0.0
    if 0.40 <= p <= 0.66: return 1.0
    t = (p - 0.12) / 0.28 if p < 0.40 else (1 - p) / 0.34
    return hf.smooth(t)


def add(frame, layer):
    premul = ImageChops.multiply(layer.convert('RGB'), layer.getchannel('A').convert('RGB'))
    frame.paste(ImageChops.add(frame.convert('RGB'), premul).convert('RGBA'))


def sprite_add(frame, name, center, size, alpha, angle=0.0):
    if alpha <= 0 or size[0] < 1 or size[1] < 1: return
    im = SPR[name].resize((max(1, round(size[0])), max(1, round(size[1]))), Image.Resampling.LANCZOS)
    if angle: im = im.rotate(-math.degrees(angle), resample=Image.Resampling.BICUBIC, expand=True)
    im.putalpha(im.getchannel('A').point(lambda v: round(v * min(1, alpha))))
    layer = Image.new('RGBA', frame.size)
    layer.alpha_composite(im, (round(center[0] - im.width / 2), round(center[1] - im.height / 2)))
    add(frame, layer)


def debris(a, origin, floor):
    """Port of MeadowBattleLightField.sample(.strike): ballistic embers with two ground rebounds."""
    out = []
    for i in range(34):
        life = 1.22 + hf.fraction(i, 5) * 0.4
        if a < 0 or a >= life: continue
        fl = floor + (i % 5 - 2) * 2.5
        spread = (((i * 73 + 3 * 37) % 101) / 100.0)
        ang = i * 2.399
        vx = 20 + math.cos(ang) * (85 + spread * 95)
        vy = -80 - (((i * 73 + 13 * 37) % 101) / 100.0) * 170
        x, y = origin[0], min(origin[1], fl - 2)
        g = 340.0
        remaining, contacts, last_age = a, 0, None
        for bounce in range(3):
            flight = (-vy + math.sqrt(vy * vy + 2 * g * (fl - y))) / g
            if remaining < flight:
                x += vx * remaining; y += vy * remaining + g * remaining * remaining / 2; vy += g * remaining
                if last_age is not None: last_age += remaining
                break
            x += vx * flight; y = fl; remaining -= flight; contacts += 1; last_age = remaining
            if bounce == 2: break
            vx *= 0.62; vy = -(vy + g * flight) * 0.32
            if remaining == 0: break
            last_age = 0
        fade = max(0, 1 - a / life) ** 0.65
        out.append((x, min(y, fl), math.atan2(vy, vx), 6 + hf.fraction(i, 17) * 7, fade, last_age if contacts else None))
    return out


def text_layer(text, size, color, outline=(38, 26, 10)):
    f = ImageFont.truetype(font_file, size)
    probe = Image.new('RGBA', (10, 10)); d = ImageDraw.Draw(probe)
    box = d.textbbox((0, 0), text, font=f, stroke_width=3)
    im = Image.new('RGBA', (box[2] - box[0] + 8, box[3] - box[1] + 8))
    ImageDraw.Draw(im).text((4 - box[0], 4 - box[1]), text, font=f, fill=(*color, 255), stroke_width=3, stroke_fill=(*outline, 255))
    return im


def monster_overlay(frame, m, pos, scale_xy, alpha):
    white = Image.new('RGBA', m.size, (255, 248, 225, 0)); white.putalpha(m.getchannel('A').point(lambda v: round(v * alpha)))
    white = white.resize((round(m.width * scale_xy[0] * es), round(m.height * scale_xy[1] * es)), Image.Resampling.NEAREST)
    frame.alpha_composite(white, (round(pos[0]), round(pos[1])))


def cast_dim(e):
    t = e
    envelope = (0.45 + (0.64 - 0.45) * hf.smooth(t / 0.44)) * (1 - hf.smooth((t - 2) / 1.36))
    age = t - CONTACT
    peak = hf.smooth(age / 0.035) if 0 <= age < 0.035 else (1 - hf.smooth((age - 0.035) / 0.19)) if 0.035 <= age < 0.225 else 0
    return max(envelope, 0.82 * peak)


def camera_warp(frame, dx, dy, zoom, rot):
    s = 1 + zoom; c, sn = math.cos(rot), math.sin(rot); cx, cy = W / 2, H / 2
    # out = C + s*R*(in-C) + t  =>  in = C + R^-1 (out - C - t) / s
    a, b = c / s, sn / s; d, e2 = -sn / s, c / s
    cc = cx - (a * (cx + dx) + b * (cy + dy)); ff = cy - (d * (cx + dx) + e2 * (cy + dy))
    return frame.transform((W, H), Image.Transform.AFFINE, (a, b, cc, d, e2, ff), Image.Resampling.BICUBIC)


def render_scene(e, mode, tier, damage):
    a = e - CONTACT
    p = min(1, pose_time(e) / 1.2)
    attacking = 0.4 <= e < DURATION
    clip = 'attack' if attacking else 'idle'
    hero = render(clip, p if attacking else (e % 2.4) / 2.4)
    tx = travel * approach(p) if attacking else 0
    # monster motion
    if mode == 'old':
        recoil = W * 0.025 * ((hf.smooth((a + 0.02) / 0.16) if a <= 0.14 else 1 - hf.smooth((a - 0.14) / 0.38)) if a > -0.02 else 0)
        sx = sy = 1.0
    else:
        recoil = hf.knockback(a, tier, W) if a >= 0 else 0
        sx, sy = hf.squash(a, tier) if a >= 0 else (1.0, 1.0)
    dim = cast_dim(e) if e < CONTACT + 1.5 else 0
    scene = ImageEnhance.Brightness(plate).enhance(1 - dim)
    foot_x, foot_y = ex + 178.5 * es + recoil, ey + 241 * es
    mpos = (foot_x - 178.5 * es * sx, foot_y - 241 * es * sy)
    shadow(scene, enemy, ex + recoil, ey, es)
    shadow(scene, hero, hx + tx, hy, hs)
    scene.alpha_composite(hero.resize((round(256 * hs), round(256 * hs)), Image.Resampling.NEAREST), (round(hx + tx), round(hy)))
    monster = ImageEnhance.Brightness(enemy).enhance(1 - dim * .55)
    scene.alpha_composite(monster.resize((round(enemy.width * es * sx), round(enemy.height * es * sy)), Image.Resampling.NEAREST), (round(mpos[0]), round(mpos[1])))
    if mode == 'new':
        fl = hf.flash(a)
        if fl > 0:
            monster_overlay(scene, enemy, mpos, (sx, sy), fl * 0.16)          # faint whole-body tint
            mask = SPR['HeavyHitMask'].resize((round(enemy.width * es * sx), round(enemy.height * es * sy)), Image.Resampling.LANCZOS)
            layer = Image.new('RGBA', scene.size); layer.alpha_composite(mask, (round(mpos[0]), round(mpos[1])))
            layer.putalpha(layer.getchannel('A').point(lambda v: round(v * fl * 0.95))); add(scene, layer)
    else:
        if 0 <= a < 0.22:
            alpha = 0.85 * (hf.smooth((a + 0.04) / 0.08) if a < 0.04 else 1 - hf.smooth((a - 0.04) / 0.18))
            mask = SPR['HeavyHitMask'].resize((round(enemy.width * es), round(enemy.height * es)), Image.Resampling.LANCZOS)
            layer = Image.new('RGBA', scene.size); layer.alpha_composite(mask, (round(mpos[0]), round(mpos[1])))
            layer.putalpha(layer.getchannel('A').point(lambda v: round(v * alpha))); add(scene, layer)
    scene.alpha_composite(foreground)
    ip = (impact[0] + (tx - travel * approach(min(1, pose_time(CONTACT) / 1.2))) * 0, impact[1])
    floor = ey + 240 * es
    if a >= 0:
        draw_impact(scene, a, mode, tier, damage, ip, floor, foot_x)
    if mode == 'old':
        shake = 4 * (1 - hf.smooth(a / 0.28)) if 0 <= a < 0.5 else 0
        zoom = 0.045 * (1 - hf.smooth(a / 0.5)) if 0 <= a < 0.5 else 0
        cam = (math.sin(a * 83) * shake, math.cos(a * 64) * shake * 0.55, zoom, 0.0) if a >= 0 else (0, 0, 0, 0)
    else:
        cam = hf.camera(a, tier, 1.0) if a >= 0 else (0, 0, 0, 0)
    return camera_warp(scene, *cam)


def draw_impact(scene, a, mode, tier, damage, ip, floor, foot_x):
    ss = 2
    # keep the weapon sweep (slash + arc); the large bloom is what the new design replaces
    burst = hf.pulse(a, -0.035, 0.035, 0.52) if hasattr(hf, 'pulse') else (hf.smooth((a + .035) / .07) if a <= .035 else 1 - hf.smooth((a - .035) / .485))
    slash = (hf.smooth((a + .06) / .06) if a <= 0 else 1 - hf.smooth(a / .25))
    spread = max(0, a)
    if mode == 'old':
        sprite_add(scene, 'Slash', ip, (225, 225), slash)
        sprite_add(scene, 'HeavyArc', ip, (225 + spread * 300,) * 2, burst * .9, -0.65 + spread * 3.8)
        echo = hf.smooth((a - .10) / .09) if a <= .19 else 1 - hf.smooth((a - .19) / .46)
        sprite_add(scene, 'HeavyArc', (ip[0] + spread * 22, ip[1]), (285 + spread * 160, 225 + spread * 170), echo * .38)
        sprite_add(scene, 'Burst', ip, (205 + spread * 145,) * 2, burst)
        sprite_add(scene, 'HeavySpray', (ip[0] + 95 + spread * 75, ip[1] - 15), (250 + spread * 180, 160), burst * .9)
        for i in range(26):
            ang = i * 2.399; d = spread * (150 + (i % 5) * 38)
            sprite_add(scene, 'Mote', (ip[0] + math.cos(ang) * d, ip[1] + math.sin(ang) * d), (22 if i % 4 == 0 else 10, 7 if i % 4 == 0 else 10), burst * .9)
        light(scene, (ip[0] + 20, floor), (235 / 2, 55 / 2), burst * .76)
        light(scene, ip, (195 / 2, 190 / 2), burst * .48)
    else:
        sprite_add(scene, 'Slash', ip, (190, 190), slash * .8)
        sprite_add(scene, 'HeavyArc', ip, (170 + spread * 220,) * 2, burst * .55, -0.65 + spread * 3.8)
        light(scene, ip, (60, 60), hf.flash(a) * .55)
        light(scene, (ip[0] + 20, floor), (110, 24), burst * .30)
        layer = Image.new('RGBA', (W * ss, H * ss)); d = ImageDraw.Draw(layer)
        P = lambda x, y: ((ip[0] + x) * ss, (ip[1] + y) * ss)
        fl = hf.flare(a, tier)
        if fl:
            R, al = fl; c = round(255 * al)
            for length, thick, ang in [(R * 2.2, R * .16, -0.30), (R * 1.25, R * .13, 1.2), (R * 1.0, R * .10, -1.45)]:
                ca, sa = math.cos(ang), math.sin(ang)
                pts = [P(ca * length, sa * length), P(-sa * thick, ca * thick), P(-ca * length, -sa * length), P(sa * thick, -ca * thick)]
                d.polygon(pts, fill=(255, 235, 170, c))
            cx, cy = P(0, 0); d.ellipse((cx - R * .30 * ss, cy - R * .30 * ss, cx + R * .30 * ss, cy + R * .30 * ss), fill=(255, 255, 255, c))
        rg = hf.ring(a, tier)
        if rg:
            r, wid, al = rg; cx, cy = P(0, 0)
            d.ellipse((cx - r * ss, cy - r * .82 * ss, cx + r * ss, cy + r * .82 * ss), outline=(255, 225, 150, round(255 * al)), width=max(1, round(wid * ss)))
        for hx_, hy_, tx_, ty_, wid, al, heat in hf.sparks(a, tier, 1.0):
            col = (255, round(255 - 90 * heat), round(215 - 175 * heat), round(255 * al))
            d.line([P(tx_, ty_), P(hx_, hy_)], fill=col, width=max(1, round(wid * ss)))
        add(scene, layer.resize((W, H), Image.Resampling.LANCZOS))
        dl = Image.new('RGBA', (W, H)); dd = ImageDraw.Draw(dl)
        for dx, rx, ry, al in hf.dust(a, tier):
            dd.ellipse((foot_x + dx - rx + 10, floor - ry, foot_x + dx + rx + 10, floor + ry), fill=(190, 175, 140, round(255 * al)))
        scene.alpha_composite(dl)
        ll = Image.new('RGBA', (W, H)); ld = ImageDraw.Draw(ll)
        for x, y, rot, size, al, tone in hf.leaves(a, tier, 1.0):
            cx, cy = ip[0] + x, ip[1] + y
            ca, sa = math.cos(rot), math.sin(rot)
            pts = [(cx + ca * size - sa * 0, cy + sa * size), (cx - sa * size * .45, cy + ca * size * .45), (cx - ca * size, cy - sa * size), (cx + sa * size * .45, cy - ca * size * .45)]
            ld.polygon(pts, fill=[(86, 142, 62), (128, 176, 74), (60, 112, 52)][tone] + (round(235 * al),))
        scene.alpha_composite(ll)
    for pxx, pyy, ang, size, fade, gage in debris(a, ip, floor):
        sprite_add(scene, 'GoldEmber', (pxx, pyy), (size * 2.2, size * 1.5), fade * .8, ang - math.pi * .75)
        if gage is not None and gage < .24:
            sprite_add(scene, 'GroundSpark', (pxx, floor), (30, 12), (1 - gage / .24) * fade * .9)
    # damage number
    if mode == 'old':
        if a < 0.7:
            t = text_layer(f'-{damage}', 23, (255, 255, 255)); scene.alpha_composite(t, (round(ip[0] - t.width / 2), round(ip[1] - t.height / 2 - a * 30)))
    else:
        n = hf.number(a, tier)
        if n:
            pop, rise, al, size = n
            t = text_layer(f'-{damage}', round(size), (255, 226, 130) if tier == 'heavy' else (255, 255, 255))
            t = t.resize((max(1, round(t.width * pop)), max(1, round(t.height * pop))), Image.Resampling.LANCZOS)
            t.putalpha(t.getchannel('A').point(lambda v: round(v * al)))
            scene.alpha_composite(t, (round(ip[0] - t.width / 2), round(ip[1] - t.height / 2 + rise - 6)))


CROP = (120, 150, 720, 580)
FONT = ImageFont.truetype(font_file, 15)


def labelled(img, text):
    f = img.crop(CROP).convert('RGB'); d = ImageDraw.Draw(f)
    d.rectangle((0, 0, f.width, 24), fill=(14, 22, 20)); d.text((8, 3), text, font=FONT, fill=(245, 232, 199))
    return f


def main():
    only_sheets = '--sheets' in sys.argv
    cases = [('normal-attack', 'medium', 9, '普通攻击 · 中档（伤害 9）'), ('strong-strike', 'heavy', 16, '强击 · 重档（伤害 16）')]
    for name, tier, damage, title in ([] if only_sheets else cases):
        frames = []
        t = 0.82
        while t < 1.82:
            old, new = render_scene(t, 'old', tier, damage), render_scene(t, 'new', tier, damage)
            a, b = labelled(old, '现在 · ' + title), labelled(new, '新 · ' + title)
            sheet = Image.new('RGB', (a.width + b.width + 6, a.height), (40, 40, 40)); sheet.paste(a, (0, 0)); sheet.paste(b, (a.width + 6, 0))
            ImageDraw.Draw(sheet).text((a.width + 6 + b.width - 150, 3), f'接触后 {t - CONTACT:+.2f}s', font=FONT, fill=(190, 200, 190))
            frames.append(sheet); t += 0.02
        packed = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
        packed[0].save(OUT / f'{name}-old-vs-new-real-speed.gif', save_all=True, append_images=packed[1:], duration=20, loop=0, optimize=True)
        # slow version (x4) to read the 0.1 s freeze
        packed[0].save(OUT / f'{name}-old-vs-new-slow.gif', save_all=True, append_images=packed[1:], duration=80, loop=0, optimize=True)
    # timeline sheet for the normal attack (new only) and tier comparison at contact
    times = [-0.06, 0.0, 0.04, 0.09, 0.14, 0.20, 0.30, 0.50]
    cells = [labelled(render_scene(CONTACT + a, 'new', 'medium', 9), f'a={a:+.2f}s').resize((300, 215), Image.Resampling.LANCZOS) for a in times]
    S = Image.new('RGB', (4 * 300, 2 * 215)); [S.paste(c, ((i % 4) * 300, (i // 4) * 215)) for i, c in enumerate(cells)]
    S.save(OUT / 'normal-attack-timeline.png')
    tiers = [('light', 4), ('medium', 9), ('heavy', 16)]
    cells = [labelled(render_scene(CONTACT + a, 'new', tr, dm), f'{tr} · a={a:+.2f}s').resize((300, 215), Image.Resampling.LANCZOS) for tr, dm in tiers for a in (0.02, 0.07, 0.18)]
    S = Image.new('RGB', (3 * 300, 3 * 215)); [S.paste(c, ((i % 3) * 300, (i // 3) * 215)) for i, c in enumerate(cells)]
    S.save(OUT / 'tiers-comparison.png')


if __name__ == '__main__':
    main()
