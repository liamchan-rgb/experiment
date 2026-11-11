import { PixelLayer } from './PixelLayer';
import { HI, OUTLINE } from './palette';

/**
 * Brush：在「单位坐标」里画连续形状，再落到像素格上。
 *
 * 角色的所有形状都用单位坐标描述（64×96 单位的画布），实际像素 = 单位 × 倍率 S。
 * 每个像素取中心点求值：形状内外、表面法线 → 左上方光照 → 量化到调色板的明暗阶。
 * 所以提高 S 就是真正多出细节，而不是把像素块放大。
 */

/** 光源方向（指向光源，左上偏前），已归一化 */
export const LX = -0.56, LY = -0.62, LZ = 0.55;

/** 特殊「颜色」：对已有像素做相对操作 */
export const DARKEN = -10;
export const LIGHTEN = -11;
export const ERASE = -12;

/**
 * 把光照强度（约 -1..1）量化成明暗阶，精确到半阶（共 9 档过渡）。
 * 最暗的一档直接用描边色：深阴影和轮廓线融成一片，形体更有分量。
 */
const TONE_X = [-1.03, -0.41, 0.21, 0.71, 1.09];
export function tone(lam: number, bias = 0): number {
  const v = lam + bias;
  if (v <= TONE_X[0]) return OUTLINE;
  for (let i = 1; i < 5; i++) {
    if (v < TONE_X[i]) return Math.round((i - 1 + (v - TONE_X[i - 1]) / (TONE_X[i] - TONE_X[i - 1])) * 2) / 2;
  }
  return HI;
}

/** 整数格点上的哈希噪声，0..1 */
function hash2(x: number, y: number): number {
  let n = (Math.imul(x, 374761393) + Math.imul(y, 668265263)) | 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
}

export interface Pt {
  x: number;
  y: number;
}

export class Brush {
  /** 为 true 时只在本层已有像素上作画（给衣褶、纽扣等细节用，不会画出轮廓外） */
  clip = false;
  /**
   * 粗粝度：量化前给光照加多大的噪声（0 = 光滑的色带）。
   * 噪声让色块边缘参差、色面里夹杂零星的邻阶像素，像手点出来的而不是算出来的。
   */
  grit = 0.16;

  private ax = 0;
  private ay = 0;
  private ci = 0;
  private cj = 0;

  constructor(readonly L: PixelLayer, readonly S: number) {}

  /** 噪声纹理的原点（单位坐标）。设在会动的关节上，纹理就跟着肢体走，不会在身上「游」。 */
  anchor(u: number, v: number): void {
    this.ax = Math.round(u * this.S);
    this.ay = Math.round(v * this.S);
  }

  /** 当前像素的噪声，-1..1：一半是几个像素大的斑块，一半是单像素的颗粒 */
  private noise(): number {
    const x = this.ci - this.ax, y = this.cj - this.ay;
    const cell = Math.max(2, Math.round(2.6 * this.S));
    const gx = Math.floor(x / cell), gy = Math.floor(y / cell);
    const fx = x / cell - gx, fy = y / cell - gy;
    const a = hash2(gx, gy), b = hash2(gx + 1, gy), c = hash2(gx, gy + 1), d = hash2(gx + 1, gy + 1);
    const blotch = a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
    return (blotch * 2 - 1) * 0.85 + (hash2(x + 31, y - 17) * 2 - 1) * 0.22;
  }

  /** 带粗粝感的量化：在 fill / ellipse / capsule 等的回调里用它代替 tone() */
  t(lam: number, bias = 0): number {
    return tone(lam + this.noise() * this.grit, bias);
  }

  private put(i: number, j: number, s: number): void {
    const L = this.L;
    if (i < 0 || j < 0 || i >= L.w || j >= L.h) return;
    const has = L.idx[j * L.w + i] > 0;
    if (s === DARKEN) { if (has) L.reshade(i, j, -1); return; }
    if (s === LIGHTEN) { if (has) L.reshade(i, j, 1); return; }
    if (s === ERASE) { L.px(i, j, -1); return; }
    if (s < 0) return;
    if (this.clip && !has) return;
    L.px(i, j, s);
  }

  /** 对单位坐标包围盒内的每个像素中心求值。fn 返回明暗阶，<0 跳过。 */
  fill(x0: number, y0: number, x1: number, y1: number, fn: (u: number, v: number) => number): void {
    const { S, L } = this;
    const i0 = Math.max(0, Math.floor(x0 * S)), i1 = Math.min(L.w - 1, Math.ceil(x1 * S));
    const j0 = Math.max(0, Math.floor(y0 * S)), j1 = Math.min(L.h - 1, Math.ceil(y1 * S));
    for (let j = j0; j <= j1; j++) {
      for (let i = i0; i <= i1; i++) {
        this.ci = i;
        this.cj = j;
        const s = fn((i + 0.5) / S, (j + 0.5) / S);
        if (s !== -1) this.put(i, j, s);
      }
    }
  }

