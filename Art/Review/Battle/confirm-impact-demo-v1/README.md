# build50 确认停骰与击打点数字

悬停时骰子继续翻动，点击确认技能时立即停在本次原GameCore掷骰结果面并显示点数，随后保持到命中后淡出；取消原来的“命中后再减速停骰”。确认只在隔离事务中求值一次，活跃HP/AP/次数/库存/RNG/历史仍到实际命中提交，没有提前扣血或第二次掷骰；取消丢弃，状态被外部修改则拒绝旧事务。固定加值方块仅保留色块和数值，下方字幕全部移除。伤害/格挡数字改在怪物身体或玩家/盾面实际击打点居中出现，再轻微上浮，回血浮字保持独立位置。单人原定值演练同步方块无字幕与击打点数字。怪物显示使用当前演练目录，保留本地训练模板的真实骰型。

长期标准已写入Art/Standards/BattleHealing-v1/README.md并加入AGENTS：恢复技能越强，光带越粗、光核/粒子/地面染光与收尾层次越华丽；强度来自技能本身，不随悬停增加、不新增蓄力层级。本轮记录标准，不声称已将所有恢复技能重新分级制作。

| 正常速度动图 | 审核范围 |
| --- | --- |
| [突袭确认与命中](ambush-normal.gif) | 220帧/4.4秒，多骰确认停稳、原时点伤害、自疗回位 |
| [普通攻击与反击](attack-buff-normal.gif) | 300帧/6秒，固定增伤无字幕、双方击打点数字 |
| [致死与数字同事件](lethal-normal.gif) | 190帧/3.8秒，目标预设3HP，仅用于致死审核 |

[完整站姿](ambush-standing.png) · [已停骰但尚未扣血](ambush-dash.png) · [突袭命中数字](ambush-impact.png) · [普通命中数字](attack-buff-impact.png) · [致死数字](lethal-impact.png) · [完整人物1×](actor-body-1x.png) · [2×](actor-body-2x.png) · [完整场景1×](whole-world-1x.png) · [2×](whole-world-2x.png) · [确认/命中时间证据](confirmation-trace.json)

主线程独自审核25页710实际GIF解码帧，六完整人物和六全场各1×/2×共四板。正常50fps/每帧20ms，生产Swift与原规则回执驱动的离线合成，字体/混合/地图/光照/UI近似；静态序列不称连续播放或UIKit/实机录屏。[审核](review.json) · [保留](preservation.json)。新美术认可null。

源码`a47f5d1ccf852337a784e3373e42a655ce1b2e54`、设备Release [40272222309](https://github.com/liamchan-rgb/experiment/actions/runs/40272222309)，97纯规则/适配/几何/事务测试与五旧纯Swift检查通过。Mac/Linux1190小队帧/3570请求/1500骰子与怪物帧/360公式图库在1e-6内一致，只有acted集合按无序比较。原10814美术/资源路径、13原核心/清单摘要与单人模型/时钟前缀保持。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b50.ipa) · [包记录](../../../../Media/Build50/package.json)，1.6.24/build50，31,878,612字节，SHA256 `ee3e6dcd9c253a374ed117aa2aeabe294cfbe68dabbbf432c28a8f9041c05cc9`。经典ZIP2.0/CRC/arm64/资源与权限已核。无App/模拟器/实机运行，安装、操作与实际FPS由用户测试。入口：林地战斗→小队支援。

公开交付：10个完整GET200，96选定路径/246编译输入摘要匹配。[回执](delivery.json)。浏览器动图直链：

[ambush](https://cdn.jsdelivr.net/gh/liamchan-rgb/experiment@4858744e4dbcc24b9e9144ad38c71e3adbd4767f/Art/Review/Battle/confirm-impact-demo-v1/ambush-normal.gif)

[attack-buff](https://cdn.jsdelivr.net/gh/liamchan-rgb/experiment@4858744e4dbcc24b9e9144ad38c71e3adbd4767f/Art/Review/Battle/confirm-impact-demo-v1/attack-buff-normal.gif)

[lethal](https://cdn.jsdelivr.net/gh/liamchan-rgb/experiment@4858744e4dbcc24b9e9144ad38c71e3adbd4767f/Art/Review/Battle/confirm-impact-demo-v1/lethal-normal.gif)

[固定提交直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/4858744e4dbcc24b9e9144ad38c71e3adbd4767f/Downloads/MeadowJourney-b50.ipa)
