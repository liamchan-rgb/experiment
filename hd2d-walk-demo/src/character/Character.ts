import * as THREE from 'three';
import { PixelLayer } from '../pixel/PixelLayer';
import { Brush } from '../pixel/Brush';
import type { Palette } from '../pixel/palette';
import { bakeSheet } from '../pixel/bake';
import { Animator } from './animator';
import { Equipment } from './equipment';
import { ScarfTail } from './scarfPhysics';
import {
  DIR8_MAP, DIRS5, FOOT_Y, SPRITE_SCALE, SPR_H, SPR_W, UNIT_H, UNIT_W, CX, dir8FromVector, makePose,
} from './rig';
import type { Dir8, ItemDef, Slot } from './types';

/** 显示画布在精灵四周留的边（单位）：给飘出去的围巾尾留地方 */
const PAD_X = 26;
const PAD_Y = 6;
/** 世界里 1 个单位坐标有多大：角色约 60 单位高 → 约 1.75 米 */
export const WORLD_PER_UNIT = 1 / 34;

/**
 * 场景里的角色：纸娃娃装备 + 动画状态机 + billboard 精灵 + 脚下阴影 + 围巾尾。
 *
 * 每帧只做一件便宜的事：把缓存好的 sheet 里的一格（必要时水平镜像）和围巾尾
 * 叠到一张小画布上。sprite sheet 只在换装时重新烘焙，并按装备组合缓存。
 */
export class Character {
  readonly object = new THREE.Group();
  readonly equipment: Equipment;
  readonly animator = new Animator();
  dir: Dir8 = 'S';
  /** 移动速度（世界单位/秒） */
  speed = 2.9;
  readonly velocity = new THREE.Vector3();

  private sheetCanvas!: HTMLCanvasElement;
  private dirty = true;
  private listeners: (() => void)[] = [];

  private display = document.createElement('canvas');
  private dctx: CanvasRenderingContext2D;
  private big = document.createElement('canvas');
  private bctx: CanvasRenderingContext2D;
  private tailCanvas = document.createElement('canvas');
  private tctx: CanvasRenderingContext2D;
  private tailLayer!: PixelLayer;
  private tailBrush!: Brush;
  private tailImage!: ImageData;
  private tail = new ScarfTail();
  private texture: THREE.CanvasTexture;
  private sprite: THREE.Mesh;
  private scale = 0;
  /** 上次烘焙花了多少毫秒 / 是否命中缓存（给 UI 显示） */
  lastBake = { ms: 0, cached: false };

  constructor(bodyDef: ItemDef, private camera: THREE.PerspectiveCamera) {
    this.equipment = new Equipment(bodyDef);
    this.dctx = this.display.getContext('2d')!;
    this.bctx = this.big.getContext('2d')!;
    this.tctx = this.tailCanvas.getContext('2d')!;

    this.texture = new THREE.CanvasTexture(this.big);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.magFilter = THREE.LinearFilter;
    this.texture.minFilter = THREE.LinearMipmapLinearFilter;
    this.texture.anisotropy = 4;

    // 竖直的 billboard：底边中点踩在地面上
    const w = (UNIT_W + PAD_X * 2) * WORLD_PER_UNIT;
    const h = (UNIT_H + PAD_Y * 2) * WORLD_PER_UNIT;
    const geo = new THREE.PlaneGeometry(w, h);
    // 把脚底那一行对到 y = 0
    geo.translate(0, h / 2 - (UNIT_H + PAD_Y - FOOT_Y - 0.6) * WORLD_PER_UNIT, 0);
    this.sprite = new THREE.Mesh(
      geo,
      new THREE.MeshBasicMaterial({ map: this.texture, alphaTest: 0.5, side: THREE.DoubleSide, fog: false }),
    );
    this.object.add(this.sprite);
    this.object.add(makeBlobShadow());
    this.resize();
  }

  // ---------- 装备 API ----------

  equip(slot: Slot, item: ItemDef): void {
    this.equipment.equip(slot, item);
    this.invalidate();
  }

  unequip(slot: Slot): void {
    this.equipment.unequip(slot);
    this.invalidate();
  }

  setPalette(slot: Slot, palette: Palette, key = 'main'): void {
    this.equipment.setPalette(slot, palette, key);
    this.invalidate();
  }

  setVariant(slot: Slot, variantId: string): void {
    this.equipment.setVariant(slot, variantId);
    this.invalidate();
  }

  /** 精灵倍率变了之后调用 */
  invalidate(): void {
    this.dirty = true;
  }

  onRebake(cb: () => void): void {
    this.listeners.push(cb);
  }

  /** 当前的 sprite sheet（需要时才烘焙） */
  get sheet(): HTMLCanvasElement {
    if (this.dirty) this.rebake();
    return this.sheetCanvas;
  }

  /** 当前帧在 sheet 里的列号 */
  get frame(): number {
    return this.animator.frame;
  }

