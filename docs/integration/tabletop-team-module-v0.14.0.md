# 六名学生组队与主持人预留席位

## 六名学生组队与老师独立席位 · 课堂v0.14.0/build19（2026-11-07）

按桌游仓库docs/课堂桌游_需求设计_v1.md §1.2/3.1/3.2/8.1/9.1/10.1接入，当前用户的独立距离移动条覆盖原移动AP描述。新行程1—6名学生，逐人姓名/职业，默认同队；旧双人档兼容，继续保留原人数/地图/资产/队列/RNG，不强制转六人。

教师管理→队伍与仓库可建队、拆队、调成员、改名、合并、查看实时队分和仓库。同队金币/个人背包物品互转与仓库存取限探索，不扣AP、无同节点要求，跨队普通转移和战斗取仓拒绝，教师可显式跨队调拨并记录后台事件；已穿戴装备须先卸下。换队仅改teamID，个人资产/HP/AP/技能次数保留，旧队仓库留原队；合并一次提交成员与两仓库，空原队保留历史。原GameEngine命令原子保存、历史回执、撤销，失败回滚，无第二规则/AI/RNG。

不同队不随所选队移动，当前队最大AP平均×50为上限，分队距离余额独立；购买仅用本队金币，战斗AP保持个人独立。地图演员/步态/诊断索引、血条、行囊成员和用药目标、战斗演员/站位/血条/命中动态人数，原队列支持全部学生。主持人API ClassroomGameBackend.joinTeacher(name:classID:team:role:)仅教师可调用，预留host=true的p7，不占六名学生；最多一名，沿用同套资源/计分规则和教师后台权限，无启用UI。未来调用后重装同会话渲染器刷新人数。P3—P7独立外观缺失，复用现有资源并以编号姓名区分，未新画美术。

新增12专项：1—6人存档往返/非法人数、主持人权限与限额、成员字段与RNG保留、队分、仓库守恒/合并/撤销、原队仓库保留、跨队/透支/战斗拒绝、保存失败回滚、六人战斗队列、不同队不跟随、分队移动与AP独立。此前317测试和12专项在Linux通过；实际编译`99b25d16d0e40ed6ddfe094b91bbfa16945aa8e1`、run42375834060 attempt1完成329规则/后台+6绘本核心零失败、4项Python CI工具检查、设备Release归档。IPA0.14.0/build19，最低iPadOS27.0、SDKiphoneos27.2；arm64/755/CRC/经典ZIP2.0、Metal、568源资源SHA/281编译名称/3挂载JSON通过，可执行文件不同于build18。

原一屏教师控件/原技能卡点击与悬停、固定1280×720画布、教师960×540/30Hz和电视60Hz目标保持。私有分组仓库表单不进入公开捕获，公开端无法调用组队/主持人接口。正常GIF为6秒离线结构/站位示意，复用既有演员资源；主线程查看起中末接触表并逐帧解码。非App/UIKit/触摸回放/性能测试，无App/模拟器/实机运行；六人密度/实际点击/帧率/电视隐私由用户安装复核。

源码快照`0d266cc2b1874a2a9c337a3fd4758a7f771a170f`与实际编译提交分开，标签`archive-team-module-meadow-v0.14.0-20261107`。完整源码/Git bundle/IPA/诊断/GIF在archive-assets；ZIP逐文件校验、独立bundle恢复/fsck、全部公开分片GET通过，归档run42376363859；main仅索引。直接IPA完整GET200，62227227字节，SHA256`f60a1f9fb1b856554453316d5909b99a8da854acbbfe753b67c1b0410300dec9`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/5a314ebd8da584a173b7c2139cbfd328f3e3e1fa/archive-team-module-meadow-v0.14.0-20261107/ClassroomStage2-v0.14.0-unsigned.ipa) · [正常速度组队离线示意GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/5a314ebd8da584a173b7c2139cbfd328f3e3e1fa/archive-team-module-meadow-v0.14.0-20261107/team-module-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/team-module-meadow-v0.14.0-20261107.json)

experiment本体仍Build95，本轮只同步对接记录。后两步仍为绘本人物状态区≤画面10%；教师绘本页发放AP/金币。本轮未实施。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/team-module-v0.14.0.md

绘本待办：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/planning/classroom-book-status-backlog.md
