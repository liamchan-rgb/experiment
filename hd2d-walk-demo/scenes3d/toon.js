/**
 * 卡通渲染（cel shading）：
 *   1. 光照分档：太阳光（含投影）按「受光程度 = N·L × 阴影」量化成 3 档（亮 / 半调 / 暗），交界是干净的硬边；
 *      环境光（天光）偏冷蓝，所以照不到太阳的暗档和投影自然是冷色，亮档是暖色。
 *   2. 树冠、草的法线重写：树冠用「从树冠中心往外」的球形法线（整团叶子像一个色块，不会碎成斑点），
 *      草和花用朝上的法线（整片草地明暗一致）。
 *   3. 描边：另渲染一张「法线 + 深度 + 描边权重」图，后期按深度跳变（外轮廓）和法线突变（内折线）找边，
 *      再加手绘感：线条位置轻微抖动、粗细按「笔压」噪声和远近变化、偶尔断笔、线色取底色压暗偏冷（彩色墨线，不是纯黑）。
 */
import * as THREE from 'three';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

/** 按模型名给材质分类：canopy 树冠/灌木叶，grass 草花蕨，solid 其他（树干、石头、蘑菇、地面） */
export function classify(modelName, mat) {
  const foliage = /leaf|leaves|grass|flower|petal|fern|plant|clover/i.test(mat.name + (mat.map?.name ?? ''));
  if (!foliage) return 'solid';
  return /Tree|Pine|Bush/i.test(modelName) ? 'canopy' : 'grass';
}

/** 重写法线（每个几何体只做一次；模型 clone 共享几何体） */
export function rewriteNormals(mesh, kind) {
  const g = mesh.geometry;
  if (g.userData.toonNormals || kind === 'solid') return;
  g.userData.toonNormals = true;
  const p = g.attributes.position, n = g.attributes.normal;
  if (!n) return;
  g.computeBoundingBox();
  const c = new THREE.Vector3(), half = new THREE.Vector3();
  g.boundingBox.getCenter(c); g.boundingBox.getSize(half).multiplyScalar(0.5).max(new THREE.Vector3(1e-3, 1e-3, 1e-3));
  const v = new THREE.Vector3(), o = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    o.set(n.getX(i), n.getY(i), n.getZ(i));
    if (kind === 'canopy') {
      // 椭球法线：(p - c) / half²，往上偏一点让树冠顶部吃光
      v.set(p.getX(i) - c.x, p.getY(i) - c.y, p.getZ(i) - c.z).divide(half).divide(half).normalize();
      v.y += 0.25; v.normalize();
      v.lerp(o, 0.12).normalize();
    } else {
      v.set(0, 1, 0).lerp(o, 0.2).normalize();
    }
    n.setXYZ(i, v.x, v.y, v.z);
  }
  n.needsUpdate = true;
}

