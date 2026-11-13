import { Equipment } from '../character/equipment';
import type { Slot } from '../character/types';
import { body, SKIN_TONES } from './body';
import { OUTFITS } from './outfits';
import { getItem } from './registry';

/**
 * 角色预设：一个角色 = 套装 + 发型 + 五官 + 肤色 + 武器，以及各自的换色方案。
 * 网页预览和导出脚本都读这份清单；hero1–3 对应 iPad 游戏里的三位旅人
 * （导出为 Hero1Directions.png …，可直接替换 Assets.xcassets 里的同名资源）。
 */
export interface CharacterPreset {
  id: string;
  name: string;
  /** OUTFITS 里的套装 id */
  outfit: string;
  hair: string;
  face: string;
  skin?: keyof typeof SKIN_TONES;
  /** 主手武器 id，不填 = 空手 */
  weapon?: string;
  /** 各槽位的换色方案 id，会覆盖套装里写的 */
  variants?: Partial<Record<Slot, string>>;
}

export const CHARACTERS: CharacterPreset[] = [
  {
    id: 'hero1', name: '旅人',
    outfit: 'traveler', hair: 'hair_messy', face: 'face_round', weapon: 'weapon_short_sword',
  },
  {
    id: 'hero2', name: '红斗篷',
    outfit: 'red_cloak', hair: 'hair_neat', face: 'face_smile', skin: 'light', weapon: 'weapon_staff',
    variants: { hair: 'black' },
  },
  {
    id: 'hero3', name: '林间行者',
    outfit: 'traveler', hair: 'hair_messy', face: 'face_round', skin: 'tan',
    variants: { top: 'green', scarf: 'cream', hair: 'blonde', face: 'amber' },
  },
];

/** 按预设穿戴好一套装备。找不到的 id 直接报错，避免悄悄画出缺件的角色。 */
export function buildEquipment(p: CharacterPreset): Equipment {
  const need = (id: string) => {
    const it = getItem(id);
    if (!it) throw new Error(`角色 ${p.id}：找不到装备 ${id}`);
    return it;
  };
  const outfit = OUTFITS.find((o) => o.id === p.outfit);
  if (!outfit) throw new Error(`角色 ${p.id}：找不到套装 ${p.outfit}`);

  const eq = new Equipment(body);
  if (p.skin) eq.setBodyPalette(SKIN_TONES[p.skin]);
  eq.equip('hair', need(p.hair));
  eq.equip('face', need(p.face));
  for (const [slot, id] of Object.entries(outfit.slots) as [Slot, string | null][]) {
    if (id) eq.equip(slot, need(id));
  }
  if (p.weapon) eq.equip('weapon_main', need(p.weapon));
  const variants = { ...outfit.variants, ...p.variants };
  for (const [slot, v] of Object.entries(variants) as [Slot, string][]) eq.setVariant(slot, v);
  return eq;
}
