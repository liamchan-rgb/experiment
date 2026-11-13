import { BASE, DARK, HI, LIGHT } from '../../pixel/palette';
import type { DrawCtx, PartDef } from '../../character/types';

/**
 * 武器共用的画法：
 *   along()  沿武器方向作画，长度自动乘手部锚点的 reach（指向镜头时变短）
 *   trailPart()  挥砍拖影（关键帧标了 trail 的那几帧）
 *   sparkle()  蓄力 / 释放时的星形闪光
 *   makeSword()  参数化的剑：短剑、重剑、星辉刃、龙牙剑都由它画
 */

export interface Frame {
  x: number;
  y: number;
  dx: number;
  dy: number;
  /** 缩短比例 */
  k: number;
}

export function frameOf(c: DrawCtx): Frame | undefined {
  const h = c.hand;
  if (!h) return undefined;
  return { x: h.x, y: h.y + 0.6, dx: Math.cos(h.angle), dy: Math.sin(h.angle), k: h.reach };
}

/** 沿武器方向画一段：t0..t1 是武器自身的长度坐标，fn 收到的 t 也是未缩短的值 */
export function along(c: DrawCtx, f: Frame, t0: number, t1: number, half: number, fn: (t: number, o: number) => number): void {
  c.g.axis(f.x, f.y, f.dx, f.dy, t0 * f.k, t1 * f.k, half, (t, o) => fn(t / f.k, o));
}

/** 武器上某一点的坐标 */
export function at(f: Frame, t: number, o = 0): { x: number; y: number } {
  return { x: f.x + f.dx * t * f.k - f.dy * o, y: f.y + f.dy * t * f.k + f.dx * o };
}

/** 四角星闪光（不描边的特效层用） */
export function sparkle(c: DrawCtx, x: number, y: number, r: number): void {
  const { g } = c;
  g.fill(x - r, y - r, x + r, y + r, (u, v) => {
    const ax = Math.abs(u - x), ay = Math.abs(v - y);
    const arm = Math.min(ax, ay);
    if (ax + ay > r || arm > Math.max(0.5, r * 0.18)) return ax * ax + ay * ay < (r * 0.32) ** 2 ? LIGHT : -1;
    return ax + ay < r * 0.45 ? HI : LIGHT;
  });
}

/**
 * 挥砍拖影：一段从上一帧武器方向扫到当前方向的弧，靠近当前武器的一端最亮。
 * r0..r1 是弧的内外半径（武器自身长度坐标）。
 */
export function trailPart(r0: number, r1: number, key = 'fx'): PartDef {
  return {
    layer: 'weapon_front',
    outline: false,
    draw: (c) => {
      const h = c.hand;
      const f = frameOf(c);
      if (!h || !f || h.trailFrom === undefined) return;
      const a1 = h.angle;
      let sweep = a1 - h.trailFrom;
      while (sweep > Math.PI) sweep -= 2 * Math.PI;
      while (sweep < -Math.PI) sweep += 2 * Math.PI;
      if (Math.abs(sweep) < 0.2) return;
      const R0 = r0 * f.k, R1 = r1 * f.k;
      c.pal(key);
      c.g.grit = 0;
      c.g.dither = false;
      c.g.fill(f.x - R1, f.y - R1, f.x + R1, f.y + R1, (u, v) => {
        const ex = u - f.x, ey = v - f.y;
        const d = Math.hypot(ex, ey);
        if (d < R0 || d > R1) return -1;
        let a = Math.atan2(ey, ex) - h.trailFrom!;
        while (a > Math.PI) a -= 2 * Math.PI;
        while (a < -Math.PI) a += 2 * Math.PI;
        const k = a / sweep; // 0 = 上一帧，1 = 当前武器
        if (k < 0 || k > 0.92) return -1;
        // 弧越靠前越宽：前端占满半径，尾端只剩外缘一条
        const outer = (d - R0) / (R1 - R0);
        if (outer < 1 - k * 1.1) return -1;
        return k > 0.6 && outer > 0.55 ? HI : k > 0.3 ? LIGHT : BASE;
      });
      c.g.dither = true;
    },
  };
}

