import type { Dir5, Dir8 } from './types';
import { captured, type CapturedKey } from './mocap';

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
/**
 * sheet 每一行的列：先是普通待机、行走，然后是战斗用的各段动画（长度不一）。
 * 挥砍 / 重劈 / 突进斩、受击取自原型动作包的动作捕捉（见 mocap.ts），8 帧左右；射箭、施法仍是手调的 4 帧。
 */
export type ActionId = 'slash' | 'heavy' | 'dash' | 'shoot' | 'cast';
export const ACTIONS: ActionId[] = ['slash', 'heavy', 'dash', 'shoot', 'cast'];
export type ExtraId = 'guard' | 'hurt' | 'victory' | 'defeat';
export const EXTRAS: ExtraId[] = ['guard', 'hurt', 'victory', 'defeat'];
export type AnimId = 'idle' | 'walk' | 'ready' | ActionId | ExtraId;

/** 每段动画的帧数，顺序就是 sheet 里的顺序 */
export const CLIP_LENGTHS: [AnimId, number][] = [
  ['idle', 2], ['walk', 6], ['ready', 2],
  ['slash', 8], ['heavy', 8], ['dash', 8], ['shoot', 4], ['cast', 4],
  ['guard', 2], ['hurt', 6], ['victory', 2], ['defeat', 6],
];
/** 动画名 → sheet 列号 */
export const CLIP_FRAMES: Record<AnimId, number[]> = (() => {
  const out = {} as Record<AnimId, number[]>;
  let at = 0;
  for (const [id, n] of CLIP_LENGTHS) { out[id] = Array.from({ length: n }, (_, k) => at + k); at += n; }
  return out;
})();
export const FRAMES_PER_DIR = CLIP_LENGTHS.reduce((n, [, k]) => n + k, 0);
export const IDLE_FRAMES = CLIP_FRAMES.idle;
export const WALK_FRAMES = CLIP_FRAMES.walk;
/** 战斗待机：两脚前后分开、压低重心、武器指向敌人，2 帧呼吸。姿势随武器种类变 */
export const READY_FRAMES = CLIP_FRAMES.ready;
export const ACTION_FRAMES = Object.fromEntries(ACTIONS.map((a) => [a, CLIP_FRAMES[a]])) as Record<ActionId, number[]>;
export const EXTRA_FRAMES = Object.fromEntries(EXTRAS.map((a) => [a, CLIP_FRAMES[a]])) as Record<ExtraId, number[]>;
/** 攻击 / 施法的「出手帧」（动画内序号）：战斗里伤害数字、箭、法术对准它 */
export const IMPACT_FRAME: Record<ActionId, number> = { slash: 2, heavy: 3, dash: 3, shoot: 2, cast: 2 };

/**
 * 8 相位的行走（不在 sheet 里，按需烘焙）：iPad 地图的行走图集是 8 个相位，
 * 用 6 帧去凑会有两帧重复、走起来一顿一顿，所以单独提供 WALK8_BASE..+7 这 8 个虚拟帧。
 */
export const WALK8_BASE = 100;
export const WALK8_FRAMES = Array.from({ length: 8 }, (_, i) => WALK8_BASE + i);

/** sheet 列号 → 动画名和动画内的帧序号 */
export function frameInfo(frame: number): { anim: AnimId; t: number; walk8?: boolean } {
  if (frame >= WALK8_BASE && frame < WALK8_BASE + 8) return { anim: 'walk', t: frame - WALK8_BASE, walk8: true };
  let at = 0;
  for (const [id, n] of CLIP_LENGTHS) {
    if (frame < at + n) return { anim: id, t: frame - at };
    at += n;
  }
  return { anim: 'idle', t: 0 };
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
  /** 膝盖：腿伸直时在髋和脚的中点，下蹲 / 跨步时往前顶 */
  knee: Joint;
  foot: Joint;
}

