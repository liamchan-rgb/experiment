import { pal, BASE, DARK, HI, LIGHT, OUTLINE } from '../../pixel/palette';
import { DARKEN, LIGHTEN } from '../../pixel/Brush';
import { CX } from '../../character/rig';
import type { DrawCtx, ItemDef, PartDef } from '../../character/types';
import { armLayer, armOf, farBias, frontX, sleeveParts, torsoShape } from '../shared';

/**
 * 桌游物品表里的四件护甲（armor 槽 → 纸娃娃的 top 槽）：
 *   皮甲 leatherArmor、符文甲 runeArmor、星辉甲 starlightArmor、龙纹甲 dragonArmor
 * 结构都一样：躯干甲片 + 袖子 + 护肩（护肩各占一个部件，近侧压在手臂前、远侧被身体挡住）。
 * 金属件的明暗对比比布料大，并带一道高光，读起来才像金属。
 */

const ROWS = 13.2;

/** 金属的明暗：对比拉大，受光处一道高光 */
function metal(c: DrawCtx, lam: number, bias = 0): number {
  return c.g.t(lam * 1.35 + bias);
}

interface PauldronOpts {
  key?: string;
  trimKey?: string;
  r?: number;
  spikes?: boolean;
  /** 只在左肩（皮甲的单边护肩） */
  only?: 'L' | 'R';
}

function pauldrons(o: PauldronOpts): PartDef[] {
  const make = (side: 'R' | 'L'): PartDef => ({
    layer: armLayer(side),
    draw: (c) => {
      const { g } = c;
      const a = armOf(c, side);
      const fb = farBias(c, a.hand);
      const r = o.r ?? 3;
      const x = a.shoulder.x, y = a.shoulder.y + 0.6;
      c.pal(o.key);
      g.ellipse(x, y, r + 0.6, r * 0.85, (lam, _nx, ny) => {
        if (o.trimKey && ny > 0.45) {
          c.pal(o.trimKey);
          return metal(c, lam, fb + 0.1);
        }
        c.pal(o.key);
        return metal(c, lam, fb);
      });
      if (o.spikes) {
        c.pal(o.trimKey);
        const sx = side === 'R' ? -1 : 1;
        for (const k of [-0.5, 0.6]) {
          const bx = x + k * r * c.pose.cos * sx;
          g.tri({ x: bx - 1, y: y - r * 0.6 }, { x: bx + 1, y: y - r * 0.6 }, { x: bx + 0.4 * sx * c.pose.cos, y: y - r - 2.4 }, k < 0 ? LIGHT : BASE);
        }
      }
    },
  });
  if (o.only) return [make(o.only)];
  return [make('L'), make('R')];
}

/** 腰带（只画在已有的甲片上） */
function belt(c: DrawCtx, r0: number, r1: number, key: string, buckleKey?: string): void {
  const { g } = c;
  c.pal(key);
  torsoShape(c, ROWS, { flare: 2 }, (lam, _nx, r) => (r < r0 || r > r1 ? -1 : r > r1 - 0.5 ? OUTLINE : g.t(lam, -0.1)));
  if (buckleKey && c.pose.cos > 0.3) {
    const fx = frontX(c), ny = c.pose.neckY;
    c.pal(buckleKey);
    g.rect(fx - 1.1, ny + r0, 2.2, r1 - r0, (u, v) => (u < fx - 0.3 || v < ny + r0 + 0.5 ? HI : DARK));
  }
}

// ---------------------------------------------------------------- 皮甲

const leather = pal('leather-armor', '#140a06', '#3c2412', '#6a4224', '#9a6a3a', '#c8975c');
const leatherDark = pal('leather-strap', '#0c0604', '#24140a', '#3e2614', '#5e3c20', '#80583a');
const brass = pal('leather-brass', '#2e1a06', '#74501a', '#b8862e', '#e8c060', '#fff0b0');
const linen = pal('leather-linen', '#3a3428', '#7a7060', '#b0a68e', '#dcd2b8', '#f6f0de');

