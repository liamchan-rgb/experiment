# 美术任务入口：星辉甲 / 龙纹甲

本文件供已连接 `liamchan-rgb/experiment` 仓库的 Chat / agent 直接读取。工作分支：`fix/build33-face-grounding-camera`。资料、PNG、SVG、模板已存入仓库，不需要用户重复下载、上传参考包或粘贴完整提示词。

## 读取顺序

1. [总任务书](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/README.md) 和 [总指令](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/CHAT_START.txt)。
2. [阶段与职责](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/01_PIPELINE.md)。
3. [星辉甲](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/02_STARLIGHT_ARMOR.md)、[龙纹甲](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/03_DRAGON_ARMOR.md)。
4. [分层规格](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/04_LAYER_AND_POSE_SPEC.md)、[验收](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/05_ACCEPTANCE.md)。
5. [示例索引](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/examples/README.md)：实际打开其中身体/关节导板、蓝衣分层图和母版复用示例，不只读文字。
6. [交付模板](Art/Standards/P1-Locomotion-Delivery-v1/chat-apparel-v2/templates/README.md)。

## 当前选型与执行结果（2026-11-07）

用户明确“两个都选择b”：星辉甲B天仪礼甲、龙纹甲B龙翼巡游甲，分别登记。随后要求“你一路做完所有方向的”，本轮不在正面C2暂停。

实际新资源位于 `Art/Parts/P1-v1/chat-apparel-v2/<item>/`：每件五默认视角+三右向，共八view×四层＝32张256RGBA静态母版；两件64张。原模组输出每件104绑定/416层引用，两件208姿势/832引用，未重画人体或动作。正常GIF、整身站姿、13姿势表、实际解码/检查记录见[本轮审核页](Art/Review/P1/chat-apparel-v2-b-eight-way-r1/README.md)。

设计B已选定；新母版/八向动作的用户认可仍待反馈。资源未接入App/课堂，不自动打IPA。旧B5与旧服装保留，模板仍是未填写的格式示例，实际进度读新包 master-manifest.json / asset.json / authoring.json。

## 访问与交接

- 本地检出仓库时，以上相对链接直接指向实际文件；GitHub工具读取时必须选择上述工作分支，不能默认另一个分支。
- 如果对话没有仓库读取能力，应如实说明未能读取的文件，不假装已经看过示例。`Downloads/Chat-Apparel-Masters-v2.zip` 仅作为无仓库访问能力时的备用离线包。
- 记录本次实际读取的分支/提交、文件、已完成阶段与缺项。绘图任务到母版交接为止；不自动启动游戏功能开发或打IPA。

后续两步：集中处理用户八向反馈；认可后按对接协议接入demo/课堂并归档直接IPA。
