# 右上 r5 · 基于已认可左上r5的镜像

主线程独自制作和审核，无智能体。用户授权采用镜像方式制作右上，但尚未认可本方向新图。左上认可范围及原展示哈希见 `Art/Review/P1/neutral-up-left-r5/approval.json`，不改变原素材。

所有动作帧、部件透明边界、关节、脚底标记、支撑脚及近远层次都由左上r5同步镜像。左右语义交换，帧序与120ms时长保留；头部96px局部坐标也同步反射，保持新方向挂点为正手性。裤子跟随和近侧手遮挡继承认可版。

直接翻图会反转灯光。本版由imagegen生成一份固定左上方光照参考，主线程将其颜色离线绑定到同一套源像素坐标，再用于所有动作帧；保留认可图的镜像alpha/轮廓、原描边和隐藏源。没有逐帧生成新人物或自动拟合运动帧，运行时仍使用普通pose-map。

```sh
# UV数据已留存；需要重建时，在隔离副本中重现认可版导出并检查原画面不变。
python scripts/capture-neutral-pose-uv.py Art/Templates/P1-Neutral/up-left/walk-r5-coupled-clothing Art/Templates/P1-Neutral/up-right/walk-r5-mirrored-up-left/source/approved-left-uv
python scripts/author-neutral-mirror-lighting.py Art/Templates/P1-Neutral/up-right/walk-r5-mirrored-up-left
python scripts/export-neutral-mirrored-pose-map.py Art/Templates/P1-Neutral/up-right/walk-r5-mirrored-up-left --review Art/Review/P1/neutral-up-right-r5-mirror
python scripts/verify-neutral-mirrored-pose-map.py
```

当前仅中性底模idle00/walk01–08。不代表非对称头发、五官、衣物或背剑也可以直接反转；新装备应按方向校正。没有完整隐藏人体、起停、App/设备测试或IPA工作。主线程检查1×/2×整身全部帧和首尾序列，查看器不能连续播放，不声称完成连续播放器观看。
