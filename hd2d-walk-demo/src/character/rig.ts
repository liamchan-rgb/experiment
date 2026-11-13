import type { Dir5, Dir8 } from './types';

/**
 * 骨架（Rig）：给出每个方向、每一帧的关节位置和手部锚点（都是单位坐标，可以是小数）。
 *
 * 做法：角色有一套局部 3D 坐标（side = 角色左手方向，up = 向上，fwd = 面朝方向），
 * 按朝向角绕竖轴旋转后正交投影到精灵平面。这样腿、手臂的摆动只写一份，
 * 5 个方向自动得到一致的动作，遮挡关系（near）也一并算出。
 */

/** 单位坐标下的画布大小。所有形状都在这个坐标系里描述。 */
export const UNIT_W = 64;
export const UNIT_H = 96;
/** 精灵中轴（镜像轴），单位坐标 */
export const CX = 32;
/** 脚底所在高度，单位坐标 */
export const FOOT_Y = 90;

/**
 * 精灵倍率：实际像素 = 单位 × SPRITE_SCALE。
 * 0.65 → 每帧 42×62 像素，角色约 36 像素高：颗粒粗，接近经典 HD-2D 小人的密度；
 * 调大就多出细节，装备数据不用改。
 */
export let SPRITE_SCALE = 0.65;
/** 每帧的像素大小 */
export let SPR_W = Math.round(UNIT_W * SPRITE_SCALE);
export let SPR_H = Math.round(UNIT_H * SPRITE_SCALE);

export function setSpriteScale(s: number): void {
  SPRITE_SCALE = s;
  SPR_W = Math.round(UNIT_W * s);
  SPR_H = Math.round(UNIT_H * s);
}

export const DIRS5: Dir5[] = ['S', 'SE', 'E', 'NE', 'N'];
/** 战斗动作：每个 4 帧，接在行走后面 */
export type ActionId = 'slash' | 'heavy' | 'shoot' | 'cast';
export const ACTIONS: ActionId[] = ['slash', 'heavy', 'shoot', 'cast'];
export const ACTION_LEN = 4;
export const IDLE_FRAMES = [0, 1];
export const WALK_FRAMES = [2, 3, 4, 5, 6, 7];
/** 每个动作在 sheet 里的列号：挥砍 8–11，重劈 12–15，射箭 16–19，施法 20–23 */
export const ACTION_FRAMES: Record<ActionId, number[]> = Object.fromEntries(
  ACTIONS.map((a, i) => [a, Array.from({ length: ACTION_LEN }, (_, k) => 8 + i * ACTION_LEN + k)]),
) as Record<ActionId, number[]>;
export const FRAMES_PER_DIR = 8 + ACTIONS.length * ACTION_LEN;

/** sheet 列号 → 动画名和动画内的帧序号 */
export function frameInfo(frame: number): { anim: 'idle' | 'walk' | ActionId; t: number } {
  if (frame < 2) return { anim: 'idle', t: frame };
  if (frame < 8) return { anim: 'walk', t: frame - 2 };
  const k = frame - 8;
  return { anim: ACTIONS[Math.floor(k / ACTION_LEN)], t: k % ACTION_LEN };
}

/** 朝向角：S = 面向镜头 */
const TRIG: Record<Dir5, [number, number]> = {
  S: [0, 1],
  SE: [Math.SQRT1_2, Math.SQRT1_2],
  E: [1, 0],
  NE: [Math.SQRT1_2, -Math.SQRT1_2],
  N: [0, -1],
};

/**
 * 身体比例（从脚底往上的高度，单位）。Q 版约 2.1 头身：头大、身体短、手脚小。
 */
const HIP = 16;
const HAND = 17;
const SHOULDER = 29;
const NECK = 30;
const HEAD = 41.8;
/** 头的半径 */
export const HEAD_RX = 11.6;
export const HEAD_RY = 10.9;

/** 俯视带来的纵向错位：离镜头近的点在屏幕上更低 */
const TILT = 0.35;

export interface Joint {
  x: number;
  y: number;
  /** > 0 表示比身体中轴更靠近镜头 */
  near: number;
}

