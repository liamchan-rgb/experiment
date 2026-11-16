/**
 * 苔石魔像（代码建模，第三版：参考素材包石头的做法）
 *
 * 素材包的石头 = 形体干净的模型 + 烘焙的手绘贴图（淡紫灰石面、亮的棱边、暗的缝隙、缝里和顶上长苔藓）。这里用代码做同样的两件事：
 *
 * 1. 形体：每个能动的部件（躯干连头、左右手臂、下身连腿脚）是「一整块」——用有向距离场（SDF）把椭球
 *    平滑并在一起（smooth union，接缝是雕出来的过渡，不是球插球），再用随机平面「凿」出切面和硬棱，
 *    眼窝、心核的凹坑是直接挖出来的；最后用 marching cubes 转成网格，法线取距离场梯度（棱是利的）。
 * 2. 表面：不靠顶点色（会糊），在着色器里逐像素画：
 *    石色斑驳 + 细裂纹 → 凸棱提亮（曲率，来自距离场的拉普拉斯）→ 凹处压暗 →
 *    朝上和凹处长苔藓（硬边 + 黄绿色毛边 + 小斑点）→ 躯干上从心核往外的发光裂纹（自发光，会脉动）。
 *
 * 朝 +z，脚底 y = 0，约 2.7 米高。update(t) 播放 2.4 秒循环的待机。
 */
import * as THREE from 'three';
import { MarchingCubes } from 'three/addons/objects/MarchingCubes.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ---------------------------------------------------------------- 噪声 / 随机
function hash3(x, y, z, s) { const h = Math.sin(x * 127.1 + y * 311.7 + z * 74.7 + s * 19.19) * 43758.5453; return h - Math.floor(h); }
function vnoise(x, y, z, s = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const f = (t) => t * t * (3 - 2 * t), u = f(x - xi), v = f(y - yi), w = f(z - zi);
  const L = (a, b, t) => a + (b - a) * t;
  const c = (dx, dy, dz) => hash3(xi + dx, yi + dy, zi + dz, s);
  return L(L(L(c(0, 0, 0), c(1, 0, 0), u), L(c(0, 1, 0), c(1, 1, 0), u), v), L(L(c(0, 0, 1), c(1, 0, 1), u), L(c(0, 1, 1), c(1, 1, 1), u), v), w);
}
function mulberry(a) { return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ---------------------------------------------------------------- SDF
const smin = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k * 0.25; };
const smax = (a, b, k) => -smin(-a, -b, k);
/**
 * 一个「石块」原件：椭球 + 若干凿切平面。
 * { c: 中心, r: 三轴半径, rot: 欧拉角, cuts: 切面数, k: 和前面的融合半径（0 = 硬接）, seed, sub: true = 挖掉 }
 */
