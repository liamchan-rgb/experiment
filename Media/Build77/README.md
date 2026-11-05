# Build77 · 正式怪物回合闪退修复 · 1.6.50

[直接下载IPA](../../Downloads/MeadowJourney-b77.ipa) · [正常怪物回合GIF](../../Art/Review/Battle/campaign-crashfix-v1/monster-turn-normal.gif) · [完整战斗MP4](../../Art/Review/Battle/campaign-crashfix-v1/encounter-full.mp4) · [原因与回归](../../docs/planning/random-map-v1/build77-monster-dice-crash.md) · [包检](verification.json)

修复Build76新/旧档战斗轮到正式怪物时的可复现崩溃：BattleDice用真实m-node-index直接查仅含演练m1/m2的字典，并强制解包。演员和目标均经既有foot/slot映射，真实规则ID保持，玩家接敌时的骰子血条避让同时恢复。无需删除存档，三倍移动、原人物/服装/武器/动作/特效资源、规则与存档格式保持。

旧生产函数独立回归复现fatal/signal4，修复后Linux与Mac194项纯Swift测试及道路/战斗/特效/模组四组回归通过。新增3项用例与首领再生显示扩展覆盖多节点两敌站位、P1/P2接敌的1/2/5骰、真实AI两轮、怪物回合续档及真实骰子定位，不把仅规则回执通过当作显示覆盖。测试不是用户设备崩溃日志或实机稳定性验收。

GitHub Actions故障已恢复；前次41864553920及41869668339 attempt3均失败，归档零步骤；此前还出现过无法取得构建机。最终仅采用41869668339 attempt3成功归档，源提交以verification.json/native-run.json为准。候选旧排队状态保存outage-before-release.json，不能作为当前状态。unsigned设备IPA核过版本1.6.50/77、CRC、经典ZIP2.0无extra、arm64/执行权限、Metal/Assets.car/建筑资源、原地图/步态/规则目录及实际会话模块链接；安装交SideStore签名。公开直链完整GET回执见public-downloads.json，不把CI内部ZIP作为用户下载。

主线程已独审238个实际GIF解码帧的4页接触表、翻面/命中/回位、玩家骰子与胜利整场关键图。GIF238×20ms=4.76秒为怪物连续两次攻击及回位，完整MP4为948×20ms=18.96秒。实际持久化怪物ID先调用真正diceAnchor/channels/PolyhedralDice，再作原美术站位别名。光影/UI近似，不是UIKit/Metal/模拟器或设备录屏，未运行App/模拟器/实机。设备稳定性和操作仍由用户验证，用户新美术认可null。

后两项仍为M4单节点内容编辑，再行程行囊/换装与队伍配置；本次不推进其他功能。
