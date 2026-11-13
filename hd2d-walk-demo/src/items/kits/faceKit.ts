import { pal, DARK, BASE, type Palette } from '../../pixel/palette';
import type { Dir5, DrawCtx, ItemDef, ItemVariant } from '../../character/types';

/**
 * 五官引擎：把一份五官数据（JSON）变成「face」槽位的装备。
 *
 * 五官全部按像素格摆，不用椭圆：原点是头中心的像素
 *   px = round(hx·S), py = round((hy + 0.4)·S)，其中 hx = head.x + sin·0.9，hy = head.y；
 * 坐标单位是「格」（一格 = max(1, round(S)) 个像素）。正面的左右对称轴在 px + 0.5。
 *
 * 画在 head 图层、头之后；只落在已经画好的脸上（mask: 'below'），不描边，
 * 所以五官永远不会在轮廓外鼓出小包。
 *
 * 颜色：眼睛图案里的数字是 eye 调色板的明暗阶；腮红用 blush 调色板第 2 阶；
 * 嘴和眉用身体的 skin 调色板第 1 阶（换肤色时一起变）。
 *
 * 数据格式见 Sources/Resources/CharacterParts/face/*.json 和 docs/CHARACTER_SPRITES.md 第 6.2 节。
 */

/** [图案名, x, y]；图案名加 ! 表示水平镜像 */
export type EyePlacement = [string, number, number];
export type Cell = [number, number];

export interface FaceView {
  eyes?: EyePlacement[];
  blush?: Cell[];
  mouth?: Cell[];
  brows?: Cell[];
}

export interface FaceData {
  id: string;
  name: string;
  palettes: { eye: string[]; blush: string[] };
  variants?: { id: string; name: string; palettes: { eye?: string[]; blush?: string[] } }[];
  patterns: Record<string, string[]>;
  /** 有五官的方向：通常是 S / SE / E（NE、N 看不到脸） */
  views: Partial<Record<Dir5, FaceView>>;
}

export function mirrorPattern(rows: string[]): string[] {
  return rows.map((r) => [...r].reverse().join(''));
}

/** 五官原点（像素）与一格的像素数 */
export function faceOrigin(c: DrawCtx): { px: number; py: number; k: number } {
  const S = c.g.S;
  const hx = c.pose.head.x + c.pose.sin * 0.9, hy = c.pose.head.y;
  return { px: Math.round(hx * S), py: Math.round((hy + 0.4) * S), k: Math.max(1, Math.round(S)) };
}

function drawFace(c: DrawCtx, d: FaceData): void {
  const view = d.views[c.dir];
  if (!view) return;
  const { g } = c;
  const { px, py, k } = faceOrigin(c);
  const dot = (cell: Cell, shade: number) => g.cellsPx([String(shade)], px + cell[0] * k, py + cell[1] * k);

  c.pal('eye');
  for (const [name, x, y] of view.eyes ?? []) {
    const mirrored = name.endsWith('!');
    const rows = d.patterns[mirrored ? name.slice(0, -1) : name];
    if (!rows) throw new Error(`${d.id}: unknown eye pattern ${name}`);
    g.cellsPx(mirrored ? mirrorPattern(rows) : rows, px + x * k, py + y * k);
  }
  c.pal('blush');
  for (const cell of view.blush ?? []) dot(cell, BASE);
  c.pal('skin');
  for (const cell of view.mouth ?? []) dot(cell, DARK);
  for (const cell of view.brows ?? []) dot(cell, DARK);
}

export function makeFace(d: FaceData): ItemDef {
  const palettes: Record<string, Palette> = {
    eye: pal(`${d.id}-eye`, ...d.palettes.eye),
    blush: pal(`${d.id}-blush`, ...d.palettes.blush),
  };
  const variants: ItemVariant[] = (d.variants ?? []).map((v) => {
    const p: Record<string, Palette> = {};
    if (v.palettes.eye) p.eye = pal(`${d.id}-${v.id}-eye`, ...v.palettes.eye);
    if (v.palettes.blush) p.blush = pal(`${d.id}-${v.id}-blush`, ...v.palettes.blush);
    return { id: v.id, name: v.name, palettes: p };
  });
  return {
    id: d.id,
    name: d.name,
    slot: 'face',
    palettes,
    variants,
    parts: [{ layer: 'head', mask: 'below', outline: false, draw: (c) => drawFace(c, d) }],
  };
}
