/**
 * 护盾（自己写的 pixelfx 风格特效，替代 holy/divine-shield 那种布满经纬线、偏大的球）：
 *   - 贴合 Q 版小人的椭圆罩子（默认 17 × 23 像素，站在地上），底下一圈地面光印
 *   - 表面是很淡的六边形蜂窝，只在边缘（菲涅尔）和扫过的光带里看得见，中间几乎透明，不挡脸
 *   - 1 像素的清晰轮廓，左上受光处最亮，外面一圈柔光；左上角一道气泡高光
 *   - 生成：从地面往上长出来，切口一道亮线，长满时整个闪一下
 *   - 受击（hitAt / hitAngle）：从击中点沿表面扩散一圈涟漪，附近的蜂窝格子亮起来
 *   - 破碎（breakAt）：轮廓碎成一片片往外飞、旋转、变暗，中心一闪
 * 选项：palette（暗 → 亮，至少 7 色）、rx / ry、cy（中心离地高度）、form（生成用时，0 = 已经在）、hitAt、hitAngle、breakAt、seed
 */
// @ts-expect-error vendored plain JS
import { fit, clamp, TAU, WHITE, sparkle } from '../../vendor/pixelfx/src/core/index.js';

type Painter = {
  each(x0: number, y0: number, x1: number, y1: number, fn: (x: number, y: number, sx: number, sy: number) => void): void;
  blendPx(sx: number, sy: number, c: number, a: number): void;
  blend(x: number, y: number, c: number, a: number): void;
  px(x: number, y: number, c: number): void;
  dot(x: number, y: number, c: number, a?: number): void;
  glow(x: number, y: number, r: number, c: number, k?: number): void;
  glowRing(x: number, y: number, R: number, r: number, c: number, k?: number): void;
  light(x: number, y: number, c: number, k?: number): void;
  line(x0: number, y0: number, x1: number, y1: number, c: number, a?: number): void;
};
type Opts = { palette: string[]; rx: number; ry: number; cy: number; form: number; hitAt: number; hitAngle: number; breakAt: number; seed: number };

export const meta = {
  name: 'Aegis',
  desc: 'A fitted bubble shield: faint honeycomb at the rim, crisp lit edge, ground seal; forms from the ground, ripples when hit, shatters when broken.',
  size: [80, 80],
  origin: [40, 70],
  duration: 30,
  loop: false,
  fps: 30,
  options: {
    palette: ['#081830', '#123a6a', '#1e6ab0', '#3ca0e6', '#80d0ff', '#c8eeff', '#ffffff'],
    rx: 17, ry: 23, cy: -21, form: 0.42, hitAt: -1, hitAngle: -0.4, breakAt: -1, seed: 3,
  },
};

const ease = (x: number) => 1 - (1 - clamp(x)) ** 3;
/** 平顶六边形蜂窝：到最近格子中心的距离（归一到格子半径） */
function hexEdge(x: number, y: number, s: number): number {
  const q = (x * 2) / 3 / s, r = (-x / 3 + (Math.sqrt(3) / 3) * y) / s;
  let rx = Math.round(q), ry = Math.round(r), rz = Math.round(-q - r);
  const dx = Math.abs(rx - q), dy = Math.abs(ry - r), dz = Math.abs(rz + q + r);
  if (dx > dy && dx > dz) rx = -ry - rz; else if (dy > dz) ry = -rx - rz;
  const cx = s * 1.5 * rx, cy = s * Math.sqrt(3) * (ry + rx / 2);
  const ex = Math.abs(x - cx), ey = Math.abs(y - cy);
  // 六边形的「半径」度量：越接近 1 越在格子边上
  return Math.max(ex / s, (ex * 0.5 + ey * Math.sqrt(3) / 2) / s);
}

