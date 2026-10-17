# SideStore 安装与迭代包

最新版本 **1.6.1 build 26**：保留各方向鞋子的原画角度，鞋部只随脚踝平移；继续使用三位人物、八方向、每方向 24 姿势的步态系统。

[直接下载 MeadowJourney-b26.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b26.ipa)

IPA：16,641,050 字节，SHA-256：`555c8467897e0e263bc12731158293a06cbc9aac4c86e020764bb493f632e98d`。已检查 ZIP CRC、ZIP_STORED、arm64、0755 执行权限及 Metal 库。安装包未签名，使用 SideStore 重签；安装名称 MeadowJourney，包标识 com.liamchan.experiment.meadow，可覆盖旧版，最低 iPadOS 15。

Safari 下载后保存到“文件”，再打开 SideStore → My Apps → ＋，选择该 IPA 重签安装。

[正常速度录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Normal-b26.mp4) · [四分之一速度录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Quarter-b26.mp4) · [鞋部方向连续抽帧](../Media/Build26-Gait/README.md) · [可换装骨骼方案评估](../docs/CHARACTER_RIG_EVALUATION.md) · [迭代日志](../docs/ITERATION_STATUS.md)。

[构建 39033438871](https://github.com/liamchan-rgb/experiment/actions/runs/39033438871) 通过设备 Release archive、16 项原生检查和 3 项 iPad UI 检查。云端运行于 iPad Pro 13-inch（M4）模拟器、iOS 18.5；兼容性测试仅覆盖 iPad，未测试物理 M1／iPadOS 27.2。正常录像漏掉最初“上”方向，八方向完整抽样以慢速录像和 UI 测试为准。

[来源与完整性元数据](MeadowJourney-build26.json) · [IPA SHA-256 列表](SHA256SUMS)。

历史版本：[build 25](MeadowJourney-build25.json) · [build 24](MeadowJourney-build24.json) · [build 23](MeadowJourney-build23.json) · [build 22](MeadowJourney-build22.json)。
