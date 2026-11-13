import { pal, BASE, DARK, HI, LIGHT } from '../../pixel/palette';
import type { DrawCtx, ItemDef } from '../../character/types';
import { frameOf } from '../kits/weaponKit';

/**
 * 猎弓：拿在左手（hold: 'bow'），普通攻击是射箭（shoot）：举弓搭箭 → 满弦 → 放箭 → 回位。
 * 弓身是一道弧，弓臂两端往射手一侧收；拉弦时弦从两端连到右手，搭着一支箭；放箭那一帧画一道飞出去的箭影。
 */
const wood = pal('bow-wood', '#1a0e06', '#4e2e14', '#86562a', '#bc8644', '#e8b874');
const wrap = pal('bow-wrap', '#0e1408', '#24341a', '#3e5a2a', '#62843e', '#90b062');
const string = pal('bow-string', '#3a3628', '#8a826a', '#c8c0a4', '#ece6d0', '#ffffff');
const arrow = pal('bow-arrow', '#1a1410', '#5a4a38', '#9a8466', '#d2c0a0', '#fff4dc');
const fletch = pal('bow-fletch', '#3a0c0c', '#8a2420', '#c84a3a', '#ec8a6a', '#ffd0b8');

const LIMB = 13;

export const huntingBow: ItemDef = {
  id: 'weapon_hunting_bow',
  name: '猎弓',
  slot: 'weapon_main',
  hold: 'bow',
  gameItem: 'huntingBow',
  palettes: { wood, wrap, string, arrow, fletch },
  parts: [
    // 弓身描边；弦和箭只有 1 像素宽，单独一个不描边的部件
    { layer: 'weapon', draw: (c) => drawBow(c, true) },
    { layer: 'weapon', outline: false, draw: (c) => drawBow(c, false) },
  ],
};

function drawBow(c: DrawCtx, body: boolean): void {
  {
    {
        const f = frameOf(c);
        if (!f) return;
        const { g, pose } = c;
        // 面朝方向在画面上的投影：弓身往这一侧鼓，弓梢往反方向收
        const fx = pose.sin, fy = pose.cos * 0.35;
        const px = -f.dy, py = f.dx;
        const side = px * fx + py * fy;
        const sgn = side >= 0 ? 1 : -1;
        const bulge = 2.4 * Math.max(0.35, Math.min(1, Math.abs(side) * 1.4));
        const pt = (t: number) => {
          const back = -sgn * bulge * (t / LIMB) ** 2;
          return { x: f.x + f.dx * t * f.k + px * back, y: f.y + f.dy * t * f.k + py * back };
        };
        const pts = Array.from({ length: 13 }, (_, i) => pt(-LIMB + (i * 2 * LIMB) / 12));
        if (body) {
        c.pal('wood');
        g.ribbon(pts, (s) => 0.95 - 0.45 * Math.abs(s - 0.5) * 2, (lam, o) => (o < -0.3 ? LIGHT : o > 0.4 ? DARK : g.t(lam) > LIGHT ? HI : BASE));
        c.pal('wrap');
        g.ribbon([pt(-1.8), pt(0), pt(1.8)], () => 1.05, (_l, o) => (o < 0 ? LIGHT : DARK));
        return;
        }

        const top = pt(LIMB), bottom = pt(-LIMB);
        const drawing = pose.fx === 'arrow';
        const hand = pose.handR;
        c.pal('string');
        if (drawing && pose.anim === 'shoot') {
          g.line(top.x, top.y, hand.x, hand.y + 0.4, LIGHT);
          g.line(bottom.x, bottom.y, hand.x, hand.y + 0.4, BASE);
          // 箭：从右手指向前方，越过弓身
          const ax = pose.sin, ay = pose.cos * 0.35 + 0.02;
          const al = Math.hypot(ax, ay) || 1;
          const ux = ax / al, uy = ay / al;
          const len = 15 * (0.4 + 0.6 * Math.min(1, al));
          const tx = hand.x + ux * len, ty = hand.y + 0.4 + uy * len;
          c.pal('arrow');
          g.line(hand.x, hand.y + 0.4, tx, ty, LIGHT);
          g.dot(tx, ty, HI);
          c.pal('fletch');
          g.dot(hand.x + ux * 1.2, hand.y + 0.4 + uy * 1.2 - 0.6, LIGHT);
          g.dot(hand.x + ux * 1.2, hand.y + 0.4 + uy * 1.2 + 0.6, BASE);
        } else {
          g.line(top.x, top.y, bottom.x, bottom.y, BASE);
        }
        if (pose.fx === 'loose') {
          // 箭已经飞出去：弓前方一道细长的箭影
          const ax = pose.sin, ay = pose.cos * 0.35 + 0.02;
          const al = Math.hypot(ax, ay) || 1;
          const ux = ax / al, uy = ay / al;
          const sx = f.x + ux * 8, sy = f.y + uy * 8;
          c.pal('arrow');
          g.line(sx, sy, sx + ux * 12, sy + uy * 12, HI);
          c.pal('string');
          g.line(sx - ux * 3, sy - uy * 3 + 1, sx + ux * 4, sy + uy * 4 + 1, LIGHT);
        }
    }
  }
}
