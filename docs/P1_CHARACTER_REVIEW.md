# P1 人物素材逐张审核

开始日期：2026-10-18。用户要求 P1 原始素材按方向逐张审核，修改后确认再推进下一张，最终以认可结果建立支持换装备、自定义人物的人物模板。

## 当前审核

**八方向步态已获用户认可；当前审核向下方向的分层换装小样 v1。**

用户确认“可以的，我们走路的方向动画都调好了”，右上 r1 的认可已记录。已认可动作冻结为 `Art/Templates/P1-Motion-v1.json`，共八方向、每方向站姿＋八帧。用户随后以“按你说的来”授权先做向下方向换装验证；这个授权不等于新外观美术认可。

- [在线换装预览（iPad）](https://p1-character-atelier.smokytide.chatgpt.site)
- [向下换装小样说明与源文件](../Art/Templates/P1-Down/v1/README.md) · [离线交互预览（下载后打开）](../Art/Templates/P1-Down/v1/preview.html)
- [原动作／银发游侠持剑同步循环](../Art/Templates/P1-Down/v1/review/walk-compare.gif) · [慢速](../Art/Templates/P1-Down/v1/review/walk-compare-slow.gif) · [九帧对照](../Art/Templates/P1-Down/v1/review/comparison.png)
- [小样验证记录](../Art/Templates/P1-Down/v1/validation.json) · [八方向动作锁定清单](../Art/Templates/P1-Motion-v1.json)
- [右上 r1 认可](../Art/Review/P1/directions/up-right/revisions/r1/approval.json) · [完整审核状态](../Art/Review/P1/review.json)

当前小样含两种头发、两种面部、两套同袖型上衣及短剑／空手，共 16 种搭配，提供透明部件、逐帧关节／挂点、18 份 ORA 与 18 份分组 SVG、图集和逐帧预览。默认搭配可见像素还原已认可向下原图，腿脚不随外观变化。只提交向下方向小样审核，不将它扩大为八方向分层完成或新外观已认可。右上旧预览中的 REVIEW 标签保留其提交时历史状态。

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
| 08 | 右上 ↗ | [r1 横条](../Art/Review/P1/directions/up-right/revisions/r1/strip.png) | [r1 预览](../Art/Review/P1/directions/up-right/revisions/r1/review-2x.png) | r1 用户已认可 |

每次只提交当前方向。收到反馈后按帧编号另存修改版本，记录具体意见与依据，再提交同一方向；用户明确认可后才推进下一方向。历史站姿提取和旧版图集识别不代表美术认可。

八个已认可方向均为站姿＋八张步行关键姿势，编号 00–08，与旧版 00–24 不同。右上以左上 r6 同号完整姿势为参照绘制对应视角，保留相位、脚距、膝踝关系与摆臂。当前只有向下方向进行了分层换装试验，其余七方向、正式运行资源与安装包尚未接入。

## 现有资源与问题依据

P1 原始素材有两张 4 × 4 图：`hero1-gait-v1.2.png` 和 `hero1-diagonal-v1.3.png`。当前 `scripts/prepare-gait-assets.py` 的 `legacy_rows()` 只选择每方向第一列站姿，裁切腿部生成每方向 24 张步行帧；其余原始行走姿势并未直接用于正式动画。运行时右侧面还采用左侧面的完整镜像。因而这次需要重新审核原始姿势、修改依据和最终动态，不能把既有自动生成结果视为通过。

以用户确认的完整图集为素材来源，按方向切片审核，结合帧编号定位修改；审核顺序和下一项由当前项的实际进展更新。动作仍需逐帧与连续播放检查，特别是承重、摆腿、两次过腿、鞋尖朝向及鞋腿接缝。

## 人物模板目标（向下小样已制作，待审核）

- 统一八方向的身体比例、观察角度、画布、地面线与左右肢体命名。
- 分离身体、头发、服装、手、腿、左右鞋和装备，明确被衣物遮住的身体所需补画，保留可编辑源文件。
- 记录髋、膝、踝和装备挂点，区分角色自身左右与画面左右；替换部件需遵守同一挂点和尺寸约定。
- 每张姿势记录脚底接触、抬脚、前后遮挡和部件绘制顺序；前景与阴影共用确认过的姿势。
- 用确认后的 P1 建立模板 v1，再验证至少一次装备替换和人物外观替换，之后扩展其他人物。

以上是完整模板要求。当前向下小样验证了预制外观替换、挂点与图集输出，完整隐藏肢体、任意衣型和其他七方向仍需补齐。换装小样尚未获美术认可；运行时接入另行实施。

## 同方向完整动作横图参考

用户询问此前看到的一张很宽、包含一个方向所有动作的图。现提供 [P1 向下完整步态横图](../Art/Review/P1/reference-down-build28-strip.png)，尺寸 6400 × 256，最左格为站姿，随后 24 格是行走帧 01–24。

该图按原像素提取自 build 28 正式 `Hero1Directions.png` 第一行，逐像素核对一致。用户随后明确这不是要找的图，最终确认的是上方所列的完整四方向图集。此单行保留作历史参考，不作为当前审核对象。
