import { pal, ramp, BASE, DARK, HI, LIGHT } from '../../pixel/palette';
import type { DrawCtx, ItemDef } from '../../character/types';
import { along, at, frameOf, fxPart, type Frame } from '../kits/weaponKit';

/**
 * 法杖类：竖握在身侧（hold: 'up'），普通攻击是施法（cast）：蓄力 → 高举 → 前推释放。
 *   法杖：长木柄 + 月牙形金托 + 发光宝珠
 *   传奇权杖：螺旋金柄，杖头一对金翼托着大宝石，外面套一圈浮空的金环
 */
const wood = pal('staff-wood', '#180e08', '#4a2e18', '#7c522a', '#aa7a40', '#d4a460');
const gold = pal('staff-gold', '#3e2408', '#8a5c16', '#d8a430', '#f6d86c', '#fff6c0');
const gem = pal('staff-gem', '#082a44', '#147aa0', '#30c2dc', '#90f0f4', '#f0ffff');

/** 宝珠：球面光照 + 一个高光点 */
function orb(c: DrawCtx, x: number, y: number, r: number): void {
  c.g.ellipse(x, y, r, r, (lam) => (lam > 0.8 ? HI : lam > 0.4 ? LIGHT : lam > -0.15 ? BASE : DARK));
  c.g.dot(x - r * 0.4, y - r * 0.4, HI);
}

function drawStaff(c: DrawCtx): void {
  const f = frameOf(c);
  if (!f) return;
  const { g } = c;
  // 木柄：带几处木节，握把处缠了布条
  c.pal('wood');
  along(c, f, -11, 34.5, 0.75, (t, o) => {
    if (t > -2 && t < 2.8) return o > 0.2 ? DARK : Math.floor(t * 1.2 + 10) % 2 ? BASE : LIGHT;
    const knot = Math.abs(((t + 40) % 7) - 3.5) < 0.5;
    return o < 0 ? (knot ? BASE : LIGHT) : DARK;
  });
  // 金箍和杖尾
  c.pal('gold');
  along(c, f, 33.6, 35.6, 1.2, (_t, o) => (o < -0.4 ? HI : o > 0.5 ? DARK : LIGHT));
  along(c, f, -12.4, -11, 1.05, (_t, o) => (o < 0 ? LIGHT : DARK));

  // 月牙金托：围着宝珠的大半个环，朝杖尖一侧开口
  const { x: ox, y: oy } = at(f, 40);
  const { dx, dy } = f;
  g.fill(ox - 6, oy - 6, ox + 6, oy + 6, (u, v) => {
    const ex = u - ox, ey = v - oy;
    const d = Math.hypot(ex, ey);
    const al = (ex * dx + ey * dy) / (d || 1);
    const half = 0.8 * Math.max(0, 1 - Math.max(0, al + 0.2) * 1.1); // 往两个尖端收细
    if (Math.abs(d - 4.2) > half || al > 0.62) return -1;
    const lit = -(ex * 0.56 + ey * 0.62) / d;
    return lit > 0.55 ? HI : lit > 0 ? LIGHT : lit > -0.6 ? BASE : DARK;
  });
  c.pal('gem');
  orb(c, ox, oy, 2.7);
  // 宝珠旁飘着的两点微光
  g.dot(ox + dx * 4.5 - dy * 2.4, oy + dy * 4.5 + dx * 2.4, HI);
  g.dot(ox - dy * 5 + dx, oy + dx * 5 + dy, LIGHT);
}

