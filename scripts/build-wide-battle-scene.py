"""Builds the wide battle scene (2x the width of the camp clearing) from art already in the repo: the four camp-clearing layers in the
middle, and to the left and right the same forest and meadow continued and dressed with the map's scenery props (oaks, pines, rocks,
shrubs, fence, flowers, tent). Output: four 2618x1201 layers; the original 1309 px scene sits untouched at x = 654 ... 1963.
Run: python3 scripts/build-wide-battle-scene.py"""
import glob, random
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'Sources/Resources/Assets.xcassets'
OUT = ROOT / 'Art/Scenes/MeadowBattle/camp-clearing/wide-v1'
W, H, X0 = 1309, 1201, 654
WW = W * 2

def layer(name): return Image.open(glob.glob(str(ASSETS / f'MeadowCamp{name}.imageset/*.png'))[0]).convert('RGBA')
def prop(name): return Image.open(glob.glob(str(ASSETS / f'{name}.imageset/*.png'))[0]).convert('RGBA')

far, ground, mid, fore = layer('FarForest'), layer('Ground'), layer('Midground'), layer('Foreground')
flip = lambda im: im.transpose(Image.FLIP_LEFT_RIGHT)

def continued(im):
    """The layer in the middle, flipped copies joined on each side (edges meet without a seam)."""
    out = Image.new('RGBA', (WW, H), (0, 0, 0, 0))
    f = flip(im)
    out.paste(f.crop((W - X0, 0, W, H)), (0, 0))
    out.paste(im, (X0, 0))
    out.paste(f.crop((0, 0, WW - X0 - W, H)), (X0 + W, 0))
    return out

wide_far, wide_ground = continued(far), continued(ground)

# Where the meadow's upper edge is, per column of the wide ground (props stand on it).
ga = wide_ground.split()[3].load()
def horizon(x):
    x = max(0, min(WW - 1, int(x)))
    for y in range(H):
        if ga[x, y] > 128: return y
    return H

def toned(im, haze=0.0, dark=1.0, sat=1.0):
    """A prop pushed back into the scene: less saturated, mixed with the forest's blue-green haze."""
    r, g, b, a = im.split()
    rgb = Image.merge('RGB', (r, g, b))
    rgb = ImageEnhance.Color(rgb).enhance(sat); rgb = ImageEnhance.Brightness(rgb).enhance(dark)
    if haze > 0: rgb = Image.blend(rgb, Image.new('RGB', rgb.size, (96, 130, 104)), haze)
    return Image.merge('RGBA', (*rgb.split(), a))

def place(canvas, im, x, base, scale, mirror=False, shadow=True, **tone):
    im = toned(im, **tone) if tone else im
    if mirror: im = flip(im)
    w, h = int(im.width * scale), int(im.height * scale)
    im = im.resize((w, h), Image.LANCZOS)
    if shadow:
        s = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); d = ImageDraw.Draw(s)
        d.ellipse((x - w * 0.42, base - h * 0.05, x + w * 0.42, base + h * 0.05), fill=(20, 30, 10, 105))
        canvas.alpha_composite(s.filter(ImageFilter.GaussianBlur(8)))
    canvas.alpha_composite(im, (int(x - w / 2), int(base - h * 0.97)))

P = {n: prop(n) for n in ['OakA', 'OakB', 'Pines', 'RockHigh', 'RockLow', 'RockSmall', 'Shrub', 'Fence', 'Flowers', 'CampTent', 'Banner']}

# --- far forest: big hazy trees stand over the joins and fill the sides, so the continued forest is not a mirror image
for name, x, s, m, hz in [('OakA', 640, 1.55, False, 0.30), ('Pines', 470, 1.35, True, 0.36), ('OakB', 250, 1.5, True, 0.33), ('Pines', 60, 1.5, False, 0.4),
                          ('OakB', 1975, 1.6, False, 0.30), ('Pines', 2150, 1.4, False, 0.36), ('OakA', 2330, 1.55, True, 0.33), ('Pines', 2540, 1.5, True, 0.4)]:
    place(wide_far, P[name], x, horizon(x) + 40, s, mirror=m, shadow=False, haze=hz, dark=0.9, sat=0.85)

# --- ground: the path that would mirror into a V is covered, and the sides get their own flowers
for name, x, dy, s, m in [('Flowers', 300, 330, 0.2, False), ('Flowers', 120, 520, 0.24, True), ('RockSmall', 420, 250, 0.3, False),
                          ('Flowers', 2230, 300, 0.2, True), ('Flowers', 2480, 480, 0.24, False), ('RockSmall', 2120, 210, 0.28, True)]:
    place(wide_ground, P[name], x, horizon(x) + dy, s, mirror=m)

