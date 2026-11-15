/**
 * 游戏内烘焙入口：打包成一个独立的 JS 文件（npm run runtime），iPad 端用 JavaScriptCore 执行，
 * 和网页制作工具是同一份代码，画出来的像素完全一致，不需要再手工移植到 Swift。
 *
 * 全局对象 PixelBaker：
 *   info()              → JSON：帧尺寸、每方向帧数、动画列号、发型 / 五官 / 装备清单
 *   bake(specJSON)      → Uint8Array：RGBA。spec.dirs × spec.frames 排成 行 × 列（不写 = 5 个方向 × 全部帧）。
 *                         游戏里只烘需要的部分：地图要 5 个方向的待机 + 行走，战斗只要右侧的战斗帧。
 *                         没有 JIT 的 JavaScriptCore 里一整张约 2.5 秒，只烘需要的帧约 1 秒，结果缓存到磁盘。
 *   bakeFx(specJSON)    → Uint8Array：装备特效叠加层（4 相位），没有特效时长度 0
 *   feet(holdOrEmpty)   → JSON：每个方向每一帧两只脚的像素坐标（地图投影 / 战斗落脚点用）
 *   anchors(specJSON)   → JSON：战斗用的发射点（弓弦、法杖宝珠）在各帧的像素坐标
 */
import { PixelLayer } from './pixel/PixelLayer';
import { composeFrame } from './character/paperdoll';
import { Equipment } from './character/equipment';
import {
  ACTION_FRAMES, CX, DIRS5, FOOT_Y, FRAMES_PER_DIR, IDLE_FRAMES, READY_FRAMES, SPRITE_SCALE, SPR_H, SPR_W, WALK_FRAMES,
  EXTRA_FRAMES, WALK8_FRAMES, IMPACT_FRAME, makePose, type Hold,
} from './character/rig';
import type { Dir5, Slot } from './character/types';
import { SLOTS } from './character/types';
import { body, SKIN_TONES } from './items/body';
import { getItem, itemsFor } from './items/registry';

export interface BakeSpec {
  /** 槽位 → 装备 id（不写 = 空） */
  slots: Partial<Record<Slot, string>>;
  /** 槽位 → 换色方案 id */
  variants?: Partial<Record<Slot, string>>;
  skin?: keyof typeof SKIN_TONES;
  /** 要烘的方向（S / SE / E / NE / N），默认 5 个 */
  dirs?: Dir5[];
  /** 要烘的帧（sheet 列号），默认全部 */
  frames?: number[];
}

function equipment(spec: BakeSpec): Equipment {
  const eq = new Equipment(body);
  if (spec.skin && SKIN_TONES[spec.skin]) eq.setBodyPalette(SKIN_TONES[spec.skin]);
  for (const slot of SLOTS) {
    const id = spec.slots[slot];
    if (!id) continue;
    const it = getItem(id);
    if (!it) throw new Error(`unknown item ${id}`);
    eq.equip(slot, it);
  }
  for (const [slot, v] of Object.entries(spec.variants ?? {}) as [Slot, string][]) if (v) eq.setVariant(slot, v);
  return eq;
}

function bake(specJSON: string): Uint8Array {
  const spec = JSON.parse(specJSON) as BakeSpec;
  const entries = equipment(spec).resolve();
  const dirs = spec.dirs ?? DIRS5;
  const cols = spec.frames ?? Array.from({ length: FRAMES_PER_DIR }, (_, i) => i);
  const W = SPR_W * cols.length, H = SPR_H * dirs.length;
  const out = new Uint8Array(W * H * 4);
  const frame = new Uint8ClampedArray(SPR_W * SPR_H * 4);
  const L = new PixelLayer(SPR_W, SPR_H);
  dirs.forEach((dir, r) => {
    cols.forEach((f, c) => {
      L.clear();
      composeFrame(entries, dir, f, L);
      L.toRGBA(frame);
      for (let y = 0; y < SPR_H; y++) {
        out.set(frame.subarray(y * SPR_W * 4, (y + 1) * SPR_W * 4), ((r * SPR_H + y) * W + c * SPR_W) * 4);
      }
    });
  });
  return out;
}

function info(): string {
  const list = (slot: Slot) => itemsFor(slot).map((it) => ({
    id: it.id, name: it.name, gameItem: it.gameItem, hold: it.hold, attack: it.attack,
    variants: (it.variants ?? []).map((v) => ({ id: v.id, name: v.name })),
  }));
  return JSON.stringify({
    sprW: SPR_W, sprH: SPR_H, scale: SPRITE_SCALE, framesPerDir: FRAMES_PER_DIR, impact: IMPACT_FRAME,
    dirs: DIRS5, footPx: [CX * SPRITE_SCALE, FOOT_Y * SPRITE_SCALE],
    frames: { idle: IDLE_FRAMES, walk: WALK_FRAMES, walk8: WALK8_FRAMES, ready: READY_FRAMES, ...ACTION_FRAMES, ...EXTRA_FRAMES },
    items: Object.fromEntries((['hair', 'face', 'top', 'bottom', 'shoes', 'scarf', 'bag', 'weapon_main'] as Slot[]).map((s) => [s, list(s)])),
    skins: Object.keys(SKIN_TONES),
  });
}

