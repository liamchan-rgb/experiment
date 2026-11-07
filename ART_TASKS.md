# 美术任务入口：星辉甲 / 龙纹甲

本文件供已连接 `liamchan-rgb/experiment` 仓库的 Chat / agent 直接读取。工作分支：`fix/build33-face-grounding-camera`。资料、PNG、SVG、模板已存入仓库，不需要用户重复下载、上传参考包或粘贴完整提示词。

## 读取顺序

1. [总任务书](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/README.md) 和 [总指令](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/CHAT_START.txt)。
2. [阶段与职责](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/01_PIPELINE.md)。
3. [星辉甲](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/02_STARLIGHT_ARMOR.md)、[龙纹甲](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/03_DRAGON_ARMOR.md)。
4. [分层规格](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/04_LAYER_AND_POSE_SPEC.md)、[验收](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/05_ACCEPTANCE.md)。
5. [示例索引](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/examples/README.md)：实际打开其中身体/关节导板、蓝衣分层图和母版复用示例，不只读文字。
6. [交付模板](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/templates/README.md)。

## 本轮执行范围

先做 C0、C1：核实读到的参考，给两件甲各三个结构不同的方案，每方案用相同人物的正面和左下视角展示，等用户分别选定。新设计尚未选型，不得把旧B5候选当作认可款。

选型后按 C2—C4 制作静态分层母版：每件五视角，每视角四层，共20张PNG；不是20次独立随机生成，也不要求逐帧重画。现有人体、头脸、裤靴、武器、动作和步相保持。

Codex接收母版后按 `integration/` 复用原模组适配、批量导出104姿势、修复并审核正常速度动图。最终输出数量不属于绘图Chat的手绘工作量，技术检查不能代替美术审核或用户认可。

## 访问与交接

- 本地检出仓库时，以上相对链接直接指向实际文件；GitHub工具读取时必须选择上述工作分支，不能默认另一个分支。
- 如果对话没有仓库读取能力，应如实说明未能读取的文件，不假装已经看过示例。`Downloads/Chat-Apparel-Masters-v2.zip` 仅作为无仓库访问能力时的备用离线包。
- 记录本次实际读取的分支/提交、文件、已完成阶段与缺项。绘图任务到母版交接为止；不自动启动游戏功能开发或打IPA。

后续两步：分别选定两件设计；制作五视角分层母版后交Codex适配。
