import type { Palette } from '../pixel/palette';
import type { PixelLayer } from '../pixel/PixelLayer';
import type { Brush } from '../pixel/Brush';
import type { HandAnchor, Hold, Pose, Joint } from './rig';
import type { LayerId } from './layers';

/** 装备槽位 */
export type Slot = 'face' | 'hair' | 'top' | 'bottom' | 'shoes' | 'scarf' | 'bag' | 'weapon_main' | 'weapon_off';
export const SLOTS: Slot[] = ['face', 'hair', 'top', 'bottom', 'shoes', 'scarf', 'bag', 'weapon_main', 'weapon_off'];

/** 手绘的 5 个方向；另外 3 个由水平镜像得到 */
export type Dir5 = 'S' | 'SE' | 'E' | 'NE' | 'N';
export type Dir8 = 'S' | 'SE' | 'E' | 'NE' | 'N' | 'NW' | 'W' | 'SW';

/** 传给每个部件绘制函数的上下文 */
export interface DrawCtx {
  dir: Dir5;
  /** sheet 列号：0-1 待机，2-7 行走 */
  frame: number;
  anim: 'idle' | 'walk';
  /** 这一帧的骨架姿态（关节坐标、手部锚点等） */
  pose: Pose;
  /** 当前部件的临时图层（像素坐标），只写调色板索引 */
  L: PixelLayer;
  /** 画笔：用单位坐标画连续形状（椭球、胶囊、带子、衣褶…），自动算光照 */
  g: Brush;
  /** 选择本装备的某个调色板（已应用换色覆盖） */
  pal(key?: string): void;
  /** 武器槽位专用：所在手的锚点（weapon_main → hand_R，weapon_off → hand_L） */
  hand?: HandAnchor;
}

export type AnchorName = 'head' | 'torso' | 'hip' | 'hand_R' | 'hand_L';

/**
 * 一件装备里的一个可绘制部件。
 * 形状二选一：
 *   - draw：绘制函数（适合随姿态变化的部件）
 *   - frames：像素矩阵（适合刚性小部件），贴到 anchor 关节上
 */
export interface PartDef {
  /**
   * 所在图层。'weapon' 表示按手部锚点和握持方式自动选择 weapon_front / weapon_mid / weapon_back。
   * 也可以是函数，按方向/帧动态决定。
   */
  layer: LayerId | 'weapon' | ((c: DrawCtx) => LayerId);
  draw?: (c: DrawCtx) => void;
  /** 每个方向的像素矩阵（一个字符 = 一格，一格的像素数随精灵倍率取整）：'.' 为空，'0'-'4' 为明暗阶 */
  frames?: Partial<Record<Dir5, string[]>>;
  /** 矩阵贴到哪个关节（或自定义函数），默认 torso */
  anchor?: AnchorName | ((c: DrawCtx) => { x: number; y: number });
  /** 矩阵左上角相对锚点的偏移（单位坐标） */
  offset?: [number, number];
  /** 矩阵使用的调色板键，默认 'main' */
  paletteKey?: string;
  /** 是否自动描边，默认 true */
  outline?: boolean;
  /**
   * 'below'：只画在下面已经合成好的本体像素上（不含描边），用于五官、刺绣这类贴在表面的细节，
   * 保证不会画到轮廓外。这类部件不描边、不投接触阴影。
   */
  mask?: 'below';
}

/** 围巾尾 / 飘带之类的次级运动定义（运行时由弹簧驱动，不烘焙进 sheet） */
export interface TailDef {
  /** 根部挂点（精灵像素坐标），near > 0 表示在身体前面 */
  anchor: (pose: Pose) => Joint;
  paletteKey?: string;
  segments?: number;
  segmentLength?: number;
}

export interface ItemVariant {
  id: string;
  name: string;
  /** 覆盖 palettes 中的同名键 */
  palettes: Record<string, Palette>;
}

/** 一件装备 = 一个数据对象 */
export interface ItemDef {
  id: string;
  name: string;
  slot: Slot;
  parts: PartDef[];
  /** 默认调色板，按键取用（'main'、'trim' …） */
  palettes: Record<string, Palette>;
  /** 可选的换色方案（套装预设里按 id 引用） */
  variants?: ItemVariant[];
  /** 图层顺序覆盖：返回 { 图层: 新的 z 值 }，只影响本装备的部件 */
  layerOverride?: (dir: Dir5, frame: number) => Partial<Record<LayerId, number>>;
  /** 武器的握持方式：'up' 竖举（默认），'down' 剑尖朝下垂握。骨架会据此摆手臂和手部锚点 */
  hold?: Hold;
  /** 装备后隐藏哪些槽位 */
  hides?: Slot[];
  tail?: TailDef;
}

/** 套装预设 */
export interface OutfitDef {
  id: string;
  name: string;
  /** 槽位 → 装备 id；null 表示卸下；未列出的槽位保持不变 */
  slots: Partial<Record<Slot, string | null>>;
  /** 槽位 → 换色方案 id */
  variants?: Partial<Record<Slot, string>>;
}
