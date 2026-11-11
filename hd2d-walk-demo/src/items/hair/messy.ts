import { pal, ramp, BASE, DARK, LIGHT, HI, OUTLINE } from '../../pixel/palette';
import type { Pt } from '../../pixel/Brush';
import type { Pose } from '../../character/rig';
import type { DrawCtx, ItemDef } from '../../character/types';

/**
 * 蓬松乱发 —— 一缕一缕画出来的。
 *
 * 把头发看成贴在一个球面上的许多发束：每束从头顶的发旋出发，沿经线往下长到某个纬度，
 * 发梢向外翘一点、朝同一侧拧一点（斜刘海）。按角色朝向把球面投影到屏幕，5 个方向自然一致：
 * 正面看到刘海和鬓角，背面看到一层层的后发。
 * 发束下面先铺一层「发根底色」（同样按球面算出发际线），保证不会露头皮。
 */

/** 头发球的半径（比头大一圈，才有蓬松的体积），单位坐标 */
const RX = 11.6, RY = 11;
/** 镜头俯视的角度：能多看到一点头顶 */
const TILT = (18 * Math.PI) / 180;
const CT = Math.cos(TILT), ST = Math.sin(TILT);
const RAD = Math.PI / 180;

interface Lock {
  /** 方位角（度）：0 = 脸的正前方，正值 = 角色左侧，±180 = 后脑勺 */
  phi: number;
  /** 起止纬度（度，0 = 头顶） */
  a0: number;
  a1: number;
  /** 发梢相对发根在方位上拧多少度 */
  twist: number;
  /** 发梢向外翘出的比例 */
  flick: number;
  /** 发根离头皮的高度（上层的短发束更高） */
  lift: number;
  /** 最大半宽（单位） */
  width: number;
  /** 0 长发束 / 1 上层短发束 / 2 呆毛 */
  tier: number;
  /** 这一束整体偏亮 / 偏暗多少：每束深浅不一，才看得出是一缕一缕的 */
  tint: number;
}

