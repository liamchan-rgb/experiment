# build51 停骰摆正与战斗状态修正

确认技能时仍立即锁定原核心本次结果，结果面正对屏幕、面上数字朝上；各面统一朝上的几何基，停止时不再保留三轴倾角，也不因四元数正负等价表示变化而抖动；深度量化与面值平局规则固定跨平台等深度面的绘制次序。D4/D6/D8/D10/D12/D20全部结果面均检查。随机骰移除下方重复数字，数值只留在骰面；固定加值方块内的数值保留，下字幕继续隐藏。怪物HP0同一次呈现更新隐藏完整名称与生命/护盾条，并同步伤害数字及右吹消散；重置重新显示，玩家倒地牌保留。单人和小队共用黄色菱形AP，亮实心表示剩余、暗空心表示已耗，上限取原状态数据，保留原槽位与行动进度队列。

| 正常速度动图 | 审核范围 |
| --- | --- |
| [突袭](ambush-normal.gif) | 220帧/4.4秒；悬停翻面→确认正向停骰→原时点伤害与自疗 |
| [普通攻击/反击](attack-buff-normal.gif) | 300帧/6秒；无重复数字、黄色菱形消耗、双方反馈 |
| [致死](lethal-normal.gif) | 190帧/3.8秒；血条与HP0/数字/右吹同事件消失 |

[完整站姿](ambush-standing.png) · [确认停骰](ambush-dash.png) · [致死瞬间](lethal-impact.png) · [消散与隐藏血条](lethal-recovery.png) · [各骰型正向落面](dice-upright-gallery.png) · [整身1×](actor-body-1x.png) · [2×](actor-body-2x.png) · [全场1×](whole-world-1x.png) · [2×](whole-world-2x.png) · [确认/死亡时序](confirmation-death-trace.json)

主线程亲看25页710实际GIF解码帧、六完整人物和六全场1×/2×共四板及骰型图库。正常速度50fps/每帧20ms的离线合成，生产Swift网格/状态/实际原规则回执驱动；字体、混合、地图、光照、UI近似。静态序列审核，不称连续播放或UIKit/实机录屏。致死夹具预设目标3HP用于审核，默认仍18HP。[审核](review.json) · [资源保留](preservation.json)。新美术认可null。

源码`850ea80801ee4ab0e57cbed4cd37b93f9febe942`，设备Release [40278764694](https://github.com/liamchan-rgb/experiment/actions/runs/40278764694)成功；98纯规则/事务/几何测试及五旧纯Swift检查通过。Mac/Linux1190小队帧、3570请求、1500骰子/怪物帧与360骰型/公式帧逐字段在1e-6内一致，acted集合按无序比较。原10814美术/资源路径、13原核心/清单摘要与单人模型/时钟前缀保持。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b51.ipa) · [包记录](../../../../Media/Build51/package.json)。1.6.25/build51，31,878,628字节，SHA256 `0121c60bd65e150dd4b02e913ad76a9fd82dbe1a75d24da9fa68e2ae4a0e9523`。经典ZIP2.0/CRC/平台/权限/原目录与资源已核，无App/模拟器/实机执行。入口：林地战斗→小队支援；原单人演练同步AP菱形和死亡隐条。
