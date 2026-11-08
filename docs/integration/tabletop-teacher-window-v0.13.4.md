# 教师游戏窗口一屏操作

## 教师游戏窗口一屏操作 · 课堂v0.13.4/build18（2026-11-07）

用户要求教师按钮尽量移入游戏窗口、无须上下翻页，技能必须合并到游戏原画面。本轮删除后台整页ScrollView、画外按钮和独立battleControls技能网格，改固定管理栏44pt、阶段操作栏48pt、自适应真实游戏画面、单行状态28pt。探索常用选人/选地点编辑/修改内容/交互/行囊/补移动/暂停在窗口内；低频新行程/续档/保存/资源调整/发奖/队伍/路线/节点编辑收进管理菜单。全屏复用同一结构。

战斗直接点击原公开MeadowPartyBattleView技能卡，无第二套技能按钮；鼠标悬停走原骰子预览，点角色或血条选目标。紧凑工具栏提供目标/道具/暂停/结束行动。命中先还原固定1280×720画布，再按真实UIView坐标转换查询原卡/角色位置，经requireTeacher与原后台battleTarget校验执行；公开源技能/角色回调仍禁用，不启用电视操作，不创建第二份引擎/AI/RNG。课堂技能卡均分可用宽度，移除已删除道具占位，不需横向滚动。地图拖动捏合和点路保留，技能tap与相机pan分别判定。全屏私有表单通过当前教师呈现宿主打开，实际弹窗仍停止输入/回传。

私有工具栏属于教师宿主兄弟视图，不进入游戏控制器捕获；电视仍仅游戏/玩家面板/绘本，无权限按钮/备注/编辑界面。教师960×540/30Hz和电视60Hz仍为目标，不称实机稳定帧率。缺失美术只登记，本轮没有新人物/技能资源。

实际编译`2d6607489fa9f353c108d8b63fa98c616a0942b4`、run42365112217 attempt1完成317规则/后台+6绘本核心零失败、4项Python CI工具检查和设备Release归档；包版本0.13.4/build18、最低iPadOS27.0、SDKiphoneos27.2。arm64/755/CRC/经典ZIP2.0、Metal、568源资源SHA/281编译名称/3挂载JSON通过；可执行文件与build17不同。未运行App/模拟器/实机，原技能点击命中、菜单与单页布局、投屏隔离由用户安装复核。

正常GIF复用已有符文斩战斗采样与原资源，40ms采样，展示单页结构/原卡位置/窗口工具栏；主线程查看起中末接触表并逐帧解码。仅离线结构示意，CPU布局/道路/阴影近似，不称UIKit截图/触摸回放/性能测试或新美术认可。

源码快照`29d64e673be47c97c57e89d4a1bb85b355155c1d`与IPA实际编译提交分开，标签`archive-teacher-window-meadow-v0.13.4-20261107`。完整源码/Git bundle/IPA/诊断/正常GIF已存archive-assets；ZIP逐文件校验、独立bundle恢复/fsck及全部公开分片GET通过，归档run42365742197。main仅索引。直接IPA完整GET200，62106787字节，SHA256`7293052f23de2149081c45304da1f70d7cd2762a919e3e12542bccff08ae3abc`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/c5ef4b871590ef9bb965f41908cfe7826c40700e/archive-teacher-window-meadow-v0.13.4-20261107/ClassroomStage2-v0.13.4-unsigned.ipa) · [正常速度离线窗口示意GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/c5ef4b871590ef9bb965f41908cfe7826c40700e/archive-teacher-window-meadow-v0.13.4-20261107/teacher-window-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/teacher-window-meadow-v0.13.4-20261107.json)

experiment本体仍Build95，本轮只同步对接记录。后两步仍为绘本生命/AP/金币状态区≤画面10%；教师在绘本页发放AP/金币，本轮未实施。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/teacher-window-v0.13.4.md

绘本待办：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/planning/classroom-book-status-backlog.md
