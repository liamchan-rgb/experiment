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

## 4 · 五官/性别自定义 第 1 步：拆头 + 运行时合成器（2026-11-06，待 CI）

- 先验证：60 张 P1 地图图集全部能由分层部件逐像素重现（30 种装备状态 × 2）。
- `scripts/build-p1-head-split.py` 生成 20 个身体状态的 under/body 页、20 张头部部件页和清单 dataset（约 +14 MB PNG）；
  拆分后用原头重叠与原图集最大差 1 个色阶、997 像素；3,120 格手均不压头；头部件与装备无关。记录见 `Art/Integration/P1-head-split-v1/`。
- 新增 `P1AppearanceCompositor.swift`（CoreGraphics 叠图，格式同原图集）与 `Tests/P1AppearanceCompositorTests.swift`（全 60 张对比、换头只改头部像素）。
- 本步不接入游戏显示；工程文件手工追加 2 个源文件，未运行生成脚本。

## 5 · 交付流程（用户 2026-11-06 决定）

视觉检查由用户在实机完成；本分支不在云端运行模拟器。用户选择公开预发布：新增 `.github/workflows/visual-refactor-ipa.yml`，
只在本分支、且提交信息含 `[ipa]` 时，用 macos-15-intel 做工程校验与行走回归 + 设备 Release 无签名归档，
并以 GitHub 预发布（tag `visual-<短提交号>`）发布 IPA 直链供 SideStore 侧载。PR 自动触发的模拟器流程推送后手动取消。之后流程与提交说明用中文。

## 6 · 修正侧向肤色不一致（2026-11-06，用户反馈）

用户指出头部在侧向时肤色和轮廓都变了。核查：正面/正左/正右皮肤主色 #fbcb9b（桃色），四个斜向与正背面为 #fdbf70（偏橙），手部同样；轮廓线颜色各方向一致。
`scripts/fix-p1-skin-tone.py` 把这 5 个方向的 head.base、手、手臂皮肤按亮度排名映射到正面色阶（保留明暗结构，不动轮廓线、眼睛、衣物），共 325 张部件图；
`scripts/rebake-p1-map-atlases.py` 用已验证的部件组合重新烘焙全部 60 张 P1 地图图集（名称、尺寸、格子顺序、锚点、hero-gait.json 不变），再重跑头部拆分（复核仍为最大差 1 级、997 像素、手不压头）。

## 7 · 斜向五官与发型精修（2026-11-06，用户要求）

- 左下/右下眼睛按正面眼重建（近侧 10 列、远侧 6 列、间隔 3 像素、高度与正面一致），两种眼型；右下为左下镜像。
- 银发四个斜向按亮度排名统一到正面/背面/侧面色阶；栗发一致未改。
- 重烘 60 张图集 + 头部拆分复核通过；正常速度八方向 GIF 与前后对比见 `Art/Review/P1/diagonal-heads-v1/`。

## 8 · 斜向头部 v2（2026-11-06，用户反馈）

左下/右下去掉下巴 1 像素尖点并加宽下颌 5 行（圆下巴）；左上/右上头发下沿延伸约 8 像素盖住太阳穴；修复上一轮银发调色误带入的绿色标记像素，
脚本改为只用不透明参考像素。重烘 60 张图集与头部拆分，复核通过、无不透明纯绿像素。
