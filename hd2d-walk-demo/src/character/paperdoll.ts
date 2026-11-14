import { PixelLayer } from '../pixel/PixelLayer';
import { shadeCode, OUTLINE, SOFT_OUTLINE, HI, LIGHT } from '../pixel/palette';
import type { Palette } from '../pixel/palette';
import { Z, type LayerId } from './layers';
import { makePose, SPR_W, SPR_H, SPRITE_SCALE, CX, FOOT_Y } from './rig';
import { Brush } from '../pixel/Brush';
import type { Hold } from './rig';
import type { Dir5, DrawCtx, ItemDef, PartDef, Slot } from './types';

/** 合成时的一项：一件装备 + 它最终生效的调色板 */
export interface LoadoutEntry {
  slot: Slot | 'body';
  item: ItemDef;
  palettes: Record<string, Palette>;
}

/** 同一图层内的先后：身体最底，其余按槽位 */
function holdOf(entries: LoadoutEntry[], slot: Slot): Hold | undefined {
  const e = entries.find((x) => x.slot === slot);
  return e ? e.item.hold ?? 'up' : undefined;
}

/**
 * 接触阴影的采样点：[dx, dy, 压暗多少阶]（像素）。
 * 朝右下方投出 1–2 个单位，紧贴处最深，往外渐淡。
 */
let tapsCache: { S: number; taps: [number, number, number][] } | undefined;
function shadowTaps(): [number, number, number][] {
  if (tapsCache?.S === SPRITE_SCALE) return tapsCache.taps;
  // 部件自己的描边占掉紧贴的一圈，所以阴影从第 2 像素起才落到下层上
  const reach = Math.max(2, Math.round(2.8 * SPRITE_SCALE));
  const taps: [number, number, number][] = [];
  for (let dy = 0; dy <= reach; dy++) {
    for (let dx = 0; dx <= reach; dx++) {
      if (!dx && !dy) continue;
      const d = Math.hypot(dx * 0.8, dy); // 主要往下投，略偏右
      if (d > reach) continue;
      taps.push([dx, dy, 0.85 * (1 - (d - 1) / reach)]);
    }
  }
  tapsCache = { S: SPRITE_SCALE, taps };
  return taps;
}

/** 部件之间的内描边用哪一阶（见 PixelLayer.drawOnto）：0.75 = 介于描边色和暗部之间 */
export const INNER_LINE = 0.75;

const SLOT_ORDER: (Slot | 'body')[] = [
  'body', 'face', 'bottom', 'shoes', 'top', 'bag', 'scarf', 'hair', 'weapon_off', 'weapon_main',
];

let tmp = new PixelLayer(SPR_W, SPR_H);
let brush = new Brush(tmp, SPRITE_SCALE);

function anchorPoint(part: PartDef, c: DrawCtx): { x: number; y: number } {
  const a = part.anchor ?? 'torso';
  if (typeof a === 'function') return a(c);
  const p = c.pose;
  switch (a) {
    case 'head': return p.head;
    case 'hip': return { x: (p.legs[0].hip.x + p.legs[1].hip.x) / 2, y: p.legs[0].hip.y };
    case 'hand_R': return p.handR;
    case 'hand_L': return p.handL;
    default: return { x: p.proj(0, 0, 0).x, y: p.neckY };
  }
}

/**
 * 把一组装备合成为某方向某帧的一张像素图。
 * 每个部件先画到临时层 → 自动描边 → 按 z 从后到前叠到 out 上。
 */
