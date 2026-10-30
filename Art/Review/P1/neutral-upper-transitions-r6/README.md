# 上斜起停 r6 候选

用户已认可左上/右上 r5 整身站姿及正常步态，本轮继续同一底模的指定起步与停步路径。由主线程独自制作和审核，无智能体参与。新过渡尚未获得用户认可。

- [左右同屏正常起停 GIF](start-stop-120ms.gif)：idle00停留480ms → start01/02 → 原八帧步行两轮 → stop01/02 → idle00停留480ms；所有动作帧120ms。
- [同屏正常步行 GIF](walk-120ms.gif)：保留原8×120ms循环。
- [整身站姿](idle-review-2x.png)。左右分别见 `up-left/`、`up-right/`。
- [主线程美术检查](art-review.md)、[技术检查](validation.json)、[可复现导出](reexport-validation.json)、[时序](sequence.json)。

原18张认可帧及144张分层逐字节不变。每方向新增两起步、两停步姿势，保留同一身体/头部/裤口域；右上重用已校正光照源和镜像语义、挂点。当前指定idle00接walk01、walk08收至idle00，不代表任意步相急停或完整隐藏人体。当前工具不能连续播放，主线程检查的是1×/2×完整帧序列，未声称观看连续播放器。无App、设备测试或IPA工作。

复现：在仓库根目录执行 `python scripts/reexport-upper-transitions.py`。新动作沿用公共pose-map合同，无外观ID运行分支；后续独立衣物须覆盖新增四姿势。

[浏览器正常起停动图](https://raw.githubusercontent.com/liamchan-rgb/experiment/53e3a9b2077a1f218c21ecc1ac7f2d849a31b536/Art/Review/P1/neutral-upper-transitions-r6/start-stop-120ms.gif) · [整身站姿](https://raw.githubusercontent.com/liamchan-rgb/experiment/53e3a9b2077a1f218c21ecc1ac7f2d849a31b536/Art/Review/P1/neutral-upper-transitions-r6/idle-review-2x.png)。HTTP200、MIME/哈希及22帧时序均已核对；交付回执见delivery.json。
