# 左上／右上中性底模r1（用户判退）

**2026-10-23：用户指出手臂像剥离身体、腿部疯狂闪烁。本版内部美术通过结论撤回，原稿及历史技术证据保留；当前返修见../neutral-upper-diagonals-r2/。**

本轮按用户授权同时推进两个斜后方向。每方向 idle00 + walk01–08；步行固定120ms/帧、8帧循环。新方向美术认可仍为空。

## 原稿与返修

- 旧穿衣步态仅提供镜头、空间和历史落脚问题参考；新中性人物用共同解剖左右相位，01–04左支撑，05–08右支撑。
- 两方向单独生成，保留批量判退稿与逐帧原稿。批量稿曾把斜后头画成侧脸、重复同一支撑腿，未用作完成稿。
- 主线程判退支撑侧反复跳变、重复姿势、比例改变和重复手臂；右上加粗导板曾偏半周期，已在作者数据中修正相位，原导板保留，不作为已测量关节。
- 每方向复用同一份idle头部／躯干，按实际源图肩／髋锚点作固定整数平移接入四肢。不在运行时按alpha边界适配、缩放或添加外观ID分支；离线源组件按作者肩髋／足底标作固定注册，矩阵和原尺寸保留。头颈有轻微独立枢轴摆动。
- 左上03返画稿站立腿过长，被主线程判退；保留原r1腿，用髋枢轴刚性转动补摆腿passing，不拉长／缩短肢体。
- 右上头部重新统一左上方受光；生成原稿、固定注册和原颈部接缝依据单独保留。

## 本轮边界

这是两方向可分层的可见中性人体与基本idle／walk候选，不表示所有隐蔽解剖、独立衣物／头发／面部组合、背负道具角度或起停动作已完成。未接入App。主线程最终整身／连续帧复核与技术验证记录另存。

- 正常速度同屏动图：`walk-comparison-120ms.gif`
- 同屏站姿：`idle-comparison-2x.png`
- 每方向1×／2×九姿势与正常循环：`up-left/`、`up-right/`
- 实际公共装配器复合与检查：`validation.json`
- 主线程美术返修依据：`art-review.md`
- 发布直链核对：`delivery.json`

主线程已检查最终实际装配的1×/2×九姿势，按01→08→01核对序列；GIF为8×120ms。当前查看工具仅展示GIF静帧，未将其记录为已实际观看连续播放。技术核对通过不代替用户对动图的美术认可。

[浏览器正常同屏动图](https://raw.githubusercontent.com/liamchan-rgb/experiment/ee8b719d8ae477eddcd9579e27f3cd2b38993a33/Art/Review/P1/neutral-upper-diagonals-v1/walk-comparison-120ms.gif) · [同屏站姿](https://raw.githubusercontent.com/liamchan-rgb/experiment/ee8b719d8ae477eddcd9579e27f3cd2b38993a33/Art/Review/P1/neutral-upper-diagonals-v1/idle-comparison-2x.png)。同屏及两方向GIF、站姿均实测HTTP200，MIME/哈希与本地一致，GIF八帧各120ms；见delivery.json。
