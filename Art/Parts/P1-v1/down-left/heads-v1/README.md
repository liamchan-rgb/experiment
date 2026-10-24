# 左下独立头部外观 v1 · 待用户审核

四个head-local资源包：棕色短发、银灰短发、蓝眼五官、琥珀眼五官。两发型×两五官共4组合，使用同一已认可左下r1中性身体与13姿势；五官不含脸皮/耳/颈/头形，头发不含皮肤或五官。

每包自带原始imagegen源、准确提示词、明确登记数据、独立PNG/ORA/SVG与公共清单。眉/眼/鼻/嘴分别独立；从明确源部件按固定导板登记，细线采用固定采样相位，所有动作复用同一局部96px图片，不逐帧生成脸，也不按外观换身体或拟合。

主线程修掉早期眉眼间距、棕发远眼角遮挡和嘴线漏采。棕发刘海由imagegen单独修短，原失败源/整身诊断保留。银发中央V形分缝是露额发际线，头顶与后侧应覆盖的头皮保持覆盖；不能把这处有意露额当作头顶透明孔。

共同profile只增加down-left头部导板数据，其余字段不变。原身体、headToCanvas、四肢关节/脚底/支撑及步态保持；新展示模板只扩展drawOrder加入外观层。公共compositor和contract代码不变，未增加外观ID分支。

重现：`python scripts/reexport-down-left-heads.py`。本轮head-local四包与52张真实装配检查完成；不等于右下头部、衣物、背剑、完整隐藏人体或App验收。新美术无用户认可。

[正常行走](../../../../Review/P1/modular-down-left-heads-v1/walk-comparison-120ms.gif) · [正常起停](../../../../Review/P1/modular-down-left-heads-v1/start-stop-comparison-120ms.gif) · [全身站姿](../../../../Review/P1/modular-down-left-heads-v1/idle-comparison-2x.png) · [具体复核](../../../../Review/P1/modular-down-left-heads-v1/art-review.md)
