import { pal, ramp, type Palette, OUTLINE, DARK, BASE, LIGHT, HI } from '../pixel/palette';
import { getItem } from '../items/registry';
import { lit, sphere, type IconCtx, type IconDef, type Piece } from './iconKit';

/**
 * 武器图标（参考用户给的像素武器设计稿的画法）：
 *   - 刀身有结构：受光的刃口一道 1 像素亮线、背脊一道暗线，颜色从护手到剑尖渐变；
 *   - 轮廓有记忆点：锯齿背、水晶棱、弯牙、带宝石的圆形尖刺护手、龙翼护手、弯月杖头……
 *   - 特效画进图里：火焰、冰晶、星屑、飘带，不只靠外面的光；
 *   - 斜 45° 摆放，宽度都取 √½ 的整数倍，刃口落在像素的斜对角上，台阶整齐不毛。
 * 动画光效（光晕、扫光、星芒、粒子）仍由 iconKit 按稀有度叠加。
 */

// 沿刀身的方向（左下 → 右上）和垂直方向（右下为正）
const DX = Math.SQRT1_2, DY = -Math.SQRT1_2;
const R = Math.SQRT1_2;
/** k 个对角像素的宽度 */
const w = (k: number) => k * R;

const P = (item: string, key: string): Palette => {
  const p = getItem(item)?.palettes[key];
  if (!p) throw new Error(`icon palette ${item}.${key} missing`);
  return p;
};

/** 刀身坐标系里逐像素作画：t 从 (gx, gy) 往右上，o 往右下 */
function space(c: IconCtx, gx: number, gy: number, fn: (t: number, o: number) => number): void {
  c.g.fill(0, 0, 32, 32, (u, v) => {
    const du = u - gx, dv = v - gy;
    return fn(du * DX + dv * DY, du * -DY + dv * DX);
  });
}

/** 刀身明暗：受光刃口（左上）一道亮线，背脊（右下）一道暗线 */
function edge(o: number, half: number): number {
  if (o < -half + 0.75) return HI;
  if (o > half - 0.75) return DARK;
  return o < 0 ? LIGHT : BASE;
}

/** 按沿刀身的位置在几段调色板之间切换（颜色渐变） */
function grad(c: IconCtx, k: number, steps: [number, Palette][]): void {
  let p = steps[0][1];
  for (const [at, q] of steps) if (k >= at) p = q;
  c.use(p);
}

/** 不描边的部件（火焰、星屑这类本身就是光的东西） */
const glowPiece = (draw: (c: IconCtx) => void): Piece => ({ draw, outline: false });

// ---------------------------------------------------------------- 调色板

const steel = pal('w-steel', '#141a28', '#4a5872', '#94a6c0', '#d4e2f2', '#ffffff');
const iron = P('weapon_training_sword', 'blade');
const wood = P('weapon_training_sword', 'grip');
const leather = pal('w-leather', '#160a06', '#3a1e10', '#64381e', '#94582e', '#c08048');
const darkIron = pal('w-dark-iron', '#0c0c10', '#2a2a34', '#4c4c5a', '#7a7a88', '#b0b0bc');
const ruby = pal('w-ruby', '#2a040c', '#7a1020', '#d02a34', '#ff6a5a', '#ffd8c8');
const gold = pal('w-gold', '#3a1e04', '#8a5410', '#d89a26', '#f8d468', '#fffbd0');
const deepBlue = pal('w-deep-blue', '#081030', '#132a6e', '#1f4fb0', '#3f86e6', '#7cc4ff');
const crystal = P('weapon_starlight_blade', 'blade');
const ice = pal('w-ice', '#1c4a7a', '#4aa0d8', '#8ad8f6', '#d0f6ff', '#ffffff');
const silver = P('weapon_starlight_blade', 'hilt');
const navy = P('weapon_starlight_blade', 'grip');
const crimson = pal('w-crimson', '#2a0408', '#6a0e12', '#a8241c', '#e0502a', '#ff8a4a');
const ember = pal('w-ember', '#5a1206', '#b4320c', '#f0701c', '#ffb438', '#fff0a0');
const hot = pal('w-hot', '#8a2a08', '#e06a18', '#ffa830', '#ffe070', '#fffbe0');
const shaft = P('weapon_legendary_staff', 'shaft');
const orb = P('weapon_legendary_staff', 'gem');
const bowWood = P('weapon_hunting_bow', 'wood');
const bowWrap = P('weapon_hunting_bow', 'wrap');
const bowString = P('weapon_hunting_bow', 'string');
const featherRed = P('weapon_hunting_bow', 'fletch');
const featherWhite = pal('w-feather-white', '#3a3a44', '#8a8a96', '#c8c8d0', '#ececf0', '#ffffff');
const cord = ramp('w-cord', '#b8342c');

