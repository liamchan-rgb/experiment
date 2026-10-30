# build46 小队支援集成候选

范围B0/B1。入口：林地战斗 → 左上“小队支援”。保留原单人演练，新的全幅小队场景复用两个P1身体与两只鹿灵，非游侠新皮肤/正式六怪完成。既有角色、行走、场景原画像素未改。

固定来源与适配边界见Vendor/ClassroomGameCore/UPSTREAM.json。原桌游仓库只读；原Sources/catalog与72测试不改，SPM最低iOS15适配及独立MeadowBattleSupport模块。内存仅新增训练鹿灵模板。preview不扣值，prepare记录意图，视觉命中时commit/apply一次；取消不扣，重放不重复。援护/振奋/四消耗救援与冒险者旧三技能读原规则/AP/次数/库存/盾max/buff轮数/救援下轮限制。旧单人固定伤害/叠盾演练另保留，不混称已变正式规则。

援护弧流/目标绿金回血成盾，振奋上升金粒和短箭形光波、节点队友分别表现；持久状态留方框，可hover/focus/触屏查看。药水用旧图标原字节和既有恢复/盾；复活保留既有低身defeat并反向起身。人物死亡不采用怪物消散。怪物HP0/数字/右吹同事件；带盾目标前沿接触按真实圆盾注册。无新增蓄力或运镜。

最终源码cf245fe98d2234941423e487bacc8be0f67685be，CI40212372613通过79纯规则/适配测试、既有五项检查、iPhoneOS Release归档。正常五GIF/整身审核/包/下载回执见Art/Review/Battle/party-support-demo-v1与Media/Build46。目标60，整场支援打开时原地图停渲染。无App/模拟器/实机执行，实际安装/交互/FPS待用户，artApproval=null；完整桌游UI/存档/装备和B2之后未算完成。
