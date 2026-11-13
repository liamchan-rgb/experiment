import type { ItemDef, Slot } from '../character/types';
import { makeHair, type HairColorsData, type HairData } from './kits/hairKit';
import { makeFace, type FaceData } from './kits/faceKit';

/**
 * 装备注册表，自动收集两类来源，新增装备不用改任何核心代码：
 *   - src/items/<分类>/*.ts 里导出的 ItemDef（衣服、鞋、围巾、挎包、武器……用代码画）
 *   - Sources/Resources/CharacterParts/hair|face/*.json（发型、五官是纯数据，和 iPad 端共用）
 */
const modules = import.meta.glob('./*/*.ts', { eager: true }) as Record<string, Record<string, unknown>>;
const hairFiles = import.meta.glob('../../../Sources/Resources/CharacterParts/hair/*.json', {
  eager: true, import: 'default',
}) as Record<string, HairData>;
const colorFiles = import.meta.glob('../../../Sources/Resources/CharacterParts/hair-colors.json', {
  eager: true, import: 'default',
}) as Record<string, HairColorsData>;
const sharedHairColors = Object.values(colorFiles)[0]?.colors ?? [];
const faceFiles = import.meta.glob('../../../Sources/Resources/CharacterParts/face/*.json', {
  eager: true, import: 'default',
}) as Record<string, FaceData>;

function isItem(v: unknown): v is ItemDef {
  return !!v && typeof v === 'object' && 'id' in v && 'slot' in v && Array.isArray((v as ItemDef).parts);
}

const byId = new Map<string, ItemDef>();
function add(item: ItemDef, from: string): void {
  if (byId.has(item.id)) console.warn(`[items] 重复的装备 id: ${item.id} (${from})`);
  byId.set(item.id, item);
}

for (const path of Object.keys(modules).sort()) {
  if (path.startsWith('./kits/')) continue;
  for (const exported of Object.values(modules[path])) if (isItem(exported)) add(exported, path);
}
for (const path of Object.keys(hairFiles).sort()) add(makeHair(hairFiles[path], sharedHairColors), path);
for (const path of Object.keys(faceFiles).sort()) add(makeFace(faceFiles[path]), path);

export function getItem(id: string): ItemDef | undefined {
  return byId.get(id);
}

/** 某槽位可用的装备。副手槽可以拿任何主手武器。 */
export function itemsFor(slot: Slot): ItemDef[] {
  const accept: Slot[] = slot === 'weapon_off' ? ['weapon_off', 'weapon_main'] : [slot];
  return [...byId.values()].filter((it) => accept.includes(it.slot));
}
