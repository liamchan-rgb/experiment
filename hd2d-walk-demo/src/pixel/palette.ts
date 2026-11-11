/**
 * 调色板：每个部件手写 5 阶色，相邻两阶之间再自动插一个过渡色，实际可用 9 阶。
 * 明暗阶可以写半阶（1.5 = 暗部和主色之间），tone() 量化时会用到。
 *   0 = 描边（主色的暗色，不用纯黑）
 *   1 = 暗部
 *   2 = 主色
 *   3 = 亮部
 *   4 = 高光
 * 形状数据里只写这些索引，换色只需要换 Palette。
 */
export interface Palette {
  id: string;
  colors: string[];
}

export const OUTLINE = 0;
export const DARK = 1;
export const BASE = 2;
export const LIGHT = 3;
export const HI = 4;
/** 受光侧（左、上）的浅描边：由描边色和暗部色混合得到，不需要在调色板里手写 */
export const SOFT_OUTLINE = 5;

/** 明暗阶 → 图层里存的编号（1..9 是九阶色，11 是浅描边；0 留给空像素） */
export function shadeCode(shade: number): number {
  return Math.round(shade * 2) + 1;
}

export function pal(id: string, ...colors: string[]): Palette {
  if (colors.length !== 5) throw new Error(`palette ${id} needs 5 colors`);
  return { id, colors };
}

function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.replace(/(.)/g, '$1$1') : h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function rgbToHsl(r: number, g: number, b: number): [number, number, number] {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h: number;
  if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
  else if (max === g) h = (b - r) / d + 2;
  else h = (r - g) / d + 4;
  return [h * 60, s, l];
}

function hslToHex(h: number, s: number, l: number): string {
  h = ((h % 360) + 360) % 360;
  s = Math.min(1, Math.max(0, s));
  l = Math.min(1, Math.max(0, l));
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  const [r, g, b] =
    h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] :
    h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  const to = (v: number) => Math.round((v + m) * 255).toString(16).padStart(2, '0');
  return `#${to(r)}${to(g)}${to(b)}`;
}

/** 把色相朝 target 方向转 amount 度（走最短路径）。 */
function hueToward(h: number, target: number, amount: number): number {
  const diff = ((target - h + 540) % 360) - 180;
  return h + Math.sign(diff) * Math.min(Math.abs(diff), amount);
}

/**
 * 由一个主色自动生成 5 阶色带：暗部偏冷、亮部偏暖（像素画常用的 hue shifting）。
 * 方便做换色（发色、布料色）。
 */
export function ramp(id: string, base: string): Palette {
  const [h, s, l] = rgbToHsl(...hexToRgb(base));
  return {
    id,
    colors: [
      hslToHex(hueToward(h, 255, 22), s * 0.95 + 0.05, l * 0.36),
      hslToHex(hueToward(h, 255, 12), s * 1.02, l * 0.68),
      hslToHex(h, s, l),
      hslToHex(hueToward(h, 50, 8), s * 0.95, l + (1 - l) * 0.3),
      hslToHex(hueToward(h, 50, 14), s * 0.85, l + (1 - l) * 0.58),
    ],
  };
}

const rgbCache = new WeakMap<Palette, Uint8Array>();

/**
 * 调色板解析成 RGB 字节表（缓存）：下标 = shade × 2。
 * 0,2,4,6,8 是手写的五阶，1,3,5,7 是自动插出的过渡色，10 是浅描边。
 */
export function paletteRGB(p: Palette): Uint8Array {
  let out = rgbCache.get(p);
  if (!out) {
    out = new Uint8Array(11 * 3);
    const base = p.colors.map(hexToRgb);
    for (let i = 0; i < 9; i++) {
      const a = base[i >> 1], b = base[Math.min(4, (i + 1) >> 1)];
      for (let k = 0; k < 3; k++) out[i * 3 + k] = Math.round((a[k] + b[k]) / 2);
    }
    for (let k = 0; k < 3; k++) out[30 + k] = Math.round(base[0][k] * 0.55 + base[1][k] * 0.45);
    rgbCache.set(p, out);
  }
  return out;
}