  /** 椭球：shade(lam, nx, ny, u, v)，lam 是球面光照。传数字则平涂。 */
  ellipse(
    cx: number, cy: number, rx: number, ry: number,
    shade: number | ((lam: number, nx: number, ny: number, u: number, v: number) => number),
  ): void {
    this.fill(cx - rx, cy - ry, cx + rx, cy + ry, (u, v) => {
      const nx = (u - cx) / rx, ny = (v - cy) / ry;
      const d = nx * nx + ny * ny;
      if (d > 1) return -1;
      if (typeof shade === 'number') return shade;
      return shade(nx * LX + ny * LY + Math.sqrt(1 - d) * LZ, nx, ny, u, v);
    });
  }

  /**
   * 胶囊体（可变粗细的圆柱，两端圆头）：肢体、带子都用它。
   * shade(lam, o, t, u, v)：lam 是圆柱面光照；o ∈ [-1,1] 是横向位置（朝右下为正）；t 是沿轴位置 0..1。
   */
  capsule(
    ax: number, ay: number, bx: number, by: number, ra: number, rb: number,
    shade: number | ((lam: number, o: number, t: number, u: number, v: number) => number),
  ): void {
    const dx = bx - ax, dy = by - ay;
    const len2 = dx * dx + dy * dy || 1e-6, len = Math.sqrt(len2);
    let px = -dy / len, py = dx / len;
    if (px + py < 0) { px = -px; py = -py; }
    const pl = px * LX + py * LY;
    const r = Math.max(ra, rb);
    this.fill(Math.min(ax, bx) - r, Math.min(ay, by) - r, Math.max(ax, bx) + r, Math.max(ay, by) + r, (u, v) => {
      const t = ((u - ax) * dx + (v - ay) * dy) / len2;
      const tc = Math.max(0, Math.min(1, t));
      const rr = ra + (rb - ra) * tc;
      const ex = u - (ax + dx * tc), ey = v - (ay + dy * tc);
      if (ex * ex + ey * ey > rr * rr) return -1;
      if (typeof shade === 'number') return shade;
      const o = Math.max(-1, Math.min(1, (ex * px + ey * py) / rr));
      return shade(o * pl + Math.sqrt(1 - o * o) * LZ, o, t, u, v);
    });
  }

