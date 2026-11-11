# 人物美术交接：路线 B（概念图风格 · 参数化像素人）

写给接手人物工作的另一个 Claude Code 窗口。特效窗口继续在 `claude/meadowjourney-visual-refactor-kh0zpr` 上做技能特效，**不要和它抢文件**（见“分工”）。

## 1. 项目与协作规则（沿用，不要改）

- 项目：MeadowJourney（Swift/UIKit iOS 游戏）。本线是“视觉重构”，草稿 PR #6，目标合入 Codex 的 `fix/build33-face-grounding-camera`。**Codex 的规则/逻辑代码一律不动**，只改表现层与美术。
- 与用户用**中文**沟通。所有视觉检查由用户做；**不要在云端跑模拟器**。
- 交付方式：提交信息含 `[ipa]` → 云端出**未签名 IPA 预发布**（tag `visual-<短提交号>`），用户用 SideStore 侧载。每次交付前先发**正常速度 GIF**给用户审美，每次交付后列出**接下来两项**。
- 本机**没有 Swift 工具链**，Swift 编不了。纯逻辑部分用“Python 参考实现 + Swift 逐式移植 + golden 对照脚本”（见 `scripts/check-battle-hitfeel.sh`、`scripts/check-battle-procedural.sh`），在 CI 里先编译比对；UIKit 部分只能靠设备归档编译。
- `project.pbxproj` **不要运行 `scripts/generate-project.py`**（会丢掉本地包引用），新增 Swift 文件用 `python3 scripts/add-swift-source.py <Sources 下相对路径>`。
- 不要运行 `scripts/p1-model-v3/bake.py`（会覆盖已恢复的手绘数据）。
- 不要主动开 PR；不要往别人的分支推送。

## 2. 目标

把游戏里的人物从“手绘大图”改成**参数化像素人**：一个骨架 + 可换部件（身体、发型、五官、服装、武器），动作写一次、所有部件跟着走。可换五官/发型/性别是这套系统的自然结果。

**这一阶段只做 M0（小实验）**，用来回答三个问题：好不好看、能不能和鹿灵搭、换部件顺不顺。不要一上来全量替换。

## 3. 像素密度（已和用户讨论过，务必遵守）

用户的 GPT 概念图里“16×16”是虚的，像素大小各处不一致，只能参考造型、动作清单、配色，**不能当素材**。

我们对现有主角做过自动降采样对比（`Art/Review/Character/density-v1/density-compare.png`，脚本 `scripts/review-character-density.py`），按真实显示大小放在鹿灵旁边：

| 人物高度 | 每个方块比鹿灵粗 | 观感 |
|---|---|---|
| 现在 约 134 | 1.0 倍 | 基准 |
| 72 | 1.7 倍 | 最接近现在，和鹿灵最搭 |
| 51 | 2.4 倍 | 脸开始变成色块 |
| 36 | 3.4 倍 | 五官丢失 |

**建议值：人物 64 个逻辑像素高 × 约 36 宽（含头发、手臂），每个逻辑像素最终约比鹿灵粗 1.9 倍。** 生成器请把高度做成参数（可切 48 / 64 / 72），先用 64。头约 26 高、躯干约 20、腿约 18；眼睛 3×4、眉 4×1、嘴 3×1、耳 3×4、手 4×4；1 个像素的深色轮廓（`#2a1c1a`，不用纯黑）；光源左上；每种材质 3 个明度；整幅配色不超过 24 种。

现有手绘规格供对照：战斗英雄在 256 格里约 106×132 像素，舞台上放大约 0.83～0.9；怪物同密度（布局测试里有一条“角色与怪物像素密度相近”）。

## 4. M0 交付物

