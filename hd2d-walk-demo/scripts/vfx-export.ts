/**
 * 技能特效导出给游戏：把预览（scripts/vfx-preview.ts）里用到的 pixelfx 特效逐个预渲染成帧图，外加一份「配方」：
 * 游戏里每个特效 id（MeadowSkillProcedural 的 skillIDs）放哪些片段、什么时候放、贴在谁身上。
 *
 *   npx vite-node scripts/vfx-export.ts <输出目录>
 * 输出：clips/<片段 id>.rgba（全部帧：先 back 层再 front 层）、recipes.json；tools/vfx_export.py 再打包进游戏素材目录。
 *
 * 约定（「正向」= 特效往右打：施法者在左、目标在右；游戏里方向是 -1 时整段水平镜像）：
 *   at      相对游戏特效开始的秒数（可以是负数：开始时片段已经播了一段）
 *   anchor  caster / target（每个目标各一份）/ center（目标的中心）/ fly（从施法者飞到目标）
 *   dx, dy  相对锚点（脚底）的像素偏移，1 像素 = 人物的 1 个像素（游戏里 4 × heroScale 个布局单位）
 *   stagger 多个目标时每个目标往后错开的秒数
 *   behind  整段画在人物后面
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { PixelLayer } from '../src/pixel/PixelLayer';
import { composeFrame } from '../src/character/paperdoll';
import { CLIP_FRAMES, SPR_H, SPR_W } from '../src/character/rig';
import { CHARACTERS, buildEquipment } from '../src/items/characters';
// @ts-expect-error vendored plain JS
import { createFx, createFrame, clearFrame, composite } from '../vendor/pixelfx/src/core/index.js';

const out = process.argv[2] ?? 'vfx-export';
mkdirSync(`${out}/clips`, { recursive: true });
const FPS = 20;

const PAL = {
  rune: ['#06222a', '#0a4a56', '#108a94', '#24c8c8', '#6af0e0', '#c8fff6', '#ffffff'],
  violet: ['#140a30', '#2e1870', '#5a34c0', '#8a64f0', '#b89cff', '#e2d6ff', '#ffffff'],
  fire: ['#2a0804', '#6a1606', '#b8320c', '#f0681c', '#ffa83a', '#ffe08a', '#fffbe0'],
  amber: ['#2a1404', '#6a3a0c', '#b8701c', '#f0a832', '#ffd060', '#fff0b0', '#ffffff'],
  gold: ['#2a1a04', '#6a4a0c', '#b8861c', '#f0c040', '#ffe070', '#fff6c0', '#ffffff'],
  crimson: ['#2a0408', '#6a0c16', '#b02028', '#f04a3a', '#ff8a5a', '#ffd0a0', '#ffffff'],
  steel: ['#101420', '#2a3448', '#566880', '#94a8c0', '#cad8e8', '#f0f6ff', '#ffffff'],
  ice: ['#081a30', '#103a6a', '#1e6ab0', '#3ca0e6', '#80d0ff', '#d0f2ff', '#ffffff'],
  magenta: ['#2a0420', '#6a0c50', '#b01e8a', '#f04ab8', '#ff8ad8', '#ffd0f0', '#ffffff'],
  heal: ['#08261a', '#0e4228', '#1a7a44', '#2eb862', '#6ee896', '#b8ffd0', '#e8fff0', '#ffffff'],
  sweep: ['#081436', '#14328c', '#2a64d0', '#5ca8ff', '#9ad2ff', '#d8f0ff', '#ffffff'],
  fury: ['#2a0806', '#6a160a', '#b83214', '#f0602a', '#ff9a4a', '#ffd890', '#ffffff'],
  down: ['#140c14', '#2e1c28', '#5a3448', '#8a5068', '#b8889a', '#e8d0d8', '#ffffff'],
  goo: ['#0c1e10', '#1a4224', '#2e7a3a', '#4cb050', '#8ae07a', '#d0ffc0', '#ffffff'],
};

type Anchor = 'caster' | 'target' | 'center' | 'fly';
interface Ev {
  fx: string;
  at: number;
  anchor: Anchor;
  dx?: number;
  dy?: number;
  opts?: Record<string, unknown>;
  /** 循环特效：开始后多少秒淡出 */
  stop?: number;
  stagger?: number;
  behind?: boolean;
  /** fly：飞行时长、抛物线高度、出手点离地高度 */
  flight?: number;
  arc?: number;
  lift?: number;
}

