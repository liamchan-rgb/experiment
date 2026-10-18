# P1 人物素材逐张审核

开始日期：2026-10-18。用户要求 P1 原始素材按方向逐张审核，修改后确认再推进下一张，最终以认可结果建立支持换装备、自定义人物的人物模板。

## 当前审核

**当前第 07 个方向、斜向第三组：P1 左上 ↖ r3 待用户审核。四个正交方向、右下和左下 r1 均已认可，右上仍排队。**

左下已认可；用户随后要求修订左上 r1 的 04–06，并回复“那就开始修”。用户又指出 04 右脚外翻，当前 r3 只修订 04，其他八张姿势原样继承 r2，不提前推进右上。

- [当前左上 r3 编号图](../Art/Review/P1/directions/up-left/revisions/r3/review-2x.png)
- [正常循环](../Art/Review/P1/directions/up-left/revisions/r3/walk.gif) · [四分之一速度循环](../Art/Review/P1/directions/up-left/revisions/r3/walk-slow.gif)
- [左上 r3 说明与来源](../Art/Review/P1/directions/up-left/revisions/r3/README.md) · [问题依据](../Art/Review/P1/directions/up-left/AUDIT.md)
- [已认可左下 r1 与记录](../Art/Review/P1/directions/down-left/revisions/r1/approval.json) · [已认可右下 r1](../Art/Review/P1/directions/down-right/revisions/r1/README.md)
- [04 局部前后对照](../Art/Review/P1/directions/up-left/revisions/r3/detail-04.png) · [同步慢速对照](../Art/Review/P1/directions/up-left/revisions/r3/r2-r3-slow.gif)
- [完整状态与全部认可范围](../Art/Review/P1/review.json)

两份固定图集均为 build 28 正式生成结果，各 6400 × 1024、每格 256 × 256，与正式图集逐字节一致。正交图集行序下、左、上、右；斜向图集为右下、左下、左上、右上，由生成器 HEADINGS 索引 4–7 与运行时逐行加载核对。每行最左格为站姿，随后 01–24 步行帧。

各方向原像素横条为 6400 × 256，原编号预览为黑底 5 × 5，00 站姿、01–24 步行。仅机械切片、排版和添加编号，横条 RGBA 与固定基线对应行一致。PNG 为透明背景，预览显示黑底。新修订另存 revisions/r1、r2、r3 等独立目录，不覆盖原图。

| 顺序 | 方向 | 原像素横条／新稿 | 编号预览 | 审核状态 |
| --- | --- | --- | --- | --- |
| 01 | 下 | [r1 横条](../Art/Review/P1/directions/down/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/down/revisions/r1/review-2x.png) | r1 用户已认可 |
| 02 | 左 | [r1 横条](../Art/Review/P1/directions/left/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/left/revisions/r1/review-2x.png) | r1 用户已认可 |
| 03 | 上 | [r1 横条](../Art/Review/P1/directions/up/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/up/revisions/r1/review-2x.png) | r1 用户已认可 |
| 04 | 右 | [r1 横条](../Art/Review/P1/directions/right/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/right/revisions/r1/review-2x.png) | r1 用户已认可 |
| 05 | 右下 ↘ | [r1 横条](../Art/Review/P1/directions/down-right/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/down-right/revisions/r1/review-2x.png) | r1 用户已认可 |
| 06 | 左下 ↙ | [r1 横条](../Art/Review/P1/directions/down-left/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/down-left/revisions/r1/review-2x.png) | r1 用户已认可 |
| 07 | 左上 ↖ | [r3 横条](../Art/Review/P1/directions/up-left/revisions/r3/strip.png) | [r3 预览](../Art/Review/P1/directions/up-left/revisions/r3/review-2x.png) | 当前，r3 待认可 |
| 08 | 右上 ↗ | [原横条](../Art/Review/P1/directions/up-right/strip.png) | [原预览](../Art/Review/P1/directions/up-right/review.png) | 排队，未重画／审核 |

每次只提交当前方向。收到反馈后按帧编号另存修改版本，记录具体意见与依据，再提交同一方向；用户明确认可后才推进下一方向。历史站姿提取和旧版图集识别不代表美术认可。

六个已认可方向与当前左上审核稿均为站姿＋八张关键姿势，编号 00–08，与旧版 00–24 不同。左上参照原左上视角和已认可向上背部／靴子设计，逐张重画完整姿势，协调短步幅、抬跟、两次过腿与反向摆臂。左上 r3 修订 04 的画面右脚外翻，其余八张原样继承 r2；认可为空，右上未重画。最终分层模板及固定侧装备挂点尚未完成，正式安装包未更新。

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
