# P1 向左独立外观 v1

在同一份用户已认可展示的左向r3人体与13姿势上，完成三发型、两五官、Forester绿短上衣、Wayfarer蓝长外套、共用灰裤棕靴和独立背剑。当前为内部复核后提交的新外观候选，用户美术认可为空。

## 查看

- [两衣型正常行走GIF](../../../../Review/P1/modular-left-wardrobe-v1/outfits-comparison-120ms.gif)：8帧×120ms。
- [有过渡关键姿势的起停GIF](../../../../Review/P1/modular-left-wardrobe-v1/start-stop-comparison-120ms.gif)：22帧，首末站姿各480ms，其余20帧120ms。
- [整身站姿](../../../../Review/P1/modular-left-wardrobe-v1/outfits-comparison-2x.png)、[主审核记录](../../../../Review/P1/modular-left-wardrobe-v1/art-review.md)、[技术证据](../../../../Review/P1/modular-left-wardrobe-v1/checks.json)。



## 制作与复用

原始部件与导出图片分别记录：三发型、两组五官在每个方向内共享局部PNG，由原头部矩阵带动；背剑一图绑定13姿势；会变形的衣袖、裤腿、靴子和衣摆按共同身体导板作者变形，再导出普通pose-map PNG。保留imagegen原稿、提示词、作者注册、透明PNG、分层ORA与SVG；不使用运行时骨骼系统，不逐外观增加引擎分支。

motion.json仅在原body.drawOrder中插入独立外观槽位，原身体槽相对顺序、关节、脚底、头部矩阵与姿势键不变。裤装在body.torso安全短裤之后，近侧袖口在近侧手之前。base-invariance.json保存原身体/动作/公共compositor摘要；13姿势裸身合成与原帧逐像素一致，不为衣物遮挡擦除或替换身体。

## 验证与边界

实际compositor检查72组合×13姿势=936图；3120项穿衣身体贡献检查没有>5%漏盖（只允许原领口的解剖颈部开口）；468组背剑切换无武器轮廓外/不透明手部变化；去头发/五官/武器后的26整身姿势无颈下衣物孤立色块。10清单通过；264份PNG/ORA/SVG连续两轮由保留原稿重导字节一致；26合同和21装配器回归通过。重现入口：`python Art/Review/P1/modular-left-wardrobe-v1/verify.py`。

当前只覆盖left的idle00、walk01–08、walk-start01–02、walk-stop01–02。起停展示只覆盖idle00→walk01与walk08→idle00两条已有作者路径，不代表任意步相中断、其他方向或完整隐藏解剖。没有App/设备接入、模拟器运行或IPA交付。新外观须由用户审核后再进入下一方向。
