import { LX, LZ } from '../pixel/Brush';
import { CX } from '../character/rig';
import type { Arm, Joint } from '../character/rig';
import type { DrawCtx, PartDef } from '../character/types';

/**
 * 装备数据文件共用的小工具：手臂、躯干、袖子等基础形状。
 * 全部用单位坐标 + Brush 绘制，光照统一来自左上。
 */

/** 侧向时远侧的肢体整体压暗（返回给 g.t() 的偏置） */
export function farBias(c: DrawCtx, j: Joint): number {
  return Math.abs(c.pose.sin) > 0.5 && j.near < 0 ? -0.6 : 0;
}

export function armOf(c: DrawCtx, side: 'R' | 'L'): Arm {
  return side === 'R' ? c.pose.armR : c.pose.armL;
}

/** 手臂所在图层：近侧手臂在躯干前，远侧在后 */
export const armLayer = (side: 'R' | 'L') => (c: DrawCtx) =>
  armOf(c, side).hand.front ? ('arm_front' as const) : ('arm_back' as const);

/**
 * 画一条带肘弯的手臂（肩 → 肘 → 手）。r = [肩, 肘, 腕] 处的半径；
 * upto 表示前臂画到多长（袖长）。返回末端坐标。
 */
export function drawArm(
  c: DrawCtx, side: 'R' | 'L', r: [number, number, number], upto = 1, bias = 0,
): { x: number; y: number } {
  const { g } = c;
  const a = armOf(c, side);
  const fb = farBias(c, a.hand) + bias;
  const ex = a.elbow.x + (a.hand.x - a.elbow.x) * upto;
  const ey = a.elbow.y + (a.hand.y - a.elbow.y) * upto;
  g.anchor(a.elbow.x, a.elbow.y);
  g.capsule(a.shoulder.x, a.shoulder.y, a.elbow.x, a.elbow.y, r[0], r[1], (lam) => g.t(lam, fb));
  g.capsule(a.elbow.x, a.elbow.y, ex, ey, r[1], r[1] + (r[2] - r[1]) * upto, (lam) => g.t(lam, fb));
  return { x: ex, y: ey };
}

/**
 * 躯干形状：从颈部往下 rows 个单位，肩部收圆，下摆张开。
 * shade(lam, nx, r, u, v)：lam 是把躯干当圆柱算出的光照；nx ∈ [-1,1] 横向位置；r 是离颈部的距离。
 */
export function torsoShape(
  c: DrawCtx,
  rows: number,
  opts: { flare?: number; pad?: number },
  shade: (lam: number, nx: number, r: number, u: number, v: number) => number,
): void {
  const { g, pose } = c;
  const ny = pose.neckY, flare = opts.flare ?? 1, hw0 = pose.torsoHalf + (opts.pad ?? 0);
  const shift = Math.abs(pose.torsoX(0) - pose.torsoX(rows));
  g.fill(CX - hw0 - flare - 1 - shift, ny, CX + hw0 + flare + 1 + shift, ny + rows, (u, v) => {
    const r = v - ny;
    if (r < 0 || r > rows) return -1;
    let hw = hw0;
    if (r < 2.4) hw -= (2.4 - r) * (2.4 - r) * 0.35;
    if (r > rows - 7) hw += (flare * (r - (rows - 7))) / 7;
    const nx = (u - pose.torsoX(r)) / hw;
    if (Math.abs(nx) > 1) return -1;
    return shade(nx * LX + Math.sqrt(1 - nx * nx) * LZ + 0.05, nx, r, u, v);
  });
}

/** 能看到正面时，门襟 / 领口中线所在的横坐标 */
export function frontX(c: DrawCtx): number {
  return c.pose.torsoX(5) + c.pose.torsoHalf * 0.72 * c.pose.sin;
}

/**
 * 两只袖子（各占一个部件，这样近侧手臂能压在躯干前、远侧被挡住）。
 * cuffKey 给出袖口镶边用的调色板键。
 */
export function sleeveParts(opts: { key?: string; cuffKey?: string; length?: number; r?: number }): PartDef[] {
  const make = (side: 'R' | 'L'): PartDef => ({
    layer: armLayer(side),
    draw: (c) => {
      const { g } = c;
      const a = armOf(c, side);
      const fb = farBias(c, a.hand);
      const r = opts.r ?? 2, len = opts.length ?? 0.72;
      c.pal(opts.key);
      // 肩头圆一点、宽一点
      g.anchor(a.elbow.x, a.elbow.y);
      g.ellipse(a.shoulder.x, a.shoulder.y + 0.4, r + 0.5, r + 0.3, (lam) => g.t(lam, fb));
      const end = drawArm(c, side, [r, r - 0.1, r + 0.25], len);
      // 肘部的衣褶
      g.fold(a.elbow.x - 1.5, a.elbow.y - 0.3, a.elbow.x + 1.6, a.elbow.y + 0.5);
      if (opts.cuffKey) {
        // 宽袖口
        c.pal(opts.cuffKey);
        const k = (len - 0.2) / len;
        const sx = a.elbow.x + (end.x - a.elbow.x) * k, sy = a.elbow.y + (end.y - a.elbow.y) * k;
        g.capsule(sx, sy, end.x, end.y, r + 0.15, r + 0.3, (lam, _o, t) => (t > 1 ? -1 : g.t(lam, fb + 0.1)));
      }
    },
  });
  return [make('L'), make('R')];
}
