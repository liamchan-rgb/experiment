"""Side-by-side: original hand-drawn P1 (git 527e3548) vs rule-drawn 32x48 and 48x72, same on-screen size."""
import io, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from PIL import Image, ImageDraw, ImageFont
import pix, clips

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Art/Review/P1/pixel-rule-v1'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 18)

def original():
    p = 'Sources/Resources/Assets.xcassets/Hero1Diagonals.imageset/Hero1Diagonals.png'
    a = Image.open(io.BytesIO(subprocess.check_output(['git', '-C', str(ROOT), 'show', f'527e3548:{p}']))).convert('RGBA')
    return [a.crop((c * 256, 0, c * 256 + 256, 256)).crop((56, 72, 200, 228)) for c in range(9)]   # row 0 = down-right

def rule(H, W, scale):
    cells = []
    for clip, n in [('idle', 0)] + [('walk', k) for k in range(1, 9)]:
        im = pix.draw(clips.pose(clip, n), 'down-right', H, W).image()
        big = im.resize((W * scale, H * scale), Image.NEAREST)
        cell = Image.new('RGBA', (144, 156)); cell.alpha_composite(big, ((144 - big.width) // 2, 156 - big.height - 4))
        cells.append(cell)
    return cells

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cols = [('现在游戏的原画（手绘，约70×140）', original()), ('规则画 32×48（×3 显示）', rule(48, 32, 3)), ('规则画 48×72（×2 显示）', rule(72, 48, 2))]
    Z = 2
    sheet = Image.new('RGBA', (3 * 144 * Z + 40, 9 * 156 * Z // 3 + 60), (74, 104, 62, 255))
    # still sheet: idle big + jog strip
    S = Image.new('RGB', (3 * (144 * Z + 20) + 20, 156 * Z + 50 + 3 * (156 + 30)), (40, 40, 40))
    d = ImageDraw.Draw(S)
    for i, (label, cells) in enumerate(cols):
        x = 20 + i * (144 * Z + 20)
        d.text((x, 8), label, font=FONT, fill=(255, 230, 150))
        bg = Image.new('RGBA', (144 * Z, 156 * Z), (74, 104, 62, 255))
        bg.alpha_composite(cells[0].resize((144 * Z, 156 * Z), Image.NEAREST))
        S.paste(bg.convert('RGB'), (x, 40))
    y = 156 * Z + 60
    for i, (label, cells) in enumerate(cols):
        d.text((20, y), label + ' · 小跑/行走 8 帧', font=FONT, fill=(255, 230, 150))
        for k, c in enumerate(cells[1:]):
            bg = Image.new('RGBA', (144, 156), (74, 104, 62, 255)); bg.alpha_composite(c)
            S.paste(bg.convert('RGB').resize((int(144 * .75), int(156 * .75)), Image.NEAREST) if False else bg.convert('RGB').crop((22, 0, 122, 156)), (20 + k * 104, y + 26))
        y += 156 + 34
    S.save(OUT / 'compare-still.png')
    for ms, tag in ((120, 'slow'), (40, 'game-speed')):
        frames = []
        for k in range(16):
            F = Image.new('RGB', (3 * (144 * Z + 20) + 20, 156 * Z + 50), (40, 40, 40))
            dd = ImageDraw.Draw(F)
            for i, (label, cells) in enumerate(cols):
                x = 20 + i * (144 * Z + 20)
                dd.text((x, 8), label, font=FONT, fill=(255, 230, 150))
                bg = Image.new('RGBA', (144 * Z, 156 * Z), (74, 104, 62, 255))
                bg.alpha_composite(cells[1 + k % 8].resize((144 * Z, 156 * Z), Image.NEAREST))
                F.paste(bg.convert('RGB'), (x, 40))
            frames.append(F)
        frames[0].save(OUT / f'compare-{tag}.gif', save_all=True, append_images=frames[1:], duration=ms, loop=0)

if __name__ == '__main__':
    main()