const each = (fx: string, at: number, o: Partial<Ev> = {}): Ev => ({ fx, at, anchor: 'target', ...o });
const me = (fx: string, at: number, o: Partial<Ev> = {}): Ev => ({ fx, at, anchor: 'caster', ...o });

/** 命中类（hitInfo：release 0.05）：预览里命中在 0.75 秒，这里换成相对特效开始 */
const H = (previewAt: number) => +(previewAt - 0.7).toFixed(3);

const RECIPES: Record<string, Ev[]> = {
  // ---- 技能（时间和预览一样，从特效开始算）
  runeSlash: [
    me('arcane/rune-circle', 0.05, { stop: 1.3, opts: { palette: PAL.rune } }),
    me('arcane/spell-charge', 0.2, { stop: 0.8, opts: { palette: PAL.rune } }),
    me('melee/double-slash', 0.93, { opts: { palette: PAL.rune } }),
    each('impacts/crit-hit', 1.048, { dy: -10, opts: { palette: PAL.rune } }),
  ],
  dragonFlame: [
    me('arcane/spell-charge', 0, { stop: 0.46, opts: { palette: PAL.fire } }),
    me('fire/fire-breath', 0.41, { dx: 12, dy: -28, stop: 1.1, opts: { palette: PAL.fire, spread: 0.32, speed: 380, angle: 0.3 } }),
    each('impacts/blunt-hit', 0.58, { dy: -6, stagger: 0.1 }),
    each('status/burning', 0.76, { stop: 1.24 }),
  ],
  starlightPulse: [
    me('arcane/spell-charge', 0, { stop: 0.75, opts: { palette: PAL.violet } }),
    { fx: 'arcane/star-fall', at: 0.2, anchor: 'center', dy: -4, opts: { palette: PAL.violet } },
    each('impacts/hit-spark', 0.75, { dy: -10, stagger: 0.05, opts: { palette: PAL.violet } }),
  ],
  runeWard: [each('arcane/rune-circle', 0.15, { stop: 1.85, opts: { palette: PAL.rune } })],
  battleRune: [
    me('arcane/rune-circle', 0, { stop: 0.96, opts: { palette: PAL.amber } }),
    each('status/rage', 0.56, { stop: 1.34, opts: { palette: PAL.amber } }),
  ],
  dragonScaleWard: [
    me('arcane/spell-charge', 0, { stop: 0.56, opts: { palette: PAL.amber } }),
    each('holy/heal', 0.46, { opts: { palette: PAL.amber.concat('#ffffff') } }),
  ],
  dragonOrder: [
    me('holy/sunburst', 0.15, { dy: -24, behind: true, stop: 1.55, opts: { palette: PAL.crimson } }),
    each('holy/blessing', 0.56, { stagger: 0.3, stop: 1.4, opts: { palette: PAL.crimson } }),
  ],
  rally: [
    me('holy/halo', 0.05, { stop: 1.15, opts: { palette: PAL.gold } }),
    each('holy/blessing', 0.56, { stop: 1.3, opts: { palette: PAL.gold } }),
  ],
  dragonSoulWard: [
    me('arcane/spell-charge', 0, { stop: 0.38, opts: { palette: PAL.ice } }),
    me('holy/feather-burst', 0.38, { dy: -20, opts: { palette: PAL.ice } }),
  ],
  shieldDome: [each('arcane/rune-circle', 0.1, { stop: 1.4, opts: { palette: PAL.ice } })],
  healMicro: [each('holy/heal', 0.05, { opts: { palette: PAL.heal } })],
  healStandard: [each('nature/healing-bloom', 0), each('holy/heal', 0.25, { opts: { palette: PAL.heal } })],
  healStrong: [
    { fx: 'holy/heal-aoe', at: 0, anchor: 'center', dy: 6, opts: { reach: 70 } },
    each('holy/heal', 0.35, { stagger: 0.1, opts: { palette: PAL.heal } }),
  ],
  buffAura: [each('status/rage', 0.3, { stop: 2.4, opts: { palette: PAL.fury } }), each('holy/blessing', 0.3, { opts: { palette: PAL.fury } })],
  downAura: [each('arcane/rune-circle', 0.2, { stop: 2.6, opts: { palette: PAL.gold } }), each('pickups/crystal-shard', 0.5, { dy: -14, stop: 2.3, opts: { palette: PAL.gold } })],
  revive: [
    each('holy/holy-pillar', 0, { stop: 1.1, opts: { palette: PAL.gold } }),
    each('holy/feather-burst', 0.55, { dy: -18, opts: { palette: PAL.gold } }),
    each('holy/heal', 0.8, { opts: { palette: PAL.gold.concat('#ffffff') } }),
  ],
  playerDown: [
    each('impacts/blunt-hit', 0, { dy: -14 }),
    each('impacts/hit-spark', 0, { dy: -14 }),
    each('impacts/heavy-landing', 0.5),
    each('spawn/poof', 0.5, { opts: { palette: PAL.down } }),
  ],
  sweep: [
    me('melee/heavy-cleave', 0.768, { opts: { palette: PAL.sweep } }),
    { fx: 'melee/spin-slash', at: 1.0, anchor: 'center', dy: 12, opts: { palette: PAL.sweep } },
    each('impacts/hit-spark', 1.048, { dy: -10, stagger: 0.04, opts: { palette: PAL.sweep } }),
  ],
  natural20: [
    each('holy/sunburst', 0, { dy: -18, behind: true, stop: 1.8, opts: { palette: PAL.gold } }),
    each('impacts/crit-hit', 0, { dy: -12, opts: { palette: PAL.gold } }),
    each('ui/crit-number', 0.1, { dy: -44, opts: { text: '20!', label: 'NAT', palette: PAL.gold.concat('#ffffff') } }),
  ],
  // ---- 飞行物（release = 飞到的时刻）
  projBow: [
    { fx: 'projectiles/arrow', at: 0, anchor: 'fly', flight: 0.19, arc: 4, lift: 30 },
    each('impacts/hit-spark', 0.19, { dy: -12, opts: { palette: PAL.gold } }),
  ],
  projStaff: [
    me('arcane/spell-charge', 0, { stop: 0.49, opts: { palette: PAL.magenta } }),
    { fx: 'projectiles/plasma-shot', at: 0.49, anchor: 'fly', flight: 0.21, arc: 2, lift: 32, opts: { palette: PAL.magenta.concat('#ffffff') } },
    each('arcane/mana-burst', 0.7, { opts: { palette: PAL.magenta } }),
  ],
  projArcher: [
    { fx: 'projectiles/arrow', at: 0, anchor: 'fly', flight: 0.22, arc: 4, lift: 22 },
    each('impacts/hit-spark', 0.22, { dy: -14 }),
  ],
  projDragon: [
    { fx: 'fire/fireball', at: 0, anchor: 'fly', flight: 0.22, arc: 3, lift: 26, opts: { radius: 4 } },
    each('impacts/blunt-hit', 0.22, { dy: -14 }),
    each('status/burning', 0.22, { stop: 0.8 }),
  ],
  // ---- 命中：英雄打怪
  hitBlade: [me('melee/sword-slash', H(0.63), { opts: { palette: PAL.steel } }), each('impacts/hit-spark', H(0.75), { dy: -10, opts: { palette: PAL.steel } })],
  hitGreat: [me('melee/heavy-cleave', H(0.5), { opts: { palette: PAL.steel } }), each('impacts/blunt-hit', H(0.75), { dy: -6 })],
  hitBow: [each('impacts/hit-spark', H(0.75), { dy: -12, opts: { palette: PAL.gold } })],
  hitStaff: [each('arcane/mana-burst', H(0.75), { opts: { palette: PAL.magenta } })],
  hitAmbush: [me('melee/thrust', H(0.6), { opts: { palette: PAL.gold } }), each('impacts/crit-hit', H(0.75), { dy: -10, opts: { palette: PAL.gold } })],
  // ---- 命中：怪物打人（正向：怪物在左边往右打，游戏里方向 -1 时镜像）
  hitClaw: [each('melee/claw-swipe', H(0.55), { dx: -26 }), each('impacts/hit-spark', H(0.75), { dy: -14 })],
  hitWard: [each('melee/claw-swipe', H(0.55), { dx: -36 })],
  hitSlime: [each('nature/acid-splash', H(0.7), { dx: -4 }), each('impacts/hit-spark', H(0.75), { dy: -14, opts: { palette: PAL.goo } })],
  hitWolf: [each('melee/claw-swipe', H(0.33), { dx: -26 }), each('melee/claw-swipe', H(0.55), { dx: -24, dy: -4, opts: { seed: 5 } }), each('impacts/hit-spark', H(0.75), { dy: -14 })],
  hitArrowM: [each('impacts/hit-spark', H(0.75), { dy: -14 })],
  hitStone: [each('impacts/blunt-hit', H(0.75), { dy: -12 }), each('impacts/heavy-landing', H(0.75))],
  hitTroll: [each('impacts/ground-slam', H(0.65), { dx: -10, stop: 0.9, opts: { reach: 50 } }), each('impacts/blunt-hit', H(0.75), { dy: -12 })],
  hitDragon: [each('melee/claw-swipe', H(0.55), { dx: -26, opts: { palette: PAL.fire } }), each('explosions/small-explosion', H(0.75), { dx: 2, stop: 0.75, opts: { size: 0.45 } })],
  // ---- 怪物死亡（怪物本身的消散由游戏的死亡帧画，这里只加烟尘、碎屑、爆炸）
  deathSlime: [each('nature/acid-splash', 0, { opts: { palette: PAL.goo.concat('#ffffff') } })],
  deathWolf: [each('spawn/poof', 0.25)],
  deathGoblin: [each('spawn/poof', 0.2), each('spawn/coin-drop', 0.35)],
  deathStone: [each('impacts/blunt-hit', 0, { dy: -14 }), each('impacts/heavy-landing', 0.45)],
  deathTroll: [each('impacts/heavy-landing', 0.35), each('spawn/poof', 0.4)],
  deathDragon: [each('explosions/small-explosion', 0, { stop: 1.8, opts: { size: 0.8 } }), each('holy/feather-burst', 0.3, { dy: -20, opts: { palette: PAL.fire } })],
  deathBurst: [each('spawn/poof', 0.05)],
  // ---- 护盾：被打碎（常驻护盾的生成 / 待机 / 挨打由下面的 SHIELD 片段按单位的护盾状态播放）
  shieldBreak: [each('our/aegis', 0, { stop: 1.0, opts: { palette: PAL.ice, form: 0, breakAt: 0 } }), each('impacts/blunt-hit', 0, { dy: -14 })],
  shieldShell: [],
  shieldShellHit: [],
};

