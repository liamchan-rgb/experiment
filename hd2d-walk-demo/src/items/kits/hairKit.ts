import { pal, ramp, type Palette, BASE, DARK, LIGHT, HI, OUTLINE } from '../../pixel/palette';
import type { Pt } from '../../pixel/Brush';
import { HEAD_RX, type Pose } from '../../character/rig';
import type { DrawCtx, ItemDef, ItemVariant } from '../../character/types';

/**
 * 发型引擎：把一份发型数据（JSON）变成装备。
 *
 * 头发看成贴在椭球上的少量宽发束：每束从头顶出发，沿经线往下长到某个纬度，
 * 发梢略向外翘、朝一侧拧（斜刘海）。按角色朝向投影到画面，5 个方向自然一致。
 * 发束下面先铺一层「发根底色」（按发际线反投影算出），保证不会露头皮。
 * 明暗以整颗头的受光为主，加一道弧形高光带，发束之间只用暗一档的缝分开。
 *
 * 数据格式见 Sources/Resources/CharacterParts/hair/*.json 和 docs/CHARACTER_SPRITES.md 第 6.3 节。
 */

export interface LockData {
  /** 方位角（度）：0 = 脸正前方，正值 = 角色左侧，±180 = 后脑 */
  phi: number;
  /** 起止纬度（度，0 = 头顶），a0 默认 5 */
  a0?: number;
  a1: number;
  /** 发梢在方位上拧多少度，默认 0 */
  twist?: number;
  /** 发梢外翘比例，默认 1.06 */
  flick?: number;
  /** 发根离头皮的高度，默认 0 */
  lift?: number;
  /** 最大半宽（单位，按头的大小再缩放） */
  width: number;
  /** 0 发束 / 1 头顶短翘发 / 2 呆毛，默认 0 */
  tier?: number;
}

export interface PaletteVariantData {
  id: string;
  name: string;
  /** 手写 5 色；或者只给 base，由 ramp() 自动生成 */
  palette?: string[];
  base?: string;
}

export interface HairData {
  id: string;
  name: string;
  palette: string[];
  variants?: PaletteVariantData[];
  /** 发际线：[[方位绝对值, 纬度], ...]，按方位分段线性；同一方位出现两次表示在此处跳变 */
  hairline: [number, number][];
  locks: LockData[];
}

/** 发型整体相对头的大小：头放大时一起放大，发束宽度也跟着变 */
const HS = HEAD_RX / 10.4;
const RX = 11.6 * HS, RY = 11 * HS;
/** 前后方向的半径：比左右窄，侧面看头才是圆的而不是横着的长条 */
const RZ = 10.2 * HS;
/** 镜头俯视的角度：能多看到一点头顶 */
const TILT = (18 * Math.PI) / 180;
const CT = Math.cos(TILT), ST = Math.sin(TILT);
const RAD = Math.PI / 180;

interface Lock extends Required<LockData> {}

interface Proj extends Pt {
  near: number;
}

/** 球面坐标 → 屏幕坐标（已按朝向旋转、按俯视角压扁） */
function project(pose: Pose, cx: number, cy: number, alphaDeg: number, phiDeg: number, rho: number): Proj {
  const a = alphaDeg * RAD, p = phiDeg * RAD;
  const w = Math.cos(a), f = Math.sin(a) * Math.cos(p), s = Math.sin(a) * Math.sin(p);
  // 先按椭球压扁前后方向，再旋转到朝向
  const fz = (f * RZ) / RX;
  const X = s * pose.cos + fz * pose.sin;
  const n = fz * pose.cos - s * pose.sin;
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

/** 发际线分段线性插值 */
export function hairlineAt(points: [number, number][], phiAbs: number): number {
  for (let i = 0; i < points.length - 1; i++) {
    const [p0, a0] = points[i], [p1, a1] = points[i + 1];
    if (phiAbs < p1) return p1 === p0 ? a1 : a0 + ((phiAbs - p0) / (p1 - p0)) * (a1 - a0);
  }
  return points[points.length - 1][1];
}

function drawLocks(c: DrawCtx, locks: Lock[], hairline: [number, number][], back: boolean): void {
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
      if (alpha >= hairlineAt(hairline, phi)) return -1;
      // 底色也按整体受光着色（偏暗），发束之间的缝隙不会是一个个黑点
      return ring(u, v) ? LIGHT : g.t(headLight(u, v) * 0.9 - 0.55);
    });
  }

  const items = locks.map((k, i) => {
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

export function variantPalette(id: string, v: PaletteVariantData): Palette {
  if (v.palette) return pal(id, ...v.palette);
  if (v.base) return ramp(id, v.base);
  throw new Error(`variant ${id}: needs palette or base`);
}

export function makeHair(d: HairData): ItemDef {
  const locks: Lock[] = d.locks.map((k) => ({
    a0: 5, twist: 0, flick: 1.06, lift: 0, tier: 0, ...k,
  }));
  const variants: ItemVariant[] = (d.variants ?? []).map((v) => ({
    id: v.id, name: v.name, palettes: { main: variantPalette(`${d.id}-${v.id}`, v) },
  }));
  return {
    id: d.id,
    name: d.name,
    slot: 'hair',
    palettes: { main: pal(`${d.id}-main`, ...d.palette) },
    variants,
    parts: [
      { layer: 'hair_back', draw: (c) => drawLocks(c, locks, d.hairline, true) },
      { layer: 'hair', draw: (c) => drawLocks(c, locks, d.hairline, false) },
    ],
  };
}
