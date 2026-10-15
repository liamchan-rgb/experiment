# SideStore 安装与视觉验收

[最新三维阴影试验包：1.4.1 build 12 贴图轮廓版](SHADOW_LAB_PREVIEW.md)。安装后点地图左上角「光影试验」。

[直接下载 1.3.0（build 9）IPA](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Downloads/MeadowJourney-v1.3.0-unsigned.ipa)。

在 Safari 保存到“文件”，然后 SideStore → My Apps → ＋，选择带 v1.3.0 的文件重签安装。安装名称为 MeadowJourney，需要 iOS / iPadOS 15 及以上。包标识保持 com.liamchan.experiment.meadow，可覆盖更新旧版。

本版增强动态阳光、移动云影与最小缩放下的树冠阵风；增加三位人物四种斜向朝向与双腿接触控制，降低走路起伏；重做透明根部的花簇和灌木，并减少散布密度。包含旗杆屋脊和投影脚底锚点修复，阴影继续使用现有 2.5D 轮廓投影。

来源为源码 1fc2415 与 [成功构建 38696431707](https://github.com/liamchan-rgb/experiment/actions/runs/38696431707)：25 项模型／资源／实际渲染测试、iPhone 与 iPad 各 2 项交互测试、原生录屏与设备 Release archive 通过。包内版本、arm64 架构、双设备支持、资源完整性及 SHA-256 均已核验。

[录像与截图](../Media/README.md) · [完整构建来源与校验值](../Media/BuildInfo-v1.3.0.json) · [迭代记录](../docs/ITERATION_STATUS.md)

MeadowJourney-unsigned.ipa 通用下载文件也指向本版；SHA256SUMS 保存所有包的校验值。1.2.0、1.1.0 等旧包保留作历史对照。
