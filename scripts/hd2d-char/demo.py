"""The walking demo: two baked figures walk an octagon (all eight facings) over a procedural meadow with HD-2D style finishing
(soft focus towards the top and bottom, bloom, light shafts, vignette). Everything is generated; nothing is drawn by hand."""
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from bake import OUT, WALK
from render import SIZE, FOOT, PX
from rig import STRIDE

W, H, S = 1280, 720, 2                   # frame size; sprites are shown at 2x
FPS, STEP = 25, 0.08                     # 0.08 s per walk frame
SPEED = 2 * STRIDE / (WALK * STEP)       # units per second, so the planted foot does not slide
GY = 0.57                                # how much a step "into" the screen moves up it
SIDE = 1.0
CX, CY = 640, 420

def to_screen(x, y): return CX + x * PX * S, CY - y * PX * S * GY

rng = np.random.default_rng(7)
def noise(w, h, cell):
    g = rng.random((h // cell + 2, w // cell + 2))
    ys, xs = np.mgrid[0:h, 0:w] / cell
    y0, x0 = ys.astype(int), xs.astype(int); fy, fx = ys - y0, xs - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    return (g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx) * (1 - fy) + (g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx) * fy

def ground():
    """The meadow at half resolution (each pixel doubled later, to match the sprites' pixels)."""
    w, h = W // 2, H // 2
    n = 0.55 * noise(w, h, 48) + 0.3 * noise(w, h, 14) + 0.15 * rng.random((h, w))
    grass = np.array([[52, 104, 58], [70, 128, 62], [96, 150, 66], [132, 172, 76]], np.float32)
    img = grass[np.digitize(n, [0.38, 0.52, 0.66])]
    # the path the figures walk: an octagon of trodden earth
    ys, xs = np.mgrid[0:h, 0:w]
    wx, wy = (xs * 2 - CX) / (PX * S), (CY - ys * 2) / (PX * S * GY)
    ang = np.arctan2(wy, wx); r = np.hypot(wx, wy)
    apothem = SIDE / (2 * np.tan(np.pi / 8)); edge = apothem / np.cos(((ang + np.pi / 8) % (np.pi / 4)) - np.pi / 8)
    d = np.abs(r - edge) + 0.05 * (noise(w, h, 9) - 0.5)
    earth = np.array([[150, 112, 70], [176, 136, 86], [198, 160, 104]], np.float32)[np.digitize(noise(w, h, 6), [0.4, 0.62])]
    m = np.clip((0.16 - d) / 0.05, 0, 1)[..., None]; img = img * (1 - m) + earth * m
    im = Image.fromarray(img.astype(np.uint8)); dr = ImageDraw.Draw(im)
    for _ in range(420):                                   # tufts, flowers, pebbles
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h)); k = rng.random()
        if m[y, x, 0] > 0.3:
            if k < 0.25: dr.ellipse((x - 2, y - 1, x + 2, y + 1), fill=(128, 118, 110)); dr.point((x - 1, y - 1), fill=(170, 162, 150))
            continue
        if k < 0.6: dr.line((x, y, x - 1, y - 3), fill=(40, 88, 50)); dr.line((x + 1, y, x + 2, y - 4), fill=(150, 190, 84)); dr.line((x + 3, y, x + 4, y - 2), fill=(60, 110, 56))
        elif k < 0.85:
            c = [(250, 244, 230), (250, 214, 90), (236, 130, 150), (150, 170, 250)][int(rng.integers(0, 4))]
            dr.point([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], fill=c); dr.point((x, y), fill=(250, 200, 60)); dr.line((x, y + 2, x, y + 4), fill=(44, 96, 50))
        else: dr.ellipse((x - 3, y - 2, x + 3, y + 1), fill=(112, 112, 116)); dr.line((x - 2, y - 2, x + 1, y - 2), fill=(168, 168, 170))
    return im.resize((W, H), Image.NEAREST)

