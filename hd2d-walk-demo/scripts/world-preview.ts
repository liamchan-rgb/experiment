/**
 * 场景与怪物重做的预览（推倒重来，只保留名字）：和人物、图标同一套画笔 / 调色板 / 描边，
 * 但像素密度是人物的 2 倍（1 个场景像素 = 1.66 布局单位，人物是 3.32），所以比人物更精细，又在同一个像素网格上。
 *
 *   npx vite-node scripts/world-preview.ts <输出目录>
 * 输出：meadow.rgba（602 × 362 战斗场景，静态底图）、meadow-grass.rgba（会摆的前景草 4 帧）、wolf.rgba（狼：待机 6 帧 + 扑咬 6 帧）、world.json
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { PixelLayer } from '../src/pixel/PixelLayer';
import { Brush } from '../src/pixel/Brush';
import { pal, BASE, DARK, HI, LIGHT, OUTLINE, type Palette } from '../src/pixel/palette';

const out = process.argv[2] ?? 'world-preview';
mkdirSync(out, { recursive: true });

// ---------------------------------------------------------------- 工具

const hash = (x: number, y: number, k = 0) => {
  let n = (Math.imul(Math.floor(x) + 1013, 374761393) ^ Math.imul(Math.floor(y) + 7, 668265263) ^ Math.imul(k + 3, 2147483647)) | 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
};
/** 平滑值噪声 */
function noise(x: number, y: number, k = 0): number {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const s = (t: number) => t * t * (3 - 2 * t);
  const a = hash(xi, yi, k), b = hash(xi + 1, yi, k), c = hash(xi, yi + 1, k), d = hash(xi + 1, yi + 1, k);
  return a + (b - a) * s(xf) + (c - a) * s(yf) + (a - b - c + d) * s(xf) * s(yf);
}
const fbm = (x: number, y: number, k = 0) => noise(x, y, k) * 0.55 + noise(x * 2.1, y * 2.1, k + 1) * 0.3 + noise(x * 4.3, y * 4.3, k + 2) * 0.15;
const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));

/** 一个部件：画在临时层 → 描边 → 叠到目标层（重叠处自动变成内描边，和人物一样） */
function part(dst: PixelLayer, draw: (g: Brush, L: PixelLayer) => void, opts: { outline?: boolean; inner?: number } = {}): void {
  const L = new PixelLayer(dst.w, dst.h);
  const g = new Brush(L, 1);
  g.grit = 0.12;
  draw(g, L);
  if (opts.outline !== false) { L.bounce(); L.outline(); }
  L.drawOnto(dst, 0, 0, opts.outline === false ? undefined : opts.inner ?? 0.75);
}

// ---------------------------------------------------------------- 场景：林间营地（602 × 362）

const SW = 602, SH = 362;
const P = {
  farLeaf: pal('far-leaf', '#0e1a22', '#1a2e36', '#28443e', '#3a5c48', '#577a58'),
  farTrunk: pal('far-trunk', '#0c1418', '#162228', '#203034', '#2c3e3e', '#3c5048'),
  leaf: pal('leaf', '#0c1a0e', '#1e3a16', '#3a6420', '#6a9a2c', '#b8d850'),
  leafWarm: pal('leaf-warm', '#14200c', '#2e4614', '#567a1c', '#8eb02a', '#e0e868'),
  bark: pal('bark', '#140c08', '#2e1e14', '#4e3624', '#745238', '#9c7652'),
  moss: pal('moss', '#0e1a0a', '#24401a', '#3e6a22', '#6c9a30', '#a8cc50'),
  rock: pal('rock', '#14141a', '#33343e', '#555864', '#7e8290', '#b4b8c4'),
  grass: pal('grass', '#16260e', '#2e4a16', '#4c7420', '#7aa22c', '#c4dc5a'),
  dirt: pal('dirt', '#24160c', '#4a301a', '#76502c', '#a47a46', '#d4b078'),
  tent: pal('tent', '#0c1430', '#1a2c66', '#2a48a0', '#4a72d0', '#8cb0f0'),
  canvas: pal('canvas', '#2a2418', '#5a4e36', '#9a8a64', '#cec09a', '#f4ecd2'),
  wood: pal('wood', '#1a0e06', '#3e2412', '#6a4222', '#946436', '#c09058'),
  flag: pal('flag', '#2a0408', '#6a0c16', '#b02028', '#e84a3a', '#ff9a7a'),
  flowerW: pal('flower-w', '#3a3a44', '#8a8a96', '#d8d8e0', '#f4f4f8', '#ffffff'),
  flowerY: pal('flower-y', '#4a3006', '#9a6a10', '#e8b020', '#ffd84a', '#fff4a0'),
  fern: pal('fern', '#040806', '#0a140c', '#122216', '#1c3220', '#28442c'),
};