export const leatherArmor: ItemDef = {
  id: 'top_leather_armor',
  name: '皮甲',
  slot: 'top',
  gameItem: 'leatherArmor',
  palettes: { main: leather, strap: leatherDark, metal: brass, cloth: linen },
  parts: [
    {
      layer: 'top',
      draw: (c) => {
        const { g, pose } = c;
        const ny = pose.neckY, hw = pose.torsoHalf;
        c.pal('main');
        torsoShape(c, ROWS, { flare: 2.2 }, (lam, _nx, r) => {
          if (r < 2.4) return OUTLINE;
          if (r < 3.4) return DARK;
          // 胸口和腹部两块皮片，中间一道接缝
          return g.t(lam, r > 6.6 && r < 7.2 ? -0.5 : r > 10.6 ? -0.15 : 0.05);
        });
        g.clip = true;
        // 缝线：接缝上方一排亮点
        for (let u = CX - hw + 1; u < CX + hw - 0.5; u += 1.6) g.dot(u, ny + 6.2, LIGHTEN);
        if (pose.cos > -0.3) {
          // 斜挎的皮带：左肩到右腰
          c.pal('strap');
          const s = pose.cos;
          g.fill(CX - hw - 1, ny + 2, CX + hw + 1, ny + 12, (u, v) => {
            const k = (v - ny - 2.5) / 9;
            const mid = CX + hw * 0.9 * s * (0.8 - 1.7 * k) + pose.sin * hw * 0.5;
            return Math.abs(u - mid) < 1.1 ? (u < mid - 0.3 ? LIGHT : BASE) : -1;
          });
          c.pal('metal');
          const bx = CX + hw * 0.9 * s * (0.8 - 1.7 * 0.35) + pose.sin * hw * 0.5;
          g.dot(bx, ny + 5.7, HI);
        }
        g.clip = false;
        belt(c, 9.6, 11.2, 'strap', 'metal');
      },
    },
    ...sleeveParts({ key: 'cloth', length: 0.62, r: 1.9 }),
    ...pauldrons({ key: 'main', trimKey: 'strap', r: 2.8, only: 'L' }),
  ],
};

// ---------------------------------------------------------------- 符文甲

const slate = pal('rune-steel', '#0a0e14', '#222c3a', '#3e4e62', '#6a7e96', '#a8bccc');
const steelTrim = pal('rune-trim', '#141820', '#46505e', '#7e8a98', '#bcc6d0', '#eef4fa');
const runeGlow = pal('rune-glow', '#06343a', '#0e7a80', '#28c6c0', '#86f4e4', '#e8fff8');
const runeCloth = pal('rune-cloth', '#0a0a14', '#1c1c34', '#2e2e52', '#46467a', '#6a6aa4');

export const runeArmor: ItemDef = {
  id: 'top_rune_armor',
  name: '符文甲',
  slot: 'top',
  gameItem: 'runeArmor',
  palettes: { main: slate, trim: steelTrim, rune: runeGlow, cloth: runeCloth },
  parts: [
    {
      layer: 'top',
      draw: (c) => {
        const { g, pose } = c;
        const ny = pose.neckY;
        c.pal('main');
        torsoShape(c, ROWS, { flare: 2.4 }, (lam, _nx, r) => {
          if (r < 2.4) return OUTLINE;
          if (r > ROWS - 2) {
            c.pal('trim'); // 下摆的钢边
            return metal(c, lam, r > ROWS - 0.6 ? -0.4 : 0.1);
          }
          c.pal('main');
          // 胸甲往下分成两段，段与段之间一道深缝
          return metal(c, lam, r > 7.6 && r < 8.3 ? -0.8 : r < 3.4 ? -0.5 : 0);
        });
        g.clip = true;
        c.pal('rune');
        if (pose.cos > 0.3) {
          // 正面：胸口一道竖着的符文，两侧各一个符点
          const fx = frontX(c);
          g.line(fx, ny + 3.6, fx, ny + 7, LIGHT);
          g.dot(fx, ny + 4.4, HI);
          g.dot(fx - 2.6, ny + 5.4, BASE);
          g.dot(fx + 2.6, ny + 5.4, BASE);
          g.line(fx - 1.6, ny + 9.4, fx + 1.6, ny + 9.4, LIGHT);
        } else if (pose.cos < -0.3) {
          const bx = CX - pose.torsoHalf * 0.4 * pose.sin;
          g.line(bx - 2.4, ny + 5, bx + 2.4, ny + 5, LIGHT);
          g.dot(bx, ny + 5, HI);
        } else {
          g.line(CX + 0.6 * pose.sin, ny + 4, CX + 0.6 * pose.sin, ny + 6.6, LIGHT);
        }
        g.clip = false;
      },
    },
    ...sleeveParts({ key: 'cloth', cuffKey: 'trim', r: 2 }),
    ...pauldrons({ key: 'main', trimKey: 'trim', r: 3.1 }),
    {
      // 护肩上的符点（不描边，亮的）
      layer: 'arm_front',
      outline: false,
      draw: (c) => {
        const a = c.pose.armL.hand.front ? c.pose.armL : c.pose.armR;
        c.pal('rune');
        c.g.clip = true;
        c.g.dot(a.shoulder.x, a.shoulder.y + 0.2, HI);
        c.g.clip = false;
      },
      mask: 'below',
    },
  ],
};

// ---------------------------------------------------------------- 星辉甲

const silver = pal('star-armor', '#1a1e2c', '#5a6276', '#9aa4b8', '#d6dde8', '#ffffff');
const starGold = pal('star-gold', '#3a2206', '#8a5a14', '#d4a030', '#f6d670', '#fff8c8');
const starBlue = pal('star-cloth', '#08122e', '#173064', '#2a52a0', '#4a7ed0', '#86b4ee');
const starGem = pal('star-gem', '#0e3a6a', '#2a7ac0', '#5cbcf0', '#b0ecff', '#ffffff');

