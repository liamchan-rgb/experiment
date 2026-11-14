import { pal, ramp, type Palette, OUTLINE, DARK, BASE, LIGHT, HI } from '../pixel/palette';
import { getItem } from '../items/registry';
import { bar, gem, lit, sphere, type IconCtx, type IconDef, type Piece } from './iconKit';
import { WEAPON_ICONS } from './weapons';

/**
 * 桌游物品表（initial-content.json）里全部 18 件物品的图标。
 * 装备的颜色直接取自人物身上的同名装备（调色板同一份），药水、饰品等另配调色板。
 * 武器统一斜放：握柄在左下，尖端朝右上；护甲正面平放；瓶子、饰品居中。
 */

const P = (item: string, key: string): Palette => {
  const it = getItem(item);
  const p = it?.palettes[key];
  if (!p) throw new Error(`icon palette ${item}.${key} missing`);
  return p;
};

// 斜放的方向：从左下指向右上

// ---------------------------------------------------------------- 护甲（正面）

interface ArmorSpec {
  main: Palette; trim: Palette; cloth: Palette; accent?: Palette;
  /** 胸甲的明暗：金属对比大，皮革小 */
  shine: number;
  pauldron: 'none' | 'left' | 'both' | 'spikes';
  detail: (c: IconCtx) => void;
  skirt?: boolean;
}

/** 躯干：圆肩、收腰、下摆略张开，左上受光 */
function torso(c: IconCtx, shine: number, bias = 0): void {
  c.g.fill(4, 6, 28, 29, (u, v) => {
    const y = v - 7; // 0..22
    if (y < 0 || y > 21) return -1;
    let hw = y < 3 ? 6 + y * 1.6 : y < 12 ? 10.6 - (y - 3) * 0.28 : 8.1 + (y - 12) * 0.32;
    if (y < 2.2) hw = 4.5 + y * 2.4; // 领口
    const nx = (u - 16) / hw;
    if (Math.abs(nx) > 1) return -1;
    if (y < 1.2 && Math.abs(nx) < 0.45) return -1; // 领口凹下去
    const lam = lit(nx * 0.9, (y / 21) * 1.2 - 0.5, Math.sqrt(Math.max(0, 1 - nx * nx)));
    return c.g.t(lam * shine, bias);
  });
}

function armor(s: ArmorSpec): Piece[] {
  const pieces: Piece[] = [];
  // 袖子（布）
  pieces.push((c) => {
    c.use(s.cloth);
    for (const side of [-1, 1]) {
      c.g.capsule(16 + side * 9.8, 10, 16 + side * 11.2, 18.5, 2.4, 2, (lam) => c.g.t(lam, side > 0 ? -0.25 : 0.05));
    }
  });
  if (s.skirt) {
    pieces.push((c) => {
      c.use(s.cloth);
      c.g.fill(7, 22, 25, 31, (u, v) => {
        const y = v - 23, hw = 7.5 + y * 0.45;
        if (y < 0 || y > 7 || Math.abs(u - 16) > hw) return -1;
        const fold = Math.sin((u - 16) * 1.1) > 0.4;
        return c.g.t(lit((u - 16) / hw, 0.2, 0.8), fold ? -0.35 : 0);
      });
    });
  }
  // 胸甲
  pieces.push((c) => {
    c.use(s.main);
    torso(c, s.shine);
    c.g.clip = true;
    s.detail(c);
    c.g.clip = false;
  });
  // 腰带 / 下摆滚边
  pieces.push((c) => {
    c.use(s.trim);
    c.g.fill(6, 23.5, 26, 26.5, (u, v) => {
      const hw = 8.1 + (v - 19) * 0.32;
      if (Math.abs(u - 16) > hw || v < 23.6 || v > 26.2) return -1;
      return v < 24.4 ? HI : v > 25.6 ? DARK : c.g.t(lit((u - 16) / hw, 0, 0.8));
    });
    c.g.rect(14.6, 23.3, 2.8, 3.2, (u) => (u < 15.6 ? HI : BASE));
  });
  // 护肩
  if (s.pauldron !== 'none') {
    for (const side of s.pauldron === 'left' ? [-1] : [-1, 1]) {
      pieces.push((c) => {
        c.use(s.main);
        const x = 16 + side * 9.6, y = 9.2;
        c.g.ellipse(x, y, 4.4, 3.4, (lam, nx, ny) => {
          if (ny > 0.55) { c.use(s.trim); return sphere(lam); }
          c.use(s.main);
          return c.g.t(lam * s.shine, side > 0 ? -0.15 : 0.1);
        });
        if (s.pauldron === 'spikes') {
          c.use(s.trim);
          c.g.tri({ x: x - 1.6, y: y - 2.2 }, { x: x + 1.4, y: y - 2.2 }, { x: x + side * 1.8, y: y - 6.4 }, side < 0 ? LIGHT : BASE);
        }
      });
    }
  }
  return pieces;
}

