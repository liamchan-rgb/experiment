# 地面黑底与步态修正包

[下载 1.5.2 build 15 IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b15.ipa)。请替换出现黑底的 build 14。保存到「文件 → 我的 iPad」，再在 SideStore 点「＋」选择 MeadowJourney-b15.ipa，可覆盖安装。

- 草地、道路和阴影接收由同一原生 Metal 不透明地面通道输出，修复整层黑底。前景透明属性在首次显示前配置。
- 去掉源帧之外的全身抬升；向右整体镜像用户认可的完整向左动画。左右 profile 保持源步态。
- 正背向和斜向使用连续下肢网格补充承重脚后扫，人物与深度投影共享相位和几何，脚底落在同一地面平面。
- 继续使用全地图 alpha 轮廓实时阴影和合并道路遮罩。

[构建 38842001680](https://github.com/liamchan-rgb/experiment/actions/runs/38842001680) 已通过设备 Release 归档、15 项原生检查，以及 iPhone／iPad 各 1 项 UI 检查，共 17 项、0 失败。UI 检查读取初始、缩放、试验场返回后的实际屏幕像素；已核对 iPad 地面确实显示。IPA 的版本、CRC、arm64、Metal 资源、可执行权限和 ZIP_STORED 格式已校验。

三位人物的实际渲染接触／经过帧已对照：[P1](../Media/Build15-Gait/Hero1-contacts.png) · [P2](../Media/Build15-Gait/Hero2-contacts.png) · [P3](../Media/Build15-Gait/Hero3-contacts.png)。正背向原素材仍缺少清楚分离的鞋底姿态，完整锁脚和步态自然程度需要实机反馈。阴影和道路的美术效果继续由用户检查。

[迭代日志](../docs/ITERATION_STATUS.md) · [实现记录](../docs/SHADOW_LAB.md) · [来源与 SHA-256](MeadowJourney-build15.json)

历史：build 14 收到地面黑底反馈，build 13 最终交互检查失败，均已被替换。此前已确认的小场景：[1.4.1 build 12](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b12.ipa)。