/** 常驻护盾：生成（0.6 秒）、待机（4 秒无缝循环）、挨打（0.6 秒，带一圈涟漪） */
const SHIELD: Record<string, { opts: Record<string, unknown>; seconds: number }> = {
  shieldForm: { opts: { palette: PAL.ice, form: 0.42 }, seconds: 0.6 },
  shieldIdle: { opts: { palette: PAL.ice, form: 0 }, seconds: 4 },
  shieldHit: { opts: { palette: PAL.ice, form: 0, hitAt: 0, hitAngle: -0.35 }, seconds: 0.6 },
};

// ---------------------------------------------------------------- 渲染

const loaders = import.meta.glob('../vendor/pixelfx/src/fx/*/*.js');
async function mod(id: string): Promise<unknown> {
  if (id === 'our/aegis') return import('../src/vfx/aegis');
  const load = loaders[`../vendor/pixelfx/src/fx/${id}.js`];
  if (!load) throw new Error(`pixelfx effect ${id} not found`);
  return load();
}

/**
 * 有的特效要描「角色的身体」（治疗、祝福、怒气、燃烧、光环）：给它一个通用的 Q 版人物轮廓（战斗待机的遮罩），
 * 但不给像素颜色——预渲染的帧是给所有人共用的，不能把某一个人的样子画进去；身体本身由游戏里的人物负责。
 */
