#!/usr/bin/env python3
"""Offline two-weapon action studies on the existing fixed battle scene.

The two animations are original presentation candidates.  They do not call
GameCore, change HP, simulate an equipped item, or capture an app/device.
"""
from pathlib import Path
import argparse
import copy
import json
import math
import random
import shutil
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy.interpolate import CubicHermiteSpline, PchipInterpolator

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "Sources/Resources/Assets.xcassets"
SPEC = ROOT / "Art/Scenes/MeadowBattle/b2-weapon-actions-v1/action-poses.json"
OUT = ROOT / "Art/Review/Battle/b2-weapons-v1"
OUT.mkdir(parents=True, exist_ok=True)
params = json.loads(SPEC.read_text())
W, H = 800, 480
HERO_FOOT = tuple(params["heroFoot"])
ENEMY_FOOT = tuple(params["enemyFoot"])
HS, ES = params["actorScale"], params["enemyScale"]
LENGTH = params["durationSeconds"]
try:
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 14)
except OSError:
    font = ImageFont.load_default()


def asset(name):
    folder = ASSETS / (name + ".imageset")
    filename = json.loads((folder / "Contents.json").read_text())["images"][0]["filename"]
    return Image.open(folder / filename).convert("RGBA")


renderer = ROOT / "Art/Scenes/MeadowBattle/hero-combat-v2/render-review.py"
ns = {"__file__": str(renderer)}
exec(compile(renderer.read_text().split("\nfor clip,data in lib['clips'].items():")[0],
             str(renderer), "exec"), ns)
library = json.loads((ASSETS / "MeadowBattleHeroAnimationV2.dataset/animation.json").read_text())
original_layers = dict(ns["LAYERS"])
weapon_images = {
    item: Image.open(ROOT / "Art/Parts/P1-v1/b2-equipment-v1" / item / "battle-weapon.png").convert("RGBA")
    for item in ("greatSword", "legendaryStaff")
}


def continuous_keys(keys):
    """Shape-preserving joint curves, with a stationary start and finish."""
    times = np.array([key["t"] for key in keys], dtype=float)
    fields = ("lean", "crouch", "shoulder", "elbow", "wrist",
              "nearHip", "nearKnee", "farHip", "farKnee", "flash", "recoil")
    samples = np.linspace(0, 1, 241)
    output = [{"t": float(t), "root": [0., 0.]} for t in samples]
    for field in (*fields, "rootX", "rootY"):
        values = np.array([key["root"][0 if field == "rootX" else 1]
                           if field.startswith("root") else key[field] for key in keys])
        slopes = PchipInterpolator(times, values).derivative()(times)
        slopes[0] = slopes[-1] = 0
        curve = CubicHermiteSpline(times, values, slopes)(samples)
        for sample, value in zip(output, curve):
            if field.startswith("root"):
                sample["root"][0 if field == "rootX" else 1] = float(value)
            else:
                sample[field] = float(value)
    return output


motion_keys = {item: continuous_keys(keys) for item, keys in params["poseKeys"].items()}
# Add a compact leg cycle during the airborne approach and backward recovery.
# It goes to zero at each end so it joins the authored planted poses.
for key in motion_keys["greatSword"]:
    when = params["motionStartsAt"] + key["t"] * params["motionDuration"]
    if .33 < when < .89:
        phase, amplitude = (when - .33) / .56, .38
    elif 1.32 < when < 1.76:
        phase, amplitude = (when - 1.32) / .44, .20
    else:
        continue
    swing = amplitude * math.sin(math.tau * phase) * math.sin(math.pi * phase)
    key["nearHip"] += swing
    key["farHip"] -= swing * .72
    key["nearKnee"] += .16 * max(0, -swing / amplitude)
    key["farKnee"] += .12 * max(0, swing / amplitude)
enemy = asset("MeadowBattleForestWarden").resize(
    (round(384 * ES), round(256 * ES)), Image.Resampling.NEAREST
)
burst = asset("BattleVFXBurst")
arc = asset("BattleVFXHeavyArc")


def clamp(v):
    return min(1., max(0., v))


def smooth(v):
    v = clamp(v)
    return v * v * (3 - 2 * v)


