# 训练短剑 · 八方向装备/空背

训练短剑trainingSword正式物品ID绑定既有背剑部件、战斗剑层和原图标。两衣装×八方向×13姿势=208带剑格逐像素保持，新增208空槽格由相同身体/motion/逐帧层序装配。现有P1菜单新增武器选择，探索态原.equip命令处理装备/卸下和背包数量；地图前景与Metal投影同选型，保持路线/朝向/步相/脚点，战斗人物/接地阴影/残影同武器层。小队新演练读取装备快照；单人旧练习同步可见武器与空手禁用普攻。装备短剑普攻仍1D6，战斗中不能换装。

[正常行走](walk-normal.gif)：8×120ms=0.96秒循环；[起步/收步](transitions-normal.gif)：站姿+2起步+8步相+2收步，共13×120ms=1.56秒。原八方向入口/出口保持。四行分别林间绿衣背剑/空背、行旅蓝衣背剑/空背；[完整站姿](standing.png)。32张1×/2×原尺寸板覆盖16组完整13姿势，主线程亲看416整身及21实际GIF解码帧/两页；静态序列审核，不冒称连续播放或App运行。

[正式itemID/部件/战斗/图标绑定](../../../Integration/Equipment-training-sword-v1/binding.json) · [208格逐像素与空槽记录](../../../Integration/Equipment-training-sword-v1/walking-bindings.json) · [战斗演出审核](../../Battle/training-sword-smooth-demo-v1/README.md) · [审核记录](review.json)。全部既有源画稿、body/motion/脚点保持，新认可null；复用既有候选不算重画新剑/新身体。