export const staff: ItemDef = {
  id: 'weapon_staff',
  name: '法杖',
  slot: 'weapon_main',
  palettes: { wood, gold, gem, fx: gem },
  variants: [
    { id: 'aqua', name: '水蓝宝珠', palettes: { gem, fx: gem } },
    { id: 'ember', name: '炽红宝珠', palettes: { gem: ramp('staff-gem-ember', '#e8552c'), fx: ramp('staff-gem-ember', '#e8552c') } },
    { id: 'violet', name: '紫晶宝珠', palettes: { gem: ramp('staff-gem-violet', '#9a5ce0'), fx: ramp('staff-gem-violet', '#9a5ce0') } },
  ],
  parts: [
    { layer: 'weapon', draw: drawStaff },
    fxPart((f: Frame) => at(f, 40), 'fx', 1),
  ],
};

const royal = pal('scepter-gold', '#3a1c04', '#8a5410', '#d89a26', '#f8d468', '#fffbd0');
const ruby = pal('scepter-gem', '#2a0420', '#7a1050', '#c42a80', '#f070b4', '#ffd8f0');
const shaftDark = pal('scepter-shaft', '#0c0a18', '#24203c', '#3e3864', '#625a94', '#9088c4');

function drawScepter(c: DrawCtx): void {
  const f = frameOf(c);
  if (!f) return;
  const { g } = c;
  const { dx, dy } = f;
  // 深色柄缠着金色螺旋
  c.pal('shaft');
  along(c, f, -9, 31, 0.8, (_t, o) => (o < -0.1 ? LIGHT : o > 0.4 ? DARK : BASE));
  c.pal('gold');
  g.clip = true;
  along(c, f, -9, 31, 0.8, (t, o) => (Math.abs(((t * 0.55 + o * 0.9 + 20) % 2) - 1) < 0.32 ? (o < 0 ? HI : LIGHT) : -1));
  g.clip = false;
  along(c, f, -10.6, -9, 1.2, (_t, o) => (o < 0 ? LIGHT : DARK));
  along(c, f, 30, 32.4, 1.5, (_t, o) => (o < -0.4 ? HI : o > 0.6 ? DARK : LIGHT));

  // 杖头：一对金翼从两侧往上合拢，托着宝石
  const { x: hx, y: hy } = at(f, 37.5);
  for (const side of [-1, 1]) {
    g.fill(hx - 8, hy - 8, hx + 8, hy + 8, (u, v) => {
      const ex = u - hx, ey = v - hy;
      const t = -(ex * dx + ey * dy); // 沿杖往下为正
      const o = (ex * -dy + ey * dx) * side; // 往这一侧为正
      if (t < -4.5 || t > 4.5) return -1;
      // 翼的外缘：中段鼓出去，往上收成尖
      const outer = 3.2 + 2.6 * Math.cos(((t + 0.5) / 5) * 1.4) - Math.max(0, -t - 2) * 0.9;
      if (o < 2.2 || o > outer) return -1;
      const feather = Math.abs(((o + t * 0.6 + 20) % 1.6) - 0.8) < 0.22;
      const lit = side < 0 ? 0.4 : -0.2;
      return feather ? DARK : lit - t * 0.08 > 0.2 ? HI : lit > 0 ? LIGHT : BASE;
    });
  }
  c.pal('gem');
  orb(c, hx, hy, 2.6);
  c.pal('gold');
  // 浮空的金环：宝石上方一道细椭圆弧
  const ring = at(f, 43.2);
  g.fill(ring.x - 4, ring.y - 3, ring.x + 4, ring.y + 3, (u, v) => {
    const ex = (u - ring.x) / 3.4, ey = (v - ring.y) / 1.3;
    const d = Math.hypot(ex, ey);
    return Math.abs(d - 1) < 0.28 ? (ey < 0 ? HI : LIGHT) : -1;
  });
}

export const legendaryStaff: ItemDef = {
  id: 'weapon_legendary_staff',
  name: '传奇权杖',
  slot: 'weapon_main',
  gameItem: 'legendaryStaff',
  palettes: { shaft: shaftDark, gold: royal, gem: ruby, fx: ruby },
  parts: [
    { layer: 'weapon', draw: drawScepter },
    fxPart((f: Frame) => at(f, 37.5), 'fx', 1.2),
  ],
};
