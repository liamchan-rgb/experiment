# 右下中性动作模组 r1 · 待用户审核

[正常行走](walk-120ms.gif) · [正常起停](start-stop-120ms.gif) · [全身站姿](idle-review-2x.png) · [左右站姿对照](idle-comparison-2x.png) · [左右正常步态对照](walk-comparison-120ms.gif) · [全部13姿势1×](all-poses-fullbody-1x.png) · [全部13姿势2×](all-poses-fullbody-2x.png) · [主线程复核](art-review.md) · [技术检查](validation.json) · [重导](reexport-validation.json)

基于用户认可左下r1逐层反射，转换左右语义、关节/脚底/支撑脚和头部局部坐标，保持原步相、裤口跟随和8×120ms时序；左下完整保持。头顶及身体高光校回固定左上方向。新右下不继承左下的美术认可。

00站姿，01–08行走，09–10起步，11–12收步。起停预览22帧：首尾站姿480ms，其余20帧120ms，展示两帧起步、两个正常行走循环和两帧收步；不是慢放。当前只含中性底模，没有制作独立外观或接入App。

13张实际公共装配器图与导出完全一致，104层alpha精确匹配源反射，13次头部局部挂载RGBA匹配，左右/脚底/支撑/层序正确；关节透明缺口0、26次整臂分区一致、近手全保留、短裤8张行走独立变化。6019份旧文件保持。源/重导/发布回执详见JSON，HTTPS发布后写delivery.json。

主线程亲自检查完整1×/2×全部13姿势与帧序。查看器只能显示静帧，不声称连续播放器验收；本轮没有智能体、App、模拟器、实机或IPA工作。

美术提交 `a950fb0b635bf6c1312572942702a699a07983eb`。三份HTTPS文件均已实测HTTP200、MIME及SHA256/本地字节一致；GIF帧数、120ms帧速与起停停留时长符合登记。[正常行走直链](https://raw.githubusercontent.com/liamchan-rgb/experiment/a950fb0b635bf6c1312572942702a699a07983eb/Art/Review/P1/neutral-down-right-r1-mirror/walk-120ms.gif)；完整回执见[delivery.json](delivery.json)。386份重导文件逐字节一致。
