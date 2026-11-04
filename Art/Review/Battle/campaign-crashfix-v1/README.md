# Build77 · 正式怪物骰子崩溃返修预览

[怪物回合正常 GIF](monster-turn-normal.gif) · [完整遭遇 MP4](encounter-full.mp4) · [缺陷原因与测试](../../../../docs/planning/random-map-v1/build77-monster-dice-crash.md)

用户报告Build76战斗一轮后闪退，新档相同。旧生产函数BattleDice.swift:91直接用m-node-index查演练feet字典而强制解包，纯Swift回归已复现fatal/signal4。现在统一用现有foot/slot映射，真实规则ID不改，人物对敌的骰子避让也同步映射。现有行程可继续，不要求清档；三倍移动和原资源/动作/规则/存档格式保持。

194项纯Swift测试、原道路/战斗/特效/模组四组回归与真实行程CLI导出通过。新增定位用例覆盖多节点的两敌站位、P1/P2对两敌的攻击/突袭/符文斩及1/2/5骰；真实AI连续两轮、怪物回合读档、首领再生绿色骰子均调用与界面相同的定位函数。设备Release归档状态见Media/Build77，不把离线验证等同用户设备稳定性。

本轮离线导出明确调用真实持久化怪物ID的diceAnchor和BattleDice.channels，附生产PolyhedralDice投影与确认回执，先计算真正的显示字段后才序列化为原美术站位别名。原Build76导出仅测规则回执、没有调用骰子定位，这一覆盖遗漏已修补。data包含真实sourceID、每个unit定位与实际出招骰子投影，整个948帧导出均执行这些函数。

正常速度GIF取完整战斗帧0—237，238×20ms=4.76秒，包含第一个怪物连续两次攻击、命中数字和完整回位。完整MP4为948×20ms=18.96秒，继续到胜利/右吹消散。主线程亲看238个实际GIF解码帧的4页接触表、命中/翻面/末帧及玩家出招、胜利整场关键图；不是948帧逐像素全分辨率验收。光照/UI/地面及字形是离线近似，不是UIKit/Metal捕获，不运行App/模拟器/实机，不测试实机FPS。用户美术认可null。

复现：`bash scripts/check-campaign.sh Art/Review/Battle/campaign-crashfix-v1/data`；`python scripts/review-campaign.py Art/Review/Battle/campaign-crashfix-v1`；`python scripts/review-campaign-monster-turn.py Art/Review/Battle/campaign-crashfix-v1`。需要Swift/Pillow/NumPy/中文Noto字体/ffmpeg/gifsicle，GIFSICLE可指定路径。沿用的地图行走预览见[Build76行走GIF](../../Map/campaign-v1/travel-normal.gif)，不重新制作资源。

后两项仍为M4单节点内容编辑，行程行囊/换装与队伍配置。
