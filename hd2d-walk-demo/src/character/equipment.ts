import type { Palette } from '../pixel/palette';
import type { LoadoutEntry } from './paperdoll';
import { SLOTS, type ItemDef, type Slot } from './types';

interface Equipped {
  item: ItemDef;
  /** 换色覆盖：键 → 调色板 */
  overrides: Record<string, Palette>;
  variantId?: string;
}

/**
 * 装备系统：只管「哪个槽位穿着什么、用什么颜色」，不关心怎么画。
 */
export class Equipment {
  private slots = new Map<Slot, Equipped>();

  constructor(private body: ItemDef) {}

  equip(slot: Slot, item: ItemDef): void {
    this.slots.set(slot, { item, overrides: {} });
  }

  unequip(slot: Slot): void {
    this.slots.delete(slot);
  }

  get(slot: Slot): ItemDef | undefined {
    return this.slots.get(slot)?.item;
  }

  variantOf(slot: Slot): string | undefined {
    return this.slots.get(slot)?.variantId;
  }

  /** 替换某槽位装备的一个调色板（默认替换 'main'）。 */
  setPalette(slot: Slot, palette: Palette, key = 'main'): void {
    const e = this.slots.get(slot);
    if (e) {
      e.overrides[key] = palette;
      e.variantId = undefined;
    }
  }

  /** 应用装备自带的换色方案。 */
  setVariant(slot: Slot, variantId: string): void {
    const e = this.slots.get(slot);
    const v = e?.item.variants?.find((x) => x.id === variantId);
    if (e && v) {
      e.overrides = { ...v.palettes };
      e.variantId = v.id;
    }
  }

  /** 解析成合成用的列表（身体在最前，处理 hides）。 */
  resolve(): LoadoutEntry[] {
    const hidden = new Set<Slot>();
    for (const e of this.slots.values()) e.item.hides?.forEach((s) => hidden.add(s));
    const out: LoadoutEntry[] = [{ slot: 'body', item: this.body, palettes: this.body.palettes }];
    for (const slot of SLOTS) {
      const e = this.slots.get(slot);
      if (!e || hidden.has(slot)) continue;
      out.push({ slot, item: e.item, palettes: { ...e.item.palettes, ...e.overrides } });
    }
    return out;
  }
}
