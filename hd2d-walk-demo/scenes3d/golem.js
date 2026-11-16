/**
 * 苔石魔像（代码建模，精细版）。
 *   石块：二十面体细分 4 级（每块约 5 千个三角形），依次做
 *     ① 低频起伏（整体不圆）② 随机平面「凿切」（出现平整的切面和硬棱，像雕凿过的石头）
 *     ③ 脊状噪声刻裂缝 ④ 高频小坑；
 *   苔藓：朝上的区域按噪声长出一层鼓起来的苔垫（几何上真的凸出来），颜色深浅斑驳；
 *   顶点色：石色斑驳、裂缝和下面压暗、棱上提亮一点；
 *   细节件：拳头的指节、脚趾、腰间嵌石、眼窝、六棱柱水晶（胸口心核 + 背上一簇 + 肩上碎晶）、
 *     从心核沿胸口表面蔓延的发光裂纹（射线贴着身体表面走）、肩上垂下的藤蔓（带小叶子）、
 *     素材包的蘑菇和草。
 * 朝 +z，脚底 y = 0，约 2.7 米高。update(t) 播放 2.4 秒循环的待机动作。
 */
import * as THREE from 'three';
import { mergeVertices, mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ---------------------------------------------------------------- 噪声 / 随机
function hash3(x, y, z, s) { const h = Math.sin(x * 127.1 + y * 311.7 + z * 74.7 + s * 19.19) * 43758.5453; return h - Math.floor(h); }
function vnoise(x, y, z, s = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const f = (t) => t * t * (3 - 2 * t), u = f(x - xi), v = f(y - yi), w = f(z - zi);
  const L = (a, b, t) => a + (b - a) * t;
  const c = (dx, dy, dz) => hash3(xi + dx, yi + dy, zi + dz, s);
  return L(L(L(c(0, 0, 0), c(1, 0, 0), u), L(c(0, 1, 0), c(1, 1, 0), u), v), L(L(c(0, 0, 1), c(1, 0, 1), u), L(c(0, 1, 1), c(1, 1, 1), u), v), w);
}
const fbm = (x, y, z, s) => vnoise(x, y, z, s) * 0.55 + vnoise(x * 2.1, y * 2.1, z * 2.1, s + 1) * 0.3 + vnoise(x * 4.3, y * 4.3, z * 4.3, s + 2) * 0.15;
const ridged = (x, y, z, s) => 1 - Math.abs(fbm(x, y, z, s) * 2 - 1);
function mulberry(a) { return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ---------------------------------------------------------------- 材质
const STONE_A = new THREE.Color('#b0a38c'), STONE_B = new THREE.Color('#d2c5aa'), STONE_DARK = new THREE.Color('#5e5852'), STONE_EDGE = new THREE.Color('#d6cbb4');
const MOSS_A = new THREE.Color('#4a7429'), MOSS_B = new THREE.Color('#7da540'), MOSS_DARK = new THREE.Color('#33531f');
const STONE_MAT = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, name: 'GolemStone' });
const GLOW = '#7ff0d0';
const CRYSTAL_MAT = new THREE.MeshStandardMaterial({ color: '#58cdb8', emissive: GLOW, emissiveIntensity: 1.6, roughness: 0.35, name: 'GolemCrystal' });
const SEAM_MAT = new THREE.MeshStandardMaterial({ color: '#bfffee', emissive: GLOW, emissiveIntensity: 2.2, name: 'GolemSeam' });
const EYE_MAT = new THREE.MeshStandardMaterial({ color: '#effffa', emissive: GLOW, emissiveIntensity: 3.2, name: 'GolemEye' });
const SOCKET_MAT = new THREE.MeshStandardMaterial({ color: '#1f2226', roughness: 1, name: 'GolemSocket' });
const VINE_MAT = new THREE.MeshStandardMaterial({ color: '#4d7a2a', roughness: 0.9, name: 'GolemVine' });
const LEAF_MAT = new THREE.MeshStandardMaterial({ color: '#79a83a', roughness: 0.9, side: THREE.DoubleSide, name: 'GolemLeaf' });

/**
 * 一块石头。r 半径，s 三轴缩放，rot 旋转，at 位置（父节点坐标；苔藓按这个坐标系的「上」长）。
 * o.cuts 凿切面数，o.lump 起伏，o.crack 裂缝深浅，o.moss 苔藓多少（0..1），o.detail 细分级数
 */
