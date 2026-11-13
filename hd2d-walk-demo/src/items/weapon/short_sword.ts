import { pal, ramp } from '../../pixel/palette';
import type { ItemDef } from '../../character/types';
import { drawSword, trailPart, type SwordOpts } from '../kits/weaponKit';

/**
 * 单手剑：短剑和训练短剑。按手部锚点（坐标 + 角度 + 缩短比例）绘制；layer: 'weapon' 表示
 * 根据方向自动落到身前、头后或身后的武器层。普通攻击是单手挥砍（slash）。
 */
const steel = pal('steel', '#141a28', '#56647e', '#a0b0c6', '#dce8f2', '#ffffff');
const hilt = pal('hilt-gold', '#3e2408', '#8a5c16', '#d8a430', '#f6d86c', '#fff6c0');
const grip = pal('grip-leather', '#140a06', '#34200f', '#583820', '#80542e', '#aa7a48');
const swish = pal('fx-swish', '#5a6c88', '#9eb2cc', '#d4e2f0', '#f2f8ff', '#ffffff');

const SHORT: SwordOpts = { from: 3.8, to: 19.5, half: 1.15, tip: 4, grip: 2.4, guard: [3.3, 1.2, 0.6], pommel: 1.2 };

export const shortSword: ItemDef = {
  id: 'weapon_short_sword',
  name: '短剑',
  slot: 'weapon_main',
  hold: 'down',
  palettes: { blade: steel, hilt, grip, fx: swish },
  parts: [
    { layer: 'weapon', draw: (c) => drawSword(c, SHORT) },
    trailPart(11, 20),
  ],
};

/** 训练短剑：钝口的铁剑，木柄，扁平的铁护手 */
const iron = pal('iron-dull', '#16161a', '#4a4a52', '#7a7a80', '#a8a6a0', '#d0ccc0');
const wood = pal('grip-wood', '#180e08', '#4a2e18', '#7c522a', '#aa7a40', '#d4a460');
const TRAINING: SwordOpts = { from: 3.2, to: 17, half: 1.1, tip: 2.2, core: 'fuller', grip: 2.6, guard: [2.8, 1.2, 0], pommel: 1 };

export const trainingSword: ItemDef = {
  id: 'weapon_training_sword',
  name: '训练短剑',
  slot: 'weapon_main',
  hold: 'down',
  gameItem: 'trainingSword',
  palettes: { blade: iron, hilt: ramp('hilt-iron', '#6a6a70'), grip: wood, fx: swish },
  parts: [
    { layer: 'weapon', draw: (c) => drawSword(c, TRAINING) },
    trailPart(10, 18),
  ],
};
