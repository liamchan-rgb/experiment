# build49 · 突袭与交叉上升回血候选

突袭已接入游侠技能栏：按原规则2AP、每场2次，伤害2D8＋2、自身恢复3。演出为预备→快速突进/三道淡残影→双斩痕/受击局部爆光与落地光粒→回位；两道斩痕仅一次原核心结算，目标受击与施法者回血分开注册。最后敌人死亡时仍完成本人回血与回位，满血不额外触发回血光效。原身体/攻击姿势重定时复用，不声称重绘人物或已完成八件装备。

回血绿光改为两股相差半周的连续上升螺旋，绕完整人物的前后深度交替，后半由身体遮挡；星点沿同一轨道连续上升，减弱原静态长光柱/亮核，保留恢复亮点、局部地面绿光和渐隐尾光。前后光带与圆盾直接挂同一人物父节点，回位中同步移动。单人/小队的治疗与药水均复用新效果。

固定加值、增伤、恢复、授盾和复活值在选中时即显示，不再等待命中才从问号变化；随机骰仍由原回执决定结果。动画不再显示D6/D8等骰型文字，落定读数只显示结果；技能卡的公式说明保留。根线程全场检查发现P2四/五通道回位后挤到P1生命条，已按整组实际半宽调整锚点，并复核前冲末端与敌生命条间距。

| 正常速度动图 | 范围 |
| --- | --- |
| [突袭](ambush-normal.gif) | 220帧 / 4.4秒，默认两只18HP敌人的实际规则样片 |
| [带增伤的最后一击与自疗](ambush-last-normal.gif) | 220帧 / 4.4秒，预设残局M2已败、M1为3HP、P2已有振奋2；不是默认开局 |
| [单独回血](heal-normal.gif) | 190帧 / 3.8秒，以大药水名义恢复12、实际受上限恢复6的旧规则展示双螺旋 |
| [援护](support-normal.gif) | 190帧 / 3.8秒，选中即显恢复6/盾4、目标双螺旋与圆盾 |

[完整站姿](ambush-standing.png) · [固定值选中即显](ambush-selected.png) · [突进残影](ambush-dash.png) · [命中](ambush-impact.png) · [回位自疗](ambush-recovery.png) · [绿光螺旋](heal-dash.png) · [五通道与致死自疗](ambush-last-recovery.png) · [完整人物1×](actor-body-1x.png) · [2×](actor-body-2x.png) · [完整场景1×](whole-world-1x.png) · [2×](whole-world-2x.png)

主线程独自修复并亲看四正常50fpsGIF共820实际解码帧/30页、六完整人物和六全场姿势各1×/2×。这是真实生产Swift轨迹/几何与原GameCore回执驱动的离线合成，字体/光照/混合/地图/UI近似，静态解码检查不称连续播放或UIKit/实机录屏；实际浮字与输入由App执行，离线HUD为近似。每帧20ms，非设备60FPS证据。首稿透明合成错误（仅预览工具）及多通道压血条分别保留[drafts](drafts)。[审核](review.json) · [保留核对](preservation.json)。新美术认可null。

最终源码`a5547de7ad20b5737443960bacc89d80f52ee2eb`，设备Release [40268729691](https://github.com/liamchan-rgb/experiment/actions/runs/40268729691)通过94规则/适配/几何测试及五项旧纯Swift检查。Mac/Linux1190小队帧、3570请求、1500骰子/怪物/突袭帧与360公式图库逐字段比较在1e-6内一致，仅acted集合无序。双链镜像深度/连续性由生产纯数学检查覆盖；4500离线光场样本不是实机捕获。

IPA1.6.23/build49，31,878,244字节，SHA256 `c4dae118ee027eb2c6e595ad34bede6bd734f84ddb65b05a09f844cdc2d1d65d`，经典ZIP2.0/CRC/arm64/权限/资源/Metal/原目录校验通过。[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b49.ipa) · [包记录](../../../../Media/Build49/package.json)。入口：林地战斗→左上小队支援→P2突袭。无App/模拟器/实机执行，安装、操作及稳定60FPS由用户反馈。

B2本轮仅突袭候选；基础装备下一件为训练短剑itemID与完整挂载，再猎弓/重剑/权杖/两甲/两饰品。B3—B6未因本轮公式图库而完成。
