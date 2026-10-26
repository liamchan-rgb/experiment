# build48 多面骰翻面候选

D4、D6、D8、D12、D20 采用真实多面体顶点/面法线、三轴旋转与透视，另兼容原规则可用的D10。数字固定在面上随面翻转/遮挡，结果到达后连续减速0.65秒，停到原规则回执的真实数值，短暂保持后淡出。不是旧的方框晃动/逐帧换数字。

普通攻击悬停读取实际武器的GameRules.attack公式，技能按各effect.dice/count/flat与回执逐颗显示；例如2D8显示两颗八面骰，2D12显示两颗十二面骰。伤害红、骰增伤黄、恢复绿、护盾蓝；原规则里的固定增伤/恢复/护盾单独显示有类别的加值牌，保持原数值规则。悬停不消费AP/随机状态、不蓄力。

| 正常速度动图 | 范围 |
| --- | --- |
| [六种骰型](types-normal.gif) | 180帧 / 3.6秒，D4/D6/D8/D12/D20/D10 |
| [多骰与固定加值](bonus-normal.gif) | 180帧 / 3.6秒，原突袭2D8与符文斩2D12公式 |
| [攻击与增伤整场](attack-buff-normal.gif) | 300帧 / 6秒，人物头顶跟随、回执落面、怪物反击 |
| [援护整场](support-normal.gif) | 190帧 / 3.8秒，固定恢复/盾数值、绿蓝牌与原连续光效 |

[完整站姿](attack-buff-standing.png) · [攻击摇动](attack-buff-rolling.png) · [攻击结果停稳](attack-buff-settled.png) · [骰型停稳](types-landed.png) · [多骰停稳](bonus-landed.png) · [援护结果](support-held.png) · [完整战场1×](whole-world-1x.jpg) · [完整战场2×](whole-world-2x.jpg)

上述为生产Swift几何/轨迹与原GameCore回执驱动的离线美术合成。每帧20ms、正常速度50fps，字体/地图/光照/混合近似，不是UIKit或实机录屏。D4/D10仅用离线临时装备审核骰型，没有新增默认武器；多骰对照不代表突袭/符文斩整套动作特效或B2/B3已完成。

主线程自己返修并检查29页850实际GIF解码帧、6完整场景1×/2×和复用的12人物/怪物整身1×/2×四板。初稿落面太平、D10过长、字幕越界已退回修正，见[drafts](drafts/flat-landing-label-overflow)。原10814美术/资源路径、原13核心/目录摘要保持。[审核](review.json) · [保留核对](preservation.json) · [几何轨迹](poly-frames.json)。新用户美术认可null。

归档源码`4bc9855e4fe71b39022095741e64a95b05b3e133`，90规则/几何测试、既有五检查、设备Release [40264624021](https://github.com/liamchan-rgb/experiment/actions/runs/40264624021) 与包结构/CRC/摘要检查通过。Mac/Linux的1190小队、3570原光效请求、1060骰子怪物、360多面骰对照帧逐项比较，浮点容差1e-6（仅acted集合按无序比较）。无App/模拟器/实机执行，真实安装、输入与稳定60FPS由用户反馈。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b48.ipa) · [包校验](../../../../Media/Build48/package.json)。入口：林地战斗→左上“小队支援”。
