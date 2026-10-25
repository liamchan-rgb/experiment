# 技能动态、圆盾跟随与回血 · build43

用户要求完整包裹人物的大圆盾、修正移动跟随、改进回血，并以所传视频作为技能特效/场景光影理想标准，运镜不纳入。本轮主线程独自制作审核，不启动App、模拟器或实机。参考抽帧/属性笔记在Art/Scenes/MeadowBattle/skill-flow-v1，录屏原文件与分析帧不发布。

盾面与沿边光点改为hero直接子视图，跟所有人物层同一非动画事务更新；中心原生(128,144)，直径240，不再按不断变化的支撑脚取中心。圆边透明中心、无缩小展开，按完整活体动作/武器像素覆盖核对；碰撞点与破片发射圆周同步放大。破片/落地光斑继续固定世界空间，不能跟着人拖动。

回血原“喘息”仍1AP/恢复4且只结算一次，接触0.46秒；视觉动作1.2秒、上升星粒尾部1.8秒。新增绿金星光/两股盘旋光缕/柔光柱/短扩散波与地面局部绿光，提示和环境轻压暗，人物中心保持可读。强击主弧扫动、延迟弱回声与贴地光浪分阶段，仍一次5伤害，不复制参考的多段伤害。原暗场、HP0/数字/右吹同事件、无蓄力与起势后无提示圈保持；既有相机参数/人物原画/步态不改。

离线审核由生产Swift直接导出粒子/回血轨迹与盾几何，再合成三张正常GIF：强击死亡、持盾冲刺返回并格挡破裂、回血。光照/混光为近似，不能声称UIKit/GPU或实机运行。原版本保留，新artApproval=null；主线程已亲看最终440帧解码页、原尺寸关键帧和完整人物1×/2×，见[审核](../../Review/Battle/skill-flow-demo-v1/art-review.md)。最初回血在亮树林太弱已判退并保留drafts/subtle-healing-v1；最终加强两侧光缕/星点、绿白恢复短亮核和地面绿光。新美术认可null。

最终源码 `0c9f1e7a9397f26e64824412fc2d20a4472fa23f`、[设备归档40179386404](https://github.com/liamchan-rgb/experiment/actions/runs/40179386404)通过Xcode16.4设备Release/五项纯Swift。版本1.6.17/build43，IPA 28,133,914字节、SHA256 `40092768e150fd663d62181b95347be7d8ff95a2e6817b118e177cc98c33957f`；工件/IPA完整性、版本/平台/权限/Metal/新光学及行走资源核对，macOS/Linux生产轨迹1e-6内一致。首轮40178762700因Swift类型推断超时在纯检查阶段失败，修订后重新归档，不交付失败或旧源码包。

[直接IPA](../../../Downloads/MeadowJourney-b43.ipa) · [圆盾跟随正常GIF](../../Review/Battle/skill-flow-demo-v1/shield-follow-normal.gif) · [回血正常GIF](../../Review/Battle/skill-flow-demo-v1/recovery-normal.gif) · [强击死亡正常GIF](../../Review/Battle/skill-flow-demo-v1/strike-death-normal.gif) · [站姿](../../Review/Battle/skill-flow-demo-v1/shield-full-cover.png) · [下载回执](../../Review/Battle/skill-flow-demo-v1/delivery.json)

未执行App/模拟器/实机；实际跟随、色彩、光照、输入与性能交用户测试。参考视频不是demo设备证据，也没有复制其素材或新增对应全部属性技能。
