# Build76 · 正式行程与三倍移动 · 1.6.49

[直接下载 IPA](../../Downloads/MeadowJourney-b76.ipa) · [正常行走 GIF](../../Art/Review/Map/campaign-v1/travel-normal.gif) · [致死命中与胜利收尾 GIF](../../Art/Review/Map/campaign-v1/encounter-normal.gif) · [完整遭遇 MP4](../../Art/Review/Map/campaign-v1/encounter-full.mp4) · [实现记录](../../docs/planning/random-map-v1/build76-campaign.md)

进入原地图左下“随机地图”，调整数量/种子后选“开始新行程”；下次可“继续行程”。沿建筑门前真实道路探索，到达节点逐边扣行动点、揭示和结算奖励，遇敌接现有战斗布局，胜利返回继续。地图与战斗共用同一个规则引擎，伤害、物资、装备和奖励不因切场景/续档重置。新档是P1魔剑士/P2游侠双人，沿用已验证双人战斗布局；原演示三旅人保留。行程独立保存campaign-v1.json，原camp-v1.json不覆盖；新建覆盖旧行程需界面确认，坏档保留。途中继续先暂停，保留实际布局、当前边、距离和镜头，不按种子重抽。探索没有虚构的自动回合，用“补足行动”调用原规则。

移动统一三倍：原演示三人25/38/45→75/114/135；正式同行按较慢者75。步态按行进距离推进，起停原帧与战斗出招时序保持。普通鹿灵和鹿王是明确本地ID模板，分别完整复制原wolf/caveTroll数值、AI与掉落，复用已有鹿美术；六种原怪物的独立外观尚未完成。原人物/装备/服装/动作PNG、SceneMap、hero-gait及原规则目录保持。

Linux/Mac共191项纯Swift测试通过，新增9项会话测试；道路/战斗/特效/模组四组回归通过，iOS设备Release归档成功。会话覆盖到站才结算、每边扣点、奖励幂等、保存失败回滚、途中暂停续档、同一引擎和命中一次、原首领AI、胜利与后续遭遇资源保留、坏档不覆盖。干净目录重导出CLI成功：9份JSON忽略新会话UUID与revealed/acted集合编码顺序后一致，地图/道路/帧序列与回执摘要无需归一化即一致。

IPA经CRC、经典ZIP2.0无extra、版本/权限、arm64设备可执行、Metal与Assets.car/四建筑资源、原地图/步态与规则目录核对。包内MeadowCampaignSession及campaign-v1.json相关符号实际链接，来源为verification.json所列源提交与最终运行41849402511。unsigned IPA供SideStore签名。没有安装、运行App、模拟器或实机；设备帧率及操作交用户验证。

主线程独自审完整画面、关键帧与14页接触表（370行走/948战斗小图），最终GIF完整画布首/中/末解码已核；不是1318帧全分辨率逐像素验收。离线预览光照/UI近似，不冒充UIKit/实机画面。地图GIF7.40秒，胜利GIF仅战斗最后5.96秒，完整战斗另提供18.96秒MP4，均20ms正常速度取样。新美术用户认可null。

后两项：M4单节点内容编辑；行程行囊/换装与队伍配置。
