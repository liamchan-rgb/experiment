# 绘本状态发放与私有玩家GM

## 绘本状态/发放与私有玩家GM · 课堂v0.15.0/build20（2026-11-07）

用户授权完成旧两项绘本待办，并新增任意玩家各项数值与个人背包GM。公开PublicBookPage底部固定真实窗口高度9%的总状态带，横排最多7人，仅姓名、HP与绿血条、黄色菱形AP/上限、金币；绘本图像独占其余91%并保持比例，页码小角标。长名字可缩小、极值简写，朗读保留全数值。ClassroomBookPlayerStatus白名单投影不含背包/备注/权限/历史。教师本地书页复用同一只读页面，备注单独私有。

教师绘本页固定常用按钮、对象选择（单/多/全选）及AP/金币发放，不切游戏页；AP+1、金币+10快捷项按个人含装备上限封顶，与地图移动条独立，同一campaign/engine无第二账本。不解除绘本暂停、不推进AI/RNG，非法对象/重复/整数溢出整笔回滚。

游戏右上GM及绘本GM窗口使用同一教师私有宿主，含全屏。可改姓名、当前HP/护盾/AP/金币/积分、基础最大HP/基础AP/AP上限/伤害/射程、增伤数值及轮数、技能已用次数、全部目录内个人背包数量（0移除，可搜索）。字段标签持续可见，基础与装备加成分开，身份/职业/队伍/节点/穿戴/仓库不改。提高上限不自动补满资源或移动条；降低上限需同步当前值合法。倒地清盾/增伤，复活沿用下一轮可行动；道路游标中成员设倒地先到建筑节点。GM成功单次提交后才刷新公开结果，失败保留草稿；关闭未保存不写。

仅最近命令为GM/绘本发放时，可通过教师入口撤销，不能越过后续动作。专用undoPreservingPresentationPause保持当前绘本/手动/编辑/后台等显示暂停；行动者未变时保留当前剩余时钟，避免跨绘本/游戏撤销带回历史book暂停。原通用undo语义保持。原6学生+老师p7 API、一屏教师控件/原技能卡、固定1280×720画布与960×540/30Hz目标保持；不新增美术。

新增15专项涵盖1—7人多窗口面积<10%、只读字段白名单、绘本暂停中多人发放/个人封顶/移动及RNG不变、无效/重复/溢出回滚、公开端拒绝GM/发放/撤销、任意玩家数字/背包与身份隔离、非法属性/物品/技能拒绝、背包0移除、增伤/技能次数、倒地/复活、存档/撤销、磁盘失败、道路游标保护、跨页面撤销暂停保持。本地15专项通过；实际编译`92ad2d39e09bd8b289727b3be29544953a4193fa`、run42380512294 attempt1完成344规则/后台+6绘本核心零失败、4项Python CI工具及设备Release归档。IPA0.15.0/build20，最低iPadOS27.0、SDKiphoneos27.2；arm64/755/CRC/经典ZIP2.0、Metal、568源资源SHA/281编译名称/3挂载JSON通过，可执行文件不同于build19。

正常GIF是6秒离线布局/状态更新示意，7人含老师仅作容量示例，不表示老师启用UI已上线；示意页不会写入PPT或美术资源。主线程查看初始/私有草稿/保存后三幅接触表并逐帧解码。非App/UIKit/触摸回放/性能验证，未运行App/模拟器/实机；真正阅读密度、键盘/菜单、电视隐私与性能由用户安装验收。缺P3—P7独立外观仍只登记。

源码快照`eb1a922ced394361543f3faf0fc9bd85c74dbf2d`与实际编译提交分开，标签`archive-book-gm-meadow-v0.15.0-20261107`。源码/Git bundle/IPA/诊断/GIF已存archive-assets，ZIP逐文件、独立bundle恢复/fsck、全部公开分片GET通过，归档run42381086078；main仅索引。直接IPA完整GET200，62351059字节，SHA256`ed92c030c08017c28b798a427d2ac78eecdd0d5101d61b92075f32c5d75d84cc`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/1a95393811f8dd62086d3922d84455ace597d823/archive-book-gm-meadow-v0.15.0-20261107/ClassroomStage2-v0.15.0-unsigned.ipa) · [正常速度绘本/GM离线示意GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/1a95393811f8dd62086d3922d84455ace597d823/archive-book-gm-meadow-v0.15.0-20261107/book-gm-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/book-gm-meadow-v0.15.0-20261107.json)

experiment本体仍Build95，本轮只同步对接记录。旧绘本两项已实现，不能继续写“未实施”。建议后两步：教师操作历史列表与按记录回退；老师参战启用入口与7人完整流程，本轮未顺带实施。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/book-gm-v0.15.0.md

绘本待办：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/planning/classroom-book-status-backlog.md
