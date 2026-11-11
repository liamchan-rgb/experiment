import { pal, ramp, BASE, DARK, HI, LIGHT, OUTLINE } from '../../pixel/palette';
import { LX, LY, LZ, DARKEN } from '../../pixel/Brush';
import { CX, FOOT_Y } from '../../character/rig';
import { Z } from '../../character/layers';
import type { DrawCtx, ItemDef } from '../../character/types';
import { frontX, sleeveParts, torsoShape } from '../shared';

/**
 * 红色斗篷装：红色短袍 + 肩披 + 垂到小腿的斗篷。
 * 斗篷演示 layerOverride：面向镜头时在身体后面，背对镜头时盖在身体前面。
 */
const red = pal('cloak-red', '#2e0810', '#701422', '#b42a34', '#e0584c', '#fa9c84');
const gold = pal('trim-gold', '#3e2408', '#8a5c16', '#d8a430', '#f6d86c', '#fff6c0');
const leather = pal('belt-leather', '#140a06', '#34200f', '#583820', '#80542e', '#aa7a48');

const ROWS = 12.8;

function cape(c: DrawCtx): void {
  const { g, pose } = c;
  const { sin, cos } = pose;
  const outside = cos < 0.3; // 侧面和背面看到的是斗篷外侧
  const walking = pose.anim === 'walk';
  const sway = walking ? Math.sin(pose.phase + 1) : 0;
  const hwTop = 6.6 * Math.abs(cos) + 3 * Math.abs(sin) + 1.2;
  const hwBottom = hwTop + 3.8;
  const cx0 = CX - sin * 3.8;
  const y0 = pose.neckY - 0.5, y1 = FOOT_Y - 6;
  const folds = 2.2 + Math.abs(cos) * 1.4; // 能看到几道大褶

  g.grit = 0.24;
  g.fill(cx0 - hwBottom - 6, y0, cx0 + hwBottom + 6, y1 + 2, (u, v) => {
    const t = Math.min(1, (v - y0) / (y1 - y0));
    if (t < 0) return -1;
    const mid = cx0 + sway * t * 1.6 - sin * t * 2.4;
    const hw = hwTop + (hwBottom - hwTop) * t;
    const nx = (u - mid) / hw;
    if (Math.abs(nx) > 1) return -1;
    const f = nx * folds * Math.PI + t * sway * 0.8;
    // 下摆破破烂烂地随褶皱起伏
    const hem = y1 + 0.9 * Math.sin(f + 0.6) + 0.5 * Math.sin(f * 2.7 + 1) + (walking ? 0.5 * Math.sin(pose.phase * 2 + nx * 2) : 0);
    if (v > hem) return -1;
    const depth = Math.min(1, t * 1.7); // 褶越往下越深
    const ridge = Math.sin(f + 0.9) * depth;
    if (!outside) {
      c.pal('main');
      return ridge > 0.3 ? DARK : OUTLINE; // 内衬在阴影里
    }
    let lam = 0.18 + nx * LX * 0.9 + ridge * 0.75;
    if (t < 0.12) lam -= 0.6; // 肩披投下的阴影
    const dh = hem - v;
    if (dh > 1.7 && dh < 3) {
      c.pal('trim'); // 下摆的金边
      return g.t(lam, 0.25);
    }
    c.pal('main');
    return g.t(lam);
  });
}

function mantle(c: DrawCtx): void {
  const { g, pose } = c;
  const ny = pose.neckY;
  const hw = pose.torsoHalf + 2.9;
  const y0 = ny - 2, yb = ny + 4.6;
  g.fill(CX - hw, y0, CX + hw, yb + 1.4, (u, v) => {
    const nx = (u - CX) / hw;
    if (Math.abs(nx) > 1) return -1;
    const top = y0 + 2.9 * (1 - Math.sqrt(1 - nx * nx)); // 圆肩
    const bottom = yb + 0.7 * Math.cos(nx * hw * 1.7); // 扇形下缘
    if (v < top || v > bottom) return -1;
    const k = (v - y0) / (yb - y0);
    const lam = nx * LX + (k * 1.5 - 0.75) * LY + Math.sqrt(1 - nx * nx) * LZ * 0.85;
    const db = bottom - v;
    if (db > 0.8 && db < 1.8) {
      c.pal('trim'); // 金色滚边
      return g.t(lam, 0.2);
    }
    c.pal('main');
    return g.t(lam);
  });
  if (pose.cos > 0.3) {
    // 领口的金扣
    const fx = frontX(c);
    c.pal('trim');
    g.ellipse(fx, ny + 1.4, 1.3, 1.3, (lam) => (lam > 0.5 ? HI : lam > -0.1 ? LIGHT : DARK));
  }
}

export const redCloak: ItemDef = {
  id: 'top_red_cloak',
  name: '红色斗篷装',
  slot: 'top',
  palettes: { main: red, trim: gold, belt: leather },
  variants: [
    { id: 'red', name: '红', palettes: { main: red } },
    { id: 'forest', name: '墨绿', palettes: { main: ramp('cloak-forest', '#2c6e48') } },
    { id: 'night', name: '夜蓝', palettes: { main: ramp('cloak-night', '#34428c') } },
  ],
  // 背对镜头时斗篷要盖住身体和手臂，但仍在头的后面
  layerOverride: (dir) => (dir === 'N' || dir === 'NE' ? { cape: Z.mantle - 1 } : {}),
  parts: [
    { layer: 'cape', draw: cape },
    {
      layer: 'top',
      draw: (c) => {
        const { g, pose } = c;
        const hw = pose.torsoHalf, ny = pose.neckY;
        c.pal('main');
        torsoShape(c, ROWS, { flare: 1.6 }, (lam, _nx, r) => (r > ROWS - 1.6 ? -1 : g.t(lam, r > 9.8 ? -0.1 : 0)));
        c.pal('trim');
        torsoShape(c, ROWS, { flare: 1.6 }, (lam, _nx, r) => (r <= ROWS - 1.6 ? -1 : g.t(lam, 0.2)));
        // 腰带
        c.pal('belt');
        torsoShape(c, ROWS, { flare: 1.6 }, (lam, _nx, r) =>
          r < 8 || r > 9.8 ? -1 : r < 8.6 ? LIGHT : r > 9.3 ? OUTLINE : g.t(lam, -0.25));
        g.clip = true;
        c.pal('main');
        g.fold(CX - hw + 1, ny + 4.6, CX - hw + 3.6, ny + 7.2);
        g.fold(CX + hw - 1, ny + 4.2, CX + hw - 3.2, ny + 6.8);
        if (pose.cos > 0.3) {
          const fx = frontX(c);
          c.pal('trim');
          g.line(fx, ny + 4.6, fx, ny + 7.6, BASE); // 前襟的金线
          g.rect(fx - 1.2, ny + 7.8, 2.4, 2.4, (u, v) => (u < fx - 0.4 || v < ny + 8.5 ? HI : DARK)); // 带扣
        } else {
          g.line(CX, ny + 4, CX, ny + 7.6, DARKEN);
        }
        g.clip = false;
      },
    },
    ...sleeveParts({ key: 'main', cuffKey: 'trim' }),
    { layer: 'mantle', draw: mantle },
  ],
};