/** 一团树冠：一堆叶簇，每簇左上受光、下沿压暗，边缘是锯齿叶片 */
function canopy(dst: PixelLayer, cx: number, cy: number, rx: number, ry: number, palette: Palette, seed: number, far = false): void {
  part(dst, (g) => {
    g.L.use(palette);
    const n = Math.round((rx * ry) / (far ? 90 : 60));
    const blobs: [number, number, number][] = [];
    for (let i = 0; i < n; i++) {
      const a = hash(i, seed) * Math.PI * 2, r = Math.sqrt(hash(i, seed, 1));
      blobs.push([cx + Math.cos(a) * rx * r * 0.8, cy + Math.sin(a) * ry * r * 0.8, (far ? 9 : 7) + hash(i, seed, 2) * (far ? 10 : 8)]);
    }
    // 下面的先画（暗），上面的后画（亮）
    blobs.sort((p, q) => q[1] - p[1]);
    for (const [bx, by, br] of blobs) {
      g.ellipse(bx, by, br * 1.15, br, (lam, nx, ny, u, v) => {
        // 叶片锯齿：边缘按角度起伏
        const ang = Math.atan2(ny, nx), edge = 0.86 + 0.14 * Math.sin(ang * 7 + bx) * hash(Math.floor(u), Math.floor(v), seed);
        if (nx * nx + ny * ny > edge * edge) return -1;
        const leafy = (hash(Math.floor(u / 2), Math.floor(v / 2), seed + 9) - 0.5) * 0.5;
        const sky = (cy - by) / ry * 0.25; // 树冠顶部更亮
        return g.t(lam * 1.1 + leafy + sky - (far ? 0.35 : 0.05));
      });
    }
    // 高光叶片：受光面零星亮点
    if (!far) for (let i = 0; i < n * 3; i++) {
      const a = hash(i, seed, 5) * Math.PI * 2, r = Math.sqrt(hash(i, seed, 6));
      const x = cx + Math.cos(a) * rx * r, y = cy + Math.sin(a) * ry * r;
      if (y < cy + ry * 0.2 && x < cx + rx * 0.3) g.dot(x, y, HI);
    }
  }, { outline: !far, inner: 0.4 });
}

/** 树干：上细下粗，树皮纹路竖向，根部张开 */
function trunk(dst: PixelLayer, x: number, top: number, base: number, w: number, palette: Palette, seed: number): void {
  part(dst, (g) => {
    g.L.use(palette);
    g.fill(x - w * 2.2, top, x + w * 2.2, base + 3, (u, v) => {
      const k = (v - top) / (base - top);
      const flare = k > 0.8 ? ((k - 0.8) / 0.2) ** 2 * w * 1.1 : 0;
      const half = w * (0.7 + 0.3 * k) + flare + (noise(v * 0.15, seed) - 0.5) * 1.5;
      const o = (u - x) / half;
      if (Math.abs(o) > 1) return -1;
      const ridge = Math.sin((u - x) * 1.3 + noise(u * 0.3, v * 0.08, seed) * 6) > 0.55 ? -0.35 : 0;
      return g.t(-o * 0.7 + 0.05 + ridge);
    });
  });
}

