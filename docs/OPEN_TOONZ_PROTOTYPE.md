# OpenToonz 分层步态原型

[下载 1.6.2 build 27 实机测试 IPA](../Downloads/README.md)：使用 SideStore 重签后，从主地图 →“步态测试”→“原图 / 分层蓝靴对照”进入。[实机测试步骤](GAIT_TEST.md)。

## 本轮做了什么

按“离线分层动画”方案，为 P1 的向下步态导出了一组 24 帧步态周期、每帧 256×256 的 RGBA 图像序列。图层分为 `Legs`、`Boots` 和 `Body`，另有可替换的 `BlueBoots` 鞋色层。蓝鞋沿用原鞋轮廓、明暗和位置，仅单独调整颜色，用来验证装备层可以替换。PNG 序列不内嵌播放帧率；实际时序应由动画场景设置。

[下载 OpenToonz/Tahoma2D 序列包](../Art/Prototypes/P1-Down-Layered-Walk.zip) · [单帧分层检查文件](../Art/Prototypes/P1-Down-BlueBoots-Frame12.ora) · [24 帧对照图](../Media/LayeredGait-P1-Down.png)

解压序列包后，将 `P1-Down-Legs.0001.png`、`P1-Down-Boots.0001.png`（或 `P1-Down-BlueBoots.0001.png`）和 `P1-Down-Body.0001.png` 分别作为图像序列导入 OpenToonz 或 Tahoma2D 的 level，按 Legs、Boots、Body 的顺序从后向前合成。包内 `IMPORT-README.txt` 也记录了这些说明。`Reference` 是当前正式角色的逐帧原图，可作比对；`BlueVariant` 是已经合成好的蓝鞋预览。

本轮从现有步态生成器导出，没有在 OpenToonz/Tahoma2D 编辑器中手工绘制关键帧；当前执行环境没有图形界面，因此未声称完成编辑器内的导入往返。ZIP 序列和 `.ora` 分层单帧均已通过结构与 CRC 检查。

现已将逐帧深度顺序合成的 `BlueVariant` 打包为 `LayeredP1BlueVariant` 资源，并接入主地图的“步态测试”面板。点击“原图 / 分层蓝靴对照”后，P1 原帧与分层动画导出的蓝靴帧会并排同步行走；两者共用 P1 的地面阴影轮廓。这个对照用于实机检查离线换装烘焙结果，正常地图中的人物外观保持不变。

iPad Pro 13-inch（M4）模拟器、iOS 18.5 的实际地图 UI 检查通过：原图／蓝靴两组能同步播放，24 帧序列可暂停并单步，退出后回到地图。截图里蓝色鞋面变化清楚可辨，人物标签与底部面板没有遮挡角色。此轮仅验证 P1 向下方向和一种鞋色，也没有覆盖用户的 M1 iPad／iPadOS 27.2。[下载 iPad 对照截图附件](https://github.com/liamchan-rgb/experiment/actions/runs/39042942547/artifacts/12105126129) · [查看测试结果](https://github.com/liamchan-rgb/experiment/actions/runs/39042942547)。

## 保真检查与已知边界

`Reference` 的 24 帧与当前 P1 正面方向游戏图集逐像素相同。把所有腿部片段先合成到 `Legs`、再把鞋合成到 `Boots` 的三层演示合成，在最多一帧中有 342 个不同像素（256×256 单帧的约 0.52%），集中于腿鞋交叠的遮挡区域。游戏原图没有变化；独立拆层合成时的细小差异说明，继续扩展时需将远腿、近腿与鞋的前后关系分层，或在离线合成阶段保留逐帧深度顺序。

这次只验证了一个角色、一个朝向和一种鞋色替换。它证明现有程序化步态可以输出给分层动画工具检查，也证明可单独替换一个装备颜色；没有建立通用角色骨骼或正式换装界面。游戏仍以完整姿势图集运行，这个对照只是步态测试中的美术样例。逐帧原图参考与游戏图集像素一致；蓝靴图集沿用原有逐片深度顺序，只对鞋像素改色。若采用此流程，下一步应补充方向／角色覆盖，再评估如何将换装结果打入图集。

OpenToonz 图像序列说明：[Working in the Xsheet](https://opentoonz.readthedocs.io/en/latest/working_in_xsheet.html)。有官方 Linux/macOS/Windows 安装包的 OpenToonz 分支：[Tahoma2D](https://github.com/tahoma2d/tahoma2d)。

可从仓库根目录重新生成：

```bash
python3 scripts/export-layered-gait-prototype.py
```
