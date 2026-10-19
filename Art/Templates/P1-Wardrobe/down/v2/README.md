# 向下衣物／短剑 · 握持修订 r2，用户要求继续修改

2026-10-19：用户指出本版仍为反手握柄、剑宽面正对镜头；后续又指出护手未随剑身旋转。后续的 v3 单帧也被判定不通过，用户要求继续修改；当前回审为 [v4 单帧](../v4/README.md)。本目录图像保留，不代表用户认可。

用户反馈 v1“剑没有握持感”。旧方案只验证剑柄与拳头相交，柄却偏长、护手离拳底远，原拳头也没有拇指压指和卷曲手指的明确层次。此修订保留 v1 全部原文件，继续审核同一组向下动作。

[正常速度前后对照](walk.gif) · [站姿与握持放大](review.png) · [九帧手部放大](grip-closeups.png) · [九张完整姿势](poses.png) · [手／剑独立图片](independent-parts.png) · [验证记录](validation.json)

预览左列旧稿、右列修订，上方完整人物、下方跟随握点的局部放大。GIF 只播放 01–08，每帧 120 ms，无新慢速文件。

## 修正内容与复用方式

- [公共底模 walk-r3](../../../P1-Neutral/down/walk-r3/README.md)：只更新右手闭拳。拇指压在弯曲手指前，指节明确收拢。一个独立手稿按原九个握点整数平移，空手和持剑使用完全相同的新公共底模。不是为每把武器做一套身体，也没有按武器 ID 的手型分支。其余 63 张身体图层与 r2 逐字节相同，头部和衣物图层不变。
- [独立短柄剑](../../../../Parts/P1-v1/weapon-short-sword-v2/asset.json)：缩短握柄，护手贴近拳底，保留原短剑设计和垂直向下携带方向；局部 pivot=(32,31)。剑仍只有武器像素，手型只含皮肤与指节，二者分别保存；没有把剑柄画进手里。
- 原装配器和规范未改，动作的姿势、关节、握点、角度和层序不变。新动作文件只更新公共底模清单摘要。共同右手本身属于新美术，不冒充此前已认可的人体图像；整组仍待用户确认。

本阶段只有一个公共闭拳姿势，空手也呈闭拳。尚未加入松手、双手握持、挥砍等其他手部动作；这些需要之后按动作／持握类型制作，不按具体武器 ID 拼配套身体。

## 复现

在仓库根目录使用 Python3、Pillow、NumPy、jsonschema：

```sh
python3 scripts/export-common-grip-hand.py
python3 scripts/export-wardrobe-part.py Art/Parts/P1-v1/weapon-short-sword-v2
python3 scripts/review-sword-grip.py
```

实际装配命令：

```sh
python3 scripts/compose-character-parts.py \
  --catalog Art/Templates/P1-Wardrobe/down/v2/catalog.json \
  --motion Art/Templates/P1-Wardrobe/down/v2/motion.json \
  --base p1-neutral-down-walk-r3 \
  --asset p1-hair-chestnut-v1 --asset p1-face-blue-v1 \
  --asset p1-outfit-forester-v1 --asset p1-weapon-short-sword-v2 \
  --direction down --out /tmp/p1-grip
```

删除武器参数就是同一只空拳；发型、五官和衣物仍各自独立选择。此前完整 ZIP 是旧持握 v1，本次修订源在本目录、公共 r3 和新武器包中，不把旧 ZIP 当作本修订下载包。

## 检查及限制

24种组合／216个姿势在内存中复查，同一只手不随武器、衣物或头部选择改变；修订差异局限于右手和剑，原头部、衣物及其他身体层一致。1161份已有图片／装配器／规范／服装清单保持不变。

九次接触检查确认：手指覆盖短柄核心区域，护手与拳底相接，手指仍在武器前景，腕部与原手臂局部重叠至少两行像素。九份公共底模与一份武器 ORA 重合成一致，SVG结构有效，两份生成原图、实际提示词和参照摘要可追溯。正常GIF逐帧时长、顺序和量化像素核对通过。

这些只证明资源结构、接缝和相对位置，不能替代自然握持的美术认可。当前仅向下单手垂持，其他方向、攻击动作、正式运行时和设备测试未实施。
