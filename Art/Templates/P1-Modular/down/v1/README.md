# P1 向下独立头部换装 v1 · 用户已认可

2026-10-19 用户回复“没问题”，本组六种头部搭配已认可，见 [approval.json](approval.json)。以下制作与验证记录保留其提交时语义；各原清单／图像中的候选标记不再代表当前认可状态。当前转入[独立衣物与短剑](../../../P1-Wardrobe/down/v1/README.md)回审。

共同中性站姿与八帧行走已获用户认可，见[步态认可](../../../P1-Neutral/down/walk-r1/approval.json)。本轮新交付三款独立发型、两款独立五官及清单驱动装配工具；当前只审核这一组头部资源，不把文件检查当作美术认可。

[正常速度循环](walk.gif) · [头部放大图](heads.png) · [完整人物](review.png) · [独立部件，不铺底模](independent-parts.png) · [验证记录](validation.json) · [完整工具与源文件包](../../../../Prototypes/P1-Modular-Head-v1.zip)

预览从左到右为栗发、银发、青黑短发；上排蓝眼，下排金眼。六种搭配使用完全相同的身体和动作。只播放 01–08，每帧 120 ms、周期 960 ms；本轮不生成慢动作。

## 已实现的可复用部分

- 发型包只含头发，五官包只含眼、眉、鼻与嘴的独立透明层；没有脸皮、耳朵、下巴底片，也不要求另一款外观配套。各包自带 96 × 96 PNG、清单、ORA／SVG 和图像工具源稿。
- 同一方向的发型和五官图复用到站姿与八帧，以动作中的 `headToCanvas` 固定变换挂载。换发型不改变五官位置，换五官不改变发型；身体八层一张不换。
- `scripts/compose-character-parts.py` 读取资源清单和 `motion.json` 层序，支持 `head-local`、`pose-map`、`socket` 三种空间。ID 只用于查找，代码中没有栗发、银发、金眼等专用分支，也不按内容外接框裁缩。
- 初始两款发型 × 两款五官验证后，固定工具、人体、坐标与原资源，再制作青黑短发。第三款只增加一个资源包及一条目录登记，即产生另外两种搭配。

各资源包位于 [`Art/Parts/P1-v1`](../../../../Parts/P1-v1/README.md)。三个发型均是当前视角的短发；长发及会变形的衣物应按合同提供后层或逐帧全画布，不能把一张任意图片当作完整动作资源。

## 第三件资源接入证据

在第三发型目录尚不存在时记录 [integration-before-third.json](integration-before-third.json)，冻结 114 份工具／标准／人体／原外观文件及 44 份原组合输出。加入第三发型后，[integration-after-third.json](integration-after-third.json) 确认这些文件全部逐字节一致；登记清单仅追加一项。装配器、人体、动作、合同与原四件资源修改数均为零。

这是第三款**头发**的技术接入证明；新美术仍待审核，不等于衣物、武器、八方向及完整游戏换装验收完成。

## 使用同一工具装配

在仓库或完整下载包根目录安装 Python 3 及 Pillow、NumPy、jsonschema，然后运行：

```sh
python3 scripts/compose-character-parts.py \
  --catalog Art/Templates/P1-Modular/down/v1/catalog.json \
  --motion Art/Templates/P1-Modular/down/v1/motion.json \
  --base p1-neutral-down-walk-r1 \
  --asset p1-hair-teal-crop-v1 --asset p1-face-blue-v1 \
  --direction down --out /tmp/p1-composed
```

导出站姿＋八帧及素材摘要。新增资源按合同交付包，并在 `catalog.json` 增加登记，命令选择新 ID 即可；不编辑装配器、底模或动作。

```sh
python3 scripts/check-character-part.py Art/Parts/P1-v1/hair-teal-crop/asset.json
python3 scripts/test-character-compositor.py
python3 scripts/package-modular-head-review.py
```

`catalog.json` 中的路径相对于项目根目录。资源清单内部的 PNG 和可编辑源路径仅指向包内文件，拒绝路径逃逸、重复层归属、不兼容人体及缺失动作；不会补选另一件外观。

## 验证与范围

五个真实资源包通过合同检查，54 个搭配姿势与装配输出／图集一致；所有组合中的身体图层不变，头部以下合成像素与认可动作一致。每款头发在更换面部时图层不变，每款面部在更换头发时图层不变；五官位于固定区域、刘海避开眼部保留区。五份 ORA 重合成与实际图层一致，SVG 有效；十一份图像工具原稿与修订、真实提示词及参照摘要保留，弃稿不参与运行。

19 项装配器集成检查和 19 项既有合同检查通过，包括 ID 改名、九帧原样输出、固定头部挂载、全画布服装位置、武器旋转握持与手层遮挡、拒绝缺帧／双重身体／越界和错误层序。服装和武器的检查使用合成测试素材，**尚未以真实衣物或武器美术验收**。

正常 GIF 的八帧、120 ms 时长、顺序、调色后像素和无限循环通过；644 份此前 PNG／GIF 和全部已认可动作不变。可编辑文件尚未在桌面绘画软件内做 GUI 往返；未修改正式应用、IPA 或历史在线演示，未做设备测试。

完整包内含当前独立外观的全部工具源稿与弃稿、固定人体的运行图层和可编辑源、合同及装配脚本，可在独立目录运行；人体较早的完整制作历史仍以仓库为准。本轮提供可直接查看的 PNG／GIF 和源文件包，iPad 无需运行本地 HTML。后续在本组美术认可后，继续独立衣物／武器及完整遮挡与组合验收，再扩展其他七方向中性人体。