# --- midground: left of the scene the camp goes on (tent, fence, banner, trees); right of it the rocks and the wood
wide_mid = Image.new('RGBA', (WW, H), (0, 0, 0, 0))
for name, x, dy, s, m in [('Pines', 90, 40, 1.0, False), ('OakA', 230, 50, 0.95, True), ('CampTent', 430, 78, 0.46, False), 
                          ('Fence', 330, 120, 0.5, False), ('RockLow', 150, 140, 0.5, False),
                          ('RockHigh', 2090, 70, 0.72, False), ('OakB', 2260, 45, 1.0, False), ('RockLow', 2390, 110, 0.6, True), ('Pines', 2530, 50, 1.05, True),
                          ('RockSmall', 2300, 170, 0.4, False)]:
    place(wide_mid, P[name], x, horizon(x) + dy, s, mirror=m)
wide_mid.alpha_composite(mid, (X0, 0))
# Over the scene's own right edge (its rocks were cut there): an oak stands in front of the cut.
place(wide_mid, P['OakA'], 1985, horizon(1985) + 95, 0.9, mirror=True)
place(wide_mid, P['RockSmall'], 1930, horizon(1930) + 150, 0.42)
# And over its left edge (a bush was cut there): pines and a low rock.
place(wide_mid, P['Pines'], 632, horizon(632) + 75, 0.62)
place(wide_mid, P['RockLow'], 690, horizon(690) + 120, 0.32, mirror=True)

# --- foreground: the low bushes run the whole width; the framing vine and tree move out to the far edges
CUT = 700
wide_fore = Image.new('RGBA', (WW, H), (0, 0, 0, 0))
# Beside the scene the strip continues with its other end (not a mirror image next to itself), the flipped copy only further out;
# every piece fades in over its ends and overlaps its neighbour, so there is no cut.
strip, G, F = fore.crop((0, CUT, W, H)), 420, 170
def feathered(im, left=True, right=True):
    im = im.copy(); w, h = im.size
    ramp = Image.new('L', (w, 1), 255); px = ramp.load()
    for x in range(F):
        t = int(255 * (x / F) ** 1.5)
        if left: px[x, 0] = min(px[x, 0], t)
        if right: px[w - 1 - x, 0] = min(px[w - 1 - x, 0], t)
    a = Image.composite(im.split()[3], Image.new('L', (w, h), 0), ramp.resize((w, h)))
    im.putalpha(a); return im
fs = flip(strip)
wide_fore.alpha_composite(feathered(fs.crop((W - (X0 - G) - F, 0, W, H - CUT)), left=False), (0, CUT))
wide_fore.alpha_composite(feathered(fs.crop((0, 0, WW - (X0 + W + G) + F, H - CUT)), right=False), (X0 + W + G - F, CUT))
wide_fore.alpha_composite(feathered(strip.crop((W - G - F, 0, W, H - CUT))), (X0 - G - F // 2, CUT))
wide_fore.alpha_composite(feathered(strip.crop((0, 0, G + F, H - CUT))), (X0 + W - F // 2, CUT))
wide_fore.alpha_composite(feathered(strip), (X0, CUT))
wide_fore.alpha_composite(fore.crop((0, 0, 420, CUT)), (0, 0))
wide_fore.alpha_composite(fore.crop((820, 0, W, CUT)), (WW - (W - 820), 0))

OUT.mkdir(parents=True, exist_ok=True)
names = ['01-far-forest', '02-ground', '03-midground', '04-foreground']
for name, im, asset in zip(names, [wide_far, wide_ground, wide_mid, wide_fore], ['FarForest', 'Ground', 'Midground', 'Foreground']):
    if name == '01-far-forest': im = im.convert('RGB')
    im.save(OUT / f'{name}.png', optimize=True)
    folder = ASSETS / f'MeadowCampWide{asset}.imageset'; folder.mkdir(exist_ok=True)
    im.save(folder / f'{name}.png', optimize=True)
    (folder / 'Contents.json').write_text('{\n  "images" : [\n    {\n      "filename" : "%s.png",\n      "idiom" : "universal"\n    }\n  ],\n  "info" : {\n    "author" : "xcode",\n    "version" : 1\n  }\n}\n' % name)
review = wide_far.convert('RGBA'); [review.alpha_composite(l) for l in (wide_ground, wide_mid, wide_fore)]
review.convert('RGB').resize((1745, 800), Image.LANCZOS).save(OUT / 'review.jpg', quality=88)
print('ok')
