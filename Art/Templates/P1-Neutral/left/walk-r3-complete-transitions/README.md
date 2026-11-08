# P1 向左共同底模 r3 · 隐藏连接与起停过渡

从用户已认可展示外观与循环的 r2 另存；原 r2 九张合成画面保持逐 RGBA 一致。新姿势与隐藏连接的美术认可仍为空，不沿用 r2 的认可。

本包共13姿势：idle00、walk01–08、walk-start01–02、walk-stop01–02。源图使用完整1254²画布固定缩放0.194、平移(4.72,6.4)注册至256²，不按透明边界调整比例。头部复用同一原画，沿已认可的颈根小幅摆动；五官和发型需使用各姿势的同一个 headToCanvas 矩阵。

八个公共槽分别为躯干、头、双臂、双手和双腿。近侧是角色左侧，远侧是角色右侧。隐藏补片在同槽原可见像素之前绘制，随后仍依照公共 drawOrder 合成，不增加外观专用代码或切换身体。

起步的指定路径为 idle00 → walk-start01 → walk-start02 → walk01；停步为 walk08 → walk-stop01 → walk-stop02 → idle00。每张动作120ms；展示动图首末站姿各停480ms。这是画好的两条衔接路径，不代表从任意行走相位中断均已完成。

重导：

```sh
python3 scripts/export-neutral-left-walk.py Art/Templates/P1-Neutral/left/walk-r3-complete-transitions --review Art/Review/P1/neutral-left-complete-transitions-v1
python3 Art/Review/P1/neutral-left-complete-transitions-v1/verify.py
```

source/保留原始生成稿、固定作者归属、隐藏连接及 r2 认可画面的对照拷贝；editable/保留13份ORA和13份SVG，layers/保存公共分槽PNG。原始生成提示词见 source/transition-generation-prompts.json，独立过渡作者稿在相邻 start-stop-v1/目录。

仅为向左底模与动作候选。本方向独立发型、五官、两套衣物、背负武器及其他方向后续制作；未接入App、未运行模拟器或设备、未打包IPA。实际校验与美术复核见本目录 validation.json 和对应审核目录。