/** 卡通材质：MeshToonMaterial + 改写光照函数 */
export function toonMaterial(src, kind, opt) {
  const m = new THREE.MeshToonMaterial({
    color: src.color?.clone() ?? new THREE.Color(1, 1, 1), map: src.map ?? null,
    alphaTest: src.alphaTest ?? 0, side: src.side ?? THREE.FrontSide, transparent: false,
    vertexColors: !!src.vertexColors, emissive: src.emissive?.clone() ?? new THREE.Color(0), emissiveIntensity: src.emissiveIntensity ?? 1, name: src.name,
    normalMap: src.normalMap ?? null, normalScale: src.normalScale?.clone() ?? new THREE.Vector2(1, 1), emissiveMap: src.emissiveMap ?? null,
  });
  m.userData.kind = kind;
  m.onBeforeCompile = (sh) => {
    sh.uniforms.sunLum = { value: opt.sunLum };
    sh.uniforms.coolAmb = { value: new THREE.Color(opt.ambientTint) };
    sh.uniforms.bands = { value: new THREE.Vector3(...opt.bands) };
    sh.uniforms.mid = { value: opt.mid };
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <lights_toon_pars_fragment>', /* glsl */`
        varying vec3 vViewPosition;
        uniform float sunLum, mid; uniform vec3 coolAmb, bands;
        struct ToonMaterial { vec3 diffuseColor; };
        void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
          // 受光程度 = N·L × 阴影（directLight.color 已经乘过阴影），量化成 暗 / 半调 / 亮 三档
          float shadow = dot(directLight.color, vec3(0.299, 0.587, 0.114)) / sunLum;
          float lit = clamp(dot(geometryNormal, directLight.direction), 0.0, 1.0) * shadow;
          float fw = fwidth(lit) * 0.7 + 1e-4;
          float band = mix(0.0, mid, smoothstep(bands.x - fw, bands.x + fw, lit));
          band = mix(band, 1.0, smoothstep(bands.y - fw, bands.y + fw, lit));
          vec3 sunCol = directLight.color / max(shadow, 1e-4);
          reflectedLight.directDiffuse += band * sunCol * BRDF_Lambert( material.diffuseColor );
        }
        void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
          // 环境光不随法线变（不然暗部又有渐变），统一成偏冷的天光色
          reflectedLight.indirectDiffuse += coolAmb * BRDF_Lambert( material.diffuseColor );
        }
        #define RE_Direct RE_Direct_Toon
        #define RE_IndirectDiffuse RE_IndirectDiffuse_Toon
      `);
    // 贴图「压平」：树皮、石头、地面的手绘细节和高频噪点会和分档光照打架，
    // 混一部分低精度 mip（相当于取局部平均色），表面变成更干净的色块，大的花纹还在
    if (kind === 'solid' && src.map) {
      sh.uniforms.flatAmt = { value: opt.flatten ?? 0.72 };
      sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>', /* glsl */`
        #ifdef USE_MAP
          vec4 sampledDiffuseColor = texture2D( map, vMapUv );
          sampledDiffuseColor.rgb = mix( sampledDiffuseColor.rgb, texture2D( map, vMapUv, 4.5 ).rgb, flatAmt );
          diffuseColor *= sampledDiffuseColor;
        #endif
      `).replace('uniform float sunLum, mid;', 'uniform float sunLum, mid, flatAmt;');
    }
    // 换色：素材包自带的深红叶子（TwistedTree / 灌木）太刺眼——取贴图红通道当明暗花纹，填上新颜色
    if (src.userData.recolor && src.map) {
      sh.uniforms.recolor = { value: new THREE.Color(src.userData.recolor) };
      sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>', /* glsl */`
        #ifdef USE_MAP
          vec4 sampledDiffuseColor = texture2D( map, vMapUv );
          sampledDiffuseColor.rgb = recolor * clamp(sampledDiffuseColor.r / 0.40, 0.0, 1.6);
          diffuseColor *= sampledDiffuseColor;
        #endif
      `).replace('uniform float sunLum, mid;', 'uniform float sunLum, mid; uniform vec3 recolor;');
    }
    // 叶片是双面卡片：背面不翻法线（用重写过的球形法线，整团叶子明暗连续）
    if (kind !== 'solid') sh.fragmentShader = sh.fragmentShader.replace('#include <normal_fragment_begin>',
      THREE.ShaderChunk.normal_fragment_begin.replace('normal *= faceDirection;', ''));    // 额外的着色补丁（例如魔像石头的程序化手绘表面）
    if (src.userData.toonPatch) src.userData.toonPatch(sh, m);
  };
  if (src.userData.recolor) m.color.setRGB(1, 1, 1);
  m.customProgramCacheKey = () => 'toon-' + kind + (src.map ? '-map' : '') + (src.userData.recolor ? '-re' : '') + (src.vertexColors ? '-vc' : '') + (src.userData.toonPatch ? '-patch-' + src.name : '') + (src.normalMap ? '-nm' : '') + (src.emissiveMap ? '-em' : '');
  return m;
}

/** 法线 + 深度 + 描边权重（rg = 视空间法线 xy，b = 描边权重，a = 线性深度 / far） */
export function ndMaterial(src, kind, far) {
  const weight = { solid: 1.0, canopy: 0.8, grass: 0.35 }[kind] ?? 1;
  return new THREE.ShaderMaterial({
    uniforms: { map: { value: src.map ?? null }, useMap: { value: src.map ? 1 : 0 }, alphaTest: { value: src.alphaTest ?? 0 }, weight: { value: weight }, far: { value: far }, flip: { value: kind === 'solid' ? 1 : 0 } },
    side: src.side ?? THREE.FrontSide,
    vertexShader: /* glsl */`
      varying vec2 vUv; varying vec3 vN; varying float vZ;
      void main(){ vUv = uv; vec4 mv = modelViewMatrix * vec4(position, 1.0); vZ = -mv.z; vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: /* glsl */`
      uniform sampler2D map; uniform float useMap, alphaTest, weight, far, flip;
      varying vec2 vUv; varying vec3 vN; varying float vZ;
      void main(){
        if (useMap > 0.5 && texture2D(map, vUv).a < alphaTest) discard;
        vec3 n = normalize(vN); if (flip > 0.5 && !gl_FrontFacing) n = -n;
        gl_FragColor = vec4(n.xy * 0.5 + 0.5, weight, vZ / far);
      }`,
  });
}

