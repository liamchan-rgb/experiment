# 仅供项目Codex：动作输出规格，不是Chat绘图任务

Chat只交五视角四层母版。以下104姿势/416引用是Codex调用既有挂载与表面映射后批量生成的结果；不逐帧重新画，不要求Chat制作运行清单。

# 图层、坐标、命名与帧规格

## 固定输入与实际左右

沿用 `p1-eight-way-base-v1` 与当前 `motion.json`，身体及动作原图摘要不变。`pose-map` 已是注册好的256整画布，不再套 `bodyTranslation`、旧方向 registration 或源步相重排；它们保留在记录中，不是让新衣服再次移动一次。

当前真实 `down / idle / frame=0` 的部分关节点如下，单位为256画布像素；其他103姿势必须读各自记录，不能复用这些数值。

| 关节 | x,y | 在正面画面的位置 |
| --- | --- | --- |
| neck | 128,132 | 颈根 |
| shoulderLeft / elbowLeft / wristLeft | 144,136 / 150,153 / 152,167 | 画面右边，角色自身左侧 |
| shoulderRight / elbowRight / wristRight | 114,136 / 108,153 / 106,167 | 画面左边，角色自身右侧 |
| hipLeft / hipRight | 139,175 / 121,175 | 髋部参考，不是给前裙甲加裤腿 |

示例关节导板用青色标角色左链、橙色标角色右链；白色为颈根，粉色为髋。标线/文字只能在审核图里，不能出现在正式PNG。背向和侧向的屏幕左右不靠正面结论猜，仍按关节名取值。

## 四层的所有权

| layer键 | 应包含 | 不得包含 |
| --- | --- | --- |
| `outfit.torso` | 选定衣身/胸腹甲、领口、腰带/扣件 | 独立摆动的肩饰、皮肤、手、裤子、武器 |
| `outfit.sleeve.left` | 自身左侧肩口/肩甲/袖子/袖口，隐藏接合余量 | 右袖、左手、底衣白边残片 |
| `outfit.sleeve.right` | 自身右侧对应部件 | 左袖、右手、上版蓝衣残片 |
| `outfit.hem.front` | 前护裙/衣片，腰带下隐藏上缘、随髋腿变化的下缘 | 整条裤腰、裤腿、背剑、地面阴影 |

肩甲的视觉接合可藏到衣身后，但像素仍属于对应袖层；不能把同一肩片同时画进torso和sleeve，造成双轮廓。相邻层需要稳定隐藏重叠，大小依原姿势实际接合决定，不能用统一拉宽/移动手臂来补洞。

## 每张图的硬规格

- PNG，真实RGBA，固定256×256，sRGB/straight alpha；不可用RGB白底/JPEG/棋盘格截图替代。
- 左上原点，x向右、y向下。全部层保留同样画布与透明边距，不按内容裁切或居中，不逐帧缩放，不碰画布边界。
- alpha=0像素RGB归零。半透明像素可用于必要边缘，不用软糊光团、照片渐变或随机噪点填造型；不能简单阈值化啃掉金边/轮廓。
- 正式衣物层没有人体、文字、格线、背景、地面投影、武器和粒子。材质自阴影允许；正常颈部露肤由原身体提供。
- 没有前裙甲时，只有该槽可以明确使用透明占位并在authoring写原因。不能把所有层设透明、依靠原衣服仍能显示而称新甲完成。

## 方向、帧和文件名

方向固定：`down, down-left, left, up-left, up, up-right, right, down-right`。

| clip | JSON frame | 目录片段 | 每方向数量 |
| --- | --- | --- | --- |
| idle | 0 | `png/down/idle/00/` | 1 |
| walk | 1…8 | `png/down/walk/01/`…`08/` | 8 |
| walk-start | 1,2 | `png/down/walk-start/01/`、`02/` | 2 |
| walk-stop | 1,2 | `png/down/walk-stop/01/`、`02/` | 2 |

以上每个目录都有四个按layer键命名的PNG，例如 `outfit.sleeve.left.png`。帧号在JSON里是整数，目录用两位；不写 `idle frame=1`，不写 `walk frame=0`。

一个真实的当前蓝衣绑定长这样，路径相对它自己的包目录：

```json
{
  "direction": "down",
  "clip": "idle",
  "frame": 0,
  "layers": {
    "outfit.torso": "png/down/idle/00/outfit.torso.png",
    "outfit.sleeve.left": "png/down/idle/00/outfit.sleeve.left.png",
    "outfit.sleeve.right": "png/down/idle/00/outfit.sleeve.right.png",
    "outfit.hem.front": "png/down/idle/00/outfit.hem.front.png"
  }
}
```

完整真实范例见[蓝衣asset.json](https://github.com/liamchan-rgb/experiment/blob/fix/build33-face-grounding-camera/Art/Parts/P1-v1/eight-way-v1/wayfarer/asset.json)。新包改用新的ID、路径和真正新画稿。`sourceFiles`列出存在的authoring/palette/可编辑源；不能列不存在的PSD，也不能为通过检查放一个空文件。运行清单可对照上述原蓝衣asset；本任务templates目录只提供母版清单，不是运行清单。

## 动作与起停边界

行走独立GIF：`walk01→…→walk08→01`，8帧、各120ms、总960ms、循环。当前游戏移动×3不改变本任务书的原画审核时基。

| 方向 | entryPhase（0基） | 首张进入的walk（1基） | exitPhase（0基） | 最后退出的walk（1基） |
| --- | --- | --- | --- | --- |
| down | 1 | 02 | 0 | 01 |
| down-left | 4 | 05 | 3 | 04 |
| left | 4 | 05 | 3 | 04 |
| up-left | 4 | 05 | 3 | 04 |
| up | 4 | 05 | 3 | 04 |
| up-right | 0 | 01 | 7 | 08 |
| right | 0 | 01 | 7 | 08 |
| down-right | 0 | 01 | 7 | 08 |

每方向起停预览：`idle→start01→start02→从本向入口开始两圈walk→stop01→stop02→idle`。22帧，首尾idle各480ms，中间20帧各120ms，总3360ms。不要把正下start02硬接walk01：其入口是walk02。`08→01`与起停的真实入口/出口都要看。

原模板的收步会先到指定出口，不是任意相位制动。这里只给衣服适配原动作，不要求重画新制动帧。runtime图集索引和阴影接入归项目Codex处理，Chat不改游戏时钟或runtime facing来迁就画稿。

## 对应的层序

以当前motion每一帧的 `drawOrder` 为准。不能全八向共用一张“手臂永远在衣身前”的表，也不通过把所有袖子放顶层来遮缝。新衣只占原四槽，不擅自新增 `outfit.hem.back`、披风或独立肩甲槽；若设计必须新增层序，应另列合同扩展，当前包不能标零动作改动完成。
