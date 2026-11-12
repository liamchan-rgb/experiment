import { deflateSync } from 'node:zlib';

/** 极简 PNG 编码器（RGBA8，无依赖），给导出脚本用。 */

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(buf: Uint8Array): number {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type: string, data: Uint8Array): Buffer {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  out.write(type, 4, 'ascii');
  Buffer.from(data).copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}

export function encodePNG(width: number, height: number, rgba: Uint8Array | Uint8ClampedArray): Buffer {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // RGBA
  const raw = Buffer.alloc((width * 4 + 1) * height);
  for (let y = 0; y < height; y++) {
    raw[y * (width * 4 + 1)] = 0; // filter: none
    Buffer.from(rgba.buffer, rgba.byteOffset + y * width * 4, width * 4).copy(raw, y * (width * 4 + 1) + 1);
  }
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 9 })),
    chunk('IEND', new Uint8Array(0)),
  ]);
}

/** RGBA 画布：只做导出要用的「贴一块」和「最近邻整数放大」。 */
export class Image {
  readonly data: Uint8ClampedArray;
  constructor(readonly w: number, readonly h: number) {
    this.data = new Uint8ClampedArray(w * h * 4);
  }

  /** 把 src 贴到 (dx, dy)，按 scale 做最近邻放大，flip = 水平镜像。只覆盖不透明像素。 */
  blit(src: Image, dx: number, dy: number, scale = 1, flip = false): void {
    for (let y = 0; y < src.h; y++) {
      for (let x = 0; x < src.w; x++) {
        const si = (y * src.w + (flip ? src.w - 1 - x : x)) * 4;
        if (src.data[si + 3] === 0) continue;
        for (let by = 0; by < scale; by++) {
          const ty = dy + y * scale + by;
          if (ty < 0 || ty >= this.h) continue;
          for (let bx = 0; bx < scale; bx++) {
            const tx = dx + x * scale + bx;
            if (tx < 0 || tx >= this.w) continue;
            const ti = (ty * this.w + tx) * 4;
            this.data[ti] = src.data[si];
            this.data[ti + 1] = src.data[si + 1];
            this.data[ti + 2] = src.data[si + 2];
            this.data[ti + 3] = src.data[si + 3];
          }
        }
      }
    }
  }

  png(): Buffer {
    return encodePNG(this.w, this.h, this.data);
  }
}
