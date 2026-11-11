/**
 * 键盘输入：WASD 或方向键，组合键得到斜向；输出已归一化的移动向量。
 */
export class Keyboard {
  private down = new Set<string>();

  constructor(target: Window = window) {
    target.addEventListener('keydown', (e) => {
      if (isTyping(e)) return;
      this.down.add(e.code);
      if (e.code.startsWith('Arrow') || e.code === 'Space') e.preventDefault();
    });
    target.addEventListener('keyup', (e) => this.down.delete(e.code));
    target.addEventListener('blur', () => this.down.clear());
  }

  /** x：右为正；z：朝镜头（屏幕下方）为正。斜向时长度仍为 1。 */
  axis(): { x: number; z: number } {
    const k = this.down;
    let x = 0, z = 0;
    if (k.has('KeyA') || k.has('ArrowLeft')) x -= 1;
    if (k.has('KeyD') || k.has('ArrowRight')) x += 1;
    if (k.has('KeyW') || k.has('ArrowUp')) z -= 1;
    if (k.has('KeyS') || k.has('ArrowDown')) z += 1;
    const len = Math.hypot(x, z);
    return len > 0 ? { x: x / len, z: z / len } : { x: 0, z: 0 };
  }

  /** 测试 / 演示用：用代码按下或松开一个键 */
  set(code: string, pressed: boolean): void {
    if (pressed) this.down.add(code);
    else this.down.delete(code);
  }
}

function isTyping(e: KeyboardEvent): boolean {
  const t = e.target as HTMLElement | null;
  return !!t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA');
}
