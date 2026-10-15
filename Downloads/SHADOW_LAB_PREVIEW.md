# 全地图轮廓阴影迭代包

[下载 1.5.1 build 14 IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b14.ipa)。请用此包替换此前先行提供的 build 13；build 13 的最终 UI 检查失败，已撤回最终交付资格。

保存到「文件 → 我的 iPad」，再在 SideStore 点「＋」选择 MeadowJourney-b14.ipa。包标识不变，可覆盖安装。启动后的主地图已经启用本轮修改；左上角「光影试验」仍可单独调整光向和显示轮廓网格。

- 已确认的 alpha 轮廓实时投影推广到地图树木、岩石、栅栏、帐篷、塔、花草、旗帜和三位人物；删除简模投影模式。
- 删除人物着色器重复交换膝下 UV 的逻辑，完整动画帧负责姿态，投影读取同一朝向帧。
- 道路改为全图距离并集遮罩，交叉口只合成一次；使用低饱和裸土、细微轮迹、碎石和稀草，并软化草土交界。
- 旗杆保持在建筑后方，由屋顶遮住杆身下段。
- 主地图统一由场景驱动，背景投影上限 30fps，镜头／动作帧变化时即时刷新，修正此前候选包的交互超时。

构建 38775110277 已通过 Swift／Metal 编译、设备 Release 归档、8 项原生资源／GPU／步态检查，以及 1 项播放／缩放／复位／试验场往返的 UI 检查（合计 9 项，0 失败）。IPA 的版本、CRC、arm64、Metal 资源、可执行权限和 ZIP_STORED 格式已校验。

三位人物八方向接触帧已放大对照；阴影和道路画面由用户继续反馈。此轮不检查这些效果图片、不录制新的验收视频。

[迭代日志](../docs/ITERATION_STATUS.md) · [实现记录](../docs/SHADOW_LAB.md) · [来源与 SHA-256](MeadowJourney-build14.json)

历史可用小场景：[1.4.1 build 12](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b12.ipa)。build 13 的失败记录保存在 [MeadowJourney-build13.json](MeadowJourney-build13.json)。
