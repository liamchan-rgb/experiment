import { Palette, paletteRGB, shadeCode, OUTLINE, SOFT_OUTLINE, DARK, HI, SUB } from './palette';

/**
 * 索引色像素图层。
 * 每个像素存「调色板编号 + 明暗阶」，而不是 RGB —— 形状与颜色彻底分离。
 * 所有绘制原语都按整数像素落点，不做抗锯齿。
 */
export class PixelLayer {
  /** 0 = 空；否则 = shade × SUB + 1（支持 1/SUB 阶） */
  readonly idx: Uint8Array;
  /** 该像素使用的调色板在 palettes 中的下标 */
  readonly pid: Uint8Array;
  readonly palettes: Palette[] = [];
  private cur = 0;
  /**
   * 写过像素的包围盒（含边界；空图层时 x1 < x0）。描边、投影、合成这些逐像素的步骤只扫这个范围：
   * 一个部件通常只占画布的一小块，结果和扫整张完全一样，只是快得多（游戏里用无 JIT 的 JavaScriptCore 跑）。
   */
  x0 = 0;
  y0 = 0;
  x1 = -1;
  y1 = -1;

  constructor(readonly w: number, readonly h: number) {
    this.idx = new Uint8Array(w * h);
    this.pid = new Uint8Array(w * h);
  }

  clear(): this {
    this.idx.fill(0);
    this.palettes.length = 0;
    this.cur = 0;
    this.x0 = this.y0 = 0;
    this.x1 = this.y1 = -1;
    return this;
  }

  /** 把 (x, y) 并进包围盒 */
  touch(x: number, y: number): void {
    if (this.x1 < this.x0) {
      this.x0 = this.x1 = x;
      this.y0 = this.y1 = y;
      return;
    }
    if (x < this.x0) this.x0 = x; else if (x > this.x1) this.x1 = x;
    if (y < this.y0) this.y0 = y; else if (y > this.y1) this.y1 = y;
  }

  /** 选择后续绘制使用的调色板。 */
  use(p: Palette): this {
    let i = this.palettes.indexOf(p);
    if (i < 0) {
      this.palettes.push(p);
      i = this.palettes.length - 1;
    }
    this.cur = i;
    return this;
  }

  /** 画一个像素；shade < 0 表示擦除。 */
  px(x: number, y: number, shade: number): void {
    x = Math.round(x);
    y = Math.round(y);
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
    const i = y * this.w + x;
    if (shade < 0) {
      this.idx[i] = 0;
      return;
    }
    this.idx[i] = shadeCode(shade);
    this.pid[i] = this.cur;
    this.touch(x, y);
  }

  /** 把已有像素调亮 / 调暗 delta 阶（保持调色板不变，限制在 暗部..高光 之间）。 */
  reshade(x: number, y: number, delta: number): void {
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
    const i = y * this.w + x;
    if (!this.idx[i]) return;
    const v = (this.idx[i] - 1) / SUB;
    if (v < DARK || v > HI) return;
    this.idx[i] = shadeCode(Math.max(DARK, Math.min(HI, v + delta)));
  }

  /** 读取明暗阶，空像素返回 -1。 */
  get(x: number, y: number): number {
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return -1;
    const v = this.idx[y * this.w + x];
    return v ? (v - 1) / SUB : -1;
  }