export interface HandAnchor extends Joint {
  /** 手臂所在图层：近侧手臂画在躯干前 */
  front: boolean;
  /** 武器指向（屏幕空间弧度，y 向下） */
  angle: number;
  /** 手持武器应画在身前还是身后 */
  weaponFront: boolean;
  /** 竖握的长柄武器是否画在头前面 */
  weaponOverHead: boolean;
  /** 武器是否从头后面穿过（画在 weapon_mid：身体前、头后） */
  weaponMid: boolean;
  /** 武器在画面上的缩短比例（指向镜头时变短），0.5..1；武器长度都乘它 */
  reach: number;
  /** 挥砍拖影：上一帧武器的屏幕角度（只有挥动的那几帧有） */
  trailFrom?: number;
}

export interface Arm {
  shoulder: Joint;
  elbow: Joint;
  hand: HandAnchor;
}

export interface Leg {
  id: 'R' | 'L';
  hip: Joint;
  foot: Joint;
}

export interface Pose {
  dir: Dir5;
  sin: number;
  cos: number;
  frame: number;
  anim: 'idle' | 'walk' | ActionId;
  /** 动画内的帧序号（待机 0-1，行走 0-5，动作 0-3） */
  t: number;
  /** 行走相位（弧度），待机为 0 */
  phase: number;
  /** 上半身下沉的量（呼吸 / 走路弹跳） */
  bob: number;
  /** 局部坐标 → 精灵坐标 */
  proj(side: number, up: number, fwd: number, tilt?: number): Joint;
  head: Joint;
  /** 颈部所在高度（屏幕 y） */
  neckY: number;
  /** 颈部的 up 值（已含 bob），给 proj() 用：proj(side, neckUp - n, fwd) */
  neckUp: number;
  /** 躯干半宽（随朝向变窄） */
  torsoHalf: number;
  armR: Arm;
  armL: Arm;
  /** 手部锚点（= armR.hand / armL.hand），武器按它绘制 */
  handR: HandAnchor;
  handL: HandAnchor;
  /** 两条腿，已按远 → 近排序 */
  legs: [Leg, Leg];
  /** 动作特效：'glow' 蓄力 / 'burst' 释放 / 'arrow' 搭箭 / 'loose' 放箭，武器按需画 */
  fx?: 'glow' | 'burst' | 'arrow' | 'loose';
}

/**
 * 握持方式：'up' 竖着举在身侧（法杖），'down' 剑尖朝下垂在身前（单手剑），
 * 'shoulder' 双手大剑扛在右肩上，'bow' 弓拿在左手（右手空出来拉弦）
 */
export type Hold = 'up' | 'down' | 'shoulder' | 'bow';

type V3 = [number, number, number];
/** 动作的一帧：右手 / 左手的位置（side, up, fwd）、武器指向，身体前倾、下沉、跨步 */
interface ActKey {
  R: V3;
  L: V3;
  /** 武器指向（局部坐标）。双手武器左手自动握在剑柄上 */
  dir: V3;
  lean: number;
  bob: number;
  step: number;
  /** 这一帧有挥砍拖影：从上一帧的武器指向扫过来 */
  trail?: boolean;
  fx?: Pose['fx'];
}

/**
 * 四个战斗动作的关键帧（右手 side 为负）。都是局部坐标，5 个方向共用一份。
 *   slash 单手挥砍：举剑 → 横斩 → 收势 → 回位
 *   heavy 双手重劈：高举过头 → 下劈 → 砸地 → 回位
 *   shoot 拉弓：举弓搭箭 → 满弦 → 放箭 → 回位（弓在左手）
 *   cast  施法 / 鼓舞：蓄力 → 高举 → 前推释放 → 回位（没有法杖时就是举起武器或手）
 */
