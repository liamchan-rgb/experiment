# 三档治疗特效 · Build 69 审核

[正常速度全场动画 GIF](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Art/Review/Battle/healing-effects-v1/healing-tiers-normal.gif) · [三档峰值并排对照](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Art/Review/Battle/healing-effects-v1/healing-three-tiers-peak-overview.jpg) · [治疗素材源包](../../../../Parts/BattleVFX/healing-v1/README.md)

动图按顺序演示实际恢复 3 HP 的微量、6 HP 的标准、11 HP 的强效治疗。每档 118 帧，20ms／帧，三档总计 354 帧、7.08 秒；逐帧解码确认所有时长均为 20ms。

使用用户交付的 5×4 RGBA 图集原帧，没有重绘或裁切掉透明画布。微量、标准、强效按真实恢复量（已应用最大 HP 上限）分类，0 恢复不触发。应用用 60Hz 显示时钟淡化相邻 20fps 美术帧，绿色环境光／脚底光环随档位增强，并按各自图集修正脚底锚点。

本图是原战斗场景／人物／UI示意与 GameCore 实际回执的离线美术复核，不是 UIKit、模拟器或实机录屏。素材逐帧对照源 ZIP 与 App 图集一致；动画外观由主线程检查。实机效果待用户安装验收。

IPA：`Downloads/MeadowJourney-b69.ipa` · 1.6.43 / build69 · 无签名设备 Release 包。
