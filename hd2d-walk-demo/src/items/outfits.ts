import type { OutfitDef } from '../character/types';

/** 套装预设：只是一组「槽位 → 装备 id」，UI 的套装按钮由这里生成。 */
export const OUTFITS: OutfitDef[] = [
  {
    id: 'traveler',
    name: '蓝色旅人装',
    slots: {
      top: 'top_traveler',
      bottom: 'bottom_trousers',
      shoes: 'shoes_boots',
      scarf: 'scarf_navy',
      bag: 'bag_satchel',
    },
    variants: { top: 'blue', bottom: 'dark', shoes: 'brown', scarf: 'navy' },
  },
  {
    id: 'red_cloak',
    name: '红色斗篷装',
    slots: {
      top: 'top_red_cloak',
      bottom: 'bottom_trousers',
      shoes: 'shoes_boots',
      scarf: null,
      bag: 'bag_satchel',
    },
    variants: { top: 'red', bottom: 'brown', shoes: 'black' },
  },
];

export const DEFAULT_OUTFIT = 'traveler';