const genericActor = (() => {
  const eq = buildEquipment(CHARACTERS[0]);
  eq.unequip('scarf'); eq.unequip('bag');
  const L = new PixelLayer(SPR_W, SPR_H);
  composeFrame(eq.resolve(), 'E', CLIP_FRAMES.ready[0], L);
  const rgba = new Uint8ClampedArray(SPR_W * SPR_H * 4);
  L.toRGBA(rgba);
  let x0 = SPR_W, y0 = SPR_H, x1 = -1, y1 = -1;
  for (let y = 0; y < SPR_H; y++) for (let x = 0; x < SPR_W; x++) if (rgba[(y * SPR_W + x) * 4 + 3]) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  const w = x1 - x0 + 1, h = y1 - y0 + 1, data = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) data[y * w + x] = rgba[((y0 + y) * SPR_W + x0 + x) * 4 + 3] ? 1 : 0;
  const lx = x0 - 21, ly = y0 - 59;
  return { mask: { w, h, data }, pixels: new Uint32Array(w * h), x: lx, y: ly, w, h, k: 2, head: [0, ly], chest: [0, ly + Math.round(h * 0.45)] };
})();

const BW = 420, BH = 320, OX = 210, OY = 230;
interface Clip { id: string; w: number; h: number; ox: number; oy: number; n: number; back: boolean; front: boolean; loop?: boolean }
const clips = new Map<string, Clip>();

