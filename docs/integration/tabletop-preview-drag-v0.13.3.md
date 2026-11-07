# 教师高清30帧目标与拖动地图

## 教师高清30帧目标与拖动地图 · 课堂v0.13.3/build17（2026-11-07）

用户要求提高教师部分清晰度与帧率并恢复原demo拖动。本轮在classroom-boardgame分支feat/teacher-backend-meadow-v0.13实现教师960×540/30Hz目标，覆盖v16的640×360/15Hz。真实地图CGImage直接分层显示，公开透明UIView另行缓存；静态HUD按脏最高10Hz，战斗/骰子30Hz。GPU缩小、后台utility读取、单一在途、隐藏/绘本/后台/私有弹窗暂停保持。新地图帧直接推送，阶段时钟容忍略早vsync，挂起不追补队列。理论GPU裸像素预算62,208,000字节/秒，不代表设备耗时或稳定帧率；电视原生1280×720/60Hz目标保持。没有设备CPU/GPU测量。

对照原experiment panMap/pinchMap和GameScene.panBy/setZoom，教师端单指/双指/鼠标拖动平移相机、双指捏合围绕触点缩放；沿用原方向/边界/缩放规则，先换算回固定逻辑画布。tap等待拖动/捏合失败，拖动抬手不下走路命令。道路点按移动、建筑选中保持，地图拖动优先于后台ScrollView，地图外正常滚动。相机手势不扣移动值/AP、不改规则/RNG；公开电视无控制手势/后台按钮/备注/私有弹窗。单一规则/AI/计时、固定画布及设备角色权限保持。

21项专项和4项CI工具检查通过，实际提交`a4a1f901a5b01bd11f3470c1c8a403ebf1616f05`、run42356713660 attempt1完成317规则/后台+6绘本核心测试零失败及设备Release归档。IPA0.13.3/build17、最低iPadOS27.0、SDKiphoneos27.2；arm64/755/CRC/经典ZIP2.0、Metal、568源资源SHA/281编译名称/3挂载JSON核验通过，二进制不同于build16。没有运行App、模拟器、实机。真实手势/清晰度/帧率/电视与断开对齐由用户安装复核。

新正常GIF为60个40ms采样点、2.4秒的离线相机规则示意，复用地图素材，CPU道路/阴影仅作近似；主线程查看起始/中间/结束接触表，教师与电视相机一致，指针仅教师。它不是App/触摸回放/性能测量，不把离线示意称实机流畅度或美术认可。缺失美术只登记，本轮没有新人物/技能资源。

源码快照`b9bc217f928cfd061f787f634328dd8b13fa6e62`与IPA实际编译提交分开，标签`archive-preview-drag-meadow-v0.13.3-20261107`。完整源码/Git bundle/IPA/诊断/正常GIF已存archive-assets；ZIP逐文件校验、独立bundle恢复/fsck及全部公开分片GET通过，归档run42357179451。main仅索引。直接IPA完整GET200，62091075字节，SHA256`35db2d3b18f79085a84977bd3ab0abfc6319c44144e953f1cbe18017f5fa3860`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/a0503327974cbb72525eeea26ea4bd20eeb98113/archive-preview-drag-meadow-v0.13.3-20261107/ClassroomStage2-v0.13.3-unsigned.ipa) · [正常速度离线拖动示意GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/a0503327974cbb72525eeea26ea4bd20eeb98113/archive-preview-drag-meadow-v0.13.3-20261107/preview-drag-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/preview-drag-meadow-v0.13.3-20261107.json)

experiment本体仍Build95，本轮仅同步对接记录。后两步仍为：绘本生命/AP/金币状态总占画面≤10%；教师在绘本界面发放AP/金币。本轮两项均未实施，先收当前设备反馈。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/preview-drag-v0.13.3.md

绘本待办：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/planning/classroom-book-status-backlog.md
