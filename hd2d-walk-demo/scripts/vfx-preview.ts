/**
 * 技能特效预览：用 pixelfx（MIT，vendor/pixelfx）的像素特效二次创作桌游的技能和命中效果，
 * 时长、出手时刻、压暗、镜头（技能镜头 / 震屏 / 导演镜头 / 命中顿帧）照搬游戏里的数值（MeadowSkillProcedural、MeadowBattleHitFeel）。
 *
 *   npm run vfx-preview -- <输出目录>
 * 每个场景输出 <id>.rgba（逐帧舞台，透明底）和 <id>.json（每帧的镜头、压暗），由 tools/vfx_gif.py 合成背景、镜头并出 GIF。
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { PixelLayer } from '../src/pixel/PixelLayer';
import { composeFrame } from '../src/character/paperdoll';
import { CLIP_FRAMES, IMPACT_FRAME, SPR_H, SPR_W, type AnimId } from '../src/character/rig';
import { CHARACTERS, buildEquipment, type CharacterPreset } from '../src/items/characters';
import { getItem } from '../src/items/registry';
// @ts-expect-error vendored plain JS
import { createFx, createFrame, clearFrame, composite } from '../vendor/pixelfx/src/core/index.js';

const outDir = process.argv[2] ?? 'vfx-preview';
mkdirSync(outDir, { recursive: true });

// ---------------------------------------------------------------- 舞台

/** 游戏战斗舞台 1000 × 600（布局单位）；人物放大 4 倍 × heroScale 0.83 → 1 个精灵像素 = 3.32 单位 */
const U = 4 * 0.83;
const W = Math.round(1000 / U), H = Math.round(600 / U);
const FPS = 20;
const FOOT = { x: 20.8, y: 58.5 };

type Pt = { x: number; y: number };
const px = (x: number, y: number): Pt => ({ x: x / U, y: y / U });
/** 课堂默认站位（PartyVisual.classicFeet） */
const FEET: Record<string, Pt> = {
  p1: px(165, 420), p2: px(315, 505), p4: px(280, 315),
  m1: px(650, 395), m2: px(835, 510), m3: px(600, 585),
};

// ---------------------------------------------------------------- 游戏的镜头（MeadowSkillProcedural / MeadowBattleHitFeel 的移植）

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const smooth = (x: number) => { const t = clamp01(x); return t * t * (3 - 2 * t); };
const easeOut = (x: number) => { const t = clamp01(x); return 1 - (1 - t) ** 3; };
const b2d = (v: boolean) => (v ? 1 : 0);
const thump = (t: number, t0: number, a: number, k: number, w: number, ph = 0) => { const r = t - t0; return r < 0 ? 0 : a * Math.exp(-r * k) * Math.cos(r * w + ph); };

interface Cam { dx: number; dy: number; zoom: number; rot: number }
const ZERO: Cam = { dx: 0, dy: 0, zoom: 0, rot: 0 };
const add = (a: Cam, b: Cam): Cam => ({ dx: a.dx + b.dx, dy: a.dy + b.dy, zoom: a.zoom + b.zoom, rot: a.rot + b.rot });

const INFO: Record<string, { duration: number; release: number; dim: number; tint: [number, number, number] }> = {
  starlightPulse: { duration: 1.6, release: 0.75, dim: 0.34, tint: [0.8, 0.76, 1] },
  dragonSoulWard: { duration: 2.0, release: 0.38, dim: 0.32, tint: [0.74, 0.88, 1] },
  dragonScaleWard: { duration: 2.2, release: 0.56, dim: 0.28, tint: [1, 0.88, 0.7] },
  runeSlash: { duration: 2.4, release: 1.048, dim: 0.3, tint: [0.8, 0.92, 1] },
  runeWard: { duration: 2.4, release: 0.72, dim: 0.28, tint: [0.8, 0.92, 1] },
  battleRune: { duration: 2.1, release: 0.56, dim: 0.28, tint: [1, 0.88, 0.72] },
  dragonFlame: { duration: 2.2, release: 0.46, dim: 0.34, tint: [1, 0.78, 0.62] },
  dragonOrder: { duration: 2.1, release: 0.56, dim: 0.32, tint: [1, 0.78, 0.72] },
  rally: { duration: 2.0, release: 0.56, dim: 0.24, tint: [1, 0.94, 0.8] },
  healMicro: { duration: 1.35, release: 0.1, dim: 0.26, tint: [0.82, 0.96, 0.86] },
  healStandard: { duration: 1.8, release: 0.1, dim: 0.28, tint: [0.8, 0.96, 0.85] },
  healStrong: { duration: 2.3, release: 0.1, dim: 0.32, tint: [0.78, 0.95, 0.84] },
  sweep: { duration: 2.0, release: 1.048, dim: 0.26, tint: [0.82, 0.9, 1] },
  natural20: { duration: 2.8, release: 0.05, dim: 0.5, tint: [1, 0.92, 0.7] },
  shieldDome: { duration: 1.9, release: 0.46, dim: 0.26, tint: [0.8, 0.92, 1] },
  shieldShell: { duration: 3.0, release: 0.5, dim: 0, tint: [1, 1, 1] },
  shieldShellHit: { duration: 3.0, release: 0.5, dim: 0, tint: [1, 1, 1] },
  shieldBreak: { duration: 1.2, release: 0.03, dim: 0, tint: [1, 1, 1] },
  deathSlime: { duration: 1.8, release: 0.04, dim: 0, tint: [1, 1, 1] },
  deathWolf: { duration: 1.8, release: 0.04, dim: 0, tint: [1, 1, 1] },
  deathGoblin: { duration: 1.8, release: 0.04, dim: 0, tint: [1, 1, 1] },
  deathStone: { duration: 2.0, release: 0.04, dim: 0, tint: [1, 1, 1] },
  deathTroll: { duration: 1.8, release: 0.04, dim: 0, tint: [1, 1, 1] },
  deathDragon: { duration: 2.4, release: 0.04, dim: 0, tint: [1, 1, 1] },
  deathBurst: { duration: 1.8, release: 0.04, dim: 0, tint: [1, 1, 1] },
  playerDown: { duration: 2.2, release: 0.05, dim: 0, tint: [1, 1, 1] },
  buffAura: { duration: 3.0, release: 0.3, dim: 0, tint: [1, 1, 1] },
  revive: { duration: 1.8, release: 0.3, dim: 0, tint: [1, 1, 1] },
  downAura: { duration: 3.0, release: 0.5, dim: 0, tint: [1, 1, 1] },
  projBow: { duration: 0.54, release: 0.19, dim: 0, tint: [1, 1, 1] },
  projStaff: { duration: 1.05, release: 0.7, dim: 0, tint: [1, 1, 1] },
  projArcher: { duration: 0.57, release: 0.22, dim: 0, tint: [1, 1, 1] },
  projDragon: { duration: 0.57, release: 0.22, dim: 0, tint: [1, 1, 1] },
};
/** 游戏里的「打击类」：没有技能镜头、导演镜头和压暗，只有震屏（MeadowSkillProcedural.isBlow） */
const isBlow = (id: string) => id.startsWith('hit') || id.startsWith('proj') || id.startsWith('shieldShell') || id.startsWith('death') || id === 'downAura' || id === 'buffAura' || id === 'shieldBreak';