  rect(x: number, y: number, w: number, h: number, shade: number): void {
    x = Math.round(x);
    y = Math.round(y);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) this.px(x + i, y + j, shade);
  }

  hline(x0: number, x1: number, y: number, shade: number): void {
    x0 = Math.round(x0);
    x1 = Math.round(x1);
    for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++) this.px(x, y, shade);
  }

  /** Bresenham 直线。 */
  line(x0: number, y0: number, x1: number, y1: number, shade: number): void {
    x0 = Math.round(x0); y0 = Math.round(y0);
    x1 = Math.round(x1); y1 = Math.round(y1);
    const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx + dy;
    for (;;) {
      this.px(x0, y0, shade);
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 >= dy) { err += dy; x0 += sx; }
      if (e2 <= dx) { err += dx; y0 += sy; }
    }
  }

  /** 对矩形范围内每个像素调用 fn，返回 shade（<0 跳过）。用于程序化形状 + 明暗。 */
  fill(x0: number, y0: number, x1: number, y1: number, fn: (x: number, y: number) => number): void {
    for (let y = Math.round(y0); y <= Math.round(y1); y++) {
      for (let x = Math.round(x0); x <= Math.round(x1); x++) {
        const s = fn(x, y);
        if (s >= 0) this.px(x, y, s);
      }
    }
  }

  ellipse(cx: number, cy: number, rx: number, ry: number, shade: number): void {
    this.fill(cx - rx - 1, cy - ry - 1, cx + rx + 1, cy + ry + 1, (x, y) => {
      const dx = (x - cx) / rx, dy = (y - cy) / ry;
      return dx * dx + dy * dy <= 1 ? shade : -1;
    });
  }

  /**
   * 贴一个像素矩阵。每行一个字符串：'.' 或空格为空，'0'-'4' 为明暗阶。
   * (x, y) 是矩阵左上角。
   */
  stamp(rows: string[], x: number, y: number): void {
    x = Math.round(x);
    y = Math.round(y);
    rows.forEach((row, j) => {
      for (let i = 0; i < row.length; i++) {
        const ch = row.charCodeAt(i) - 48;
        if (ch >= 0 && ch <= 4) this.px(x + i, y + j, ch);
      }
    });
  }

  /**
   * 自动 1px 外描边：与已有像素四邻接的空像素填成该邻居调色板的描边色。
   * 光源在左上，所以形状左缘 / 上缘的描边用浅一档的颜色（selective outline），
   * 右缘 / 下缘用深描边，线条不会一圈一样重。
   */
  outline(): void {
    const { w, h, idx, pid } = this;
    if (this.x1 < this.x0) return;
    const src = idx.slice();
    const X0 = Math.max(0, this.x0 - 1), X1 = Math.min(w - 1, this.x1 + 1);
    const Y0 = Math.max(0, this.y0 - 1), Y1 = Math.min(h - 1, this.y1 + 1);
    for (let y = Y0; y <= Y1; y++) {
      for (let x = X0; x <= X1; x++) {
        const i = y * w + x;
        if (src[i]) continue;
        const left = x > 0 && src[i - 1] > 0;
        const up = y > 0 && src[i - w] > 0;
        const right = x < w - 1 && src[i + 1] > 0;
        const down = y < h - 1 && src[i + w] > 0;
        if (!left && !up && !right && !down) continue;
        // 只挨着右边 / 下边的形状 → 这个描边像素在形状的受光侧
        // 两侧都有像素、上方空着的凹口（发尖之间的缝）也按受光处理，不然会在头顶留下一个个黑点
        const lit = !up && (!left || right);
        idx[i] = shadeCode(lit ? SOFT_OUTLINE : OUTLINE);
        pid[i] = pid[left ? i - 1 : up ? i - w : right ? i + 1 : i + w];
      }
    }
    this.x0 = X0; this.x1 = X1; this.y0 = Y0; this.y1 = Y1;
  }

  /**
   * 补洞：被三面包围、或被左右 / 上下夹住的空像素，用相邻像素的调色板按暗部色补上（做两遍）。
   * 发束之间常会漏出一两个空像素，不补的话描边会把它们包成一个个黑点。
   */
  closeHoles(shade = DARK, passes = 2): void {
    const { w, h, idx, pid } = this;
    // 补上的像素一定在两侧都有像素的位置，所以不会超出包围盒
    const X0 = Math.max(1, this.x0), X1 = Math.min(w - 2, this.x1);
    const Y0 = Math.max(1, this.y0), Y1 = Math.min(h - 2, this.y1);
    for (let pass = 0; pass < passes; pass++) {
      const src = idx.slice();
      for (let y = Y0; y <= Y1; y++) {
        for (let x = X0; x <= X1; x++) {
          const i = y * w + x;
          if (src[i]) continue;
          const l = src[i - 1], r = src[i + 1], u = src[i - w], d = src[i + w];
          const count = (l ? 1 : 0) + (r ? 1 : 0) + (u ? 1 : 0) + (d ? 1 : 0);
          // 三面包围，或者左右 / 上下两面夹住的细缝
          if (count < 3 && !(l && r) && !(u && d)) continue;
          idx[i] = shadeCode(shade);
          pid[i] = pid[l ? i - 1 : r ? i + 1 : u ? i - w : i + w];
        }
      }
    }
  }

  /**
   * 清理内部描边：四邻都不空、且至少两邻是本体像素的描边像素，说明它已经不在轮廓上了
   * （比如前后两层发束的描边叠在一起），改成 shade 阶。只处理调色板在 only 里的像素，
   * 不会动到五官里刻意画的深色。
   */
  fillInteriorOutlines(shade: number, only: Palette[]): void {
    const { w, h, idx, pid, palettes } = this;
    const OUT = shadeCode(OUTLINE), SOFT = shadeCode(SOFT_OUTLINE);
    const body = (v: number) => v > 0 && v !== OUT && v !== SOFT;
    const src = idx.slice();
    for (let y = 1; y < h - 1; y++) {
      for (let x = 1; x < w - 1; x++) {
        const i = y * w + x;
        if ((src[i] !== OUT && src[i] !== SOFT) || !only.includes(palettes[pid[i]])) continue;
        const n = [src[i - 1], src[i + 1], src[i - w], src[i + w]];
        // 四邻都不空（不挨着外面），且至少两邻是本体：双层描边里靠内的那一圈也算
        if (n.every((v) => v > 0) && n.filter(body).length >= 2) {
          idx[i] = shadeCode(src[i] === OUT ? shade : shade + 0.5);
        }
      }
    }
  }

  /**
   * 背光侧反光：贴着右缘 / 下缘轮廓的暗部像素提亮一点（来自地面和环境的反射光）。
   * 形体的明暗就成了 亮 → 暗 → 更暗 → 微亮，比一路暗到描边更有体积。
   * 在描边之前调用。
   */
  bounce(amount = 0.5, lo = 0.6, hi = 1.9): void {
    const { w, h, idx } = this;
    const src = idx.slice();
    for (let y = Math.max(0, this.y0); y <= this.y1; y++) {
      for (let x = Math.max(0, this.x0); x <= this.x1; x++) {
        const i = y * w + x;
        if (!src[i]) continue;
        const edge = (x === w - 1 || !src[i + 1]) || (y === h - 1 || !src[i + w]);
        if (!edge) continue;
        const v = (src[i] - 1) / SUB;
        if (v < lo || v > hi) continue;
        idx[i] = shadeCode(Math.min(hi, v + amount));
      }
    }
  }

  /**
   * 接触阴影：src（刚画好的上层部件）在本层（已合成的下层）投下一道柔和的阴影。
   * 光源在左上，所以阴影落在部件的右下方，离得越远越淡。
   * 只压暗本层原有、且没被 src 盖住的像素；描边色不再变暗。
   */
  castShadow(src: PixelLayer, taps: [number, number, number][]): void {
    const { w, h } = this;
    if (src.x1 < src.x0) return;
    if (!this.dark || this.dark.length !== w * h) this.dark = new Float32Array(w * h);
    const dark = this.dark;
    // 只看 src 的包围盒；阴影最远投到右下 reach 个像素
    let reach = 0;
    for (const [dx, dy] of taps) reach = Math.max(reach, dx, dy);
    const RX1 = Math.min(w - 1, src.x1 + reach), RY1 = Math.min(h - 1, src.y1 + reach);
    for (let y = src.y0; y <= RY1; y++) dark.fill(0, y * w + src.x0, y * w + RX1 + 1);
    for (let y = src.y0; y <= src.y1; y++) {
      for (let x = src.x0; x <= src.x1; x++) {
        const v = src.idx[y * w + x];
        // 描边像素不投影：只算部件本体，阴影边缘才不会多出一圈
        if (!v || v === shadeCode(OUTLINE) || v === shadeCode(SOFT_OUTLINE)) continue;
        for (const [dx, dy, k] of taps) {
          const tx = x + dx, ty = y + dy;
          if (tx < 0 || ty < 0 || tx >= w || ty >= h) continue;
          const ti = ty * w + tx;
          if (dark[ti] < k) dark[ti] = k;
        }
      }
    }
    for (let y = src.y0; y <= RY1; y++) {
      for (let x = src.x0; x <= RX1; x++) {
        const i = y * w + x;
        if (!dark[i] || src.idx[i] || !this.idx[i]) continue;
        const v = (this.idx[i] - 1) / SUB;
        if (v <= OUTLINE + 0.25 || v > HI) continue;
        this.idx[i] = shadeCode(Math.max(0.25, v - dark[i]));
      }
    }
  }
  /** castShadow 的暂存（复用，避免每个部件都分配一次） */
  private dark?: Float32Array;

  /**
   * 把本层盖到 dst 上（非空像素覆盖）。可带偏移。
   *
   * innerLine：内描边改色。本层的描边像素如果落在 dst 已有的「本体」像素上，
   * 说明这一段是部件之间的内部线条，不是人物外轮廓，就改用本部件自己的暗部色
   * （深描边 → innerLine 阶，浅描边 → 再亮半阶）。外轮廓仍保留深描边。
   * 小尺寸精灵里描边占比很高，换成有颜色的内线后，色阶过渡才有空间显出来。
   *
   * maskBelow：只画在 dst 已有的本体像素上（五官等贴在表面的细节）。
   */
  drawOnto(dst: PixelLayer, ox = 0, oy = 0, innerLine?: number, maskBelow = false): void {
    const OUT = shadeCode(OUTLINE), SOFT = shadeCode(SOFT_OUTLINE);
    const map = this.palettes.map((p) => {
      let i = dst.palettes.indexOf(p);
      if (i < 0) {
        dst.palettes.push(p);
        i = dst.palettes.length - 1;
      }
      return i;
    });
    for (let y = Math.max(0, this.y0); y <= this.y1; y++) {
      const ty = y + oy;
      if (ty < 0 || ty >= dst.h) continue;
      for (let x = Math.max(0, this.x0); x <= this.x1; x++) {
        const v = this.idx[y * this.w + x];
        if (!v) continue;
        const tx = x + ox;
        if (tx < 0 || tx >= dst.w) continue;
        const di = ty * dst.w + tx;
        const under = dst.idx[di];
        // maskBelow：只写在 dst 已有的本体像素上（不含描边）
        if (maskBelow && (!under || under === OUT || under === SOFT)) continue;
        if (innerLine !== undefined && (v === OUT || v === SOFT) && under && under !== OUT && under !== SOFT) {
          dst.idx[di] = shadeCode(v === OUT ? innerLine : innerLine + 0.5);
        } else {
          dst.idx[di] = v;
        }
        dst.pid[di] = map[this.pid[y * this.w + x]];
        dst.touch(tx, ty);
      }
    }
  }

  /** 查表上色，写入 RGBA 缓冲（ImageData.data）。 */
  toRGBA(out: Uint8ClampedArray): void {
    const tables = this.palettes.map(paletteRGB);
    for (let i = 0; i < this.idx.length; i++) {
      const v = this.idx[i];
      const o = i * 4;
      if (!v) {
        out[o] = out[o + 1] = out[o + 2] = out[o + 3] = 0;
        continue;
      }
      const t = tables[this.pid[i]];
      const c = (v - 1) * 3;
      out[o] = t[c];
      out[o + 1] = t[c + 1];
      out[o + 2] = t[c + 2];
      out[o + 3] = 255;
    }
  }
}
