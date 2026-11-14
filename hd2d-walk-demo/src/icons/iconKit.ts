import { PixelLayer } from '../pixel/PixelLayer';
import { Brush, LX, LY } from '../pixel/Brush';
import { paletteRGB, type Palette, HI, LIGHT } from '../pixel/palette';
import { INNER_LINE } from '../character/paperdoll';

/**
 * 物品图标：32 × 32 像素，和人物用同一套画笔、描边、内描边、接触阴影和调色板（直接取自对应装备），
 * 所以背包里的图标和人物身上穿的是同一件东西、同一种画风。
 *
 * 稀有度决定特效（参考 pixelfx 的做法，MIT：https://github.com/patch-gg/pixelfx）：
 *   不透明的像素画 + 一层叠加的「光」（只加亮，不遮挡），光在像素格上计算，放大后仍是一格一格的。
 *   common    静态，无特效
 *   rare      一层淡淡的光 + 偶尔一道斜光扫过 + 两颗星芒
 *   epic      再加一圈呼吸的彩色光晕
 *   legendary 光晕更亮、星芒更多，并带专属粒子（星屑 / 余烬 / 符文光点）
 */

export const ICON = 32;

export type Rarity = 'common' | 'rare' | 'epic' | 'legendary';

export interface IconCtx {
  g: Brush;
  L: PixelLayer;
  use(p: Palette): void;
}

/** 一个部件：单独画、单独描边，再叠到图标上（叠的地方自动变成有颜色的内描边） */
export type Piece = (c: IconCtx) => void;

export interface IconFx {
  /** 光晕颜色 */
  glow?: string;
  /** 光晕中心（默认画面中心）和半径 */
  center?: [number, number];
  radius?: number;
  /** 专属粒子 */
  particles?: 'stars' | 'embers' | 'motes';
  /** 粒子 / 星芒的颜色（默认取光晕色） */
  sparkle?: string;
}

export interface IconDef {
  /** 桌游物品 id */
  id: string;
  name: string;
  rarity: Rarity;
  pieces: Piece[];
  fx?: IconFx;
}

// ---------------------------------------------------------------- 绘制

/** 静态图标：逐个部件画到临时层 → 描边 → 投接触阴影 → 叠上去 */
export function drawIcon(def: IconDef): PixelLayer {
  const out = new PixelLayer(ICON, ICON);
  const tmp = new PixelLayer(ICON, ICON);
  const g = new Brush(tmp, 1);
  g.vgrad = 0.18;
  const taps: [number, number, number][] = [[1, 1, 0.8], [1, 0, 0.45], [0, 1, 0.55], [2, 1, 0.3], [1, 2, 0.35]];
  for (const piece of def.pieces) {
    tmp.clear();
    g.clip = false;
    g.grit = 0.08;
    g.dither = true;
    g.anchor(0, 0);
    piece({ g, L: tmp, use: (p) => tmp.use(p) });
    tmp.bounce(0.4);
    tmp.outline();
    out.castShadow(tmp, taps);
    tmp.drawOnto(out, 0, 0, INNER_LINE);
  }
  return out;
}

// ---------------------------------------------------------------- 常用形状（单位 = 像素）

/** 沿线段画一条（剑身、杖身）：fn(t, o)，t 从 a 到 b 的距离，o 横向偏移（朝右下为正） */
export function bar(c: IconCtx, ax: number, ay: number, bx: number, by: number, half: number, fn: (t: number, o: number, len: number) => number): void {
  const len = Math.hypot(bx - ax, by - ay);
  const dx = (bx - ax) / len, dy = (by - ay) / len;
  c.g.axis(ax, ay, dx, dy, 0, len, half, (t, o) => fn(t, o, len));
}

/** 金属：受光一侧亮、背光一侧暗，中间一道高光 */
export function metal(o: number, half: number): number {
  const k = o / half;
  if (k < -0.45) return HI;
  if (k < -0.05) return LIGHT;
  if (k < 0.5) return 2;
  return 1;
}

/** 球面光照 → 明暗阶（不抖动，适合宝石、玻璃） */
export function sphere(lam: number): number {
  return lam > 0.85 ? HI : lam > 0.45 ? LIGHT : lam > -0.05 ? 2 : lam > -0.5 ? 1 : 0.5;
}

/** 刻面宝石：上半两块受光面、下半三块背光面，台面一个白点 */
export function gem(c: IconCtx, x: number, y: number, r: number): void {
  c.g.fill(x - r - 1, y - r - 1, x + r + 1, y + r + 1, (u, v) => {
    const dx = u - x, dy = v - y;
    if (Math.abs(dx) + Math.abs(dy) * 1.1 > r) return -1;
    if (dy < -r * 0.15) return dx < -0.3 ? HI : dx < r * 0.3 ? LIGHT : 2;
    return dx < -r * 0.2 ? 2 : dx < r * 0.25 ? 1 : 0.5;
  });
}

