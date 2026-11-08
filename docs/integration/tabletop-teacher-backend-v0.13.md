# 课堂教师后台与完整Meadow接入

## 教师后台重构交付 · v0.13/build14（2026-11-07）

用户更正上一版架构：删除原桌游游戏部分；当前Meadow demo的操作与教师权限移到教师后台，随机地图生成留后台；投放端只显示探索地图、按需玩家行囊/怪物预览，战斗用现有完整战斗预览。本轮在classroom-boardgame分支 `feat/teacher-backend-meadow-v0.13` 执行，覆盖此前v0.12.1“保留旧游戏/切换简化公开页”的后续安排。旧代码/旧包保留于历史存档，App里无旧游戏回退。

删除原RulesLab/PVEAppSession/旧地图战斗公开页/v0.12简化适配；保留PPT导入、页面、备注、备份与iPadOS27独立公开场景。完整导入当前demo的GameViewController、Metal GameScene、MeadowBattlePreview/PartyBattle/PartyStage、动作/骰子/技能/死亡演出、规则与资源。公开模式不挂载管理按钮，根输入禁用，战斗公开回调另行拒绝；所有原游戏弹窗转交教师根presenter，公开端只读玩家信息，不含节点编辑/备注。ClassroomGameBackend持有单一正式campaign/encounter；教师后台驱动地图生成/移动、AI/时钟，公开端不创建训练局或第二份规则。战斗结束演出完成回地图；绘本/暂停保留同一会话。新行程独立ClassroomMeadow命名空间，旧个人资料不删除、不自动转旧PVE存档。

后台操作地图支持道路任意点/节点编辑/镜头/角色选择/怪物预览/背包装备/移动补充/资源/奖励/队伍/路线，战斗目标、技能、悬停骰子、物品与回合操作留后台。最终检查补齐当前玩家回合/AP/库存/次数/目标校验，键盘同样守卫；校验不prepare、不掷骰、不改状态。沿用当前双人行程与平均距离移动条，不声称扩为完整课堂多成员。

资源来自experiment175c7dfc4a68e62cb9693da8d837b77081619a6b，568份源资源SHA逐份一致、281编译资源名称、3份SPM挂载JSON逐字节、Assets.car与Metal库已核对；无新美术生成或新增用户认可。主线程亲看完整联系表并解码118帧/4720ms正常速度GIF，属于离线职责示意/既有资源合成，非UIKit或设备截图，不称实际窗口路由或连续播放验收。缺图仍仅登记。

实际设备Release编译提交 `b20e3a95cf5c52d4724f66e5f88d219bdff48f58`，run 42341843315 attempt1，306规则/后台测试+6绘本核心测试零失败，另4项Python CI工具测试通过。IPA0.13/build14、iPhoneOS arm64/755、CRC/经典ZIP2.0无extra、内置PPT、完整地图/步态资源、Metal库头均通过；最低iPadOS27.0、SDKiphoneos27.2。未运行App、模拟器或实机，真实外屏切换/比例/触摸由用户安装截图反馈。

永久源码快照 `34931ec42f8f92f614ffe2a2a6b212177b42b7b5` 与编译提交分开记录；唯一标签 `archive-teacher-backend-meadow-v0.13-20261107`。完整源码/Git bundle/本步IPA与诊断/正常GIF已存archive-assets，ZIP逐文件、独立bundle恢复/fsck及所有分片公开GET通过，归档run 42342449892。索引仅加入main，不合并代码或二进制分支。IPA完整公开GET200：62037369字节，SHA256 `7eefd10008f2820807a909ecf4fd185816d067f3c0fdf39bd405c8823cbb714c`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/f74f280a2598f11f440f7b0b8b8b3ae77f58a836/archive-teacher-backend-meadow-v0.13-20261107/ClassroomStage2-v0.13-unsigned.ipa) · [正常速度离线GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/f74f280a2598f11f440f7b0b8b8b3ae77f58a836/archive-teacher-backend-meadow-v0.13-20261107/teacher-public-normal.gif) · [可恢复存档与校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/teacher-backend-meadow-v0.13-20261107.json)

入口：ClassroomProbe → 游戏后台 → 随机地图与新行程 → 生成/开始。未接外屏可全屏预览；接屏后由独立公开窗口承载同一渲染器。experiment本体仍Build95，不冒称Build96。后两步：①依据教师端/投放端实机截图调操作密度、投放比例和切换；②扩展课堂更多成员与目标布局，缺图只登记。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/teacher-backend-v0.13.md
