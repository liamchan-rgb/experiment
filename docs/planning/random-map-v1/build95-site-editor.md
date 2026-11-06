## Build95交付 · 服务参数编辑与桌游demo对接核查（2026-11-06）

地图→编辑地点→营地/空地，设置商店/失物/清泉，营地保留商店。买卖价10—500%（100%原目录价、整数最低1），失物金币1—1000，清泉恢复1—100；最终卖价不得高于可购商品买价。字段常驻名称，取消不写入，失败保留草稿可重试，已处理事件显示只读配置且不能重置/改类型。编辑不发奖、不改个人HP/AP/库存/RNG/道路；移动/战斗/结算后拒绝。报价、确认和实际交易使用同一份保存配置；事件收益也读取该配置。可选siteConfiguration缺省保持旧SITES1和原价5金币/4回复；校验拒绝非法或套利导入，不改全局目录。

Linux/Mac完整296项零失败，新增6项覆盖改价实际扣款/卖价与续档、事件类型/金币保存与处理后锁定、清泉配置封顶、范围/营地类型/套利导入拒绝、保存失败回滚重试、旧nil配置与暂停道路编辑拒绝。四专项/项目绑定/语法/设备Release通过。原27+27+24固定策略在Mac重跑并断言完整集合，与Build94保留参考逐字段相同（距离<1e−8）；未宣称本轮Linux重跑78整程或参数经济已平衡。

随后只读核查classroom-boardgame main 1e9100c4c18364ea64b3ec974fe957ba4ef42f6f及战斗分支a0427b83d9233f1a83178b3c47d3fab39eed664e，确认TeacherHost/PPT/独立公开窗口、PVEAppSession/PresentationLedger/PublicPlayFrame可作入口，两分支关键会话/公开协议相同。推荐原demo为主壳，Meadow先作公开帧只读画面适配：规则/保存/AI/计时仅一处负责；已提交回执不得再次prepare/apply/commit或重掷，教师私有信息不投影。双人默认场景先验证，1—6学生+主持人、任意ID、公开外观数据、存档/撤销及移动规则模式需逐项适配。原UPSTREAM指纹是历史来源，当前Core已分叉，不能直接覆盖。方案与审计见docs/integration/tabletop-demo-bridge-plan.md和tabletop-demo-audit.json。本轮未改/未编译/未运行桌游demo，不声称真实对接完成。

最终1.6.68/build95，源码175c7dfc4a68e62cb9693da8d837b77081619a6b，run 42265928750 attempt1。IPA CRC/ZIP2.0无extra/arm64及755/版本平台/Metal头/12图集6数据集通过；源资源569份SHA256匹配，原地图/步态/规则JSON字节同Build94，系统assetutil解析288条。实际SDK/编译目录摘要另记，无新美术或美术认可，缺图继续标注。未运行App/模拟器/实机。

直接IPA完整公开GET200，64792405字节，SHA256 2d1ae3f9abe0fec4ac63202b37e1ed11b37ac1f0b636698c9f30328b196ef8e3；[下载](https://raw.githubusercontent.com/liamchan-rgb/experiment/ac9d4cb0d2e2c3385d5d535a2bec2a2d3d0ca6b2/Downloads/MeadowJourney-b95.ipa)。来源/日志/包检Media/Build95，设备体验由用户验收。

后两项：PublicPlayFrame只读画面适配样例；验证后在桌游新分支接入公开画面开关与原功能回退。

## Build95候选 · 地点服务参数编辑与桌游对接核查（2026-11-06）

编辑地点后选营地/空地：营地保留商店，未处理空地可在商店/失物/清泉间切换；买卖价格比例10—500%、失物金币1—1000、清泉恢复1—100。100%指原目录价，整数价最低1，最终卖价不得高于可购商品买价。字段有常驻名称，保存失败保留草稿可重试，取消不写入。已处理事件只读查看且不能重置，编辑不发奖/不改HP/AP/库存/RNG/道路坐标；移动、战斗、结算后拒绝。新可选siteConfiguration仅在明确保存时写入，旧nil配置完全沿用SITES1和原价5金币/4回复；报价与实际扣款读取同一函数，事件数值也读保存配置。恶意导入的非法/套利配置也拒绝。

Linux完整296测试通过，新增6项覆盖改价实际交易/续档、事件类型与金币持久/处理后锁定、清泉配置封顶、非法比例/营地类型/导入套利拒绝、保存失败回滚重试、旧nil配置/暂停道路禁编辑。四原专项、项目/语法检查通过；设备Release、原78固定策略及IPA/公开GET待完成。原数值/资源/美术复用，无App/模拟器/实机运行。

随后只读核查桌游main及战斗分支现有demo，确认TeacherHost/PPT/独立公开窗口、PVEAppSession/PresentationLedger/PublicPlayFrame入口。建议以原demo为主壳，先做公开帧只读渲染适配，保留单一规则/保存/计时权威，避免双重结算。两库Core已分叉，原UPSTREAM指纹仅历史，不能直接覆盖存档/主程序。详见docs/integration/tabletop-demo-bridge-plan.md与审计JSON；本轮未改桌游仓库或实现真实对接。

候选1.6.68/build95。美术缺口按原约定只标注，不阻塞。后两项：PublicPlayFrame只读画面适配样例；验证后在桌游新分支接入公开画面开关与原功能回退。