/** 一帧护盾。back = 后半个罩子（在人物后面），front = 前半个（在人物前面，更透明） */
function shell(p: Painter, t: number, o: Opts, back: boolean): void {
  const C = fit(o.palette, 7) as number[];
  const { rx, ry, cy } = o;
  const form = o.form > 0 ? ease(t / o.form) : 1;
  const broken = o.breakAt >= 0 && t >= o.breakAt;
  if (broken) return;
  // 生成：从地面往上长，切口高度（屏幕 y）
  const cut = -(form * (ry * 2 + 4)) + 2;
  const flash = o.form > 0 ? Math.max(0, 1 - Math.abs(t - o.form) / 0.12) : 0;
  const sheen = -1.6 + 3.2 * (((t * 0.42) % 1.6) / 1.6);
  const hitR = o.hitAt >= 0 && t >= o.hitAt ? (t - o.hitAt) * 55 : -1;
  const hx = Math.cos(o.hitAngle) * rx, hy = cy + Math.sin(o.hitAngle) * ry;
  const ripple0 = (x: number, y: number) => (hitR >= 0 ? Math.max(0, 1 - Math.abs(Math.hypot(x - hx, y - hy) - hitR) / 2) * Math.max(0, 1 - hitR / 30) : 0);
  p.each(-rx - 2, cy - ry - 2, rx + 2, 2, (x, y, sx, sy) => {
    const nx = x / rx, ny = (y - cy) / ry;
    const d = Math.hypot(nx, ny);
    if (d > 1 || y < cut || y > 0.5) return;
    const fres = d ** 5;
    const hex = hexEdge(x + 0.5, y + 0.5 - cy, 3.1);
    const onLine = hex > 0.86;
    const band = Math.max(0, 1 - Math.abs((nx - ny) * 0.7 - sheen) / 0.25);
    let ripple = 0;
    if (hitR >= 0) {
      const dist = Math.hypot(x - hx, y - hy);
      ripple = Math.max(0, 1 - Math.abs(dist - hitR) / 1.6) * Math.max(0, 1 - hitR / 30);
    }
    const lit = back ? 0.35 : 1;
    let a = (back ? 0.05 : 0.02) + 0.22 * fres;
    if (onLine) a += (0.03 + 0.6 * fres + 0.45 * band + 0.6 * ripple) * lit;
    a += 0.12 * band * lit * fres + flash * 0.4 * fres + 0.12 * ripple;
    // 生成的切口：一道亮线
    const atCut = form < 1 && y - cut < 1.2;
    if (atCut) { p.blendPx(sx, sy, WHITE, 0.9); return; }
    if (a < 0.03) return;
    const c = ripple > 0.5 ? C[6] : onLine ? C[5] : C[4];
    p.blendPx(sx, sy, c, Math.min(0.7, a));
  });
  if (back) return;
  // 轮廓：1 像素，左上最亮（轮廓是球的边缘，人物在里面不会被它挡住，所以只画在前面）
  const n = Math.ceil((rx + ry) * 3.2);
  for (let j = 0; j < n; j++) {
    const g = (j / n) * TAU;
    const x = Math.cos(g) * rx, y = cy + Math.sin(g) * ry;
    if (y < cut || y > 0.5) continue;
    const litk = Math.cos(g + 2.36);
    const c = litk > 0.7 || flash > 0.3 ? WHITE : litk > -0.2 ? C[6] : C[5];
    // 实线：受光的一侧不透明，背光的一侧半透明（blend 不抖动，线条是连续的）
    if (litk > 0.2 || ripple0(x, y) > 0.3) p.px(x, y, ripple0(x, y) > 0.3 ? WHITE : c);
    else p.blend(x, y, c, 0.5 + 0.5 * Math.max(0, litk + 0.2));
    p.blend(Math.cos(g) * (rx - 1), cy + Math.sin(g) * (ry - 1), C[4], 0.2 + 0.25 * Math.max(0, litk));
  }
  {
    p.glowRing(0, cy, (rx + ry) / 2, 4, C[4], 0.16 + flash * 0.3);
    // 气泡高光：左上一道弧 + 一个点
    if (form > 0.95) {
      for (let g = 3.6; g < 4.15; g += 0.05) p.px(Math.cos(g) * rx * 0.72, cy + Math.sin(g) * ry * 0.72, g > 3.75 && g < 4.0 ? WHITE : C[6]);
      p.px(Math.cos(3.42) * rx * 0.6, cy + Math.sin(3.42) * ry * 0.6, WHITE);
      // 两颗沿边缘追逐的星芒
      for (const off of [0, Math.PI]) {
        const g = t * 1.6 + off + 0.8;
        sparkle(p, Math.cos(g) * rx, cy + Math.sin(g) * ry, 1 + Math.round(1 + Math.sin(t * 5 + off)), WHITE, C[6], 0.35);
      }
    }
    if (hitR >= 0 && hitR < 12) {
      sparkle(p, hx, hy, hitR < 4 ? 4 : 2, WHITE, C[6], 0.4);
      p.glow(hx, hy, 7, C[5], 0.35 * (1 - hitR / 12));
    }
  }
}

/** 地面光印：一圈椭圆 + 一圈小符点，生成时从中间往外展开 */
function seal(p: Painter, t: number, o: Opts, back: boolean): void {
  const C = fit(o.palette, 7) as number[];
  const grow = o.form > 0 ? ease(t / (o.form * 0.6)) : 1;
  const R = o.rx * 1.05 * grow;
  if (o.breakAt >= 0 && t > o.breakAt + 0.3) return;
  for (let j = 0; j < 64; j++) {
    const g = (j / 64) * TAU;
    if ((Math.sin(g) < 0) !== back) continue;
    const x = Math.cos(g) * R, y = Math.sin(g) * R * 0.26;
    if (j % 2) continue;
    p.blend(x, y, j % 8 === (Math.floor(t * 6) * 2) % 8 ? WHITE : C[5], 0.75);
  }
  if (back) p.glow(0, 0, R * 0.9, C[4], 0.12);
}

/** 破碎：沿轮廓切成 14 片往外飞 */
function shatter(p: Painter, t: number, o: Opts): void {
  if (o.breakAt < 0 || t < o.breakAt) return;
  const C = fit(o.palette, 7) as number[];
  const r = t - o.breakAt;
  if (r > 1) return;
  const { rx, ry, cy } = o;
  if (r < 0.1) p.glow(0, cy, 16, C[6], 0.55 * (1 - r / 0.1));
  for (let k = 0; k < 14; k++) {
    const g = (k / 14) * TAU + 0.2;
    const sp = 34 + ((k * 37) % 23);
    const x = Math.cos(g) * (rx + sp * r), y = cy + Math.sin(g) * (ry + sp * r) + 60 * r * r;
    const len = 4 * (1 - r), rot = g + r * 9 * (k % 2 ? 1 : -1);
    const a = 1 - r;
    p.line(x - Math.cos(rot) * len, y - Math.sin(rot) * len, x + Math.cos(rot) * len, y + Math.sin(rot) * len, r < 0.3 ? WHITE : C[5], a);
    p.light(x, y, C[5], 0.4 * a);
  }
}

export function drawBack(p: Painter, t: number, o: Opts): void {
  seal(p, t, o, true);
  shell(p, t, o, true);
}

export function draw(p: Painter, t: number, o: Opts): void {
  shell(p, t, o, false);
  seal(p, t, o, false);
  shatter(p, t, o);
}