// ---------------------------------------------------------------- 训练短剑（普通）

const trainingSword: IconDef = {
  id: 'trainingSword', name: '训练短剑', rarity: 'common',
  pieces: [
    // 木柄缠两道皮条，末端一个铁环
    (c) => space(c, 10.5, 21.5, (t, o) => {
      if (t < -5.2 || t > -0.6 || Math.abs(o) > w(1.5)) return -1;
      const band = Math.floor(-t / w(2)) % 2 === 0;
      c.use(band ? leather : wood);
      return o < -0.4 ? LIGHT : o > 0.4 ? DARK : BASE;
    }),
    (c) => space(c, 10.5, 21.5, (t, o) => {
      const d = Math.hypot(t + 6.6, o);
      if (d > 1.9 || d < 0.7) return -1;
      c.use(iron);
      return sphere(lit(-(t + 6.6) * DX, o * DX, 0.5));
    }),
    // 钝口铁剑：刃口亮线、中间一道血槽，刃上两处磕口（练习用的旧剑）
    (c) => space(c, 10.5, 21.5, (t, o) => {
      const len = 18, half = w(2.5);
      if (t < 0.4 || t > len) return -1;
      const hw = t > len - 3.2 ? (half * (len - t)) / 3.2 : half;
      if (Math.abs(o) > hw) return -1;
      if ((t > 6.5 && t < 7.8 && o > hw - 0.8) || (t > 10.8 && t < 11.9 && o < -hw + 0.8)) return -1;
      c.use(iron);
      if (Math.abs(o) < 0.4 && t > 2 && t < len - 4) return DARK;
      return edge(o, hw);
    }),
    // 一字护手，两头圆
    (c) => space(c, 10.5, 21.5, (t, o) => {
      if (Math.abs(t) > 0.75 || Math.abs(o) > w(5.5)) return -1;
      c.use(iron);
      return Math.abs(o) > w(4.5) ? BASE : o < 0 ? HI : LIGHT;
    }),
    // 系在护手上的红绳
    (c) => {
      c.use(cord);
      c.g.line(12, 23.5, 12.6, 25.5, BASE);
      c.g.dot(12.6, 26.5, DARK);
    },
  ],
};

// ---------------------------------------------------------------- 猎弓（普通）

const huntingBow: IconDef = {
  id: 'huntingBow', name: '猎弓', rarity: 'common',
  pieces: [
    // 反曲弓身：中段鼓、两端往回勾，刻着两圈金线
    (c) => {
      const pts = Array.from({ length: 21 }, (_, i) => {
        const s = i / 10 - 1;
        const a = Math.abs(s);
        const bulge = 5.6 * (1 - s * s) - (a > 0.78 ? 14 * (a - 0.78) ** 2 : 0);
        const along = s * 12.4;
        return { x: 16 + DX * along - DY * bulge, y: 16 + DY * along + DX * bulge };
      });
      c.g.ribbon(pts, (s) => 1.9 - 1.15 * Math.abs(s - 0.5) * 2, (_lam, o, s) => {
        const ring = Math.abs(Math.abs(s - 0.5) - 0.27) < 0.025;
        c.use(ring ? gold : bowWood);
        if (ring) return o < 0 ? HI : LIGHT;
        return o < -0.35 ? HI : o > 0.45 ? DARK : o < 0.1 ? LIGHT : BASE;
      });
    },
    // 握把缠绳
    (c) => {
      c.use(bowWrap);
      space(c, 16 - DY * 5.6, 16 + DX * 5.6, (t, o) => (Math.abs(t) > 2.4 || Math.abs(o) > 2 ? -1 : o > 0.8 ? DARK : Math.floor(t + 10) % 2 ? BASE : LIGHT));
    },
    // 弓弦
    (c) => {
      c.use(bowString);
      const a = { x: 16 - DX * 11.6 + DY * 0.6, y: 16 - DY * 11.6 - DX * 0.6 }, b = { x: 16 + DX * 11.6 + DY * 0.6, y: 16 + DY * 11.6 - DX * 0.6 };
      c.g.line(a.x, a.y, b.x, b.y, LIGHT);
    },
    // 握把下挂的羽毛吊坠：一红一白
    (c) => {
      c.use(cord);
      c.g.line(21.5, 21, 22.5, 25, DARK);
      c.use(featherRed);
      c.g.ellipse(22, 27.3, 1.3, 2.6, (_l, nx) => (nx < 0 ? LIGHT : BASE));
      c.use(featherWhite);
      c.g.ellipse(24.6, 26.2, 1.2, 2.4, (_l, nx) => (nx < 0 ? HI : LIGHT));
    },
  ],
};