def pulse(t, start, peak, end):
    if t < start or t > end:
        return 0.
    return smooth((t - start) / (peak - start)) if t < peak else 1 - smooth((t - peak) / (end - peak))


def configure(item):
    ns["lib"] = copy.deepcopy(library)
    ns["lib"]["clips"]["attack"]["keys"] = motion_keys[item]
    ns["LAYERS"] = dict(original_layers, MeadowBattleHeroWeapon=weapon_images[item])


def motion(t):
    return clamp((t - params["motionStartsAt"]) / params["motionDuration"])


def point(q, pose, root):
    pivot, offset, angle = pose
    x, y = q[0] - pivot[0], q[1] - pivot[1]
    return (pivot[0] + offset[0] + x * math.cos(angle) - y * math.sin(angle) + root[0],
            pivot[1] + offset[1] + x * math.sin(angle) + y * math.cos(angle) + root[1])


def blade_point(t, foot, reference):
    transforms, root, _, _, _ = ns["sample"]("attack", motion(t))
    x, y = point(reference, transforms["MeadowBattleHeroWeapon"], root)
    return (foot[0] + (x - 123) * HS, foot[1] + (y - 214) * HS)


configure("greatSword")
hit_pose = blade_point(params["swordImpactAt"], HERO_FOOT, params["swordTipRest"])
approach = params["targetContactX"] - hit_pose[0]
impact = (hit_pose[0] + approach, hit_pose[1])


def sword_foot(t):
    go = smooth((t - 0.33) / 0.56)
    back = smooth((t - 1.32) / 0.44)
    # Lift during the dash and land before contact. A light backward hop
    # carries the recovery, so neither translation drags a planted foot.
    u = clamp((t - 0.33) / .56)
    v = clamp((t - 1.32) / .44)
    lift = 22 * math.sin(math.pi * u) if .33 < t < .89 else 10 * math.sin(math.pi * v) if 1.32 < t < 1.76 else 0
    return (HERO_FOOT[0] + approach * go * (1 - back), HERO_FOOT[1] - lift)


def resized_layer(name):
    return asset(name).resize((800, 734), Image.Resampling.LANCZOS).crop((0, 135, 800, 615))


background = Image.new("RGBA", (W, H))
for name in ("MeadowCampFarForest", "MeadowCampGround", "MeadowCampMidground"):
    background.alpha_composite(resized_layer(name))
foreground = resized_layer("MeadowCampForeground")
black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
yy, xx = np.mgrid[:128, :128]
falloff = np.clip(1 - np.sqrt(((xx - 63.5) / 63.5) ** 2 + ((yy - 63.5) / 63.5) ** 2), 0, 1)
falloff = (falloff ** 1.6 * 255).astype("uint8")


def glow(frame, center, radii, color, power):
    if power <= 0:
        return
    width, height = max(1, round(radii[0] * 2)), max(1, round(radii[1] * 2))
    mask = Image.fromarray(falloff, "L").resize((width, height), Image.Resampling.BILINEAR)
    mask = mask.point(lambda v: round(v * min(1., power)))
    light = Image.new("RGB", (width, height), color)
    light = ImageChops.multiply(light, mask.convert("RGB"))
    x, y = round(center[0] - width / 2), round(center[1] - height / 2)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + width), min(H, y + height)
    if x0 >= x1 or y0 >= y1:
        return
    region = frame.crop((x0, y0, x1, y1)).convert("RGB")
    lit = ImageChops.add(region, light.crop((x0 - x, y0 - y, x1 - x, y1 - y)))
    frame.paste(lit, (x0, y0))


def stamp(frame, image, center, size, opacity=1., angle=0, additive=True):
    if opacity <= 0:
        return
    image = image.resize((max(1, round(size[0])), max(1, round(size[1]))), Image.Resampling.LANCZOS)
    if angle:
        image = image.rotate(-angle, Image.Resampling.BICUBIC, expand=True)
    image.putalpha(image.getchannel("A").point(lambda a: round(a * clamp(opacity))))
    x, y = round(center[0] - image.width / 2), round(center[1] - image.height / 2)
    if not additive:
        frame.alpha_composite(image, (x, y))
        return
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + image.width), min(H, y + image.height)
    if x0 >= x1 or y0 >= y1:
        return
    source = image.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    premul = ImageChops.multiply(source.convert("RGB"), source.getchannel("A").convert("RGB"))
    frame.paste(ImageChops.add(frame.crop((x0, y0, x1, y1)).convert("RGB"), premul), (x0, y0))