  private rebake(): void {
    if (this.scale !== SPRITE_SCALE) this.resize();
    const t0 = performance.now();
    const res = bakeSheet(this.equipment.resolve());
    this.sheetCanvas = res.canvas;
    this.lastBake = { ms: performance.now() - t0, cached: res.cached };
    this.dirty = false;
    const tailDef = this.equipment.get('scarf')?.tail;
    if (tailDef) this.tail.configure(tailDef.segments ?? 7, tailDef.segmentLength ?? 2.7);
    this.listeners.forEach((f) => f());
  }

  private resize(): void {
    const S = (this.scale = SPRITE_SCALE);
    const w = Math.round((UNIT_W + PAD_X * 2) * S), h = Math.round((UNIT_H + PAD_Y * 2) * S);
    this.display.width = this.tailCanvas.width = w;
    this.display.height = this.tailCanvas.height = h;
    // 先用最近邻整数倍放大，再交给 GPU 做线性采样：像素块边缘锐利，又不会因为非整数缩放而抖动
    const k = Math.max(2, Math.round(6 / S));
    this.big.width = w * k;
    this.big.height = h * k;
    this.tailLayer = new PixelLayer(w, h);
    this.tailBrush = new Brush(this.tailLayer, S);
    this.tailImage = this.tctx.createImageData(w, h);
    this.texture.dispose();
  }

  // ---------- 每帧 ----------

  /**
   * @param mx,mz 输入方向（已归一化；x 向右，z 朝镜头）
   */
  update(dt: number, mx: number, mz: number, time: number): void {
    const moving = mx !== 0 || mz !== 0;
    if (moving) this.dir = dir8FromVector(mx, mz);
    this.velocity.set(mx * this.speed, 0, mz * this.speed);
    this.object.position.addScaledVector(this.velocity, dt);
    this.animator.update(dt, moving);

    // billboard：保持竖直，只补偿相机俯角带来的压扁
    const pitch = Math.atan2(
      this.camera.position.y - this.object.position.y,
      Math.hypot(this.camera.position.z - this.object.position.z, this.camera.position.x - this.object.position.x),
    );
    this.sprite.scale.y = 1 / Math.cos(pitch);

    this.redraw(dt, time);
  }

  private redraw(dt: number, time: number): void {
    const sheet = this.sheet;
    const S = SPRITE_SCALE;
    const { dir, flip } = DIR8_MAP[this.dir];
    const frame = this.animator.frame;
    const ox = Math.round(PAD_X * S), oy = Math.round(PAD_Y * S);
    const g = this.dctx;
    g.clearRect(0, 0, this.display.width, this.display.height);

    // 围巾尾
    const scarf = this.equipment.get('scarf');
    const tailDef = scarf?.tail;
    let tailFront = false, hasTail = false;
    if (scarf && tailDef) {
      const a = tailDef.anchor(makePose(dir, frame));
      const ax = flip ? 2 * CX - a.x : a.x;
      const upu = 1 / WORLD_PER_UNIT;
      // 世界速度 → 屏幕速度：z 朝镜头的移动在屏幕上是往下
      this.tail.step(dt, ax, a.y, this.velocity.x * upu, this.velocity.z * upu * 0.6, flip ? 1 : -1, time);
      const palette = this.equipment.resolve().find((e) => e.slot === 'scarf')!.palettes[tailDef.paletteKey ?? 'main'];
      this.tail.draw(this.tailLayer, this.tailBrush, palette, PAD_X, PAD_Y);
      this.tailLayer.toRGBA(this.tailImage.data);
      this.tctx.putImageData(this.tailImage, 0, 0);
      tailFront = a.near > 0;
      hasTail = true;
    }

    if (hasTail && !tailFront) g.drawImage(this.tailCanvas, 0, 0);
    const sx = frame * SPR_W, sy = DIRS5.indexOf(dir) * SPR_H;
    if (flip) {
      // 绕精灵中轴镜像：镜像方向不会错位
      g.save();
      g.translate(ox + 2 * CX * S, oy);
      g.scale(-1, 1);
      g.drawImage(sheet, sx, sy, SPR_W, SPR_H, 0, 0, SPR_W, SPR_H);
      g.restore();
    } else {
      g.drawImage(sheet, sx, sy, SPR_W, SPR_H, ox, oy, SPR_W, SPR_H);
    }
    if (hasTail && tailFront) g.drawImage(this.tailCanvas, 0, 0);

    const b = this.bctx;
    b.imageSmoothingEnabled = false;
    b.clearRect(0, 0, this.big.width, this.big.height);
    b.drawImage(this.display, 0, 0, this.big.width, this.big.height);
    this.texture.needsUpdate = true;
  }

  /** 角色身体中心的世界坐标（给相机和景深对焦用） */
  focusPoint(out: THREE.Vector3): THREE.Vector3 {
    return out.copy(this.object.position).setY(0.85);
  }
}

/** 脚下的椭圆 blob 阴影 */
function makeBlobShadow(): THREE.Mesh {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(32, 32, 2, 32, 32, 31);
  grad.addColorStop(0, 'rgba(10,20,10,0.62)');
  grad.addColorStop(0.55, 'rgba(10,20,10,0.38)');
  grad.addColorStop(1, 'rgba(10,20,10,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(1.25, 0.72),
    new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false }),
  );
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = 0.02;
  mesh.renderOrder = 1;
  return mesh;
}
