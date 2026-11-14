/**
 * 战斗动作 / 装备预览：每行一套「护甲 + 武器」，先是右侧的普通待机做对比，再是战斗待机（正面、右前、右侧两帧），然后是这把武器的攻击动作
 * （右侧 4 帧 = 战斗场景里的朝向，右前 4 帧），最后是施法 / 鼓舞动作的右侧 4 帧。
 *   npm run action-preview -- <输出.png>
 */
import { writeFileSync } from 'node:fs';
import { PixelLayer } from '../src/pixel/PixelLayer';
import { composeFrame } from '../src/character/paperdoll';
import { ACTION_FRAMES, READY_FRAMES, SPR_H, SPR_W, type ActionId } from '../src/character/rig';
import type { Dir5 } from '../src/character/types';
import { CHARACTERS, buildEquipment, type CharacterPreset } from '../src/items/characters';
import { getItem } from '../src/items/registry';
import { Image } from './png';

const out = process.argv[2] ?? 'action-preview.png';
const rows: { label: string; p: CharacterPreset; top?: string }[] = [
  { label: '训练短剑 + 皮甲', p: { ...CHARACTERS[0], weapon: 'weapon_training_sword' }, top: 'top_leather_armor' },
  { label: '猎弓 + 皮甲', p: { ...CHARACTERS[2], weapon: 'weapon_hunting_bow' }, top: 'top_leather_armor' },
  { label: '重剑 + 符文甲', p: { ...CHARACTERS[0], hair: 'hair_swept', weapon: 'weapon_great_sword' }, top: 'top_rune_armor' },
  { label: '传奇权杖 + 符文甲', p: { ...CHARACTERS[1], hair: 'hair_long', weapon: 'weapon_legendary_staff' }, top: 'top_rune_armor' },
  { label: '星辉刃 + 星辉甲', p: { ...CHARACTERS[0], hair: 'hair_ponytail', weapon: 'weapon_starlight_blade' }, top: 'top_starlight_armor' },
  { label: '龙牙剑 + 龙纹甲', p: { ...CHARACTERS[0], hair: 'hair_swept', skin: 'tan', weapon: 'weapon_dragon_fang' }, top: 'top_dragon_armor' },
];

const Z = 4, PAD = 2;
const head: [Dir5, number][] = [['E', 0], ['S', READY_FRAMES[0]], ['SE', READY_FRAMES[0]], ['E', READY_FRAMES[0]], ['E', READY_FRAMES[1]]];
function rowCells(attack: ActionId): [Dir5, number][] {
  return [
    ...head,
    ...ACTION_FRAMES[attack].map((f) => ['E', f] as [Dir5, number]),
    ...ACTION_FRAMES[attack].map((f) => ['SE', f] as [Dir5, number]),
    ...ACTION_FRAMES.cast.map((f) => ['E', f] as [Dir5, number]),
  ];
}
const cols = rowCells('slash').length;
const img = new Image(cols * (SPR_W * Z + PAD), rows.length * (SPR_H * Z + PAD));
for (let i = 0; i < img.data.length; i += 4) img.data.set([95, 143, 80, 255], i);

rows.forEach((r, ri) => {
  const eq = buildEquipment(r.p);
  if (r.top) eq.equip('top', getItem(r.top)!);
  eq.unequip('scarf');
  eq.unequip('bag');
  const w = getItem(r.p.weapon!)!;
  const attack: ActionId = w.attack ?? ({ down: 'slash', shoulder: 'heavy', bow: 'shoot', up: 'cast' } as const)[w.hold ?? 'up'];
  rowCells(attack).forEach(([dir, f], ci) => {
    const L = new PixelLayer(SPR_W, SPR_H);
    composeFrame(eq.resolve(), dir, f, L);
    const im = new Image(SPR_W, SPR_H);
    L.toRGBA(im.data);
    img.blit(im, ci * (SPR_W * Z + PAD), ri * (SPR_H * Z + PAD), Z);
  });
  console.log(`${r.label}: ${attack}`);
});
writeFileSync(out, img.png());
console.log(`→ ${out}`);