def shadow(frame, foot, width, strength=0.38):
    layer = Image.new("RGBA", (round(width * 2), 42))
    ImageDraw.Draw(layer).ellipse((width * .15, 11, width * 1.85, 31),
                                  fill=(3, 8, 5, round(strength * 255)))
    layer = layer.filter(ImageFilter.GaussianBlur(5))
    frame.alpha_composite(layer, (round(foot[0] - width), round(foot[1] - 20)))


def enemy_sprite(frame, hit_age):
    recoil = pulse(hit_age, 0, .08, .48)
    pos = (round(ENEMY_FOOT[0] - 178.5 * ES + recoil * 7),
           round(ENEMY_FOOT[1] - 240 * ES))
    shadow(frame, (ENEMY_FOOT[0] + recoil * 4, ENEMY_FOOT[1]), 103, .55)
    sprite = enemy.copy()
    flash = pulse(hit_age, -.015, .04, .2) * .46
    if flash:
        white = Image.new("RGBA", sprite.size, (255, 251, 220, 0))
        white.putalpha(sprite.getchannel("A").point(lambda a: round(a * flash)))
        sprite.alpha_composite(white)
    frame.alpha_composite(sprite, pos)


def hero_sprite(frame, t, foot):
    actor = ns["render"]("attack", motion(t))
    shadow(frame, (foot[0], HERO_FOOT[1]), 62, .30 if foot[1] < HERO_FOOT[1] - 2 else .38)
    actor = actor.resize((round(256 * HS), round(256 * HS)), Image.Resampling.NEAREST)
    frame.alpha_composite(actor, (round(foot[0] - 123 * HS), round(foot[1] - 214 * HS)))


def screen_layer(frame, overlay):
    # Add light instead of obscuring bodies with an opaque painted polygon.
    rgb = overlay.convert("RGB")
    premul = ImageChops.multiply(rgb, overlay.getchannel("A").convert("RGB"))
    frame.paste(ImageChops.add(frame.convert("RGB"), premul), (0, 0))


def particles(frame, age, color, seed):
    if age < 0 or age > 1.15:
        return
    rng = random.Random(seed)
    overlay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(overlay)
    ground = ENEMY_FOOT[1] + 2
    for i in range(34):
        delay = rng.uniform(0, .16)
        vx = rng.uniform(-145, 215)
        vy = rng.uniform(-190, 10)
        gravity = rng.uniform(390, 580)
        life = rng.uniform(.55, 1.05)
        a = age - delay
        if a < 0 or a > life:
            continue
        x = impact[0] + vx * a
        y = impact[1] + vy * a + .5 * gravity * a * a
        if y > ground:
            disc = vy * vy + 2 * gravity * (ground - impact[1])
            landing = (-vy + math.sqrt(max(0, disc))) / gravity
            since = a - landing
            if since > .25:
                continue
            y = ground - max(0, 32 * since - 105 * since * since)
            if 0 < since < .10 and i % 3 == 0:
                glow(frame, (x, ground), (15, 5), color, .23 * (1 - since / .10))
        alpha = round(225 * (1 - smooth(a / life)))
        length = max(2, 10 * (1 - a / life))
        d.line((x, y, x - vx * .035, y - vy * .025 - length * .15),
               fill=(*color, alpha), width=2 if i % 3 else 3)
        d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(255, 248, 222, alpha))
    screen_layer(frame, overlay)