/** 每个方向每一帧：两只脚的像素坐标 [x, y]（按远 → 近） */
function feet(hold: string): string {
  const h = (hold || undefined) as Hold | undefined;
  const S = SPRITE_SCALE;
  return JSON.stringify(DIRS5.map((dir) => Array.from({ length: FRAMES_PER_DIR }, (_, f) => {
    const p = makePose(dir, f, { armedR: h });
    return p.legs.map((l) => [+(l.foot.x * S).toFixed(2), +(l.foot.y * S).toFixed(2)]);
  })));
}

/** 只要某个方向几帧的落脚点：feetAt(hold, dir, framesJSON) → [[[x, y], [x, y]], ...] */
function feetAt(hold: string, dir: string, framesJSON: string): string {
  const h = (hold || undefined) as Hold | undefined;
  const S = SPRITE_SCALE;
  return JSON.stringify((JSON.parse(framesJSON) as number[]).map((f) =>
    makePose(dir as Dir5, f, { armedR: h }).legs.map((l) => [+(l.foot.x * S).toFixed(2), +(l.foot.y * S).toFixed(2)])));
}

/** 某个方向某一帧武器手的像素坐标、武器指向和缩短比例：handAt(hold, dir, frame) → [x, y, angle, reach] */
function handAt(hold: string, dir: string, frame: number): string {
  const h = (hold || undefined) as Hold | undefined;
  const p = makePose(dir as Dir5, frame, { armedR: h });
  const hand = h === 'bow' ? p.handL : p.handR;
  const S = SPRITE_SCALE;
  return JSON.stringify([hand.x * S, hand.y * S, hand.angle, hand.reach, S]);
}

/** 武器手（弓是左手）在每个方向每一帧的像素坐标和武器指向，战斗特效从这里发射 */
function hands(hold: string): string {
  const h = (hold || undefined) as Hold | undefined;
  const S = SPRITE_SCALE;
  return JSON.stringify(DIRS5.map((dir) => Array.from({ length: FRAMES_PER_DIR }, (_, f) => {
    const p = makePose(dir, f, { armedR: h });
    const hand = h === 'bow' ? p.handL : p.handR;
    return [+(hand.x * S).toFixed(2), +(hand.y * S).toFixed(2), +hand.angle.toFixed(3), +hand.reach.toFixed(3)];
  })));
}

/**
 * 装备特效叠加层（PartDef.glow：权杖光芒、龙牙剑火苗……）：同样的方向 / 帧，每帧 4 个相位，
 * 只留「加了特效以后变了的像素」（被身体挡住的特效自然不出现）。排成 行 = 方向 × 4 + 相位、列 = 帧。
 * 这身装备没有特效就返回长度 0。游戏按时间循环相位，叠在人物上面，站着不动时特效也在动。
 */
function bakeFx(specJSON: string): Uint8Array {
  const spec = JSON.parse(specJSON) as BakeSpec;
  const entries = equipment(spec).resolve();
  if (!entries.some((e) => e.item.parts.some((p) => p.glow))) return new Uint8Array(0);
  const dirs = spec.dirs ?? DIRS5;
  const cols = spec.frames ?? Array.from({ length: FRAMES_PER_DIR }, (_, i) => i);
  const P = 4, W = SPR_W * cols.length, H = SPR_H * dirs.length * P;
  const out = new Uint8Array(W * H * 4);
  const plain = new Uint8ClampedArray(SPR_W * SPR_H * 4), lit = new Uint8ClampedArray(SPR_W * SPR_H * 4);
  const L = new PixelLayer(SPR_W, SPR_H);
  dirs.forEach((dir, r) => {
    cols.forEach((f, c) => {
      L.clear(); composeFrame(entries, dir, f, L, { glow: false }); L.toRGBA(plain);
      for (let ph = 0; ph < P; ph++) {
        L.clear(); composeFrame(entries, dir, f, L, { phase: ph }); L.toRGBA(lit);
        for (let y = 0; y < SPR_H; y++) for (let x = 0; x < SPR_W; x++) {
          const i = (y * SPR_W + x) * 4;
          if (lit[i + 3] === 0) continue;
          if (lit[i] === plain[i] && lit[i + 1] === plain[i + 1] && lit[i + 2] === plain[i + 2] && lit[i + 3] === plain[i + 3]) continue;
          out.set(lit.subarray(i, i + 4), (((r * P + ph) * SPR_H + y) * W + c * SPR_W + x) * 4);
        }
      }
    });
  });
  return out;
}

(globalThis as unknown as { PixelBaker: unknown }).PixelBaker = { info, bake, bakeFx, feet, hands, feetAt, handAt };
