# build47 · 共享UI、骰子与怪物反馈

多人战斗已恢复单人同款左右地图/战场、回合进度条、技能卡与生命/护盾/AP条；四单位进度token与当前行动者状态同步。预备人物光效改头顶持续摇动骰子，仍按技能固定强度压暗。红伤害、黄增伤、绿恢复、蓝护盾，援护绿蓝同时出现；确认后沿人物前冲跟随，命中回执到达后0.36s平滑停稳，保持可读后淡出。

[直接下载IPA](../../Downloads/MeadowJourney-b47.ipa) · [五正常GIF/站姿](../../Art/Review/Battle/dice-party-demo-v1/README.md) · [包校验](package.json)。入口仍为林地战斗→小队支援；单人也已同步预备骰子。

版本1.6.21/build47，31,791,196字节，SHA256 `be893efe718c77d250d4b323b268fb5791dc00b730f68c44fc0b2e45daf6525e`。最终输入 `463d221dbf80752a75d3d1449b859f76d841b03f`，CI [40217822252](https://github.com/liamchan-rgb/experiment/actions/runs/40217822252)。84纯规则/适配测试、旧五项与iPhoneOS Release通过。Linux/macOS1060骰子/怪物/队列帧匹配，浮点1e-6，acted是无序Set按集合比较，不把序列化顺序当规则差异；原1190轨迹/3570请求也匹配。包经典ZIP2.0本地与中央头/CRC、版本/平台/权限/Metal、图标/VFX/行走与原目录资源已核。

目标60，不运行App/模拟器/实机；安装/操作/稳定FPS由用户测试。先前SideStore安装问题未确定根因，本包沿用兼容封装。主审38页1060解码帧、12整身1×/2×与关键图，非UIKit/连续播放/设备录像。新美术认可null。怪物为既有鹿灵素材的动作反馈补齐，非正式六怪/新手绘全动作库，后续技能装备批次未算完成。

公开交付提交 `4c8879729872f9a5e331ac264515a50796d135f9`，13个公开链接完整GET200/摘要通过；110选定路径和242编译输入已核。下载核验：[delivery.json](../../Art/Review/Battle/dice-party-demo-v1/delivery.json)。