def staff_projectile(frame, t):
    release = params["staffReleaseAt"]
    hit = params["staffImpactAt"]
    current = blade_point(t, HERO_FOOT, params["staffGemRest"])
    build = pulse(t, .42, .91, 1.10)
    glow(frame, current, (48, 40), (20, 165, 255), build * .36)
    if .42 < t < release:
        overlay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(overlay)
        for i in range(3):
            phase = t * 6.5 + i * math.tau / 3
            x = current[0] + math.cos(phase) * (11 + i * 3)
            y = current[1] + math.sin(phase) * (7 + i * 2)
            radius = 2 + i
            d.ellipse((x-radius, y-radius, x+radius, y+radius),
                      fill=(80, 213, 255, round(build * 190)))
        screen_layer(frame, overlay)
    if not release <= t <= hit:
        return
    start = blade_point(release, HERO_FOOT, params["staffGemRest"])
    u = clamp((t - release) / (hit - release))
    # Short arcing projectile, with its tail behind the moving head.
    def path(v):
        return ((1-v)*start[0] + v*impact[0],
                (1-v)*start[1] + v*impact[1] - 40 * math.sin(math.pi * v))
    head = path(u)
    points = [path(max(0, u - k * .045)) for k in range(7, -1, -1)]
    overlay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(overlay)
    d.line(points, fill=(37, 145, 250, 105), width=13, joint="curve")
    d.line(points, fill=(104, 228, 255, 185), width=5, joint="curve")
    d.line(points, fill=(239, 255, 255, 250), width=2, joint="curve")
    d.ellipse((head[0]-5, head[1]-5, head[0]+5, head[1]+5), fill=(220, 252, 255, 240))
    screen_layer(frame, overlay)
    glow(frame, head, (40, 30), (30, 174, 255), .45)


def sword_effect(frame, t):
    hit = params["swordImpactAt"]
    age = t - hit
    # Recent physical blade-tip positions form the arc; the contact point is
    # the same point used by the monster reaction, burst, and ground sparks.
    if .88 <= t <= 1.14:
        points = []
        for k in range(9, -1, -1):
            earlier = max(.88, t - k * .013)
            points.append(blade_point(earlier, sword_foot(earlier), params["swordTipRest"]))
        overlay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(overlay)
        a = pulse(t, .88, 1.02, 1.14)
        d.line(points, fill=(245, 147, 38, round(100*a)), width=15, joint="curve")
        d.line(points, fill=(255, 216, 130, round(210*a)), width=6, joint="curve")
        d.line(points, fill=(255, 252, 221, round(250*a)), width=2, joint="curve")
        screen_layer(frame, overlay)
    intensity = pulse(age, -.025, .035, .43)
    glow(frame, impact, (110, 105), (255, 167, 60), intensity * .55)
    glow(frame, (impact[0], ENEMY_FOOT[1]), (125, 24), (255, 178, 50), intensity * .60)
    stamp(frame, burst, impact, (85 + max(0, age)*220, 85 + max(0, age)*220), intensity * .88)
    stamp(frame, arc, (impact[0] + 4, impact[1] + 8),
          (170 + max(0, age)*90, 160 + max(0, age)*90), intensity * .60, angle=-18 + age*80)
    particles(frame, age, (255, 182, 66), 711)


def staff_effect(frame, t):
    staff_projectile(frame, t)
    age = t - params["staffImpactAt"]
    intensity = pulse(age, -.02, .035, .46)
    glow(frame, impact, (108, 100), (38, 180, 255), intensity * .58)
    glow(frame, (impact[0], ENEMY_FOOT[1]), (112, 22), (38, 194, 240), intensity * .52)
    if intensity:
        overlay = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(overlay)
        scale = 22 + max(0, age) * 120
        x, y = impact
        d.polygon([(x, y-scale*1.4),(x+scale*.23,y-scale*.2),(x+scale,y),
                   (x+scale*.23,y+scale*.2),(x,y+scale*1.4),
                   (x-scale*.23,y+scale*.2),(x-scale,y),(x-scale*.23,y-scale*.2)],
                  fill=(115, 229, 255, round(intensity*200)))
        d.ellipse((x-scale*.18,y-scale*.18,x+scale*.18,y+scale*.18),
                  fill=(246, 255, 255, round(intensity*255)))
        for k in range(3):
            radius = scale * (.7 + k * .38)
            d.arc((x-radius,y-radius*.5,x+radius,y+radius*.5),
                  start=15+k*24+age*90,end=110+k*24+age*90,
                  fill=(75, 201, 255, round(intensity*180)),width=2)
        screen_layer(frame, overlay)
    particles(frame, age, (83, 208, 255), 393)


