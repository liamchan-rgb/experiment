/**
 * 调试页：把每套预设烘焙出的整张 sprite sheet 放大显示。
 * 打开 /?scale=4&s=0.8&weapon=weapon_staff （scale = 放大倍数，s = 精灵倍率）
 */
import { Equipment } from './character/equipment';
import { bakeSheet } from './pixel/bake';
import { body } from './items/body';
import { getItem, itemsFor } from './items/registry';
import { OUTFITS } from './items/outfits';
import type { Slot } from './character/types';
import { setSpriteScale } from './character/rig';

const q = new URLSearchParams(location.search);
const scale = Number(q.get('scale') ?? 4);
if (q.get('s')) setSpriteScale(Number(q.get('s')));

for (const outfit of OUTFITS) {
  const eq = new Equipment(body);
  eq.equip('hair', itemsFor('hair')[0]);
  for (const [slot, id] of Object.entries(outfit.slots) as [Slot, string | null][]) {
    const item = id ? getItem(id) : undefined;
    if (item) eq.equip(slot, item);
  }
  for (const [slot, v] of Object.entries(outfit.variants ?? {}) as [Slot, string][]) eq.setVariant(slot, v);
  const weapon = getItem(q.get('weapon') ?? '');
  if (weapon) eq.equip('weapon_main', weapon);
  const off = getItem(q.get('off') ?? '');
  if (off) eq.equip('weapon_off', off);

  const { canvas } = bakeSheet(eq.resolve());
  // 放大显示
  const big = document.createElement('canvas');
  big.width = canvas.width * scale;
  big.height = canvas.height * scale;
  const g = big.getContext('2d')!;
  g.imageSmoothingEnabled = false;
  g.drawImage(canvas, 0, 0, big.width, big.height);
  document.body.append(outfit.name, big);
}
