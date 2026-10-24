# Wayfarer blue split coat · down-only candidate

第二衣型为蓝色长款分片外套，与Forester短上衣使用同一份r6人体、同一动作和同一装配器。袖子与空手摆臂共用肩部变换；左右长衣摆有独立小幅摆动。屏幕右衣摆向内收，避免与固定背剑鞘尾的镶边相切。头发、五官与背剑均为独立已有资源。

生成原稿、提示词与参考记录保存在source/；完整1254²源稿按固定仿射注册到256²，不按alpha外接框缩放。authoring.json记录源锚点、分层边界、服装underlap和衣摆/袖子变换。source/shared-lower保留共享裤靴原像素，patterns沿用已验证的服装隐藏重叠区；这些是服装部件，不是替换人体。高不透明度alpha>=250统一为255，身体文件不作任何修改。

重导：`python3 scripts/export-wayfarer-coat-v1.py Art/Parts/P1-v1/outfit-wayfarer-coat-v1`。包含9姿势×8部件、分层ORA/SVG和普通pose-map清单，现有装配器无外观专用代码。

完整组合与正常速度全身GIF见Art/Review/P1/modular-down-second-outfit-v1/。当前仅向下候选，用户美术认可为空；不代表其他方向或App接入完成。