const leatherArmor: IconDef = {
  id: 'leatherArmor', name: '皮甲', rarity: 'common',
  pieces: armor({
    main: P('top_leather_armor', 'main'), trim: P('top_leather_armor', 'strap'), cloth: P('top_leather_armor', 'cloth'),
    shine: 0.9, pauldron: 'left',
    detail: (c) => {
      // 胸口接缝和缝线
      c.g.line(7, 15.5, 25, 15.5, DARK);
      for (let u = 8; u < 25; u += 2) c.g.dot(u, 14.6, LIGHT);
      // 斜挎皮带
      c.use(P('top_leather_armor', 'strap'));
      bar(c, 21, 8, 10, 23, 1.4, (_t, o) => (o < 0 ? LIGHT : BASE));
      c.use(P('top_leather_armor', 'metal'));
      c.g.dot(17.2, 13.4, HI); c.g.dot(17.2, 14.4, BASE);
    },
  }),
};

const runeArmor: IconDef = {
  id: 'runeArmor', name: '符文甲', rarity: 'rare',
  pieces: armor({
    main: P('top_rune_armor', 'main'), trim: P('top_rune_armor', 'trim'), cloth: P('top_rune_armor', 'cloth'),
    shine: 1.35, pauldron: 'both',
    detail: (c) => {
      c.g.line(6, 18.5, 26, 18.5, OUTLINE); // 胸甲分段
      c.use(P('top_rune_armor', 'rune'));
      c.g.line(16, 10, 16, 16, LIGHT);
      c.g.dot(16, 11, HI);
      c.g.dot(13, 13, BASE); c.g.dot(19, 13, BASE);
      c.g.line(14, 21, 18, 21, LIGHT);
    },
  }),
  fx: { glow: '#3ee6d8' },
};

const starlightArmor: IconDef = {
  id: 'starlightArmor', name: '星辉甲', rarity: 'legendary',
  pieces: armor({
    main: P('top_starlight_armor', 'main'), trim: P('top_starlight_armor', 'trim'), cloth: P('top_starlight_armor', 'cloth'),
    shine: 1.4, pauldron: 'both', skirt: true,
    detail: (c) => {
      c.use(P('top_starlight_armor', 'trim'));
      c.g.line(6, 21.5, 26, 21.5, LIGHT);
      // 胸口星纹
      c.use(P('top_starlight_armor', 'gem'));
      c.g.fill(11, 9, 21, 19, (u, v) => {
        const ax = Math.abs(u - 16), ay = Math.abs(v - 14);
        if (ax + ay > 4.6 || Math.min(ax, ay) > 0.9) return -1;
        return ax + ay < 1.6 ? HI : u < 16 || v < 14 ? LIGHT : BASE;
      });
    },
  }),
  fx: { glow: '#7cc4ff', sparkle: '#e0f4ff', particles: 'stars' },
};

const dragonArmor: IconDef = {
  id: 'dragonArmor', name: '龙纹甲', rarity: 'legendary',
  pieces: armor({
    main: P('top_dragon_armor', 'main'), trim: P('top_dragon_armor', 'trim'), cloth: P('top_dragon_armor', 'cloth'),
    shine: 1.3, pauldron: 'spikes',
    detail: (c) => {
      // 龙鳞
      for (let row = 0; row < 7; row++) {
        for (let k = -4; k <= 4; k++) {
          const x = 16 + k * 2.6 + (row % 2) * 1.3, y = 11 + row * 2.2;
          c.g.line(x - 1.1, y, x + 1.1, y, DARK);
        }
      }
      // 金色龙首纹
      c.use(P('top_dragon_armor', 'trim'));
      c.g.tri({ x: 12.5, y: 10 }, { x: 19.5, y: 10 }, { x: 16, y: 16 }, LIGHT);
      c.g.dot(16, 11.5, HI);
      c.g.line(12.5, 10, 11, 8, BASE); c.g.line(19.5, 10, 21, 8, BASE);
    },
  }),
  fx: { glow: '#ff5a30', sparkle: '#ffb060', particles: 'embers' },
};