// ---------------------------------------------------------------- 重剑（稀有）

const greatSword: IconDef = {
  id: 'greatSword', name: '重剑', rarity: 'rare',
  pieces: [
    // 长柄缠斜纹皮带 + 尖头配重
    (c) => space(c, 8.5, 23.5, (t, o) => {
      if (t < -9.8 || t > -2.2) return -1;
      if (t < -7.4) {
        const hw = w(2) * (t + 9.8) / 2.4;
        if (Math.abs(o) > hw) return -1;
        c.use(darkIron);
        return o < 0 ? LIGHT : BASE;
      }
      if (Math.abs(o) > w(1.5)) return -1;
      c.use(leather);
      return Math.floor(t * 1.2 - o * 1.2 + 20) % 2 ? BASE : LIGHT;
    }),
    // 宽刃：刃口亮线，背脊一排锯齿，中间一道深血槽
    (c) => space(c, 8.5, 23.5, (t, o) => {
      const len = 23.5, half = w(4.5);
      if (t < 0.5 || t > len) return -1;
      const hw = t > len - 4.4 ? (half * (len - t)) / 4.4 : half;
      // 背脊上一排锯齿（每 4 个对角像素一颗，突出 1.5 格）
      const ph = t % w(4);
      const tooth = t > 5 && t < 18.5 ? Math.max(0, w(1.5) - Math.abs(ph - w(1.5)) * 1.1) : 0;
      if (o < -hw || o > hw + tooth) return -1;
      c.use(steel);
      if (o > hw) return o > hw + 0.5 ? DARK : BASE; // 锯齿
      if (Math.abs(o) < 0.4 && t > 2.5 && t < len - 5) return DARK; // 血槽
      return edge(o, hw);
    }),
    // 圆形尖刺护手：一圈铁环 + 八根尖刺
    (c) => space(c, 8.5, 23.5, (t, o) => {
      const r = Math.hypot(t, o), a = Math.atan2(o, t);
      const spike = 4.1 + 1.9 * Math.max(0, Math.cos(4 * a)) ** 8;
      if (r > spike || r < 1.6) return -1;
      c.use(darkIron);
      if (r > 4.1) return lit(t * DX - o * DY, t * DY + o * DX) > 0 ? LIGHT : BASE;
      return sphere(lit((t * DX - o * DY) / r, (t * DY + o * DX) / r, 0.5));
    }),
    // 护手中心的红宝石
    (c) => {
      c.use(ruby);
      c.g.ellipse(8.5, 23.5, 2, 2, (lam) => sphere(lam));
      c.g.dot(7.8, 22.6, HI);
    },
  ],
  fx: { glow: '#ff6a5a', center: [14, 18] },
};

// ---------------------------------------------------------------- 传奇权杖（传说）