def frame(item, t):
    configure(item)
    hit_at = params["swordImpactAt"] if item == "greatSword" else params["staffImpactAt"]
    dark = smooth((t - .10) / .42) * (1 - smooth((t - hit_at - .20) / .55))
    dark *= .43 if item == "legendaryStaff" else .32
    result = Image.blend(background, black, dark)
    hit_age = t - hit_at
    # Light touches the scene below the actors, then short flashes also light
    # the monster itself and foreground.
    color = (255, 168, 60) if item == "greatSword" else (50, 188, 255)
    power = pulse(hit_age, -.015, .04, .45)
    glow(result, (impact[0], ENEMY_FOOT[1]), (175, 42), color, power * .36)
    enemy_sprite(result, hit_age)
    hero_sprite(result, t, sword_foot(t) if item == "greatSword" else HERO_FOOT)
    result.alpha_composite(Image.blend(foreground, Image.new("RGBA", foreground.size),
                                       dark * .55))
    if item == "greatSword":
        sword_effect(result, t)
    else:
        staff_effect(result, t)
    return result.convert("RGB")


def make_stills():
    stamps = [0, .35, .7, .9, 1.0, 1.04, 1.12, 1.25, 1.33, 1.48, 1.8, 2.25]
    for item in ("greatSword", "legendaryStaff"):
        configure(item)
        board = Image.new("RGB", (1200, 1040), "#20372a")
        draw = ImageDraw.Draw(board)
        for n, t in enumerate(stamps):
            im = frame(item, t)
            x, y = (n % 3) * 400, (n // 3) * 260
            board.paste(im.resize((400, 240), Image.Resampling.LANCZOS), (x, y))
            draw.text((x + 4, y + 242), f"{item} {t:.3f} s", fill="white", font=font)
            if t in (0, 1.04, 1.25, 1.48):
                im.save(OUT / f"{item}-{t:.2f}.png")
        board.save(OUT / f"{item}-study.png")
    print("Study boards rendered; impact point", impact)


def make_media():
    tmp = Path(tempfile.gettempdir()) / "b2-weapon-review-frames"
    tmp.mkdir(exist_ok=True)
    for item in ("greatSword", "legendaryStaff"):
        folder = tmp / item
        folder.mkdir(exist_ok=True)
        total = round(LENGTH * 60)
        for n in range(total):
            frame(item, n / 60).save(folder / f"{n:04}.png")
            if n % 30 == 0:
                print(item, n, "/", total, flush=True)
        video = OUT / f"{item}-scene-60fps.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "60", "-i",
                        str(folder / "%04d.png"), "-c:v", "libx264", "-crf", "19",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], check=True)
        source = [Image.open(folder / f"{round(n*60/50):04}.png").convert("RGB")
                  for n in range(round(LENGTH*50))]
        sample = Image.new("RGB", (W*3, H*3))
        for n, idx in enumerate((0, 15, 30, 45, 52, 62, 70, 85, 110)):
            sample.paste(source[idx], ((n % 3)*W, (n // 3)*H))
        palette = sample.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        encoded = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in source]
        path = OUT / f"{item}-scene-normal.gif"
        encoded[0].save(path, save_all=True, append_images=encoded[1:], duration=20,
                        loop=0, disposal=1, optimize=True)
        optimizer = shutil.which("gifsicle")
        if not optimizer and Path("/workspace/gifsicle-1.96/src/gifsicle").is_file():
            optimizer = "/workspace/gifsicle-1.96/src/gifsicle"
        if optimizer:
            optimized = path.with_suffix(".optimized.gif")
            subprocess.run([optimizer, "-O3", str(path), "-o", str(optimized)], check=True)
            optimized.replace(path)
        print(item, "MP4 bytes", video.stat().st_size, "GIF bytes", path.stat().st_size, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--media", action="store_true")
    args = parser.parse_args()
    make_stills()
    if args.media:
        make_media()
