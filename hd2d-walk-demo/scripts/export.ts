/**
 * 导出 sprite sheet，交给 iPad 游戏（SpriteKit）使用。
 *
 *   npm run export            → 默认 SPRITE_SCALE
 *   npm run export -- 1       → 指定精灵倍率
 *
 * 每个角色预设（src/items/characters.ts）输出三样东西到 export/：
 *   native/<name>.png   原生 sheet：5 行（S/SE/E/NE/N）× 8 列（待机 0-1、行走 2-7），每格 SPR_W×SPR_H
 *   native/<name>.json  元数据：帧尺寸、脚底锚点、每帧手部锚点、围巾尾挂点、帧率
 *   ios/<Hero1>Directions.png 兼容游戏现有格式的 1536×1536 图集：4×4，每格 384×384，
 *                             行 = 正面/左/背面/右，列 = 待机/左脚/过渡/右脚，脚底在 y=336
 *
 * 另外写一份 manifest.json，列出每个角色用了哪些装备和换色。
 * 装备从 src/items 和 CharacterParts 自动收集，新增装备不用改这个脚本。
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { PixelLayer } from '../src/pixel/PixelLayer';
import { composeFrame } from '../src/character/paperdoll';
import type { Equipment } from '../src/character/equipment';
import {
  CX, DIRS5, FOOT_Y, FRAMES_PER_DIR, IDLE_FRAMES, SPRITE_SCALE, SPR_H, SPR_W, WALK_FRAMES, makePose, setSpriteScale,
} from '../src/character/rig';
import { Animator } from '../src/character/animator';
import { CHARACTERS, buildEquipment } from '../src/items/characters';
import { Image } from './png';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'export');
if (process.argv[2]) setSpriteScale(Number(process.argv[2]));

/** iOS 图集：行（正面、左、背面、右）→ 原生方向 + 是否镜像 */
const IOS_ROWS = [
  { dir: 'S', flip: false },
  { dir: 'E', flip: true }, // 左 = 右侧镜像
  { dir: 'N', flip: false },
  { dir: 'E', flip: false },
] as const;
/** iOS 图集：列（待机、左脚在前、过渡、右脚在前）→ 原生 sheet 的列号 */
const IOS_COLS = [0, 6, 5, 3];
const IOS_CELL = 384;
const IOS_FOOT_Y = 336;

function frameImage(eq: Equipment, dir: (typeof DIRS5)[number], col: number): Image {
  const L = new PixelLayer(SPR_W, SPR_H);
  composeFrame(eq.resolve(), dir, col, L);
  const img = new Image(SPR_W, SPR_H);
  L.toRGBA(img.data);
  return img;
}

const round = (v: number) => Math.round(v * 100) / 100;

