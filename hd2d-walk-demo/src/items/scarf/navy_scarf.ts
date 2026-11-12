import { pal, ramp, HI, LIGHT } from '../../pixel/palette';
import { LX, LY, LZ } from '../../pixel/Brush';
import { CX } from '../../character/rig';
import type { ItemDef } from '../../character/types';

/**
 * 深蓝围巾：又厚又大的一圈，把下巴都埋进去一点；颈部一圈烘焙进 sheet，
 * 飘在身后的尾巴由 tail 定义，运行时用弹簧驱动（见 character/scarfPhysics.ts）。
 */
const navy = pal('scarf-navy', '#05081a', '#111c44', '#22346e', '#3c549c', '#7c94d4');

export const navyScarf: ItemDef = {
  id: 'scarf_navy',
  name: '深蓝围巾',
  slot: 'scarf',
  palettes: { main: navy },
  variants: [
    { id: 'navy', name: '深蓝', palettes: { main: navy } },
    { id: 'crimson', name: '绯红', palettes: { main: ramp('scarf-crimson', '#a82838') } },
    { id: 'cream', name: '米白', palettes: { main: ramp('scarf-cream', '#d8ccac') } },
    { id: 'moss', name: '苔绿', palettes: { main: ramp('scarf-moss', '#527e38') } },
  ],
  tail: {
    // 从后颈偏左的位置垂出
    anchor: (pose) => pose.proj(2.4, pose.neckUp - 0.5, -5.2),
    paletteKey: 'main',
    segments: 7,
    segmentLength: 2.7,
  },
  parts: [
    {
      layer: 'scarf',
      draw: (c) => {
        const { g, pose } = c;
        // 侧面看围巾只比脖子粗一圈，不能按正面宽度画，否则会前后各凸出一截
        const hw = pose.torsoHalf + 2.2 - 1.5 * Math.abs(pose.sin);
        const sx = CX + pose.sin * 0.5;
        const yc = pose.neckY + 1.5, hh = 2.8;
        c.pal('main');
        g.grit = 0.26;
        // 颈部一圈：一条厚实的圆筒，上亮下暗，带斜向的褶
        g.fill(sx - hw, yc - hh, sx + hw, yc + hh, (u, v) => {
          const nx = (u - sx) / hw, ny = (v - yc) / hh;
          if (Math.abs(nx) ** 2.6 + Math.abs(ny) ** 3 > 1) return -1; // 圆头，不是方筒
          const lam = ny * LY * 1.2 + nx * LX * 0.6 + Math.sqrt(Math.max(0, 1 - ny * ny)) * LZ * 0.9;
          return g.t(lam + Math.sin((u + v * 0.6) * 1.7) * 0.32, -0.02);
        });
        g.fold(sx - hw + 1, yc - 1.2, sx + hw - 1.6, yc + 1, false); // 两圈之间的叠缝

        if (pose.cos > 0.3) {
          // 正面能看到围巾结和垂下的一小段，末端两道浅色条纹
          const kx = CX + (hw - 3.8) * (0.3 + pose.sin * 0.6);
          g.capsule(kx + 0.2, yc + 2.8, kx + 0.8, yc + 9.4, 1.5, 1.8, (lam, _o, t) =>
            (t > 0.68 && t < 0.78) || (t > 0.88 && t < 0.97) ? (lam > 0.2 ? HI : LIGHT) : g.t(lam));
          g.ellipse(kx, yc + 2.2, 2.1, 2, (lam) => g.t(lam, 0.08));
        } else if (pose.cos < -0.3) {
          // 背面：后颈处尾巴的根部
          const a = pose.proj(2.4, pose.neckUp - 0.5, -5.2);
          g.ellipse(a.x, a.y + 0.6, 2.1, 1.9, (lam) => g.t(lam, 0.08));
        }
      },
    },
  ],
};
