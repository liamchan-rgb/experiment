# 视觉重构日志（分支 claude/meadowjourney-visual-refactor-kh0zpr）

独立于 Codex 的逻辑分支 `fix/build33-face-grounding-camera`，最后统一合并；为避免与其顶部日志冲突，
本分支的逐步记录写在这里，合并时再向 `docs/ITERATION_STATUS.md` / `AGENTS.md` 补总结条目。

范围（用户 2026-11-06）：地图素材保留；技能特效重构；先做世界层 HD-2D 后处理，再人物步态参数、灯光、战斗氛围等。
不改点击、寻路、镜头、探索、战斗规则；不改资源名称/尺寸/锚点。

## 1 · 世界层 HD-2D 后处理 v1（2026-11-06，待 CI 与用户审核）

- 新增 `Sources/Game/MeadowPostProcess.{swift,metal}`；`MeadowShadowRenderer.encodeComposite` 增加后处理分支。
- 流程：原背景 + SpriteKit 世界 → 全分辨率离屏 → 1/4、1/8、1/16 降采样链（移轴两档、亮部提取、两档泛光，
  自写可分离高斯，不依赖 MPS）→ 合成到屏幕（移轴、泛光、远景暖雾、世界锚定光柱、S 曲线/饱和/冷暖分离、暗角）
  → 再画一遍 zPosition ≥ 22000 的地图内 UI（P1/P2 标牌、节点徽记、完成火花），不模糊不调色。UIKit 按钮在 Metal 之上本就不受影响。
- 步态检视（gaitTest）、`-alignmentReview` 像素对齐检查不走后处理；启动参数 `-noPostProcess` 可关闭，管线创建失败自动回退原单通道路径。
- 额外显存：iPad Pro 12.9（2732×2048）约 28.6 MB（离屏 22.4 MB + 降采样链约 6.2 MB）；11 寸约 20 MB。帧率待 CI/实机测。
- 未在本机编译（Linux 无 Swift/Metal 工具链），由 PR 的 GitHub Actions 编译与截图验证。
- 离线参数预览：`Art/Review/PostProcess/hd2d-v1/`（明确为离线近似）。
