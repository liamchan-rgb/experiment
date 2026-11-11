import { pal, ramp, LIGHT, DARK, OUTLINE } from '../../pixel/palette';
import { LX, LZ, DARKEN } from '../../pixel/Brush';
import type { DrawCtx, ItemDef } from '../../character/types';

/**
 * 斜挎皮包：背带从左肩斜到右胯。
 * 包体和背带用绘制函数；金属搭扣用「像素矩阵 + 锚点」的写法（演示 PartDef.frames）。
 */
const leather = pal('satchel-leather', '#1e1008', '#583216', '#8e5828', '#bc8442', '#eabc64');
const brass = pal('satchel-brass', '#3e2408', '#8a5c16', '#d8a430', '#f6d86c', '#fff6c0');

/** 包体挂在右胯略靠前的位置 */
const pouchAt = (c: DrawCtx) => c.pose.proj(-4, c.pose.neckUp - 12.6, 2.4, 0.1);
/** 背对镜头时包在身体另一侧：放到最后面，只从身侧露出一点 */
const pouchLayer = (c: DrawCtx) => (c.dir === 'N' ? ('cape' as const) : ('bag' as const));

// 搭扣：一个字符 = 一格。1 暗 2 主色 3 亮 4 高光
const BUCKLE = ['43', '31'];

export const satchel: ItemDef = {
  id: 'bag_satchel',
  name: '棕色皮挎包',
  slot: 'bag',
  palettes: { main: leather, metal: brass },
  variants: [
    { id: 'leather', name: '棕皮', palettes: { main: leather } },
    { id: 'olive', name: '橄榄帆布', palettes: { main: ramp('satchel-olive', '#70703a') } },
  ],
  parts: [
    {
      // 背带
      layer: 'bag',
      draw: (c) => {
        const { g, pose } = c;
        const a = pose.proj(5.4, pose.neckUp + 0.4, 0, 0);
        const b = pouchAt(c);
        c.pal('main');
        g.capsule(a.x, a.y, b.x, b.y - 3, 0.8, 0.8, (_lam, o) => (o < -0.2 ? LIGHT : o > 0.45 ? OUTLINE : DARK));
      },
    },
    {
      layer: pouchLayer,
      draw: (c) => {
        const { g } = c;
        const p = pouchAt(c);
        const hw = 3.9 - Math.abs(c.pose.sin) * 0.9, hh = 3.7;
        c.pal('main');
        g.anchor(p.x, p.y);
        g.grit = 0.24;
        // 包身：圆角的方盒，上半是翻盖
        g.fill(p.x - hw, p.y - hh, p.x + hw, p.y + hh, (u, v) => {
          const nx = (u - p.x) / hw, ny = (v - p.y) / hh;
          if (nx ** 4 + ny ** 4 > 1) return -1;
          const lam = nx * LX + Math.sqrt(1 - nx * nx) * LZ;
          const flap = -0.05 + 0.3 * Math.cos(nx * 1.4); // 翻盖下缘是弧形
          if (ny < flap) return ny > flap - 0.2 ? DARK : g.t(lam, 0.3);
          return g.t(lam, -0.3);
        });
        g.clip = true;
        g.line(p.x - hw + 0.8, p.y + hh - 0.7, p.x + hw - 0.8, p.y + hh - 0.7, DARKEN); // 包底
        g.clip = false;
      },
    },
    {
      // 金属搭扣（像素矩阵）
      layer: pouchLayer,
      anchor: pouchAt,
      offset: [-1, 0],
      paletteKey: 'metal',
      outline: false,
      frames: { S: BUCKLE, SE: BUCKLE, E: BUCKLE, NE: BUCKLE },
    },
  ],
};