function rock(r, s, rot, at, seed, o = {}) {
  const { cuts = 7, lump = 0.14, crack = 1, moss = 0.5, detail = 4 } = o;
  let g = new THREE.IcosahedronGeometry(1, detail);
  g.deleteAttribute('normal'); g.deleteAttribute('uv');
  g = mergeVertices(g);
  const rand = mulberry(seed * 7919 + 13);
  const planes = [];
  for (let k = 0; k < cuts; k++) {
    const n = new THREE.Vector3(rand() * 2 - 1, rand() * 2 - 1, rand() * 2 - 1).normalize();
    planes.push([n, 0.7 + rand() * 0.2]);
  }
  const p = g.attributes.position, v = new THREE.Vector3(), crackV = new Float32Array(p.count);
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    v.multiplyScalar(1 + (fbm(v.x * 1.3, v.y * 1.3, v.z * 1.3, seed) - 0.5) * 2 * lump);
    for (const [n, off] of planes) { const d = v.dot(n) - off; if (d > 0) v.addScaledVector(n, -d); }
    const c = Math.pow(ridged(v.x * 2.6, v.y * 2.6, v.z * 2.6, seed + 40), 12);
    crackV[i] = c;
    v.multiplyScalar(1 - c * 0.06 * crack + (vnoise(v.x * 11, v.y * 11, v.z * 11, seed + 50) - 0.5) * 0.022);
    p.setXYZ(i, v.x, v.y, v.z);
  }
  g.applyMatrix4(new THREE.Matrix4().compose(new THREE.Vector3(...at), new THREE.Quaternion().setFromEuler(new THREE.Euler(...rot)), new THREE.Vector3(...s).multiplyScalar(r)));
  g.computeVertexNormals();
  // 苔垫：朝上的区域按噪声鼓起来一层
  const nrm = g.attributes.normal, mossV = new Float32Array(p.count);
  if (moss > 0) {
    for (let i = 0; i < p.count; i++) {
      v.fromBufferAttribute(p, i);
      const ny = nrm.getY(i);
      const m = ny - 0.15 + (fbm(v.x * 2.4, v.y * 2.4, v.z * 2.4, seed + 9) - 0.5) * 0.9 - (1 - moss);
      const a = THREE.MathUtils.smoothstep(m, 0.0, 0.18);
      mossV[i] = a;
      if (a > 0) {
        const puff = (0.018 + vnoise(v.x * 14, v.y * 14, v.z * 14, seed + 60) * 0.03) * a;
        p.setXYZ(i, v.x + nrm.getX(i) * puff, v.y + nrm.getY(i) * puff, v.z + nrm.getZ(i) * puff);
      }
    }
    g.computeVertexNormals();
  }
  // 顶点色
  const col = new Float32Array(p.count * 3), c = new THREE.Color(), mc = new THREE.Color();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const ny = nrm.getY(i);
    c.copy(STONE_A).lerp(STONE_B, fbm(v.x * 2.5, v.y * 2.5, v.z * 2.5, seed + 5));
    if (ny < -0.2) c.lerp(STONE_DARK, Math.min(1, (-ny - 0.2) * 1.1));
    c.lerp(STONE_DARK, Math.min(1, crackV[i] * 1.6));
    // 小块浅色风化斑
    if (vnoise(v.x * 7, v.y * 7, v.z * 7, seed + 70) > 0.78) c.lerp(STONE_EDGE, 0.45);
    if (mossV[i] > 0) {
      mc.copy(MOSS_A).lerp(MOSS_B, fbm(v.x * 6, v.y * 6, v.z * 6, seed + 3));
      if (mossV[i] < 0.5) mc.lerp(MOSS_DARK, 0.5); // 苔垫边缘深一点
      c.lerp(mc, Math.min(1, mossV[i] * 1.6));
    }
    c.toArray(col, i * 3);
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const m = new THREE.Mesh(g, STONE_MAT);
  // 不接收投影：凹凸表面的自阴影在卡通分档下会变成一块块脏斑；站在树荫里也保持亮、好认（和像素人物一致）
  m.castShadow = true; m.receiveShadow = false;
  return m;
}

/** 六棱柱水晶（尖头），平面法线 */
function crystal(h, r, at, rot, mat = CRYSTAL_MAT) {
  const body = new THREE.CylinderGeometry(r, r * 0.85, h, 6, 1); body.translate(0, h / 2, 0);
  const tip = new THREE.ConeGeometry(r, r * 1.6, 6, 1); tip.translate(0, h + r * 0.8, 0);
  let g = mergeGeometries([body.toNonIndexed(), tip.toNonIndexed()]);
  g.deleteAttribute('uv'); g.computeVertexNormals();
  const m = new THREE.Mesh(g, mat);
  m.position.set(...at); m.rotation.set(...rot); m.castShadow = true;
  return m;
}

