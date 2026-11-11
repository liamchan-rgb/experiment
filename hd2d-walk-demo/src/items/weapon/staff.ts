import { pal, ramp, BASE, DARK, HI, LIGHT } from '../../pixel/palette';
import type { ItemDef } from '../../character/types';

/** 法杖：比人还高的长木柄 + 月牙形金托 + 发光的宝珠。竖握在身侧，宝珠高过头顶。 */
const wood = pal('staff-wood', '#180e08', '#4a2e18', '#7c522a', '#aa7a40', '#d4a460');
const gold = pal('staff-gold', '#3e2408', '#8a5c16', '#d8a430', '#f6d86c', '#fff6c0');
const gem = pal('staff-gem', '#082a44', '#147aa0', '#30c2dc', '#90f0f4', '#f0ffff');

export const staff: ItemDef = {
  id: 'weapon_staff',
  name: '法杖',
  slot: 'weapon_main',
  palettes: { wood, gold, gem },
  variants: [
    { id: 'aqua', name: '水蓝宝珠', palettes: { gem } },
    { id: 'ember', name: '炽红宝珠', palettes: { gem: ramp('staff-gem-ember', '#e8552c') } },
    { id: 'violet', name: '紫晶宝珠', palettes: { gem: ramp('staff-gem-violet', '#9a5ce0') } },
  ],
  parts: [
    {
      layer: 'weapon',
      draw: (c) => {
        const h = c.hand;
        if (!h) return;
        const { g } = c;
        const dx = Math.cos(h.angle), dy = Math.sin(h.angle);
        const x = h.x, y = h.y + 0.6;

        // 木柄：带几处木节，握把处缠了布条
        c.pal('wood');
        g.axis(x, y, dx, dy, -11, 34.5, 0.75, (t, o) => {
          if (t > -2 && t < 2.8) return o > 0.2 ? DARK : Math.floor(t * 1.2 + 10) % 2 ? BASE : LIGHT;
          const knot = Math.abs(((t + 40) % 7) - 3.5) < 0.5;
          return o < 0 ? (knot ? BASE : LIGHT) : DARK;
        });
        // 金箍和杖尾
        c.pal('gold');
        g.axis(x, y, dx, dy, 33.6, 35.6, 1.2, (_t, o) => (o < -0.4 ? HI : o > 0.5 ? DARK : LIGHT));
        g.axis(x, y, dx, dy, -12.4, -11, 1.05, (_t, o) => (o < 0 ? LIGHT : DARK));

        // 月牙金托：围着宝珠的大半个环，朝杖尖一侧开口
        const ox = x + dx * 40, oy = y + dy * 40;
        g.fill(ox - 6, oy - 6, ox + 6, oy + 6, (u, v) => {
          const ex = u - ox, ey = v - oy;
          const d = Math.hypot(ex, ey);
          const along = (ex * dx + ey * dy) / (d || 1);
          const half = 0.8 * Math.max(0, 1 - Math.max(0, along + 0.2) * 1.1); // 往两个尖端收细
          if (Math.abs(d - 4.2) > half || along > 0.62) return -1;
          const lit = -(ex * 0.56 + ey * 0.62) / d;
          return lit > 0.55 ? HI : lit > 0 ? LIGHT : lit > -0.6 ? BASE : DARK;
        });
        // 宝珠
        c.pal('gem');
        g.ellipse(ox, oy, 2.7, 2.7, (lam) => (lam > 0.8 ? HI : lam > 0.4 ? LIGHT : lam > -0.15 ? BASE : DARK));
        g.dot(ox - 1, oy - 1.1, HI);
        // 宝珠旁飘着的两点微光
        g.dot(ox + dx * 4.5 - dy * 2.4, oy + dy * 4.5 + dx * 2.4, HI);
        g.dot(ox - dy * 5 + dx, oy + dx * 5 + dy, LIGHT);
      },
    },
  ],
};
