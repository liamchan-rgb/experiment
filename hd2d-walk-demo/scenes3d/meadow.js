/**
 * 林间营地战斗场景（HD-2D：3D 场景 + 像素人物）。模型：Quaternius「Stylized Nature MegaKit」免费版（CC0）。
 * 全部由代码摆放：地面（程序生成的草地 + 泥土小路贴图）、远中近三层树、石头、草丛花朵蘑菇、前景草；
 * 太阳光 + 软阴影 + 雾；后期：移轴景深（舞台那一带清晰，上下渐虚）、泛光、调色、暗角。
 *
 * 坐标（米）：x 向右（左边英雄、右边怪物），z 朝镜头，y 向上。Q 版人物约 1.6 米高，战斗舞台约 x ∈ [-5, 5]、z ∈ [-1.5, 2.5]；
 * 模型是真实尺寸（树 7 米），小植物按人物比例缩小。
 * 页面参数：?w=宽&h=高&t=时间（风吹草动的相位）&cam=镜头推近（0..1）&px=像素化倍数（1 = 不像素化）
 *
 * 像素风滤镜（px > 1）：整个场景按 w/px × h/px 的低分辨率渲染，截图后最近邻放大回去，每个场景像素是 px × px 的方块。
 *   px = 3（1920 宽时）= 人物像素密度的 2 倍：比人物精细，但在同一个像素网格上。
 *   描边：按深度 / 法线的跳变画深色外轮廓和内轮廓（RenderPixelatedPass）；
 *   明暗分档：亮度量化成 6 档，交界处用 4×4 Bayer 有序抖动（和人物、图标的画法一样）；
 *   限色：每个通道量化，暗部偏冷紫、亮部偏暖，饱和度略提。
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RenderPixelatedPass } from 'three/addons/postprocessing/RenderPixelatedPass.js';
import { classify, rewriteNormals, toonMaterial, ndMaterial, edgePass } from './toon.js';

const q = new URLSearchParams(location.search);
const W = +(q.get('w') ?? 1920), H = +(q.get('h') ?? 1152), T = +(q.get('t') ?? 0), CAM = +(q.get('cam') ?? 0), PX = +(q.get('px') ?? 1);
const RW = Math.round(W / PX), RH = Math.round(H / PX);
/**
 * mode：
 *   final（默认）  一次出完整画面（雾、景深、光都在页面里做；px > 1 时连雾一起像素化）
 *   albedo        只要「物体本身」：px 倍的低分辨率像素块（描边、明暗分档），关掉雾、景深、泛光、暗角
 *   depth         全分辨率深度图（RGB 打包），给外面按真实距离加雾、景深、光——这些不像素化，是平滑的
 */
const MODE = q.get('mode') ?? 'final';
/** style：hd2d（默认，写实光照 + 后期）| toon（卡通渲染：光照分 3 档、冷色阴影、按深度 / 法线突变画手绘描边，见 toon.js） */
const STYLE = q.get('style') ?? 'hd2d', TOON = STYLE === 'toon';

// 可复现的随机数
let seed = 7;
const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
const range = (a, b) => a + (b - a) * rnd();

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(MODE === 'depth' ? W : RW, MODE === 'depth' ? H : RH);
renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = TOON ? THREE.NeutralToneMapping : THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = TOON ? 1.0 : 1.15;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
// 天空：上蓝下暖的渐变；雾和天空下沿同色，远处的树自然融进去
const skyTex = (() => {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, '#5f9fd8'); gr.addColorStop(0.55, '#a9d2ea'); gr.addColorStop(1, '#f2e6c4');
  g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
})();
scene.background = skyTex;
scene.fog = new THREE.Fog('#dfe9dc', 13, 48);

// 镜头：略俯视、长焦（透视不夸张，像舞台）
const camera = new THREE.PerspectiveCamera(30, W / H, 0.3, 200);
const camPos = new THREE.Vector3(0, 4.6 - CAM * 0.8, 12.5 - CAM * 3), camLook = new THREE.Vector3(0, 0.9, 0);
camera.position.copy(camPos); camera.lookAt(camLook);

