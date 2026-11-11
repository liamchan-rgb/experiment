import { pal, BASE, DARK, HI, LIGHT } from '../../pixel/palette';
import type { ItemDef } from '../../character/types';

/**
 * 短剑。按手部锚点（坐标 + 角度）绘制；layer: 'weapon' 表示
 * 根据方向自动落到身前或身后的武器层。
 */
const steel = pal('steel', '#141a28', '#56647e', '#a0b0c6', '#dce8f2', '#ffffff');
const hilt = pal('hilt-gold', '#3e2408', '#8a5c16', '#d8a430', '#f6d86c', '#fff6c0');
const grip = pal('grip-leather', '#140a06', '#34200f', '#583820', '#80542e', '#aa7a48');

export const shortSword: ItemDef = {
  id: 'weapon_short_sword',
  name: '短剑',
  slot: 'weapon_main',
  hold: 'down',
  palettes: { blade: steel, hilt, grip },
  parts: [
    {
      layer: 'weapon',
      draw: (c) => {
        const h = c.hand;
        if (!h) return;
        const { g } = c;
        const dx = Math.cos(h.angle), dy = Math.sin(h.angle);
        const x = h.x, y = h.y + 0.6;

        // 剑身：受光面亮、背光面暗，末端收成剑尖
        c.pal('blade');
        g.axis(x, y, dx, dy, 3.8, 19.5, 1.2, (t, o) => {
          const hw = t < 15.5 ? 1.15 : (1.15 * (19.5 - t)) / 4;
          if (Math.abs(o) > hw) return -1;
          if (o < -0.15) return t > 7 && t < 14 ? HI : LIGHT;
          return o > 0.55 ? DARK : BASE;
        });
        // 握柄（缠皮）
        c.pal('grip');
        g.axis(x, y, dx, dy, -2.4, 3, 0.75, (t, o) => (o > 0.3 ? DARK : Math.floor(t * 1.2 + 10) % 2 ? BASE : LIGHT));
        // 护手和配重球
        c.pal('hilt');
        g.axis(x, y, dx, dy, 2.6, 4.2, 3.3, (t, o) => {
          const bend = 0.2 * Math.abs(o); // 两端朝剑尖方向翘
          if (t < 2.7 + bend || t > 3.9 + bend) return -1;
          return o < -1.6 ? HI : o > 1.8 ? DARK : LIGHT;
        });
        g.ellipse(x - dx * 3.2, y - dy * 3.2, 1.2, 1.2, (lam) => (lam > 0.4 ? HI : lam > -0.2 ? BASE : DARK));
      },
    },
  ],
};
