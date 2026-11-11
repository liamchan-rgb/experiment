import { pal, ramp } from '../../pixel/palette';
import { LX, LZ, DARKEN } from '../../pixel/Brush';
import { CX } from '../../character/rig';
import type { ItemDef, PartDef } from '../../character/types';
import { farBias } from '../shared';

/** 深色长裤。两条裤腿各占一个部件，这样交叉时有描边分隔。 */
const dark = pal('trousers-dark', '#0a0a12', '#1a1c2a', '#2e3142', '#484c62', '#6c7088');

const leg = (i: 0 | 1): PartDef => ({
  layer: 'bottom',
  draw: (c) => {
    const { g } = c;
    const l = c.pose.legs[i];
    const fb = farBias(c, l.foot);
    const fx = l.foot.x, fy = l.foot.y - 5;
    c.pal('main');
    g.anchor(fx, fy);
    g.capsule(l.hip.x, l.hip.y, fx, fy, 2.8, 2.5, (lam) => g.t(lam, fb + 0.05));
    // 膝盖和裤脚的褶
    const kx = (l.hip.x + fx) / 2, ky = (l.hip.y + fy) / 2;
    g.fold(kx - 1.8, ky, kx + 1.4, ky + 0.7);
    g.fold(fx - 1.8, fy - 1.4, fx + 1.6, fy - 0.8, false);
  },
});

export const trousers: ItemDef = {
  id: 'bottom_trousers',
  name: '深色长裤',
  slot: 'bottom',
  palettes: { main: dark },
  variants: [
    { id: 'dark', name: '深灰蓝', palettes: { main: dark } },
    { id: 'brown', name: '深棕', palettes: { main: ramp('trousers-brown', '#54392a') } },
    { id: 'white', name: '米白', palettes: { main: ramp('trousers-cream', '#c4b898') } },
  ],
  parts: [
    leg(0),
    leg(1),
    {
      // 胯部
      layer: 'bottom',
      draw: (c) => {
        const { g, pose } = c;
        const hw = pose.torsoHalf - 0.2, y = pose.legs[0].hip.y;
        c.pal('main');
        g.fill(CX - hw, y - 4.5, CX + hw, y + 3, (u, v) => {
          const nx = (u - CX) / hw;
          if (Math.abs(nx) > 1 || v < y - 4.5) return -1;
          if (v > y + 1 + 1.4 * (1 - Math.abs(nx))) return -1; // 下缘中间收成裆部
          return g.t(nx * LX + Math.sqrt(1 - nx * nx) * LZ, -0.15); // 整个在上衣的阴影里
        });
        if (Math.abs(pose.sin) < 0.9) {
          const sx = CX + pose.sin * 2.2;
          g.clip = true;
          g.line(sx, y - 1, sx, y + 2.2, DARKEN); // 裆部的分缝
          g.clip = false;
        }
      },
    },
  ],
};
