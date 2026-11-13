import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  // 发型、五官数据放在 iPad 工程的 Sources/Resources/CharacterParts 里，两端共用
  server: { fs: { allow: ['..'] } },
});
