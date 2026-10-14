# 动态版 1.1.0 视觉验收

- [iPad 横屏录像](https://github.com/liamchan-rgb/experiment/raw/refs/heads/main/Media/iPad-LivingScene-v1.1.0.mp4)：约 18 秒，2752 × 2064、H.264、30 FPS，已调整为正确横屏方向并压缩，保持像素尺寸。
- [iPad 原尺寸截图](https://github.com/liamchan-rgb/experiment/raw/refs/heads/main/Media/iPad-LivingScene-v1.1.0-native.png)。
- [放大截图](https://github.com/liamchan-rgb/experiment/raw/refs/heads/main/Media/iPad-LivingScene-v1.1.0-zoom.png)。
- `RuntimeMetrics-v1.1.0.json`：CI iPad 模拟器运行采样，平均约 58 FPS，基础纹理预算 42.36 MiB。此数据不代表真机性能。
- `BuildInfo-v1.1.0.json`：源码提交、已通过的构建、测试和 IPA 校验信息。

本版本来自已完整通过 Xcode 编译、12 项模型/资源检查、iPhone 与 iPad 界面测试的源码提交。整图背景已从 App 移除，场景通过独立资源搭建，风、雾、光束、投影及人物运动在运行时更新。

草地仍有可见重复形状。最后的均匀地表纹理、全局随机采样和道路材质坐标调整保留在 `feat/layered-living-scene`，尚未进入此 IPA：GitHub 因账户付款失败或支出上限拒绝启动这次 macOS 构建。解除账单限制后需要重新验证和打包。