/** 苔藓石头 */
function rock(dst: PixelLayer, x: number, y: number, rx: number, ry: number, seed: number): void {
  part(dst, (g) => {
    g.L.use(P.rock);
    g.ellipse(x, y, rx, ry, (lam, nx, ny, u, v) => {
      const facet = (hash(Math.floor((u - x) / 4), Math.floor((v - y) / 3), seed) - 0.5) * 0.5;
      if (ny < -0.35 + (noise(u * 0.3, seed) - 0.5) * 0.5) { g.L.use(P.moss); return g.t(lam + 0.1); }
      g.L.use(P.rock);
      return g.t(lam * 1.2 + facet);
    });
  });
}

function tent(dst: PixelLayer, x: number, y: number, s: number): void {
  part(dst, (g) => {
    g.L.use(P.tent);
    g.fill(x - 22 * s, y - 26 * s, x + 22 * s, y, (u, v) => {
      const k = (y - v) / (26 * s), half = 22 * s * (1 - k);
      if (Math.abs(u - x) > half) return -1;
      const stripe = Math.floor((u - x + 40) / (5 * s)) % 2 ? 0.12 : -0.05;
      return g.t((x - u) / half * 0.6 + stripe + 0.1);
    });
  });
  part(dst, (g) => { // 门帘
    g.L.use(P.canvas);
    g.tri({ x: x - 5 * s, y }, { x: x + 5 * s, y }, { x, y: y - 16 * s }, DARK);
  });
  part(dst, (g) => { // 旗杆和红旗
    g.L.use(P.wood);
    g.rect(x - 0.5, y - 40 * s, 1.2, 16 * s, BASE);
    g.L.use(P.flag);
    g.fill(x, y - 40 * s, x + 12 * s, y - 33 * s, (u, v) => (v - (y - 40 * s) < 7 * s - (u - x) * 0.25 ? g.t(0.3 - (u - x) * 0.03) : -1));
  });
}

function fence(dst: PixelLayer, x0: number, x1: number, y: number): void {
  part(dst, (g) => {
    g.L.use(P.wood);
    for (let x = x0; x <= x1; x += 9) g.rect(x, y - 13, 2.4, 13, LIGHT);
    g.rect(x0 - 2, y - 11, x1 - x0 + 6, 2.2, BASE);
    g.rect(x0 - 2, y - 5, x1 - x0 + 6, 2.2, BASE);
  });
}

