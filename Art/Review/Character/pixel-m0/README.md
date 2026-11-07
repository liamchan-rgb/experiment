# M0 · 参数化像素人 v0（离线预览，待审）

由 `python3 scripts/character-pixel/build_m0.py` 生成（`--height 48|72` 输出到子目录）。

- `battle-scene.gif`：真实大小放进战斗场景，与鹿灵并排；朝右持剑待机 → 普攻 → 待机，游戏速度（待机 200/180 ms，普攻 140/70/220/200 ms）。
- `walk-8dir.gif`：8 方向（左侧为镜像），上行行走 4×140 ms，下行待机，×4 放大。
- `sheet.png`：5 方向 × 待机/行走 + 朝右普攻，×4。
- `swap-compare.png` / `swap-compare-right.png`：3 发型 × 3 脸 × 2 服装，同一动作（↘ / →）。
- `frames/`：基础款逻辑分辨率帧（1×）。
- `checks.json`：头部逐像素稳定、色数、换部件隔离、尺寸。

离线合成，不是游戏内截图；用户美术认可：null。详见 `docs/visual-refactor/CHARACTER-LOG.md`。
