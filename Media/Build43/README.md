# build43 · 圆盾跟随、回血与技能动态

版本1.6.17，源码 `0c9f1e7a9397f26e64824412fc2d20a4472fa23f`，[归档40179386404](https://github.com/liamchan-rgb/experiment/actions/runs/40179386404)。Xcode16.4设备Release与五项纯Swift通过，无App、模拟器或实机运行，沿用SideStore重签安装。

进入“林地战斗 → 开始遭遇”。检查圆盾：先简易防护，再选鹿灵强击，最后结束回合；大圆盾包住人物并随冲刺/返回，鹿灵在盾前接触，最后4盾耗尽才破。检查回血：重试后直接结束回合挨一击，再点喘息，HP8→12及+4在恢复时出现，绿金光缕/星粒上升并给地面染光。强击新增扫动主弧/弱回声/光浪，仍一次5伤害；第四次致死与数字/右吹同时，数值/动作/行走及既有相机参数保持。

[直接IPA](../../Downloads/MeadowJourney-b43.ipa) · [圆盾正常GIF](../../Art/Review/Battle/skill-flow-demo-v1/shield-follow-normal.gif) · [回血正常GIF](../../Art/Review/Battle/skill-flow-demo-v1/recovery-normal.gif) · [强击正常GIF](../../Art/Review/Battle/skill-flow-demo-v1/strike-death-normal.gif) · [完整站姿](../../Art/Review/Battle/skill-flow-demo-v1/shield-full-cover.png) · [来源校验](package.json) · [主审](../../Art/Review/Battle/skill-flow-demo-v1/art-review.md)

IPA 28,133,914字节，SHA256 `40092768e150fd663d62181b95347be7d8ff95a2e6817b118e177cc98c33957f`；直接下载IPA，无外层ZIP。工件/包CRC、结构、版本/平台/权限/Metal/资源与gait字节核对完成，macOS/Linux生产轨迹全部字段/浮点1e-6内一致。三GIF共440帧40ms，生产Swift导出光粒/回血/盾几何、同源动作和贴图的离线美术合成，光照/混光近似，非UIKit/GPU录屏。正常跟随180帧相对盾心不漂移及505姿态覆盖与整场人工复核已记录，不能当作实机延迟/性能测试；用户复测，新美术认可null。HTTPS/远端字节证据见交付回执。