function skillCamera(id: string, t: number, dir: number): Cam {
  const i = INFO[id];
  if (!i || t < 0 || t >= i.duration || isBlow(id)) return ZERO;
  const c = { ...ZERO };
  switch (id) {
    case 'starlightPulse':
      c.zoom = 0.008 * smooth(t / 0.75) * b2d(t < 0.75) + Math.max(0, thump(t, 0.75, 0.024, 7, 0));
      c.dx = dir * thump(t, 0.75, 3, 9, 30); c.dy = -thump(t, 0.75, 1.6, 10, 34, 0.6); break;
    case 'dragonSoulWard':
      c.zoom = 0.014 * smooth(t / 0.38) * b2d(t < 0.38) + Math.max(0, thump(t, 0.38, 0.03, 6, 0));
      c.dy = -thump(t, 0.38, 3, 8, 34, 0.6); c.rot = thump(t, 0.38, 0.004, 9, 24); break;
    case 'runeSlash':
      for (let k = 0; k < 5; k++) {
        const t0 = 1.048 + 0.06 * k, s = k % 2 === 0 ? 1 : -1;
        c.dx += dir * s * thump(t, t0, 3.4, 26, 62); c.dy += -s * thump(t, t0, 1.6, 24, 70, 0.4);
      }
      c.zoom = Math.max(0, thump(t, 1.35, 0.03, 8, 0)); c.rot = dir * thump(t, 1.35, 0.006, 10, 28); break;
    case 'runeWard':
      c.zoom = Math.max(0, thump(t, 1.12, 0.02, 10, 0)) + 0.006 * smooth(t / 0.72) * b2d(t < 1.12); c.dy = -thump(t, 1.12, 2.2, 12, 40, 0.6); break;
    case 'battleRune': {
      const r = t - 0.56;
      if (r >= 0) { c.dx = 2.6 * Math.sin(t * 71) * Math.exp(-r * 2.2); c.dy = 2 * Math.sin(t * 83 + 1) * Math.exp(-r * 2.4); c.zoom = Math.max(0, thump(t, 0.56, 0.02, 8, 0)); }
      break;
    }
    case 'dragonFlame': {
      c.dx = dir * thump(t, 0.46, 7, 7, 28); c.dy = -thump(t, 0.46, 4, 8, 36, 0.6);
      c.zoom = Math.max(0, thump(t, 0.46, 0.045, 6, 0)); c.rot = dir * thump(t, 0.46, 0.008, 8, 26);
      const r = t - 0.9;
      if (r >= 0 && r < 1) c.dy += 0.9 * Math.sin(t * 47) * (1 - r);
      break;
    }
    case 'dragonScaleWard':
      c.zoom = Math.max(0, thump(t, 0.56, 0.032, 9, 0)); c.dy = -thump(t, 0.56, 3.2, 10, 30, 0.6); break;
    case 'rally':
      c.zoom = Math.max(0, thump(t, 0.56, 0.03, 9, 0)); c.dy = -thump(t, 0.56, 2, 12, 40, 0.5); break;
    case 'dragonOrder':
      [0.02, 0.022, 0.036].forEach((amp, k) => {
        const t0 = 0.56 + 0.3 * k;
        c.zoom += Math.max(0, thump(t, t0, amp, 12, 0)); c.dy += -thump(t, t0, 1.6 + k, 14, 40, 0.5);
      });
      break;
    case 'playerDown':
      c.zoom = Math.max(0, thump(t, 0, 0.06, 4, 0)); c.dx = dir * thump(t, 0, 10, 4, 30); c.dy = -thump(t, 0, 8, 4.5, 36, 0.6); c.rot = -dir * thump(t, 0, 0.016, 4, 22); break;
    case 'natural20': {
      c.zoom = Math.max(0, thump(t, 0, 0.07, 5, 0)); c.dx = dir * thump(t, 0, 12, 4.5, 34); c.dy = -thump(t, 0, 8, 5, 40, 0.6);
      c.rot = dir * thump(t, 0, 0.02, 5, 24);
      const r = t - 0.4;
      if (r >= 0 && r < 1.2) c.dy += 1.2 * Math.sin(t * 53) * (1 - r / 1.2);
      break;
    }
    case 'sweep':
      c.dx = dir * thump(t, 1.048, 6, 9, 30); c.dy = -thump(t, 1.048, 2.4, 10, 40, 0.6);
      c.zoom = Math.max(0, thump(t, 1.048, 0.035, 7, 0)); c.rot = dir * thump(t, 1.048, 0.006, 9, 26); break;
    default:
      c.zoom = 0.006 * Math.sin((Math.PI * t) / i.duration);
  }
  return c;
}

function trauma(id: string, t: number): number {
  const i = INFO[id];
  if (!i || t < 0 || id.startsWith('hit') || id.startsWith('proj') || id.startsWith('heal') || id.startsWith('shieldShell') || id === 'downAura' || id === 'buffAura' || id === 'shieldDome') return 0;
  const table: Record<string, [number, number]> = {
    dragonFlame: [0.95, 3.2], runeSlash: [0.7, 4.5], starlightPulse: [0.5, 4], dragonScaleWard: [0.5, 4], dragonOrder: [0.5, 4],
    natural20: [1.0, 1.7], playerDown: [0.9, 2.6], sweep: [0.8, 4.0], shieldBreak: [0.6, 4.5],
    deathDragon: [0.8, 3.0], deathTroll: [0.6, 3.6], deathStone: [0.7, 3.4], deathSlime: [0.4, 4.5], deathWolf: [0.4, 4.5], deathGoblin: [0.4, 4.5], deathBurst: [0.4, 4.5],
  };
  const [amp, rate] = table[id] ?? [0.42, 4.5];
  const r = t - i.release;
  if (r < -0.01) return 0;
  const boost = id === 'dragonFlame' && r > 0 && r < 1.2 ? 0.3 * (1 - r / 1.2) : 0;
  return (amp * Math.exp(-Math.max(0, r) * rate) + boost) * smooth((r + 0.01) / 0.03);
}

function shake(tr: number, time: number): Cam {
  const k = clamp01(tr), s = k ** 1.5;
  const n = (seed: number) => Math.sin(time * 43 + seed) * 0.55 + Math.sin(time * 71 + seed * 2.1) * 0.3 + Math.sin(time * 109 + seed * 3.7) * 0.15;
  return { dx: 26 * s * n(1.3), dy: 18 * s * n(4.1), rot: 0.028 * s * n(7.7), zoom: 0.035 * k };
}

/** 导演镜头：蓄力时推近施法者，出手时摇向目标，之后慢慢拉开（舞台坐标） */
function shot(id: string, t: number, caster: Pt, targets: Pt[]): { fx: number; fy: number; w: number; zoom: number } {
  const i = INFO[id];
  if (!i || t < 0 || t >= i.duration || !targets.length || id.startsWith('heal') || isBlow(id)) return { fx: 500, fy: 300, w: 0, zoom: 0 };
  const mx = targets.reduce((a, p) => a + p.x, 0) / targets.length, my = targets.reduce((a, p) => a + p.y, 0) / targets.length;
  if (id === 'playerDown') {
    // 倒地：镜头慢慢推向倒下的人，停一会儿（脚底往上 30 单位；这里传进来的是胸口 = 脚底往上 73）
    const w = smooth(t / 0.2) * (1 - smooth((t - 1.0) / 0.8));
    return { fx: mx, fy: my + 43, w, zoom: w * 0.22 };
  }
  if (id === 'natural20') {
    const w = smooth(t / 0.12) * (1 - smooth((t - 1.3) / 0.9));
    return { fx: mx, fy: my, w, zoom: w * 0.34 };
  }
  const rel = Math.max(0.2, i.release);
  const tx = targets.reduce((a, p) => a + p.x, 0) / targets.length, ty = targets.reduce((a, p) => a + p.y, 0) / targets.length;
  const spread = Math.max(...targets.map((p) => Math.abs(p.x - tx)));
  const hold = rel + 0.9;
  const weight = smooth(t / (rel * 0.45)) * (1 - smooth((t - hold) / Math.min(1, Math.max(0.5, i.duration - hold))));
  const swing = smooth((t - rel * 0.55) / (rel * 0.6 + 0.12));
  const fx = caster.x + (tx - caster.x) * swing, fy = caster.y + (ty - caster.y) * swing;
  const wide = 1 - clamp01(spread / 420);
  return { fx, fy, w: weight, zoom: weight * (0.3 + (0.13 + 0.08 * wide - 0.3) * swing) };
}

function ambient(id: string, t: number): number {
  const i = INFO[id];
  if (!i || t < 0 || t >= i.duration) return 0;
  return clamp01(smooth(t / Math.max(0.1, i.release * 0.8)) * (1 - smooth((t - i.duration * 0.62) / (i.duration * 0.38))));
}

const HOLD = 0.1;
type Tier = 'light' | 'medium' | 'heavy';
const TIERK: Record<Tier, number> = { light: 0.7, medium: 1, heavy: 1.45 };
function hitCamera(age: number, tier: Tier, dir: number): Cam {
  if (age < 0) return ZERO;
  const k = TIERK[tier];
  if (age < HOLD) return { dx: 0, dy: 0, zoom: 0.032 * k * easeOut(age / 0.03), rot: 0 };
  const r = age - HOLD;
  return { dx: dir * 6 * k * Math.exp(-r * 10) * Math.cos(r * 34), dy: -2.2 * k * Math.exp(-r * 12) * Math.sin(r * 40 + 0.6), zoom: 0.032 * k * Math.exp(-r * 9), rot: dir * 0.0062 * k * Math.exp(-r * 10) * Math.sin(r * 30) };
}
function knockback(age: number, tier: Tier): number {
  if (age < HOLD) return 0;
  const k = TIERK[tier], r = age - HOLD, dist = 760 * 0.025 * (0.8 + 0.5 * (k - 0.7));
  return dist * 1.15 * (1 - Math.exp(-r * 30)) * Math.exp(-Math.max(0, r - 0.1) * 5.5);
}

// ---------------------------------------------------------------- 人物

interface Hero {
  slot: string;
  preset: CharacterPreset;
  top?: string;
  /** 动画：t（秒）→ sheet 列 */
  anim?: (t: number) => number;
  /** 前冲：t → 相对站位的水平位移（布局单位） */
  travel?: (t: number) => number;
}

const bakeCache = new Map<string, Uint8ClampedArray>();
/**
 * pixelfx 的特效默认描一个自带的木头假人（actor：遮罩 + 像素），hit-flash 会把它整个画出来（白闪后变成灰色「石像」），
 * heal / blessing / rage / burning 沿它的轮廓发光。这里换成我们角色当前这一帧的遮罩和像素，特效就贴在真正的人物身上。
 */
