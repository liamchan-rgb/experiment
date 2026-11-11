import type { ItemDef, Slot } from '../character/types';

/**
 * 装备注册表。
 * 自动收集 items/<分类>/*.ts 里导出的所有 ItemDef ——
 * 新增一件装备只需要在对应目录里加一个数据文件，不用改任何核心代码。
 */
const modules = import.meta.glob('./*/*.ts', { eager: true }) as Record<string, Record<string, unknown>>;

function isItem(v: unknown): v is ItemDef {
  return !!v && typeof v === 'object' && 'id' in v && 'slot' in v && Array.isArray((v as ItemDef).parts);
}

const byId = new Map<string, ItemDef>();
for (const path of Object.keys(modules).sort()) {
  for (const exported of Object.values(modules[path])) {
    if (!isItem(exported)) continue;
    if (byId.has(exported.id)) console.warn(`[items] 重复的装备 id: ${exported.id} (${path})`);
    byId.set(exported.id, exported);
  }
}

export function getItem(id: string): ItemDef | undefined {
  return byId.get(id);
}

/** 某槽位可用的装备。副手槽可以拿任何主手武器。 */
export function itemsFor(slot: Slot): ItemDef[] {
  const accept: Slot[] = slot === 'weapon_off' ? ['weapon_off', 'weapon_main'] : [slot];
  return [...byId.values()].filter((it) => accept.includes(it.slot));
}
