import { pal, ramp, DARK, HI, OUTLINE } from '../../pixel/palette';
import { LX, LY, LZ, DARKEN, LIGHTEN } from '../../pixel/Brush';
import type { ItemDef, PartDef } from '../../character/types';
import { farBias } from '../shared';

/** 棕色短靴：小巧的翻边靴口、薄鞋底、朝脚尖方向伸出的鞋头。脚要小，腿部动作（跨步、下蹲）才看得清。 */
const brown = pal('boots-brown', '#160c06', '#3c2212', '#6c4024', '#9c6838', '#d09c5c');

const boot = (i: 0 | 1): PartDef => ({
  layer: 'shoes',
  draw: (c) => {
    const { g, pose } = c;
    const f = pose.legs[i].foot;
    const fb = farBias(c, f);
    const x = f.x, y = f.y;
    const toe = pose.sin * 1.7;
    const front = pose.cos > 0.9;
    c.pal('main');
    g.anchor(x, y);

    // 脚掌：一个压扁的椭球，朝脚尖方向伸出去，底面削平
    const sole = y + (front ? 1.1 : 0.4);
    const fcx = x + toe * 0.9, fcy = y - 1.1 + (front ? 0.6 : 0);
    const frx = 2.2 + Math.abs(toe) * 0.7, fry = 2;
    g.fill(fcx - frx, fcy - fry, fcx + frx, sole, (u, v) => {
      const nx = (u - fcx) / frx, ny = (v - fcy) / fry;
      const d = nx * nx + ny * ny;
      if (d > 1 || v > sole) return -1;
      if (v > sole - 0.6) return OUTLINE; // 鞋底
      return g.t(nx * LX + ny * LY + Math.sqrt(1 - d) * LZ, fb);
    });
    // 靴筒
    g.capsule(x, y - 4.4, x, y - 2, 2.05, 2.15, (lam) => g.t(lam, fb));
    // 翻边靴口：比靴筒宽一圈
    g.fill(x - 2.7, y - 5.9, x + 2.7, y - 4, (u, v) => {
      const nx = (u - x) / 2.6;
      if (Math.abs(nx) > 1 || v < y - 5.8 || v > y - 4.1) return -1;
      return g.t(nx * LX + Math.sqrt(1 - nx * nx) * LZ, fb + (v > y - 4.7 ? -0.3 : 0.3));
    });

    g.clip = true;
    g.line(x - 2, y - 3.8, x + 2.2, y - 3.8, DARKEN); // 翻边下的阴影
    if (fb === 0) {
      g.dot(x - 1.8, y - 5.5, HI);
      if (pose.cos > 0.3) {
        const lx = x + pose.sin * 1.2;
        g.line(lx - 0.8, y - 2.6, lx + 0.8, y - 2.6, LIGHTEN); // 鞋带
      } else if (pose.cos < -0.3) {
        g.line(x, y - 4, x, y - 1.2, DARKEN); // 后跟的缝线
      } else {
        g.fold(x - 1, y - 3, x + 1.6, y - 2.3); // 脚踝的褶
      }
      g.dot(fcx - 0.8 + toe * 0.3, fcy - 1, LIGHTEN); // 鞋头高光
    } else {
      g.line(x - 2, y - 3.3, x + 2.2, y - 3.3, DARK);
    }
    g.clip = false;
  },
});

export const boots: ItemDef = {
  id: 'shoes_boots',
  name: '棕色短靴',
  slot: 'shoes',
  palettes: { main: brown },
  variants: [
    { id: 'brown', name: '棕', palettes: { main: brown } },
    { id: 'black', name: '黑', palettes: { main: ramp('boots-black', '#34343e') } },
  ],
  parts: [boot(0), boot(1)],
};
