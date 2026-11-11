import { IDLE_FRAMES, WALK_FRAMES } from './rig';

/** 动画状态机：待机（2 帧呼吸）⇄ 行走（6 帧循环）。输出 sheet 的列号。 */
export class Animator {
  state: 'idle' | 'walk' = 'idle';
  /** 当前 sheet 列号 */
  frame = 0;
  private t = 0;

  static readonly IDLE_FPS = 1.6;
  static readonly WALK_FPS = 10;

  update(dt: number, moving: boolean): void {
    const next = moving ? 'walk' : 'idle';
    if (next !== this.state) {
      this.state = next;
      this.t = 0;
    }
    this.t += dt;
    if (this.state === 'idle') {
      this.frame = IDLE_FRAMES[Math.floor(this.t * Animator.IDLE_FPS) % IDLE_FRAMES.length];
    } else {
      this.frame = WALK_FRAMES[Math.floor(this.t * Animator.WALK_FPS) % WALK_FRAMES.length];
    }
  }
}