export interface Pose {
  dir: Dir5;
  sin: number;
  cos: number;
  frame: number;
  anim: AnimId;
  /** 动画内的帧序号（待机 0-1，行走 0-5，战斗待机 0-1，动作 0-3） */
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
  /**
   * 躯干中线在颈下 r 个单位处的横坐标。前倾时整个上身（颈、肩、胸）一起往前倒，
   * 髋部略往后坐，躯干是一条斜线而不是直的；画躯干、衣服细节都用它代替 CX。
   */
  torsoX(r: number): number;
  armR: Arm;
  armL: Arm;
  /** 手部锚点（= armR.hand / armL.hand），武器按它绘制 */
  handR: HandAnchor;
  handL: HandAnchor;
  /** 两条腿，已按远 → 近排序 */
  legs: [Leg, Leg];
  /** 动作特效：'glow' 蓄力 / 'burst' 释放 / 'arrow' 搭箭 / 'loose' 放箭，武器按需画 */
  fx?: 'glow' | 'burst' | 'arrow' | 'loose';
  /** 倒地：合成好的整张图顺时针转 90°（脸朝下趴着），lift = 离地多少单位 */
  lying?: { lift: number };
  /** 受击的第一帧：整个人闪白 */
  flash?: boolean;
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
  /** 动作捕捉的帧：前倾、下蹲、脚的位置都是绝对值，不再叠加站姿 */
  absolute?: boolean;
  /** 颈 / 髋的前后偏移（局部 fwd），不写就由 lean 推算 */
  neckF?: number;
  hipF?: number;
  /** 右脚 / 左脚的局部坐标，不写就按站姿 + step */
  feet?: [V3, V3];
  /** 倒地：整个人画好后顺时针转 90°，脸朝下趴在地上 */
  lying?: boolean;
}

/** 动作捕捉的关键帧 → ActKey */
function fromCapture(list: CapturedKey[]): ActKey[] {
  return list.map((k) => ({ R: k.R, L: k.L, dir: k.dir, lean: 0, bob: k.bob, step: 0, trail: k.trail, absolute: true, neckF: k.neckF, hipF: k.hipF, feet: k.feet }));
}

/**
 * 四个战斗动作的关键帧（右手 side 为负）。都是局部坐标，5 个方向共用一份。
 *   slash 单手挥砍：举剑 → 横斩 → 收势 → 回位
 *   heavy 双手重劈：高举过头 → 下劈 → 砸地 → 回位
 *   shoot 拉弓：举弓搭箭 → 满弦 → 放箭 → 回位（弓在左手）
 *   cast  施法 / 鼓舞：蓄力 → 高举 → 前推释放 → 回位（没有法杖时就是举起武器或手）
 */
const ACTION_KEYS: Record<ActionId, ActKey[]> = {
  // 挥砍 / 重劈 / 突进斩：动作捕捉（原型动作包的 Attack1 / Attack3 / Dash Attack）
  slash: fromCapture(captured('attack1', { crouch: 1.6, reach: 1.3 })),
  heavy: fromCapture(captured('attack3', { crouch: 2.2, leanGain: 1.1, reach: 1.3 })).map((k, i) => (i === 3 ? { ...k, fx: 'burst' as const } : k)),
  dash: fromCapture(captured('dash', { crouch: 1.8, leanGain: 1.15, reach: 1.3 })),
  shoot: [
    { R: [-3, 27, 8], L: [5, 27, 9], dir: [0, 1, 0.1], lean: 0.3, bob: 0, step: 2, fx: 'arrow' },
    { R: [-5, 30, -1], L: [3.5, 27, 12], dir: [0, 1, 0.05], lean: 0.5, bob: 0, step: 2, fx: 'arrow' },
    { R: [-7.5, 31, -4], L: [3.5, 27, 12], dir: [0, 1, 0.05], lean: 0.3, bob: 0, step: 2, fx: 'loose' },
    { R: [-4.5, 23, 2], L: [5, 23, 8], dir: [0, 1, 0.28], lean: 0.4, bob: 0, step: 0.5 },
  ],
  cast: [
    { R: [-8, 25, 5], L: [5, 25, 7], dir: [0, 1, 0.15], lean: 0.3, bob: 1, step: 1, fx: 'glow' },
    { R: [-7, 36, 4], L: [6, 27, 8], dir: [0.05, 0.92, 0.35], lean: 0.5, bob: 0, step: 1, fx: 'glow' },
    { R: [-5, 31, 10], L: [7.5, 22, 2], dir: [0.05, 0.55, 0.85], lean: 1.5, bob: 0.5, step: 2, fx: 'burst' },
    { R: [-7, 24, 5], L: [6, 25, 7], dir: [0.05, 0.9, 0.4], lean: 0.6, bob: 0, step: 0.5 },
  ],
};

/**
 * 战斗站姿（按右手武器的握持方式）：战斗待机直接用它，攻击动作的脚步和下蹲也以它为底。
 *   front / back：前脚（左脚）往前、后脚（右脚）往后各多少；crouch：压低多少
 *   key：战斗待机那一帧的手和武器（第 2 帧在此基础上呼吸下沉）
 */