/** 蓄力 / 释放的闪光：画在武器某一点（剑尖、宝珠）上 */
export function fxPart(point: (f: Frame) => { x: number; y: number }, key = 'fx', size = 1): PartDef {
  return {
    layer: 'weapon_front',
    outline: false,
    draw: (c) => {
      const f = frameOf(c);
      const fx = c.pose.fx;
      if (!f || (fx !== 'glow' && fx !== 'burst')) return;
      const p = point(f);
      c.pal(key);
      c.g.grit = 0;
      if (fx === 'glow') {
        sparkle(c, p.x, p.y, 3.2 * size);
        c.g.dot(p.x - 4 * size, p.y + 2.5 * size, LIGHT);
        c.g.dot(p.x + 3.5 * size, p.y - 3.2 * size, HI);
      } else {
        sparkle(c, p.x, p.y, 6 * size);
        for (const [ox, oy] of [[-5.5, -3.5], [5, 3], [3, -5.5], [-4, 4.5]]) c.g.dot(p.x + ox * size, p.y + oy * size, HI);
      }
    },
  };
}

export interface SwordOpts {
  /** 剑身从哪里开始、多长（单位，握柄在 0 附近） */
  from: number;
  to: number;
  /** 剑身半宽 */
  half: number;
  /** 剑尖收窄的长度 */
  tip: number;
  /** 剑身弯曲：剑尖往刃口一侧偏多少（龙牙剑） */
  curve?: number;
  /** 剑身中线的血槽 / 发光芯 */
  core?: 'fuller' | 'glow';
  /** 握柄长度（往后） */
  grip: number;
  /** 护手半宽、厚度，两端往剑尖翘多少 */
  guard: [number, number, number];
  /** 配重球半径 */
  pommel: number;
}

/**
 * 画一把剑。调色板键：blade 剑身、hilt 护手与配重、grip 握柄、gem（可选，护手中间的宝石）。
 */
export function drawSword(c: DrawCtx, o: SwordOpts, withGem = false): void {
  const f = frameOf(c);
  if (!f) return;
  const len = o.to;
  c.pal('blade');
  along(c, f, o.from, o.to, o.half + Math.abs(o.curve ?? 0) + 0.4, (t, off) => {
    const s = (t - o.from) / (len - o.from);
    const shift = (o.curve ?? 0) * s * s;
    const w = t < len - o.tip ? o.half : (o.half * (len - t)) / o.tip;
    const q = off - shift;
    if (Math.abs(q) > w) return -1;
    if (o.core === 'glow' && Math.abs(q) < w * 0.35 && t > o.from + 1) return HI;
    if (o.core === 'fuller' && Math.abs(q) < 0.35 && t > o.from + 1.5 && t < len - o.tip - 1) return DARK;
    if (q < -w * 0.15) return t > o.from + (len - o.from) * 0.3 && t < len - o.tip ? HI : LIGHT;
    return q > w * 0.5 ? DARK : BASE;
  });
  c.pal('grip');
  along(c, f, -o.grip, o.from - 0.6, 0.8, (t, off) => (off > 0.3 ? DARK : Math.floor(t * 1.2 + 10) % 2 ? BASE : LIGHT));
  c.pal('hilt');
  const [gh, gt, bend] = o.guard;
  along(c, f, o.from - 1.6, o.from + 0.4, gh, (t, off) => {
    const b = bend * Math.abs(off) / gh;
    if (t < o.from - 1.4 + b - gt / 2 || t > o.from - 1.4 + b + gt / 2) return -1;
    return off < -gh * 0.5 ? HI : off > gh * 0.55 ? DARK : LIGHT;
  });
  const pm = at(f, -o.grip - o.pommel * 0.6);
  c.g.ellipse(pm.x, pm.y, o.pommel, o.pommel, (lam) => (lam > 0.4 ? HI : lam > -0.2 ? BASE : DARK));
  if (withGem) {
    c.pal('gem');
    const gp = at(f, o.from - 1.2);
    c.g.ellipse(gp.x, gp.y, 1.1, 1.1, (lam) => (lam > 0.3 ? HI : LIGHT));
  }
}
