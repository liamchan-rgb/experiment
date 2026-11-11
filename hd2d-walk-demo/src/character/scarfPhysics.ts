import { PixelLayer } from '../pixel/PixelLayer';
import { Brush } from '../pixel/Brush';
import { HI, LIGHT, type Palette } from '../pixel/palette';

/**
 * 围巾尾的次级运动：一条 Verlet 质点链。
 * 根部钉在颈后的挂点上；角色移动时受到反向的「风」，停下时在重力和微风里垂落摆动。
 * 坐标是单位坐标（y 向下），和精灵用同一套尺度。
 */
export class ScarfTail {
  private pts: { x: number; y: number; px: number; py: number }[] = [];
  private ready = false;

  constructor(private segments = 7, private segLen = 2.7) {
    this.reset();
  }

  private reset(): void {
    this.pts = [];
    for (let i = 0; i <= this.segments; i++) this.pts.push({ x: 0, y: 0, px: 0, py: 0 });
    this.ready = false;
  }

  configure(segments: number, segLen: number): void {
    if (segments === this.segments && segLen === this.segLen) return;
    this.segments = segments;
    this.segLen = segLen;
    this.reset();
  }

  /**
   * @param ax,ay  根部挂点
   * @param vx,vy  角色在屏幕空间的速度（单位/秒）
   * @param rest   静止时尾巴偏向哪一侧（-1 左 / +1 右）
   */
  step(dt: number, ax: number, ay: number, vx: number, vy: number, rest: number, time: number): void {
    const p = this.pts;
    if (!this.ready) {
      p.forEach((q, i) => {
        q.x = q.px = ax + rest * i * 0.8;
        q.y = q.py = ay + i * this.segLen * 0.9;
      });
      this.ready = true;
    }
    dt = Math.min(dt, 1 / 30);
    const damp = Math.pow(0.02, dt); // 每秒保留 2% 的速度
    p[0].x = ax;
    p[0].y = ay;
    for (let i = 1; i < p.length; i++) {
      const q = p[i];
      const k = i / (p.length - 1);
      // 风 = 反向的移动速度 + 一点带相位差的微风
      const gust = Math.sin(time * 2.3 + i * 0.9) * 24 + Math.sin(time * 5.1 + i * 1.7) * 9;
      const fx = -vx * 9 + rest * 50 + gust * (0.4 + k);
      const fy = 200 - vy * 9 + Math.cos(time * 3.1 + i) * 12 * k;
      const nx = q.x + (q.x - q.px) * damp + fx * dt * dt;
      const ny = q.y + (q.y - q.py) * damp + fy * dt * dt;
      q.px = q.x; q.py = q.y;
      q.x = nx; q.y = ny;
    }
    // 距离约束：每节保持固定长度
    for (let it = 0; it < 4; it++) {
      for (let i = 1; i < p.length; i++) {
        const a = p[i - 1], b = p[i];
        const dx = b.x - a.x, dy = b.y - a.y;
        const d = Math.hypot(dx, dy) || 1e-4;
        b.x = a.x + (dx / d) * this.segLen;
        b.y = a.y + (dy / d) * this.segLen;
      }
    }
  }

  /** 把尾巴画成一条带子：根部粗、末端略细，靠近末端有两道浅色条纹，自动描边。 */
  draw(L: PixelLayer, g: Brush, palette: Palette, ox: number, oy: number): void {
    L.clear();
    if (!this.ready) return;
    L.use(palette);
    g.clip = false;
    g.grit = 0.24;
    const pts = this.pts.map((q) => ({ x: q.x + ox, y: q.y + oy }));
    g.anchor(pts[0].x, pts[0].y);
    g.ribbon(pts, (s) => 1.9 - s * 0.5, (lam, _o, s) =>
      (s > 0.74 && s < 0.81) || (s > 0.88 && s < 0.95) ? (lam > 0.2 ? HI : LIGHT) : g.t(lam, 0.05));
    L.outline();
  }
}
