# 上斜裤靴 v2 · 修正腿型候选

替换原上斜lower-v1，原两个r6底模、动作、两衣型、两发色、背剑与公共装配器均不修改。

source/generated.png是图像工具的独立衣料/鞋靴原稿。紧凑导板约束膝、踝和鞋底位置；按固定全画布缩放至192×192，四个96×96源片以固定原点登记到256×256。paintOffsets只平移绘制颜色以对齐原鞋底，无单腿横向/纵向缩放。最终轮廓来自原腿/骨盆alpha的几何导板加1px衣料余量，未采样原皮肤/安全衣颜色。缺少出血的细小边缘只延用最近的原稿不透明RGB，范围上限6px；source-audit证明全部衣物RGB来自原独立衣物原稿。

裤腰根部补齐原骨盆覆盖，裤腿/膝/小腿保留原腿轴，低靴语义源区从y202开始，原膝y189；旧靴层y195起。原靴宽31–35px，新靴25px，近/远鞋底高度保留。裤靴通过原共同UV离线导出，不逐帧手绘补洞、不修改原动作。每方向13姿势（站立、8行走、2起步、2停步），包含PNG、ORA/SVG及asset.json。

source/保留位移失准首稿、边缘未覆盖稿及最终未采用的过大出血稿。它们都不是最终装配。新外观尚待用户评价。

导出：python scripts/export-upper-leg-repair.py；检查：python scripts/verify-upper-leg-repair.py；重导证明：python scripts/reexport-upper-leg-repair.py。
