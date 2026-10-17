# SideStore 安装与迭代包

最新版本 **1.6.2 build 27**：供本地检查三位人物在八个行走方向的鞋子朝向。步态测试支持正常／四分之一速度、暂停、逐帧单步和重新播放。“原图 / 分层蓝靴对照”是附带的换色小样，仅覆盖 P1 向下方向。

[直接下载 MeadowJourney-b27.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b27.ipa)

IPA：16,744,850 字节，SHA-256：`2954efd466000db241ac4d1b61e9c3d743ed9bb8839925f9993417e5d8048e93`。已检查 ZIP CRC、ZIP_STORED、无 Zip64／额外字段、真机 arm64、0755 执行权限、Metal 库，以及包内蓝靴图集和对照入口代码。安装包未签名，使用 SideStore 重签；安装名称 MeadowJourney，包标识 com.liamchan.experiment.meadow，最低 iPadOS 15。沿用原 SideStore 账号和安装方式更新即可，不需要先删除旧版。

Safari 下载后保存到“文件”，再打开 SideStore → My Apps → ＋，选择该 IPA 重签安装。

安装后进入主地图 →“步态测试”，依次选择八个方向，检查 P1、P2、P3 的鞋尖朝向及行走中的落脚状态。可切换四分之一速度、暂停和单步定位问题。完整步骤见[鞋向实机测试说明](../docs/GAIT_TEST.md)。

[正常速度录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Normal-b26.mp4) · [四分之一速度录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Quarter-b26.mp4) · [鞋部方向连续抽帧](../Media/Build26-Gait/README.md) · [可换装骨骼方案评估](../docs/CHARACTER_RIG_EVALUATION.md) · [迭代日志](../docs/ITERATION_STATUS.md)。

[本次构建 39049360600](https://github.com/liamchan-rgb/experiment/actions/runs/39049360600) 使用 Xcode 16.4、macos-15，已通过设备 Release archive 与 IPA 打包。本轮为 package-only，没有重新运行模拟器、UI 或 GPU 测试。应用代码和资源与此前[分层对照检查 39042942547](https://github.com/liamchan-rgb/experiment/actions/runs/39042942547) 相同，仅提升版本号；此前 1 项 iPad UI 检查通过，设备为 iPad Pro 13-inch（M4）模拟器、iOS 18.5。物理 iPad 的安装与运行观感待本地测试。

[来源与完整性元数据](MeadowJourney-build27.json) · [IPA SHA-256 列表](SHA256SUMS)。

历史版本：[build 26](MeadowJourney-build26.json) · [build 25](MeadowJourney-build25.json) · [build 24](MeadowJourney-build24.json) · [build 23](MeadowJourney-build23.json) · [build 22](MeadowJourney-build22.json)。
