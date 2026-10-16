# 缩放投影与启动加载修正包

[下载 1.5.3 build 16 IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b16.ipa)。在 Safari 保存到「文件」，再在 SideStore 点「＋」选择 MeadowJourney-b16.ipa，可覆盖安装。

- 前景与 Metal 地面使用同一份真实视口变换，覆盖连续放大、双指缩放上限、平移与复位。
- 道路遮罩、素材、投影网格与纹理准备移到后台，修正网格累计复制的热点；前景物件分批创建，减少启动时的集中阻塞。
- 加载页按实际完成阶段显示进度；前景与地面首帧就绪后开放操作，失败提供重试。人物阴影提前上传完整图集，运行时切帧不再上传纹理。
- 保留全地图 alpha 轮廓实时 shadow map。本轮按用户要求推迟人物步态修正，动画问题仍待后续处理。

已在 iPhone 与 iPad 模拟器通过缩放、平移、复位和地图交互检查。红色前景标记与 Metal 地面青色校准环的最大中心误差：iPhone 0.67、iPad 0.25 个 512 长边分析像素。启动耗时约 6.17 秒／15.48 秒，主线程最长停顿约 0.29 秒／0.50 秒。8 项原生渲染检查全部通过。

IPA 的版本、CRC、arm64、iPhone／iPad 支持、Metal 资源、可执行权限和经典 ZIP_STORED 格式已校验。模拟器检查结果与物理设备反馈分开记录，实机放大和冷启动体验由用户继续反馈。

[迭代日志](../docs/ITERATION_STATUS.md) · [实现记录](../docs/SHADOW_LAB.md) · [来源与 SHA-256](MeadowJourney-build16.json)

历史：[build 15](MeadowJourney-build15.json) 收到最大缩放错位与启动卡顿反馈；此前已确认的小场景为 [1.4.1 build 12](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b12.ipa)。
