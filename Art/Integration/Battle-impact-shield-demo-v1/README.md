# 强击与护盾演出接入 · build41

用户依据参考图要求加强冲击力，并追加护盾特效。本轮主线程独自制作与审核，沿用build40规则：强击5点伤害/1AP、护盾每次+4、敌方4点攻击，技能没有蓄力等级。HP0、伤害数字与右吹粒子仍同一命中事件触发，出招后不留脚下提示环。

强击：肩肘腕三个关键点调整到胸腹接触，局部命中mask随之改到怪物原图(125,164)；100ms命中停顿、开放冲击弧/白金核心/右向射线与贴地光浪，悬浮暗场45%、施放64%、命中峰值82%。只世界层短促推近/轻震，HUD/技能/血条不随世界变换，系统减少动态效果时关闭镜头扰动。原动作数据备份source/build40-animation.json，新曲线在Art/Scenes/MeadowBattle/impact-shield-v1/attack-clip.json。

护盾：获得护盾事件才展开薄而透明的青蓝边框；盾值>0持续低亮，受击按实际shieldAbsorbed显示接触涟漪与局部闪光，只有最后盾值耗尽才绘碎片和退场。不凭英雄是否扣血猜测盾吸收量，挡住后仍有盾值则保持完整轮廓。重试/返回地图清理出生、受击、破裂时间，持续护盾不是施放后残留的地面提示环。

新光学素材原稿/判退/修订提示词保留Art/Scenes/MeadowBattle/impact-shield-v1/source，导入脚本scripts/import-impact-shield-demo.py。复用原右吹实体帧，仅为加重回弹重新对齐碎片分离位移；旧光效、人物/怪物原画、行走模组保持。

最终源码 `fd019f8f542f863c9b45ef80ab5031aa1d53d974`，[归档40173101137](https://github.com/liamchan-rgb/experiment/actions/runs/40173101137)通过Xcode16.4设备Release与五项纯Swift检查。版本1.6.15/build41，直接IPA `26,986,898` 字节、SHA256 `c5361f015e4edaaa261992306ee3833d872a37ccc737f58b3c684a05f167e4cd`。包的外层摘要/CRC、IPA结构/版本/平台/权限/Metal及新光效编译资源均已核对，生产模型macOS与Linux轨迹在1e-6内一致。

主线程亲看强击165帧与护盾120帧最终解码联系页、原尺寸关键帧及16个攻击整身1×/2×姿势；完整范围见 [审核](../../Review/Battle/impact-shield-demo-v1/art-review.md)。正常GIF均40ms/帧；同源素材与生产事件离线合成，不称UIKit/GPU画面、连续播放或设备验收。没有运行模拟器/App/实机。新美术认可null，用户测试实际光效/输入/性能。

[直接IPA](../../../Downloads/MeadowJourney-b41.ipa) · [强击正常GIF](../../Review/Battle/impact-shield-demo-v1/heavy-strike-normal.gif) · [护盾正常GIF](../../Review/Battle/impact-shield-demo-v1/shield-normal.gif) · [站姿](../../Review/Battle/impact-shield-demo-v1/attack-standing.png) · [交付回执](../../Review/Battle/impact-shield-demo-v1/delivery.json)
