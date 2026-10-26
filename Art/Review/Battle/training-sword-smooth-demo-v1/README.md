# build52 训练短剑与连续停骰

训练短剑trainingSword正式物品ID绑定既有背剑部件、战斗剑层和原图标。两衣装×八方向×13姿势=208带剑格逐像素保持，新增208空槽格由相同身体/motion/逐帧层序装配。现有P1菜单新增武器选择，探索态原.equip命令处理装备/卸下和背包数量；地图前景与Metal投影同选型，保持路线/朝向/步相/脚点，战斗人物/接地阴影/残影同武器层。小队新演练读取装备快照；单人旧练习同步可见武器与空手禁用普攻。装备短剑普攻仍1D6，战斗中不能换装。

确认技能逻辑仍一次锁定原核心结果，但视觉从点击时的真实旋转姿态和浮动连续减速，在0.32秒内转正结果面；不再直接跳停，也不等命中后才开始转正。数字固定在骰面，无下方重复字幕；固定加值选中即显，HP/AP/RNG/历史仍到命中才提交，命中只启动淡出而不重置落面。黄色菱形AP、HP0/伤害数字/右吹死亡/血条隐藏同事件、双螺旋与圆盾保留。

[突袭与连续停骰](ambush-normal.gif) · [空手P1援护](unarmed-normal.gif) · [致死同步隐条](lethal-normal.gif)。正常20ms/帧，分别220/190/190帧，共600帧；主线程亲看22页全部实际解码帧。

[完整站姿](ambush-standing.png) · [空手画面](unarmed-selected.png) · [连续停骰全场时序](smooth-stop-timeline.png) · [原始确认时序](smooth-confirmation-trace.json) · [六完整身体1×](actor-body-1x.png) · [2×](actor-body-2x.png) · [六全场1×](whole-world-1x.png) · [2×](whole-world-2x.png) · [六clip/36武器开关整身1×](battle-equipment-1x.png) · [2×](battle-equipment-2x.png) · [八向装备行走](../../P1/training-sword-v1/README.md)。主线程另看全场停骰六时点及以上整身板，未仅查骰子放大局部。

生产Swift/原规则回执驱动的离线合成；字体/混合/地图/光照/UI近似，非UIKit/实机/连续播放或测得60FPS。[审核](review.json) · [保留](preservation.json)。新认可null。

源码`0da70730b77038c9eb08c6eee4dd521ebca3b311`；[设备Release40281675931](https://github.com/liamchan-rgb/experiment/actions/runs/40281675931)成功，103纯测试（原98+装备3+连续落面2）和五旧纯Swift检查通过。Mac/Linux1190小队帧/3570请求/1690骰子与怪物帧/360公式图库在1e-6内逐字段一致，面数组仍按绘制顺序比较，只有acted集合按无序。原10814资源/美术路径中10813字节保持；hero-gait.json仅新增装备映射，删除新增字段后与旧JSON完全相同。原13核心/目录摘要、身体/动作/脚点/已存在人物PNG保持。

IPA1.6.26/build52，32,901,808字节，SHA256 `5c1bf5b2c1053cbabc05c9c168797f8f08fdf99db5982ab333052b7147eb767c`。[包记录](../../../../Media/Build52/package.json) · [直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b52.ipa)。无App/模拟器/实机，安装/实际表现由用户测试。

使用：地图顶部P1 · 短剑/空手→武器→装备训练短剑/卸下；衣装仍在同一菜单。随后林地战斗→小队支援读取本次装备。此为会话内受控装备体验，不包含完整背包、商店/存档或其他装备。
