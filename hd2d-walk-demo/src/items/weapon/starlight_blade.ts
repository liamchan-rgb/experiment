import { pal, HI } from '../../pixel/palette';
import type { ItemDef } from '../../character/types';
import { at, drawSword, frameOf, fxPart, trailPart, type SwordOpts } from '../kits/weaponKit';

/** 星辉刃（星辉套装）：冰蓝色的水晶剑身，中间一道发光的芯，银色护手嵌蓝宝石；剑身旁常有星点。 */
const crystal = pal('starlight-crystal', '#0e2448', '#2a64a8', '#5aa6e0', '#a8e0fa', '#f4ffff');
const silver = pal('starlight-silver', '#1c2232', '#5a6478', '#a4aec0', '#dce4ee', '#ffffff');
const grip = pal('starlight-grip', '#0a0c1c', '#1c2450', '#2e3c80', '#4a5eb0', '#7a8ed8');
const star = pal('fx-star', '#2a5a9a', '#5aa0e0', '#9ad8f8', '#d8f4ff', '#ffffff');

const BLADE: SwordOpts = { from: 3.6, to: 21, half: 1.3, tip: 5, core: 'glow', grip: 2.6, guard: [3.6, 1.2, 1.2], pommel: 1.2 };

export const starlightBlade: ItemDef = {
  id: 'weapon_starlight_blade',
  name: '星辉刃',
  slot: 'weapon_main',
  hold: 'down',
  gameItem: 'starlightBlade',
  palettes: { blade: crystal, hilt: silver, grip, gem: star, fx: star },
  parts: [
    { layer: 'weapon', draw: (c) => drawSword(c, BLADE, true) },
    {
      // 剑身旁飘着的两颗星点
      layer: 'weapon_front',
      outline: false,
      draw: (c) => {
        const f = frameOf(c);
        if (!f) return;
        c.pal('fx');
        const a = at(f, 15, -3), b = at(f, 9, 2.8);
        c.g.dot(a.x, a.y, HI);
        c.g.dot(b.x, b.y, HI);
      },
    },
    trailPart(6, 23),
    fxPart((f) => at(f, 19), 'fx', 0.9),
  ],
};
