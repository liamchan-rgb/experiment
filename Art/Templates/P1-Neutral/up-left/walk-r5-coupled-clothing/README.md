# 左上 r5 · 肢体连接及短裤跟随返修

本轮按用户要求仅修左上，由主线程亲自修复和审核，无智能体。r4因拼接痕、运动间隙、残边和腿动裤子不动被判退，原目录保留。

本版将中性背心/颈部与安全短裤分为独立源。裤腰随骨盆，左右裤口跟随各自大腿，肩口/裤腰/裤口使用共同的连接变形域；腕部的手与臂也使用相同映射分配像素。保留原稿宽阔的大腿根，不再只复制裁窄后的178行；隐藏根部有限延入裤内。清理躯干和手部混入的另一侧肢体轮廓。近侧手置于裤子前，肩部隐藏覆盖由背心保留。

来源和固定注册图保留在source；`registration-input-r4.json`为历史参数，当前参数看authoring.json。输出components包含独立短裤/背心和完整手臂检查图，运行层仍为既有pose-map语义槽。未新增外观ID分支或另一套人体。

```sh
python scripts/author-neutral-coupled-clothing.py Art/Templates/P1-Neutral/up-left/walk-r5-coupled-clothing
python scripts/export-neutral-coupled-clothing.py Art/Templates/P1-Neutral/up-left/walk-r5-coupled-clothing --review Art/Review/P1/neutral-up-left-r5
python scripts/verify-neutral-coupled-clothing.py
```

9姿势为idle00及walk01–08，正常120ms/帧。用户美术认可为空；未修右上，未制作新外观/起停或IPA。当前查看器只显示GIF静帧，逐帧全身审核不等于连续播放器观看。详见审核目录art-review.md。