export function composeFrame(entries: LoadoutEntry[], dir: Dir5, frame: number, out: PixelLayer): void {
  if (tmp.w !== SPR_W || brush.S !== SPRITE_SCALE) {
    // 倍率变了：换一张临时图层
    tmp = new PixelLayer(SPR_W, SPR_H);
    brush = new Brush(tmp, SPRITE_SCALE);
  }
  const pose = makePose(dir, frame, {
    armedR: holdOf(entries, 'weapon_main'),
    armedL: holdOf(entries, 'weapon_off'),
  });
  const cmds: { z: number; order: number; part: PartDef; ctx: DrawCtx }[] = [];
  // 装备里找不到的调色板键，回落到身体的调色板（比如五官的嘴和眉用 skin，换肤色时一起变）
  const bodyPalettes = entries.find((e) => e.slot === 'body')?.palettes ?? {};

  entries.forEach((entry, ei) => {
    // 弓拿在左手
    const hand =
      entry.slot === 'weapon_main' ? (entry.item.hold === 'bow' ? pose.handL : pose.handR) :
      entry.slot === 'weapon_off' ? pose.handL : undefined;
    const override = entry.item.layerOverride?.(dir, frame);
    const fallback = Object.values(entry.palettes)[0];

    entry.item.parts.forEach((part, pi) => {
      const ctx: DrawCtx = {
        dir, frame, anim: pose.anim, pose, L: tmp, g: brush, hand,
        pal: (key = 'main') => {
          tmp.use(entry.palettes[key] ?? bodyPalettes[key] ?? fallback);
        },
      };
      let layer: LayerId;
      if (part.layer === 'weapon') {
        // 身后 → weapon_back；竖握的长柄武器要从头后面穿过去 → weapon_mid；其余在最前
        layer = hand && !hand.weaponFront ? 'weapon_back' : hand?.weaponMid ? 'weapon_mid' : 'weapon_front';
      }
      else if (typeof part.layer === 'function') layer = part.layer(ctx);
      else layer = part.layer;

      const z = override?.[layer] ?? Z[layer];
      const order = SLOT_ORDER.indexOf(entry.slot) * 1000 + ei * 50 + pi;
      cmds.push({ z, order, part, ctx });
    });
  });

  cmds.sort((a, b) => a.z - b.z || a.order - b.order);

  for (const { part, ctx } of cmds) {
    tmp.clear();
    brush.clip = false;
    brush.grit = 0.16;
    brush.dither = true;
    brush.anchor(CX, pose.neckY); // 默认让噪声纹理跟着上身走
    if (part.frames) {
      const rows = part.frames[dir];
      if (rows) {
        ctx.pal(part.paletteKey);
        const a = anchorPoint(part, ctx);
        brush.cells(rows, a.x + (part.offset?.[0] ?? 0), a.y + (part.offset?.[1] ?? 0));
      }
    }
    part.draw?.(ctx);
    if (part.mask === 'below') {
      tmp.drawOnto(out, 0, 0, undefined, true);
      continue;
    }
    if (part.outline !== false) {
      tmp.bounce();
      tmp.outline();
      out.castShadow(tmp, shadowTaps());
    }
    tmp.drawOnto(out, 0, 0, part.innerLine ?? INNER_LINE);
    if (part.innerLine !== undefined) out.fillInteriorOutlines(part.innerLine, tmp.palettes);
  }
  if (pose.lying) layDown(out, pose.lying.lift);
  if (pose.flash) flashWhite(out);
}

/** 受击闪白：轮廓保留深色描边，其余像素全部提到最亮阶，再往白里推一点（像被打中那一瞬间的曝光） */
function flashWhite(out: PixelLayer): void {
  const OUT = shadeCode(OUTLINE), SOFT = shadeCode(SOFT_OUTLINE), TOP = shadeCode(HI);
  for (let i = 0; i < out.idx.length; i++) {
    const v = out.idx[i];
    if (!v || v === OUT) continue;
    out.idx[i] = v === SOFT ? shadeCode(LIGHT) : TOP;
  }
}

/**
 * 倒地：把画好的人整个顺时针转 90°（头朝前、脸朝下），贴着地面线放，左右对着中轴。
 * 90° 转像素图不会糊；人比画布宽时让头那一侧完整，脚那一侧被裁掉一点。
 */
function layDown(out: PixelLayer, lift: number): void {
  const { w: W, h: H } = out;
  const src = out.idx.slice(), spid = out.pid.slice();
  let x0 = W, y0 = H, x1 = -1, y1 = -1;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    if (!src[y * W + x]) continue;
    if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
  }
  if (x1 < 0) return;
  const bw = y1 - y0 + 1, bh = x1 - x0 + 1;
  let ox = Math.round(CX * SPRITE_SCALE - bw / 2);
  if (ox + bw > W) ox = W - bw;
  const oy = Math.round(FOOT_Y * SPRITE_SCALE - lift * SPRITE_SCALE) - bh;
  out.idx.fill(0);
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
    const v = src[y * W + x];
    if (!v) continue;
    const nx = ox + (y1 - y), ny = oy + (x - x0);
    if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
    out.idx[ny * W + nx] = v;
    out.pid[ny * W + nx] = spid[y * W + x];
  }
}
