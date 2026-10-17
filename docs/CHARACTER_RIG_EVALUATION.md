# 可换装人物骨骼项目评估

检查时间：2026-10-17。目标是在后续人物美术分层后，能复用骨骼动画、替换服装／装备，并继续用 MeadowJourney 的单 MTKView 和同一帧实时阴影。

## 推荐做隔离原型：Rigby2D

[Rigby2D 源码](https://github.com/jaisurya-dev-art/rigby2d)采用 MIT 或 Apache-2.0 双许可，包含编辑器、PSD 自动绑骨、动画重定向和游戏运行时。其 Rust 核心运行时无第三方依赖，读 JSON／`.skel`，支持骨骼、网格、IK、换装 skin／slot，并输出按纹理页分批的三角网格。它的功能与后续换装需求相符，优先级高于继续扩展按坐标切分整张人物贴图的脚本。

接入限制：项目在 README 中标为 early alpha；编辑器目前面向 Windows、macOS、Linux，没有 Swift、SpriteKit 或 iOS 渲染器。Rust 核心本身只负责动作计算和网格批次，移入 app 仍需要 iOS 编译目标、稳定的 C ABI、纹理页加载和 Metal 绘制。阴影也必须从同一变形后的网格生成，不能再用独立步态近似。现有三位人物是扁平 PNG，不能靠自动绑骨无损拆成独立服装层；需要原画分层 PSD／PNG 或重新绘制肢体与衣物部件。

结论：适合作为角色编辑和动作数据的候选，不适合不经验证就替换当前运行渲染器。先用一位人物制作分层样例，在 iPad 原生构建里确认运行时能编译、服装 skin 可交换、Metal 前景与阴影共享同一姿势，且不引入第二个实时视图。完成这些检查再决定保留其 Rust 核心还是只采用其格式与编辑流程。

## 对照项目

- [DragonBones C++ Runtime](https://github.com/DragonBones/DragonBonesCPP) 是 MIT，但官方列出的运行接入示例是 Cocos2d-x 与 SFML；README 建议用 DragonBones Pro 制作动画。DragonBones 的转换工具开源，但设计面板项目依赖旧 Flash Pro／Flex 工作流。相较 Rigby2D，它没有一条现成的开源编辑器加 iOS 集成路径。
- [Rigby2D 的 Rust 运行时说明](https://github.com/jaisurya-dev-art/rigby2d/tree/main/runtimes)记录了换装 skin、贴图页三角批次和跨运行时一致性检查；后续原型应直接对照这些接口与测试，不手写另一套自定义文件格式。

## build 26 鞋子修正

build 25 的离线步态生成器根据屏幕水平位移虚构了鞋跟／鞋尖轴，再对不同朝向的原画鞋子做小幅旋转。正面和斜向鞋型本来就有各自的画笔角度，这种通用旋转会把鞋扳歪。build 26 改成刚性平移鞋部蒙版、保留当前朝向原画角度；是否解决鞋与靴筒的连接和动态落脚观感，以 iPad 模拟器连续录像抽帧结果记录。

## OpenToonz 离线分层原型

Rigby2D 之外，本轮按用户选择验证了 OpenToonz/Tahoma2D 的离线分层动画流程：从现有 P1 向下步态导出 24 帧 PNG level，将腿、鞋、身体和替代鞋色分开，供美术直接检查与编辑。它不要求把动画运行时换成骨骼系统，最终仍可烘焙成 app 现有的整帧图集。具体导入方式、对照资源和像素差异记录在 [OpenToonz 原型说明](OPEN_TOONZ_PROTOTYPE.md)。

这条路线最适合先建立可迭代的美术制作流程；它本身不会自动解决分层绘制工作，也不会提供运行时的角色自定义。原型的逐帧参考与现有图集完全一致，简单的三层重组在腿鞋遮挡处最多相差 342 像素；扩展前需要把前后腿／鞋拆层或加入逐帧遮挡顺序。编辑器 GUI 还未做导入往返验证。
