# build46 小队支援 · B0/B1候选

入口：林地战斗 → 左上“小队支援”；“返回单人”保留原演练。

已接原桌游GameCore固定快照的预览/一次结算、2玩家/2敌目标、HP/盾条、AP/库存/次数与buff方框详情。本批：援护、振奋、小治疗药水、大治疗药水、护盾药水、复活石；复用冒险者三技能。原授盾max、增益轮数、救援2AP/半血/下轮行动均由原核心执行。源19技能/18物品保持，不代表所有演出或完整背包装备完成。

| 正常速度预览 | 帧数 | 时长 |
|---|---:|---:|
| [援护](support-normal.gif) | 160 | 3.2s |
| [振奋](rally-normal.gif) | 160 | 3.2s |
| [三种药水](items-normal.gif) | 370 | 7.4s |
| [复活](revive-normal.gif) | 180 | 3.6s |
| [增伤击杀与盾面接触](combat-normal.gif) | 320 | 6.4s |

全部20ms/帧、50fps正常时长，非实机60fps录像。由真实GameCore状态、生产纯Swift姿态/粒子/盾/回血字段离线合成；光照/混光与UI为近似，不冒充UIKit/GPU画面。主线程查看31页1190解码帧、原尺寸关键帧与12完整人物1×/2×，不称连续播放。初稿浮字遮脸已返修，判退关键帧保留drafts/face-overlap-v1。

[全场站姿](support-standing.png) · [援护命中](support-impact.png) · [振奋命中](rally-impact.png) · [药水成盾](items-shield.png) · [复活起身](revive-rising.png) · [盾面接触](combat-shield-contact.png)。review.json记录检查与限制，preservation.json记录既有资源保留。

复活预览预设P1倒地，战斗预览预设敌甲3HP以触发致死，是受控审核场景；App默认两敌18HP、P1为6/12、P2为12/18。两人复用当前P1身体，鹿灵为训练模板。复活借既有低身defeat动作连续反放，没有声称新绘平躺身体。新美术认可null，安装、输入、真实性能由用户实机反馈。
