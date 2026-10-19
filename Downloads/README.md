# SideStore 安装与迭代包

## Meadow Journey 横版战斗场景试验包 · 1.6.5 build 30

修正 build 29 的左侧地图缩成中间矩形、上下露底问题：地图现在铺满左栏，保留进入前的缩放和物件大小，并聚焦当前旅人；退出后恢复原来的镜头。只保留右侧一个“返回地图”按钮。右侧仍是复用 Meadow Journey 地表、树石与林地氛围的战场原型，人物单帧仍待审核。

[直接下载 MeadowJourney-b30.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/meadow-battle-scene-v0.1/Downloads/MeadowJourney-b30.ipa) · [查看实际分屏截图](../Media/MeadowBattle-b30.png)

IPA 为 17,208,156 字节，SHA-256：`9a49b0ed7d38560b84dc0767364643a999b2fc6631234747d5b4e9e24a8a5bef`。已检查包内版本、真机 arm64、iPad 支持、Metal 库、可执行权限、ZIP CRC 和 ZIP_STORED 格式。[构建与完整性元数据](MeadowJourney-build30.json)。

首次打开主地图后点“战斗预览”，地图留在左侧，右侧查看横版战场；点击战斗面板的“返回地图”可退出。请用 SideStore 重签安装。2 项原生相机检查与 2 项 iPad UI 检查均通过，包含左栏顶部／底部的真实地面纹理、相机缩放和退出恢复检查；实际截图已目视核对。完整步态套件未重跑，既有失败记录见[迭代记录](../docs/ITERATION_STATUS.md)；此包尚未在物理 iPad 上测试。

上一版原型保留为 [build 29](MeadowJourney-build29.json)，包含已在 build 30 修复的左栏适配问题。

上次完整通过 iPad UI 套件的正式基线仍是 build 28：

**1.6.3 build 28**：修正三位人物在八个行走方向中两只鞋分别向外撇的问题，使鞋尖更一致地朝向前进方向。“原图 / 分层蓝靴对照”仍是附带的换色小样，仅覆盖 P1 向下方向。

[直接下载 MeadowJourney-b28.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b28.ipa)

IPA：16,806,354 字节，SHA-256：`e99c0e9754dd3ea4875566603df82273b49365474b8069a7e0693e25fad0cd0f`。已检查 ZIP CRC、ZIP_STORED、无 Zip64／额外字段、真机 arm64、0755 执行权限、Metal 库，以及包内蓝靴图集和对照入口代码。安装包未签名，使用 SideStore 重签；安装名称 MeadowJourney，包标识 com.liamchan.experiment.meadow，最低 iPadOS 15。沿用原 SideStore 账号和安装方式更新即可，不需要先删除旧版。

Safari 下载后保存到“文件”，再打开 SideStore → My Apps → ＋，选择该 IPA 重签安装。

安装后进入主地图 →“步态测试”，依次选择八个方向，检查 P1、P2、P3 的鞋尖是否一同朝向前进方向、交替时有没有反转或鞋腿断缝。可切换四分之一速度、暂停和单步定位问题。完整步骤见[鞋向实机测试说明](../docs/GAIT_TEST.md)。

[正常速度录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Normal-b26.mp4) · [四分之一速度录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Quarter-b26.mp4) · [鞋部方向连续抽帧](../Media/Build26-Gait/README.md) · [可换装骨骼方案评估](../docs/CHARACTER_RIG_EVALUATION.md) · [迭代日志](../docs/ITERATION_STATUS.md)。

[本次构建 39051625894](https://github.com/liamchan-rgb/experiment/actions/runs/39051625894) 的设备 Release IPA、八方向 iPad UI 检查和实际地图录像均已通过：模拟器逐个切换八个朝向，并逐帧检查每方向 24 张步态姿势；另保存了正常／四分之一速度地图录像。测试设备为 iPad Pro 13-inch（M4）模拟器、iOS 18.5；物理 iPad 的安装与运行观感仍需本地确认。

[来源与完整性元数据](MeadowJourney-build28.json) · [IPA SHA-256 列表](SHA256SUMS)。

历史版本：[build 27](MeadowJourney-build27.json) · [build 26](MeadowJourney-build26.json) · [build 25](MeadowJourney-build25.json) · [build 24](MeadowJourney-build24.json) · [build 23](MeadowJourney-build23.json) · [build 22](MeadowJourney-build22.json)。