/** 发光裂纹：从 start 出发，在 mesh 正面表面上随机游走（每一步从前方打射线贴到表面） */
function seams(mesh, start, n, seed) {
  const rand = mulberry(seed), ray = new THREE.Raycaster(), group = new THREE.Group();
  mesh.updateMatrixWorld(true);
  const surf = (x, y) => {
    ray.set(new THREE.Vector3(x, y, 4), new THREE.Vector3(0, 0, -1));
    const h = ray.intersectObject(mesh, false)[0];
    return h ? h.point.addScaledVector(h.face.normal, 0.004) : null;
  };
  for (let k = 0; k < n; k++) {
    let a = (k / n) * Math.PI * 2 + rand() * 0.6, x = start[0], y = start[1];
    const pts = [];
    const steps = 7 + Math.floor(rand() * 6);
    for (let i = 0; i < steps; i++) {
      const pnt = surf(x, y); if (!pnt) break;
      pts.push(pnt);
      a += (rand() - 0.5) * 1.1; const st = 0.045 + rand() * 0.04;
      x += Math.cos(a) * st; y += Math.sin(a) * st;
    }
    if (pts.length < 3) continue;
    const curve = new THREE.CatmullRomCurve3(pts);
    // 越往外越细：分两段，外段细一半
    const tube = new THREE.TubeGeometry(curve, pts.length * 4, 0.014, 5, false);
    const rad = tube.attributes.position, cnt = rad.count, ring = 6;
    for (let i = 0; i < cnt; i++) {
      const seg = Math.floor(i / ring) / (cnt / ring), ctr = curve.getPoint(Math.min(1, seg));
      const t = 1 - seg * 0.7;
      rad.setXYZ(i, ctr.x + (rad.getX(i) - ctr.x) * t, ctr.y + (rad.getY(i) - ctr.y) * t, ctr.z + (rad.getZ(i) - ctr.z) * t);
    }
    tube.computeVertexNormals();
    group.add(new THREE.Mesh(tube, SEAM_MAT));
  }
  return group;
}

/** 藤蔓：一条管子 + 交替的小叶片 */
function vine(points, seed) {
  const rand = mulberry(seed), curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)));
  const group = new THREE.Group();
  const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 40, 0.022, 6, false), VINE_MAT); tube.castShadow = true;
  group.add(tube);
  const leafGeo = new THREE.SphereGeometry(0.07, 8, 5); leafGeo.scale(1, 0.25, 0.55);
  const L = curve.getLength(), n = Math.floor(L / 0.07);
  for (let i = 1; i < n; i++) {
    const t = i / n, pt = curve.getPoint(t), tan = curve.getTangent(t);
    const side = new THREE.Vector3().crossVectors(tan, new THREE.Vector3(0, 0, 1)).normalize().multiplyScalar(i % 2 ? 1 : -1);
    const leaf = new THREE.Mesh(leafGeo, LEAF_MAT);
    const sc = 0.7 + rand() * 0.6 - t * 0.3;
    leaf.scale.setScalar(sc);
    leaf.position.copy(pt).addScaledVector(side, 0.05 * sc);
    leaf.lookAt(pt.clone().addScaledVector(side, 1)); leaf.rotateX(Math.PI / 2 + (rand() - 0.5) * 0.8); leaf.rotateZ((rand() - 0.5) * 0.8);
    leaf.castShadow = true;
    group.add(leaf);
  }
  return group;
}

