# 1.6.0（build 25）步态复核

[下载 IPA](../Downloads/README.md) · [正常录像](iPad-Gait-Normal-b25.mp4) · [四分之一速度录像](iPad-Gait-Quarter-b25.mp4) · [八方向连续抽帧与19项检查](Build25-Gait/README.md)。

三位人物、八方向、每方向24张完整行走姿势。使用实际地图渲染器完成 iPad 云端运行、录像和连续抽帧复核。构建来源、帧率、时间轴及证据范围见上方记录。

以下为历史验收资料。

# 1.3.0（build 9）视觉验收

[下载 IPA](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Downloads/MeadowJourney-v1.3.0-unsigned.ipa) · [构建与校验信息](BuildInfo-v1.3.0.json) · [来源构建](https://github.com/liamchan-rgb/experiment/actions/runs/38696431707)

- [八方向步态近景](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-EightDirectionGait-v1.3.0.mp4)：三位人物以 42 世界单位／秒行走，与默认生产速度一致；查看正背、左右及四个斜向的换腿、衣摆和投影。[八方向抽帧索引](iPad-GaitDirections-v1.3.0.jpg)、[斜向接触姿势连续抽帧](iPad-DiagonalContacts-v1.3.0.png)。
- [最小缩放、静止镜头光照与风动](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-MinimumZoomAtmosphere-v1.3.0.mp4)：倍率固定为 100%，人物暂停；观察移动光带、云影、流动雾和树冠阵风。[开始画面](iPad-MinimumZoomAtmosphere-v1.3.0-start.png)、[结束画面](iPad-MinimumZoomAtmosphere-v1.3.0-end.png)、[树冠局部连续抽帧](iPad-TreeWind-v1.3.0.png)。
- [行旅演示](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Media/iPad-LivingScene-v1.3.0.mp4)与[原尺寸场景截图](iPad-LivingScene-v1.3.0-native.png)：演示巡逻、道路移动、镜头缩放和探索；长录像提供紧凑预览，时间比例见下方记录。

录像校正为横屏，保留 2752 × 2064 像素，使用 H.264 / 30 FPS。步态与固定镜头片段保留原始时间轴；行旅紧凑预览的时间比例和原始时长保存在 [RecordingInfo](RecordingInfo-v1.3.0.json)。完整原始录像、iPhone／iPad 原尺寸测试截图与 Xcode 报告保存在来源构建的 Actions Artifact 中。抽帧索引与局部截图用于检查动作，不替代原尺寸录像。

本包对应源码 `1fc2415`。25 项模型／资源／实际渲染检查和 iPhone、iPad 各 2 项交互测试通过。检查覆盖光雾实际像素变化、全景尺寸的树木轮廓风动、四个斜向的不同接触姿势、肢体连通、衣摆宽度与同步投影。

[场景采样](RuntimeMetrics-v1.3.0.json)最后 30 个样本平均 58.97 FPS、最低 55 FPS，最高驻留内存 173.89 MiB；[最小缩放采样](MinimumZoomMetrics-v1.3.0.json)平均 56.38 FPS、最低 51 FPS，最高驻留内存 209.30 MiB。基础 RGBA 纹理预算为 55.14 MiB，独立物件 288 个。这些数据来自 macOS 上的 iPad 模拟器及录屏过程，不是物理 iPad 的性能测量。

早先的 1.2.0 与 1.1.0 文件保留为历史对照；本页链接均指向 build 9。