/** 描边后期 */
export function edgePass(tND, W, H, far, o = {}) {
  const pass = new ShaderPass({
    uniforms: {
      tDiffuse: { value: null }, tND: { value: tND }, res: { value: new THREE.Vector2(W, H) }, far: { value: far },
      width: { value: o.width ?? 1.35 }, ink: { value: new THREE.Color(o.ink ?? '#4a3f66') },
    },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: /* glsl */`
      uniform sampler2D tDiffuse, tND; uniform vec2 res; uniform float far, width; uniform vec3 ink; varying vec2 vUv;
      float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float noise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i), hash(i + vec2(1,0)), f.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x), f.y); }
      vec3 nrm(vec4 s){ vec2 xy = s.rg * 2.0 - 1.0; return vec3(xy, sqrt(max(0.0, 1.0 - dot(xy, xy)))); }
      void main(){
        vec2 px = 1.0 / res, P = vUv * res;
        // 手抖：采样位置跟着低频噪声轻轻漂，线条不是死贴着几何边
        vec2 wob = vec2(noise(P / 34.0), noise(P / 34.0 + 17.3)) - 0.5;
        vec2 uv = vUv + wob * px * 3.4;
        vec4 c0 = texture2D(tND, uv);
        float d0 = c0.a * far;
        // 笔压：粗细按噪声起伏；近处的线粗、远处细
        float press = 0.55 + 0.9 * noise(P / 70.0 + 5.0);
        float r = mix(2.3, 0.9, smoothstep(9.0, 32.0, d0)) * press * width;
        float de = 0.0, ne = 0.0;
        vec3 n0 = nrm(c0);
        for (int i = 0; i < 8; i++) {
          float a = float(i) * 0.785398;
          vec4 c = texture2D(tND, uv + vec2(cos(a), sin(a)) * px * r);
          // 外轮廓只画在靠前的物体这一侧（邻居更远时）
          de = max(de, (c.a - c0.a) / max(c0.a, 1e-4));
          ne = max(ne, (1.0 - dot(n0, nrm(c))) * min(c.b, c0.b));
        }
        float w = c0.b;
        float eD = smoothstep(0.035, 0.08, de) * mix(0.45, 1.0, w);
        float eN = smoothstep(0.22, 0.5, ne);
        float e = max(eD, eN);
        // 远处线变淡（雾里不该有很黑的线），偶尔断笔
        e *= 1.0 - smoothstep(14.0, 46.0, d0) * 0.8;
        e *= 0.55 + 0.45 * smoothstep(0.2, 0.45, noise(P / 11.0 + 31.0));
        vec3 col = texture2D(tDiffuse, vUv).rgb;
        // 线色：底色压暗再往墨色（冷紫）靠——彩色墨线
        vec3 line = mix(col * 0.32, ink * 0.25, 0.45);
        col = mix(col, line, clamp(e, 0.0, 1.0));
        // 整体饱和度收一点（高饱和的花草最明显）
        float L = dot(col, vec3(0.2126, 0.7152, 0.0722));
        gl_FragColor = vec4(mix(vec3(L), col, 0.86), 1.0);
      }`,
  });
  // ShaderPass 会克隆 uniforms（贴图被克隆后和渲染目标断开），这里重新指回去
  pass.uniforms.tND.value = tND;
  return pass;
}