1. **Python 参考生成器**（确定性，不用随机；粒子/变体用固定 id 的 `frac(i, salt)` 之类）：输入 = 部件选择 + 朝向 + 动作 + 帧，输出 = 逻辑分辨率的 RGBA 帧；再按整数倍最近邻放大。放在 `scripts/character-pixel/`。
2. **一个身体、3 种发型、3 种脸、2 套服装**（一套是概念图的蓝色束腰上衣基础款，一套请与用户确认），**5 个方向**（→ ↘ ↓ ↗ ↑，左侧镜像），动作：待机 4 帧、行走 4 帧、普攻 4 帧（先只做朝右）。
3. **预览**：按真实大小放进战斗场景，与鹿灵并排（复用 `scripts/review-character-density.py` 的合成方式，或 `scripts/review-battle-effects-demo.py` 的 `plate/enemy/foreground/shadow`），出**游戏速度的 GIF**，再出一张“换部件”对比图（同一动作，3 发型 × 3 脸 × 2 服装的组合）。
4. **验收标准**：帧间无抖动（头、头发在各帧里逐像素相同，只允许整体 1 像素起伏）；轮廓与调色板统一；换部件不改动其它像素；放在鹿灵旁边不违和。通过后再向用户申请 M1（地图八方向 + 装备 + 接入步态与阴影）。

## 5. 现有人物管线（接入时要对接，不要先改）

- 地图：P1 有 60 张按装备组合烘焙的图集（2 衣装 × 5 武器 × 无甲/皮甲/符文甲），拆分后连同身体/头部页约 160 张；布局 13 列 × 4 行 × 256 格；脚底/锚点数据 `Sources/Resources/hero-gait.json`；控制器 `Sources/Game/WalkCycle.swift`、`HeroFrames.swift`、`HeroBreathing.swift`；P2/P3 是较老的 `Hero2/3Directions|Diagonals` 图集。
- 头部拆分与运行时合成：`scripts/build-p1-head-split.py`、`Sources/Game/P1AppearanceCompositor.swift`、设计稿 `docs/visual-refactor/customization-design.md`（五官、前发各 1 张/方向，所以新增一种眼睛 = 画 8 张小图而不是逐帧重画）。
- 战斗：英雄是 22 个部件的分层骨架（`MeadowBattleHero*` 图集 + `MeadowBattleHeroAnimationV2.dataset`，6 组动作：idle/attack/guard/hit/victory/defeat），武器和护甲都按现有身体适配过（`Art/Review/Battle` 里约 40 个适配迭代目录）。**替换身体意味着这些全要重适配**，所以 M0 不要碰它们。
- 历史：`docs/visual-refactor/LOG.md` 第 8～16 条记录了人物路线的全过程（规则画 32×48/48×72 样张在 `scripts/p1-pixel/`；低模 v3 被否决，`scripts/p1-model-v3/`；原画上皮原型 `scripts/p1-reskin/`；第 15 条已恢复手绘原图）。可参考，但 B 路线不是它们的延续。
- 用户之前发给特效窗口的演示包（`pixel_demo_pack.zip`，含 `pixel_walker.py` 的程序化像素小人八方向行走）是同类方法的参考，需要请向用户索取。

## 6. 分工与分支（避免冲突）

**特效窗口负责（人物窗口请勿修改）**：`Sources/Game/MeadowSkill*.swift`、`Sources/Game/MeadowPartyStageView.swift`、`Sources/Game/MeadowBattleScenePresentation.swift`、`Sources/Game/MeadowBattleHitFeel*.swift`、`scripts/battle-vfx/**`、`scripts/review-skill-*.py`、`scripts/*battle-*regression*`、`Art/Review/Battle/skill-*`、`Art/Review/Battle/healing-*`。
**必须碰到这些文件时**（例如英雄绘制位置）改动尽量小，并先 `git fetch` 后基于最新提交。

**分支**：从 `origin/claude/meadowjourney-visual-refactor-kh0zpr` 的最新提交新建 `claude/meadowjourney-character-pixel`，所有人物工作推这个分支。IPA 工作流只对上面那条分支生效，所以在你的分支里把 `.github/workflows/visual-refactor-ipa.yml` 的 `on.push.branches` 加上你的分支名（工作流文件取推送提交里的版本）；它的并发组按分支隔离，两个窗口的构建不会互相取消。
需要特效最新代码时 `git merge origin/claude/meadowjourney-visual-refactor-kh0zpr`。最终谁合并谁，等用户决定。

**日志**：写在 `docs/visual-refactor/CHARACTER-LOG.md`（不要追加 `LOG.md`，两个窗口会冲突）。

## 7. 暂缓事项（别顺手做）

五官/性别自定义界面与存档（等 M0 通过后再接）；P2/P3 换新；怪物降密度；Codex 侧测试（战斗布局、影子、图层顺序等是基础分支本来就失败的，与本线无关）。
