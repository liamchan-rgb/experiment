# 1.2.0 视觉验收资料

本轮修复在 [PR #3](https://github.com/liamchan-rgb/experiment/pull/3)，当前主分支仍保留 1.1.0。安装使用 [1.2.0 IPA](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Downloads/MeadowJourney-v1.2.0-unsigned.ipa)。

- [四方向步态近景](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-FourDirectionGait-v1.2.0.mp4)：约 40 秒，保留原始时间轴；三位人物分别展示正面、向左、背面、向右行走；可查看双腿交替、腰部和装备边缘，以及地面投影是否跟随人物姿势。
- [正面接触姿态对照](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-GaitContact-v1.2.0.png)与[四方向画面索引](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-GaitDirections-v1.2.0.png)。
- [静止镜头光雾](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-Atmosphere-v1.2.0.mp4)：人物暂停、镜头固定，约 60 秒紧凑预览，查看雾、光束、云影与风动；[开始画面](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-Atmosphere-v1.2.0-start.png)与[结束画面](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-Atmosphere-v1.2.0-end.png)供对照。
- [iPad 行旅演示](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-LivingScene-v1.2.0.mp4)：约 40 秒紧凑预览，巡逻、缩放及探索地点。
- [原尺寸场景截图](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-LivingScene-v1.2.0-native.png)与[放大截图](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-LivingScene-v1.2.0-zoom.png)。

录像调整为正确横屏方向、H.264 / 30 FPS，保留 2752 × 2064 像素；PNG 保留原尺寸。超长录屏的紧凑预览按比例缩短，并保留整段场景变化；原始时间轴录像与 Xcode 测试附件在来源构建的 Actions 页面，具体时间比例见 `RecordingInfo-v1.2.0.json`。

`BuildInfo-v1.2.0.json` 记录源码、成功构建、测试数量、录像整理来源和 IPA 校验值。`RuntimeMetrics-v1.2.0.json` 为 iPad 模拟器原始运行采样，基础纹理预算约 42.36 MiB；模拟器的帧率和驻留内存不代表物理 iPad。

恢复时发现旧构建的四方向录屏为空白，原因是验收场景在 UIKit 初次布局前按零尺寸建立节点，未适配后续尺寸。此次修复后重新执行 iPhone 与 iPad 验收入口测试，并检查实际录像。早先的 1.1.0 文件保留作历史对照；本页的链接均指向 1.2.0。