def octagon(dist):
    """Position, facing index (0 up, counting anticlockwise in 45 degree steps) on the octagon after walking `dist`."""
    dist %= 8 * SIDE; k = int(dist // SIDE); f = dist - k * SIDE
    R = SIDE / (2 * np.sin(np.pi / 8))
    a0, a1 = -np.pi / 2 - np.pi / 8 + k * np.pi / 4, -np.pi / 2 - np.pi / 8 + (k + 1) * np.pi / 4
    p0, p1 = np.array([np.cos(a0), np.sin(a0)]) * R, np.array([np.cos(a1), np.sin(a1)]) * R
    p = p0 + (p1 - p0) * f / SIDE; dirn = (p1 - p0) / SIDE
    yaw = np.arctan2(-dirn[0], dirn[1]); facing = int(round(yaw / (np.pi / 4))) % 8
    return p, facing

def main():
    base = ground()
    atlases = {n: Image.open(OUT / f'{n}-atlas.png') for n in ('knight', 'mage')}
    def cell(name, facing, i):
        im = atlases[name].crop((i * SIZE[0], facing * SIZE[1], (i + 1) * SIZE[0], (facing + 1) * SIZE[1]))
        return im.resize((SIZE[0] * S, SIZE[1] * S), Image.NEAREST)
    # finishing layers
    ys = np.linspace(0, 1, H)[:, None]; xs = np.linspace(0, 1, W)[None, :]
    focus = np.clip(np.abs(ys - 0.58) / 0.42, 0, 1) ** 1.6 * np.ones((1, W))
    focus_mask = Image.fromarray((focus * 255).astype(np.uint8))
    vig = 1 - 0.42 * np.clip(np.hypot((xs - 0.5) * 1.15, (ys - 0.52) * 1.25) * 1.5 - 0.35, 0, 1) ** 1.5
    loop = 8 * SIDE / SPEED; frames = int(round(loop * FPS)); out = []
    tmp = OUT / 'frames'; tmp.mkdir(exist_ok=True)
    for fi in range(frames):
        t = fi / FPS
        scene = base.copy().convert('RGBA')
        actors = []
        for name, lead in (('knight', 0.0), ('mage', 4 * SIDE)):
            p, facing = octagon(t * SPEED + lead)
            actors.append((p[1], name, p, facing))
        shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sprites = []
        for _, name, p, facing in sorted(actors, key=lambda a: -a[0]):
            im = cell(name, facing, int(t / STEP) % WALK)
            sx, sy = to_screen(*p)
            # the cast shadow: the sprite's own silhouette laid on the ground, away from the light
            a = im.split()[3]; sh = Image.new('RGBA', im.size, (18, 30, 40, 150)); sh.putalpha(a.point(lambda v: 150 if v else 0))
            hh = int(im.height * 0.42); sh = sh.resize((im.width, hh), Image.BILINEAR)
            sh = sh.transform((im.width + 120, hh), Image.AFFINE, (1, 0.9, -120 * 0 - 0.9 * hh * (FOOT[1] / SIZE[1]) + 0, 0, 1, 0), Image.BILINEAR)
            shadow.alpha_composite(sh, (int(sx - FOOT[0] * S), int(sy - hh * FOOT[1] / SIZE[1])))
            sprites.append((im, (int(sx - FOOT[0] * S), int(sy - FOOT[1] * S))))
        scene.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(2.5)))
        # soft focus on the ground only, away from the band the figures stand in
        ground_rgb = scene.convert('RGB')
        scene = Image.composite(ground_rgb.filter(ImageFilter.GaussianBlur(5)), ground_rgb, focus_mask).convert('RGBA')
        for im, at in sprites: scene.alpha_composite(im, at)
        arr = np.asarray(scene.convert('RGB')).astype(np.float32)
        # light shafts drifting across, then bloom, grade and vignette
        shafts = np.clip(np.sin((xs * 1.6 + ys * 0.9) * 9 + t * 0.6) * 0.5 + np.sin((xs * 1.6 + ys * 0.9) * 23 - t * 0.4) * 0.3, 0, 1) * (1 - ys) ** 0.7
        arr += shafts[..., None] * np.array([70, 58, 26], np.float32)
        bright = Image.fromarray(np.clip((arr - 150) * 1.6, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
        arr = arr + np.asarray(bright).astype(np.float32) * 0.55
        arr = (arr * np.array([1.04, 1.0, 0.92], np.float32) + np.array([6, 2, -4], np.float32)) * vig[..., None]
        frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); frame.save(tmp / f'{fi:04d}.png'); out.append(frame)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(tmp / '%04d.png'), '-pix_fmt', 'yuv420p', '-crf', '17', str(OUT / 'walk-demo.mp4')], check=True)
    gif = [f.resize((640, 360), Image.LANCZOS).quantize(colors=160, method=Image.MEDIANCUT, dither=Image.NONE) for f in out[::2]]
    gif[0].save(OUT / 'walk-demo.gif', save_all=True, append_images=gif[1:], duration=int(2000 / FPS), loop=0, optimize=True)
    out[int(0.31 * frames)].save(OUT / 'walk-demo-still.png')
    for f in tmp.iterdir(): f.unlink()
    tmp.rmdir(); print('frames', frames)

if __name__ == '__main__': main()
