# build42 · 发光粒子、地面碰撞与圆盾

版本1.6.16，源码 `3894119b1d96f102e79e3635aa592a3dbfceb0e5`，[设备归档40175880891](https://github.com/liamchan-rgb/experiment/actions/runs/40175880891)。Xcode16.4设备Release及五项纯Swift检查通过，无App、模拟器或实机运行。

进入“林地战斗 → 开始遭遇 → 选中鹿灵 → 强击”。新金色粒子随受击出现、落地溅亮反弹，第四次强击致死后配合向右消散和暖光带；仍5点伤害/1AP，三击剩3血，结束回合后下一轮第四击致死。选择“简易防护”出现更鲜明的蓝青圆盾；鹿灵冲撞停在盾前，接触波纹/光粒、最后盾值耗尽时较大蓝碎片与落地反弹。连续两次防护可看8→4不破、第二击4→0才破。场景/人物/步态原资源保持，沿用SideStore重签安装。

[直接IPA](../../Downloads/MeadowJourney-b42.ipa) · [受击/死亡正常GIF](../../Art/Review/Battle/particles-round-shield-demo-v1/heavy-strike-normal.gif) · [圆盾正常GIF](../../Art/Review/Battle/particles-round-shield-demo-v1/shield-normal.gif) · [站姿](../../Art/Review/Battle/particles-round-shield-demo-v1/attack-standing.png) · [来源校验](package.json) · [主审](../../Art/Review/Battle/particles-round-shield-demo-v1/art-review.md)

IPA 27,661,018字节，SHA256 `128f620175ec552817ec17779c52f8b8df6e2461066ab8e6dfd1a0934fd71de5`。直接IPA无外层ZIP。外层摘要/CRC、IPA结构/版本/平台/权限/Metal/新资源及gait一致性已核对；模型全部字段/浮点与Linux在1e-6内一致。离线两GIF共享素材/动作/生产事件与生产粒子轨迹，40ms正常速度，Pillow照明近似，非UIKit/GPU录屏。实际画面、输入与性能交用户反馈，新美术认可null。远端/HTTPS证据见交付回执。
