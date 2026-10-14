# SideStore 安装与视觉验收

[直接下载 1.2.0（build 5）IPA](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Downloads/MeadowJourney-v1.2.0-unsigned.ipa)（约 14.8 MiB）。

在 Safari 保存到“文件”，然后 SideStore → My Apps → ＋，选择带 `v1.2.0` 的新 IPA 重签安装。安装名称为 MeadowJourney，需要 iOS / iPadOS 15 及以上。包标识保持 `com.liamchan.experiment.meadow`，可以覆盖更新此前安装的 Demo。

这个包来自源码 `e9e7819`，对应 [成功构建 38567622574](https://github.com/liamchan-rgb/experiment/actions/runs/38567622574)：模拟器编译、18 项模型/资源/渲染测试、iPhone 与 iPad 交互测试，以及 iOS 设备 Release archive 均通过。

本轮包含距离驱动的四方向步态、正背面双腿交替、统一太阳方向的轮廓投影与接触阴影、流动雾与光束、草地随机采样、道路碎石，以及移开人物身体的探索标记。修复仍在 [PR #3](https://github.com/liamchan-rgb/experiment/pull/3)，主分支的旧版 1.1.0 保留供对照。

[录像、原尺寸截图及验证信息](../Media/README.md)。`MeadowJourney-unsigned.ipa` 通用地址也指向此验收版。SHA-256 校验值见 `SHA256SUMS`。