/** 固定种子的随机数：发型每次烘焙都一样 */
function rng(seed: number): () => number {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildLocks(): Lock[] {
  const r = rng(77123);
  const j = (amp: number) => (r() * 2 - 1) * amp;
  const out: Lock[] = [];
  // 刘海：盖住额头但不压住眼睛，整体朝一侧斜；中间一缕长一点
  for (const [phi, len] of [[-58, 60], [-37, 64], [-16, 71], [5, 62], [26, 65], [48, 60]]) {
    out.push({ phi: phi + j(4), a0: 5, a1: len + j(3), twist: 16 + j(9), flick: 1.05 + r() * 0.07, lift: 0, width: 2.9, tier: 0, tint: j(0.22) });
  }
  // 鬓角：垂到下颌，框住脸，发梢向外翘
  for (const phi of [72, 95, -72, -95]) {
    out.push({ phi: phi + j(5), a0: 5, a1: 116 + j(9), twist: j(12), flick: 1.16 + r() * 0.14, lift: 0, width: 3, tier: 0, tint: j(0.22) });
  }
  // 后发：垂到后颈，长短不齐，往外炸开
  for (const phi of [118, 141, 164, -173, -150, -127]) {
    out.push({ phi: phi + j(5), a0: 5, a1: 120 + j(12), twist: j(16), flick: 1.14 + r() * 0.2, lift: 0, width: 3.2, tier: 0, tint: j(0.22) });
  }
  // 上层：短而翘的发束，叠在长发束上面，把轮廓打乱成尖尖的一圈
  for (let phi = -160; phi <= 180; phi += 45) {
    out.push({ phi: phi + j(14), a0: 3, a1: 50 + j(12), twist: 12 + j(24), flick: 1.2 + r() * 0.22, lift: 0.05, width: 2.8, tier: 1, tint: j(0.25) });
  }
  // 头顶的呆毛
  out.push({ phi: 30, a0: 0, a1: 34, twist: 40, flick: 1.6, lift: 0.04, width: 0.9, tier: 2, tint: 0 });
  return out;
}

const LOCKS = buildLocks();

interface Proj extends Pt {
  near: number;
}

/** 球面坐标 → 屏幕坐标（已按朝向旋转、按俯视角压扁） */
function project(pose: Pose, cx: number, cy: number, alphaDeg: number, phiDeg: number, rho: number): Proj {
  const a = alphaDeg * RAD, p = phiDeg * RAD;
  const w = Math.cos(a), f = Math.sin(a) * Math.cos(p), s = Math.sin(a) * Math.sin(p);
  const X = s * pose.cos + f * pose.sin;
  const n = f * pose.cos - s * pose.sin;
  return { x: cx + RX * rho * X, y: cy - RY * rho * (w * CT - n * ST), near: n * CT + w * ST };
}

function lockPath(pose: Pose, cx: number, cy: number, k: Lock, i: number): Proj[] {
  const pts: Proj[] = [];
  const N = 12;
  // 走路时发梢跟着步子甩动（每束相位不同）
  const swing = pose.anim === 'walk' ? Math.sin(pose.phase * 2 + i * 1.3) : 0;
  for (let n = 0; n <= N; n++) {
    const s = n / N;
    const rho = 1 + k.lift + (k.flick - 1 + swing * 0.03) * s * s * s;
    pts.push(project(pose, cx, cy, k.a0 + (k.a1 - k.a0 + swing * 2.5) * s, k.phi + (k.twist + swing * 4) * s * s, rho));
  }
  return pts;
}

/** 发束的粗细：根部细，中段最粗，发梢收尖 */
function profile(s: number): number {
  return s < 0.55 ? 0.5 + 0.5 * (s / 0.55) : Math.max(0, 1 - Math.pow((s - 0.55) / 0.45, 1.7));
}

/** 发际线：某个方位上，发根底色盖到多低的纬度（度） */
function hairline(phiAbs: number): number {
  if (phiAbs < 50) return 50;
  if (phiAbs < 78) return 50 + ((phiAbs - 50) / 28) * 65;
  return 115 + ((phiAbs - 78) / 102) * 14;
}

function drawLocks(c: DrawCtx, back: boolean): void {
  const { g, pose } = c;
  const cx = pose.head.x - pose.sin * 0.5, cy = pose.head.y - 1.2;
  c.pal('main');
  g.grit = 0.2;
  g.anchor(cx, cy);

  if (!back) {
    // 发根底色：把像素反投影回球面，落在发际线以内的就是头发
    g.fill(cx - RX, cy - RY, cx + RX, cy + RY, (u, v) => {
      const X = (u - cx) / RX, a = (cy - v) / RY;
      const q = 1 - X * X;
      if (q <= 0 || a * a > q) return -1;
      const sq = Math.sqrt(q);
      const beta = Math.acos(Math.max(-1, Math.min(1, a / sq))) - TILT;
      const w = sq * Math.cos(beta), n = sq * Math.sin(beta);
      const s = X * pose.cos - n * pose.sin, f = X * pose.sin + n * pose.cos;
      const alpha = Math.acos(Math.max(-1, Math.min(1, w))) / RAD;
      const phi = Math.abs(Math.atan2(s, f)) / RAD;
      return alpha < hairline(phi) ? OUTLINE : -1;
    });
  }

  const items = LOCKS.map((k, i) => {
    const pts = lockPath(pose, cx, cy, k, i);
    return { k, pts, depth: pts[8].near + k.tier * 0.6 };
  })
    .filter((it) => (it.pts[8].near < -0.12) === back)
    .sort((p, q) => p.depth - q.depth);

  for (const { k, pts } of items) {
    g.ribbon(pts, (s) => k.width * profile(s), (lam, o, s, u, v) => {
      if (k.tier === 2) return o > 0.2 ? DARK : s > 0.5 ? LIGHT : BASE;
      // 整个头的受光：左上亮、右下暗
      const gl = -((u - cx) / RX) * 0.56 + ((cy - v) / RY) * 0.62;
      let sh = g.t(lam * 0.85 + gl * 0.6 - 0.3 + k.tint + (back ? -0.5 : 0));
      // 一圈高光带（天使环）：只出现在受光一侧发束的亮面上
      const alpha = k.a0 + (k.a1 - k.a0) * s;
      if (!back && alpha > 36 && alpha < 50 && gl > 0.05 && o < -0.05 && o > -0.75 && sh >= BASE) sh = HI;
      // 每束右下缘一道深色的缝，把相邻发束分开
      if (o > 0.66) sh = OUTLINE;
      else if (o > 0.36) sh = Math.max(DARK, sh - 1);
      if (s > 0.85) sh = Math.max(DARK, sh - 1); // 发梢
      return sh;
    });
  }
}

const brown = pal('hair-brown', '#1c100c', '#4a2a1a', '#7c4a2a', '#b47c42', '#ecc27a');

export const messyHair: ItemDef = {
  id: 'hair_messy',
  name: '蓬松乱发',
  slot: 'hair',
  palettes: { main: brown },
  variants: [
    { id: 'brown', name: '棕色', palettes: { main: brown } },
    { id: 'black', name: '墨黑', palettes: { main: pal('hair-black', '#08080e', '#1a1a26', '#30323e', '#52566a', '#9098b0') } },
    { id: 'blonde', name: '金色', palettes: { main: pal('hair-blonde', '#4a2c10', '#96641e', '#d4a036', '#f2cc5e', '#fff2ac') } },
    { id: 'red', name: '赤红', palettes: { main: ramp('hair-red', '#b03a26') } },
    { id: 'silver', name: '银白', palettes: { main: pal('hair-silver', '#2e3246', '#6a7088', '#a8b0c2', '#d8dee8', '#ffffff') } },
    { id: 'teal', name: '青绿', palettes: { main: ramp('hair-teal', '#2a8e84') } },
  ],
  parts: [
    { layer: 'hair_back', draw: (c) => drawLocks(c, true) },
    { layer: 'hair', draw: (c) => drawLocks(c, false) },
  ],
};
