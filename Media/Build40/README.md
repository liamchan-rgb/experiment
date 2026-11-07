# build40 · 战斗光效接入

版本1.6.14，最终源码2f1d2475b119eb57e96c69200a2fc25468c8c2c8，[设备归档40167117136](https://github.com/liamchan-rgb/experiment/actions/runs/40167117136)。Xcode16.4，五项纯Swift检查与设备Release归档通过；无模拟器、App或实机运行。

进入“林地战斗 → 开始遭遇 → 选中鹿灵 → 强击”。仍是5点固定伤害/1AP；前三击后余3血，结束回合等鹿灵行动，再选靶强击即可检查致死命中、伤害数字与右吹粒子同步。鼠标悬浮/键盘焦点/触屏按住技能卡预示光效，强击发光时压暗；正常施放会退出光圈。重试/返回地图清理旧效果。门控在接触点结算，按钮输入不提前扣血。

[直接IPA](../../Downloads/MeadowJourney-b40.ipa) · [正常整场离线GIF](../../Art/Review/Battle/effects-demo-v1/battle-demo-normal.gif) · [站姿](../../Art/Review/Battle/effects-demo-v1/standing.png) · [来源与SHA256](package.json) · [主线程审核](../../Art/Review/Battle/effects-demo-v1/art-review.md)

IPA25,176,986字节，SHA256 `2ed99a131c16c1030d22dc9a90070945009c04c6c2c76a9c56268d84a27267be`。原始unsigned iPhoneOS/arm64安装包，沿用SideStore重签安装；直接下载IPA，不提供外层artifact ZIP给用户。外层工件摘要/CRC、IPA CRC/ZIP_STORED/无extra与ZIP64、版本/平台/权限/Metal、VFX与两P1预设编译资源名及gait原字节均核对。最终浏览器HTTPS实际GET记录见交付回执，不将本地包校验称为实机安装。

离线动图使用导入素材和生产状态时钟数据，非UIKit/GPU画面。像素混光、输入与帧率仍由用户实机反馈；尚未新增其他属性技能、音效或人物自身粒子死亡。
