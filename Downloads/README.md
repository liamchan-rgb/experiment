# SideStore 安装与迭代包

最新版本 **1.6.0 build 25**：重做三位人物的八方向行走，每方向 24 张完整姿势，修正膝盖／靴口连接、鞋尖重复、裙摆残片及步幅与移动速度的匹配。[来源与校验信息](MeadowJourney-build25.json)。

[直接下载 MeadowJourney-b25.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b25.ipa)

Safari 下载后保存到“文件”，再打开 SideStore → My Apps → ＋，选择该 IPA 重签。安装名 MeadowJourney，包标识 com.liamchan.experiment.meadow，可覆盖旧版；最低 iPadOS 15。

进入地图后点击顶部“步态测试”，可切换八个方向、正常／四分之一速度、暂停和单步。单步前进一张完整姿势；返回地图会恢复镜头和人物状态。[操作说明](../docs/GAIT_TEST.md)。

[正常录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Normal-b25.mp4) · [慢速录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Quarter-b25.mp4) · [抽帧与测试记录](../Media/Build25-Gait/README.md) · [迭代日志](../docs/ITERATION_STATUS.md)

[构建 39023714295](https://github.com/liamchan-rgb/experiment/actions/runs/39023714295)已通过设备 Release 归档、16 项原生／资源／渲染检查、3 项 iPad 界面检查和两组原生录像。已对两组录像逐方向抽帧复核。云端使用 iPad Pro 13-inch（M4）模拟器、iOS 18.5；不把它等同于物理 M1 iPadOS 27 验证。本轮未运行 iPhone 测试。

IPA：17,276,922 字节，SHA-256：`1ca2dbde7a80f2701c3d1a903a1ce01c5efd49fc3a065f8313621c743408a664`。ZIP CRC、arm64、0755 执行权限、Metal 库和步态资源均已检查。

历史版本：[build 24](MeadowJourney-build24.json) · [build 23](MeadowJourney-build23.json) · [build 22](MeadowJourney-build22.json) · [build 21](MeadowJourney-build21.json)。