function drawScene(): { base: PixelLayer; grass: PixelLayer[] } {
  const S = new PixelLayer(SW, SH);
  const g0 = new Brush(S, 1);
  // 1. 远景林墙：冷色、低对比，上方有一道透光的天空缝
  S.use(P.farLeaf);
  g0.fill(0, 0, SW, 150, (u, v) => {
    const gap = Math.exp(-(((u - 330) / 70) ** 2)) * Math.exp(-((v / 60) ** 2)); // 林间亮处
    return g0.t(-0.9 + fbm(u * 0.05, v * 0.06, 1) * 0.9 + gap * 1.8 + v * 0.002);
  });
  for (let i = 0; i < 14; i++) trunk(S, 20 + i * 43 + hash(i, 1) * 20, 30, 150, 2 + hash(i, 2) * 2, P.farTrunk, 30 + i);
  for (let i = 0; i < 12; i++) canopy(S, 15 + i * 52 + hash(i, 3) * 20, 25 + hash(i, 4) * 40, 40, 30, P.farLeaf, 50 + i, true);
  // 2. 地面：远处偏冷偏暗，舞台中间（人物站的地方）最亮；中间一条小路
  const ground = (u: number, v: number) => {
    const depth = clamp((v - 128) / (SH - 128));
    const pool = Math.exp(-(((u - 300) / 260) ** 2) - (((v - 240) / 110) ** 2)); // 中间的光池
    const road = Math.abs(u - (300 + (v - 128) * 0.55 + Math.sin(v * 0.04) * 18)) < 10 + depth * 30 + (noise(u * 0.2, v * 0.2, 7) - 0.5) * 10;
    return { depth, pool, road };
  };
  g0.fill(0, 128, SW, SH, (u, v) => {
    const { depth, pool, road } = ground(u, v);
    const tex = (hash(Math.floor(u / 2), Math.floor(v), 11) - 0.5) * 0.5; // 竖向的草纹
    const shade = -0.75 + pool * 1.1 + depth * 0.15 + tex + (fbm(u * 0.04, v * 0.05, 12) - 0.5) * 0.5;
    if (road) { S.use(P.dirt); return g0.t(shade - 0.1 + (hash(u, v, 13) < 0.06 ? -0.6 : 0)); }
    S.use(P.grass);
    return g0.t(shade);
  });
  // 草叶：竖着的 2-4 像素小笔触，近处更长
  S.use(P.grass);
  for (let i = 0; i < 2600; i++) {
    const u = hash(i, 21) * SW, v = 132 + hash(i, 22) * (SH - 132);
    const { depth, pool, road } = ground(u, v);
    if (road) continue;
    const h = 2 + depth * 4 * hash(i, 23);
    const s = pool > 0.5 ? (hash(i, 24) < 0.5 ? HI : LIGHT) : hash(i, 24) < 0.5 ? LIGHT : BASE;
    g0.line(u, v, u + (hash(i, 25) - 0.5) * 2, v - h, s);
    g0.dot(u, v + 1, DARK);
  }
  // 小石子、野花
  for (let i = 0; i < 70; i++) {
    const u = hash(i, 31) * SW, v = 140 + hash(i, 32) * (SH - 150);
    part(S, (g) => { g.L.use(P.rock); g.ellipse(u, v, 1.6 + hash(i, 33) * 1.6, 1.1 + hash(i, 33), (lam) => g.t(lam)); });
  }
  for (let i = 0; i < 160; i++) {
    const u = hash(i, 41) * SW, v = 140 + hash(i, 42) * (SH - 150);
    if (ground(u, v).road) continue;
    S.use(hash(i, 43) < 0.6 ? P.flowerW : P.flowerY);
    g0.dot(u, v, HI); g0.dot(u - 1, v, LIGHT); g0.dot(u + 1, v, LIGHT); g0.dot(u, v - 1, LIGHT);
  }
  // 3. 中景：营地（左后方）、苔藓石（右后方）、两侧大树
  fence(S, 30, 100, 150);
  tent(S, 66, 146, 1.1);
  tent(S, 120, 138, 0.8);
  rock(S, 420, 140, 26, 14, 1); rock(S, 452, 146, 16, 10, 2); rock(S, 395, 150, 12, 7, 3);
  rock(S, 30, 176, 14, 8, 4); rock(S, 540, 190, 18, 10, 5);
  trunk(S, 520, 20, 168, 9, P.bark, 1); canopy(S, 520, 30, 85, 46, P.leafWarm, 61);
  trunk(S, 210, 10, 140, 6, P.bark, 2); canopy(S, 215, 20, 60, 34, P.leaf, 62);
  trunk(S, 590, 0, 230, 13, P.bark, 3); canopy(S, 600, 10, 60, 60, P.leaf, 63);
  trunk(S, 10, 0, 210, 11, P.bark, 4); canopy(S, 0, 20, 70, 60, P.leafWarm, 64);
  // 4. 光束：从左上斜射进林间（提亮已有像素，不画新东西）
  for (let y = 0; y < 300; y++) for (let x = 0; x < SW; x++) {
    const d = Math.abs((x - y * 0.6) - 250);
    if (d < 26 && S.get(x, y) > 0 && hash(x, y, 77) < (1 - d / 26) * 0.55 * (1 - y / 300)) S.reshade(x, y, 1);
  }
  // 5. 四角暗角：边缘压暗一阶，舞台中间不动
  for (let y = 0; y < SH; y++) for (let x = 0; x < SW; x++) {
    const d = Math.hypot((x - 300) / 330, (y - 230) / 230);
    if (d > 1 && hash(x, y, 78) < (d - 1) * 2.2) S.reshade(x, y, -1);
  }
  // 6. 前景：左下、右下角的暗色蕨叶（4 帧轻轻摆动，单独一层）
  const grass: PixelLayer[] = [];
  for (let f = 0; f < 4; f++) {
    const G = new PixelLayer(SW, SH);
    for (const [bx, dir] of [[18, 1], [70, 1], [540, -1], [590, -1]] as const) {
      for (let k = 0; k < 7; k++) {
        part(G, (g) => {
          g.L.use(P.fern);
          const sway = Math.sin(f * Math.PI / 2 + k) * 2;
          const len = 40 + hash(k, bx) * 30, ang = -Math.PI / 2 + dir * (0.25 + k * 0.12) + sway * 0.02;
          const pts = Array.from({ length: 6 }, (_, i) => ({ x: bx + k * 4 * dir + Math.cos(ang) * len * i / 5 + dir * (i / 5) ** 2 * 14 + sway * i / 5, y: SH + 4 + Math.sin(ang) * len * i / 5 }));
          g.ribbon(pts, (s) => 3.2 * (1 - s) + 0.4, (lam, o, s, u, v) => (Math.sin(s * 40) > 0.3 && Math.abs(o) > 0.4 ? -1 : g.t(lam * 0.8 - 0.2)));
        }, { inner: 0.3 });
      }
    }
    grass.push(G);
  }
  return { base: S, grass };
}