/** 光照：一个 2D 法线（指向外）对左上光源的亮度 */
export function lit(nx: number, ny: number, z = 0.6): number {
  const l = Math.hypot(nx, ny, z) || 1;
  return (nx * LX + ny * LY + z * 0.55) / l;
}

// ---------------------------------------------------------------- 特效

/** 简单可复现的随机数 */
function rand(i: number, seed: number, k = 0): number {
  let n = (Math.imul(i + 1, 374761393) + Math.imul(seed + 7, 668265263) + Math.imul(k + 3, 2147483647)) | 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
}

function hexRGB(hex: string): [number, number, number] {
  const n = parseInt(hex.replace('#', ''), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export const FRAMES = 24;
export const FPS = 12;

const RARITY: Record<Rarity, { halo: number; glints: number; shine: boolean; particles: boolean }> = {
  common: { halo: 0, glints: 0, shine: false, particles: false },
  rare: { halo: 0.24, glints: 2, shine: true, particles: false },
  epic: { halo: 0.5, glints: 3, shine: true, particles: false },
  legendary: { halo: 0.85, glints: 4, shine: true, particles: true },
};

/**
 * 一帧图标的 RGBA（32 × 32）。t ∈ [0, 1) 是循环里的位置。
 * 颜色层：静态图标 + 斜光扫过时被提亮的像素 + 星芒 / 粒子像素；
 * 光层：光晕、星芒和粒子自带的光，叠加上去（落在透明处时变成半透明的彩色光）。
 */
export function iconFrame(def: IconDef, base: PixelLayer, t: number): Uint8ClampedArray {
  const W = ICON, H = ICON;
  const spec = RARITY[def.rarity];
  const fx = def.fx ?? {};
  const glow = hexRGB(fx.glow ?? '#ffe6a0');
  const spark = hexRGB(fx.sparkle ?? fx.glow ?? '#fff4c8');
  const [cx, cy] = fx.center ?? [16, 16];
  const out = new Uint8ClampedArray(W * H * 4);
  base.toRGBA(out);
  const light = new Float32Array(W * H * 3);
  const add = (x: number, y: number, rgb: [number, number, number], k: number) => {
    x = Math.floor(x); y = Math.floor(y);
    if (x < 0 || y < 0 || x >= W || y >= H || k <= 0) return;
    const i = (y * W + x) * 3;
    light[i] += (rgb[0] / 255) * k; light[i + 1] += (rgb[1] / 255) * k; light[i + 2] += (rgb[2] / 255) * k;
  };
  const glowAt = (x: number, y: number, r: number, rgb: [number, number, number], k: number) => {
    for (let py = Math.floor(y - r); py <= y + r; py++) for (let px = Math.floor(x - r); px <= x + r; px++) {
      const d = Math.hypot(px + 0.5 - x, py + 0.5 - y) / r;
      if (d < 1) add(px, py, rgb, (1 - d) * (1 - d) * k);
    }
  };
  const setPx = (x: number, y: number, rgb: [number, number, number]) => {
    x = Math.floor(x); y = Math.floor(y);
    if (x < 0 || y < 0 || x >= W || y >= H) return;
    const o = (y * W + x) * 4;
    out[o] = rgb[0]; out[o + 1] = rgb[1]; out[o + 2] = rgb[2]; out[o + 3] = 255;
  };
  const WHITE: [number, number, number] = [255, 255, 255];
  const body = (x: number, y: number) => base.idx[y * W + x] > 0;

  // 呼吸的光晕：外圈一层淡的，贴着物品一层亮的（只在物品周围，不是一个大圆片）
  if (spec.halo > 0) {
    const pulse = 0.72 + 0.28 * Math.sin(t * Math.PI * 2);
    const R = fx.radius ?? 15;
    glowAt(cx, cy, R, glow, spec.halo * 0.55 * pulse);
    // 沿着轮廓的一圈光：离物品像素越近越亮
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (body(x, y)) continue;
      let near = 9;
      for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) {
        const xx = x + dx, yy = y + dy;
        if (xx >= 0 && yy >= 0 && xx < W && yy < H && body(xx, yy)) near = Math.min(near, Math.hypot(dx, dy));
      }
      if (near < 3.5) add(x, y, glow, spec.halo * pulse * (1 - near / 3.5) * 1.1);
    }
  }

  // 一道斜光从左上扫到右下（循环的前 40%），只亮物品本身的像素
  if (spec.shine) {
    const q = t / 0.4;
    if (q < 1) {
      const pos = -8 + q * (W + H + 16) * 0.62;
      const tables = base.palettes.map(paletteRGB);
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        const v = base.idx[y * W + x];
        if (!v || v <= 3 || v >= 21) continue; // 描边（深 / 浅）和最暗的阶不亮
        const band = Math.abs(x * 0.62 + y * 0.38 - pos);
        if (band < 0.7) setPx(x, y, WHITE);
        else if (band < 1.8) {
          const pid = base.pid[y * W + x], tb = tables[pid];
          const code = Math.min(17, v + 6), c = (code - 1) * 3;
          setPx(x, y, [tb[c], tb[c + 1], tb[c + 2]]);
        }
      }
    }
  }

  // 星芒：在物品轮廓附近轮流一闪一灭（四角星，白心）
  const outline: [number, number][] = [];
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
    if (!body(x, y)) continue;
    if (!body(x - 1, y) || !body(x + 1, y) || !body(x, y - 1) || !body(x, y + 1)) outline.push([x, y]);
  }
  const seed = def.id.length * 31 + def.id.charCodeAt(0);
  for (let i = 0; i < spec.glints && outline.length; i++) {
    const life = 0.22, start = (i + 0.35) / spec.glints;
    const age = (((t - start) % 1) + 1) % 1;
    if (age > life) continue;
    const k = Math.sin((age / life) * Math.PI);
    const [ox, oy] = outline[Math.floor(rand(i, seed, Math.floor((t - start + 2) / 1)) * outline.length)];
    const arm = Math.round(1 + 2 * k);
    for (let d = 1; d <= arm; d++) {
      const c: [number, number, number] = d === arm && arm > 1 ? spark : WHITE;
      setPx(ox + d, oy, c); setPx(ox - d, oy, c); setPx(ox, oy + d, c); setPx(ox, oy - d, c);
    }
    setPx(ox, oy, WHITE);
    glowAt(ox + 0.5, oy + 0.5, 3 + arm * 2, spark, 0.55 * k);
  }

  // 专属粒子
  if (spec.particles && fx.particles) {
    const n = fx.particles === 'embers' ? 7 : 6;
    for (let i = 0; i < n; i++) {
      const phase = (t + i / n) % 1;
      if (fx.particles === 'embers') {
        // 余烬：从下方升起、左右摇摆、越升越暗
        const x = 6 + rand(i, seed, 1) * 20 + Math.sin(phase * 6 + i) * 1.5;
        const y = 30 - phase * 26;
        const k = Math.sin(phase * Math.PI);
        const hot: [number, number, number] = phase < 0.5 ? [255, 230, 140] : spark;
        if (k > 0.25) setPx(x, y, hot);
        glowAt(x + 0.5, y + 0.5, 3, spark, 0.5 * k);
      } else if (fx.particles === 'stars') {
        // 星屑：绕着物品慢慢飘落、闪烁
        const a = rand(i, seed, 2) * Math.PI * 2 + phase * 1.2;
        const d = 10 + rand(i, seed, 3) * 4;
        const x = cx + Math.cos(a) * d, y = cy + Math.sin(a) * d * 0.9 + phase * 3;
        const k = Math.sin(phase * Math.PI);
        if (k > 0.5) { setPx(x, y, WHITE); if (k > 0.85) { setPx(x + 1, y, spark); setPx(x - 1, y, spark); setPx(x, y + 1, spark); setPx(x, y - 1, spark); } }
        glowAt(x + 0.5, y + 0.5, 2.5, spark, 0.45 * k);
      } else {
        // 符文光点：贴着物品慢慢上浮
        const x = cx - 9 + rand(i, seed, 4) * 18, y = cy + 8 - phase * 16;
        const k = Math.sin(phase * Math.PI);
        if (k > 0.4) setPx(x, y, spark);
        glowAt(x + 0.5, y + 0.5, 2.5, spark, 0.5 * k);
      }
    }
  }

  // 把光叠上去：不透明像素直接加亮；透明处变成半透明的彩色光
  for (let i = 0; i < W * H; i++) {
    const lr = light[i * 3], lg = light[i * 3 + 1], lb = light[i * 3 + 2];
    if (lr + lg + lb <= 0.004) continue;
    const o = i * 4;
    if (out[o + 3]) {
      out[o] += lr * 255 * 0.9; out[o + 1] += lg * 255 * 0.9; out[o + 2] += lb * 255 * 0.9;
    } else {
      const a = Math.min(1, Math.max(lr, lg, lb));
      // 光的透明度量化成几档，放大后是一圈圈的像素光，不是平滑的渐变
      const aq = Math.round(a * 6) / 6;
      if (aq <= 0) continue;
      out[o] = Math.min(255, (lr / a) * 255); out[o + 1] = Math.min(255, (lg / a) * 255); out[o + 2] = Math.min(255, (lb / a) * 255);
      out[o + 3] = aq * 255;
    }
  }
  return out;
}
