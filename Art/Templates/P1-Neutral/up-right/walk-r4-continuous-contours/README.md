# up-right · r4 continuous contours

主线程独自返修与逐帧审核；无智能体。用户美术认可为空。

此前r3因腿角度扭曲、四肢/衣物边界破碎被用户判退，本版另存。髋关节点移回短裤内部；完整腿轮廓由共用连续网格驱动，取消分段圆补片拼接；源区域按空间轮廓归属，取消肤色阈值抠除轮廓。背心边归躯干，完整手部与手臂采用同一网格域，脚不混入另一侧的像素。头层截去旧颈肩杂片，由躯干提供完整颈部。

`source/registration-input.json` 保存r3注册/作者参数供追溯，不能作为r4最终参数。当前值在 `authoring.json`；`source/head-before-neck-cleanup.png` 保留清理前的头部源。原始生成图和固定注册图均保留。隐藏髋根使用同侧皮肤横截面延入裤内，属于有限关节覆盖，不宣称已建立完整被衣物遮挡的人体。

离线重现：

```sh
python scripts/author-neutral-continuous-contours.py
python scripts/export-neutral-continuous-contours.py Art/Templates/P1-Neutral/up-right/walk-r4-continuous-contours --review Art/Review/P1/neutral-upper-diagonals-r4/up-right
python scripts/verify-neutral-continuous-contours.py
```

使用既有公共装配器和pose-map契约；新增外观不引入ID分支或另一套人体。当前仅idle00与walk01–08，8×120ms。当前查看器只显示GIF静帧，主线程检查的是1×/2×全身完整序列与首尾关系，未宣称已观看连续播放器。详见 `Art/Review/P1/neutral-upper-diagonals-r4/art-review.md`。
