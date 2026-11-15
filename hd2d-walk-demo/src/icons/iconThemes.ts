/**
 * 稀有物品的「主题特效」：不再只是沿轮廓套一圈光，而是强调物品自己的重点部位——
 *   传奇权杖：宝石向外辐射旋转的光芒      龙牙剑：刃口窜起火苗、余烬上升
 *   星辉刃：一道冷光沿剑身流过、冰晶星屑     重剑：护手红宝石脉动、刃口一闪
 *   符文甲：符文依次点亮、符文光点上浮      星辉甲：胸口星章放出十字星芒
 *   龙纹甲：护肩尖角冒火、甲片间余烬         行动戒指：宝石闪烁、一点光绕戒圈
 *   星辉 / 龙纹饰品：星屑环绕 / 火焰环绕    复活石：心跳一样的脉动、灵光上升
 * 关键部位按调色板找（图标就是用这些调色板画的），找不到就退回图标中心。
 */
import type { PixelLayer } from '../pixel/PixelLayer';

export type RGB = [number, number, number];
export interface ThemeApi {
  /** 循环里的位置 0..1 */
  t: number;
  base: PixelLayer;
  /** 叠加光（只加亮） */
  add(x: number, y: number, rgb: RGB, k: number): void;
  glowAt(x: number, y: number, r: number, rgb: RGB, k: number): void;
  /** 改一个不透明像素 */
  setPx(x: number, y: number, rgb: RGB): void;
  /** 用这些调色板画的像素 */
  find(...ids: string[]): [number, number][];
  rand(i: number, k?: number): number;
}

const WHITE: RGB = [255, 255, 255];
const hex = (h: string): RGB => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const TAU = Math.PI * 2;
const centroid = (pts: [number, number][], fallback: [number, number]): [number, number] => {
  if (!pts.length) return fallback;
  const sx = pts.reduce((a, p) => a + p[0], 0), sy = pts.reduce((a, p) => a + p[1], 0);
  return [sx / pts.length + 0.5, sy / pts.length + 0.5];
};
/** 光线：从 (x, y) 沿角度 a 画一条渐暗的光，长度 len */
function ray(api: ThemeApi, x: number, y: number, a: number, len: number, rgb: RGB, k: number): void {
  for (let d = 2; d < len; d += 0.5) api.add(x + Math.cos(a) * d, y + Math.sin(a) * d, rgb, k * (1 - d / len) * 0.9);
}
/** 四角星 */
function star(api: ThemeApi, x: number, y: number, arm: number, tip: RGB): void {
  for (let d = 1; d <= arm; d++) {
    const c = d === arm && arm > 1 ? tip : WHITE;
    api.setPx(x + d, y, c); api.setPx(x - d, y, c); api.setPx(x, y + d, c); api.setPx(x, y - d, c);
  }
  api.setPx(x, y, WHITE);
}
/** 一朵像素火苗：底宽顶尖，从热白到橙红 */
function flame(api: ThemeApi, x: number, y: number, h: number, sway: number): void {
  const hot = hex('#fff2a0'), mid = hex('#ffa030'), cool = hex('#e0401c');
  for (let k = 0; k < h; k++) {
    const q = k / h, w = Math.max(0, Math.round((1 - q) * 1.4));
    const cx = x + Math.sin(q * 3 + sway) * q * 1.2;
    for (let o = -w; o <= w; o++) {
      const c = q < 0.3 && Math.abs(o) < 1 ? hot : q < 0.65 ? mid : cool;
      api.setPx(cx + o, y - k, c);
    }
  }
  api.glowAt(x + 0.5, y - h * 0.4, 3 + h * 0.4, hex('#ff7a24'), 0.35);
}
/** 上升的粒子（余烬 / 光点），phase 0..1 */
function rising(api: ThemeApi, n: number, x0: number, x1: number, y0: number, rise: number, rgb: RGB, core: RGB, k = 1): void {
  for (let i = 0; i < n; i++) {
    const p = (api.t + i / n) % 1;
    const x = x0 + api.rand(i, 7) * (x1 - x0) + Math.sin(p * 7 + i) * 1.2, y = y0 - p * rise;
    const a = Math.sin(p * Math.PI);
    if (a > 0.3) api.setPx(x, y, p < 0.45 ? core : rgb);
    api.glowAt(x + 0.5, y + 0.5, 2.6, rgb, 0.45 * a * k);
  }
}

