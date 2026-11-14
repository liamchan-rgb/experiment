"""
把 scripts/icon-export.ts 的输出写进游戏的素材目录（Assets.xcassets）：
  PixelIcon<Id>.imageset     静态图标，32 → 512（16 倍最近邻，和原来的图标一样大）
  PixelIconFX<Id>.imageset   稀有以上：24 帧发光动画横排，每帧 32 → 192
  另外把已有的旧图标（MeadowParty… / Meadow…Icon，按物品 id 对应）换成新图，直接按名字取图的界面也统一画风。
用法：python3 tools/icon_export.py <导出目录> <Assets.xcassets>
"""
import json, os, sys
from PIL import Image

src, cat = sys.argv[1], sys.argv[2]
meta = json.load(open(os.path.join(src, 'icons.json')))
N, F = meta['size'], meta['frames']
OLD = {
    'trainingSword': 'MeadowPartyTrainingSword', 'huntingBow': 'MeadowPartyHuntingBow', 'greatSword': 'MeadowPartyGreatSword',
    'legendaryStaff': 'MeadowPartyLegendaryStaff', 'leatherArmor': 'MeadowLeatherArmorIcon', 'runeArmor': 'MeadowRuneArmorIcon',
    'powerBadge': 'MeadowPowerBadge', 'actionRing': 'MeadowActionRing', 'smallPotion': 'MeadowPartySmallPotion',
    'largePotion': 'MeadowPartyLargePotion', 'shieldPotion': 'MeadowPartyShieldPotion', 'revivalStone': 'MeadowPartyRevivalStone',
}


def imageset(name, img):
    d = os.path.join(cat, name + '.imageset')
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'):
            os.remove(os.path.join(d, f))
    img.save(os.path.join(d, name + '.png'), optimize=True)
    json.dump({'images': [{'idiom': 'universal', 'filename': name + '.png'}], 'info': {'author': 'xcode', 'version': 1}},
              open(os.path.join(d, 'Contents.json'), 'w'), indent=2)


for it in meta['icons']:
    i = it['id']
    cap = i[0].upper() + i[1:]
    still = Image.frombytes('RGBA', (N, N), open(os.path.join(src, i + '.rgba'), 'rb').read()).resize((N * 16, N * 16), Image.NEAREST)
    imageset('PixelIcon' + cap, still)
    if i in OLD and os.path.isdir(os.path.join(cat, OLD[i] + '.imageset')):
        imageset(OLD[i], still)
    if it['animated']:
        raw = open(os.path.join(src, i + '-fx.rgba'), 'rb').read()
        strip = Image.new('RGBA', (N * 6 * F, N * 6))
        for k in range(F):
            fr = Image.frombytes('RGBA', (N, N), raw[k * N * N * 4:(k + 1) * N * N * 4]).resize((N * 6, N * 6), Image.NEAREST)
            strip.paste(fr, (k * N * 6, 0))
        imageset('PixelIconFX' + cap, strip)
    print(i, it['rarity'])
