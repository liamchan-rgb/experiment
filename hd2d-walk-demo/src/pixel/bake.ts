import { PixelLayer } from './PixelLayer';
import { composeFrame, type LoadoutEntry } from '../character/paperdoll';
import { DIRS5, FRAMES_PER_DIR, SPR_W, SPR_H, SPRITE_SCALE } from '../character/rig';

/**
 * Sprite sheet 烘焙。
 * 布局：5 行（S / SE / E / NE / N）× 8 列（待机 0-1，行走 2-7），每格 SPR_W × SPR_H 像素。
 * 以「装备 id + 调色板 id」为键做 LRU 缓存 —— 换回旧搭配不会重画。
 */

const CACHE_LIMIT = 32;
const cache = new Map<string, HTMLCanvasElement>();

export function loadoutKey(entries: LoadoutEntry[]): string {
  return `x${SPRITE_SCALE}|` + entries
    .map((e) => `${e.slot}=${e.item.id}[${Object.entries(e.palettes).map(([k, p]) => `${k}:${p.id}`).join(',')}]`)
    .join('|');
}

export interface BakeResult {
  canvas: HTMLCanvasElement;
  key: string;
  cached: boolean;
}

export function bakeSheet(entries: LoadoutEntry[]): BakeResult {
  const key = loadoutKey(entries);
  const hit = cache.get(key);
  if (hit) {
    cache.delete(key); // 刷新 LRU 顺序
    cache.set(key, hit);
    return { canvas: hit, key, cached: true };
  }

  const canvas = document.createElement('canvas');
  canvas.width = SPR_W * FRAMES_PER_DIR;
  canvas.height = SPR_H * DIRS5.length;
  const g = canvas.getContext('2d')!;
  const frame = new PixelLayer(SPR_W, SPR_H);
  const img = g.createImageData(SPR_W, SPR_H);

  DIRS5.forEach((dir, row) => {
    for (let col = 0; col < FRAMES_PER_DIR; col++) {
      frame.clear();
      composeFrame(entries, dir, col, frame);
      frame.toRGBA(img.data);
      g.putImageData(img, col * SPR_W, row * SPR_H);
    }
  });

  cache.set(key, canvas);
  if (cache.size > CACHE_LIMIT) cache.delete(cache.keys().next().value!);
  return { canvas, key, cached: false };
}