export const starlightArmor: ItemDef = {
  id: 'top_starlight_armor',
  name: '星辉甲',
  slot: 'top',
  gameItem: 'starlightArmor',
  palettes: { main: silver, trim: starGold, cloth: starBlue, gem: starGem },
  parts: [
    {
      layer: 'top',
      draw: (c) => {
        const { g, pose } = c;
        const ny = pose.neckY;
        c.pal('cloth');
        // 底下的蓝布衣：下摆从甲片下面露出来
        torsoShape(c, ROWS + 0.6, { flare: 2.6 }, (lam, _nx, r) => (r < 9.5 ? -1 : g.t(lam, -0.05)));
        c.pal('main');
        torsoShape(c, 10.2, { flare: 0.8 }, (lam, nx, r) => {
          if (r < 2.4) return OUTLINE;
          if (r > 9.3 || Math.abs(Math.abs(nx) - 0.97) < 0.03) {
            c.pal('trim'); // 胸甲的金边
            return metal(c, lam, 0.15);
          }
          c.pal('main');
          return metal(c, lam, r < 3.4 ? -0.4 : 0.1);
        });
        if (pose.cos > 0.3) {
          // 胸口的星形纹章
          const fx = frontX(c), y = ny + 5.6;
          c.pal('gem');
          g.clip = true;
          g.fill(fx - 2.4, y - 2.4, fx + 2.4, y + 2.4, (u, v) => {
            const ax = Math.abs(u - fx), ay = Math.abs(v - y);
            if (ax + ay > 2.6 || Math.min(ax, ay) > 0.5) return -1;
            return ax + ay < 1 ? HI : u < fx || v < y ? LIGHT : BASE;
          });
          g.clip = false;
        } else if (pose.cos < -0.3) {
          c.pal('trim');
          g.clip = true;
          g.line(CX - 2, ny + 4.6, CX + 2, ny + 4.6, LIGHT);
          g.clip = false;
        }
      },
    },
    ...sleeveParts({ key: 'cloth', cuffKey: 'main', r: 2 }),
    ...pauldrons({ key: 'main', trimKey: 'trim', r: 3.2 }),
  ],
};

// ---------------------------------------------------------------- 龙纹甲

const crimson = pal('dragon-armor', '#1e0408', '#4e0c14', '#8a1a20', '#c43c30', '#ee7a56');
const dragonGold = pal('dragon-gold', '#341a04', '#80500e', '#c88e22', '#f0c858', '#fff2b8');
const charcoal = pal('dragon-cloth', '#08080a', '#1a1a20', '#2c2c34', '#46464e', '#6a6a72');

export const dragonArmor: ItemDef = {
  id: 'top_dragon_armor',
  name: '龙纹甲',
  slot: 'top',
  gameItem: 'dragonArmor',
  palettes: { main: crimson, trim: dragonGold, cloth: charcoal },
  parts: [
    {
      layer: 'top',
      draw: (c) => {
        const { g, pose } = c;
        const ny = pose.neckY;
        c.pal('main');
        torsoShape(c, ROWS + 0.4, { flare: 3 }, (lam, _nx, r, u, v) => {
          if (r < 2.4) return OUTLINE;
          if (r > ROWS - 1.8) {
            c.pal('trim'); // 腰甲的金边
            return metal(c, lam, r > ROWS - 0.2 ? -0.5 : 0.1);
          }
          c.pal('main');
          // 龙鳞：错开的一排排弧形甲片，每片下缘压暗
          const row = Math.floor((v - ny) / 1.9);
          const cu = (u + (row % 2) * 1.3) / 2.6;
          const fu = cu - Math.floor(cu) - 0.5;
          const fv = (v - ny) / 1.9 - row;
          const edge = fv > 0.72 - fu * fu * 1.2;
          return metal(c, lam, (edge ? -0.75 : 0.05) + (r < 3.4 ? -0.4 : 0));
        });
        if (pose.cos > 0.3) {
          // 胸口的金色龙首纹：一个倒三角 + 两只角
          const fx = frontX(c), y = ny + 4.2;
          c.pal('trim');
          g.clip = true;
          g.tri({ x: fx - 2.2, y }, { x: fx + 2.2, y }, { x: fx, y: y + 3.4 }, LIGHT);
          g.dot(fx, y + 1, HI);
          g.line(fx - 2.2, y, fx - 3.2, y - 1.2, BASE);
          g.line(fx + 2.2, y, fx + 3.2, y - 1.2, BASE);
          g.clip = false;
        }
        g.clip = true;
        g.line(CX - 0.4, ny + 3, CX - 0.4, ny + 3, DARKEN);
        g.clip = false;
      },
    },
    ...sleeveParts({ key: 'cloth', cuffKey: 'trim', r: 2 }),
    ...pauldrons({ key: 'main', trimKey: 'trim', r: 3.3, spikes: true }),
  ],
};
