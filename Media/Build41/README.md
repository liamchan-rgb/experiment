# build41 · 强击冲击与护盾演出

版本1.6.15，最终源码 `fd019f8f542f863c9b45ef80ab5031aa1d53d974`，[设备归档40173101137](https://github.com/liamchan-rgb/experiment/actions/runs/40173101137)。Xcode16.4设备Release与五项纯Swift检查通过；未运行App、模拟器或实机。沿用SideStore重签安装。

进入“林地战斗 → 开始遭遇 → 选中鹿灵”。强击仍5点固定伤害/1AP；前三击剩3血，结束回合后下一轮第四击可看数字/HP0/向右吹散同步。选择“简易防护”增加4盾，结束回合让鹿灵冲撞，检查透明盾面展开/持续/前侧涟漪/耗尽碎裂；连续两次防护可检查8盾挡一击后余4不破，第二次归零才破。技能卡悬浮/焦点/触屏按住预示已有接线，实际输入由用户测试。强击100ms命中停顿、更深暗场与短促世界推近轻震，HUD稳定；系统减少动态效果时关闭相机扰动。

[直接IPA](../../Downloads/MeadowJourney-b41.ipa) · [强击正常GIF](../../Art/Review/Battle/impact-shield-demo-v1/heavy-strike-normal.gif) · [护盾正常GIF](../../Art/Review/Battle/impact-shield-demo-v1/shield-normal.gif) · [站姿](../../Art/Review/Battle/impact-shield-demo-v1/attack-standing.png) · [来源校验](package.json) · [主线程审核](../../Art/Review/Battle/impact-shield-demo-v1/art-review.md)

IPA 26,986,898字节，SHA256 `c5361f015e4edaaa261992306ee3833d872a37ccc737f58b3c684a05f167e4cd`。直接下载IPA，无外层ZIP。工件与IPA完整性、iPhoneOS/arm64/版本/权限/Metal、新光效和两P1预设的编译资源名、gait原字节均核对；实际下载HTTPS记录见交付回执，不将包校验当作安装测试。两张GIF来自导入素材/当前动作/生产时钟的离线美术合成，非UIKit/GPU录屏，分别165×40ms和120×40ms。主线程亲看最终全部解码帧与关键帧；新美术认可null。
