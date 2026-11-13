import { pal, ramp, BASE, DARK, LIGHT, HI, OUTLINE } from '../../pixel/palette';
import type { Pt } from '../../pixel/Brush';
import type { Pose } from '../../character/rig';
import type { DrawCtx, ItemDef } from '../../character/types';

/**
 * 蓬松短发 —— 少量宽发束，读成一整块。
 *
 * 把头发看成贴在一个球面上的许多发束：每束从头顶的发旋出发，沿经线往下长到某个纬度，
 * 发梢向外翘一点、朝同一侧拧一点（斜刘海）。按角色朝向把球面投影到屏幕，5 个方向自然一致：
 * 正面看到刘海和鬓角，背面看到一层层的后发。
 * 发束下面先铺一层「发根底色」（同样按球面算出发际线），保证不会露头皮。
 */

/** 头发球的半径（比头大一圈，才有蓬松的体积），单位坐标 */
/** 发型整体相对头的大小：头放大时一起放大，发束宽度也跟着变 */
const HS = 11.6 / 10.4;
const RX = 11.6 * HS, RY = 11 * HS;
/** 前后方向的半径：比左右窄，侧面看头才是圆的而不是横着的长条 */
const RZ = 10.2 * HS;
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
  // 低像素密度下发型越简单越好看：少而宽的几大缕，靠整体受光分出大块亮面和暗面，
  // 不做一缕一缕深浅不同的细碎层次（那些在 40 像素的头上只会变成噪点）。

  // 刘海：4 缕宽发束盖住额头，整体朝一侧斜；中间一缕略长
  for (const [phi, len] of [[-48, 64], [-17, 73], [14, 65], [44, 62]]) {
    out.push({ phi: phi + j(3), a0: 5, a1: len + j(2), twist: 16, flick: 1.06, lift: 0, width: 3.3, tier: 0, tint: 0 });
  }
  // 鬓角：左右各一缕，贴在耳前，只垂到脸颊上半
  for (const phi of [100, -100]) {
    out.push({ phi, a0: 5, a1: 96, twist: 0, flick: 1.08, lift: 0, width: 3.4, tier: 0, tint: 0 });
  }
  // 后发：4 缕宽发束垂到后颈，发梢只微微外翘
  for (const phi of [128, 160, -168, -136]) {
    out.push({ phi: phi + j(4), a0: 5, a1: 126 + j(6), twist: j(8), flick: 1.06, lift: 0, width: 3.8, tier: 0, tint: 0 });
  }
  // 头顶三撮短翘发：只为了让轮廓不是一个光滑的圆，明暗和整体一致，不另做层次
  for (const phi of [-150, -40, 75]) {
    out.push({ phi, a0: 3, a1: 40, twist: 18, flick: 1.18, lift: 0.04, width: 2.6, tier: 1, tint: 0 });
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
  // 先按椭球压扁前后方向，再旋转到朝向
  const sx = s, fz = (f * RZ) / RX;
  const X = sx * pose.cos + fz * pose.sin;
  const n = fz * pose.cos - sx * pose.sin;
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
  if (phiAbs < 70) return 50;
  if (phiAbs < 100) return 50 + ((phiAbs - 70) / 30) * 45; // 耳前：发根只盖到脸颊上半
  return 115 + ((phiAbs - 78) / 102) * 14;
}

function drawLocks(c: DrawCtx, back: boolean): void {
  const { g, pose } = c;
  const cx = pose.head.x + pose.sin * 0.2, cy = pose.head.y - 1.2;
  c.pal('main');
  g.grit = 0.1;
  g.anchor(cx, cy);
  // 整个头的受光：左上亮、右下暗。头发的明暗主要由它决定，大块面
  const headLight = (u: number, v: number) => -((u - cx) / RX) * 0.62 + ((cy - v) / RY) * 0.7;
  // 天使环：画面上一道向两侧下弯的弧形光带，只在受光的左上那一侧出现
  const ring = (u: number, v: number) => {
    const x = (u - cx) / RX, y = (cy - v) / RY - 0.16 * x * x;
    return y > 0.3 && y < 0.46 && headLight(u, v) > 0.12;
  };

  if (!back) {
    // 发根底色：把像素反投影回球面，落在发际线以内的就是头发
    const rxView = Math.hypot(RX * pose.cos, RZ * pose.sin);
    g.fill(cx - RX, cy - RY, cx + RX, cy + RY, (u, v) => {
      const X = (u - cx) / rxView, a = (cy - v) / RY;
      const q = 1 - X * X;
      if (q <= 0 || a * a > q) return -1;
      const sq = Math.sqrt(q);
      const beta = Math.acos(Math.max(-1, Math.min(1, a / sq))) - TILT;
      const w = sq * Math.cos(beta), n = sq * Math.sin(beta);
      const s = X * pose.cos - n * pose.sin, f = X * pose.sin + n * pose.cos;
      const alpha = Math.acos(Math.max(-1, Math.min(1, w))) / RAD;
      const phi = Math.abs(Math.atan2(s, f)) / RAD;
      // 底色也按整体受光着色（偏暗），发束之间的缝隙不会是一个个黑点
      if (alpha >= hairline(phi)) return -1;
      return ring(u, v) ? LIGHT : g.t(headLight(u, v) * 0.9 - 0.55);
    });
  }

  const items = LOCKS.map((k, i) => {
    const pts = lockPath(pose, cx, cy, k, i);
    return { k, pts, depth: pts[8].near + k.tier * 0.6 };
  })
    .filter((it) => (it.pts[8].near < -0.12) === back)
    .sort((p, q) => p.depth - q.depth);

  for (const { k, pts } of items) {
    g.ribbon(pts, (s) => k.width * HS * profile(s), (lam, o, s, u, v) => {
      if (k.tier === 2) return o > 0.2 ? DARK : s > 0.5 ? LIGHT : BASE;
      const gl = headLight(u, v);
      // 以整体受光为主，发束自身的圆柱光照只占一小部分
      let sh = g.t(gl * 0.95 + lam * 0.3 - 0.22 + (back ? -0.45 : 0));
      // 一道干净的高光带（天使环）
      if (ring(u, v) && o < 0.6) sh = gl > 0.42 ? HI : Math.max(sh + 1, LIGHT + 0.5);
      // 发束之间只用暗一档的缝分开，不用深描边
      if (o > 0.72 && s > 0.25) sh = Math.max(OUTLINE + 0.5, sh - 1.5);
      if (s > 0.9) sh = Math.max(DARK, sh - 0.5); // 发梢略暗
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
