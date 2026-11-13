import { pal } from '../../pixel/palette';
import type { ItemDef } from '../../character/types';
import { at, drawSword, fxPart, trailPart, type SwordOpts } from '../kits/weaponKit';

/**
 * 双手大剑：平时扛在右肩（hold: 'shoulder'），普通攻击是双手重劈（heavy）。
 *   重剑：宽厚的钢剑身，长柄，粗大的十字护手
 *   龙牙剑：龙牙一样微弯、往剑尖收得很长的骨白色剑身，暗红握柄，翼形护手
 */
const steel = pal('greatsword-steel', '#10141e', '#4a5468', '#8c9aae', '#cad6e4', '#f6faff');
const iron = pal('greatsword-hilt', '#121216', '#3c3c46', '#6c6c78', '#a2a2ac', '#d8d8e0');
const leather = pal('greatsword-grip', '#120806', '#2e1a0e', '#523420', '#7a5232', '#a07648');
const swish = pal('fx-heavy', '#5c6a80', '#a0b0c4', '#d6e0ec', '#f2f6fc', '#ffffff');

const GREAT: SwordOpts = { from: 4.2, to: 31, half: 2, tip: 4, core: 'fuller', grip: 5, guard: [4.6, 1.6, 0.8], pommel: 1.5 };

export const greatSword: ItemDef = {
  id: 'weapon_great_sword',
  name: '重剑',
  slot: 'weapon_main',
  hold: 'shoulder',
  gameItem: 'greatSword',
  palettes: { blade: steel, hilt: iron, grip: leather, fx: swish },
  parts: [
    { layer: 'weapon', draw: (c) => drawSword(c, GREAT) },
    trailPart(19, 31),
    fxPart((f) => at(f, 28), 'fx', 0.9),
  ],
};

const bone = pal('fang-bone', '#2a1810', '#7a5a44', '#c0a888', '#e8dcc4', '#fffaf0');
const crimson = pal('fang-hilt', '#24060a', '#62121a', '#a42a2a', '#dc5a3e', '#f8a070');
const wrap = pal('fang-grip', '#0e0606', '#2a1012', '#4a1e1e', '#6e3028', '#94503c');
const ember = pal('fx-ember', '#7a1c0c', '#d04a18', '#f6902c', '#ffd060', '#fff6c8');

const FANG: SwordOpts = { from: 4, to: 29, half: 2.2, tip: 11, curve: -1.8, grip: 4.6, guard: [5, 1.8, 2.2], pommel: 1.4 };

export const dragonFangSword: ItemDef = {
  id: 'weapon_dragon_fang',
  name: '龙牙剑',
  slot: 'weapon_main',
  hold: 'shoulder',
  gameItem: 'dragonFangSword',
  palettes: { blade: bone, hilt: crimson, grip: wrap, gem: ember, fx: ember },
  parts: [
    { layer: 'weapon', draw: (c) => drawSword(c, FANG, true) },
    trailPart(18, 29),
    fxPart((f) => at(f, 26), 'fx', 1),
  ],
};
