# P1 人物素材逐张审核

开始日期：2026-10-18。用户反馈 build 28 步态仍有问题，要求 P1 原始素材逐张发送审核，每张修改确认后再处理下一张，最后以确认结果建立支持换装备、自定义人物的人物模板。

## 当前审核

**当前第 04 个方向：P1 向右，原有站姿＋24 帧步态待审核。向下 r1、向左 r1、向上 r1 已获用户认可。**

用户在看到原有 `Hero1Directions.png` 完整宽图后回复“就是这个”，随后要求按方向切片讨论。向下 r1、向左 r1、向上 r1 先后重画并获认可；用户在向上 r1 后回复“可以的，继续下一个方向”，现按下、左、上、右顺序进入向右审核。

- [当前向右方向编号图](../Art/Review/P1/directions/right/review.png)
- [当前向右正常循环](../Art/Review/P1/directions/right/walk-baseline.gif) · [四分之一速度循环](../Art/Review/P1/directions/right/walk-baseline-slow.gif)
- [向右原像素横条](../Art/Review/P1/directions/right/strip.png) · [当前审核说明](../Art/Review/P1/directions/right/README.md)
- [已认可的向上 r1](../Art/Review/P1/directions/up/revisions/r1/README.md) · [用户确认记录](../Art/Review/P1/directions/up/revisions/r1/approval.json)
- [已认可的向左 r1](../Art/Review/P1/directions/left/revisions/r1/README.md) · [用户确认记录](../Art/Review/P1/directions/left/revisions/r1/approval.json)
- [已认可的向下 r1](../Art/Review/P1/directions/down/revisions/r1/README.md) · [用户确认记录](../Art/Review/P1/directions/down/revisions/r1/approval.json)
- [完整图集固定基线](../Art/Review/P1/01-cardinal-atlas/baseline.png)
- [审核状态及来源记录](../Art/Review/P1/review.json)

图集为 build 28 正式生成结果，6400 × 1024，每格 256 × 256。四行从上到下为向下、向左、向上、向右；每行最左格是站姿，随后为步行帧 01–24。PNG 为透明背景，工具预览显示为黑底。基线文件与正式图集逐字节一致，独立保留用于后续对照。

每方向保存一张 6400 × 256 的原像素横条，以及一张黑底 5 列 × 5 行编号预览。编号预览按从左到右、从上到下读取：00 是站姿，01–24 是行走帧；只改变排版、添加编号与查看用底色，没有修图。横条与固定基线对应行的 RGBA 像素逐一一致。

| 顺序 | 方向 | 原像素横条 | 编号预览 | 审核状态 |
| --- | --- | --- | --- | --- |
| 01 | 下 | [r1 横条](../Art/Review/P1/directions/down/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/down/revisions/r1/review-2x.png) | r1 用户已认可 |
| 02 | 左 | [r1 横条](../Art/Review/P1/directions/left/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/left/revisions/r1/review-2x.png) | r1 用户已认可 |
| 03 | 上 | [r1 横条](../Art/Review/P1/directions/up/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/up/revisions/r1/review-2x.png) | r1 用户已认可 |
| 04 | 右 | [横条](../Art/Review/P1/directions/right/strip.png) | [预览](../Art/Review/P1/directions/right/review.png) | 当前，待反馈 |

收到反馈后按方向、帧编号另存修改版本，记录具体意见与改法，再提交同一方向。用户明确认可当前方向后才进入下一方向；四个基本方向完成后再处理斜向图集。此前单独站姿和向下单行的提取文件仍保留为历史记录，均未被标记通过。

已认可的向下 r1、向左 r1、向上 r1 均为一张新站姿与八张重画关键姿势，编号 00–08；当前向右仍是旧版站姿＋24 帧，编号 00–24，帧号含义不同。三份认可记录均保存用户原话、范围及图像／循环摘要，作为后续模板的方向依据。向右尚未认可，最终分层模板尚未完成，正式安装包未更新。

## 现有资源与问题依据

P1 原始素材有两张 4 × 4 图：`hero1-gait-v1.2.png` 和 `hero1-diagonal-v1.3.png`。当前 `scripts/prepare-gait-assets.py` 的 `legacy_rows()` 只选择每方向第一列站姿，裁切腿部生成每方向 24 张步行帧；其余原始行走姿势并未直接用于正式动画。运行时右侧面还采用左侧面的完整镜像。因而这次需要重新审核原始姿势、修改依据和最终动态，不能把既有自动生成结果视为通过。

以用户确认的完整图集为素材来源，按方向切片审核，结合帧编号定位修改；审核顺序和下一项由当前项的实际进展更新。动作仍需逐帧与连续播放检查，特别是承重、摆腿、两次过腿、鞋尖朝向及鞋腿接缝。

## 人物模板目标（待审核后制作）

- 统一八方向的身体比例、观察角度、画布、地面线与左右肢体命名。
- 分离身体、头发、服装、手、腿、左右鞋和装备，明确被衣物遮住的身体所需补画，保留可编辑源文件。
- 记录髋、膝、踝和装备挂点，区分角色自身左右与画面左右；替换部件需遵守同一挂点和尺寸约定。
- 每张姿势记录脚底接触、抬脚、前后遮挡和部件绘制顺序；前景与阴影共用确认过的姿势。
- 用确认后的 P1 建立模板 v1，再验证至少一次装备替换和人物外观替换，之后扩展其他人物。

以上是模板要求，当前尚未产出或认可最终模板，也未选定新的运行时。

## 同方向完整动作横图参考

用户询问此前看到的一张很宽、包含一个方向所有动作的图。现提供 [P1 向下完整步态横图](../Art/Review/P1/reference-down-build28-strip.png)，尺寸 6400 × 256，最左格为站姿，随后 24 格是行走帧 01–24。

该图按原像素提取自 build 28 正式 `Hero1Directions.png` 第一行，逐像素核对一致。用户随后明确这不是要找的图，最终确认的是上方所列的完整四方向图集。此单行保留作历史参考，不作为当前审核对象。