const legendaryStaff: IconDef = {
  id: 'legendaryStaff', name: '传奇权杖', rarity: 'legendary',
  pieces: [
    // 杖身：深紫色，三道金箍，底端金色尖头
    (c) => space(c, 5.5, 26.5, (t, o) => {
      if (t < -3.4 || t > 18.4) return -1;
      if (t < 0) {
        if (Math.abs(o) > w(1.5) * (t + 3.4) / 3.4) return -1;
        c.use(gold);
        return o < 0 ? HI : LIGHT;
      }
      if (Math.abs(o) > w(1.5)) return -1;
      const band = [4.2, 9.2, 14.2].some((k) => Math.abs(t - k) < 0.75);
      c.use(band ? gold : shaft);
      if (band) return o < 0 ? HI : BASE;
      return o < -0.4 ? LIGHT : o > 0.4 ? DARK : BASE;
    }),
    // 弯月金托：围着宝珠、往右上开口
    (c) => space(c, 21.4, 10.6, (t, o) => {
      const r = Math.hypot(t, o);
      if (r < 3.6 || r > 5.6) return -1;
      if (t / r > 0.42) return -1; // 开口
      c.use(gold);
      const nx = (t * DX - o * DY) / r, ny = (t * DY + o * DX) / r;
      return r > 4.9 ? (lit(nx, ny) > 0.1 ? HI : BASE) : lit(-nx, -ny) > 0 ? LIGHT : BASE;
    }),
    // 大宝珠
    (c) => {
      c.use(orb);
      c.g.ellipse(21.4, 10.6, 3.3, 3.3, (lam) => sphere(lam));
      c.g.dot(20.3, 9.2, HI);
      c.g.dot(22.6, 12, LIGHT);
    },
    // 环绕的三颗小宝石
    (c) => {
      const gems: [number, number, Palette][] = [[27.5, 5.5, ice], [28, 15.5, gold], [15, 4.5, orb]];
      for (const [x, y, p] of gems) {
        c.use(p);
        c.g.fill(x - 2, y - 2, x + 2, y + 2, (u, v) => (Math.abs(u - x) + Math.abs(v - y) > 1.6 ? -1 : u < x || v < y ? HI : BASE));
      }
    },
  ],
  fx: { glow: '#ff5ab4', sparkle: '#ffd0f0', particles: 'motes', center: [20, 11] },
};

// ---------------------------------------------------------------- 星辉刃（传说）

const starlightBlade: IconDef = {
  id: 'starlightBlade', name: '星辉刃', rarity: 'legendary',
  pieces: [
    // 深蓝握柄缠银线，末端一颗小四角星
    (c) => space(c, 9.5, 22.5, (t, o) => {
      const star = Math.abs(t + 7) + Math.abs(o) * 0.6;
      if (star < 1.6 || (Math.min(Math.abs(t + 7), Math.abs(o)) < 0.5 && Math.abs(t + 7) + Math.abs(o) < 2.6)) {
        c.use(silver);
        return t + 7 < 0 || o < 0 ? HI : LIGHT;
      }
      if (t < -5.6 || t > -1.4 || Math.abs(o) > w(1.5)) return -1;
      const wrap = Math.floor(-t / w(2)) % 2 === 0;
      c.use(wrap ? silver : navy);
      return o < 0 ? LIGHT : BASE;
    }),
    // 水晶刀身：深蓝 → 晶蓝 → 冰白渐变，发光的芯，两侧刃上长出斜向剑尖的冰晶棱
    (c) => space(c, 9.5, 22.5, (t, o) => {
      const len = 22, half = w(3.5);
      if (t < 0.6 || t > len) return -1;
      const hw = t > len - 6 ? (half * (len - t)) / 6 : half;
      let shard = 0;
      for (const t0 of [5, 10, 15]) {
        const a = t - t0;
        if (a >= 0 && a < 3) shard = Math.max(shard, 2.6 * (1 - a / 3));
      }
      const ao = Math.abs(o);
      if (ao > hw + shard) return -1;
      const k = t / len;
      if (ao > hw) { c.use(ice); return o < 0 ? HI : LIGHT; } // 冰晶棱
      grad(c, k, [[0, deepBlue], [0.4, crystal], [0.76, ice]]);
      if (ao < 0.45 && t > 1.5) return HI; // 发光的芯
      return edge(o, hw);
    }),
    // 四角星护手，中心一颗冰蓝宝石
    (c) => space(c, 9.5, 22.5, (t, o) => {
      const at = Math.abs(t), ao = Math.abs(o);
      const across = ao / 5.4 + at / 1.5 <= 1, along = at / 3 + ao / 1.2 <= 1;
      if (!across && !along) return -1;
      const centre = Math.hypot(t, o) < 1.4;
      c.use(centre ? ice : silver);
      if (centre) return HI;
      return o < 0 || t > 0 ? HI : at + ao > 3 ? BASE : LIGHT;
    }),
    // 飘着的星屑（不描边）
    glowPiece((c) => {
      c.use(ice);
      for (const [x, y, big] of [[26.5, 21.5, true], [6.5, 9.5, true], [23.5, 27.5, false], [4.5, 15.5, false]] as const) {
        c.g.dot(x, y, HI);
        if (big) { c.g.dot(x + 1, y, LIGHT); c.g.dot(x - 1, y, LIGHT); c.g.dot(x, y + 1, LIGHT); c.g.dot(x, y - 1, LIGHT); }
      }
    }),
  ],
  fx: { glow: '#5cc0ff', sparkle: '#d8f6ff', particles: 'stars', center: [17, 15] },
};

