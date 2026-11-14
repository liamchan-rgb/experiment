import { defineConfig } from 'vite';

/**
 * 游戏内烘焙器：把 src/runtime.ts 打成一个不依赖 DOM 的 IIFE 文件，
 * iPad 端用 JavaScriptCore 执行（npm run runtime → dist-runtime/pixel-baker.js）。
 */
export default defineConfig({
  server: { fs: { allow: ['..'] } },
  build: {
    outDir: 'dist-runtime',
    emptyOutDir: true,
    target: 'es2019',
    minify: true,
    lib: { entry: 'src/runtime.ts', formats: ['iife'], name: 'PixelBakerBundle', fileName: () => 'pixel-baker.js' },
  },
});
