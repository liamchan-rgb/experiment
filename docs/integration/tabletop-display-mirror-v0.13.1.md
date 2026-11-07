# 电视地图布局与教师同画面返修

## 电视地图对齐返修与教师实际画面同步 · 课堂v0.13.1/build15（2026-11-07）

用户报告v0.13/build14初始iPad正常，连接电视后地图地面/树木/阴影错乱，断开后仍异常；截图右侧地面被截断。用户还要求教师端不单独生成简略地图，直接同步实际游戏画面，操作按钮不投放。

本轮在classroom-boardgame的`feat/teacher-backend-meadow-v0.13`修复：统一1280×720逻辑画布（含只读行囊/结算），窗口仅等比居中留边；跨宿主先清UIView transform再设bounds并完成布局，禁止在变换中写frame；classroom地图SpriteKit改aspectFit，Metal关闭drawable自动缩放并固定一点一像素，地图/战斗分区使用整数像素尺寸。屏幕DPI/窗口比例不再改变地图、相机与阴影的内部坐标。这是源码修正，未声称已在用户电视复验成功。

删除TeacherControlMap简图，教师端直接使用实际游戏画面。无电视时本机显示唯一原生渲染器；有电视时该渲染器投放电视，教师端异步回传其Metal完成帧与公开UIView层（上限30Hz，电视渲染目标仍60Hz，不作实机性能承诺）。仅捕获游戏控制器view的公开内容，后台按钮/节点表单/备注属于另一根窗口；无第二份地图、规则、AI或掷骰。教师点击先消除等比留边，再逆变换当前真实相机轴到世界坐标，支持放大和平移后的道路/节点选择；公开端不进入编辑模式。

用户明确先记录、不在此轮实现的绘本待办：①人物生命/行动值/金币简要状态合计≤公开画面10%，不遮绘本；②教师在绘本界面直接发放AP和金币。已保存至上游docs/planning/classroom-book-status-backlog.md及本轮说明。后两步按此顺序推进，不自动扩课堂人数。

新增4项纯画布/投影回归，14项后台专项在Linux通过；实际构建run 42346131666 attempt1、编译提交`7ffc6b13ab3f58c39ea21f63669e2c46440d6e2f`，完整310规则/后台+6绘本核心测试零失败，另4项CI工具测试通过，设备Release归档成功。首轮run42345436987因Apple平台CoreGraphics未显式导入而在纯包编译失败，未产IPA；补齐导入后重建。源码审计/测试不等于运行外屏验证。

IPA0.13.1/build15，最低iPadOS27.0、SDKiphoneos27.2，arm64/755/CRC/经典ZIP2.0无extra、内置PPT、Metal库、568源资源SHA/281编译名称/3份挂载JSON通过。原美术复用，无新人物资源或新增认可。离线连接规则GIF实际5帧/8000ms，主线程查看全部阶段与全景；CPU道路/阴影近似，非App/Metal/电视截图，不作为设备修复证明。未运行App/模拟器/实机，安装后需用户比较初始iPad、电视投放、断开及重复连接。

源码快照`5664dd2f2ae4920ccc765585857074f872be1506`与IPA实际编译提交分开，唯一标签`archive-display-mirror-meadow-v0.13.1-20261107`。完整源码/Git bundle/IPA及诊断/离线GIF已永久备份archive-assets，ZIP逐文件、独立bundle恢复/fsck及所有分片公开GET通过，归档run42346849708；main仅加索引。IPA完整公开GET200：62053723字节，SHA256`88b62f485759e72d606159497dcb1d3f74235b4f5987d675b59e950a1ef2f244`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/01604bc3a93627a60881da807bf923b4fc02fc07/archive-display-mirror-meadow-v0.13.1-20261107/ClassroomStage2-v0.13.1-unsigned.ipa) · [离线显示规则GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/01604bc3a93627a60881da807bf923b4fc02fc07/archive-display-mirror-meadow-v0.13.1-20261107/display-mirror-normal.gif) · [可恢复存档与校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/display-mirror-meadow-v0.13.1-20261107.json)

安装后打开ClassroomProbe → 游戏后台，实际画面支持道路点击，开启“选取地点进行后台编辑”后点建筑再编辑；权限表单仍只在教师端。experiment本体仍Build95，本轮仅同步对接记录，不伪造Build96。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/display-mirror-v0.13.1.md

绘本待办：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/planning/classroom-book-status-backlog.md
