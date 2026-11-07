# 模型 v3（低模）实验，未用于游戏

用户 2026-11-07 决定恢复手绘原图（见 `docs/visual-refactor/LOG.md` 第 15 条）。本目录是 SDF 低模绘制与烘焙实验，保留作参考。

**不要随手运行 `bake.py`**：它会覆盖 `Art/Parts/P1-v1/eight-way-v1/*` 的部件 PNG、`motion.json` 与 `hero-gait.json`。
若要重新实验，先在另一个工作副本里运行，并在之后用 `git checkout 527e3548 -- <路径>` 还原。
