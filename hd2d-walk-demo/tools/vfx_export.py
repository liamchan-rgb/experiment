"""
把 scripts/vfx-export.ts 的输出打包进游戏素材目录（Assets.xcassets）：
  PixelFX_<片段>.imageset   每个片段一张网格图：先 back 层的全部帧，再 front 层的全部帧，从左到右、从上到下排，每行最多 4096 像素宽
  PixelFXRecipes.dataset    recipes.json（片段尺寸、锚点、网格列数 + 每个游戏特效 id 的配方）
用法：python3 tools/vfx_export.py <导出目录> <Assets.xcassets>
"""
import json, math, os, shutil, sys
from PIL import Image

src, cat = sys.argv[1], sys.argv[2]
data = json.load(open(os.path.join(src, 'recipes.json')))
for old in os.listdir(cat):
    if old.startswith('PixelFX_') and old.endswith('.imageset'):
        shutil.rmtree(os.path.join(cat, old))
total = 0
for c in data['clips']:
    w, h, n = c['w'], c['h'], c['n']
    layers = (1 if c['back'] else 0) + (1 if c['front'] else 0)
    count = n * layers
    raw = open(os.path.join(src, 'clips', c['id'] + '.rgba'), 'rb').read()
    cols = max(1, min(count, 4096 // w))
    rows = math.ceil(count / cols)
    sheet = Image.new('RGBA', (cols * w, rows * h))
    for k in range(count):
        fr = Image.frombytes('RGBA', (w, h), raw[k * w * h * 4:(k + 1) * w * h * 4])
        sheet.paste(fr, ((k % cols) * w, (k // cols) * h))
    c['cols'] = cols
    name = 'PixelFX_' + c['id']
    d = os.path.join(cat, name + '.imageset')
    os.makedirs(d, exist_ok=True)
    sheet.save(os.path.join(d, name + '.png'), optimize=True)
    total += os.path.getsize(os.path.join(d, name + '.png'))
    json.dump({'images': [{'idiom': 'universal', 'filename': name + '.png'}], 'info': {'author': 'xcode', 'version': 1}}, open(os.path.join(d, 'Contents.json'), 'w'), indent=2)
d = os.path.join(cat, 'PixelFXRecipes.dataset')
os.makedirs(d, exist_ok=True)
json.dump(data, open(os.path.join(d, 'recipes.json'), 'w'), separators=(',', ':'))
json.dump({'data': [{'idiom': 'universal', 'filename': 'recipes.json'}], 'info': {'author': 'xcode', 'version': 1}}, open(os.path.join(d, 'Contents.json'), 'w'), indent=2)
print(len(data['clips']), 'clips', round(total / 1e6, 1), 'MB of PNG')