  /**
   * 沿折线的带子，宽度可随位置变化（发束、飘带）。
   * halfW(s) 给出 s ∈ [0,1] 处的半宽；shade(lam, o, s, u, v) 同 capsule。
   */
  ribbon(
    pts: Pt[],
    halfW: (s: number) => number,
    shade: (lam: number, o: number, s: number, u: number, v: number) => number,
  ): void {
    const n = pts.length - 1;
    if (n < 1) return;
    const cum = [0];
    for (let i = 0; i < n; i++) cum.push(cum[i] + Math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y));
    const total = cum[n] || 1e-6;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, wmax = 0;
    for (let i = 0; i <= n; i++) {
      x0 = Math.min(x0, pts[i].x); x1 = Math.max(x1, pts[i].x);
      y0 = Math.min(y0, pts[i].y); y1 = Math.max(y1, pts[i].y);
      wmax = Math.max(wmax, halfW(cum[i] / total));
    }
    wmax = Math.max(wmax, halfW(0.5)) * 1.15;
    this.fill(x0 - wmax, y0 - wmax, x1 + wmax, y1 + wmax, (u, v) => {
      let best = Infinity, bs = 0, bo = 0, bl = 0;
      for (let i = 0; i < n; i++) {
        const a = pts[i], b = pts[i + 1];
        const dx = b.x - a.x, dy = b.y - a.y;
        const l2 = dx * dx + dy * dy || 1e-6;
        const tc = Math.max(0, Math.min(1, ((u - a.x) * dx + (v - a.y) * dy) / l2));
        const ex = u - (a.x + dx * tc), ey = v - (a.y + dy * tc);
        const d = ex * ex + ey * ey;
        if (d >= best) continue;
        best = d;
        const l = Math.sqrt(l2);
        let px = -dy / l, py = dx / l;
        if (px + py < 0) { px = -px; py = -py; }
        bs = (cum[i] + l * tc) / total;
        bo = ex * px + ey * py;
        bl = px * LX + py * LY;
      }
      const hw = halfW(bs);
      if (hw <= 0 || best > hw * hw) return -1;
      const o = Math.max(-1, Math.min(1, bo / hw));
      return shade(o * bl + Math.sqrt(1 - o * o) * LZ, o, bs, u, v);
    });
  }

  /**
   * 沿某个方向的局部坐标系作画（武器）：fn(t, o)，t 沿方向的距离，o 垂直偏移（朝右下为正）。
   */
  axis(
    x: number, y: number, dx: number, dy: number,
    t0: number, t1: number, half: number,
    fn: (t: number, o: number) => number,
  ): void {
    let px = -dy, py = dx;
    if (px + py < 0) { px = -px; py = -py; }
    const xs = [x + dx * t0, x + dx * t1], ys = [y + dy * t0, y + dy * t1];
    this.fill(
      Math.min(...xs) - half, Math.min(...ys) - half, Math.max(...xs) + half, Math.max(...ys) + half,
      (u, v) => {
        const t = (u - x) * dx + (v - y) * dy;
        const o = (u - x) * px + (v - y) * py;
        return t < t0 || t > t1 || Math.abs(o) > half ? -1 : fn(t, o);
      },
    );
  }

  /** 三角形 */
  tri(a: Pt, b: Pt, c: Pt, shade: number | ((u: number, v: number) => number)): void {
    const sign = (p: Pt, q: Pt, u: number, v: number) => (u - q.x) * (p.y - q.y) - (p.x - q.x) * (v - q.y);
    this.fill(Math.min(a.x, b.x, c.x), Math.min(a.y, b.y, c.y), Math.max(a.x, b.x, c.x), Math.max(a.y, b.y, c.y), (u, v) => {
      const d1 = sign(a, b, u, v), d2 = sign(b, c, u, v), d3 = sign(c, a, u, v);
      const neg = d1 < 0 || d2 < 0 || d3 < 0, pos = d1 > 0 || d2 > 0 || d3 > 0;
      if (neg && pos) return -1;
      return typeof shade === 'number' ? shade : shade(u, v);
    });
  }

  /** 轴对齐矩形（单位坐标） */
  rect(x: number, y: number, w: number, h: number, shade: number | ((u: number, v: number) => number)): void {
    this.fill(x, y, x + w, y + h, (u, v) =>
      u < x || u > x + w || v < y || v > y + h ? -1 : typeof shade === 'number' ? shade : shade(u, v));
  }

  /** 一像素宽的线（Bresenham，不会断） */
  line(ax: number, ay: number, bx: number, by: number, shade: number): void {
    const S = this.S;
    let x0 = Math.floor(ax * S), y0 = Math.floor(ay * S);
    const x1 = Math.floor(bx * S), y1 = Math.floor(by * S);
    const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx + dy;
    for (;;) {
      this.put(x0, y0, shade);
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 >= dy) { err += dy; x0 += sx; }
      if (e2 <= dx) { err += dx; y0 += sy; }
    }
  }

  /**
   * 贴一个小图案（眼睛、搭扣这类必须逐格控制的细节）。
   * 每个字符是一格：'.' 为空，'0'-'4' 为明暗阶；一格 = cell×cell 个像素，默认随倍率取整。
   */
  cells(rows: string[], u: number, v: number, cell = Math.max(1, Math.round(this.S))): void {
    const i0 = Math.floor(u * this.S), j0 = Math.floor(v * this.S);
    rows.forEach((row, r) => {
      for (let k = 0; k < row.length; k++) {
        const ch = row.charCodeAt(k) - 48;
        if (ch < 0 || ch > 4) continue;
        for (let b = 0; b < cell; b++) for (let a = 0; a < cell; a++) this.put(i0 + k * cell + a, j0 + r * cell + b, ch);
      }
    });
  }

  /** 同 cells，但位置直接给像素坐标（需要左右严格对称时用） */
  cellsPx(rows: string[], i0: number, j0: number, cell = Math.max(1, Math.round(this.S))): void {
    this.cells(rows, (i0 + 0.01) / this.S, (j0 + 0.01) / this.S, cell);
  }

  /** 一个像素 */
  dot(u: number, v: number, shade: number): void {
    this.put(Math.floor(u * this.S), Math.floor(v * this.S), shade);
  }

  /**
   * 一道衣褶：一条暗线，受光侧贴一条亮线。只画在已有像素上。
   */
  fold(ax: number, ay: number, bx: number, by: number, highlight = true): void {
    const was = this.clip;
    this.clip = true;
    this.line(ax, ay, bx, by, DARKEN);
    if (highlight) {
      const o = 1 / this.S;
      this.line(ax - o, ay - o, bx - o, by - o, LIGHTEN);
    }
    this.clip = was;
  }
}