interface Stance {
  front: number;
  back: number;
  crouch: number;
  key: ActKey;
}
const STANCES: Record<Hold | 'none', Stance> = {
  // 单手剑：侧身，剑尖斜指前上方，左手护在胸前
  down: {
    front: 5.6, back: 4.8, crouch: 2.8,
    key: { R: [-6, 22, 6], L: [5.5, 24, 4.5], dir: [0.15, 0.45, 0.88], lean: 2.4, bob: 0, step: 0 },
  },
  // 双手大剑：最宽最低的马步，双手握剑斜架在身前
  shoulder: {
    front: 6.6, back: 5.8, crouch: 3.6,
    key: { R: [-3, 21, 5], L: [0, 0, 0], dir: [0.1, 0.72, 0.68], lean: 2, bob: 0, step: 0 },
  },
  // 弓：侧身拉开距离，弓压低指向前方，右手搭在弦上
  bow: {
    front: 4.6, back: 5.4, crouch: 2,
    key: { R: [-4, 24, 2.5], L: [5, 22, 8], dir: [0, 1, 0.3], lean: 1.3, bob: 0, step: 0 },
  },
  // 法杖：杖身前倾，左手张开在身前准备施法
  up: {
    front: 4.2, back: 3.8, crouch: 1.7,
    key: { R: [-7, 24, 5], L: [6, 25, 7], dir: [0.05, 0.9, 0.42], lean: 1.6, bob: 0, step: 0 },
  },
  // 空手：双拳举在胸前
  none: {
    front: 5, back: 4.2, crouch: 2.3,
    key: { R: [-4, 26, 6], L: [4.5, 27, 7.5], dir: [0.14, 0.95, 0.1], lean: 2.2, bob: 0, step: 0 },
  },
};

/**
 * 战斗反应的关键帧（按握持方式）。lean 是绝对值，不再叠加站姿的前倾。
 *   guard   武器横架在身前挡住，第 2 帧被震得往后一缩
 *   hurt    上身后仰、双手甩开，第 2 帧缓回来一点
 *   victory 武器 / 拳头高举
 *   defeat  单膝跪地，武器拄在地上，第 2 帧头垂得更低
 */
function extraKey(anim: ExtraId, t: number, hold: Hold | 'none'): ActKey {
  const two = t === 1;
  switch (anim) {
    case 'guard': {
      const base = { lean: -0.4, bob: two ? 1.2 : 0.6, step: two ? -1.2 : -0.4 };
      if (hold === 'bow') return { R: [-3, 25, 6], L: [4, 28, 8], dir: [0.15, 1, 0.1], ...base };
      if (hold === 'none') return { R: [-1, 28, 7], L: [1.5, 27, 7.5], dir: [0.14, 0.95, 0.1], ...base };
      if (hold === 'up') return { R: [-4, 26, 7], L: [5, 26, 7], dir: [0.9, 0.45, 0.1], ...base };
      return { R: [-3, 26, 7.5], L: [4, 25, 6], dir: [0.95, 0.3, 0.1], ...base };
    }
    case 'hurt':
      // 动作捕捉（原型动作包的 Hurt），8 帧里取 6 帧
      return HURT_KEYS[Math.min(HURT_KEYS.length - 1, t)];
    case 'victory': {
      const base = { lean: 0.2, bob: two ? 0.6 : 0, step: -2.6 };
      if (hold === 'bow') return { R: [-6, 25, 3], L: [5, 38, 2], dir: [0, 1, 0.05], ...base };
      if (hold === 'none') return { R: [-6, 39, 1], L: [6, 23, 3], dir: [0.14, 0.95, 0.1], ...base };
      return { R: [-6, 38, 2], L: [6, 23, 3], dir: [0.08, 1, 0.12], ...base };
    }
    case 'defeat':
      // 参照原型动作包的 Die：踉跄前扑 → 膝盖一软往前栽 → 扑倒在地（转 90°）→ 弹一下 → 趴着不动
      return DEFEAT_KEYS[Math.min(DEFEAT_KEYS.length - 1, t)];
  }
}

const HURT_KEYS: ActKey[] = fromCapture(captured('hurt', { pick: [0, 1, 2, 3, 5, 7], crouch: 1.2 }));