function prim(o) {
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(...(o.rot ?? [0, 0, 0])));
  const inv = q.clone().invert(), e = inv.elements ?? null;
  const m = new THREE.Matrix4().makeRotationFromQuaternion(inv).elements;
  const [rx, ry, rz] = o.r, rand = mulberry((o.seed ?? 1) * 7919 + 3);
  const planes = [];
  for (let i = 0; i < Math.round((o.cuts ?? 0) * 1.2); i++) {
    const n = new THREE.Vector3(rand() * 2 - 1, rand() * 2 - 1, rand() * 2 - 1).normalize();
    const support = Math.hypot(rx * n.x, ry * n.y, rz * n.z);
    planes.push([n.x, n.y, n.z, support * (0.7 + rand() * 0.18)]);
  }
  const [cx, cy, cz] = o.c;
  return {
    k: o.k ?? 0.1, sub: !!o.sub,
    d(x, y, z) {
      const px = x - cx, py = y - cy, pz = z - cz;
      const lx = m[0] * px + m[4] * py + m[8] * pz, ly = m[1] * px + m[5] * py + m[9] * pz, lz = m[2] * px + m[6] * py + m[10] * pz;
      const k0 = Math.hypot(lx / rx, ly / ry, lz / rz), k1 = Math.hypot(lx / (rx * rx), ly / (ry * ry), lz / (rz * rz));
      let d = k0 * (k0 - 1) / Math.max(k1, 1e-6);
      for (const [nx, ny, nz, off] of planes) d = smax(d, nx * lx + ny * ly + nz * lz - off, 0.035);
      return d;
    },
  };
}
/** 把一组原件合成一个 SDF（加一点表面起伏） */
function body(prims, seed, bump = 1) {
  return (x, y, z) => {
    let d = 1e9;
    for (const p of prims) {
      const v = p.d(x, y, z);
      if (p.sub) d = smax(d, -v, p.k); else d = d > 1e8 ? v : smin(d, v, p.k);
    }
    // 表面起伏：大的轻微鼓包 + 很小的凿痕
    return d + ((vnoise(x * 3.2, y * 3.2, z * 3.2, seed) - 0.5) * 0.035 + (vnoise(x * 11, y * 11, z * 11, seed + 1) - 0.5) * 0.008) * bump;
  };
}
/** SDF → 网格（marching cubes），法线 = 距离场梯度，曲率 = 拉普拉斯 */
function mesh(sdf, center, half, res, material) {
  const mc = new MarchingCubes(res, new THREE.MeshBasicMaterial(), false, false, 400000);
  mc.isolation = 0;
  const f = mc.field;
  for (let zi = 0; zi < res; zi++) for (let yi = 0; yi < res; yi++) for (let xi = 0; xi < res; xi++) {
    const x = center[0] + ((xi - res / 2) / (res / 2)) * half, y = center[1] + ((yi - res / 2) / (res / 2)) * half, z = center[2] + ((zi - res / 2) / (res / 2)) * half;
    f[zi * res * res + yi * res + xi] = -sdf(x, y, z);
  }
  mc.update();
  const n = mc.count, pos = new Float32Array(n * 3), nrm = new Float32Array(n * 3), curv = new Float32Array(n);
  const e = 0.006, ec = 0.035;
  for (let i = 0; i < n; i++) {
    const x = center[0] + mc.positionArray[i * 3] * half, y = center[1] + mc.positionArray[i * 3 + 1] * half, z = center[2] + mc.positionArray[i * 3 + 2] * half;
    pos[i * 3] = x; pos[i * 3 + 1] = y; pos[i * 3 + 2] = z;
    let gx = sdf(x + e, y, z) - sdf(x - e, y, z), gy = sdf(x, y + e, z) - sdf(x, y - e, z), gz = sdf(x, y, z + e) - sdf(x, y, z - e);
    const l = Math.hypot(gx, gy, gz) || 1;
    nrm[i * 3] = gx / l; nrm[i * 3 + 1] = gy / l; nrm[i * 3 + 2] = gz / l;
    const d0 = sdf(x, y, z);
    curv[i] = (sdf(x + ec, y, z) + sdf(x - ec, y, z) + sdf(x, y + ec, z) + sdf(x, y - ec, z) + sdf(x, y, z + ec) + sdf(x, y, z - ec) - 6 * d0) / (ec * ec);
  }
  // marching cubes 的三角形绕向和 three 的正面相反时翻一下（用第一个三角形的面法线和梯度比）
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
  g.setAttribute('aCurv', new THREE.BufferAttribute(curv, 1));
  const a = new THREE.Vector3(...pos.slice(0, 3)), b = new THREE.Vector3(...pos.slice(3, 6)), c = new THREE.Vector3(...pos.slice(6, 9));
  const fn = new THREE.Vector3().crossVectors(b.sub(a), c.sub(a));
  if (fn.dot(new THREE.Vector3(...nrm.slice(0, 3))) < 0) {
    const idx = []; for (let i = 0; i < n; i += 3) idx.push(i, i + 2, i + 1);
    g.setIndex(idx);
  }
  const me = new THREE.Mesh(g, material);
  me.castShadow = true; me.receiveShadow = false;
  return me;
}

