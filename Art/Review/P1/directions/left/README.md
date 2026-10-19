# P1 向左方向 · r1 已认可

2026-10-18，收到用户关于鞋踝扭曲的修改意见后，交付 [向左 r1 重画稿](revisions/r1/README.md)。用户回复“没问题，继续下一个方向”，现记录为已认可；[确认记录](revisions/r1/approval.json)保存原话、范围及文件摘要。

已认可稿：[编号图](revisions/r1/review-2x.png) · [正常循环](revisions/r1/walk.gif) · [四分之一速度循环](revisions/r1/walk-slow.gif)。00 为新站姿，01–08 为两步循环八张关键姿势；具体修改依据见 [AUDIT.md](AUDIT.md)。当前进入向上审核，向右仍排队。

以下是未修改的 build 28 基线，保留供对照；帧号与 r1 不对应。

[编号图](review.png) · [原像素横条](strip.png) · [正常循环](walk-baseline.gif) · [四分之一速度循环](walk-baseline-slow.gif)

00 是站姿，01–24 是完整两步步行周期；编号图按从左到右、从上到下读取。原图保持不变，循环只播放 01–24，不将站姿插入周期。正常每帧 40 ms、周期 960 ms；慢速每帧 160 ms、周期 3840 ms。循环是素材预览，不是实体设备录像。

新增 GIF 已解码核对 24 帧、帧序、像素（经声明的 GIF 调色板量化）、时长和无限循环标记；原横条 SHA-256 保持与固定基线一致，详情见 `preview.json`。

旧版 build 28 保留为基线，未因 r1 获认可而标记通过；本目录 `preview.json` 是旧版预览记录，认可仅针对 `revisions/r1/`。