export const THEMES: Partial<Record<string, (api: ThemeApi) => void>> = {
  legendaryStaff(api) {
    const [gx, gy] = centroid(api.find('scepter-gem'), [20, 11]);
    const pink = hex('#ff5ab4'), pale = hex('#ffd0f0');
    const pulse = 0.75 + 0.25 * Math.sin(api.t * TAU * 2);
    // 8 道光芒慢慢转，长短交替
    for (let i = 0; i < 8; i++) {
      const a = api.t * TAU * 0.25 + (i * TAU) / 8;
      ray(api, gx, gy, a, (i % 2 ? 9 : 14) * pulse, i % 2 ? pink : pale, 1.1);
    }
    api.glowAt(gx, gy, 7, pink, 0.8 * pulse);
    // 宝石中心一闪
    if (Math.sin(api.t * TAU * 2) > 0.6) star(api, Math.floor(gx), Math.floor(gy), 2, pale);
    // 光点被吸向宝石
    for (let i = 0; i < 5; i++) {
      const p = (api.t * 2 + i / 5) % 1, a = api.rand(i, 3) * TAU, d = 12 * (1 - p);
      const x = gx + Math.cos(a) * d, y = gy + Math.sin(a) * d;
      api.setPx(x, y, p > 0.6 ? WHITE : pale);
      api.glowAt(x, y, 2, pink, 0.4);
    }
  },
  dragonFangSword(api) {
    const blade = api.find('w-ember', 'w-hot', 'w-crimson');
    // 刃口上方（上面没有刃的像素）站着一排跳动的火苗
    const tops = blade.filter(([x, y]) => !blade.some(([u, v]) => u === x && v === y - 1));
    tops.sort((a, b) => a[0] - b[0]);
    const n = Math.min(6, tops.length);
    for (let i = 0; i < n; i++) {
      const [x, y] = tops[Math.floor(((i + 0.5) / n) * tops.length)];
      const flick = Math.sin(api.t * TAU * 3 + i * 1.9);
      flame(api, x, y - 1, Math.round(2.5 + 2 * (0.5 + 0.5 * flick) + (i % 2)), api.t * TAU * 2 + i);
    }
    for (const [x, y] of blade) api.add(x, y, hex('#ff8a30'), 0.12 + 0.08 * Math.sin(api.t * TAU * 2 + x * 0.4));
    rising(api, 7, 4, 28, 26, 26, hex('#ff7a24'), hex('#fff0a0'));
  },
  starlightBlade(api) {
    const blade = api.find('starlight-crystal', 'w-ice');
    // 一道冷光从剑柄流到剑尖（沿 x + y 方向的位置排序）
    const span = blade.map(([x, y]) => x - y);
    const lo = Math.min(...span), hi = Math.max(...span);
    const pos = lo + ((api.t * 1.5) % 1) * (hi - lo + 6);
    blade.forEach(([x, y], i) => {
      const d = Math.abs(span[i] - pos);
      if (d < 0.8) api.setPx(x, y, WHITE);
      else if (d < 2.5) api.add(x, y, hex('#a0e8ff'), 0.6 * (1 - d / 2.5));
    });
    // 冰晶星屑绕着剑身闪烁
    for (let i = 0; i < 5; i++) {
      const life = (api.t * 2 + i / 5) % 1;
      if (life > 0.45) continue;
      const [x, y] = blade[Math.floor(api.rand(i, Math.floor(api.t * 2 + i / 5) + 11) * blade.length)] ?? [16, 16];
      const k = Math.sin((life / 0.45) * Math.PI);
      star(api, x + (i % 2 ? 3 : -3), y + (i % 3) - 1, Math.round(1 + k * 1.5), hex('#bfeeff'));
      api.glowAt(x + 0.5, y + 0.5, 4, hex('#5cc0ff'), 0.4 * k);
    }
  },
  greatSword(api) {
    const [gx, gy] = centroid(api.find('w-ruby'), [14, 18]);
    const beat = Math.max(0, Math.sin(api.t * TAU));
    api.glowAt(gx, gy, 5 + beat * 2, hex('#ff4a3a'), 0.3 + 0.45 * beat);
    if (beat > 0.85) star(api, Math.floor(gx), Math.floor(gy), 1, hex('#ffd0c8'));
  },
  runeArmor(api) {
    const runes = api.find('rune-glow');
    // 符文从下往上依次点亮
    runes.forEach(([x, y]) => {
      const wave = Math.max(0, Math.sin(api.t * TAU - y * 0.35));
      if (wave > 0.8) api.setPx(x, y, hex('#e8fff8'));
      api.glowAt(x + 0.5, y + 0.5, 3, hex('#3ee6d8'), 0.18 * wave);
    });
    rising(api, 4, 8, 24, 26, 18, hex('#3ee6d8'), hex('#c8fff4'), 0.8);
  },
  starlightArmor(api) {
    const [sx, sy] = centroid(api.find('star-gem'), [16, 15]);
    const k = 0.6 + 0.4 * Math.sin(api.t * TAU * 2);
    for (const a of [0, Math.PI / 2, Math.PI, Math.PI * 1.5]) ray(api, sx, sy, a, 15 * k, hex('#3aa0f0'), 1.4);
    for (const a of [Math.PI / 4, (3 * Math.PI) / 4, (5 * Math.PI) / 4, (7 * Math.PI) / 4]) ray(api, sx, sy, a, 8 * k, hex('#2a7ae0'), 1.2);
    api.glowAt(sx, sy, 5, hex('#7cc4ff'), 0.5 * k);
    star(api, Math.floor(sx), Math.floor(sy), k > 0.8 ? 3 : 2, hex('#5cbcf0'));
    rising(api, 4, 4, 28, 8, -14, hex('#7cc4ff'), WHITE, 0.6);
  },
  dragonArmor(api) {
    // 护肩尖角（金色的最上面几个像素）各冒一朵火
    const gold = api.find('dragon-gold');
    const peaks = gold.filter(([x, y]) => y < 12 && !gold.some(([u, v]) => Math.abs(u - x) <= 1 && v === y - 1));
    const picked: [number, number][] = [];
    for (const p of peaks.sort((a, b) => a[1] - b[1])) if (picked.every((q) => Math.abs(q[0] - p[0]) > 4)) picked.push(p);
    picked.slice(0, 4).forEach(([x, y], i) => flame(api, x, y - 1, Math.round(2 + 1.5 * (0.5 + 0.5 * Math.sin(api.t * TAU * 3 + i * 2))), i));
    for (const [x, y] of api.find('dragon-armor')) if ((x + y + Math.floor(api.t * 8)) % 9 === 0) api.add(x, y, hex('#ff7a40'), 0.35);
    rising(api, 6, 6, 26, 28, 24, hex('#ff6a28'), hex('#ffe08a'));
  },
  actionRing(api) {
    const [gx, gy] = centroid(api.find('icon-amethyst'), [16, 12]);
    const k = Math.max(0, Math.sin(api.t * TAU * 2));
    api.glowAt(gx, gy, 5, hex('#c88cff'), 0.25 + 0.4 * k);
    if (k > 0.7) star(api, Math.floor(gx), Math.floor(gy), 2, hex('#f2e0ff'));
    const a = api.t * TAU, x = 16 + Math.cos(a) * 8, y = 20 + Math.sin(a) * 4;
    api.setPx(x, y, WHITE); api.glowAt(x, y, 3, hex('#e0c0ff'), 0.5);
  },
  starlightCharm(api) {
    for (let i = 0; i < 6; i++) {
      const a = api.t * TAU * 0.5 + (i * TAU) / 6, x = 16 + Math.cos(a) * 11, y = 18 + Math.sin(a) * 7;
      const tw = 0.5 + 0.5 * Math.sin(api.t * TAU * 3 + i);
      if (tw > 0.6) star(api, Math.round(x), Math.round(y), tw > 0.9 ? 2 : 1, hex('#bfeeff'));
      api.glowAt(x, y, 3, hex('#7cd0ff'), 0.35 * tw);
    }
  },
  dragonCharm(api) {
    for (let i = 0; i < 5; i++) {
      const a = api.t * TAU * 0.5 + (i * TAU) / 5, x = 16 + Math.cos(a) * 11, y = 21 + Math.sin(a) * 6;
      if (Math.sin(a) < 0.2) flame(api, Math.round(x), Math.round(y), 3, i + api.t * 6);
    }
    rising(api, 4, 8, 24, 26, 16, hex('#ff6a28'), hex('#ffe08a'), 0.7);
  },
  revivalStone(api) {
    // 心跳：两下一停
    const q = api.t % 1, beat = Math.max(0, Math.sin(Math.min(1, q / 0.18) * Math.PI)) + 0.6 * Math.max(0, Math.sin(Math.min(1, Math.max(0, q - 0.22) / 0.18) * Math.PI));
    const [cx, cy] = centroid(api.find('icon-revival'), [16, 17]);
    api.glowAt(cx, cy, 8 + beat * 3, hex('#9cf0d8'), 0.2 + 0.4 * beat);
    for (const [x, y] of api.find('icon-revival')) api.add(x, y, hex('#c0fff0'), 0.25 * beat);
    rising(api, 5, 8, 24, 24, 20, hex('#9cf0d8'), WHITE, 0.7);
  },
};
