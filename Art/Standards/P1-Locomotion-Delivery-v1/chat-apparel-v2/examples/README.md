# 示例：五视角母版复用，不逐帧手画

| 示例 | 看什么 | 使用边界 |
| --- | --- | --- |
| `01-five-master-guides-2x.png` | 同一人体五个静态视角、自身左右与关节 | 标线只作参考，不能进衣物PNG |
| `02-four-layers-and-composite-1x.png` / `-2x.png` | 蓝衣各静态view的四层与合成 | 最后一列整人图不是衣物资源 |
| `03-one-master-to-eight-frames.png` | 历史五视角母版通过原表面映射生成8walk，证明不用手画8遍 | 旧B5造型被认为太朴素，仅作技术示例，不是新设计认可 |
| `03-reuse-demo-normal.gif` | 上述程序导出的8×120ms循环 | 离线教学，不是新甲候选或设备录屏 |
| `body-guides/<view>.png` / `<view>-joints.png` | Chat对齐的5个原人体idle及5张关节导板 | 青色自身左，橙色自身右，白色颈根，粉色髋；人体仅锁定参考 |
| `blue-coat-masters/` | 五view×四张256RGBA静态分层位置示例，共20张与清单 | 只示范位置/拆层，不保证远侧隐藏裁片完整；不能给蓝衣改色当新甲 |
| `historical-b5/` | 真正的旧五视角PNG/可编辑SVG/色板 | 仅技术参考；默认新任务20张256静态母版，不强制旧1774×887总图排版 |
| `rune-left-cuff-approved.gif` / `rune-right-cuff-approved.gif` | 历史符文甲正左/正右袖腕贴合 | 认可仅该次两方向修正，不外推其他方向/战斗/新甲 |
| `rune-cuff-approval-scope.json` | 上述认可原范围 | 不能填到新资源artApproval |
| `HISTORY-TOO-PLAIN-*.png` | 旧款整身设计反例 | 明确不作新设计通过范本 |
| `input-snapshot.json`、`reuse-verification.json` | 输入摘要与母版→8帧实际像素核对 | 技术验证不等于美术认可 |

蓝衣20张是从当前静态参考姿势取出的真实分层，供Chat明确位置与部件归属；不是说蓝衣历史上也由本次五母版导出器生成。

隐藏袖面也要完整，不只从整人图抠“看得见的部分”。教学板背景/文字另铺，正式素材取真实透明PNG，不从板子截图裁图。

蓝衣历史PNG中个别alpha=0像素有不可见RGB残留。本教学副本只将这些不可见RGB清零，alpha及所有可见RGBA逐像素保持；原项目PNG不改。输入/副本摘要与数量见blue-coat-masters/source/reference-normalization.json。嵌入SVG使用同一份已规范化的四层副本，不影响原造型。

`historical-b5/starlightArmor/registered-patterns/`另附现有采样器实际使用的20张注册后裁片母版（五视角四层），包括可见区域后面的袖面。它们尚未套逐帧运动/可见区域裁片，适合对照“母版”和最终静态层的区别；旧造型仍是历史技术示例，不作新设计认可。蓝衣正左远侧小袖片是最终静态可见层，不能照着这一小片当新母版的全部隐藏袖面。

旧1774总图的分组名是历史采样排版标签，左右归属需经其映射解释；新母版以本包关节导板、自身左右命名和注册裁片为准，不按旧总图的屏幕左右直接换名。