// ---------------------------------------------------------------- 怪物：狼（朝左，脚底中心在 (110, 104)）

const WW = 220, WH = 120, FX = 120, FY = 112;
const W = {
  furDark: pal('wolf-fur', '#0c0e16', '#1e2230', '#353a4c', '#545a6e', '#7e8496'),
  furLight: pal('wolf-belly', '#2a2a30', '#5c5a60', '#8e8a8c', '#bdb6b0', '#e6ded2'),
  mane: pal('wolf-mane', '#0e0e14', '#262636', '#40404e', '#626274', '#8e8ea0'),
  mouth: pal('wolf-mouth', '#1a0408', '#4a0c14', '#8a1e26', '#c44a4a', '#ee8a80'),
  fang: pal('wolf-fang', '#3a3428', '#7a705c', '#c8c0a8', '#ece6d4', '#ffffff'),
  eye: pal('wolf-eye', '#3a1404', '#8a3a06', '#e88a10', '#ffcc30', '#fff6b0'),
  claw: pal('wolf-claw', '#141010', '#2e2826', '#5a5250', '#8a8280', '#c0b8b0'),
};

interface WolfPose { bob: number; breathe: number; head: [number, number]; jaw: number; tail: number; legs: [number, number, number, number]; crouch: number; lunge: number }

/** 毛发的剪影：沿外缘一圈朝后的毛尖（角度 → 半径倍数），毛尖朝 dir（-1 朝左后 = 朝右） */
const fur = (nx: number, ny: number, seed: number, amp = 0.16) => {
  const ang = Math.atan2(ny, nx);
  const saw = ((ang * 9 / Math.PI + seed) % 1 + 1) % 1; // 锯齿
  return 1 - amp * saw * (0.6 + 0.4 * hash(Math.floor(ang * 9 / Math.PI + seed), seed));
};
/** 毛流：沿着方向的一道道暗纹 */
const strands = (u: number, v: number, seed: number) => {
  // 沿毛流方向（往后下）切成一格格短毛束：一部分压暗（毛缝），少数提亮（毛尖反光）
  const a = u * 0.82 + v * 0.57, b = -u * 0.57 + v * 0.82;
  const ca = Math.floor(a / 5), cb = Math.floor(b / 2.4), fa = a / 5 - ca;
  const h = hash(ca, cb, seed);
  if (fa < 0.62 && h < 0.3) return -0.38;
  if (fa > 0.2 && fa < 0.55 && h > 0.88) return 0.32;
  return 0;
};
/** 背深腹浅：交界处按抖动混合，不是一刀切 */
const bellyMix = (ny: number, u: number, v: number, at = 0.3) => ny + (hash(u, v, 91) - 0.5) * 0.35 > at;

