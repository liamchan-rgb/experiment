# 全地图轮廓阴影迭代包

**build 13 已撤回最终交付资格：最终交互检查失败。1.5.1 build 14 替换包正在构建，完成后更新本页。**

历史可用小场景：[1.4.1 build 12](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b12.ipa)。

保存到「文件 → 我的 iPad」，再在 SideStore 点「＋」选择 MeadowJourney-b13.ipa。包标识不变，可覆盖安装。启动后的主地图已启用本轮修改；左上角「光影试验」仍可单独调整光向与显示轮廓网格。

- 将已确认的 alpha 轮廓实时投影推广到地图树木、岩石、栅栏、帐篷、塔、花草、旗帜和三位人物；删除简模投影模式。
- 删除人物着色器重复交换膝下 UV 的逻辑，完整动画帧负责姿态，投影读取同一帧。
- 道路改为一张并集距离遮罩，交叉口不再叠色；裸土降低亮度和饱和度，加入细微轮迹、碎石、稀草和软化的草土交界。
- 保持旗杆在建筑后方，屋顶遮住杆身下段。

人物接触帧已自行对照；阴影和道路画面由用户继续反馈。最终源码 `42f0d68` 的 Swift／Metal 编译、设备 Release 归档及 IPA CRC、arm64、Metal 资源与可执行权限校验已通过；8 项原生检查通过，UI 缩放操作查询超时；详见下方迭代日志，等待 build 14 修正。包继续采用 build 11 已可安装的 ZIP_STORED 格式。

[迭代日志](../docs/ITERATION_STATUS.md) · [实现记录](../docs/SHADOW_LAB.md) · [来源与校验值](MeadowJourney-build13.json)

历史：[1.4.1 build 12 小场景](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b12.ipa) · [build 12 元数据](ShadowLab-build12.json)。