// ---------------------------------------------------------------- 饰品

const gold = pal('icon-gold', '#3a1e04', '#8a5410', '#d89a26', '#f8d468', '#fffbd0');
const silver = pal('icon-silver', '#1c2232', '#5a6478', '#a4aec0', '#dce4ee', '#ffffff');
const ruby = pal('icon-ruby', '#2a040c', '#7a1020', '#c82a34', '#f06a5a', '#ffd0c0');
const amethyst = pal('icon-amethyst', '#1a0830', '#4a1c86', '#8a44d8', '#c08cf6', '#f2e0ff');
const ribbon = pal('icon-ribbon', '#200810', '#5a1424', '#9a2436', '#d04e52', '#f49a8a');

const powerBadge: IconDef = {
  id: 'powerBadge', name: '力量徽章', rarity: 'common',
  pieces: [
    // 两条缎带
    (c) => {
      c.use(ribbon);
      c.g.tri({ x: 10, y: 18 }, { x: 15, y: 19 }, { x: 9, y: 30 }, BASE);
      c.g.tri({ x: 17, y: 19 }, { x: 22, y: 18 }, { x: 23, y: 30 }, DARK);
    },
    // 金色徽章
    (c) => {
      c.use(gold);
      c.g.ellipse(16, 13, 9, 9, (lam, nx, ny) => {
        const d = Math.hypot(nx, ny);
        if (d > 0.72 && d < 0.84) return DARK; // 内圈刻线
        return sphere(lam * 0.9 + 0.1);
      });
    },
    // 中间红色星
    (c) => {
      c.use(ruby);
      c.g.fill(9, 6, 23, 20, (u, v) => {
        const dx = u - 16, dy = v - 13;
        const a = Math.atan2(dy, dx), r = Math.hypot(dx, dy);
        const star = 3 + 2.4 * Math.max(0, Math.cos(5 * (a + Math.PI / 2)));
        if (r > star) return -1;
        return dx + dy < -1 ? HI : dx + dy < 1.2 ? LIGHT : BASE;
      });
    },
  ],
};

const actionRing: IconDef = {
  id: 'actionRing', name: '行动戒指', rarity: 'rare',
  pieces: [
    // 戒圈：斜着看的一个椭圆环
    (c) => {
      c.use(gold);
      c.g.fill(4, 10, 28, 30, (u, v) => {
        const ex = (u - 16) / 10.5, ey = (v - 20.5) / 7.5;
        const d = Math.hypot(ex, ey);
        if (d > 1 || d < 0.62) return -1;
        const front = ey > 0;
        return front ? sphere(lit(ex, ey, 0.7)) : Math.max(1, sphere(lit(ex, -ey, 0.2)) - 1); // 戒圈后半圈在阴影里
      });
    },
    // 戒托
    (c) => {
      c.use(gold);
      c.g.fill(9, 6, 23, 16, (u, v) => {
        if (v > 15.5 || v < 7 || Math.abs(u - 16) > 6.5 - (15.5 - v) * 0.15) return -1;
        return u < 14 ? HI : u < 18 ? LIGHT : BASE;
      });
    },
    // 紫宝石
    (c) => {
      c.use(amethyst);
      gem(c, 16, 9.5, 5.2);
    },
  ],
  fx: { glow: '#c88cff' },
};