function wolf(pose: WolfPose): PixelLayer {
  const L = new PixelLayer(WW, WH);
  const ox = FX - pose.lunge, oy = FY + pose.bob + pose.crouch;
  const X = (x: number) => ox + x, Y = (y: number) => oy + y;
  // 腿：远侧（暗）先画
  const leg = (hipX: number, hipY: number, kneeX: number, footX: number, far: boolean, lift: number, hind: boolean) => {
    part(L, (g) => {
      g.L.use(W.furDark);
      const fy = Y(-2 - lift), ky = Y(hind ? -22 : -16), shade = far ? -0.55 : 0;
      g.capsule(X(hipX), Y(hipY), X(kneeX), ky, hind ? 11 : 8.5, 5.6, (lam, o, t, u, v) => g.t(lam + shade + strands(u, v, 3)));
      g.capsule(X(kneeX), ky, X(footX), fy, 5.4, 4.2, (lam, o, t, u, v) => g.t(lam + shade + strands(u, v, 4) * 0.6));
      g.L.use(W.furLight);
      g.ellipse(X(footX - 2), fy + 1, 6, 3.2, (lam) => g.t(lam + shade - 0.1)); // 爪掌
      g.L.use(W.claw);
      for (const k of [0, 2.4, 4.8]) g.dot(X(footX - 7 + k), fy + 2.4, far ? DARK : BASE);
    });
  };
  const [lf, lfFar, lh, lhFar] = pose.legs;
  leg(-22, -34, -26, -24, true, lfFar, false);
  leg(40, -38, 50, 44, true, lhFar, true);
  // 尾巴：粗大的毛尾，往后上翘、随呼吸摆动
  part(L, (g) => {
    g.L.use(W.furDark);
    const t = pose.tail;
    const pts = [{ x: X(56), y: Y(-52) }, { x: X(70), y: Y(-50 + t) }, { x: X(82), y: Y(-40 + t * 1.4) }, { x: X(88), y: Y(-26 + t * 1.8) }];
    g.ribbon(pts, (s) => 6 + Math.sin(s * Math.PI) * 6 - s * 2, (lam, o, s, u, v) => {
      if (Math.abs(o) > fur(o, s, 3, 0.35)) return -1;
      if (s > 0.82) { g.L.use(W.furLight); return g.t(lam + 0.1); }
      g.L.use(W.furDark);
      return g.t(lam + strands(u, v, 4));
    });
  });
  // 身体：后腿臀部 + 胸腔，背深腹浅（反荫蔽），毛尖锯齿边
  part(L, (g) => {
    const body = (cx: number, cy: number, rx: number, ry: number, seed: number) => g.ellipse(X(cx), Y(cy), rx, ry + pose.breathe, (lam, nx, ny, u, v) => {
      if (nx * nx + ny * ny > fur(nx, ny, seed) ** 2) return -1;
      const belly = bellyMix(ny, u, v, 0.38);
      g.L.use(belly ? W.furLight : W.furDark);
      return g.t(lam * 1.15 + strands(u, v, seed) + (belly ? -0.2 : 0.05));
    });
    // 背从肩膀往臀部斜下去：肩高臀低，是要扑上来的姿势
    body(36, -44, 24, 18, 1);
    body(2, -52, 34, 22, 2);
  });
  leg(-12, -36, -18, -12, false, lf, false);
  leg(32, -40, 44, 38, false, lh, true);
  // 鬃毛：脖子一圈蓬起的厚毛
  part(L, (g) => {
    g.L.use(W.mane);
    g.ellipse(X(-26 + pose.head[0] * 0.4), Y(-60 + pose.head[1] * 0.4), 24, 27, (lam, nx, ny, u, v) => {
      if (nx * nx + ny * ny > fur(nx, ny, 5, 0.34) ** 2) return -1;
      const chest = bellyMix(ny + (nx < 0 ? 0.25 : -0.3), u, v, 0.5);
      g.L.use(chest ? W.furLight : W.mane);
      return g.t(lam * 1.2 + strands(u, v, 6) + (chest ? -0.1 : 0.05));
    });
  });
  // 头：额头、口鼻、下颌（张嘴时下颌往下转）、獠牙、鼻头、耳朵、发光的眼
  // 头压低、往前探
  const hx = -50 + pose.head[0], hy = -62 + pose.head[1];
  part(L, (g) => { // 远耳
    g.L.use(W.furDark);
    g.tri({ x: X(hx + 4), y: Y(hy - 6) }, { x: X(hx + 12), y: Y(hy - 4) }, { x: X(hx + 10), y: Y(hy - 22) }, DARK);
  });
  part(L, (g) => { // 下颌
    g.L.use(W.furLight);
    const j = pose.jaw;
    g.capsule(X(hx - 2), Y(hy + 8), X(hx - 24), Y(hy + 12 + j), 6, 3.6, (lam) => g.t(lam - 0.05));
  });
  if (pose.jaw > 1) part(L, (g) => { // 张开的嘴里
    g.L.use(W.mouth);
    g.tri({ x: X(hx - 4), y: Y(hy + 4) }, { x: X(hx - 28), y: Y(hy + 3) }, { x: X(hx - 26), y: Y(hy + 8 + pose.jaw) }, BASE);
  }, { outline: false });
  part(L, (g) => { // 头和口鼻
    g.L.use(W.furDark);
    g.ellipse(X(hx), Y(hy), 17, 14, (lam, nx, ny, u, v) => {
      if (nx * nx + ny * ny > fur(nx, ny, 7, 0.14) ** 2) return -1;
      if (bellyMix(ny, u, v, 0.4) && nx < 0.3) { g.L.use(W.furLight); return g.t(lam); }
      g.L.use(W.furDark);
      // 眉弓下的眼窝压暗
      const socket = Math.hypot(u - X(hx - 7), (v - Y(hy - 2)) * 1.6) < 6 ? -0.45 : 0;
      return g.t(lam * 1.15 + strands(u, v, 8) + 0.1 + socket);
    });
    g.L.use(W.furDark);
    g.capsule(X(hx - 6), Y(hy + 2), X(hx - 25), Y(hy + 5), 8.5, 5.2, (lam, o, t, u, v) => {
      // 龇牙时鼻梁上的皱褶
      if (o < -0.2 && Math.sin((u - X(hx)) * 1.4) > 0.6 && t > 0.2 && t < 0.7) return g.t(lam - 0.6);
      if (o > 0.35) { g.L.use(W.furLight); return g.t(lam); }
      g.L.use(W.furDark);
      return g.t(lam * 1.1 + 0.1);
    });
  });
  part(L, (g) => { // 近耳：竖起、内侧浅色
    g.L.use(W.furDark);
    g.tri({ x: X(hx - 2), y: Y(hy - 8) }, { x: X(hx + 8), y: Y(hy - 6) }, { x: X(hx + 6), y: Y(hy - 25) }, (u, v) => g.t(0.2 - (u - X(hx)) * 0.04));
    g.L.use(W.furLight);
    g.tri({ x: X(hx + 1), y: Y(hy - 8) }, { x: X(hx + 6), y: Y(hy - 7) }, { x: X(hx + 5), y: Y(hy - 19) }, DARK);
  });
  part(L, (g) => { // 獠牙、鼻头、眉弓
    g.L.use(W.fang);
    g.tri({ x: X(hx - 21), y: Y(hy + 8) }, { x: X(hx - 18.6), y: Y(hy + 8) }, { x: X(hx - 20), y: Y(hy + 13 + pose.jaw * 0.3) }, LIGHT);
    g.tri({ x: X(hx - 13), y: Y(hy + 9) }, { x: X(hx - 10.8), y: Y(hy + 9) }, { x: X(hx - 12), y: Y(hy + 13) }, LIGHT);
    g.tri({ x: X(hx - 19), y: Y(hy + 13 + pose.jaw) }, { x: X(hx - 17), y: Y(hy + 13 + pose.jaw) }, { x: X(hx - 18), y: Y(hy + 10 + pose.jaw) }, BASE);
    g.L.use(W.furDark);
    g.ellipse(X(hx - 26), Y(hy + 3), 3.4, 2.8, OUTLINE);
    g.dot(X(hx - 27), Y(hy + 2), LIGHT);
  }, { outline: false });
  part(L, (g) => { // 眼睛：斜长的琥珀色，竖瞳
    g.L.use(W.eye);
    g.fill(X(hx - 12), Y(hy - 4), X(hx - 3), Y(hy + 1), (u, v) => {
      const k = (u - X(hx - 12)) / 9, mid = Y(hy - 1.8) - k * 1.6;
      if (Math.abs(v - mid) > 1.6 * Math.sin(k * Math.PI) + 0.2) return -1;
      if (Math.abs(u - X(hx - 7)) < 0.6) return OUTLINE;
      return k < 0.4 ? HI : LIGHT;
    });
  }, { outline: false });
  // 背光边：右上方没有像素的边缘提亮一阶（冷色的轮廓光，让暗色的狼从暗背景里跳出来）
  for (let y = 1; y < WH - 1; y++) for (let x = 1; x < WW - 1; x++) {
    if (L.get(x, y) > 0 && (L.get(x + 1, y - 1) === 0 || L.get(x, y - 1) === 0) && L.get(x - 1, y) > 0) L.reshade(x, y, 1);
  }
  return L;
}

