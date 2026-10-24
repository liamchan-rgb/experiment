# 右下中性动作模组 r1 · 认可左下的镜像候选

用户要求“没问题，可以试一下镜像来做右下的动画”。来源为已认可左下r1的站姿、8帧行走和指定起/收步，共13姿势。左下原稿/动作/认可素材保持；新右下尚未获用户美术认可。

逐语义层按x′=255−x、y′=y反射，同时交换左右臂/手/腿、关节名、支撑脚、脚底标记和近远层序；朝向[-1,1]→[1,1]。右下近侧为角色右侧（屏幕左），远侧为角色左侧（屏幕右）。不换人体、缩放肢体或改变步相/时长。13×8层的alpha与源层镜像逐像素一致。

头部96px局部坐标同时反射，局部原点[84,61]、颈根[44,70]；源UV校准了Pillow系数取整在两帧产生的边界差异，最大仅0.0015px元数据平移，实际头部UV、RGBA与反射帧逐像素相同，不改人体、轮廓或关节。记录在mirror-authoring.json。

直接镜像的高光方向不采用。单张imagegen参考只提供左上光照颜色，绑定到同一源UV后复用所有帧；原始alpha、描边及隐藏颜色保持，超出2px的单枚不确定材质边界保留原色。肤色与暖白衣物取色分开，修掉首轮把衣料/阴影误采到臂或背心的结果。参考图的形体、背景及alpha均不导入。

重现（仓库根目录）：

```sh
python scripts/reexport-down-right-mirrored-motion.py
```

[正常行走](../../../../Review/P1/neutral-down-right-r1-mirror/walk-120ms.gif) · [正常起停](../../../../Review/P1/neutral-down-right-r1-mirror/start-stop-120ms.gif) · [站姿](../../../../Review/P1/neutral-down-right-r1-mirror/idle-review-2x.png) · [复核](../../../../Review/P1/neutral-down-right-r1-mirror/art-review.md)

包含源图/光照参考与生成记录、源UV、局部头导板、逐层PNG、ORA/SVG和公共合同。公共compositor/contract/profile保持。仅中性模组，独立发型/五官/衣物/武器、完整隐藏人体及任意步相中断待后续，不含App/设备/IPA。
