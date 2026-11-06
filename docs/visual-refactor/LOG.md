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

## 2 · P1 步态参数修正 v1（2026-11-06，待 CI 与用户审核）

- `WalkCycle.swift` 新增 `GaitTiming`：按 hero-gait.json 中 P1 每姿势的脚底点，计算每个朝向 8 个姿势各占的行走距离（落地脚实际后移量，夹限并与均匀混合 60%）；
  `AuthoredLocomotion` 可选传入，入场/出场姿势起点与收步剩余距离都按新窗口计算；不传时与原实现逐帧相同。
- 只对左、右、下生效（打滑 1.62→0.80 / 1.12）；上与斜向原图步幅太短，保持均匀，留待重烘焙。
- 新增 `HeroBreathing.swift`：待机呼吸（≤1.2%，3.4 秒，锚点不动，阴影同步，倒地不呼吸）。
- `GameScene` 只改三处：P1 传入时序、呼吸状态数组、每帧设置 yScale 并传给阴影投射。
- `modular-locomotion-regression.swift` 新增脚底时序检查：每行合计 24、短步幅方向保持均匀、其余方向打滑下降、
  姿势顺序不跳不倒、64 个“任意相位停步仍经指定出场姿势”。本机无 Swift 工具链，已用 Python 等价镜像跑通同样 64 例；Swift 版由 CI 运行。
- 正常速度对照 GIF：`Art/Review/P1/gait-timing-v1/`（离线合成）。未改：图片、方向绑定、锚点、起停帧时长、步频、移动速度。

## 3 · 修复：工程文件被生成脚本覆盖（2026-11-06）

前两次提交用 `scripts/generate-project.py` 重新生成了 `project.pbxproj`，把 Codex 手工加入的本地 Swift 包引用
（`Vendor/ClassroomGameCore` 的 ClassroomGameCore / MeadowWorldSupport / MeadowBattleSupport）、5 个 UI/战斗源文件和版本号 1.6.62/89 一并抹掉，
导致 CI 报 `no such module 'ClassroomGameCore'`。已恢复为基础分支的工程文件，只手工追加本分支 3 个新文件（HeroBreathing.swift、MeadowPostProcess.swift/.metal），
ID 与生成脚本算法一致。**本分支此后不再运行 generate-project.py**，新增文件一律手工追加。