// 光：天光 + 偏暖的太阳（左后上方，影子朝右前），补一点冷色的环境光
scene.add(new THREE.HemisphereLight('#eef4ff', '#7a8a48', 1.25));
const sun = new THREE.DirectionalLight('#ffe9c2', 3.6);
sun.position.set(-14, 20, -6);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
Object.assign(sun.shadow.camera, { left: -26, right: 26, top: 22, bottom: -22, near: 1, far: 70 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04; sun.shadow.radius = 4;
scene.add(sun);

// ---------------------------------------------------------------- 地面：程序生成的草地 + 小路
function groundTexture() {
  const S = 2048, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  g.fillStyle = '#7ea03c'; g.fillRect(0, 0, S, S);
  // 大块明暗斑：草地的深浅变化
  for (let i = 0; i < 900; i++) {
    const x = rnd() * S, y = rnd() * S, r = range(20, 120);
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    const col = rnd() < 0.5 ? 'rgba(146,180,62,' : 'rgba(78,112,34,';
    gr.addColorStop(0, col + range(0.15, 0.35) + ')'); gr.addColorStop(1, col + '0)');
    g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  // 小路：从镜头前下方蜿蜒到林子深处（贴图坐标：地面 80×80，中心 = 世界原点）
  const toTex = (x, z) => [(x / 80 + 0.5) * S, (z / 80 + 0.5) * S];
  g.lineCap = 'round'; g.lineJoin = 'round';
  const path = [];
  for (let z = 30; z >= -40; z -= 0.5) path.push(toTex(Math.sin(z * 0.18) * 1.6 + z * 0.06 + 0.4, z));
  for (const [w, col] of [[70, 'rgba(150,120,70,0.35)'], [52, '#a98a58'], [38, '#b89a66']]) {
    g.strokeStyle = col; g.lineWidth = w; g.beginPath();
    path.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.stroke();
  }
  // 泥土上的细碎颗粒和草叶笔触
  for (let i = 0; i < 60000; i++) {
    const x = rnd() * S, y = rnd() * S;
    g.fillStyle = rnd() < 0.5 ? 'rgba(40,70,20,0.18)' : 'rgba(200,220,120,0.14)';
    g.fillRect(x, y, 2, range(3, 7));
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}
const groundGeo = new THREE.PlaneGeometry(80, 80, 120, 120);
// 舞台平，远处慢慢隆起成小山坡
const pos = groundGeo.attributes.position;
for (let i = 0; i < pos.count; i++) {
  const x = pos.getX(i), y = pos.getY(i); // plane 的 y = 世界 -z
  const z = -y, back = Math.max(0, -z - 8);
  pos.setZ(i, back * back * 0.012 + Math.sin(x * 0.3) * Math.min(1, back / 10) * 0.6 + (Math.abs(x) > 20 ? (Math.abs(x) - 20) * 0.15 : 0));
}
groundGeo.computeVertexNormals();
const ground = new THREE.Mesh(groundGeo, new THREE.MeshStandardMaterial({ map: groundTexture(), roughness: 1 }));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true;
scene.add(ground);
const heightAt = (x, z) => { const back = Math.max(0, -z - 8); return back * back * 0.012 + Math.sin(x * 0.3) * Math.min(1, back / 10) * 0.6 + (Math.abs(x) > 20 ? (Math.abs(x) - 20) * 0.15 : 0); };

// ---------------------------------------------------------------- 模型
const loader = new GLTFLoader().setPath('models/');
const cache = {};
async function model(name) {
  if (!cache[name]) cache[name] = loader.loadAsync(name + '.gltf').then((g) => {
    g.scene.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = true;
      // 叶片不接收阴影（低模树冠自己挡自己会一片黑），树干、石头、地面接收
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) {
        if (m.map) { m.map.colorSpace = THREE.SRGBColorSpace; }
        const foliage = /leaf|leaves|grass|flower|petal|fern|plant|clover/i.test(m.name + (m.map?.name ?? ''));
        if (foliage) { m.alphaTest = 0.45; m.side = THREE.DoubleSide; m.transparent = false; } else o.receiveShadow = true;
        // 树皮、石头贴图偏暗：提亮；红叶往橙黄偏（秋色，不要血红）
        if (/bark/i.test(m.name)) m.color.setRGB(1.9, 1.75, 1.6);
        if (/rock/i.test(m.name)) m.color.setRGB(1.55, 1.6, 1.5);
        if (/TwistedTree/i.test(m.name) && foliage) { if (TOON) m.color.setRGB(1.25, 1.5, 0.5); else m.color.setRGB(1.5, 1.25, 0.55); }
        m.roughness = 0.9; m.metalness = 0;
      }
    });
    return g.scene;
  });
  const sc = await cache[name];
  if (TOON && !sc.userData.toon) {
    sc.userData.toon = true;
    sc.traverse((o) => {
      if (!o.isMesh) return;
      const m = Array.isArray(o.material) ? o.material[0] : o.material;
      m.userData.kind = classify(name, m);
      if (/TwistedTree/i.test(m.name) && m.userData.kind !== 'solid') m.userData.recolor = /Bush/.test(name) ? '#4f8a2c' : '#e8a03a';
      rewriteNormals(o, m.userData.kind);
      // 草花朝上的法线 → 接收投影后和地面上的影子连成一片
      if (m.userData.kind === 'grass') o.receiveShadow = true;
    });
  }
  return sc.clone(true);
}
const placed = [];
async function put(name, x, z, s = 1, rot = rnd() * Math.PI * 2, opts = {}) {
  const m = await model(name);
  m.position.set(x, heightAt(x, z) + (opts.dy ?? 0), z);
  m.rotation.y = rot;
  m.scale.setScalar(s);
  if (opts.tint) m.traverse((o) => { if (o.isMesh) { o.material = o.material.clone(); o.material.color = new THREE.Color(opts.tint); } });
  if (opts.sway) placed.push(m);
  scene.add(m);
  return m;
}
const pick = (arr) => arr[Math.floor(rnd() * arr.length)];
const pathX = (z) => Math.sin(z * 0.18) * 1.6 + z * 0.06 + 0.4;
const onPath = (x, z) => Math.abs(x - pathX(z)) < 1.1;
/** 舞台中间要留空：人物和怪物站的地方不放高的东西 */
const inStage = (x, z) => Math.abs(x) < 5.6 && z > -2.2 && z < 3.2;

const trees = ['CommonTree_1', 'CommonTree_2', 'CommonTree_3', 'CommonTree_4', 'CommonTree_5'];
const twisted = ['TwistedTree_1', 'TwistedTree_2', 'TwistedTree_3', 'TwistedTree_4', 'TwistedTree_5'];
const pines = ['Pine_1', 'Pine_2', 'Pine_3', 'Pine_4', 'Pine_5'];
const grass = ['Grass_Common_Short', 'Grass_Common_Tall', 'Grass_Wispy_Short', 'Grass_Wispy_Tall'];
const flowers = ['Flower_3_Group', 'Flower_4_Group', 'Flower_3_Single', 'Flower_4_Single', 'Bush_Common_Flowers'];
const pebbles = ['Pebble_Round_1', 'Pebble_Round_2', 'Pebble_Round_3', 'Pebble_Square_1', 'Pebble_Square_2', 'Pebble_Square_4'];

const jobs = [];
const P = (name, x, z, s, rot, opts) => jobs.push(put(name, x, z, s, rot, opts));
// 远景：林墙（越远越密，雾把它们推远）
for (let i = 0; i < 90; i++) { const x = range(-34, 34), z = range(-40, -12); P(rnd() < 0.45 ? pick(pines) : pick([...trees, ...trees, ...twisted]), x, z, range(1.0, 1.6)); }
// 中景：后排几棵树和一组石头，左右各一棵大树框住画面
for (let i = 0; i < 14; i++) { const x = range(-14, 14), z = range(-11, -5.5); if (onPath(x, z)) continue; P(pick([...trees, ...twisted, ...pines]), x, z, range(0.75, 1.1)); }
P('TwistedTree_2', -9.6, -2.6, 0.62, 0.9);
P('CommonTree_3', 10.2, -2.8, 1.05, 2.0);
P('CommonTree_5', 12.5, 1.5, 0.95);
P('Rock_Medium_2', 4.2, -4.4, 0.95, 0.4); P('Rock_Medium_3', 5.6, -4.0, 0.55); P('Rock_Medium_1', -5.2, -4.6, 0.8, 2.2);
P('Rock_Medium_3', -8.6, 2.6, 0.6); P('Rock_Medium_1', 8.8, 4.2, 0.5);
// 小路石板
for (let z = 9; z > -12; z -= 0.75) P(pick(['RockPath_Round_Small_1', 'RockPath_Round_Small_2', 'RockPath_Square_Small_1', 'RockPath_Square_Small_2', 'RockPath_Round_Thin']), pathX(z) + range(-0.4, 0.4), z, range(0.35, 0.5));
// 灌木、蕨类：舞台外围
for (let i = 0; i < 46; i++) { const x = range(-13, 13), z = range(-6, 6.5); if (inStage(x, z) || onPath(x, z)) continue; P(pick(['Bush_Common', 'Bush_Common_Flowers', 'Bush_Common', 'Plant_1_Big', 'Plant_7_Big']), x, z, range(0.45, 0.8)); }
for (let i = 0; i < 10; i++) { const x = range(-13, 13), z = range(-6, 6); if (inStage(x, z) || onPath(x, z)) continue; P('Fern_1', x, z, range(0.14, 0.2)); }
// 草：舞台上稀疏（不挡人），外围茂密
for (let i = 0; i < 1500; i++) { const x = range(-15, 15), z = range(-7, 7); if (onPath(x, z)) continue; if (inStage(x, z) && rnd() < 0.85) continue; P(pick(grass), x, z, range(0.28, 0.45), undefined, { sway: true }); }
// 花、蘑菇、小石子
for (let i = 0; i < 260; i++) {
  const x = range(-14, 14), z = range(-6, 6.5);
  if (onPath(x, z)) { if (rnd() < 0.4) P(pick(pebbles), x, z, range(0.4, 0.7)); continue; }
  if (inStage(x, z) && rnd() < 0.7) continue;
  const r = rnd();
  P(r < 0.72 ? pick(flowers) : r < 0.86 ? pick(['Mushroom_Common', 'Mushroom_Laetiporus']) : pick(pebbles), x, z, r < 0.72 ? range(0.3, 0.45) : range(0.5, 0.8));
}
// 前景：镜头最前面一排高草和蕨（会被景深虚化，左右多、中间少）
for (let i = 0; i < 90; i++) { const x = range(-7, 7), z = range(4.6, 6.4); if (Math.abs(x) < 2.6 && rnd() < 0.75) continue; P(pick(['Grass_Common_Tall', 'Grass_Wispy_Tall', 'Plant_7_Big', 'Flower_3_Group']), x, z, range(0.45, 0.7), undefined, { sway: true }); }

await Promise.all(jobs);
let tND = null;
if (TOON) {
  // 材质换成卡通材质（同一个源材质只换一次）；另备一套「法线 + 深度」材质给描边用
  const sunLum = (0.299 * sun.color.r + 0.587 * sun.color.g + 0.114 * sun.color.b) * sun.intensity;
  const opt = { sunLum, ambientTint: new THREE.Color('#b4c2e6').multiplyScalar(2.5), bands: [0.16, 0.5], mid: 0.5 };
  const toonCache = new Map(), ndCache = new Map(), meshes = [];
  scene.traverse((o) => {
    if (!o.isMesh) return;
    const src = Array.isArray(o.material) ? o.material[0] : o.material;
    const kind = src.userData.kind ?? 'solid';
    if (!toonCache.has(src)) { toonCache.set(src, toonMaterial(src, kind, opt)); ndCache.set(src, ndMaterial(src, kind, camera.far)); }
    o.material = toonCache.get(src); o.userData.nd = ndCache.get(src); meshes.push(o);
  });
  for (const m of placed) { const k = m.position.x * 0.4 + m.position.z * 0.3; m.rotation.z = Math.sin(T * 2.2 + k) * 0.06; }
  tND = new THREE.WebGLRenderTarget(W, H, { type: THREE.FloatType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
  const keep = meshes.map((o) => o.material), bg = scene.background, fog = scene.fog;
  meshes.forEach((o) => { o.material = o.userData.nd; });
  scene.background = null; scene.fog = null;
  renderer.setRenderTarget(tND); renderer.setClearColor(new THREE.Color(0.5, 0.5, 1), 1); renderer.clear(); renderer.render(scene, camera);
  renderer.setRenderTarget(null); renderer.setClearColor(0x000000, 0);
  meshes.forEach((o, i) => { o.material = keep[i]; });
  scene.background = bg; scene.fog = fog;
}
if (MODE !== 'final') scene.fog = null;
// 风：草和前景植物轻轻摆（按 t 参数，逐帧渲染时可以出动画）
for (const m of placed) { const k = m.position.x * 0.4 + m.position.z * 0.3; m.rotation.z = Math.sin(T * 2.2 + k) * 0.06; }

// ---------------------------------------------------------------- 后期
if (MODE === 'depth') {
  // 每个网格换成深度材质（保留叶片的镂空），全分辨率渲染，RGB 打包深度
  scene.background = new THREE.Color(0xffffff);
  scene.traverse((o) => {
    if (!o.isMesh) return;
    const src = Array.isArray(o.material) ? o.material[0] : o.material;
    o.material = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBDepthPacking, map: src.map ?? null, alphaTest: src.alphaTest ?? 0, side: src.side });
  });
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  renderer.render(scene, camera);
}
const composer = new EffectComposer(renderer);
composer.setSize(RW, RH);
if (TOON) {
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(edgePass(tND.texture, W, H, camera.far));
} else if (PX > 1) {
  const pix = new RenderPixelatedPass(1, scene, camera, { normalEdgeStrength: 0.7, depthEdgeStrength: 2.2 });
  composer.addPass(pix);
} else composer.addPass(new RenderPass(scene, camera));
if (MODE === 'final') composer.addPass(new UnrealBloomPass(new THREE.Vector2(RW, RH), TOON ? 0.15 : 0.32, 0.55, TOON ? 0.9 : 0.82));
// 移轴景深：屏幕上 focus 那一横带清晰（战斗舞台），往上、往下越来越虚（两遍可分离模糊）
const tilt = (dir) => new ShaderPass({
  uniforms: { tDiffuse: { value: null }, dir: { value: dir }, focus: { value: 0.6 }, band: { value: 0.16 }, amount: { value: 4.0 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; uniform vec2 dir; uniform float focus, band, amount; varying vec2 vUv;
    void main(){
      float d = max(0.0, abs(vUv.y - focus) - band);
      // 下方（离镜头近的前景草）虚得更厉害
      float k = clamp(d * (vUv.y < focus ? 3.4 : 2.0), 0.0, 1.0) * amount;
      vec4 sum = vec4(0.0); float wsum = 0.0;
      for (int i = -6; i <= 6; i++) { float w = exp(-float(i*i) / 18.0); sum += texture2D(tDiffuse, vUv + dir * float(i) * k) * w; wsum += w; }
      gl_FragColor = sum / wsum;
    }`,
});
const tiltX = tilt(new THREE.Vector2(1 / RW, 0)), tiltY = tilt(new THREE.Vector2(0, 1 / RH));
// 低分辨率时每个像素更大，模糊步长相应缩小，虚化的范围不变
// 像素模式下几乎不虚化（像素画靠雾和明暗分远近，糊掉的像素会显得脏）
for (const t of [tiltX, tiltY]) t.uniforms.amount.value = PX > 1 ? 0.55 : 4.0;
if (MODE === 'final' && !TOON) { composer.addPass(tiltX); composer.addPass(tiltY); }
// 调色 + 暗角：暗部偏冷、亮部偏暖，四周压暗，舞台中间最亮
if (MODE === 'final') composer.addPass(new ShaderPass({
  uniforms: { tDiffuse: { value: null } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; varying vec2 vUv;
    void main(){
      vec3 c = texture2D(tDiffuse, vUv).rgb;
      float l = dot(c, vec3(0.299,0.587,0.114));
      c = mix(c, c * vec3(0.86,0.95,1.10), (1.0 - l) * 0.45);
      c = mix(c, c * vec3(1.08,1.02,0.90), l * 0.35);
      c = mix(vec3(l), c, 1.12);
      vec2 p = (vUv - vec2(0.5, 0.45)) * vec2(1.0, 1.3);
      c *= 1.0 - smoothstep(0.42, 0.95, length(p)) * 0.55;
      gl_FragColor = vec4(c, 1.0);
    }`,
}));
composer.addPass(new OutputPass());
if (PX > 1) composer.addPass(new ShaderPass({
  // 像素画的明暗分档 + 有序抖动 + 限色（在显示色彩空间里做，OutputPass 之后）
  uniforms: { tDiffuse: { value: null }, res: { value: new THREE.Vector2(RW, RH) } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; uniform vec2 res; varying vec2 vUv;
    float bayer(vec2 p){
      int x = int(mod(p.x, 4.0)), y = int(mod(p.y, 4.0)), i = x + y * 4;
      int m[16] = int[16](0,8,2,10,12,4,14,6,3,11,1,9,15,7,13,5);
      return (float(m[i]) + 0.5) / 16.0 - 0.5;
    }
    void main(){
      vec3 c = texture2D(tDiffuse, vUv).rgb;
      float d = bayer(floor(vUv * res));
      float L = dot(c, vec3(0.299, 0.587, 0.114));
      // 明暗量化成 6 档，交界抖动
      float Lq = floor(L * 6.0 + 0.5 + d * 0.22) / 6.0;
      c *= clamp(Lq / max(L, 0.03), 0.35, 1.8);
      // 暗部偏冷紫、亮部偏暖（像素画常用的色相偏移）
      c = mix(c, c * vec3(0.82, 0.86, 1.18), clamp(0.55 - Lq, 0.0, 0.55) * 0.6);
      c = mix(c, c * vec3(1.08, 1.03, 0.88), clamp(Lq - 0.6, 0.0, 0.4) * 0.6);
      float g = dot(c, vec3(0.333)); c = mix(vec3(g), c, 1.15);
      // 最终限色（约 48 色）在截图后做：按整张图挑一套调色板，每块表面落成几块干净的色块
      gl_FragColor = vec4(c, 1.0);
    }`,
}));
if (MODE !== 'depth') composer.render();

// 告诉外面：舞台上几个站位在屏幕上的像素位置（合成像素人物时用）
const proj = (x, z) => { const v = new THREE.Vector3(x, heightAt(x, z), z).project(camera); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; };
window.stage = { p1: proj(-3.6, 0.6), p2: proj(-2.2, 2.0), p4: proj(-2.4, -0.8), m1: proj(2.6, 0.2), m2: proj(4.0, 1.9), m3: proj(2.0, 2.4), unit: Math.abs(proj(1, 1)[0] - proj(0, 1)[0]) };
window.camInfo = { near: camera.near, far: camera.far };
window.done = true;
