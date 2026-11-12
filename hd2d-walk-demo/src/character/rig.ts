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
 * 0.8 → 每帧 51×77 像素，角色约 43 像素高：颗粒粗，接近经典 HD-2D 小人的密度；
 * 调大就多出细节，装备数据不用改。
 */
export let SPRITE_SCALE = 0.8;
/** 每帧的像素大小 */
export let SPR_W = Math.round(UNIT_W * SPRITE_SCALE);
export let SPR_H = Math.round(UNIT_H * SPRITE_SCALE);

export function setSpriteScale(s: number): void {
  SPRITE_SCALE = s;
  SPR_W = Math.round(UNIT_W * s);
  SPR_H = Math.round(UNIT_H * s);
}

export const DIRS5: Dir5[] = ['S', 'SE', 'E', 'NE', 'N'];
export const FRAMES_PER_DIR = 8;
export const IDLE_FRAMES = [0, 1];
export const WALK_FRAMES = [2, 3, 4, 5, 6, 7];

/** 朝向角：S = 面向镜头 */
const TRIG: Record<Dir5, [number, number]> = {
  S: [0, 1],
  SE: [Math.SQRT1_2, Math.SQRT1_2],
  E: [1, 0],
  NE: [Math.SQRT1_2, -Math.SQRT1_2],
  N: [0, -1],
};

/**
 * 身体比例（从脚底往上的高度，单位）。Q 版约 2.3 头身：头大、身体短、手脚小。
 */
const HIP = 16;
const HAND = 17;
const SHOULDER = 29;
const NECK = 30;
const HEAD = 40.5;
/** 头的半径 */
export const HEAD_RX = 10.4;
export const HEAD_RY = 9.8;

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
  anim: 'idle' | 'walk';
  /** 动画内的帧序号（待机 0-1，行走 0-5） */
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
}

/** 握持方式：'up' 竖着举在身侧（法杖），'down' 剑尖朝下垂在身前（剑） */
export type Hold = 'up' | 'down';

export interface PoseOptions {
  /** 哪只手拿着武器、怎么拿：持武器的手不再垂在身侧摆动 */
  armedR?: Hold;
  armedL?: Hold;
}

export function makePose(dir: Dir5, frame: number, opts: PoseOptions = {}): Pose {
  const [sin, cos] = TRIG[dir];
  const anim = frame < 2 ? 'idle' : 'walk';
  const walking = anim === 'walk';
  const t = walking ? frame - 2 : frame;

  let s = 0, c = 0, bob = 0, phase = 0;
  if (walking) {
    phase = ((t + 0.5) / 6) * Math.PI * 2;
    s = Math.sin(phase);
    c = Math.cos(phase);
    bob = t % 3 === 1 ? 1 : 0; // 迈到最大步幅时身体下沉
  } else {
    bob = t === 1 ? 1 : 0; // 呼吸
  }
  // 走路时上身前倾一点；站着时重心偏向一条腿，不是立正
  const lean = walking ? 1 : 0;

  const proj = (side: number, up: number, fwd: number, tilt = TILT): Joint => {
    const near = fwd * cos - side * sin;
    return { x: CX + side * cos + fwd * sin, y: FOOT_Y - up + near * tilt, near };
  };

  const head = proj(walking ? 0 : -0.3, HEAD - bob, lean);

  const arm = (sign: -1 | 1, hold: Hold | undefined): Arm => {
    const shoulder = proj(7.2 * sign, SHOULDER - bob, lean * 0.6, 0.12);
    let j: Joint, elbow: Joint;
    // 武器在局部坐标里的指向（side, up, fwd）
    let ls = 0.14 * sign, lu = 0.95, lf = 0.1;
    if (hold === 'up') {
      // 竖握：上臂贴身，前臂抬到身前，手在身侧偏外。
      // 正侧面时杖头往前倾，从脸前面过去，否则竖直的杖会正好穿过脑袋。
      elbow = proj(8.6 * sign, HAND + 7 - bob, -1);
      j = proj(9.6 * sign, HAND + 5 - bob, 3.2 + 1.2 * s * sign);
      if (Math.abs(cos) < 0.5) lf = 0.62;
    } else if (hold === 'down') {
      // 垂握：手臂自然下垂略向前，剑尖朝前下方，随步伐轻晃
      elbow = proj(8.5 * sign, HAND + 6.5 - bob, 0.5 * s * sign);
      j = proj(8.8 * sign, HAND + 1.5 - bob, 2.6 + 1.6 * s * sign);
      ls = 0.5 * sign; lu = -0.55; lf = 0.65;
    } else {
      // 空手：与同侧腿反向摆动，肘部略向后弯；站立时两只手一前一后
      const swing = walking ? 4.5 * s * sign : sign < 0 ? 1.4 : -0.6;
      elbow = proj(8.3 * sign, (SHOULDER + HAND) / 2 + 0.5 - bob, swing * 0.35 - 1.2);
      j = proj(7.8 * sign, HAND - bob + Math.abs(swing) * 0.15, swing + 0.8);
    }
    const dx = ls * cos + lf * sin;
    const nr = lf * cos - ls * sin;
    const dy = -lu + nr * TILT;
    return {
      shoulder,
      elbow,
      hand: {
        ...j,
        front: shoulder.near >= -0.01,
        angle: Math.atan2(dy, dx),
        weaponFront: -7.8 * sign * sin + nr * 14 >= -0.5,
        // 竖握武器在正侧面时画在头前面（weapon_front），其余朝向从头后面穿过（weapon_mid）
        weaponOverHead: Math.abs(cos) < 0.5,
      },
    };
  };
  const armR = arm(-1, opts.armedR), armL = arm(1, opts.armedL);

  const leg = (id: 'R' | 'L', sign: -1 | 1): Leg => {
    const hip = proj(2.8 * sign, HIP - bob, 0, 0);
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