// ---------------------------------------------------------------- 龙牙剑（传说）

const dragonFangSword: IconDef = {
  id: 'dragonFangSword', name: '龙牙剑', rarity: 'legendary',
  pieces: [
    // 暗红握柄 + 金色龙爪配重
    (c) => space(c, 9.5, 23.5, (t, o) => {
      if (t < -8.4 || t > -1.6) return -1;
      if (t < -6.2) {
        const r = Math.hypot(t + 7.3, o);
        const claw = 1.6 + 0.9 * Math.max(0, Math.cos(3 * Math.atan2(o, t + 7.3))) ** 4;
        if (r > claw) return -1;
        c.use(gold);
        return o < 0 ? HI : LIGHT;
      }
      if (Math.abs(o) > w(1.5)) return -1;
      c.use(crimson);
      return Math.floor(-t * 1.2) % 2 ? DARK : BASE;
    }),
    // 背上的火焰（先画，压在刀身下面）
    glowPiece((c) => space(c, 9.5, 23.5, (t, o) => {
      if (t < 5 || t > 19) return -1;
      // 三簇火舌，越往剑尖越小
      const base = w(3) - 2.4 * (t / 22) ** 2 + 0.4;
      const ph = (t - 5) / 4.7, frac = ph - Math.floor(ph);
      if (ph >= 3) return -1;
      const h = 4.4 * Math.sin(frac * Math.PI) ** 1.3 * (1 - Math.floor(ph) * 0.2);
      const out = o - base - (1 - frac) * 0.3;
      if (out < 0 || out > h) return -1;
      const f = out / Math.max(0.01, h);
      c.use(f > 0.5 ? hot : ember);
      return f > 0.75 ? HI : f > 0.35 ? LIGHT : BASE;
    })),
    // 弯牙刀身：暗红 → 橙 → 炽黄渐变，刃口亮线，往刃口一侧弯
    (c) => space(c, 9.5, 23.5, (t, o) => {
      const len = 22.5, half = w(3);
      if (t < 0.6 || t > len) return -1;
      const k = t / len, shift = -2.4 * k * k;
      const hw = t > len - 10 ? (half * (len - t)) / 10 : half;
      const q = o - shift;
      if (Math.abs(q) > hw) return -1;
      grad(c, k, [[0, crimson], [0.48, ember], [0.82, hot]]);
      if (Math.abs(q + hw * 0.2) < 0.4 && t > 2 && t < len - 4) return k < 0.48 ? LIGHT : HI; // 熔岩纹
      return edge(q, hw);
    }),
    // 龙翼护手：两片往后掠的翼膜 + 翼骨
    (c) => space(c, 9.5, 23.5, (t, o) => {
      const ao = Math.abs(o);
      if (ao > 6.2 || ao < 0.4) return Math.abs(t) < 1.2 && ao <= 0.4 ? (c.use(gold), LIGHT) : -1;
      const back = -(ao - 0.4) * 0.62; // 翼尖往握柄方向掠
      if (t > 1.3 + back * 0.3 || t < back - 1.6 - Math.sin(ao * 1.3) * 0.6) return -1;
      const rib = Math.abs(t - back * 0.55) < 0.45;
      c.use(rib ? gold : darkIron);
      if (rib) return o < 0 ? HI : LIGHT;
      return o < 0 ? LIGHT : BASE; // 焦黑的翼膜，和炽热的刀身拉开
    }),
    // 护手中心的龙眼
    (c) => {
      c.use(P('weapon_dragon_fang', 'gem'));
      c.g.ellipse(9.5, 23.5, 1.7, 1.7, (lam, nx) => (Math.abs(nx) < 0.25 ? OUTLINE : sphere(lam)));
    },
    // 飘起的火星（不描边）
    glowPiece((c) => {
      c.use(hot);
      for (const [x, y] of [[27.5, 12.5], [25.5, 7.5], [29.5, 18.5], [21.5, 4.5]]) c.g.dot(x, y, HI);
      c.use(ember);
      for (const [x, y] of [[28.5, 9.5], [24.5, 15.5]]) c.g.dot(x, y, LIGHT);
    }),
  ],
  fx: { glow: '#ff6a24', sparkle: '#ffc060', particles: 'embers', center: [16, 16] },
};

export const WEAPON_ICONS: IconDef[] = [trainingSword, huntingBow, greatSword, legendaryStaff, starlightBlade, dragonFangSword];
