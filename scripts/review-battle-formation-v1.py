"""Offline layout study for bigger battles: up to seven heroes and three monsters, and PvP with the right team mirrored.
Mirrors MeadowBattleFormation (Sources/Game): the world grows by a factor Z (1000Z x 600Z, plates scaled by Z), units keep their size in
world units, so the camera shows more of the field. Real plates, real hero idle frames, the forest warden as the stand-in monster."""
import sys, json
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
src = (ROOT / 'scripts/review-battle-effects-demo.py').read_text().replace("'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',", "'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',")
env = {'__file__': str(ROOT / 'scripts/review-battle-effects-demo.py')}
exec(compile(src.split('\nplate = Image.new')[0], 'demo', 'exec'), env)
render, asset = env['render'], env['asset']
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'Art/Review/Battle/formation-v1'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'scripts/battle-vfx'))
import formation as F

layers = [asset(n) for n in ('MeadowCampFarForest', 'MeadowCampGround', 'MeadowCampMidground')]
fg = asset('MeadowCampForeground'); warden = asset('MeadowBattleForestWarden')

def compose(name, players, foes, pvp, px=1400, aspect=1.85):
    lay = F.layout(players, foes, pvp)
    Z = lay['zoom']; W, H = 1000 * Z, 600 * Z; k = px / W
    vis_h = W / aspect; y0 = H / 2 - vis_h / 2
    img = Image.new('RGBA', (px, int(vis_h * k)), (20, 30, 20, 255))
    def place(im, x, y, w, h):
        img.alpha_composite(im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.Resampling.LANCZOS), (int(x * k), int((y - y0) * k)))
    for l, blur in zip(layers, (3, 1.5, 1.5)):
        place(l.filter(ImageFilter.GaussianBlur(blur)), 0, -159 * Z, 1000 * Z, 1000 * Z * 1201 / 1309)
    units = sorted(lay['feet'].items(), key=lambda kv: kv[1][1])
    for uid, (fx, fy) in units:
        mirrored = uid in lay['mirrored']
        if uid.startswith('p'):
            s = .83; hero = render('idle', (hash(uid) % 100) / 100)
            if mirrored: hero = hero.transpose(Image.FLIP_LEFT_RIGHT); x = fx - (256 - 123) * s
            else: x = fx - 123 * s
            place(hero, x, fy - 214 * s, 256 * s, 256 * s)
        else:
            s = .88; place(warden, fx - 178.5 * s, fy - 240 * s, 384 * s, 256 * s)
    place(fg, 0, -159 * Z, 1000 * Z, 1000 * Z * 1201 / 1309)
    d = ImageDraw.Draw(img)
    for uid, (fx, fy) in units:
        d.text((int(fx * k) - 8, int((fy - y0) * k) + 4), uid, fill=(255, 240, 180, 255))
    img.convert('RGB').save(OUT / f'{name}.png'); print(name, 'zoom', Z)

compose('2v2', ['p1', 'p2'], ['m1', 'm2'], False)
compose('4v3', ['p1', 'p2', 'p3', 'p4'], ['m1', 'm2', 'm3'], False)
compose('7v3', ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7'], ['m1', 'm2', 'm3'], False)
compose('pvp-4v3', ['p1', 'p2', 'p3', 'p4'], ['p5', 'p6', 'p7'], True)
compose('pvp-7v7', ['p1','p2','p3','p4','p5','p6','p7'], ['q1','q2','q3','q4','q5','q6','q7'], True)