/** 倒下：前两帧是骨架姿势，后面是「直挺挺、双手前伸」的姿势转 90° 趴在地上（lift = 离地多少） */
const LIE: Omit<ActKey, 'bob'> = {
  R: [-5.5, 40, 1.5], L: [5.5, 39, 1], dir: [0.05, 1, 0.05], lean: 0, step: 0, absolute: true, neckF: 0.5, hipF: 0,
  feet: [[-2.6, 0, -0.6], [2.6, 0, 0.6]], lying: true,
};
const DEFEAT_KEYS: ActKey[] = [
  { R: [-6, 18, 9], L: [6, 19, 8], dir: [0.2, -0.5, 0.85], lean: 0, bob: 2.4, step: 0, absolute: true, neckF: 4.5, hipF: -1.2,
    feet: [[-3.2, 0, -5], [3.2, 0, 4.5]] },
  { R: [-6, 12, 11], L: [6, 13, 10], dir: [0.2, -0.8, 0.6], lean: 0, bob: 6.5, step: 0, absolute: true, neckF: 6, hipF: -2,
    feet: [[-3.2, 0, -6], [3.2, 0, 3]] },
  { ...LIE, bob: -3 },
  { ...LIE, bob: 0 },
  { ...LIE, bob: -1 },
  { ...LIE, bob: 0 },
];

/** 双手武器（重劈）：左手握在右手前面一点的剑柄上 */
const TWO_HAND_GAP = 2.6;

export interface PoseOptions {
  /** 哪只手拿着武器、怎么拿：持武器的手不再垂在身侧摆动 */
  armedR?: Hold;
  armedL?: Hold;
}