function exportOne(name: string, eq: Equipment): void {
  const S = SPRITE_SCALE;
  const entries = eq.resolve();
  const frames = DIRS5.map((dir) => Array.from({ length: FRAMES_PER_DIR }, (_, c) => frameImage(eq, dir, c)));

  // 原生 sheet
  const sheet = new Image(SPR_W * FRAMES_PER_DIR, SPR_H * DIRS5.length);
  frames.forEach((row, r) => row.forEach((f, c) => sheet.blit(f, c * SPR_W, r * SPR_H)));
  mkdirSync(join(root, 'native'), { recursive: true });
  writeFileSync(join(root, 'native', `${name}.png`), sheet.png());

  // 元数据（坐标都是帧内像素，原点在左上，y 向下）
  const armedR = entries.find((e) => e.slot === 'weapon_main')?.item.hold;
  const tail = eq.get('scarf')?.tail;
  const meta = {
    name,
    spriteScale: S,
    frameSize: { w: SPR_W, h: SPR_H },
    pivot: { x: round(CX * S), y: round(FOOT_Y * S), note: '脚底中点；SpriteKit anchorPoint = (x / w, 1 - y / h)' },
    rows: DIRS5,
    mirror: { NW: 'NE', W: 'E', SW: 'SE', how: '整帧水平翻转（xScale = -1），翻转轴 = 帧宽 / 2' },
    columns: { idle: IDLE_FRAMES, walk: WALK_FRAMES },
    fps: { idle: Animator.IDLE_FPS, walk: Animator.WALK_FPS },
    equipment: entries.filter((e) => e.slot !== 'body').map((e) => ({
      slot: e.slot,
      id: e.item.id,
      palettes: Object.fromEntries(Object.entries(e.palettes).map(([k, p]) => [k, p.id])),
    })),
    frames: DIRS5.map((dir) =>
      Array.from({ length: FRAMES_PER_DIR }, (_, col) => {
        const p = makePose(dir, col, { armedR });
        const hand = (h: typeof p.handR) => ({
          x: round(h.x * S), y: round(h.y * S), angle: round(h.angle), weaponFront: h.weaponFront,
        });
        const t = tail?.anchor(p);
        return {
          dir, col,
          bob: p.bob,
          hand_R: hand(p.handR),
          hand_L: hand(p.handL),
          ...(t ? { scarfTail: { x: round(t.x * S), y: round(t.y * S), front: t.near > 0 } } : {}),
        };
      }),
    ),
    ...(tail ? {
      scarfTail: {
        segments: tail.segments ?? 7,
        segmentLength: round((tail.segmentLength ?? 2.7) * S),
        palette: entries.find((e) => e.slot === 'scarf')!.palettes[tail.paletteKey ?? 'main'].colors,
        note: '运行时弹簧链，算法见 src/character/scarfPhysics.ts',
      },
    } : {}),
  };
  writeFileSync(join(root, 'native', `${name}.json`), JSON.stringify(meta, null, 1));

  // iOS 兼容图集：整数倍最近邻放大，脚底对齐 y=336
  const k = Math.max(1, Math.floor(Math.min((IOS_CELL - 16) / SPR_W, IOS_FOOT_Y / (FOOT_Y * S + 1))));
  const ox = Math.round(IOS_CELL / 2 - CX * S * k);
  const oy = Math.round(IOS_FOOT_Y - (FOOT_Y * S + 1) * k);
  const atlas = new Image(IOS_CELL * 4, IOS_CELL * 4);
  IOS_ROWS.forEach(({ dir, flip }, r) => {
    IOS_COLS.forEach((col, c) => {
      const f = frames[DIRS5.indexOf(dir)][col];
      const x = flip ? IOS_CELL - ox - SPR_W * k : ox;
      atlas.blit(f, c * IOS_CELL + x, r * IOS_CELL + oy, k, flip);
    });
  });
  mkdirSync(join(root, 'ios'), { recursive: true });
  const iosName = name.charAt(0).toUpperCase() + name.slice(1);
  writeFileSync(join(root, 'ios', `${iosName}Directions.png`), atlas.png());
  console.log(`${name}: native ${sheet.w}×${sheet.h}, ios 1536×1536 (×${k})`);
}

const manifest = CHARACTERS.map((p) => {
  const eq = buildEquipment(p);
  exportOne(p.id, eq);
  return {
    id: p.id,
    name: p.name,
    ios: `ios/${p.id.charAt(0).toUpperCase() + p.id.slice(1)}Directions.png`,
    native: `native/${p.id}.png`,
    skin: p.skin ?? 'fair',
    equipment: eq.resolve().filter((e) => e.slot !== 'body').map((e) => ({
      slot: e.slot, id: e.item.id, variant: eq.variantOf(e.slot as never) ?? null,
    })),
  };
});
writeFileSync(join(root, 'manifest.json'), JSON.stringify({ spriteScale: SPRITE_SCALE, characters: manifest }, null, 2));
console.log(`精灵倍率 ${SPRITE_SCALE}，每帧 ${SPR_W}×${SPR_H}，输出到 ${root}`);
