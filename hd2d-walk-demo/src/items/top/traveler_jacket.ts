import { pal, ramp, BASE, DARK, HI, LIGHT, OUTLINE } from '../../pixel/palette';
import { DARKEN, LIGHTEN } from '../../pixel/Brush';
import { CX } from '../../character/rig';
import type { ItemDef } from '../../character/types';
import { frontX, sleeveParts, torsoShape } from '../shared';

/** 蓝色旅人装：下摆张开的短上衣，翻领，金扣，下摆和袖口白色镶边。 */
const blue = pal('jacket-blue', '#0c1430', '#1c3464', '#2f589e', '#5288cc', '#a0c8f0');
const trim = pal('trim-white', '#3c4258', '#8088a0', '#c2c4c8', '#ece8dc', '#fffcf2');
const metal = pal('button-gold', '#3e2408', '#8a5c16', '#d8a430', '#f6d86c', '#fff6c0');

const ROWS = 13.2;
const HEM = 3;

export const travelerJacket: ItemDef = {
  id: 'top_traveler',
  name: '蓝色旅人装',
  slot: 'top',
  palettes: { main: blue, trim, metal },
  variants: [
    { id: 'blue', name: '蓝', palettes: { main: blue } },
    { id: 'green', name: '绿', palettes: { main: ramp('jacket-green', '#3a8a54') } },
    { id: 'purple', name: '紫', palettes: { main: ramp('jacket-purple', '#6e4eb0') } },
  ],
  parts: [
    {
      layer: 'top',
      draw: (c) => {
        const { g, pose } = c;
        const hw = pose.torsoHalf, ny = pose.neckY;
        const hem = ROWS - HEM;
        c.pal('main');
        torsoShape(c, ROWS, { flare: 2 }, (lam, _nx, r) => {
          if (r > hem) return -1;
          if (r < 2.6) return OUTLINE; // 围巾 / 下巴投下的深阴影
          if (r < 3.6 || r > hem - 0.6) return DARK;
          // 腰以下在上身的阴影里略暗，下摆翘起的地方又亮回来
          return g.t(lam, r > 7 && r < 10 ? -0.12 : 0.05);
        });
        // 下摆白边
        c.pal('trim');
        torsoShape(c, ROWS, { flare: 2 }, (lam, _nx, r) => (r <= hem ? -1 : g.t(lam, r > ROWS - 0.7 ? -0.35 : 0.3)));

        c.pal('main');
        g.clip = true;
        // 衣褶：从腋下往腰间收
        g.fold(CX - hw + 1, ny + 4.8, CX - hw + 3.8, ny + 7.4);
        g.fold(CX + hw - 1, ny + 4.4, CX + hw - 3.4, ny + 7);
        

        if (pose.cos > 0.3) {
          // 正面：门襟、翻领、金扣
          const fx = frontX(c);
          g.line(fx, ny + 3, fx, ny + hem - 0.6, DARKEN);
          c.pal('trim');
          g.tri({ x: fx, y: ny + 2.2 }, { x: fx - 3.8, y: ny + 2.8 }, { x: fx - 0.4, y: ny + 7 }, LIGHT);
          g.tri({ x: fx, y: ny + 2.2 }, { x: fx + 3.8, y: ny + 2.8 }, { x: fx + 0.4, y: ny + 7 }, BASE);
          c.pal('metal');
          for (const r of [7, 9]) {
            g.dot(fx + 1.2, ny + r, HI);
            g.dot(fx + 1.2, ny + r + 1, DARK);
          }
        } else if (pose.cos < -0.3) {
          // 背面：后中缝 + 腰间的半腰带
          const bx = CX - hw * 0.4 * pose.sin;
          g.line(bx, ny + 3.5, bx, ny + 7, DARKEN);
          g.rect(bx - 3.4, ny + 7.4, 6.8, 1.6, (_u, v) => (v < ny + 8.1 ? LIGHT : DARK));
          c.pal('metal');
          g.dot(bx - 3, ny + 7.8, HI);
          g.dot(bx + 3, ny + 7.8, LIGHT);
        } else {
          g.line(CX - 0.6, ny + 5, CX - 0.6, ny + hem - 1, DARKEN); // 侧缝
          g.line(CX + 0.6, ny + 8.6, CX + 3, ny + 8.6, LIGHTEN); // 口袋
        }
        g.clip = false;
      },
    },
    ...sleeveParts({ key: 'main', cuffKey: 'trim' }),
  ],
};
