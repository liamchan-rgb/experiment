/**
 * 发型预览：每个发型一行 —— 5 个方向的待机帧 + 一帧行走，后面接几种发色的正面。
 *   npm run hair-preview -- <输出.png> [发型 id,…]
 */
import { writeFileSync } from 'node:fs';
import { PixelLayer } from '../src/pixel/PixelLayer';
import { composeFrame } from '../src/character/paperdoll';
import { DIRS5, SPR_H, SPR_W } from '../src/character/rig';
import { CHARACTERS, buildEquipment } from '../src/items/characters';
import { itemsFor } from '../src/items/registry';
import { Image } from './png';

const out = process.argv[2] ?? 'hair-preview.png';
const only = process.argv[3]?.split(',');
const hairs = itemsFor('hair').filter((h) => !only || only.includes(h.id));
const colorsShown = ['brown', 'black', 'blonde', 'silver', 'red', 'pink'];
const Z = 5, PAD = 4;
const cols = DIRS5.length + 1 + colorsShown.length;
const img = new Image(cols * (SPR_W * Z + PAD), hairs.length * (SPR_H * Z + PAD));
for (let i = 0; i < img.data.length; i += 4) img.data.set([95, 143, 80, 255], i);

function frame(hairId: string, variant: string | undefined, dir: (typeof DIRS5)[number], col: number): Image {
  const eq = buildEquipment({ ...CHARACTERS[0], hair: hairId, weapon: undefined });
  if (variant) eq.setVariant('hair', variant);
  const L = new PixelLayer(SPR_W, SPR_H);
  composeFrame(eq.resolve(), dir, col, L);
  const im = new Image(SPR_W, SPR_H);
  L.toRGBA(im.data);
  return im;
}

hairs.forEach((h, r) => {
  const cells: Image[] = [
    ...DIRS5.map((d) => frame(h.id, undefined, d, 0)),
    frame(h.id, undefined, 'SE', 4),
    ...colorsShown.map((c) => frame(h.id, c, 'S', 0)),
  ];
  cells.forEach((c, k) => img.blit(c, k * (SPR_W * Z + PAD), r * (SPR_H * Z + PAD), Z));
});
writeFileSync(out, img.png());
console.log(`${hairs.map((h) => h.id).join(', ')} → ${out}`);
