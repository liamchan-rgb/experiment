# Meadow Journey 林地鹿灵敌方样例 v1

这是一张供 Meadow Battle 战场排版试验使用的单体敌人精灵，沿用暖棕、苔绿、琥珀与象牙白色系，并采用与 Meadow Journey 地图人物相容的清晰像素团块。角色朝左，匹配向右待机的旅人。它是本地生成的新样例，不来自 `classroom-boardgame`，也不代表最终敌方角色设计或用户审美通过。

## 注册与尺寸

- 原画及运行图：1536×1024 RGBA；`source/forest-warden-chromakey.png` 保留原始生成结果，粉色纯色背景仅用于抠图。
- 运行图 `forest-warden.png` 使用与原图相同画布，不裁切、缩放或按外接框重注册；背景粉色转为真实 alpha。
- alpha 外接框：`(32, 12, 1484, 948)`；脚底注册点使用外接框中心 x 与下沿 y。
- 场景脚底锚点：`(0.70, 0.685)`；战斗可见高度为场景画布的 38%。最近邻缩放。
- 独立地面接触阴影由运行时代码绘制，图像本身不烘焙阴影、场景或战斗效果。

## 来源与处理

图像生成提示、原始 PNG 摘要及可复现的 18% magenta color-key 命令写在 `generation.json`。工具生成物包含不完全均匀的纯粉底；最终仅用该底色建立透明通道，没有涂改角色像素。用于正式 app 资源的是 `Sources/Resources/Assets.xcassets/MeadowBattleForestWarden.imageset/forest-warden.png`。

当前只验证单张透明图、画布注册、尺寸与合成层级。尚未制作动作、攻击帧或击中特效，也未接入桌游规则。

[林地战场合成预览](review-composite.png)按运行时同一组环境层、缩放、脚底锚点和最近邻像素规则离线重组，仅供美术／排版检查，不是模拟器截图。