const ACTION_KEYS: Record<ActionId, ActKey[]> = {
  slash: [
    { R: [-8.5, 36, -3], L: [6, 22, 5], dir: [-0.15, 0.75, -0.65], lean: -0.5, bob: 0, step: 1 },
    { R: [-4, 30, 9], L: [7.5, 20, -2], dir: [0.1, 0.25, 1], lean: 1.5, bob: 0.5, step: 3, trail: true },
    { R: [-1, 22, 8], L: [8, 19, -3], dir: [0.55, -0.6, 0.55], lean: 2.2, bob: 1.5, step: 4, trail: true },
    { R: [-8, 19, 4], L: [7.8, 17.6, -0.6], dir: [0.4, -0.6, 0.7], lean: 0.8, bob: 0.5, step: 2 },
  ],
  heavy: [
    { R: [-3, 37, -2], L: [0, 0, 0], dir: [0.05, 0.55, -0.83], lean: -1, bob: 0, step: 1 },
    { R: [-2, 31, 8], L: [0, 0, 0], dir: [0.05, 0.6, 0.8], lean: 1.5, bob: 0.5, step: 3, trail: true },
    { R: [-1, 20, 9], L: [0, 0, 0], dir: [0.05, -0.45, 0.9], lean: 2.8, bob: 2.5, step: 5, trail: true, fx: 'burst' },
    { R: [-3, 22, 6], L: [0, 0, 0], dir: [0.1, -0.35, 0.93], lean: 1.5, bob: 1, step: 3 },
  ],
  shoot: [
    { R: [-3, 27, 8], L: [5, 27, 9], dir: [0, 1, 0.1], lean: 0.3, bob: 0, step: 2, fx: 'arrow' },
    { R: [-5, 30, -1], L: [3.5, 27, 12], dir: [0, 1, 0.05], lean: 0.5, bob: 0, step: 2, fx: 'arrow' },
    { R: [-7.5, 31, -4], L: [3.5, 27, 12], dir: [0, 1, 0.05], lean: 0.3, bob: 0, step: 2, fx: 'loose' },
    { R: [-8, 20, 1], L: [6.5, 24, 6], dir: [0.05, 1, 0.15], lean: 0.2, bob: 0, step: 1 },
  ],
  cast: [
    { R: [-8, 25, 5], L: [5, 25, 7], dir: [0, 1, 0.15], lean: 0.3, bob: 1, step: 1, fx: 'glow' },
    { R: [-7, 36, 4], L: [6, 27, 8], dir: [0.05, 0.92, 0.35], lean: 0.5, bob: 0, step: 1, fx: 'glow' },
    { R: [-5, 31, 10], L: [7.5, 22, 2], dir: [0.05, 0.55, 0.85], lean: 1.5, bob: 0.5, step: 2, fx: 'burst' },
    { R: [-9, 22, 3.5], L: [7.8, 17.6, -0.6], dir: [0.05, 1, 0.2], lean: 0.5, bob: 0, step: 1 },
  ],
};

/** 双手武器（重劈）：左手握在右手前面一点的剑柄上 */
const TWO_HAND_GAP = 2.6;

export interface PoseOptions {
  /** 哪只手拿着武器、怎么拿：持武器的手不再垂在身侧摆动 */
  armedR?: Hold;
  armedL?: Hold;
}

