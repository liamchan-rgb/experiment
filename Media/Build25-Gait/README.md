# build 25 人物步态复核

源码 `75e54c87223afe248ee1055379931c0a92d55219`，来自[成功构建 39023714295](https://github.com/liamchan-rgb/experiment/actions/runs/39023714295)。与交付 IPA 使用相同源码与角色资源。

[正常录像](../iPad-Gait-Normal-b25.mp4)（31.88 秒） · [四分之一速度录像](../iPad-Gait-Quarter-b25.mp4)（48.13 秒） · [19 项云端检查](CloudValidation.json) · [录像来源及校验](RecordingInfo.json)。

录像使用实际地图的单 MTKView 渲染器，三位人物同时走直线，包含实时人物投影；测试入口隐藏道路、环境物件与光雾，返回地图恢复原状态。正常每方向约 4 秒，慢速每方向约 6 秒。正常录像中走完一段会回到该方向起点，是测试循环行为。预览为 2752 × 2064、60 FPS 横屏，保持原时间轴；原生 VFR 录像保存在构建的独立 gait-normal-iPad／gait-quarter-iPad artifact。

每个方向、每位人物、每种速度各取 12 个时间样本，检查左右脚承重交替、屈膝连接、靴口／鞋尖和裙摆遮挡。抽帧为腿部对照图，不等于检查了录像的每一个编码帧；图集另外检查了全部 600 个待机／行走格的连通性及每方向 24 个不同的行走图像。UI 回归在八方向遍历了全部 24 张姿势。

| 方向 | 正常速度连续帧 | 四分之一速度连续帧 |
| --- | --- | --- |
| 上 | [正常](Normal-Review-Up.jpg) | [慢速](Review-Up.jpg) |
| 右上 | [正常](Normal-Review-NE.jpg) | [慢速](Review-NE.jpg) |
| 右 | [正常](Normal-Review-Right.jpg) | [慢速](Review-Right.jpg) |
| 右下 | [正常](Normal-Review-SE.jpg) | [慢速](Review-SE.jpg) |
| 下 | [正常](Normal-Review-Down.jpg) | [慢速](Review-Down.jpg) |
| 左下 | [正常](Normal-Review-SW.jpg) | [慢速](Review-SW.jpg) |
| 左 | [正常](Normal-Review-Left.jpg) | [慢速](Review-Left.jpg) |
| 左上 | [正常](Normal-Review-NW.jpg) | [慢速](Review-NW.jpg) |

复核样本未再出现此前的膝部拼接、重复鞋尖或小腿贴片倒置。动作观感不只以测试通过判定；此处保留原录像与抽帧供进一步实机对照。

录屏最后 30 个一秒窗口：正常平均 59.53 FPS，最低 55.83，样本最高驻留内存 249.91 MiB；慢速平均 59.70 FPS。地图启动 2.24 秒，最长主线程间隔 0.117 秒。这些是 iOS 18.5 iPad 模拟器和步态测试场景的数据，不代表物理 M1 iPadOS 27 的性能。
