# 强击 × 训练短剑 · 特效资源 v1

首组桌游资源按 `classroom-boardgame` 已归档的 B 动画规范制作：关联冒险者技能 `heavyStrike`（强击）和装备 `trainingSword`（训练短剑），输出独立的挥击／命中表现层。目标格式是 8 格、每格 256×256、总长 650ms、一次播放、末帧透明；表现只在规则库提交结果后播放一次，不重掷骰、不重复结算，也不将数字烘焙到图片里。造型沿用归档 `impact` 的红、象牙白与浅蓝几何色板，方向由左下挥向右上。

## 审核文件

- [正常速度一次播放预览](outputs/preview-normal.gif)
- [8 帧编号总览](outputs/review.png)
- [运行时透明 PNG 条带](outputs/fx_heavyStrike_sheet.png)
- [逐帧透明 PNG](frames/)
- [资源和规则映射清单](asset-manifest.json)
- [机器验证结果](validation.json)

## 资源与动画边界

此条带仅负责剑光和命中闪光，不含人物、手臂、手或剑，也不包含逐帧挥剑动作；训练短剑仍作为独立装备资源挂载，不能因技能 ID 替换装备图。下一步可按相同规范制作角色挥击关键姿势，再以角色动作、武器部件和独立效果层组合验收。本稿尚未接入桌游 App 或人物运行时。

可编辑主文件为 `source/fx_heavyStrike.svg`。早期生成概念及提示词保存在 `source/concepts/`，因色彩和发光方式与桌游归档素材不统一，没有用于正式输出。`build.py` 从 SVG 重建八个逐帧 PNG、条带和正常速度一次播放 GIF；接触总览中的底格和帧编号仅用于审核，不属于运行时素材。

## 来源规划

- 桌游规则源：`classroom-boardgame` 的 `heavyStrike` / `trainingSword`，内容提交 `1e9100c4c18364ea64b3ec974fe957ba4ef42f6f`，`initial-content.json` SHA-256 `aaab980fd5f3154ac813a02dc907a835ee0e0181c4149f2b7803d9594795f34a`。
- 动画合同：归档 `archive-design-b-art-motion-v1-20261012`（提交 `bc2049fb579ef488470a8a2a75a0c078eb492c22`），沿用独立表现贴图的 8 帧、650ms、一次播放、透明末帧约定。
- 已归档的 `impact` 条带和训练短剑 PNG 放在 `references/` 仅供审美／尺寸对照，没有修改或复制进运行时输出。

运行 `python3 build.py` 可从保留的矢量母版重建逐帧 PNG、总条带、GIF 预览、清单和机器验证文件。制作依赖 Python 3、Pillow、NumPy 和 Inkscape；它们不是运行时依赖。
