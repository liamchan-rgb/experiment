# Build77 · 正式怪物回合骰子定位崩溃返修

用户报告Build76战斗一回合后闪退，新档相同。已在纯Swift回归中用旧生产函数复现 `BattleDice.swift:91: Unexpectedly found nil while unwrapping an Optional value` / signal4：正式怪物使用 `m-<node>-<index>`，头顶骰子仍直接查仅含p1/p2/m1/m2的feet字典。MeadowPartyStageView.play在怪物行动开始时即render，diceActor改为真实怪物ID后触发，不取决于旧存档内容。这是原函数的独立可复现崩溃，与用户描述吻合；没有取得用户设备崩溃日志，不声称已经在其设备定位或复测。

骰子演员和目标统一经已有PartyVisual.foot/slot解析为认可站位，保留真实规则ID；修复强制解包，也恢复玩家接敌时避让真实敌方血条的横向位置。未知ID返回安全的顶部锚点。移动三倍、人物/武器/衣装/动作/特效PNG、原规则、存档格式保持，现有行程可继续，无需清档。

新增两个Party测试覆盖多节点两敌站位、p1/p2对两敌的攻击/突袭/符文斩全过程及1/2/5骰避让等价；新增会话测试使用三种seed推进真实怪物AI两轮，并在怪物回合续档、取实际dice channels、按60Hz采样同一定位函数和校验一次命中提交；已有首领再生测试增加真实绿色骰子定位。194项Swift测试通过。旧函数失败复现记录Media/Build77/before-fix-reproduction.log，最终设备归档与包检见同目录verification.json。

上一版会话回归覆盖了规则结算，却遗漏头顶骰子的显示定位调用；原离线合成也没有调用它，因此未暴露该崩溃。现在导出每个实际unit及出招的diceAnchor和生产PolyhedralDice投影，并调用真正的BattleDice.channels与确认回执。新正常速度整场预览包含骰子，不通过把m-node编号提前改成m1绕过这条路径。资源编号别名只用于已有图片站位。

离线动图与自审在Art/Review/Battle/campaign-crashfix-v1。光照、UI与离线帧率近似，不是UIKit/Metal录屏或设备稳定性验证。仅纯Swift验证、设备Release编译及IPA包检；不运行App/模拟器/实机。用户设备安装和连续战斗体验仍待验证。

本次优先修闪退，不推进新功能。后两项仍是M4单节点内容编辑，再行程行囊/换装与队伍配置。
