/**
 * 物品图标预览：
 *   <输出前缀>.png        18 个图标的静态总览（放大 6 倍，深色背包底）
 *   <输出前缀>-frames.rgba 动画帧（给 GIF 用）：FRAMES 帧，每帧 6 列 × 3 行图标
 *   npm run icon-preview -- <输出前缀>
 */
import { writeFileSync } from 'node:fs';
import { ICONS } from '../src/icons/icons';
import { FRAMES, ICON, drawIcon, iconFrame } from '../src/icons/iconKit';

const prefix = process.argv[2] ?? 'icons';
const cols = 6, rows = Math.ceil(ICONS.length / cols);
const bases = ICONS.map(drawIcon);
const W = cols * ICON, H = rows * ICON;
const all = new Uint8Array(W * H * 4 * FRAMES);
for (let f = 0; f < FRAMES; f++) {
  ICONS.forEach((def, i) => {
    const px = iconFrame(def, bases[i], f / FRAMES);
    const ox = (i % cols) * ICON, oy = Math.floor(i / cols) * ICON;
    for (let y = 0; y < ICON; y++) all.set(px.subarray(y * ICON * 4, (y + 1) * ICON * 4), f * W * H * 4 + ((oy + y) * W + ox) * 4);
  });
}
writeFileSync(prefix + '-frames.rgba', all);
console.log(JSON.stringify({ w: W, h: H, frames: FRAMES, cols, names: ICONS.map((d) => `${d.name}(${d.rarity})`) }));
