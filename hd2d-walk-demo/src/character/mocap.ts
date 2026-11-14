import data from './mocap.json';

/**
 * 动作捕捉：把原型动作包（Momji Pixel「Free Prototype Character Asset Pack」，CC BY 4.0）里
 * 分色小人的逐帧姿势，换算成 Q 版骨架的关键帧。tools/extract_mocap.py 先从图里量出各关节（mocap.json）。
 *
 * 原型是 5 头身、四肢细长，所以不搬坐标，只搬「相对关系」：
 *   手 = 我们的肩 + （原型的手 − 原型的肩）× 手臂比例
 *   脚 = 我们的髋 + （原型的脚 − 原型的髋）× 腿长比例
 *   躯干前倾 = 原型颈部相对髋部的前后偏移
 *   下蹲 = 原型髋部比站立时低了多少（再放大一点，Q 版的腿短）
 *   武器指向 = 原型的剑（被刀光挡住的帧用前臂方向代替）
 * 原型朝右，正好对应我们的右侧视角（E）；其他方向由骨架的 3D 局部坐标自动得到。
 */

type P2 = [number, number] | null;
interface Limb { root: P2; joint: P2; end: P2 }
interface Frame {
  head: P2; neck: P2; hip: P2;
  armNear: Limb | null; armFar: Limb | null; legA: Limb | null; legB: Limb | null;
  sword: { hilt: P2; tip: P2 } | null;
  smear: number;
}

type V3 = [number, number, number];
export interface CapturedKey {
  R: V3;
  L: V3;
  dir: V3;
  /** 颈 / 髋的前后偏移（局部 fwd，单位） */
  neckF: number;
  hipF: number;
  bob: number;
  /** 右脚 / 左脚（局部坐标） */
  feet: [V3, V3];
  trail?: boolean;
}

const clips = (data as unknown as { clips: Record<string, Frame[]> }).clips;

/** 我们骨架的尺寸（和 rig.ts 一致） */
const OUR = { shoulderUp: 29, shoulderSide: 6.4, hipUp: 16, hipSide: 3.2, arm: 12.5, leg: 15.5 };

// 原型站立时的尺寸：手臂长、腿长、髋高
const idle = clips.idle[0];
const theirArm = Math.hypot(idle.armNear!.end![0] - idle.armNear!.root![0], idle.armNear!.end![1] - idle.armNear!.root![1]);
const theirHip = idle.hip![1];
const kArm = OUR.arm / theirArm;
const kLeg = OUR.leg / theirHip;

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
function norm(x: number, y: number): [number, number] {
  const l = Math.hypot(x, y) || 1;
  return [x / l, y / l];
}

/**
 * 把一段原型动画换算成关键帧。
 * pick：取哪几帧（默认全部）；crouch：额外的下蹲（Q 版站姿要低一点才有气势）；leanGain：前倾放大
 */
export function captured(name: string, opts: { pick?: number[]; crouch?: number; leanGain?: number; reach?: number } = {}): CapturedKey[] {
  const frames = clips[name];
  if (!frames) throw new Error(`mocap clip ${name} missing`);
  const pick = opts.pick ?? frames.map((_, i) => i);
  const out: CapturedKey[] = [];
  let last: CapturedKey | undefined;
  for (const i of pick) {
    const f = frames[i];
    const hip = f.hip ?? [0, theirHip];
    const neck = f.neck ?? [hip[0], hip[1] + 8];
    const neckF = clamp((neck[0] - hip[0]) * 0.85 * (opts.leanGain ?? 1), -3.5, 6);
    const hipF = clamp(hip[0] * kLeg * 0.6, -3, 3) - neckF * 0.2;
    const bob = Math.max(0, theirHip - hip[1]) * kLeg * 1.6 + (opts.crouch ?? 1.2);
    const shUp = OUR.shoulderUp - bob, shF = neckF * 0.95;
    const reach = opts.reach ?? 1;
    const hand = (limb: Limb | null, side: number, prev: V3 | undefined): V3 => {
      if (!limb?.root || !limb.end) return prev ?? [side, shUp - 11, shF + 1];
      const dx = (limb.end[0] - limb.root[0]) * kArm * reach, dy = (limb.end[1] - limb.root[1]) * kArm * reach;
      return [side, shUp + dy, shF + dx];
    };
    const R = hand(f.armNear, -OUR.shoulderSide, last?.R);
    const L = hand(f.armFar, OUR.shoulderSide, last?.L);
    // 武器指向：有剑就用剑，否则用前臂的方向
    let dir: V3 = last?.dir ?? [0.1, 0.4, 0.9];
    if (f.sword?.hilt && f.sword.tip) {
      const [x, y] = norm(f.sword.tip[0] - f.sword.hilt[0], f.sword.tip[1] - f.sword.hilt[1]);
      dir = [0.1, y, x];
    } else if (f.armNear?.joint && f.armNear.end) {
      const [x, y] = norm(f.armNear.end[0] - f.armNear.joint[0], f.armNear.end[1] - f.armNear.joint[1]);
      dir = [0.1, y, x];
    }
    const foot = (limb: Limb | null, side: number, prev: V3 | undefined): V3 => {
      if (!limb?.end) return prev ?? [side, 0, 0];
      return [side, Math.max(0, limb.end[1] * kLeg), clamp((limb.end[0] - hip[0]) * kLeg * 0.85, -7, 8) + hipF];
    };
    // 红腿（站立时在前）当左脚 = 前脚
    const feet: [V3, V3] = [foot(f.legA, -OUR.hipSide, last?.feet[0]), foot(f.legB, OUR.hipSide, last?.feet[1])];
    const key: CapturedKey = { R, L, dir, neckF, hipF, bob, feet, trail: f.smear > 40 };
    out.push(key);
    last = key;
  }
  return out;
}