const actorCache = new Map<string, unknown>();
function actorOf(h: Hero, frame: number, flip: boolean, dy: number): unknown {
  const key = `${h.slot}|${frame}|${flip}|${dy}`;
  const hit = actorCache.get(key);
  if (hit) return hit;
  const rgba = heroFrame(h, frame);
  let x0 = SPR_W, y0 = SPR_H, x1 = -1, y1 = -1;
  for (let y = 0; y < SPR_H; y++) for (let x = 0; x < SPR_W; x++) if (rgba[(y * SPR_W + x) * 4 + 3]) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  const w = x1 - x0 + 1, hh = y1 - y0 + 1, data = new Uint8Array(w * hh), pixels = new Uint32Array(w * hh);
  for (let y = 0; y < hh; y++) for (let x = 0; x < w; x++) {
    const sx = flip ? x1 - x : x0 + x, o = ((y0 + y) * SPR_W + sx) * 4;
    if (!rgba[o + 3]) continue;
    data[y * w + x] = 1;
    pixels[y * w + x] = (rgba[o] | (rgba[o + 1] << 8) | (rgba[o + 2] << 16) | (255 << 24)) >>> 0;
  }
  // 局部坐标：原点是脚底（特效被往下挪了 dy，身体就相对往上 dy）
  const lx = flip ? Math.round(FOOT.x) - x1 - 1 : x0 - Math.round(FOOT.x), ly = y0 - Math.round(FOOT.y) - dy;
  const a = { mask: { w, h: hh, data }, pixels, x: lx, y: ly, w, h: hh, k: 2, head: [0, ly], chest: [0, ly + Math.round(hh * 0.45)] };
  actorCache.set(key, a);
  return a;
}
function heroFrame(h: Hero, frame: number): Uint8ClampedArray {
  const key = `${h.slot}|${frame}`;
  const hit = bakeCache.get(key);
  if (hit) return hit;
  const eq = buildEquipment(h.preset);
  if (h.top) eq.equip('top', getItem(h.top)!);
  eq.unequip('scarf'); eq.unequip('bag');
  const L = new PixelLayer(SPR_W, SPR_H);
  composeFrame(eq.resolve(), 'E', frame, L);
  const out = new Uint8ClampedArray(SPR_W * SPR_H * 4);
  L.toRGBA(out);
  bakeCache.set(key, out);
  return out;
}

/** 战斗待机（2 帧呼吸），在 [start, start + 帧数 × dt) 里播一段动作，出手帧对准 impact */
function clip(name: AnimId, impactAt: number, dt = 1 / 12): (t: number) => number {
  const frames = CLIP_FRAMES[name], ready = CLIP_FRAMES.ready;
  const imp = (IMPACT_FRAME as Record<string, number>)[name] ?? 0;
  const start = impactAt - imp * dt;
  return (t) => {
    if (t >= start && t < start + frames.length * dt) return frames[Math.floor((t - start) / dt)];
    return ready[Math.floor(t * 2.5) % 2];
  };
}
const readyLoop = (t: number) => CLIP_FRAMES.ready[Math.floor(t * 2.5) % 2];
/** 近战前冲：出手前 0.4 秒冲到目标前，动作结束后退回 */
function dashTo(target: Pt, home: Pt, impact: number, back = 0.9): (t: number) => number {
  const dist = (target.x - home.x) * U - 95;
  return (t) => dist * (smooth((t - (impact - 0.45)) / 0.25) - smooth((t - (impact + back)) / 0.3));
}

const look = {
  spellblade: { ...CHARACTERS[0], hair: 'hair_swept', weapon: 'weapon_starlight_blade' } as CharacterPreset,
  dragon: { ...CHARACTERS[0], hair: 'hair_swept', skin: 'tan', weapon: 'weapon_dragon_fang' } as CharacterPreset,
  ranger: { ...CHARACTERS[2], weapon: 'weapon_hunting_bow' } as CharacterPreset,
  adventurer: { ...CHARACTERS[0], weapon: 'weapon_training_sword' } as CharacterPreset,
  heavy: { ...CHARACTERS[0], hair: 'hair_messy', weapon: 'weapon_great_sword' } as CharacterPreset,
  mage: { ...CHARACTERS[1], hair: 'hair_long', weapon: 'weapon_legendary_staff' } as CharacterPreset,
  star: { ...CHARACTERS[0], hair: 'hair_ponytail', weapon: 'weapon_starlight_blade' } as CharacterPreset,
};

// ---------------------------------------------------------------- 特效

/** 特效模块缓存 */
const mods = new Map<string, unknown>();
const loaders = import.meta.glob('../vendor/pixelfx/src/fx/*/*.js');
const OURS: Record<string, () => Promise<unknown>> = { 'our/aegis': () => import('../src/vfx/aegis') };
async function mod(id: string): Promise<unknown> {
  if (!mods.has(id) && OURS[id]) mods.set(id, await OURS[id]());
  if (!mods.has(id)) {
    const load = loaders[`../vendor/pixelfx/src/fx/${id}.js`];
    if (!load) throw new Error(`pixelfx effect ${id} not found`);
    mods.set(id, await load());
  }
  return mods.get(id);
}

interface FxEvent {
  fx: string;
  /** 开始时间（秒） */
  at: number;
  /** 放在哪里：每个点各放一份 */
  where: (s: Scene, t: number) => Pt[];
  /** 相对位置偏移（像素） */
  dx?: number;
  dy?: number;
  opts?: Record<string, unknown>;
  /** 循环特效在这个时间让它淡出 */
  stop?: number;
  /** 跟着点移动（比如飞行物） */
  follow?: boolean;
  /** 整个画在人物后面（身后的光轮这类） */
  behind?: boolean;
}

interface Scene {
  id: string;
  name: string;
  duration: number;
  kind: 'skill' | 'hit';
  heroes: Hero[];
  monsters: Monster[];
  caster: string;
  targets: string[];
  events: FxEvent[];
  /** 命中：哪一刻命中、多重、打的是谁 */
  hit?: { at: number; tier: Tier; target: string; dir: number };
  /** 镜头 / 压暗按游戏里哪个特效 id 来（默认 = id），从场景的第几秒开始（前面留给出手动作） */
  cue?: string;
  cueAt?: number;
  /** 镜头方向（+1 往右） */
  dir?: number;
}
type Death = 'melt' | 'dust' | 'shatter' | 'burst' | 'crumble';
interface Monster { slot: string; fx: string; opts?: Record<string, unknown>; dieAt?: number; death?: Death; edge?: string }

/** 一个角色当前的脚底位置（像素），含前冲和被击退 */
function footOf(s: Scene, slot: string, t: number): Pt {
  const base = FEET[slot];
  const h = s.heroes.find((x) => x.slot === slot);
  let dx = h?.travel ? h.travel(t) / U : 0;
  if (s.hit && s.hit.target === slot) dx += (s.hit.dir * knockback(t - s.hit.at, s.hit.tier)) / U;
  return { x: base.x + dx, y: base.y };
}
/** 放在某个角色脚下（dy 往下为正）。记下是谁：特效要「描角色身体」时用这个角色自己的像素 */
const at = (slot: string, dy = 0) => Object.assign((s: Scene, t: number) => [{ ...footOf(s, slot, t), y: footOf(s, slot, t).y + dy }], { slot, dy });

// 调色板（暗 → 亮）
const PAL = {
  rune: ['#06222a', '#0a4a56', '#108a94', '#24c8c8', '#6af0e0', '#c8fff6', '#ffffff'],
  violet: ['#140a30', '#2e1870', '#5a34c0', '#8a64f0', '#b89cff', '#e2d6ff', '#ffffff'],
  fire: ['#2a0804', '#6a1606', '#b8320c', '#f0681c', '#ffa83a', '#ffe08a', '#fffbe0'],
  amber: ['#2a1404', '#6a3a0c', '#b8701c', '#f0a832', '#ffd060', '#fff0b0', '#ffffff'],
  gold: ['#2a1a04', '#6a4a0c', '#b8861c', '#f0c040', '#ffe070', '#fff6c0', '#ffffff'],
  crimson: ['#2a0408', '#6a0c16', '#b02028', '#f04a3a', '#ff8a5a', '#ffd0a0', '#ffffff'],
  steel: ['#101420', '#2a3448', '#566880', '#94a8c0', '#cad8e8', '#f0f6ff', '#ffffff'],
  ice: ['#081a30', '#103a6a', '#1e6ab0', '#3ca0e6', '#80d0ff', '#d0f2ff', '#ffffff'],
  magenta: ['#2a0420', '#6a0c50', '#b01e8a', '#f04ab8', '#ff8ad8', '#ffd0f0', '#ffffff'],
  heal: ['#08261a', '#0e4228', '#1a7a44', '#2eb862', '#6ee896', '#b8ffd0', '#e8fff0', '#ffffff'],
  sweep: ['#081436', '#14328c', '#2a64d0', '#5ca8ff', '#9ad2ff', '#d8f0ff', '#ffffff'],
  fury: ['#2a0806', '#6a160a', '#b83214', '#f0602a', '#ff9a4a', '#ffd890', '#ffffff'],
  down: ['#140c14', '#2e1c28', '#5a3448', '#8a5068', '#b8889a', '#e8d0d8', '#ffffff'],
  goo: ['#0c1e10', '#1a4224', '#2e7a3a', '#4cb050', '#8ae07a', '#d0ffc0', '#ffffff'],
};

// ---------------------------------------------------------------- 场景

