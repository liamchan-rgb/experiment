# P1 人物素材逐张审核

开始日期：2026-10-18。用户要求 P1 原始素材按方向逐张审核，修改后确认再推进下一张，最终以认可结果建立支持换装备、自定义人物的人物模板。

## 当前审核

**当前第 08 个方向、斜向第四组：P1 右上 ↗ r1 整组待审核。左上 r6 与其他六个方向已获认可。**

用户要求参考左上制作过程，避免朝向漂移、鞋脚外翻与相邻帧突然张腿。本轮以已认可左上 r6 的 00–08 完整姿势逐张对应绘制右上，统一相位、脚距与完整靴子设计，再用整组和左右同步循环检查。

- [当前右上 r1 编号图](../Art/Review/P1/directions/up-right/revisions/r1/review-2x.png)
- [正常循环](../Art/Review/P1/directions/up-right/revisions/r1/walk.gif) · [四分之一速度循环](../Art/Review/P1/directions/up-right/revisions/r1/walk-slow.gif)
- [左上／右上同步慢速对照](../Art/Review/P1/directions/up-right/revisions/r1/left-right-slow.gif) · [逐帧同步对照](../Art/Review/P1/directions/up-right/revisions/r1/left-right-review-2x.png)
- [右上绘制说明](../Art/Review/P1/directions/up-right/revisions/r1/README.md) · [制作约束](../Art/Review/P1/directions/up-right/AUDIT.md)
- [左上 r6 整组认可记录](../Art/Review/P1/directions/up-left/revisions/r6/approval.json) · [完整审核状态](../Art/Review/P1/review.json)

两份固定图集均为 build 28 正式生成结果，各 6400 × 1024、每格 256 × 256，与正式图集逐字节一致。正交图集行序下、左、上、右；斜向图集为右下、左下、左上、右上，由生成器 HEADINGS 索引 4–7 与运行时逐行加载核对。每行最左格为站姿，随后 01–24 步行帧。

各方向原像素横条为 6400 × 256，原编号预览为黑底 5 × 5，00 站姿、01–24 步行。仅机械切片、排版和添加编号，横条 RGBA 与固定基线对应行一致。PNG 为透明背景，预览显示黑底。新修订另存 revisions/r1、r2、r3 等独立目录；r4、r5 单张修改源也保留，不覆盖原图。

| 顺序 | 方向 | 原像素横条／新稿 | 编号预览 | 审核状态 |
| --- | --- | --- | --- | --- |
| 01 | 下 | [r1 横条](../Art/Review/P1/directions/down/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/down/revisions/r1/review-2x.png) | r1 用户已认可 |
| 02 | 左 | [r1 横条](../Art/Review/P1/directions/left/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/left/revisions/r1/review-2x.png) | r1 用户已认可 |
| 03 | 上 | [r1 横条](../Art/Review/P1/directions/up/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/up/revisions/r1/review-2x.png) | r1 用户已认可 |
| 04 | 右 | [r1 横条](../Art/Review/P1/directions/right/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/right/revisions/r1/review-2x.png) | r1 用户已认可 |
| 05 | 右下 ↘ | [r1 横条](../Art/Review/P1/directions/down-right/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/down-right/revisions/r1/review-2x.png) | r1 用户已认可 |
| 06 | 左下 ↙ | [r1 横条](../Art/Review/P1/directions/down-left/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/down-left/revisions/r1/review-2x.png) | r1 用户已认可 |
| 07 | 左上 ↖ | [r6 横条](../Art/Review/P1/directions/up-left/revisions/r6/strip.png) | [r6 预览](../Art/Review/P1/directions/up-left/revisions/r6/review-2x.png) | r6 用户已认可 |
| 08 | 右上 ↗ | [r1 横条](../Art/Review/P1/directions/up-right/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/up-right/revisions/r1/review-2x.png) | 当前，r1 整组待认可 |

每次只提交当前方向。收到反馈后按帧编号另存修改版本，记录具体意见与依据，再提交同一方向；用户明确认可后才推进下一方向。历史站姿提取和旧版图集识别不代表美术认可。

七个已认可方向与当前右上 r1 均为站姿＋八张步行关键姿势，编号 00–08，与旧版 00–24 不同。右上以左上 r6 同号完整姿势为参照绘制对应视角，保留相位、脚距、膝踝关系与摆臂，并核对 03–06 和循环接缝。右上尚未认可，最终分层模板、固定侧装备挂点与正式安装包未更新。

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
