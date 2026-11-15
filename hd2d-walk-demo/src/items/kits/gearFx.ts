import { BASE, HI, LIGHT } from '../../pixel/palette';
import type { DrawCtx, PartDef } from '../../character/types';
import { armOf } from '../shared';
import { at, frameOf } from './weaponKit';

/**
 * 稀有装备拿在手上 / 穿在身上时的主题特效（和图标的主题一致，PartDef.glow：不描边、按 c.phase 0-3 循环）：
 *   传奇权杖宝石辐射光芒、龙牙剑刃口火苗、星辉刃星点闪烁、重剑红宝石闪光、
 *   符文甲符文流光、星辉甲胸口星芒、龙纹甲护肩冒火。
 */

/** 一朵往画面上方飘的小火苗（单位坐标），h 高度，lean 往哪边歪 */
export function flame(c: DrawCtx, x: number, y: number, h: number, lean = 0.4, width = 1.15): void {
  c.g.grit = 0;
  c.g.fill(x - width - 0.6, y - h - 0.6, x + width + 0.6, y + 0.6, (u, v) => {
    const k = (y - v) / h;
    if (k < -0.4 || k > 1) return -1;
    const w = width * (1 - Math.max(0, k)) + 0.12;
    if (Math.abs(u - x - k * lean) > w) return -1;
    return k > 0.55 ? HI : k > 0.1 ? LIGHT : BASE;
  });
}

/** 从一点向外的光芒：n 道，按相位转动、长短交替 */
export function rays(c: DrawCtx, x: number, y: number, n: number, len: number, spin: number): void {
  c.g.grit = 0;
  for (let i = 0; i < n; i++) {
    const a = spin + (i * Math.PI * 2) / n, L = i % 2 ? len * 0.6 : len;
    for (let d = 3.4; d < L; d += 0.6) c.g.dot(x + Math.cos(a) * d, y + Math.sin(a) * d * 0.9, d < L * 0.55 ? HI : LIGHT);
  }
}

/** 四角星 */
export function twinkle(c: DrawCtx, x: number, y: number, arm: number): void {
  c.g.dot(x, y, HI);
  for (let d = 1; d <= arm; d++) for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) c.g.dot(x + dx * d * 0.8, y + dy * d * 0.8, d === arm ? LIGHT : HI);
}

/** 武器上的特效部件：point = 武器上的位置，跟着武器在身前 / 身后 */
export function weaponGlow(draw: (c: DrawCtx, f: NonNullable<ReturnType<typeof frameOf>>) => void, key = 'fx'): PartDef {
  return {
    layer: 'weapon',
    glow: true,
    outline: false,
    draw: (c) => {
      const f = frameOf(c);
      if (!f) return;
      c.pal(key);
      draw(c, f);
    },
  };
}

/** 权杖：宝石四周 8 道转动的光芒 + 一闪的星 */
export const scepterRays = weaponGlow((c, f) => {
  const p = at(f, 37.5);
  rays(c, p.x, p.y, 8, 9.5 + (c.phase % 2) * 2, (c.phase * Math.PI) / 16);
  if (c.phase === 1 || c.phase === 3) twinkle(c, p.x, p.y, 1);
});

/** 龙牙剑：刃口一排跳动的火苗 */
export const fangFlames = weaponGlow((c, f) => {
  for (let i = 0; i < 4; i++) {
    const t = 9 + i * 5 + ((c.phase * 3 + i * 2) % 4) * 0.5;
    const h = 1.6 + ((c.phase + i) % 3) * 0.8;
    const p = at(f, t, -2.6 - (i % 2) * 0.6);
    flame(c, p.x, p.y, h);
  }
});

/** 星辉刃：剑身两侧的星点轮流闪 */
export const bladeStars = weaponGlow((c, f) => {
  const pts = [at(f, 15, -3.4), at(f, 9, 3.2), at(f, 19, 2.6), at(f, 5.5, -2.8)];
  pts.forEach((p, i) => (i === c.phase ? twinkle(c, p.x, p.y, 2) : c.g.dot(p.x, p.y, (i + c.phase) % 2 ? LIGHT : BASE)));
});

/** 重剑：护手红宝石一闪 */
export const rubyGlint = weaponGlow((c, f) => {
  if (c.phase !== 0) return;
  const p = at(f, 3);
  twinkle(c, p.x, p.y, 1);
}, 'gem');

/** 护甲上的特效：画在躯干最上面（被手臂挡住时一起被挡） */
function armorGlow(draw: (c: DrawCtx) => void, layer: PartDef['layer'] = 'top'): PartDef {
  return { layer, glow: true, outline: false, draw };
}

/** 符文甲：一点符文光从腰往胸口流上去，两侧护肩的符点交替亮 */
export const runeFlow = armorGlow((c) => {
  const { pose } = c;
  c.pal('rune');
  c.g.grit = 0;
  if (pose.cos > 0.3) {
    // 胸口竖符文上一段亮光往上流，拖一条短尾巴
    const fx = pose.torsoX(5), y = pose.neckY + 9.6 - c.phase * 1.7;
    for (let k = 0; k < 3; k++) c.g.dot(fx, y + k * 0.7, k === 0 ? HI : LIGHT);
    c.g.dot(fx - 0.7, y, LIGHT); c.g.dot(fx + 0.7, y, LIGHT);
  }
  // 护肩的符点交替亮，亮的那边往上飘一个符文光点
  for (const side of ['L', 'R'] as const) {
    const a = armOf(c, side), on = (c.phase % 2 === 0) === (side === 'L');
    if (!a.hand.front && Math.abs(pose.cos) < 0.3) continue;
    c.g.dot(a.shoulder.x, a.shoulder.y + 0.2, on ? HI : LIGHT);
    if (on) c.g.dot(a.shoulder.x + (side === 'L' ? 1 : -1) * pose.cos, a.shoulder.y - 2.2 - (c.phase >> 1) * 1.6, HI);
  }
}, 'arm_front');

/** 星辉甲：胸口星章放出十字星芒，长短跟着相位 */
export const crestBurst = armorGlow((c) => {
  const { pose } = c;
  if (pose.cos <= 0.3) return;
  c.pal('gem');
  const x = pose.torsoX(5), y = pose.neckY + 5.4, L = 4 + (c.phase % 2) * 2.5;
  c.g.grit = 0;
  for (let d = 3.6; d < L + 3; d += 0.7) for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) c.g.dot(x + dx * d, y + dy * d, d < 5 ? HI : LIGHT);
});

/** 龙纹甲：两边护肩的尖角上各冒一朵火 */
export const pauldronFlames = (['L', 'R'] as const).map((side) => armorGlow((c) => {
  const a = armOf(c, side);
  c.pal('fx');
  const h = 4.2 + ((c.phase + (side === 'L' ? 0 : 2)) % 4) * 1.1;
  // 护肩在大头下面，火苗画在最上层，从肩膀外侧窜起来才看得见
  const out = (side === 'L' ? 1 : -1) * c.pose.cos * 2.6;
  if (!a.hand.front && Math.abs(c.pose.cos) < 0.3) return;
  flame(c, a.shoulder.x + out, a.shoulder.y - 2, h, 0.25, 1.7);
}, 'weapon_front'));