export function makePose(dir: Dir5, frame: number, opts: PoseOptions = {}): Pose {
  const [sin, cos] = TRIG[dir];
  const { anim, t } = frameInfo(frame);
  const walking = anim === 'walk';
  const act = anim !== 'idle' && anim !== 'walk' ? ACTION_KEYS[anim][t] : undefined;
  const prevAct = act && t > 0 ? ACTION_KEYS[anim as ActionId][t - 1] : undefined;

  let s = 0, c = 0, bob = 0, phase = 0;
  if (walking) {
    phase = ((t + 0.5) / 6) * Math.PI * 2;
    s = Math.sin(phase);
    c = Math.cos(phase);
    bob = t % 3 === 1 ? 1 : 0; // 迈到最大步幅时身体下沉
  } else if (act) {
    bob = act.bob;
  } else {
    bob = t === 1 ? 1 : 0; // 呼吸
  }
  // 走路时上身前倾一点；站着时重心偏向一条腿，不是立正
  const lean = act ? act.lean : walking ? 1 : 0;

  const proj = (side: number, up: number, fwd: number, tilt = TILT): Joint => {
    const near = fwd * cos - side * sin;
    return { x: CX + side * cos + fwd * sin, y: FOOT_Y - up + near * tilt, near };
  };

  const head = proj(walking || act ? 0 : -0.3, HEAD - bob, lean);

  /** 局部方向 → 画面角度、缩短比例 */
  const screenDir = (d: V3) => {
    const [ls, lu, lf] = d;
    const dx = ls * cos + lf * sin;
    const nr = lf * cos - ls * sin;
    const dy = -lu + nr * TILT;
    const len = Math.min(1, Math.hypot(dx, dy));
    return { angle: Math.atan2(dy, dx), nr, reach: 0.35 + 0.65 * Math.max(0.25, len) };
  };

  const arm = (sign: -1 | 1, hold: Hold | undefined): Arm => {
    const shoulder = proj(7.2 * sign, SHOULDER - bob, lean * 0.6, 0.12);
    let j: Joint, elbow: Joint;
    // 武器在局部坐标里的指向（side, up, fwd）
    let wd: V3 = [0.14 * sign, 0.95, 0.1];
    let trailFrom: number | undefined;
    let mid = hold === 'up' || hold === 'shoulder';

    // 弓拿在左手：左手是「持武器」的那只
    const isBowArm = hold === 'bow';
    if (act && (sign < 0 || isBowArm || anim === 'heavy')) {
      // 动作帧：手的位置来自关键帧；双手重劈时左手握在剑柄上
      let p: V3 = sign < 0 ? act.R : act.L;
      if (sign > 0 && anim === 'heavy') {
        p = [act.R[0] + act.dir[0] * TWO_HAND_GAP, act.R[1] + act.dir[1] * TWO_HAND_GAP, act.R[2] + act.dir[2] * TWO_HAND_GAP];
      }
      j = proj(p[0], p[1] - bob, p[2]);
      // 肘：肩和手的中点，往外、往下撇一点
      elbow = proj((7.2 * sign + p[0]) / 2 + 1.4 * sign, (SHOULDER + p[1]) / 2 - 1.6 - bob, (lean * 0.6 + p[2]) / 2 - 0.8);
      if (isBowArm) wd = act.dir.map((v, i) => (i === 0 ? v * sign : v)) as V3;
      else if (sign < 0) {
        wd = act.dir;
        if (act.trail && prevAct) trailFrom = screenDir(prevAct.dir).angle;
        mid = mid || act.dir[1] > 0.4;
      }
    } else if (act && sign > 0) {
      // 动作帧里不拿武器的左手
      j = proj(act.L[0], act.L[1] - bob, act.L[2]);
      elbow = proj((7.2 + act.L[0]) / 2 + 1.4, (SHOULDER + act.L[1]) / 2 - 1.6 - bob, (lean * 0.6 + act.L[2]) / 2 - 0.8);
    } else if (hold === 'up') {
      // 竖握：上臂贴身，前臂抬到身前，手在身侧偏外。
      // 正侧面时杖头往前倾，从脸前面过去，否则竖直的杖会正好穿过脑袋。
      elbow = proj(8.6 * sign, HAND + 7 - bob, -1);
      j = proj(9.6 * sign, HAND + 5 - bob, 3.2 + 1.2 * s * sign);
      if (Math.abs(cos) < 0.5) wd = [wd[0], wd[1], 0.62];
    } else if (hold === 'down') {
      // 垂握：手臂自然下垂略向前，剑尖朝前下方，随步伐轻晃
      elbow = proj(8.5 * sign, HAND + 6.5 - bob, 0.5 * s * sign);
      j = proj(8.8 * sign, HAND + 1.5 - bob, 2.6 + 1.6 * s * sign);
      wd = [0.5 * sign, -0.55, 0.65];
    } else if (hold === 'shoulder') {
      // 扛在肩上：手在胸前握柄，剑身越过右肩往后上方
      elbow = proj(8.4 * sign, HAND + 6 - bob, 1.5);
      j = proj(5.5 * sign, HAND + 5 - bob, 4 + 0.6 * s * sign);
      wd = [0.15 * sign, 0.7, -0.7];
    } else if (hold === 'bow') {
      // 弓垂在身侧：弓身竖直，随步伐轻晃
      elbow = proj(8.4 * sign, (SHOULDER + HAND) / 2 + 0.5 - bob, -0.6);
      j = proj(8.6 * sign, HAND + 1.5 - bob, 2.6 + 1.2 * s * sign);
      wd = [0.05 * sign, 1, 0.12];
    } else {
      // 空手：与同侧腿反向摆动，肘部略向后弯；站立时两只手一前一后
      const swing = walking ? 4.5 * s * sign : sign < 0 ? 1.4 : -0.6;
      elbow = proj(8.3 * sign, (SHOULDER + HAND) / 2 + 0.5 - bob, swing * 0.35 - 1.2);
      j = proj(7.8 * sign, HAND - bob + Math.abs(swing) * 0.15, swing + 0.8);
    }
    const sd = screenDir(wd);
    const overHead = Math.abs(cos) < 0.5;
    return {
      shoulder,
      elbow,
      hand: {
        ...j,
        front: shoulder.near >= -0.01,
        angle: sd.angle,
        // 拉弓时弓伸在脸前面，侧面也要压在头和近侧手臂上
        weaponFront: (act && isBowArm) || (act || hold === 'shoulder' || hold === 'bow' ? j.near + sd.nr * 10 >= -0.5 : -7.8 * sign * sin + sd.nr * 14 >= -0.5),
        // 竖握武器在正侧面时画在头前面（weapon_front），其余朝向从头后面穿过（weapon_mid）
        weaponOverHead: overHead,
        weaponMid: mid && !overHead,
        reach: hold === 'up' || hold === 'down' ? (act ? sd.reach : 1) : sd.reach,
        trailFrom,
      },
    };
  };
  // 弓在左手：把「持弓」交给左臂
  const bow = opts.armedR === 'bow';
  const armR = arm(-1, bow ? undefined : opts.armedR), armL = arm(1, bow ? 'bow' : opts.armedL);

  const leg = (id: 'R' | 'L', sign: -1 | 1): Leg => {
    const hip = proj(2.8 * sign, HIP - bob, 0, 0);
    if (act) {
      // 战斗动作：左脚往前跨，右脚往后蹬
      return { id, hip, foot: sign < 0 ? proj(-3.6, 0, -act.step * 0.5) : proj(3.2, 0, act.step) };
    }
    if (!walking) {
      // 稍息：右脚略向前、向外
      return { id, hip, foot: sign < 0 ? proj(-3.6, 0, 1.5) : proj(3, 0, -0.4) };
    }
    const swing = -s * sign; // 右脚 fwd = +s
    const lift = Math.max(0, -c * sign) * 2.6; // 向前摆的那只脚抬起
    return { id, hip, foot: proj(3 * sign, lift, 5 * swing) };
  };
  const legR = leg('R', -1), legL = leg('L', 1);
  const legs: [Leg, Leg] = legR.foot.near <= legL.foot.near ? [legR, legL] : [legL, legR];

  return {
    dir, sin, cos, frame, anim, t, phase, bob, proj,
    head,
    neckY: FOOT_Y - NECK + bob,
    neckUp: NECK - bob,
    torsoHalf: 6.5 - 1.9 * Math.abs(sin),
    armR, armL,
    handR: armR.hand,
    handL: armL.hand,
    legs,
    fx: act?.fx,
  };
}

/** 8 方向 → (手绘方向, 是否镜像) */
export const DIR8_MAP: Record<Dir8, { dir: Dir5; flip: boolean }> = {
  S: { dir: 'S', flip: false },
  SE: { dir: 'SE', flip: false },
  E: { dir: 'E', flip: false },
  NE: { dir: 'NE', flip: false },
  N: { dir: 'N', flip: false },
  NW: { dir: 'NE', flip: true },
  W: { dir: 'E', flip: true },
  SW: { dir: 'SE', flip: true },
};

/** 由移动向量（x 向右，z 向镜头）得到 8 方向 */
export function dir8FromVector(x: number, z: number): Dir8 {
  const a = Math.atan2(z, x); // 0 = E，π/2 = S
  const i = ((Math.round(a / (Math.PI / 4)) % 8) + 8) % 8;
  return (['E', 'SE', 'S', 'SW', 'W', 'NW', 'N', 'NE'] as Dir8[])[i];
}