const party = (caster: Hero, a: Hero, b: Hero) => [caster, a, b];
const ally = (slot: string, preset: CharacterPreset, top?: string): Hero => ({ slot, preset, top, anim: readyLoop });
const enemies = [
  { slot: 'm1', fx: 'critters/slime', opts: { palette: ['#0c1e10', '#1a4224', '#2e7a3a', '#4cb050', '#8ae07a', '#d0ffc0'] } },
  { slot: 'm2', fx: 'critters/slime', opts: { palette: ['#1e0c10', '#4a1a24', '#8a2e3a', '#c84c50', '#f08a7a', '#ffd0c0'], seed: 4 } },
  { slot: 'm3', fx: 'critters/ghost', opts: { seed: 2 } },
];
const ALL_M = ['m1', 'm2', 'm3'];
const ALL_P = ['p1', 'p4', 'p2'];

function scenes(): Scene[] {
  const list: Scene[] = [];
  const S = (s: Scene) => list.push(s);

  // 符文斩：冲到敌人面前，脚下符文阵、剑上蓄光，出手一记青色双斩，命中处炸开暴击
  {
    const rel = INFO.runeSlash.release;
    S({
      id: 'runeSlash', name: '符文斩', duration: 2.4, kind: 'skill', caster: 'p1', targets: ['m1'],
      heroes: party({ slot: 'p1', preset: look.spellblade, top: 'top_rune_armor', anim: clip('slash', rel), travel: dashTo(FEET.m1, FEET.p1, rel) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
      monsters: enemies,
      events: [
        { fx: 'arcane/rune-circle', at: 0.05, where: at('p1'), stop: rel + 0.3, opts: { palette: PAL.rune } },
        { fx: 'arcane/spell-charge', at: 0.2, where: at('p1'), follow: true, stop: rel - 0.05, opts: { palette: PAL.rune } },
        { fx: 'melee/double-slash', at: rel - 0.12, where: at('p1'), opts: { palette: PAL.rune } },
        { fx: 'impacts/crit-hit', at: rel, where: at('m1', -10), opts: { palette: PAL.rune } },
      ],
    });
  }
  // 龙焰：举杖蓄力，张口一道龙息扫过敌群，命中的敌人身上起火
  {
    const rel = INFO.dragonFlame.release;
    S({
      id: 'dragonFlame', name: '龙焰', duration: 2.2, kind: 'skill', caster: 'p1', targets: ALL_M,
      heroes: party({ slot: 'p1', preset: look.dragon, top: 'top_dragon_armor', anim: clip('cast', rel) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
      monsters: enemies,
      events: [
        { fx: 'arcane/spell-charge', at: 0, where: at('p1'), stop: rel, opts: { palette: PAL.fire } },
        { fx: 'fire/fire-breath', at: rel - 0.05, where: at('p1', -28), dx: 12, stop: 1.55, opts: { palette: PAL.fire, spread: 0.32, speed: 380, angle: 0.3 } },
        ...ALL_M.map((m, k) => ({ fx: 'impacts/blunt-hit', at: rel + 0.12 + k * 0.1, where: at(m, -6) }) as FxEvent),
        ...ALL_M.map((m) => ({ fx: 'status/burning', at: rel + 0.3, where: at(m), stop: 2.0 }) as FxEvent),
      ],
    });
  }
  // 星辉脉冲：剑指天空聚起星光，星辰坠向敌群
  {
    const rel = INFO.starlightPulse.release;
    S({
      id: 'starlightPulse', name: '星辉脉冲', duration: 1.9, kind: 'skill', caster: 'p1', targets: ALL_M,
      heroes: party({ slot: 'p1', preset: look.star, top: 'top_starlight_armor', anim: clip('cast', rel) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
      monsters: enemies,
      events: [
        { fx: 'arcane/spell-charge', at: 0, where: at('p1'), stop: rel, opts: { palette: PAL.violet } },
        { fx: 'arcane/star-fall', at: rel - 0.55, where: (s, t) => [{ x: (FEET.m1.x + FEET.m2.x + FEET.m3.x) / 3, y: FEET.m2.y - 4 }], opts: { palette: PAL.violet } },
        ...ALL_M.map((m, k) => ({ fx: 'impacts/hit-spark', at: rel + 0.05 * k, where: at(m, -10), opts: { palette: PAL.violet } }) as FxEvent),
      ],
    });
  }
  // 符文庇护：每位队友脚下亮起符文阵，升起青色护盾
  {
    const rel = INFO.runeWard.release;
    S({
      id: 'runeWard', name: '符文庇护', duration: 2.4, kind: 'skill', caster: 'p1', targets: ALL_P,
      heroes: party({ slot: 'p1', preset: look.spellblade, top: 'top_rune_armor', anim: clip('cast', rel) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
      monsters: enemies,
      events: [
        ...ALL_P.map((p) => ({ fx: 'arcane/rune-circle', at: 0.15, where: at(p), stop: 2.0, opts: { palette: PAL.rune } }) as FxEvent),
        ...ALL_P.map((p, k) => ({ fx: 'our/aegis', at: rel + 0.08 * k, where: at(p), stop: 2.1, opts: { palette: PAL.rune, seed: k } }) as FxEvent),
      ],
    });
  }
  // 战斗符文：施法者脚下金色符文阵，队友身上燃起战意
  {
    const rel = INFO.battleRune.release;
    S({
      id: 'battleRune', name: '战斗符文', duration: 2.1, kind: 'skill', caster: 'p1', targets: ALL_P,
      heroes: party({ slot: 'p1', preset: look.spellblade, top: 'top_rune_armor', anim: clip('cast', rel) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
      monsters: enemies,
      events: [
        { fx: 'arcane/rune-circle', at: 0, where: at('p1'), stop: rel + 0.4, opts: { palette: PAL.amber } },
        ...ALL_P.map((p) => ({ fx: 'status/rage', at: rel, where: at(p), stop: 1.9, opts: { palette: PAL.amber } }) as FxEvent),
      ],
    });
  }
  // 龙鳞庇护：琥珀色的龙鳞护盾罩住队友，同时回血
  {
    const rel = INFO.dragonScaleWard.release;
    S({
      id: 'dragonScaleWard', name: '龙鳞庇护', duration: 2.2, kind: 'skill', caster: 'p1', targets: ALL_P,
      heroes: party({ slot: 'p1', preset: look.dragon, top: 'top_dragon_armor', anim: clip('cast', rel) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
      monsters: enemies,
      events: [
        { fx: 'arcane/spell-charge', at: 0, where: at('p1'), stop: rel, opts: { palette: PAL.amber } },
        ...ALL_P.map((p) => ({ fx: 'holy/heal', at: rel - 0.1, where: at(p), opts: { palette: PAL.amber } }) as FxEvent),
        ...ALL_P.map((p, k) => ({ fx: 'our/aegis', at: rel + 0.1 + 0.08 * k, where: at(p), stop: 2.0, opts: { palette: PAL.amber, seed: k } }) as FxEvent),
      ],
    });
  }
  // 龙之号令：施法者身后一轮红金色的光，三声号令依次点亮队友
  {
    const rel = INFO.dragonOrder.release;
    S({
      id: 'dragonOrder', name: '龙之号令', duration: 2.1, kind: 'skill', caster: 'p1', targets: ALL_P,
      heroes: party({ slot: 'p1', preset: look.dragon, top: 'top_dragon_armor', anim: clip('cast', rel) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
      monsters: enemies,
      events: [
        { fx: 'holy/sunburst', at: 0.15, where: at('p1', -24), behind: true, stop: 1.7, opts: { palette: PAL.crimson } },
        ...ALL_P.map((p, k) => ({ fx: 'holy/blessing', at: rel + 0.3 * k, where: at(p), stop: 1.95, opts: { palette: PAL.crimson } }) as FxEvent),
      ],
    });
  }
  // 振奋：头顶亮起光环，金色的祝福落到每位队友身上
  {
    const rel = INFO.rally.release;
    S({
      id: 'rally', name: '振奋', duration: 2.0, kind: 'skill', caster: 'p1', targets: ALL_P,
      heroes: party({ slot: 'p1', preset: look.ranger, top: 'top_leather_armor', anim: clip('cast', rel) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.adventurer, 'top_leather_armor')),
      monsters: enemies,
      events: [
        { fx: 'holy/halo', at: 0.05, where: at('p1'), stop: 1.2, opts: { palette: PAL.gold } },
        ...ALL_P.map((p) => ({ fx: 'holy/blessing', at: rel, where: at(p), stop: 1.85, opts: { palette: PAL.gold } }) as FxEvent),
      ],
    });
  }

  // ---------------- 命中
  const hitScene = (id: string, name: string, h: Hero, impact: number, tier: Tier, events: FxEvent[], extra: Partial<Scene> = {}): Scene => ({
    id, name, duration: 1.7, kind: 'hit', caster: h.slot, targets: ['m1'], heroes: party(h, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
    monsters: enemies, events, hit: { at: impact, tier, target: 'm1', dir: 1 }, ...extra,
  });
  const I = 0.75;
  S(hitScene('hitBlade', '剑命中', { slot: 'p1', preset: look.adventurer, top: 'top_leather_armor', anim: clip('slash', I, 1 / 13), travel: dashTo(FEET.m1, FEET.p1, I, 0.5) }, I, 'medium', [
    { fx: 'melee/sword-slash', at: I - 0.12, where: at('p1'), opts: { palette: PAL.steel } },
    { fx: 'impacts/hit-spark', at: I, where: at('m1', -10), opts: { palette: PAL.steel } },
  ]));
  S(hitScene('hitGreat', '重剑命中', { slot: 'p1', preset: look.heavy, top: 'top_rune_armor', anim: clip('heavy', I, 1 / 13), travel: dashTo(FEET.m1, FEET.p1, I, 0.5) }, I, 'heavy', [
    { fx: 'melee/heavy-cleave', at: I - 0.25, where: at('p1'), opts: { palette: PAL.steel } },
    { fx: 'impacts/blunt-hit', at: I, where: at('m1', -6) },
  ]));
  S(hitScene('hitBow', '箭命中', { slot: 'p1', preset: look.ranger, top: 'top_leather_armor', anim: clip('shoot', 0.55) }, I, 'light', [
    { fx: 'projectiles/arrow', at: 0.55, stop: I, follow: true, where: (s, t) => {
      const k = clamp01((t - 0.55) / (I - 0.55)), a = footOf(s, 'p1', t), b = footOf(s, 'm1', t);
      return [{ x: a.x + 14 + (b.x - a.x - 22) * k, y: a.y - 30 + (b.y - a.y + 18) * k - Math.sin(k * Math.PI) * 6 }];
    } },
    { fx: 'impacts/hit-spark', at: I, where: at('m1', -12), opts: { palette: PAL.gold } },
  ]));
  S(hitScene('hitStaff', '法杖命中', { slot: 'p1', preset: look.mage, top: 'top_rune_armor', anim: clip('cast', 0.5) }, I + 0.1, 'medium', [
    { fx: 'projectiles/magic-missile', at: 0.45, where: at('p1', -30), opts: { palette: PAL.magenta, reach: (FEET.m1.x - FEET.p1.x) - 8, height: -2 } },
    { fx: 'arcane/mana-burst', at: I + 0.1, where: at('m1'), opts: { palette: PAL.magenta } },
  ]));
  S(hitScene('hitAmbush', '突袭命中', { slot: 'p1', preset: look.adventurer, top: 'top_leather_armor', anim: clip('dash', I, 1 / 13), travel: dashTo(FEET.m1, FEET.p1, I, 0.5) }, I, 'heavy', [
    { fx: 'melee/thrust', at: I - 0.15, where: at('p1'), opts: { palette: PAL.gold } },
    { fx: 'impacts/crit-hit', at: I, where: at('m1', -10), opts: { palette: PAL.gold } },
  ]));
  // 怪物打人：爪击落在英雄身上，英雄受击闪白
  S({
    id: 'hitClaw', name: '爪击（怪物打人）', duration: 1.7, kind: 'hit', caster: 'm1', targets: ['p1'],
    heroes: party({ slot: 'p1', preset: look.adventurer, top: 'top_leather_armor', anim: (t) => (t >= I && t < I + 6 / 12 ? CLIP_FRAMES.hurt[Math.floor((t - I) * 12)] : readyLoop(t)) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
    monsters: enemies,
    events: [
      { fx: 'melee/claw-swipe', at: I - 0.2, where: (s, t) => [{ x: FEET.p1.x + 26, y: FEET.p1.y }], opts: { flip: true } },
      { fx: 'impacts/hit-spark', at: I, where: at('p1', -14), opts: { flip: true } },
    ],
    hit: { at: I, tier: 'medium', target: 'p1', dir: -1 },
  });
  // 打在护盾上：英雄格挡，护盾闪出火花挡下
  S({
    id: 'hitWard', name: '护盾挡下', duration: 1.7, kind: 'hit', caster: 'm1', targets: ['p1'],
    heroes: party({ slot: 'p1', preset: look.heavy, top: 'top_rune_armor', anim: (t) => (t >= I - 0.05 && t < I + 0.5 ? CLIP_FRAMES.guard[t < I + 0.15 ? 0 : 1] : readyLoop(t)) }, ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')),
    monsters: enemies,
    events: [
      { fx: 'our/aegis', at: 0, where: at('p1'), stop: 1.5, opts: { palette: PAL.ice, form: 0, hitAt: I, hitAngle: -0.3 } },
      { fx: 'melee/claw-swipe', at: I - 0.2, where: (s, t) => [{ x: FEET.p1.x + 36, y: FEET.p1.y }], opts: { flip: true } },
    ],
    hit: { at: I, tier: 'light', target: 'p1', dir: -1 },
  });

  // ================================================================ 其余特效
  const hurtAt = (at: number, h: Hero): Hero => ({ ...h, anim: (t) => (t >= at && t < at + 6 / 12 ? CLIP_FRAMES.hurt[Math.floor((t - at) * 12)] : readyLoop(t)) });
  const defeat = CLIP_FRAMES.defeat, lying = defeat[defeat.length - 1];
  const fallAt = (at: number) => (t: number) => (t < at ? readyLoop(t) : t < at + 0.06 ? CLIP_FRAMES.hurt[0] : defeat[Math.min(defeat.length - 1, Math.floor((t - at - 0.06) * 10))]);
  const allies = (): [Hero, Hero] => [ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')];
  const p1 = (preset: CharacterPreset, top: string, anim?: (t: number) => number, travel?: (t: number) => number): Hero => ({ slot: 'p1', preset, top, anim: anim ?? readyLoop, travel });
  /** 怪物占位：游戏里是自己的怪物图，这里用 pixelfx 的小怪代替，m1 换成对应的那只 */
  const STAND: Record<string, Monster> = {
    slime: { slot: 'm1', fx: 'critters/slime', opts: { palette: PAL.goo.slice(0, 6) }, edge: '#d0ffc0' },
    wolf: { slot: 'm1', fx: 'critters/bat', opts: { palette: ['#0e0c10', '#24202a', '#403a48', '#605a6a', '#8a8494', '#b8b4c0', '#e8e6ee'], hover: 18 }, edge: '#ffe0a0' },
    goblin: { slot: 'm1', fx: 'critters/eyeball', opts: { seed: 3 }, edge: '#ffd0a0' },
    stone: { slot: 'm1', fx: 'critters/slime', opts: { palette: ['#141418', '#2e2e38', '#4e4e5c', '#76768a', '#a0a0b4', '#d0d0e0'], hop: 6, seed: 7 }, edge: '#f0f0ff' },
    troll: { slot: 'm1', fx: 'critters/ghost', opts: { palette: ['#0c1a10', '#1a3420', '#2e5a34', '#4e8a50', '#80b878', '#c0e0b0', '#ffffff'], hover: 6, seed: 5 }, edge: '#e0ffc0' },
    dragon: { slot: 'm1', fx: 'critters/flying-skull', opts: { seed: 2 }, edge: '#ffd890' },
  };
  const foes = (m1: Monster, extra: Partial<Monster> = {}) => [{ ...m1, ...extra }, enemies[1], enemies[2]];

  // ---- 护盾
  {
    const rel = INFO.dragonSoulWard.release;
    S({
      id: 'dragonSoulWard', name: '龙魂守护', duration: 2.0, kind: 'skill', caster: 'p1', targets: ALL_P,
      heroes: party(p1(look.dragon, 'top_dragon_armor', clip('cast', rel)), ...allies()),
      monsters: enemies,
      events: [
        { fx: 'arcane/spell-charge', at: 0, where: at('p1'), stop: rel, opts: { palette: PAL.ice } },
        { fx: 'holy/feather-burst', at: rel, where: at('p1', -20), opts: { palette: PAL.ice } },
        ...ALL_P.map((p, k) => ({ fx: 'our/aegis', at: rel + 0.06 * k, where: at(p), stop: 1.8, opts: { palette: PAL.ice, rx: 18, ry: 24, form: 0.3, seed: k } }) as FxEvent),
      ],
    });
  }
  {
    const rel = INFO.shieldDome.release;
    S({
      id: 'shieldDome', name: '护盾（防御 / 护盾药水）', duration: 1.9, kind: 'skill', caster: 'p1', targets: ['p1'],
      heroes: party(p1(look.heavy, 'top_rune_armor', (t) => (t >= rel - 0.1 && t < 1.5 ? CLIP_FRAMES.guard[t < rel + 0.1 ? 0 : 1] : readyLoop(t))), ...allies()),
      monsters: enemies,
      events: [{ fx: 'our/aegis', at: rel - 0.2, where: at('p1'), stop: 1.7, opts: { palette: PAL.ice } }],
    });
  }
  S({
    id: 'shieldShell', name: '护盾持续', duration: 3.0, kind: 'skill', caster: 'p1', targets: ['p1'],
    heroes: party(p1(look.heavy, 'top_rune_armor'), ...allies()), monsters: enemies,
    events: [{ fx: 'our/aegis', at: 0, where: at('p1'), stop: 2.8, opts: { palette: PAL.ice, form: 0.5 } }],
  });
  S({
    id: 'shieldShellHit', name: '护盾挨打', duration: 2.2, kind: 'hit', caster: 'm1', targets: ['p1'], cue: 'shieldShellHit',
    heroes: party(p1(look.heavy, 'top_rune_armor', (t) => (t >= I - 0.05 && t < I + 0.5 ? CLIP_FRAMES.guard[t < I + 0.15 ? 0 : 1] : readyLoop(t))), ...allies()),
    monsters: foes(STAND.wolf),
    events: [
      { fx: 'our/aegis', at: 0, where: at('p1'), stop: 2.0, opts: { palette: PAL.ice, form: 0, hitAt: I, hitAngle: -0.35 } },
      { fx: 'melee/claw-swipe', at: I - 0.2, where: () => [{ x: FEET.p1.x + 36, y: FEET.p1.y }], opts: { flip: true } },
    ],
    hit: { at: I, tier: 'light', target: 'p1', dir: -1 },
  });
  S({
    id: 'shieldBreak', name: '护盾被打碎', duration: 1.9, kind: 'hit', caster: 'm1', targets: ['p1'], cueAt: I,
    heroes: party(hurtAt(I, p1(look.heavy, 'top_rune_armor')), ...allies()),
    monsters: foes(STAND.troll),
    events: [
      { fx: 'our/aegis', at: 0, where: at('p1'), stop: 1.8, opts: { palette: PAL.ice, form: 0, breakAt: I } },
      { fx: 'impacts/blunt-hit', at: I, where: at('p1', -14), opts: { flip: true } },
    ],
    hit: { at: I, tier: 'heavy', target: 'p1', dir: -1 },
  });

  // ---- 治疗 / 增益 / 倒地 / 复活
  S({
    id: 'healMicro', name: '小治疗', duration: 1.35, kind: 'skill', caster: 'p4', targets: ['p1'],
    heroes: party(p1(look.adventurer, 'top_leather_armor'), ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')), monsters: enemies,
    events: [{ fx: 'holy/heal', at: 0.05, where: at('p1'), opts: { palette: PAL.heal } }],
  });
  S({
    id: 'healStandard', name: '治疗', duration: 1.8, kind: 'skill', caster: 'p4', targets: ['p1'],
    heroes: party(p1(look.adventurer, 'top_leather_armor'), ally('p4', look.mage, 'top_rune_armor'), ally('p2', look.ranger, 'top_leather_armor')), monsters: enemies,
    events: [
      { fx: 'nature/healing-bloom', at: 0, where: at('p1') },
      { fx: 'holy/heal', at: 0.25, where: at('p1'), opts: { palette: PAL.heal } },
    ],
  });
  S({
    id: 'healStrong', name: '大治疗（全队）', duration: 2.3, kind: 'skill', caster: 'p4', targets: ALL_P,
    heroes: party(p1(look.adventurer, 'top_leather_armor'), { slot: 'p4', preset: look.mage, top: 'top_rune_armor', anim: clip('cast', 0.15) }, ally('p2', look.ranger, 'top_leather_armor')), monsters: enemies,
    events: [
      { fx: 'holy/heal-aoe', at: 0, where: () => [{ x: (FEET.p1.x + FEET.p2.x + FEET.p4.x) / 3, y: FEET.p1.y + 6 }], opts: { reach: 70 } },
      ...ALL_P.map((p, k) => ({ fx: 'holy/heal', at: 0.35 + 0.1 * k, where: at(p), opts: { palette: PAL.heal } }) as FxEvent),
    ],
  });
  S({
    id: 'buffAura', name: '增益光环（持续）', duration: 3.0, kind: 'skill', caster: 'p1', targets: ['p1'],
    heroes: party(p1(look.heavy, 'top_rune_armor'), ...allies()), monsters: enemies,
    events: [
      { fx: 'status/rage', at: 0.3, where: at('p1'), stop: 2.7, opts: { palette: PAL.fury } },
      { fx: 'holy/blessing', at: 0.3, where: at('p1'), opts: { palette: PAL.fury } },
    ],
  });
  S({
    id: 'playerDown', name: '英雄倒地', duration: 2.4, kind: 'hit', caster: 'm1', targets: ['p1'], cueAt: I, dir: -1,
    heroes: party({ ...p1(look.adventurer, 'top_leather_armor'), anim: fallAt(I) }, ...allies()),
    monsters: foes(STAND.troll),
    events: [
      { fx: 'impacts/blunt-hit', at: I, where: at('p1', -14), opts: { flip: true } },
      { fx: 'impacts/hit-spark', at: I, where: at('p1', -14), opts: { flip: true } },
      { fx: 'impacts/heavy-landing', at: I + 0.5, where: at('p1') },
      { fx: 'spawn/poof', at: I + 0.5, where: at('p1'), opts: { palette: PAL.down } },
    ],
    hit: { at: I, tier: 'heavy', target: 'p1', dir: -1 },
  });
  S({
    id: 'downAura', name: '倒地等待复活（持续）', duration: 3.0, kind: 'skill', caster: 'p1', targets: ['p1'],
    heroes: party({ ...p1(look.adventurer, 'top_leather_armor'), anim: () => lying }, ...allies()), monsters: enemies,
    events: [
      { fx: 'arcane/rune-circle', at: 0.2, where: at('p1'), stop: 2.8, opts: { palette: PAL.gold } },
      { fx: 'pickups/crystal-shard', at: 0.5, where: at('p1', -14), stop: 2.8, opts: { palette: PAL.gold } },
    ],
  });
  S({
    id: 'revive', name: '复活', duration: 2.2, kind: 'skill', caster: 'p1', targets: ['p1'], cueAt: 0.2,
    heroes: party({ ...p1(look.adventurer, 'top_leather_armor'), anim: (t) => (t < 0.75 ? lying : t < 0.75 + defeat.length / 10 ? defeat[defeat.length - 1 - Math.floor((t - 0.75) * 10)] : t < 1.6 ? CLIP_FRAMES.victory[Math.floor(t * 4) % 2] : readyLoop(t)) }, ...allies()),
    monsters: enemies,
    events: [
      { fx: 'holy/holy-pillar', at: 0.2, where: at('p1'), stop: 1.3, opts: { palette: PAL.gold } },
      { fx: 'holy/feather-burst', at: 0.75, where: at('p1', -18), opts: { palette: PAL.gold } },
      { fx: 'holy/heal', at: 1.0, where: at('p1'), opts: { palette: PAL.gold.concat('#ffffff') } },
    ],
  });

  // ---- 攻击：横扫、天命 20、远程飞行物
  {
    const rel = INFO.sweep.release;
    S({
      id: 'sweep', name: '横扫（全体）', duration: 2.0, kind: 'skill', caster: 'p1', targets: ALL_M,
      heroes: party(p1(look.heavy, 'top_rune_armor', clip('heavy', rel), dashTo(FEET.m3, FEET.p1, rel)), ...allies()),
      monsters: enemies,
      events: [
        { fx: 'melee/heavy-cleave', at: rel - 0.28, where: at('p1'), opts: { palette: PAL.sweep } },
        { fx: 'melee/spin-slash', at: rel - 0.05, where: () => [{ x: (FEET.m1.x + FEET.m2.x + FEET.m3.x) / 3, y: FEET.m1.y + 12 }], opts: { palette: PAL.sweep } },
        ...ALL_M.map((m, k) => ({ fx: 'impacts/hit-spark', at: rel + 0.04 * k, where: at(m, -10), opts: { palette: PAL.sweep } }) as FxEvent),
      ],
    });
  }
  S({
    id: 'natural20', name: '天命 20（暴击结算）', duration: 3.4, kind: 'skill', caster: 'p1', targets: ['m1'], cueAt: I,
    heroes: party(p1(look.star, 'top_starlight_armor', clip('slash', I, 1 / 13), dashTo(FEET.m1, FEET.p1, I, 0.9)), ...allies()),
    monsters: foes(STAND.dragon, { dieAt: I + 1.2, death: 'burst' }),
    events: [
      { fx: 'holy/sunburst', at: I, where: at('m1', -18), behind: true, stop: I + 1.8, opts: { palette: PAL.gold } },
      { fx: 'melee/sword-slash', at: I - 0.12, where: at('p1'), opts: { palette: PAL.gold } },
      { fx: 'impacts/crit-hit', at: I, where: at('m1', -12), opts: { palette: PAL.gold } },
      { fx: 'ui/crit-number', at: I + 0.1, where: at('m1', -44), opts: { text: '20!', label: 'NAT', palette: PAL.gold.concat('#ffffff') } },
      { fx: 'explosions/small-explosion', at: I + 1.2, where: at('m1'), stop: I + 2.4, opts: { size: 0.6 } },
    ],
    hit: { at: I, tier: 'heavy', target: 'm1', dir: 1 },
  });
  /** 飞行物：from → to 的抛物线（像素），k = 0..1 */
  const fly = (from: string, to: string, t0: number, t1: number, arc = 6, lift = 26) => (s: Scene, t: number) => {
    const k = clamp01((t - t0) / (t1 - t0)), a = footOf(s, from, t), b = footOf(s, to, t), sgn = Math.sign(b.x - a.x);
    return [{ x: a.x + sgn * 12 + (b.x - a.x - sgn * 22) * k, y: a.y - lift + (b.y - a.y + lift - 14) * k - Math.sin(k * Math.PI) * arc }];
  };
  {
    const L = 0.5, A = L + 0.19;
    S({
      id: 'projBow', name: '箭（飞行）', duration: 1.5, kind: 'hit', caster: 'p1', targets: ['m1'], cueAt: L,
      heroes: party(p1(look.ranger, 'top_leather_armor', clip('shoot', L)), ...allies()), monsters: enemies,
      events: [
        { fx: 'projectiles/arrow', at: L, stop: A, follow: true, where: fly('p1', 'm1', L, A, 4, 30) },
        { fx: 'impacts/hit-spark', at: A, where: at('m1', -12), opts: { palette: PAL.gold } },
      ],
      hit: { at: A, tier: 'light', target: 'm1', dir: 1 },
    });
  }
  {
    const L = 0.3, F = L + 0.49, A = F + 0.21;
    S({
      id: 'projStaff', name: '法球（蓄力 + 飞行）', duration: 1.7, kind: 'hit', caster: 'p1', targets: ['m1'], cueAt: L,
      heroes: party(p1(look.mage, 'top_rune_armor', clip('cast', F)), ...allies()), monsters: enemies,
      events: [
        { fx: 'arcane/spell-charge', at: L, where: at('p1'), stop: F, opts: { palette: PAL.magenta } },
        { fx: 'projectiles/plasma-shot', at: F, stop: A, follow: true, where: fly('p1', 'm1', F, A, 2, 32), opts: { palette: PAL.magenta.concat('#ffffff') } },
        { fx: 'arcane/mana-burst', at: A, where: at('m1'), opts: { palette: PAL.magenta } },
      ],
      hit: { at: A, tier: 'medium', target: 'm1', dir: 1 },
    });
  }
  {
    const L = 0.5, A = L + 0.22;
    S({
      id: 'projArcher', name: '怪物射箭', duration: 1.6, kind: 'hit', caster: 'm1', targets: ['p1'], cueAt: L,
      heroes: party(hurtAt(A, p1(look.adventurer, 'top_leather_armor')), ...allies()), monsters: foes(STAND.goblin),
      events: [
        { fx: 'projectiles/arrow', at: L, stop: A, follow: true, where: fly('m1', 'p1', L, A, 4, 22), opts: { flip: true } },
        { fx: 'impacts/hit-spark', at: A, where: at('p1', -14), opts: { flip: true } },
      ],
      hit: { at: A, tier: 'light', target: 'p1', dir: -1 },
    });
    S({
      id: 'projDragon', name: '怪物吐火球', duration: 1.8, kind: 'hit', caster: 'm1', targets: ['p1'], cueAt: L,
      heroes: party(hurtAt(A, p1(look.adventurer, 'top_leather_armor')), ...allies()), monsters: foes(STAND.dragon),
      events: [
        { fx: 'fire/fireball', at: L, stop: A, follow: true, where: fly('m1', 'p1', L, A, 3, 26), opts: { flip: true, radius: 4 } },
        { fx: 'impacts/blunt-hit', at: A, where: at('p1', -14), opts: { flip: true } },
        { fx: 'status/burning', at: A, where: at('p1'), stop: 1.5 },
      ],
      hit: { at: A, tier: 'medium', target: 'p1', dir: -1 },
    });
  }

  // ---- 怪物打人
  const monsterHit = (id: string, name: string, who: Monster, tier: Tier, events: FxEvent[], duration = 1.7): Scene => ({
    id, name, duration, kind: 'hit', caster: 'm1', targets: ['p1'],
    heroes: party(hurtAt(I, p1(look.adventurer, 'top_leather_armor')), ...allies()), monsters: foes(who), events,
    hit: { at: I, tier, target: 'p1', dir: -1 },
  });
  const onP1 = (dx = 0, dy = 0) => () => [{ x: FEET.p1.x + dx, y: FEET.p1.y + dy }];
  S(monsterHit('hitSlime', '史莱姆撞击', STAND.slime, 'light', [
    { fx: 'nature/acid-splash', at: I - 0.05, where: onP1(4), opts: { flip: true } },
    { fx: 'impacts/hit-spark', at: I, where: at('p1', -14), opts: { flip: true } },
  ]));
  S(monsterHit('hitWolf', '狼连爪', STAND.wolf, 'medium', [
    { fx: 'melee/claw-swipe', at: I - 0.42, where: onP1(26), opts: { flip: true } },
    { fx: 'melee/claw-swipe', at: I - 0.2, where: onP1(24, -4), opts: { flip: true, seed: 5 } },
    { fx: 'impacts/hit-spark', at: I, where: at('p1', -14), opts: { flip: true } },
  ]));
  S(monsterHit('hitArrowM', '箭射中英雄', STAND.goblin, 'light', [
    { fx: 'projectiles/arrow', at: I - 0.25, stop: I, follow: true, where: fly('m1', 'p1', I - 0.25, I, 4, 22), opts: { flip: true } },
    { fx: 'impacts/hit-spark', at: I, where: at('p1', -14), opts: { flip: true } },
  ]));
  S(monsterHit('hitStone', '石像重拳', STAND.stone, 'heavy', [
    { fx: 'impacts/blunt-hit', at: I, where: at('p1', -12), opts: { flip: true } },
    { fx: 'impacts/heavy-landing', at: I, where: at('p1') },
  ]));
  S(monsterHit('hitTroll', '巨魔砸地', STAND.troll, 'heavy', [
    { fx: 'impacts/ground-slam', at: I - 0.1, where: onP1(10), stop: 1.6, opts: { flip: true, reach: 50 } },
    { fx: 'impacts/blunt-hit', at: I, where: at('p1', -12), opts: { flip: true } },
  ], 1.9));
  S(monsterHit('hitDragon', '龙爪 + 火', STAND.dragon, 'heavy', [
    { fx: 'melee/claw-swipe', at: I - 0.2, where: onP1(26), opts: { flip: true, palette: PAL.fire } },
    { fx: 'explosions/small-explosion', at: I, where: onP1(-2), stop: 1.5, opts: { size: 0.45 } },
  ], 1.9));

  // ---- 怪物死亡（先挨一下，再死）
  const death = (id: string, name: string, who: Monster, style: Death, events: FxEvent[], duration = 2.2, hero: Hero = p1(look.adventurer, 'top_leather_armor', clip('slash', I, 1 / 13), dashTo(FEET.m1, FEET.p1, I, 0.5))): Scene => ({
    id, name, duration, kind: 'hit', caster: 'p1', targets: ['m1'], cueAt: I + 0.1,
    heroes: party(hero, ...allies()), monsters: foes(who, { dieAt: I + 0.1, death: style }),
    events: [{ fx: 'impacts/hit-spark', at: I, where: at('m1', -10), opts: { palette: PAL.steel } }, ...events],
    hit: { at: I, tier: 'medium', target: 'm1', dir: 1 },
  });
  const onM1 = (dy = 0) => at('m1', dy);
  S(death('deathSlime', '史莱姆死亡', STAND.slime, 'melt', [
    { fx: 'nature/acid-splash', at: I + 0.1, where: onM1(), opts: { palette: PAL.goo.concat('#ffffff') } },
  ]));
  S(death('deathWolf', '狼死亡', STAND.wolf, 'dust', [
    { fx: 'spawn/poof', at: I + 0.35, where: onM1() },
  ]));
  S(death('deathGoblin', '哥布林死亡', STAND.goblin, 'dust', [
    { fx: 'spawn/poof', at: I + 0.3, where: onM1() },
    { fx: 'spawn/coin-drop', at: I + 0.45, where: onM1() },
  ]));
  S(death('deathStone', '石像死亡（碎裂）', STAND.stone, 'shatter', [
    { fx: 'impacts/heavy-landing', at: I + 0.55, where: onM1() },
  ], 2.4));
  S(death('deathTroll', '巨魔死亡（倒塌）', STAND.troll, 'crumble', [
    { fx: 'impacts/heavy-landing', at: I + 0.45, where: onM1() },
    { fx: 'spawn/poof', at: I + 0.5, where: onM1() },
  ]));
  S(death('deathDragon', '龙死亡（爆开）', STAND.dragon, 'burst', [
    { fx: 'explosions/small-explosion', at: I + 0.1, where: onM1(), stop: I + 1.9, opts: { size: 0.8 } },
    { fx: 'holy/feather-burst', at: I + 0.4, where: onM1(-20), opts: { palette: PAL.fire } },
  ], 2.9));
  S(death('deathBurst', '通用死亡', { ...enemies[0], edge: '#d0ffc0' }, 'dust', [
    { fx: 'spawn/poof', at: I + 0.15, where: onM1() },
  ]));
  return list;
}

// ---------------------------------------------------------------- 怪物死亡（拿怪物自己的像素做消散，形状才对）

const hash = (x: number, y: number, k = 0) => { const v = Math.sin(x * 127.1 + y * 311.7 + k * 74.7) * 43758.5453; return v - Math.floor(v); };
let scratch: ReturnType<typeof createFrame> | null = null;
function dying(frame: ReturnType<typeof createFrame>, m: Monster & { inst: { draw(f: unknown, l?: string): void } }, r: number, foot: Pt): void {
  scratch ??= createFrame(W, H);
  clearFrame(scratch);
  m.inst.draw(scratch, 'back'); m.inst.draw(scratch, 'front');
  const rgba = composite(scratch, new Uint8ClampedArray(W * H * 4), null);
  const style = m.death ?? 'dust';
  const len = style === 'shatter' ? 1.1 : style === 'melt' ? 0.9 : 0.75;
  const k = clamp01(r / len);
  const e = m.edge ?? '#ffe0a0';
  const edge = (parseInt(e.slice(1, 3), 16) | (parseInt(e.slice(3, 5), 16) << 8) | (parseInt(e.slice(5, 7), 16) << 16) | (255 << 24)) >>> 0;
  const put = (X: number, Y: number, c: number) => {
    X = Math.round(X); Y = Math.round(Y);
    if (X < 0 || Y < 0 || X >= W || Y >= H) return;
    frame.color[Y * W + X] = c;
  };
  const toC = (o: number) => ((rgba[o] | (rgba[o + 1] << 8) | (rgba[o + 2] << 16) | (255 << 24)) >>> 0);
  const flash = r < 0.08;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const o = (y * W + x) * 4;
    if (rgba[o + 3] < 40) continue;
    const c = flash ? 0xffffffff : toC(o);
    const ly = foot.y - y, lx = x - foot.x; // 离地高度、离中心
    if (style === 'shatter') {
      // 碎成 3×3 的块：往外飞、受重力落地（crumble = 原地塌下去）
      const bx = Math.floor(x / 3), by = Math.floor(y / 3), h1 = hash(bx, by), h2 = hash(bx, by, 1);
      const start = 0.05 + h1 * 0.1;
      const q = Math.max(0, r - start);
      if (q > 0 && q > 0.75 + h2 * 0.4) continue;
      const vx = (lx / 8 + (h1 - 0.5) * 2) * 26, vy = -30 - h2 * 40;
      const yy = Math.min(foot.y - 1 - h2 * 2, y + vy * q + 160 * q * q);
      put(x + vx * q, yy, q > 0 && q < 0.06 ? edge : c);
    } else if (style === 'melt' || style === 'crumble') {
      // melt：化成一滩（往下塌、越往下越宽）；crumble：整个往下沉、往前栽（巨魔倒地）
      const sink = style === 'melt' ? k * k : k ** 1.6;
      const spread = style === 'melt' ? 0.9 : 0.25;
      const yy = foot.y - ly * (1 - sink * (style === 'melt' ? 1 : 0.75)), xx = foot.x + lx * (1 + sink * spread) - (style === 'crumble' ? sink * ly * 0.3 : 0);
      // 塌到一半以后才开始抖动消失
      const fade = clamp01((r - len * 0.6) / (len * 0.9));
      if (fade > 0 && hash(x, y) < fade) continue;
      // 横向拉宽后每个像素填满它占的宽度，不留竖条缝
      const wpx = 1 + sink * spread;
      for (let q = 0; q < Math.ceil(wpx) + 1; q++) put(xx + (lx >= 0 ? q : -q) * 0.999, yy, c);
    } else {
      // 灰化：噪声消散，消散前沿一圈亮边，碎屑往上飘
      const n = hash(x, y) * 0.7 + (ly / 40) * 0.3;
      const p = k * 1.1;
      if (n < p - 0.08) {
        if (n > p - 0.3 && hash(x, y, 2) < 0.25) put(x + Math.sin(y + r * 6) * 2, y - (p - n) * 60, style === 'burst' ? 0xffffffff : edge);
        continue;
      }
      put(x, y, n < p ? edge : c);
    }
  }
}

// ---------------------------------------------------------------- 渲染

async function render(s: Scene): Promise<void> {
  const frame = createFrame(W, H);
  const n = Math.round(s.duration * FPS);
  const live: { ev: FxEvent; inst: { update(dt: number): void; draw(f: unknown, l?: string): void; stop(): void; done(): boolean; options: Record<string, unknown> }; i: number }[] = [];
  const spawned = new Set<FxEvent>();
  const monsters = await Promise.all(s.monsters.map(async (m) => ({ ...m, inst: (createFx as Function)(await mod(m.fx), { ...m.opts, flip: true, x: FEET[m.slot].x, y: FEET[m.slot].y }) })));
  const bytes = new Uint8Array(W * H * 4 * n);
  const meta: Record<string, unknown>[] = [];
  let effT = 0; // 效果时间：命中顿帧时停住
  const dt = 1 / FPS;
  for (let f = 0; f < n; f++) {
    const t = f * dt;
    const frozen = s.hit ? t >= s.hit.at && t < s.hit.at + HOLD : false;
    const step = frozen ? 0 : dt;
    // 生成到点的特效
    for (const ev of s.events) {
      if (spawned.has(ev) || t + 1e-6 < ev.at) continue;
      spawned.add(ev);
      const m = await mod(ev.fx);
      const on = (ev.where as { slot?: string }).slot, hero = on ? s.heroes.find((x) => x.slot === on) : undefined;
      const actor = hero ? actorOf(hero, (hero.anim ?? readyLoop)(t), !!ev.opts?.flip, (ev.where as { dy: number }).dy + (ev.dy ?? 0)) : undefined;
      ev.where(s, t).forEach((p, i) => live.push({ ev, i, inst: (createFx as Function)(m, { ...ev.opts, ...(actor ? { actor } : {}), x: p.x + (ev.dx ?? 0), y: p.y + (ev.dy ?? 0) }) }));
    }
    clearFrame(frame);
    for (const m of monsters) {
      const p = footOf(s, m.slot, t);
      m.inst.options.x = p.x; m.inst.options.y = p.y;
      if (m.dieAt !== undefined && t >= m.dieAt) dying(frame, m, t - m.dieAt, p);
      else m.inst.draw(frame, 'back');
    }
    for (const l of live) {
      if (l.ev.follow) { const p = l.ev.where(s, t)[l.i]; l.inst.options.x = p.x; l.inst.options.y = p.y; }
      const on = (l.ev.where as { slot?: string; dy?: number }).slot, hero = on ? s.heroes.find((x) => x.slot === on) : undefined;
      if (hero) l.inst.options.actor = actorOf(hero, (hero.anim ?? readyLoop)(frozen && s.hit ? s.hit.at : t), !!l.inst.options.flip, (l.ev.where as { dy: number }).dy + (l.ev.dy ?? 0));
      l.inst.draw(frame, l.ev.behind ? undefined : 'back');
    }
    for (const m of monsters) if (m.dieAt === undefined || t < m.dieAt) m.inst.draw(frame, 'front');
    // 人物（按脚的前后排序）
    const heroes = [...s.heroes].sort((a, b) => FEET[a.slot].y - FEET[b.slot].y);
    for (const h of heroes) {
      const col = (h.anim ?? readyLoop)(frozen && s.hit ? s.hit.at : t);
      const rgba = heroFrame(h, col);
      const foot = footOf(s, h.slot, t);
      const x0 = Math.round(foot.x - FOOT.x), y0 = Math.round(foot.y - FOOT.y);
      for (let y = 0; y < SPR_H; y++) for (let x = 0; x < SPR_W; x++) {
        const o = (y * SPR_W + x) * 4;
        if (!rgba[o + 3]) continue;
        const X = x0 + x, Y = y0 + y;
        if (X < 0 || Y < 0 || X >= W || Y >= H) continue;
        frame.color[Y * W + X] = (rgba[o] | (rgba[o + 1] << 8) | (rgba[o + 2] << 16) | (255 << 24)) >>> 0;
      }
    }
    for (const l of live) if (!l.ev.behind) l.inst.draw(frame, 'front');
    const rgba = composite(frame, new Uint8ClampedArray(W * H * 4), null);
    bytes.set(rgba, f * W * H * 4);
    // 推进
    for (const m of monsters) m.inst.update(step);
    for (const l of live) {
      if (l.ev.stop !== undefined && t >= l.ev.stop) l.inst.stop();
      l.inst.update(step);
    }
    for (let i = live.length - 1; i >= 0; i--) if (live[i].inst.done()) live.splice(i, 1);
    effT += step;

    // 镜头
    const dir = s.dir ?? (s.hit ? s.hit.dir : 1);
    let cam = ZERO, dim = 0, tint: [number, number, number] = [1, 1, 1], sh = { fx: 500, fy: 300, w: 0, zoom: 0 };
    const cue = s.cue ?? s.id, ct = t - (s.cueAt ?? 0);
    if (INFO[cue]) {
      cam = add(skillCamera(cue, ct, dir), shake(trauma(cue, ct), t));
      const i = INFO[cue];
      if (!isBlow(cue)) { dim = i.dim * ambient(cue, ct); tint = i.tint; }
      const toStage = (slot: string) => ({ x: FEET[slot].x * U, y: (FEET[slot].y - 22) * U });
      sh = shot(cue, ct, toStage(s.caster), s.targets.map(toStage));
    }
    if (s.hit) cam = add(cam, hitCamera(t - s.hit.at, s.hit.tier, dir));
    meta.push({ t, dx: cam.dx / U, dy: cam.dy / U, zoom: cam.zoom + sh.zoom, rot: cam.rot, fx: sh.fx / U, fy: sh.fy / U, w: sh.w, dim, tint });
  }
  writeFileSync(`${outDir}/${s.id}.rgba`, bytes);
  writeFileSync(`${outDir}/${s.id}.json`, JSON.stringify({ id: s.id, name: s.name, w: W, h: H, fps: FPS, n, frames: meta }));
  console.log(`${s.id} ${s.name}: ${n} frames`);
}

const only = process.argv[3]?.split(',');
for (const s of scenes()) if (!only || only.includes(s.id)) await render(s);
