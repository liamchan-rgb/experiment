# P1 独立外观资源包 v1

持握反馈修订见[短柄剑v2](weapon-short-sword-v2/README.md)及[共同闭拳手型](../../Templates/P1-Neutral/down/walk-r3/README.md)，当前组合统一使用新公共r3；旧剑与公共r2保留历史。

当前五个向下头部包已获用户认可；新增两个[衣物／短剑候选包](../../Templates/P1-Wardrobe/down/v1/README.md)待审核。全部面向同一中性人体，不依赖另一件外观运行。首版曾采用仅修腿层归属的r2；当前握持修订统一采用r3公共闭拳，其余63层身体不变，新手型仍待美术认可。

| 类型 | 包 | 当前内容 |
| --- | --- | --- |
| 头发 | [hair-chestnut](hair-chestnut/asset.json) | 栗色短碎发 |
| 头发 | [hair-silver](hair-silver/asset.json) | 银色分层短发 |
| 头发 | [hair-teal-crop](hair-teal-crop/asset.json) | 青黑侧分短发，第三资源接入案例 |
| 五官 | [face-blue](face-blue/asset.json) | 蓝眼及独立眉／鼻／嘴 |
| 五官 | [face-amber](face-amber/asset.json) | 金眼及独立眉／鼻／嘴 |
| 衣物 | [outfit-forester](outfit-forester/asset.json) | 绿外套、深灰长裤与棕靴，八层九姿势 |
| 武器 | [weapon-short-sword](weapon-short-sword/asset.json) | 独立64×96短剑，实际柄心挂右手 |

每包包含 `asset.json`、透明 `png/`（头部96×96、衣物256×256、武器64×96）、独立图层 ORA／SVG、固定坐标的 `authoring.json`、图像工具原 PNG 与提示词／引用摘要。`drafts/` 是未采用稿；只有 `asset.json` 声明的 PNG 参与装配。原稿导出统一整画布缩放，不按 alpha 内容猜位置或修外接框。

[统一制作合同](../../Standards/P1-Parts-v1/README.md) · [公共头板](../../Templates/P1-Neutral/down/walk-r1/shared/head-authoring.svg) · [全部搭配审核与第三资源证明](../../Templates/P1-Modular/down/v1/README.md)

新增兼容资源的步骤：

1. 对公共头板绘制部件，保留同一画布和坐标。发型不含肤色／耳朵，五官不含头部底板；不要参照某款发型移动眼睛。
2. 提交包内 PNG、清单及可编辑源。头部局部资源可在清单九个绑定中引用同一张 PNG；逐帧变形部件则交付全画布映射。
3. 在当前 `Art/Templates/P1-Wardrobe/down/v1/catalog.json` 增加一条登记，使用同一装配命令选择新 ID。无需修改引擎、身体或动作。

底层工具支持面部各槽位独立归属；当前两款五官以整组包展示。新增只有眼睛或只有嘴的包也遵守相同槽位合同，同一槽位不得由两件选中资源同时占用。