const starlightCharm: IconDef = {
  id: 'starlightCharm', name: '星辉饰品', rarity: 'legendary',
  pieces: [
    // 银链
    (c) => {
      c.use(silver);
      c.g.fill(6, 1, 26, 12, (u, v) => {
        const ex = (u - 16) / 8.5, ey = (v - 2) / 7.5;
        const d = Math.hypot(ex, ey);
        if (ey < 0 || Math.abs(d - 1) > 0.11) return -1;
        return Math.floor(u * 0.8) % 2 ? LIGHT : BASE;
      });
    },
    // 银托
    (c) => {
      c.use(silver);
      c.g.ellipse(16, 11, 2.2, 2, (lam) => sphere(lam));
    },
    // 四角星水晶
    (c) => {
      c.use(P('weapon_starlight_blade', 'blade'));
      c.g.fill(5, 10, 27, 31, (u, v) => {
        const dx = u - 16, dy = v - 20.5;
        const ax = Math.abs(dx), ay = Math.abs(dy) * 0.85;
        const r = ax + ay, arm = Math.min(ax, ay);
        if (r > 9 || arm > 2.6 - r * 0.2) return -1;
        if (r < 2.2) return HI;
        return dx < 0 && dy < 0 ? HI : dx < 0 || dy < 0 ? LIGHT : dx + dy > 4 ? 1 : BASE;
      });
    },
  ],
  fx: { glow: '#7cd0ff', sparkle: '#e8f8ff', particles: 'stars', center: [16, 20] },
};

const dragonCharm: IconDef = {
  id: 'dragonCharm', name: '龙纹饰品', rarity: 'legendary',
  pieces: [
    // 金链
    (c) => {
      c.use(gold);
      c.g.fill(6, 1, 26, 12, (u, v) => {
        const ex = (u - 16) / 8.5, ey = (v - 2) / 7.5;
        const d = Math.hypot(ex, ey);
        if (ey < 0 || Math.abs(d - 1) > 0.11) return -1;
        return Math.floor(u * 0.8) % 2 ? LIGHT : BASE;
      });
    },
    // 金色龙爪托（外圈带三个爪尖）
    (c) => {
      c.use(gold);
      c.g.fill(5, 9, 27, 31, (u, v) => {
        const dx = u - 16, dy = v - 20.5, r = Math.hypot(dx, dy), a = Math.atan2(dy, dx);
        const claw = 8.2 + 1.8 * Math.max(0, Math.cos(3 * a + 0.5)) ** 6;
        if (r > claw || r < 4.6) return -1;
        return sphere(lit(dx / r, dy / r, 0.4));
      });
    },
    // 龙眼宝石：竖瞳
    (c) => {
      c.use(P('weapon_dragon_fang', 'gem'));
      c.g.ellipse(16, 20.5, 4.8, 4.8, (lam, nx) => (Math.abs(nx) < 0.16 ? OUTLINE : sphere(lam)));
      c.g.dot(14.6, 18.6, HI);
    },
  ],
  fx: { glow: '#ff6a28', sparkle: '#ffc070', particles: 'embers', center: [16, 20] },
};

// ---------------------------------------------------------------- 药水、复活石

const cork = pal('icon-cork', '#1e1008', '#4e3018', '#8a5a30', '#c08a50', '#e8bc80');
const glass = pal('icon-glass', '#2a3440', '#6a7c8a', '#b8c8d0', '#e8f2f4', '#ffffff');
const redPotion = ramp('icon-potion-red', '#d42a34');
const bluePotion = ramp('icon-potion-blue', '#2a7ae0');

/** 圆肚瓶：玻璃外壳 + 液面以下的药水 + 高光 */
function flask(cx: number, cy: number, r: number, neck: number, liquid: Palette, level: number, ring = false): Piece[] {
  return [
    (c) => {
      // 瓶身：先画药水（液面以下），液面以上是玻璃
      c.g.fill(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1, (u, v) => {
        const nx = (u - cx) / r, ny = (v - cy) / r;
        const d = nx * nx + ny * ny;
        if (d > 1) return -1;
        const lam = lit(nx, ny, Math.sqrt(1 - d));
        const surface = cy + r * level + Math.sin(nx * 3) * 0.3;
        if (v < surface) { c.use(glass); return lam > 0.75 ? HI : lam > 0.2 ? LIGHT : 2; }
        c.use(liquid);
        if (Math.abs(v - surface) < 0.9) return HI; // 液面一道亮线
        return sphere(lam * 0.85 + 0.05);
      });
      // 瓶身左上的玻璃高光
      c.use(glass);
      c.g.dot(cx - r * 0.5, cy - r * 0.15, HI);
      c.g.dot(cx - r * 0.55, cy + r * 0.15, HI);
      c.g.dot(cx - r * 0.42, cy - r * 0.45, LIGHT);
    },
    // 瓶颈
    (c) => {
      c.use(glass);
      c.g.rect(cx - 2.2, cy - r - neck, 4.4, neck + 1.2, (u) => (u < cx - 0.8 ? HI : u < cx + 0.8 ? LIGHT : BASE));
      if (ring) {
        c.use(gold);
        c.g.rect(cx - 3, cy - r - 1.4, 6, 1.6, (u) => (u < cx - 0.5 ? HI : LIGHT));
      }
    },
    // 软木塞
    (c) => {
      c.use(cork);
      c.g.rect(cx - 2.4, cy - r - neck - 2.8, 4.8, 3, (u, v) => (v < cy - r - neck - 2 ? LIGHT : u < cx ? BASE : DARK));
    },
  ];
}

