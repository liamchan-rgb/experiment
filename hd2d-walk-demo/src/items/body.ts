import { pal, BASE, DARK, LIGHT, OUTLINE } from '../pixel/palette';
import { LX, LY, LZ } from '../pixel/Brush';
import { HEAD_RX, HEAD_RY } from '../character/rig';
import type { DrawCtx, ItemDef, PartDef } from '../character/types';
import { armLayer, armOf, drawArm, farBias, torsoShape } from './shared';

/**
 * 身体底模（皮肤 + 脸）。不属于任何装备槽位，永远在最底下。
 */
const skin = pal('skin', '#4a2620', '#a86450', '#dc9e7c', '#f4caa2', '#fff0d6');

/** 可选肤色：Equipment.setBodyPalette(SKIN_TONES.tan) */
export const SKIN_TONES = {
  fair: skin,
  light: pal('skin-light', '#54302a', '#bc7c66', '#eab896', '#fadcbe', '#fff4e4'),
  tan: pal('skin-tan', '#3a1e14', '#8a4e34', '#c07a52', '#e0a476', '#f6d0a8'),
  deep: pal('skin-deep', '#24120c', '#5a3020', '#8a5236', '#b47a54', '#dcaa82'),
};

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

  // 五官（眼、眉、嘴、腮红）在 face 槽位，见 items/kits/faceKit.ts。
  // 这里只画属于头型本身的东西：侧面鼻子的阴影和耳朵。只画在脸已有的像素上（clip）。
  g.clip = true;
  if (dir === 'E') {
    c.pal('skin');
    // 鼻子不往轮廓外加凸块，只在脸的前缘打一点阴影
    g.dot(hx + HEAD_RX - 1.4, hy + 4.4, DARK);
    g.ellipse(hx - 0.8, hy + 2.6, 1.6, 2.2, (lam) => (lam > 0.3 ? BASE : DARK)); // 耳朵
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
  palettes: { skin },
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
          g.capsule(leg.hip.x, leg.hip.y, leg.knee.x, leg.knee.y, 2, 1.7, (lam) => g.t(lam, fb));
          g.capsule(leg.knee.x, leg.knee.y, leg.foot.x, leg.foot.y - 1.5, 1.7, 1.5, (lam) => g.t(lam, fb));
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