export function makePose(dir: Dir5, frame: number, opts: PoseOptions = {}): Pose {
  const [sin, cos] = TRIG[dir];
  const { anim, t, walk8 } = frameInfo(frame);
  const walking = anim === 'walk';
  const stance = STANCES[opts.armedR ?? 'none'];
  const isExtra = (EXTRAS as string[]).includes(anim);
  const act: ActKey | undefined =
    anim === 'ready' ? { ...stance.key, bob: t === 1 ? 0.7 : 0 } :
    isExtra ? extraKey(anim as ExtraId, t, opts.armedR ?? 'none') :
    anim !== 'idle' && anim !== 'walk' ? ACTION_KEYS[anim as ActionId][t] : undefined;
  const prevAct = act && anim !== 'ready' && !isExtra && t > 0 ? ACTION_KEYS[anim as ActionId][t - 1] : undefined;
  // 双手握：重劈，以及大剑的战斗待机、格挡
  const twoHand = anim === 'heavy' || ((anim === 'ready' || anim === 'guard') && opts.armedR === 'shoulder');

  let s = 0, c = 0, bob = 0, phase = 0;
  if (walking) {
    const n = walk8 ? 8 : 6;
    phase = ((t + 0.5) / n) * Math.PI * 2;
    s = Math.sin(phase);
    c = Math.cos(phase);
    bob = t % (n / 2) === 1 ? 1 : 0; // 迈到最大步幅时身体下沉
  } else if (act) {
    // 战斗中重心一直压低（动作捕捉的帧自带下蹲）；倒地的帧是站直了再转 90°，bob 另作离地高度
    bob = act.lying ? 0 : act.absolute ? act.bob : act.bob + stance.crouch;
  } else {
    bob = t === 1 ? 1 : 0; // 呼吸
  }
  // 走路时上身前倾一点；站着时重心偏向一条腿，不是立正
  // 前倾：战斗中以站姿的前倾为底，动作在此基础上再加
  const lean = act ? act.lean + (anim === 'ready' || isExtra || act.absolute ? 0 : stance.key.lean * 0.5) : walking ? 1 : 0;
  /** 颈部、髋部的前后偏移（局部 fwd）：上身整体前倒，屁股往后坐一点 */
  const neckF = act?.neckF ?? lean * 0.95, hipF = act?.hipF ?? -lean * 0.3;

  const proj = (side: number, up: number, fwd: number, tilt = TILT): Joint => {
    const near = fwd * cos - side * sin;
    return { x: CX + side * cos + fwd * sin, y: FOOT_Y - up + near * tilt, near };
  };

  const head = proj(walking || act ? 0 : -0.3, HEAD - bob, neckF + lean * 0.25);

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
    const shoulder = proj(7.2 * sign, SHOULDER - bob, neckF * 0.95, 0.12);
    let j: Joint, elbow: Joint;
    // 武器在局部坐标里的指向（side, up, fwd）
    let wd: V3 = [0.14 * sign, 0.95, 0.1];
    let trailFrom: number | undefined;
    let mid = hold === 'up' || hold === 'shoulder';

    // 弓拿在左手：左手是「持武器」的那只
    const isBowArm = hold === 'bow';
    if (act && (sign < 0 || isBowArm || twoHand)) {
      // 动作帧：手的位置来自关键帧；双手重劈时左手握在剑柄上
      let p: V3 = sign < 0 ? act.R : act.L;
      if (sign > 0 && twoHand) {
        p = [act.R[0] + act.dir[0] * TWO_HAND_GAP, act.R[1] + act.dir[1] * TWO_HAND_GAP, act.R[2] + act.dir[2] * TWO_HAND_GAP];
      }
      j = proj(p[0], p[1] - bob, p[2] + neckF * 0.7);
      // 肘：肩和手的中点，往外、往下撇一点
      elbow = proj((7.2 * sign + p[0]) / 2 + 1.4 * sign, (SHOULDER + p[1]) / 2 - 1.6 - bob, (neckF * 1.7 + p[2]) / 2 - 0.8);
      if (isBowArm) wd = act.dir.map((v, i) => (i === 0 ? v * sign : v)) as V3;
      else if (sign < 0) {
        wd = act.dir;
        if (act.trail && prevAct) trailFrom = screenDir(prevAct.dir).angle;
        mid = mid || act.dir[1] > 0.4;
      }
    } else if (act && sign > 0) {
      // 动作帧里不拿武器的左手
      j = proj(act.L[0], act.L[1] - bob, act.L[2] + neckF * 0.7);
      elbow = proj((7.2 + act.L[0]) / 2 + 1.4, (SHOULDER + act.L[1]) / 2 - 1.6 - bob, (neckF * 1.7 + act.L[2]) / 2 - 0.8);
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
    const hipUp = HIP - bob;
    const hip = proj(2.8 * sign, hipUp, hipF, 0);
    // 先求脚的局部坐标（side, up, fwd），再算膝盖
    let fs: number, fu: number, ff: number;
    if (act) {
      // 战斗站姿：左脚在前、右脚在后，攻击时前脚再往前跨
      [fs, fu, ff] = act.feet ? act.feet[sign < 0 ? 0 : 1] : sign < 0 ? [-3.4, 0, -stance.back - act.step * 0.3] : [3.4, 0, stance.front + act.step * 0.6];
    } else if (!walking) {
      // 稍息：右脚略向前、向外
      [fs, fu, ff] = sign < 0 ? [-3.6, 0, 1.5] : [3, 0, -0.4];
    } else {
      const swing = -s * sign; // 右脚 fwd = +s
      const lift = Math.max(0, -c * sign) * 2.6; // 向前摆的那只脚抬起
      [fs, fu, ff] = [3 * sign, lift, 5 * swing];
    }
    // 膝盖：大腿和小腿一样长，髋到脚的距离不够腿长时膝盖往前顶出去（下蹲、跨步时腿是弯的）
    const LEG = 8.2;
    const ds = fs - 2.8 * sign, du = fu - hipUp, df = ff - hipF;
    const dist = Math.hypot(ds, du, df);
    const bend = Math.sqrt(Math.max(0, LEG * LEG - (dist / 2) ** 2));
    // 弯曲方向：大致朝前，后脚的膝盖也朝前（往下压）
    const knee = proj(2.8 * sign + ds / 2, hipUp + du / 2, hipF + df / 2 + bend * 0.9, 0.2);
    return { id, hip, knee, foot: proj(fs, fu, ff) };
  };
  const legR = leg('R', -1), legL = leg('L', 1);
  const legs: [Leg, Leg] = legR.foot.near <= legL.foot.near ? [legR, legL] : [legL, legR];

  return {
    dir, sin, cos, frame, anim, t, phase, bob, proj,
    head,
    neckY: FOOT_Y - NECK + bob,
    neckUp: NECK - bob,
    torsoHalf: 6.5 - 1.9 * Math.abs(sin),
    torsoX: (r: number) => {
      const k = Math.max(0, Math.min(1, r / (NECK - HIP)));
      return CX + (neckF + (hipF - neckF) * k) * sin;
    },
    armR, armL,
    handR: armR.hand,
    handL: armL.hand,
    legs,
    fx: act?.fx,
    lying: act?.lying ? { lift: Math.max(0, -act.bob) } : undefined,
    flash: anim === 'hurt' && t === 0,
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
