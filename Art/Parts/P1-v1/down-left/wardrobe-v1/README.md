# 左下独立衣物/裤靴/背剑 v1 · 候选

沿用p1-neutral-down-left-walk-r1身体与13姿势、现有四个头部包。新增绿短上衣、蓝分叉短外套、共用灰裤/低靴、背剑四个pose-map包；两衣型×两发型×两五官×空背/背剑=16搭配208张。

完整人物画布上的衣物绘制只提供RGB；动作几何与衣物matte来自固定原人体坐标、1px衣料厚度，靴底不向下扩展原源脚底。没有按外观切身体、对肢体横纵缩放、逐帧绘脸或运行时修图。所有衣物经同一源UV，裤腰/裤口随原骨盆和两腿，衣袖随原肩肘腕；手部拥有完整轮廓。

首张无头衣物图放大躯干，已退回，未用于登记；最终用完整原人物画布重绘。背剑保留同一右肩斜背物理位置，前视自然由头、躯干及腿遮挡；首稿下巴旁和腿边细线已校正，不改成中轴竖背。

源、提示词、登记/UV/matte和逐层PNG/ORA/SVG留存。重现：`python scripts/reexport-down-left-wardrobe.py`。公共compositor/contract/profile未改，原身体/动作和8044份旧文件保持。新外观无用户认可，无App/IPA改动。

[正常全身行走](../../../../Review/P1/modular-down-left-wardrobe-v1/outfits-walk-120ms.gif) · [起停](../../../../Review/P1/modular-down-left-wardrobe-v1/outfits-start-stop-120ms.gif) · [站姿](../../../../Review/P1/modular-down-left-wardrobe-v1/outfits-idle-2x.png)
