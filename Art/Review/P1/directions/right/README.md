# P1 向右方向 · r1 已认可

2026-10-18，用户要求修改向右并与向左 r1 协调；交付 [向右 r1](revisions/r1/README.md) 后，用户回复“没问题，还剩下四个斜方向的也要改，同样的方式，先来修第一组”。现已记录本稿与左右协调对照通过，[确认记录](revisions/r1/approval.json)保存原话、范围及文件摘要。

已认可稿：[向右编号图](revisions/r1/review-2x.png) · [正常循环](revisions/r1/walk.gif) · [慢速循环](revisions/r1/walk-slow.gif) · [左右同步对照](revisions/r1/left-right.gif) · [慢速对照](revisions/r1/left-right-slow.gif)。00 为新站姿，01–08 为两步循环八张关键姿势，修改依据见 [AUDIT.md](AUDIT.md)。当前进入右下斜向审核。

以下为未改动的 build 28 基线，帧号与 r1 不对应。

[编号图](review.png) · [原像素横条](strip.png) · [正常循环](walk-baseline.gif) · [四分之一速度循环](walk-baseline-slow.gif)

00 是站姿，01–24 是两步步行周期；编号图按从左到右、从上到下读取。循环只播放 01–24，不插入站姿。正常每帧 40 ms、周期 960 ms；慢速每帧 160 ms、周期 3840 ms。

新增 GIF 仅合成黑色查看底、最近邻放大两倍并组帧，未改变人物。已解码核对 24 帧、帧序、调色板量化后的像素、时长及无限循环标记；原横条 SHA-256 与固定基线一致，详情见 [preview.json](preview.json)。这是素材预览，不是实体设备录像。

旧版 build 28 未因 r1 获认可而标为通过，本目录 `preview.json` 仍为旧版预览记录。四个正交方向 r1 均已认可，斜向按右下、左下、左上、右上逐方向修改；最终分层人物模板与正式安装包尚未更新。