/** model(name)：素材包模型加载函数（点缀用的蘑菇、草） */
export async function buildGolem(model) {
  const root = new THREE.Group(); root.name = 'golem';
  // 腿 + 脚 + 脚趾
  for (const sx of [-1, 1]) {
    root.add(rock(0.36, [1, 1.35, 1], [0, 0, sx * 0.1], [sx * 0.48, 0.55, -0.05], 11 + sx, { moss: 0.2 }));
    root.add(rock(0.42, [1.15, 0.55, 1.35], [0, sx * 0.2, 0], [sx * 0.52, 0.16, 0.08], 21 + sx, { moss: 0.25, cuts: 9 }));
    for (let k = -1; k <= 1; k++) root.add(rock(0.12, [1, 0.75, 1.2], [0.2, 0, 0], [sx * 0.52 + k * 0.17 + sx * 0.04, 0.09, 0.58 - Math.abs(k) * 0.05], 25 + sx * 3 + k, { moss: 0, detail: 3 }));
  }
  // 上身：绕腰（y = 0.95）转，前倾
  const torso = new THREE.Group(); torso.position.set(0, 0.95, 0); root.add(torso);
  const body = rock(0.92, [1.18, 1.0, 0.86], [0.25, 0, 0], [0, 0.66, -0.05], 3, { moss: 0.65, cuts: 9 });
  torso.add(body);
  torso.add(rock(0.55, [1.3, 0.7, 0.9], [0.1, 0, 0], [0, 0.02, 0.05], 4, { moss: 0.15 }));
  // 腰间一圈嵌石
  for (let k = 0; k < 7; k++) {
    const a = -1.5 + k * 0.5;
    torso.add(rock(0.15 + (k % 3) * 0.03, [1.2, 0.8, 0.7], [0, a, 0.2], [Math.sin(a) * 0.68, 0.1 + (k % 2) * 0.06, Math.cos(a) * 0.48], 80 + k, { moss: 0.3, detail: 3 }));
  }
  // 心核 + 从心核蔓延的发光裂纹
  const coreAt = [0, 0.62, 0.66];
  torso.add(crystal(0.3, 0.12, coreAt, [0.25 + Math.PI / 2 * 0.15, 0.4, 0]));
  torso.add(crystal(0.18, 0.08, [0.1, 0.58, 0.66], [0.6, 0.2, -0.7]));
  torso.add(crystal(0.16, 0.07, [-0.1, 0.6, 0.66], [0.5, -0.3, 0.8]));
  torso.add(seams(body, [coreAt[0], coreAt[1] + 0.12], 6, 5));
  // 背上一簇水晶 + 肩上碎晶
  const back = [[0, 1.2, -0.5, 0.55, 0.13, -0.5, 0, 0], [0.3, 1.08, -0.58, 0.4, 0.1, -0.7, 0, -0.45], [-0.3, 1.1, -0.56, 0.46, 0.11, -0.6, 0, 0.45], [0.12, 0.85, -0.76, 0.3, 0.08, -1.0, 0, 0.2], [-0.15, 0.95, -0.72, 0.26, 0.07, -0.9, 0, -0.3], [0.45, 0.9, -0.6, 0.22, 0.06, -0.8, 0, -0.8]];
  for (const [x, y, z, h, r, rx, ry, rz] of back) torso.add(crystal(h, r, [x, y, z], [rx, ry, rz]));
  // 头：眉骨、鼻梁、下巴、眼窝 + 发光的眼
  const head = new THREE.Group(); head.position.set(0, 1.38, 0.5); torso.add(head);
  head.add(rock(0.48, [1.12, 0.86, 1.0], [0, 0, 0], [0, 0, 0], 7, { moss: 0.7, cuts: 8 }));
  head.add(rock(0.36, [1.5, 0.42, 0.62], [-0.15, 0, 0], [0, 0.17, 0.3], 8, { moss: 0.8, lump: 0.1 }));
  head.add(rock(0.13, [0.8, 1.2, 0.9], [0.3, 0, 0], [0, -0.04, 0.44], 10, { moss: 0, detail: 3 }));
  head.add(rock(0.27, [1.45, 0.55, 0.8], [0.2, 0, 0], [0, -0.27, 0.26], 9, { moss: 0 }));
  const eyes = [];
  for (const sx of [-1, 1]) {
    const so = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 10), SOCKET_MAT); so.scale.set(1.35, 0.8, 0.5); so.position.set(sx * 0.19, 0.04, 0.4); head.add(so);
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.075, 16, 10), EYE_MAT);
    e.scale.set(1.5, 0.85, 0.5); e.position.set(sx * 0.19, 0.04, 0.45); head.add(e); eyes.push(e);
  }
  // 手臂：肩 → 上臂 → 前臂 → 拳头 + 指节 + 拇指；肩上碎晶
  const arms = [];
  for (const sx of [-1, 1]) {
    const sh = new THREE.Group(); sh.position.set(sx * 1.02, 1.08, 0.05); torso.add(sh); arms.push(sh);
    sh.add(rock(0.5, [1.1, 0.95, 1.0], [0, 0, sx * 0.3], [sx * 0.05, 0.05, 0], 31 + sx, { moss: 0.8, cuts: 9 }));
    sh.add(rock(0.3, [1, 1.45, 1], [0.1, 0, sx * 0.12], [sx * 0.1, -0.52, 0.05], 41 + sx, { moss: 0.2 }));
    sh.add(rock(0.36, [1.05, 1.3, 1.05], [-0.15, 0, sx * 0.05], [sx * 0.14, -1.0, 0.14], 51 + sx, { moss: 0.25 }));
    const fist = new THREE.Group(); fist.position.set(sx * 0.16, -1.5, 0.22); fist.rotation.set(0.2, sx * 0.3, 0); sh.add(fist);
    fist.add(rock(0.5, [1.12, 0.95, 1.1], [0, 0, 0], [0, 0, 0], 61 + sx, { moss: 0.4, cuts: 9 }));
    for (let k = 0; k < 4; k++) fist.add(rock(0.13, [1, 0.95, 1.1], [0, 0, 0], [(k - 1.5) * 0.2, -0.16 + Math.abs(k - 1.5) * 0.03, 0.47], 70 + k + sx * 5, { moss: 0, detail: 3 }));
    fist.add(rock(0.13, [1, 1.3, 1], [0, 0, sx * -0.5], [sx * -0.42, 0.02, 0.36], 78 + sx, { moss: 0, detail: 3 }));
    sh.add(crystal(0.22, 0.06, [sx * 0.2, 0.38, -0.2], [-0.4, 0, sx * -0.5]));
    sh.add(crystal(0.15, 0.045, [sx * 0.32, 0.3, -0.12], [-0.2, 0, sx * -0.9]));
  }
  // 藤蔓：从右肩顶垂到上臂外侧，从头侧垂下一小段
  arms[1].add(vine([[0.05, 0.5, 0.2], [0.35, 0.35, 0.36], [0.48, 0.0, 0.36], [0.45, -0.35, 0.34], [0.4, -0.6, 0.38]], 3));
  head.add(vine([[-0.35, 0.25, 0.15], [-0.52, 0.0, 0.2], [-0.55, -0.25, 0.22]], 4));
  // 点缀：蘑菇、草、小蕨（素材包，同一套卡通材质）
  const deco = async (name, parent, at, s, ry = 0, rx = 0, rz = 0) => {
    const m = await model(name); m.position.set(...at); m.scale.setScalar(s); m.rotation.set(rx, ry, rz); parent.add(m); return m;
  };
  await Promise.all([
    deco('Mushroom_Laetiporus', arms[0], [-0.3, 0.2, 0.25], 0.5, -1.2, 0, 0.5),
    deco('Mushroom_Common', arms[1], [0.18, 0.4, 0.05], 0.45, 0.5),
    deco('Mushroom_Common', head, [0.3, 0.32, -0.1], 0.3, 1.5),
    deco('Grass_Common_Short', arms[1], [0.0, 0.42, -0.12], 0.32, 1.0),
    deco('Grass_Wispy_Short', arms[0], [0.05, 0.44, -0.05], 0.3, 0.3),
    deco('Grass_Common_Short', head, [-0.05, 0.36, -0.05], 0.3, 0.2),
    deco('Fern_1', torso, [-0.45, 1.25, -0.2], 0.08, 0.6),
    deco('Grass_Wispy_Short', torso, [0.4, 1.32, 0.0], 0.3, 2.1),
    deco('Clover_1', fist0(arms[0]), [0.1, 0.4, 0.0], 0.5, 0.4),
  ]);

  const PERIOD = 2.4;
  root.userData.update = (t) => {
    const ph = (t / PERIOD) * Math.PI * 2, b = Math.sin(ph);
    torso.position.y = 0.95 + b * 0.035;
    torso.rotation.x = b * 0.025;
    head.rotation.set(Math.sin(ph + 0.6) * 0.04, Math.sin(ph) * 0.1, 0);
    arms.forEach((a, i) => { a.rotation.x = Math.sin(ph + i * Math.PI) * 0.06 - b * 0.02; a.rotation.z = (i ? 1 : -1) * b * 0.03; });
    const pulse = 0.5 + 0.5 * Math.sin(ph * 2);
    // 材质会被换成卡通材质，按名字找
    root.traverse((o) => {
      if (!o.isMesh) return;
      if (o.material.name === 'GolemCrystal') o.material.emissiveIntensity = 1.1 + pulse * 1.0;
      if (o.material.name === 'GolemSeam') o.material.emissiveIntensity = 1.4 + pulse * 1.6;
    });
    const k = (t / PERIOD) % 1, blink = k > 0.62 && k < 0.72 ? Math.sin((k - 0.62) / 0.1 * Math.PI) : 0;
    eyes.forEach((e) => { e.scale.y = 0.85 * (1 - blink * 0.9); });
  };
  root.userData.update(0);
  return root;
}
const fist0 = (sh) => sh.children.find((c) => c.isGroup);
