# 左上／右上手臂与腿部返修r2（用户再次判退）

**2026-10-23：用户再次判退，撤回本版内部美术通过/足够交付结论。复查见[主线程问题描述](reinspection-r2-rejected.md)。此前技术证据只保留作历史，不表示动作自然或美术通过。**

用户判退r1：“这走起来手都要剥离身体了”“腿部也是在疯狂闪烁”。主线程撤回原内部美术通过结论，保留旧图与技术记录，当前待审候选为r2。

- **手臂**：同侧原手与前臂共用同一肩枢轴矩阵，肩点固定，禁止分别移动到不同链；摆幅7°，与同侧腿反相。
- **腿**：每侧一条固定原腿，一条连续单调行网格，膝踝不切开；固定矢状骨长后投影到斜后视角。投影后的2D长度自然连续改变，不逐帧换腿形、重分左右归属或换身体。
- **迈步**：增大初版过窄步幅和抬脚量，正常120ms×8帧；足部保持原形平移，头部保留轻微摆动。
- **清理**：静态去掉误归腿层的旧短裤裆边和孤立碎点；原始源部件保留。光栅结果仅允许≤2像素的独立噪声清理，大块直接报错。

[同屏正常GIF](walk-comparison-120ms.gif)、[站姿](idle-comparison-2x.png)、[主线程复核与漏检记录](art-review.md)、[技术核对](validation.json)。每方向实际装配1×/2×九姿势和正常循环见各方向目录。

主线程亲自查看最终实际全身全部帧与01→08→01顺序。当前工具只显示GIF静帧，不能将逐帧和计时核对写成已观看播放器连续播放。实际正常GIF仍照常交付，用户美术认可为空。当前未接App，不包含衣装组合、起停、完整隐藏人体或实机验证。

[浏览器正常同屏动图](https://raw.githubusercontent.com/liamchan-rgb/experiment/850dab930f42d68800e03b3c5c9f0bf2824e22b1/Art/Review/P1/neutral-upper-diagonals-r2/walk-comparison-120ms.gif) · [同屏站姿](https://raw.githubusercontent.com/liamchan-rgb/experiment/850dab930f42d68800e03b3c5c9f0bf2824e22b1/Art/Review/P1/neutral-upper-diagonals-r2/idle-comparison-2x.png)。同屏及两方向GIF、站姿均实测HTTP200，MIME/哈希与本地一致，GIF八帧各120ms；见delivery.json。
