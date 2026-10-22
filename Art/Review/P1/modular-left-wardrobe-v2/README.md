# 向左衣物返修 v2

用户判退v1后的独立候选，主线程负责修正与整合，没有把智能体通过结论沿用为美术通过。当前仍是向左这一方向，用户认可为空。

[正常行走GIF](outfits-comparison-120ms.gif) · [正常起停GIF](start-stop-comparison-120ms.gif) · [站姿](outfits-comparison-2x.png) · [绿衣13姿势](thirteen-poses-fullbody-1x.png) · [蓝衣13姿势](wayfarer-thirteen-poses-fullbody-1x.png) · [六组头部全身](head-combinations-fullbody-1x.png)

行走8帧×120ms；起停22帧，首末idle各480ms，其余20帧120ms。只覆盖原r3已经绘制的idle00→walk01和walk08→idle00路径，不扩大为任意步相起停。

[主线程复核与返修依据](art-review.md)、[全部实际合成证据](audit.json)、[原稿重导/清单/时长核对](checks.json)、[衣物源稿及导出](../../../Parts/P1-v1/left/wardrobe-repair-v2/README.md)。verify.py可重导三包、检查十清单并调用实际compositor复核；技术检查不代替美术审阅。浏览器交付链接在发布实测后记入delivery.json。
