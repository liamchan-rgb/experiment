# 桌游教师端/公开端试接结果

## 桌游双屏试接交付 · v0.12.1/build13（2026-11-07）

用户要求尝试接入，随后明确“两个模块”指教师操作端与公开展示端。本轮在 classroom-boardgame 新分支 `feat/meadow-public-bridge-v0.12` 实际接入 PublicSurface，只收脱敏 PublicPlayFrame；原教师控制、完整教师地图、选人/目标/发奖/编辑/撤销/记录与绘本/备注隔离保留。公开端可切 Meadow/原画面，教师端“PVE课堂→预览公开画面”查看同一公开数据源。未改原 App 外接场景注册，不用教师屏镜像替代独立公开端。

只有原 PVEAppSession/GameEngine 负责结算/掷骰/保存/AI/计时。新增账本 before 是 publicSnapshot，不是完整GameState；只记录真实技能ID与HP/盾变化。命中 .46 秒显示伤害/死亡，恢复/新盾 .72 秒后显示；混合技能分别处理，队列不跳未来结果，历史恢复/撤销不重放。战斗画面只取真实 queueIDs，移动用已提交路径，抵达再切战斗。原桌游仍按AP/道路/抵达开战规则；没有迁入Meadow距离移动条或覆盖存档，未建立第二套引擎。

114份已有素材SHA匹配experiment 175c7dfc4a68e62cb9693da8d837b77081619a6b；蓝衣通用近战及怪物/技能特效复用。初次整景审核发现治疗盖住接敌人物，根线程自行改至人物背后并延后，符文斩峰值对齐命中；v0.12内部稿保留，最终交付v0.12.1/build13。主线程查看79个GIF解码帧的五页整景、三处1×/2×完整人物场景；正常GIF3000ms。离线Pillow合成含辉光/文字近似，不称作UIKit/外接屏截图或设备连续播放验收。默认双人adventurer/spellblade复用蓝衣近战；其余职业暂沿用原美术，职业装备/远程动作绑定、完整Metal地图及全部课堂容量视觉仍为后续，不声称全部Meadow玩法已移植；缺图只标注。

实际设备Release源码 `3f1b684f978df334d4ec0ec7cf52d31f9e85afa4`，run 42319105836 attempt1，79 GameCore + 6 ProbeCore零失败，另4项CI工具检查通过。IPA版本0.12.1/build13、iPhoneOS arm64/755、CRC/经典ZIP2.0无extra、内置PPT/114素材逐文件SHA通过；二进制确实不同于build12。桌游原部署目标保留 iPadOS27.0，SDK27.2；本次不需要自定义Metal库。未运行App/模拟器/实机，不声称外接屏/PPT实际设备已验收。

永久归档源码快照 `a011d69a4d85cb3832aea40f0e4264c594c68502`，标签 `archive-meadow-public-bridge-v0.12.1-20261107`，源码与实际编译提交分开记录；完整源码/Git历史bundle/交付及诊断已备份到archive-assets，ZIP逐文件、bundle独立恢复/fsck和所有分片公开GET通过。首次误触发备份因未生成新版本记录而安全退出，补齐实际成功run/artifact记录后run42319544558完成归档。索引收尾不递归归档。

IPA完整公开GET200：36150190字节，SHA256 `e8618ee986a6029f702b84b68fc1f8a8f5b50a83f1f6e2f28dd7f11830d21b71`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/b5923d3286cfe2a2e30b10148dfc7f690f8fc4b7/archive-meadow-public-bridge-v0.12.1-20261107/ClassroomStage2-v0.12.1-unsigned.ipa) · [正常速度离线GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/b5923d3286cfe2a2e30b10148dfc7f690f8fc4b7/archive-meadow-public-bridge-v0.12.1-20261107/meadow-public-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/meadow-public-bridge-v0.12.1-20261107.json)

experiment本体仍为Build95，本轮没有伪造Build96或重打Meadow旧包。后两步：①按用户教师端/公开端实机截图修正比例、字重与信息密度；②逐职业补公开装备/远程动作绑定与精确时间轴，再扩全部课堂容量，缺图仅列清单。


上游详细说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/meadow-public-bridge-v0.12/docs/integration/meadow-v0.12.md
