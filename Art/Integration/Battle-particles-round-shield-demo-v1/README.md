# 发光粒子与圆盾接入 · build42

用户确认build41特效可用，追加受击/怪物死亡发光粒子、环境照明和落地碰撞，以及圆形更鲜明的护盾和破裂。主线程独自制作审核；没有转交智能体，也没有运行App、模拟器或实机。

原强击胸腹接触、暗场、100ms命中停顿、世界相机反馈、HP0/数字/右吹同事件保持。新增纯Swift MeadowBattleLightField：受击34粒、死亡52粒分批发射，重力下落、两次减速反弹、第三次接地停留；落点短光斑/小溅射、空中局部光晕与死亡暖光带。光粒位置用解析飞行计算，与渲染帧率无关。发射时保存世界坐标，后续防御动作不会拖动已落地光斑；3秒后清理，重试/退出同时清空。

护盾用新圆形透明中心素材，132×132参考世界单位，饱和蓝/青白边框；持续亮度0.60，展开和接触更强。接触12粒，最后盾值归零再发32片较大蓝色碎片，带重力/落地；仍有盾值时不破。鹿灵冲撞按有盾/无盾在动作开始时固定终点，撞在圆盾前缘，不能消耗护盾后突然穿到人物身上。5点强击/+4护盾/4点敌攻等原规则保持，无蓄力等级。

四张光学素材导入脚本scripts/import-battle-light-particles.py；原图与固定裁切见Art/Scenes/MeadowBattle/particles-round-shield-v1。离线审核用scripts/export-battle-light-review.swift直接调用生产粒子函数，保存285帧实际粒子轨迹，再由Pillow合成整场；不是另写一套粒子模拟，也不是UIKit/GPU录屏。圆盾、落地照明与整场遮挡仍须主线程亲看最终GIF解码帧。主线程已亲看最终285帧解码联系页与原尺寸关键帧，见[审核](../../Review/Battle/particles-round-shield-demo-v1/art-review.md)。新美术认可null；build41用户认可单独记录，不自动扩展。

最终源码 `3894119b1d96f102e79e3635aa592a3dbfceb0e5`、[设备归档40175880891](https://github.com/liamchan-rgb/experiment/actions/runs/40175880891)通过Xcode16.4设备Release/五项纯Swift检查。版本1.6.16/build42，IPA 27,661,018字节，SHA256 `128f620175ec552817ec17779c52f8b8df6e2461066ab8e6dfd1a0934fd71de5`；工件/IPA完整性、平台/权限/Metal/新光效与行走资源、macOS/Linux生产轨迹1e-6内一致已核对。没有启动App/模拟器/实机。

[直接IPA](../../../Downloads/MeadowJourney-b42.ipa) · [正常受击/死亡GIF](../../Review/Battle/particles-round-shield-demo-v1/heavy-strike-normal.gif) · [正常圆盾GIF](../../Review/Battle/particles-round-shield-demo-v1/shield-normal.gif) · [站姿](../../Review/Battle/particles-round-shield-demo-v1/attack-standing.png) · [交付回执](../../Review/Battle/particles-round-shield-demo-v1/delivery.json)
