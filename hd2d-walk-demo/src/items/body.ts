import { pal, BASE, DARK, LIGHT, OUTLINE } from '../pixel/palette';
import { LX, LY, LZ } from '../pixel/Brush';
import { HEAD_RX, HEAD_RY } from '../character/rig';
import type { DrawCtx, ItemDef, PartDef } from '../character/types';
import { armLayer, armOf, drawArm, farBias, torsoShape } from './shared';

/**
 * 身体底模（皮肤 + 脸）。不属于任何装备槽位，永远在最底下。
 */
const skin = pal('skin', '#4a2620', '#a86450', '#dc9e7c', '#f4caa2', '#fff0d6');
/** 0 眼线  1 瞳孔  2 虹膜  3 虹膜亮部  4 眼白 / 高光 */
const eye = pal('eye', '#17101e', '#1e3a5c', '#3e9aa8', '#8ad8d8', '#ffffff');
const blushPal = pal('blush', '#a85048', '#cc7466', '#e08a78', '#f0a894', '#fcd0c8');

function arm(side: 'R' | 'L'): PartDef {
  return {
    layer: armLayer(side),
    draw: (c) => {
      const { g } = c;
      const a = armOf(c, side);
      const fb = farBias(c, a.hand);
      g.grit = 0.08;
      c.pal('skin');
      drawArm(c, side, [1.6, 1.45, 1.3]);
      g.ellipse(a.hand.x, a.hand.y + 0.7, 1.7, 1.8, (lam) => g.t(lam, fb - 0.05)); // 手
    },
  };
}

// 眼睛：一格一格摆（一格 = 一个像素）。0 眼线 1 瞳孔 2 虹膜 3 虹膜亮部 4 高光
const EYE_L = ['000', '041', '012', '.23'];
const EYE_R = ['000', '140', '210', '32.'];
const EYE_SIDE = ['00', '41', '12', '23'];
const EYE_FAR = ['00', '01', '12', '.2'];

function head(c: DrawCtx): void {
  const { g, pose, dir } = c;
  const hx = pose.head.x + pose.sin * 0.9, hy = pose.head.y;
  g.grit = 0.07;
  g.anchor(hx, hy);

  c.pal('skin');
  // 脖子：整个在下巴的阴影里
  const nx0 = pose.head.x - pose.sin * 0.6;
  g.rect(nx0 - 1.9, hy + 7, 3.8, 5.2, (_u, v) => (v < hy + 10.4 ? OUTLINE : DARK));

  // 头：椭球，下半张脸收窄成下巴；额头落在刘海的阴影里
  g.fill(hx - HEAD_RX - 1, hy - HEAD_RY - 1, hx + HEAD_RX + 1, hy + HEAD_RY + 1, (u, v) => {
    const dx = u - hx, dy = v - hy;
    // 圆脸：下巴几乎不收窄，下半张脸短一点；下半部接近正圆，下巴两角是圆弧而不是方角
    const lower = dy > 0;
    const rx = lower ? HEAD_RX * (1.05 - 0.05 * (dy / HEAD_RY) * (dy / HEAD_RY)) : HEAD_RX; // 脸颊处略鼓
    const ry = lower ? HEAD_RY * 0.84 : HEAD_RY; // 下巴的弧线收在围巾上方，才看得出是圆的
    const nx = dx / rx, ny = dy / ry;
    const shape = lower ? Math.abs(nx) ** 2 + Math.abs(ny) ** 2.3 : nx * nx + ny * ny;
    if (shape > 1) return -1;
    const d = Math.min(1, nx * nx + ny * ny);
    const lam = nx * LX + ny * LY + Math.sqrt(1 - d) * LZ;
    if (dy < -3.4) return DARK; // 刘海的阴影
    // 脸上的过渡要柔：压缩光照范围，只落在 暗部..亮部 之间
    return Math.max(DARK, Math.min(LIGHT, g.t(lam * 0.62, 0.2)));
  });

  // 五官按像素格摆，保证大小固定、左右对称。
  // 只画在脸已有的像素上（clip）：落到轮廓外的像素会被自动描边包一圈，变成脸上鼓出的小包。
  g.clip = true;
  const S = g.S, k = Math.max(1, Math.round(S));
  const px = Math.round(hx * S), py = Math.round((hy + 0.4) * S);
  const dot = (i: number, j: number, sh: number) => g.cellsPx([String(sh)], px + i * k, py + j * k);
  if (dir === 'S') {
    c.pal('eye');
    g.cellsPx(EYE_L, px - 5 * k, py);
    g.cellsPx(EYE_R, px + 3 * k, py);
    c.pal('blush');
    dot(-6, 4, 2); dot(-5, 4, 2);
    dot(5, 4, 2); dot(6, 4, 2);
    c.pal('skin');
    dot(0, 5, 1); // 嘴（正面的对称轴在 px + 0.5，单像素的嘴正好居中）
    dot(-5, -2, 1); dot(-4, -2, 1); dot(-3, -1, 1); // 眉
    dot(5, -2, 1); dot(4, -2, 1); dot(3, -1, 1);
  } else if (dir === 'SE') {
    c.pal('eye');
    g.cellsPx(EYE_L, px - 2 * k, py);
    g.cellsPx(EYE_FAR, px + 5 * k, py);
    c.pal('blush');
    dot(-3, 4, 2); dot(-2, 4, 2);
    c.pal('skin');
    dot(3, 5, 1); dot(4, 5, 1);
    dot(-2, -2, 1); dot(-1, -2, 1); dot(0, -1, 1);
  } else if (dir === 'E') {
    c.pal('skin');
    // 鼻子不往轮廓外加凸块，只在脸的前缘打一点阴影
    g.dot(hx + HEAD_RX - 1.4, hy + 4.4, DARK);
    c.pal('eye');
    g.cellsPx(EYE_SIDE, px + 4 * k, py);
    c.pal('blush');
    dot(2, 4, 2); dot(3, 4, 2);
    c.pal('skin');
    dot(6, 5, 1);
    dot(4, -2, 1); dot(5, -2, 1);
    // 耳朵
    g.ellipse(hx - 0.8, hy + 2.6, 1.6, 2.2, (lam) => (lam > 0.3 ? BASE : DARK));
    g.dot(hx - 0.8, hy + 2.6, DARK);
  } else if (dir === 'NE') {
    g.ellipse(hx + 6.8, hy + 2.6, 1.3, 2.1, (lam) => (lam > 0.3 ? BASE : DARK)); // 只露出耳朵和一点脸颊
  }
  g.clip = false;
}

export const body: ItemDef = {
  id: 'body',
  name: '身体',
  slot: 'top', // 占位：身体不走槽位，由 Equipment 固定放在最底层
  palettes: { skin, eye, blush: blushPal },
  parts: [
    arm('L'),
    arm('R'),
    {
      layer: 'legs',
      draw: (c) => {
        const { g } = c;
        g.grit = 0.08;
        c.pal('skin');
        for (const leg of c.pose.legs) {
          const fb = farBias(c, leg.foot);
          g.capsule(leg.hip.x, leg.hip.y, leg.foot.x, leg.foot.y - 1.5, 2.2, 1.8, (lam) => g.t(lam, fb));
        }
      },
    },
    {
      layer: 'torso',
      draw: (c) => {
        c.g.grit = 0.08;
        c.pal('skin');
        torsoShape(c, 12.5, { flare: 0, pad: -0.3 }, (lam) => c.g.t(lam));
      },
    },
    { layer: 'head', draw: head },
  ],
};
