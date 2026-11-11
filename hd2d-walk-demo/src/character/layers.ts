/**
 * 纸娃娃图层，从后到前。
 * 对应需求里的顺序：后围巾/披风 → 后手武器 → 身体 → 下装 → 上衣 → 挎包 → 头 → 头发 → 前手武器，
 * 中间补了手臂前后层、鞋、肩披等细分层。
 */
export const LAYER_ORDER = [
  'cape',          // 披风 / 身后的东西
  'weapon_back',   // 被身体挡住的武器
  'arm_back',      // 远侧手臂
  'legs',          // 身体：腿
  'bottom',        // 下装
  'shoes',         // 鞋
  'torso',         // 身体：躯干
  'top',           // 上衣
  'bag',           // 挎包
  'arm_front',     // 近侧手臂（含袖子）
  'mantle',        // 肩披 / 背向时的披风
  'weapon_mid',    // 竖握的长柄武器：在手和身体前面，但被头挡住
  'hair_back',     // 后脑勺一侧、被头挡住的头发
  'head',          // 头
  'scarf',         // 围巾（颈部一圈）
  'hair',          // 头发
  'weapon_front',  // 身前的武器
] as const;

export type LayerId = (typeof LAYER_ORDER)[number];

/** 每个图层的默认 z 值（间隔 10，方便 layerOverride 插到中间） */
export const Z = Object.fromEntries(LAYER_ORDER.map((id, i) => [id, i * 10])) as Record<LayerId, number>;
