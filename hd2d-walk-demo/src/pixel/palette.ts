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

/** 相邻两个手写色之间细分成几档：4 → 0, 0.25, 0.5, 0.75, 1 … 共 17 阶过渡 */
export const SUB = 4;

/** 明暗阶 → 图层里存的编号（1..17 是 17 阶色，21 是浅描边；0 留给空像素） */
export function shadeCode(shade: number): number {
  return Math.round(shade * SUB) + 1;
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

// ---- OKLab：感知均匀的色彩空间，插值出来的过渡色亮度均匀、色相不发灰 ----
const toLin = (c: number) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const toSrgb = (c: number) => (c <= 0.0031308 ? c * 12.92 : 1.055 * c ** (1 / 2.4) - 0.055);

function rgbToOklab([r8, g8, b8]: [number, number, number]): [number, number, number] {
  const r = toLin(r8 / 255), g = toLin(g8 / 255), b = toLin(b8 / 255);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}

function oklabToRgb([L, A, B]: [number, number, number]): [number, number, number] {
  const l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3;
  const m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3;
  const s = (L - 0.0894841775 * A - 1.291485548 * B) ** 3;
  const r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
  const g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
  const b = -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s;
  const to8 = (v: number) => Math.max(0, Math.min(255, Math.round(toSrgb(Math.max(0, Math.min(1, v))) * 255)));
  return [to8(r), to8(g), to8(b)];
}

/**
 * 调色板解析成 RGB 字节表（缓存）：下标 = shade × SUB。
 * 手写的五阶落在 0, 4, 8, 12, 16；中间的过渡色在 OKLab 里插值，
 * 两端颜色的色相差（暗部偏冷、亮部偏暖）会被平滑地带过去。下标 20 是浅描边。
 */
export function paletteRGB(p: Palette): Uint8Array {
  let out = rgbCache.get(p);
  if (!out) {
    const n = SOFT_OUTLINE * SUB + 1;
    out = new Uint8Array(n * 3);
    const base = p.colors.map((c) => rgbToOklab(hexToRgb(c)));
    for (let i = 0; i <= 4 * SUB; i++) {
      const k = Math.min(3, Math.floor(i / SUB)), f = i / SUB - k;
      const a = base[k], b = base[k + 1];
      out.set(oklabToRgb([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]), i * 3);
    }
    const soft = oklabToRgb(base[0].map((v, k) => v * 0.55 + base[1][k] * 0.45) as [number, number, number]);
    out.set(soft, SOFT_OUTLINE * SUB * 3);
    rgbCache.set(p, out);
  }
  return out;
}
