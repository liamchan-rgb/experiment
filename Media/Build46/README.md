# build46 · 小队支援 B0/B1

本轮B0/B1小队支援已接入：援护、振奋、三种药水与复活石，2玩家/2敌目标、真实buff/AP/次数/库存与一次结算。入口为林地战斗→左上“小队支援”，原单人演练保留。正式盾max、buff轮数、救援2AP/半血/下轮行动由原GameCore执行。角色/步态与原资源10806路径保持，原13核心源文件/目录SHA匹配；两个P1与训练鹿灵复用不算新职业皮肤/正式怪完成。

源码 `cf245fe98d2234941423e487bacc8be0f67685be`，CI [40212372613](https://github.com/liamchan-rgb/experiment/actions/runs/40212372613)。79纯规则测试及原五项检查通过，iPhoneOS Release归档通过；macOS/Linux1190帧状态与3570请求逐字段比较、浮点1e-6内一致。无App/模拟器/实机/UI运行。

直接IPA：1.6.20/build46，31,740,108字节，SHA256 `3cd7c942e82d91a238ba9f11f4921c88f24a640734fbb38154f1e008f04e855d`；arm64/iPhone+iPad/iOS15、经典ZIP2.0本地头/中央头、CRC/权限/Metal/资源与原目录打包均核验。沿用SideStore重签；实际安装及60FPS由用户测试，未宣称之前安装报错根因已确认。

[直接下载IPA](../../Downloads/MeadowJourney-b46.ipa) · [五正常GIF与站姿](../../Art/Review/Battle/party-support-demo-v1/README.md) · [包校验](package.json)。主线程独自查看31页1190实际GIF解码帧、12完整人物1×/2×及原尺寸关键帧，浮字遮脸首稿已退回修正。离线预览不称UIKit/实机画面，新美术认可null。完整装备/背包与B2后续不在本轮完成范围。