async function renderClip(id: string, fx: string, opts: Record<string, unknown>, stop: number | undefined, seconds?: number): Promise<Clip> {
  const m = await mod(fx);
  // 没有淡出时间的循环特效（飞行物）：只渲染一个周期，游戏里循环播放
  const meta = (m as { meta?: { loop?: boolean; duration?: number } }).meta ?? {};
  const loop = !!meta.loop && stop === undefined && seconds === undefined;
  if (loop) seconds = meta.duration;
  const inst = (createFx as Function)(m, { ...opts, actor: { ...genericActor, mask: genericActor.mask }, x: OX, y: OY });
  const fb = createFrame(BW, BH), ff = createFrame(BW, BH);
  const backs: Uint8ClampedArray[] = [], fronts: Uint8ClampedArray[] = [];
  const dt = 1 / FPS, maxN = Math.round((seconds ?? 4.5) * FPS);
  for (let f = 0; f < maxN; f++) {
    if (seconds === undefined && inst.done()) break;
    clearFrame(fb); clearFrame(ff);
    inst.draw(fb, 'back'); inst.draw(ff, 'front');
    backs.push(composite(fb, new Uint8ClampedArray(BW * BH * 4), null));
    fronts.push(composite(ff, new Uint8ClampedArray(BW * BH * 4), null));
    if (stop !== undefined && f * dt >= stop) inst.stop();
    inst.update(dt);
  }
  // 所有帧的共同包围盒
  let x0 = BW, y0 = BH, x1 = -1, y1 = -1, anyB = false, anyF = false;
  const scan = (a: Uint8ClampedArray) => {
    let any = false;
    for (let y = 0; y < BH; y++) for (let x = 0; x < BW; x++) if (a[(y * BW + x) * 4 + 3] > 8) { any = true; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    return any;
  };
  for (const a of backs) anyB = scan(a) || anyB;
  for (const a of fronts) anyF = scan(a) || anyF;
  if (x1 < 0) { x0 = OX; y0 = OY; x1 = OX; y1 = OY; }
  const w = x1 - x0 + 1, h = y1 - y0 + 1, n = backs.length;
  const layers = [...(anyB ? backs : []), ...(anyF ? fronts : [])];
  const bytes = new Uint8Array(w * h * 4 * layers.length);
  layers.forEach((a, k) => { for (let y = 0; y < h; y++) bytes.set(a.subarray(((y0 + y) * BW + x0) * 4, ((y0 + y) * BW + x0 + w) * 4), (k * h + y) * w * 4); });
  writeFileSync(`${out}/clips/${id}.rgba`, bytes);
  if (x1 >= 0 && (x0 === 0 || y0 === 0 || x1 === BW - 1 || y1 === BH - 1)) console.warn(`  ${id}: touches the render box edge`);
  return { id, w, h, ox: OX - x0, oy: OY - y0, n, back: anyB, front: anyF, ...(loop ? { loop: true } : {}) };
}

const safe = (s: string) => s.replace(/[^a-zA-Z0-9]+/g, '_');
const recipes: Record<string, unknown[]> = {};
for (const [game, evs] of Object.entries(RECIPES)) {
  const list: unknown[] = [];
  for (const ev of evs) {
    const key = JSON.stringify([ev.fx, ev.opts ?? {}, ev.stop ?? null]);
    let clip = clips.get(key);
    if (!clip) {
      clip = await renderClip(`${safe(ev.fx)}_${clips.size}`, ev.fx, ev.opts ?? {}, ev.stop);
      clips.set(key, clip);
      console.log(`${clip.id}: ${clip.n} frames ${clip.w}x${clip.h}`);
    }
    const { fx: _fx, opts: _o, stop: _s, ...rest } = ev;
    list.push({ clip: clip.id, ...rest });
  }
  recipes[game] = list;
}
for (const [name, s] of Object.entries(SHIELD)) {
  const clip = await renderClip(name, 'our/aegis', s.opts, undefined, s.seconds);
  if (name === 'shieldIdle') clip.loop = true;
  clips.set(name, clip);
  console.log(`${clip.id}: ${clip.n} frames ${clip.w}x${clip.h}`);
}
writeFileSync(`${out}/recipes.json`, JSON.stringify({ fps: FPS, clips: [...clips.values()], recipes }, null, 1));
console.log(`${clips.size} clips, ${Object.keys(recipes).length} recipes`);
