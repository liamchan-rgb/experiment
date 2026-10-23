# 左上／右上中性人体 r4 返修

r3已被用户判退。本版由主线程独自修复并检查，不使用智能体。

- [正常速度同屏GIF](walk-comparison-120ms.gif)：8帧×120ms，左为左上，右为右上。
- [同屏站姿](idle-comparison-2x.png)
- [1×完整九姿势](both-directions-nine-poses-1x.png)
- [主线程检查及边界](art-review.md)
- [技术检查](validation.json)

当前用户美术认可为空。查看器仅显示GIF静帧，不能把逐帧检查写成连续播放器验收。没有App、模拟器、设备运行或IPA改动。

[浏览器正常同屏GIF](https://raw.githubusercontent.com/liamchan-rgb/experiment/295e0ae27829a3b2f496eed11dc2be6cad8a4480/Art/Review/P1/neutral-upper-diagonals-r4/walk-comparison-120ms.gif) · [同屏站姿](https://raw.githubusercontent.com/liamchan-rgb/experiment/295e0ae27829a3b2f496eed11dc2be6cad8a4480/Art/Review/P1/neutral-upper-diagonals-r4/idle-comparison-2x.png)。同屏及两方向GIF、站姿均实测HTTP200，MIME/哈希与本地一致；GIF八帧各120ms、无限循环。回执见delivery.json。
