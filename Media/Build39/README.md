# Build39 · 新分层八向人物接入

1.6.13 build39，将统一八向中性身体/独立部件烘焙到demo，同步前景、足点与Metal阴影。点“P1 衣装”选“林间绿衣”或“行旅蓝衣”，保留当前路线/朝向/步相；起步与收步沿各向专用帧。

停步当前会在原地播放完到指定出口的循环尾部，再收脚；没有新绘任意相位制动动作。步态测试仍可看八方向/单步；战斗保持此前版本，不在此轮重画。

源码与归档见 [package.json](package.json)，实际导入图集/生产控制器trace的正常速度 [起停GIF](../../Art/Review/P1/modular-demo-v1/demo-eight-way-start-stop-120ms.gif)、[切向GIF](../../Art/Review/P1/modular-demo-v1/demo-turn-120ms.gif)、[站姿](../../Art/Review/P1/modular-demo-v1/demo-idle-2x.png)。这些是离线资源预览；设备运行/截图由用户完成。

设备Release归档及纯逻辑检查通过，未运行模拟器或物理设备。安装包沿用已有SideStore重签方式，交付 [直接IPA](../../Downloads/MeadowJourney-b39.ipa)，不交付外层artifact ZIP。主线程审核详见 [art-review.md](../../Art/Review/P1/modular-demo-v1/art-review.md)。
