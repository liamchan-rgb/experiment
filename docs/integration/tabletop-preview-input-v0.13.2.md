# 教师预览性能与输入返修

## 教师预览开销与点击返修 · 课堂v0.13.2/build16（2026-11-07）

用户反馈v15交互卡、点不动。源码确认：投屏时主线程30Hz完整1280×720游戏UIView重绘及像素复制/CGImage构造偏重；不投屏时该链路原本关闭，仍有全屏遗漏教师手势和encounter预览拦截地图输入的独立问题。未在设备测量CPU/GPU占比，不把所有卡顿归因于这一处。

本轮在classroom-boardgame分支feat/teacher-backend-meadow-v0.13修改：GPU先缩小为640×360，GPU buffer读取/CGImage构造放utility队列，主线程必要公开UIView合成以半分辨率15Hz上限进行，单次在途不堆积。教师画面滚出屏幕、离开游戏页、绘本、后台、私有对话框或无电视时停止回传。界面revision改为实际状态变化发布，保留AI/超时计时。理论GPU裸像素预算110592000→13824000字节/秒（1/8），不是设备实际帧率/耗时提升8倍。电视仍为1280×720原生60Hz目标，教师辅助回传降采样；原美术资源不变，缺图仍只登记。

全屏接入同一TeacherGamePreview输入，新增教师端收起预览按钮；怪物预览外可继续点道路，卡片内部只读；无效状态给提示。建筑真实命中与相机逆变换、地图/阴影固定画布、单一规则/AI/掷骰、公开端权限隔离保持。教师预览不捕获后台按钮/备注/私有弹窗。绘本≤10%生命/AP/金币状态区与教师发放入口仍只记录，未实施；后两步仍按这两项顺序。

17后台/画布/预览专项在Linux通过，新增覆盖预览后导航不改战斗RNG、裸像素预算上限/独立画布、隐藏/本机/绘本/后台/私有对话框禁回传；源码审计确认全屏手势、滚动可见性、单次在途与后台队列。实际编译提交`81406b3bf1c08e11b9d70defdac90a0297a4cc7a`、run42350765946 attempt1，313规则/后台+6绘本核心测试零失败，4项CI工具检查、设备Release归档通过。过渡run42350196166/42350410685因补滚动离屏停止回传和暂停缓存策略主动取消，未发布为最终包。

IPA0.13.2/build16，最低iPadOS27.0、SDKiphoneos27.2，arm64/755/CRC/经典ZIP2.0、Metal及568源资源SHA/281编译名称/3挂载JSON通过，二进制不同于build15。正常显示规则GIF复用v15同一离线5帧/8秒示意（非性能对比、非App/电视截图），不称新美术认可或实机流畅度验收。未运行App、模拟器、实机；实际触摸响应、电视对齐及帧率待用户安装复核。

源码快照`2c9f395448421218f7a90f3576b1e6a22ebde451`与IPA编译提交分开，标签`archive-preview-input-meadow-v0.13.2-20261107`。完整源码/Git bundle/IPA/诊断/离线GIF已存archive-assets，ZIP逐文件、独立bundle恢复/fsck及全部公开分片GET通过，归档run42351319022；main仅索引。IPA完整GET200，62087899字节，SHA256`d335bc7fe9320357dcca960fbc556a134a97ded8b7ccc2e379a8c7efd30f355a`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/0b1981b3b78d07ee0ba8d4cd45f6a077c9a4bd59/archive-preview-input-meadow-v0.13.2-20261107/ClassroomStage2-v0.13.2-unsigned.ipa) · [沿用的显示规则GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/0b1981b3b78d07ee0ba8d4cd45f6a077c9a4bd59/archive-preview-input-meadow-v0.13.2-20261107/preview-input-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/preview-input-meadow-v0.13.2-20261107.json)

experiment本体仍Build95，本轮只同步对接记录，不伪造Build96。安装后打开ClassroomProbe，重点复核全屏点路、怪物预览外点路和操作按钮响应。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/preview-input-v0.13.2.md

绘本待办：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/planning/classroom-book-status-backlog.md