// ---------------------------------------------------------------- 石头表面（卡通材质的着色补丁）
const GLOW = new THREE.Color('#7ff0d0');
function stoneMaterial(name, core) {
  const mat = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 1, name });
  mat.userData.toonPatch = (sh, toonMat) => {
    sh.uniforms.glowAmt = { value: toonMat.userData.glowAmt ?? 1 };
    sh.uniforms.coreP = { value: new THREE.Vector3(...(core ?? [0, -100, 0])) };
    sh.uniforms.glowCol = { value: GLOW.clone() };
    sh.uniforms.golemFloor = { value: toonMat.userData.floorY ?? 0 };
    sh.uniforms.bumpK = { value: 0.035 };
    toonMat.userData.shader = sh;
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float aCurv; varying float vCurv; varying vec3 vOP; varying vec3 vWN; varying vec3 vWP;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvCurv = aCurv; vOP = position; vWN = normalize(mat3(modelMatrix) * normal); vWP = (modelMatrix * vec4(position, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', /* glsl */`#include <common>
        varying float vCurv; varying vec3 vOP; varying vec3 vWN; varying vec3 vWP;
        uniform float glowAmt, golemFloor, bumpK; uniform vec3 coreP, glowCol;
        float h3(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
        float n3(vec3 x){ vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
          return mix(mix(mix(h3(i), h3(i + vec3(1,0,0)), f.x), mix(h3(i + vec3(0,1,0)), h3(i + vec3(1,1,0)), f.x), f.y),
                     mix(mix(h3(i + vec3(0,0,1)), h3(i + vec3(1,0,1)), f.x), mix(h3(i + vec3(0,1,1)), h3(i + vec3(1,1,1)), f.x), f.y), f.z); }
        float fb(vec3 p){ return n3(p) * 0.5 + n3(p * 2.03) * 0.25 + n3(p * 4.07) * 0.15 + n3(p * 8.3) * 0.1; }
        vec3 srgb(vec3 c){ return pow(c, vec3(2.2)); }
      `)
      .replace('#include <map_fragment>', /* glsl */`
        // 参照 Bestiary 怪物的上色：中等明度、饱和的固有色，内部对比低；
        // 明暗靠大的色区渐变（上亮下暗、凹处暗）而不是亮边，细节交给雕刻（下面的凹凸）
        vec3 P = vOP;
        vec3 sDark = srgb(vec3(0.42, 0.40, 0.37)), sMid = srgb(vec3(0.58, 0.55, 0.50)), sLight = srgb(vec3(0.67, 0.63, 0.57));
        float big = fb(P * 1.6);
        vec3 stone = mix(sDark, sMid, smoothstep(0.2, 0.55, big));
        stone = mix(stone, sLight, smoothstep(0.55, 0.8, big) * 0.7);
        // 上亮下暗（像烘焙的环境光遮蔽）
        stone *= mix(0.72, 1.06, smoothstep(0.1, 2.3, vWP.y - golemFloor));
        float convex = smoothstep(8.0, 18.0, vCurv), concave = smoothstep(-2.0, -10.0, vCurv);
        stone = mix(stone, stone * 1.18, convex * 0.5);
        stone *= 1.0 - concave * 0.4;
        float cr = abs(fb(P * 2.6 + 11.0) - 0.5);
        float crack = (1.0 - smoothstep(0.004, 0.02, cr)) * (1.0 - step(0.4, n3(P * 1.3 + 5.0)));
        stone *= 1.0 - crack * 0.35;
        // 苔藓：暗橄榄绿，软过渡，长在朝上和凹处
        float m = vWN.y * 0.8 + concave * 0.5 + (fb(P * 2.2 + 3.0) - 0.5) * 0.9 - convex * 0.2;
        float moss = smoothstep(0.42, 0.6, m);
        vec3 mossC = mix(srgb(vec3(0.30, 0.38, 0.14)), srgb(vec3(0.44, 0.52, 0.19)), smoothstep(0.3, 0.75, fb(P * 5.0)));
        vec3 col = mix(stone, mossC, moss);
        diffuseColor.rgb *= col;
      `)
      .replace('#include <normal_fragment_maps>', /* glsl */`#include <normal_fragment_maps>
        {
          // 雕刻细节（程序化凹凸）：裂缝刻进去、表面有凿痕和小坑，苔藓处是软的小鼓包
          vec3 Q = vOP;
          float c2 = abs(fb(Q * 2.6 + 11.0) - 0.5);
          float h = -(1.0 - smoothstep(0.004, 0.03, c2)) * (1.0 - step(0.4, n3(Q * 1.3 + 5.0))) * 1.0
                    + fb(Q * 6.0) * 0.4 + n3(Q * 18.0) * 0.06;
          vec2 dh = vec2(dFdx(h), dFdy(h)) * bumpK;
          vec3 sp = -vViewPosition;
          vec3 sx = dFdx(sp), sy = dFdy(sp), R1 = cross(sy, normal), R2 = cross(normal, sx);
          float det = dot(sx, R1);
          normal = normalize(abs(det) * normal - sign(det) * (dh.x * R1 + dh.y * R2));
        }
      `)
      .replace('#include <emissivemap_fragment>', /* glsl */`#include <emissivemap_fragment>
        // 心核发出的发光裂纹：只在心核附近、沿另一套裂纹走，越远越淡
        float gl = abs(fb(vOP * 2.4 + 37.0) - 0.5);
        float fall = 1.0 - smoothstep(0.1, 0.5, distance(vOP, coreP));
        float line = 1.0 - smoothstep(0.012, 0.03, gl);
        totalEmissiveRadiance += glowCol * glowAmt * line * fall * 2.2;
        totalEmissiveRadiance += glowCol * glowAmt * smoothstep(0.35, 0.0, distance(vOP, coreP)) * 0.25;
      `);
  };
  return mat;
}

// ---------------------------------------------------------------- 发光件、藤蔓
const CRYSTAL_MAT = new THREE.MeshStandardMaterial({ color: '#58cdb8', emissive: GLOW, emissiveIntensity: 1.6, roughness: 0.35, name: 'GolemCrystal' });
const EYE_MAT = new THREE.MeshStandardMaterial({ color: '#effffa', emissive: GLOW, emissiveIntensity: 3.2, name: 'GolemEye' });
const VINE_MAT = new THREE.MeshStandardMaterial({ color: '#4d7a2a', roughness: 0.9, name: 'GolemVine' });
const LEAF_MAT = new THREE.MeshStandardMaterial({ color: '#79a83a', roughness: 0.9, side: THREE.DoubleSide, name: 'GolemLeaf' });

function crystal(h, r, at, rot) {
  const b = new THREE.CylinderGeometry(r, r * 0.85, h, 6, 1); b.translate(0, h / 2, 0);
  const t = new THREE.ConeGeometry(r, r * 1.6, 6, 1); t.translate(0, h + r * 0.8, 0);
  const g = mergeGeometries([b.toNonIndexed(), t.toNonIndexed()]); g.deleteAttribute('uv'); g.computeVertexNormals();
  const m = new THREE.Mesh(g, CRYSTAL_MAT); m.position.set(...at); m.rotation.set(...rot); m.castShadow = true;
  return m;
}
function vine(points, seed) {
  const rand = mulberry(seed), curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)));
  const group = new THREE.Group();
  const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 40, 0.022, 6, false), VINE_MAT); tube.castShadow = true; group.add(tube);
  const leafGeo = new THREE.SphereGeometry(0.07, 8, 5); leafGeo.scale(1, 0.25, 0.55);
  const n = Math.floor(curve.getLength() / 0.07);
  for (let i = 1; i < n; i++) {
    const t = i / n, pt = curve.getPoint(t), tan = curve.getTangent(t);
    const side = new THREE.Vector3().crossVectors(tan, new THREE.Vector3(0, 0, 1)).normalize().multiplyScalar(i % 2 ? 1 : -1);
    const leaf = new THREE.Mesh(leafGeo, LEAF_MAT), sc = 0.7 + rand() * 0.6 - t * 0.3;
    leaf.scale.setScalar(sc); leaf.position.copy(pt).addScaledVector(side, 0.05 * sc);
    leaf.lookAt(pt.clone().addScaledVector(side, 1)); leaf.rotateX(Math.PI / 2 + (rand() - 0.5) * 0.8); leaf.rotateZ((rand() - 0.5) * 0.8);
    leaf.castShadow = true; group.add(leaf);
  }
  return group;
}

// ---------------------------------------------------------------- 组装
export async function buildGolem(model, { res = 1 } = {}) {
  const R = (n) => Math.round(n * res);
  const root = new THREE.Group(); root.name = 'golem';
  const STONE = stoneMaterial('GolemStone'), CORE_AT = [0, 0.64, 0.6];
  const STONE_CORE = stoneMaterial('GolemStoneCore', CORE_AT);

  // 下身：骨盆 + 两条腿 + 脚 + 脚趾（一整块）
  const lower = [prim({ c: [0, 0.82, -0.02], r: [0.62, 0.3, 0.42], cuts: 6, seed: 2 })];
  for (const sx of [-1, 1]) {
    lower.push(prim({ c: [sx * 0.47, 0.52, -0.04], r: [0.34, 0.46, 0.34], rot: [0, 0, sx * 0.1], cuts: 6, seed: 10 + sx, k: 0.14 }));
    lower.push(prim({ c: [sx * 0.52, 0.17, 0.1], r: [0.46, 0.22, 0.56], rot: [0, sx * 0.2, 0], cuts: 7, seed: 20 + sx, k: 0.12 }));
    lower.push(prim({ c: [sx * 0.56, 0.13, 0.55], r: [0.36, 0.13, 0.2], cuts: 4, seed: 30 + sx, k: 0.08 })); // 脚尖一块
  }
  root.add(mesh(body(lower, 5), [0, 0.6, 0.15], 1.12, R(96), STONE));

  // 躯干 + 头（一整块）：前倾的大胸、腰、眉骨、鼻、下巴；挖出眼窝和心核的坑
  const torso = new THREE.Group(); torso.position.set(0, 0.95, 0); root.add(torso);
  const tp = [
    prim({ c: [0, 0.66, -0.05], r: [1.02, 0.92, 0.76], rot: [0.25, 0, 0], cuts: 9, seed: 3 }),
    prim({ c: [0, 0.08, 0.04], r: [0.68, 0.38, 0.46], cuts: 6, seed: 4, k: 0.16 }),
    prim({ c: [0, 1.36, 0.48], r: [0.5, 0.4, 0.46], cuts: 8, seed: 7, k: 0.16 }),
    prim({ c: [0, 1.5, 0.78], r: [0.5, 0.13, 0.2], rot: [-0.2, 0, 0], cuts: 4, seed: 8, k: 0.06 }),
    prim({ c: [0, 1.32, 0.9], r: [0.09, 0.15, 0.11], rot: [0.3, 0, 0], cuts: 3, seed: 9, k: 0.05 }),
    prim({ c: [0, 1.1, 0.72], r: [0.36, 0.14, 0.22], rot: [0.2, 0, 0], cuts: 4, seed: 6, k: 0.07 }),
    prim({ c: [-0.19, 1.38, 0.88], r: [0.15, 0.1, 0.12], sub: true, k: 0.04 }),
    prim({ c: [0.19, 1.38, 0.88], r: [0.15, 0.1, 0.12], sub: true, k: 0.04 }),
    prim({ c: CORE_AT, r: [0.2, 0.24, 0.16], sub: true, k: 0.06 }),
  ];
  torso.add(mesh(body(tp, 15), [0, 0.75, 0.15], 1.25, R(120), STONE_CORE));
  // 心核水晶簇（坐在坑里）、眼睛、背上水晶
  torso.add(crystal(0.3, 0.1, [0, 0.52, 0.58], [0.35, 0.4, 0]));
  torso.add(crystal(0.2, 0.07, [0.08, 0.52, 0.58], [0.7, 0.2, -0.7]));
  torso.add(crystal(0.18, 0.065, [-0.08, 0.53, 0.58], [0.6, -0.3, 0.8]));
  const eyes = [];
  for (const sx of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.085, 16, 10), EYE_MAT);
    e.scale.set(1.4, 0.7, 0.6); e.position.set(sx * 0.19, 1.38, 0.86); torso.add(e); eyes.push(e);
  }
  const back = [[0, 1.2, -0.5, 0.55, 0.13, -0.5, 0, 0], [0.3, 1.08, -0.58, 0.4, 0.1, -0.7, 0, -0.45], [-0.3, 1.1, -0.56, 0.46, 0.11, -0.6, 0, 0.45], [0.12, 0.85, -0.76, 0.3, 0.08, -1.0, 0, 0.2], [-0.15, 0.95, -0.72, 0.26, 0.07, -0.9, 0, -0.3]];
  for (const [x, y, z, h, r, rx, ry, rz] of back) torso.add(crystal(h, r, [x, y, z], [rx, ry, rz]));

  // 手臂（各一整块）：肩甲 → 上臂 → 前臂 → 拳头 + 指节 + 拇指
  const arms = [];
  for (const sx of [-1, 1]) {
    const sh = new THREE.Group(); sh.position.set(sx * 1.0, 1.08, 0.05); torso.add(sh); arms.push(sh);
    const ap = [
      prim({ c: [sx * 0.06, 0.06, 0], r: [0.56, 0.48, 0.52], rot: [0, 0, sx * 0.3], cuts: 9, seed: 40 + sx }),
      prim({ c: [sx * 0.1, -0.52, 0.05], r: [0.28, 0.42, 0.28], rot: [0.1, 0, sx * 0.12], cuts: 5, seed: 42 + sx, k: 0.07 }),
      prim({ c: [sx * 0.14, -1.0, 0.14], r: [0.35, 0.45, 0.36], rot: [-0.15, 0, sx * 0.05], cuts: 6, seed: 44 + sx, k: 0.06 }),
      prim({ c: [sx * 0.16, -1.5, 0.22], r: [0.54, 0.46, 0.54], rot: [0.2, sx * 0.3, 0], cuts: 8, seed: 46 + sx, k: 0.06 }),
    ];
    const fq = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.2, sx * 0.3, 0));
    for (let k = 0; k < 4; k++) {
      const off = new THREE.Vector3((k - 1.5) * 0.2, -0.17 + Math.abs(k - 1.5) * 0.03, 0.47).applyQuaternion(fq);
      ap.push(prim({ c: [sx * 0.16 + off.x, -1.5 + off.y, 0.22 + off.z], r: [0.13, 0.14, 0.14], cuts: 4, seed: 50 + k + sx * 5, k: 0.1 }));
    }
    const th = new THREE.Vector3(-sx * 0.44, 0.02, 0.32).applyQuaternion(fq);
    ap.push(prim({ c: [sx * 0.16 + th.x, -1.5 + th.y, 0.22 + th.z], r: [0.14, 0.19, 0.14], rot: [0, 0, sx * -0.5], cuts: 4, seed: 60 + sx, k: 0.1 }));
    sh.add(mesh(body(ap, 25 + sx), [sx * 0.12, -0.7, 0.15], 1.35, R(124), STONE));
    sh.add(crystal(0.22, 0.06, [sx * 0.2, 0.42, -0.2], [-0.4, 0, sx * -0.5]));
    sh.add(crystal(0.15, 0.045, [sx * 0.34, 0.33, -0.12], [-0.2, 0, sx * -0.9]));
  }
  arms[1].add(vine([[0.05, 0.5, 0.2], [0.38, 0.35, 0.36], [0.5, 0.0, 0.34], [0.46, -0.35, 0.32], [0.42, -0.62, 0.36]], 3));

  // 点缀（素材包）
  const deco = async (name, parent, at, s, ry = 0, rx = 0, rz = 0) => {
    const m = await model(name); m.position.set(...at); m.scale.setScalar(s); m.rotation.set(rx, ry, rz); parent.add(m); return m;
  };
  await Promise.all([
    deco('Mushroom_Laetiporus', arms[0], [-0.32, 0.2, 0.25], 0.5, -1.2, 0, 0.5),
    deco('Mushroom_Common', arms[1], [0.2, 0.44, 0.05], 0.42, 0.5),
    deco('Grass_Common_Short', arms[1], [0.0, 0.46, -0.12], 0.3, 1.0),
    deco('Grass_Wispy_Short', arms[0], [0.05, 0.48, -0.05], 0.28, 0.3),
    deco('Grass_Common_Short', torso, [-0.05, 1.72, 0.4], 0.28, 0.2),
    deco('Fern_1', torso, [-0.45, 1.25, -0.2], 0.08, 0.6),
  ]);

  const PERIOD = 2.4;
  root.userData.update = (t) => {
    const ph = (t / PERIOD) * Math.PI * 2, b = Math.sin(ph);
    torso.position.y = 0.95 + b * 0.035;
    torso.rotation.set(b * 0.025, Math.sin(ph) * 0.03, 0);
    arms.forEach((a, i) => { a.rotation.x = Math.sin(ph + i * Math.PI) * 0.06 - b * 0.02; a.rotation.z = (i ? 1 : -1) * b * 0.03; });
    const pulse = 0.5 + 0.5 * Math.sin(ph * 2);
    root.traverse((o) => {
      if (!o.isMesh) return;
      if (o.material.name === 'GolemCrystal') o.material.emissiveIntensity = 1.1 + pulse * 1.0;
      if (/GolemStone/.test(o.material.name)) { const g = 0.55 + pulse * 0.6; o.material.userData.glowAmt = g; const sh = o.material.userData.shader; if (sh) sh.uniforms.glowAmt.value = g; }
    });
    const k = (t / PERIOD) % 1, blink = k > 0.62 && k < 0.72 ? Math.sin((k - 0.62) / 0.1 * Math.PI) : 0;
    eyes.forEach((e) => { e.scale.y = 0.7 * (1 - blink * 0.9); });
  };
  root.userData.update(0);
  return root;
}