const smallPotion: IconDef = { id: 'smallPotion', name: '小治疗药水', rarity: 'common', pieces: flask(16, 20, 7.2, 4.5, redPotion, -0.15) };
const largePotion: IconDef = { id: 'largePotion', name: '大治疗药水', rarity: 'common', pieces: flask(16, 19, 9.6, 3.6, redPotion, -0.35, true) };

const shieldPotion: IconDef = {
  id: 'shieldPotion', name: '护盾药水', rarity: 'common',
  pieces: [
    // 盾形瓶身
    (c) => {
      c.g.fill(5, 9, 27, 31, (u, v) => {
        const dx = u - 16, y = v - 10;
        if (y < 0) return -1;
        const hw = y < 9 ? 10 : 10 * Math.sqrt(Math.max(0, 1 - ((y - 9) / 11.5) ** 2));
        if (Math.abs(dx) > hw || y > 20.5) return -1;
        const edge = Math.abs(dx) > hw - 1.4 || y < 1.4;
        if (edge) { c.use(gold); return dx < 0 || y < 1.4 ? HI : BASE; }
        const lam = lit(dx / 10, (y - 10) / 12, 0.7);
        if (y < 4) { c.use(glass); return lam > 0.3 ? LIGHT : 2; }
        c.use(bluePotion);
        if (y < 5) return HI;
        return sphere(lam);
      });
      c.use(glass);
      c.g.dot(11, 16, HI); c.g.dot(11, 18, HI);
    },
    (c) => {
      c.use(glass);
      c.g.rect(13.8, 4.8, 4.4, 5.2, (u) => (u < 15.2 ? HI : u < 16.8 ? LIGHT : BASE));
    },
    (c) => {
      c.use(cork);
      c.g.rect(13.6, 2, 4.8, 3, (u, v) => (v < 2.8 ? LIGHT : u < 16 ? BASE : DARK));
    },
  ],
};

const revivalCrystal = pal('icon-revival', '#0e2a3a', '#2a7a8a', '#6cd0c8', '#c0f6e0', '#ffffff');

const revivalStone: IconDef = {
  id: 'revivalStone', name: '复活石', rarity: 'rare',
  pieces: [
    (c) => {
      c.use(revivalCrystal);
      c.g.fill(4, 2, 28, 31, (u, v) => {
        const dx = u - 16, dy = v - 16.5;
        const ax = Math.abs(dx) / 8.5, ay = Math.abs(dy) / 14;
        if (ax + ay > 1) return -1;
        // 刻面：左上两块亮、右下暗，中间一道竖棱
        if (Math.abs(dx) < 0.6) return dy < 0 ? HI : LIGHT;
        if (dy < 0) return dx < 0 ? (ax + ay > 0.6 ? LIGHT : HI) : BASE;
        return dx < 0 ? LIGHT : ax + ay > 0.55 ? 1 : BASE;
      });
      // 里面的暖光（复活的生命之光）
      c.use(gold);
      c.g.fill(13, 13, 19, 21, (u, v) => (Math.abs(u - 16) + Math.abs(v - 17) * 0.8 < 2.4 ? (Math.abs(u - 16) + Math.abs(v - 17) < 1 ? HI : LIGHT) : -1));
    },
  ],
  fx: { glow: '#9cf0d8' },
};

export const ICONS: IconDef[] = [
  ...WEAPON_ICONS,
  leatherArmor, runeArmor, starlightArmor, dragonArmor,
  powerBadge, actionRing, starlightCharm, dragonCharm,
  smallPotion, largePotion, shieldPotion, revivalStone,
];
