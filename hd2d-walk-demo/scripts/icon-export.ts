/**
 * 物品图标导出给游戏：每个图标一张静态图 + 稀有以上的发光动画帧（原始 RGBA，tools/icon_export.py 转成素材目录的 PNG）。
 *   npx vite-node scripts/icon-export.ts <输出目录>
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { ICONS } from '../src/icons/icons';
import { FRAMES, FPS, ICON, drawIcon, iconFrame } from '../src/icons/iconKit';

const out = process.argv[2] ?? 'icon-export';
mkdirSync(out, { recursive: true });
const list: { id: string; name: string; rarity: string; animated: boolean }[] = [];
for (const def of ICONS) {
  const base = drawIcon(def);
  const still = new Uint8ClampedArray(ICON * ICON * 4);
  base.toRGBA(still);
  writeFileSync(`${out}/${def.id}.rgba`, still);
  const animated = def.rarity !== 'common';
  if (animated) {
    const strip = new Uint8Array(ICON * ICON * 4 * FRAMES);
    for (let f = 0; f < FRAMES; f++) strip.set(iconFrame(def, base, f / FRAMES), f * ICON * ICON * 4);
    writeFileSync(`${out}/${def.id}-fx.rgba`, strip);
  }
  list.push({ id: def.id, name: def.name, rarity: def.rarity, animated });
}
writeFileSync(`${out}/icons.json`, JSON.stringify({ size: ICON, frames: FRAMES, fps: FPS, icons: list }, null, 1));
console.log(list.map((i) => `${i.id}(${i.rarity})`).join(' '));