const IDLE: WolfPose[] = Array.from({ length: 6 }, (_, f) => {
  const s = Math.sin((f / 6) * Math.PI * 2);
  return { bob: 0, breathe: s * 0.9, head: [0, s * 0.8] as [number, number], jaw: 1.2 + Math.max(0, s), tail: Math.sin((f / 6) * Math.PI * 2 + 1) * 3, legs: [0, 0, 0, 0] as [number, number, number, number], crouch: 0, lunge: 0 };
});
// 扑咬：蓄力下压 → 前扑张嘴 → 咬合 → 收回
const POUNCE: WolfPose[] = [
  { bob: 0, breathe: 0, head: [4, 6], jaw: 1, tail: -2, legs: [0, 0, 0, 0], crouch: 4, lunge: -4 },
  { bob: 0, breathe: -1, head: [6, 8], jaw: 2, tail: -4, legs: [0, 0, 0, 0], crouch: 6, lunge: -8 },
  { bob: -10, breathe: 1, head: [-6, -4], jaw: 9, tail: 6, legs: [10, 8, 0, 2], crouch: 0, lunge: 26 },
  { bob: -6, breathe: 1, head: [-10, 0], jaw: 2, tail: 4, legs: [6, 4, 2, 0], crouch: 0, lunge: 40 },
  { bob: 0, breathe: 0, head: [-4, 2], jaw: 1, tail: 0, legs: [0, 0, 0, 0], crouch: 2, lunge: 20 },
  { bob: 0, breathe: 0, head: [0, 0], jaw: 1.5, tail: 0, legs: [0, 0, 0, 0], crouch: 0, lunge: 4 },
];

const { base, grass } = drawScene();
const rgba = (L: PixelLayer) => { const a = new Uint8ClampedArray(L.w * L.h * 4); L.toRGBA(a); return a; };
writeFileSync(`${out}/meadow.rgba`, rgba(base));
writeFileSync(`${out}/meadow-grass.rgba`, Buffer.concat(grass.map((G) => Buffer.from(rgba(G)))));
writeFileSync(`${out}/wolf.rgba`, Buffer.concat([...IDLE, ...POUNCE].map((p) => Buffer.from(rgba(wolf(p))))));
writeFileSync(`${out}/world.json`, JSON.stringify({ scene: [SW, SH], grassFrames: grass.length, wolf: { w: WW, h: WH, foot: [FX, FY], idle: IDLE.length, pounce: POUNCE.length } }));
console.log('ok');
