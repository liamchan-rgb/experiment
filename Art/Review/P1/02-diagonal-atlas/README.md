# P1 四斜向固定基线

2026-10-18，从 build 28 正式 `Sources/Resources/Assets.xcassets/Hero1Diagonals.imageset/Hero1Diagonals.png` 原样复制 `baseline.png`，尺寸 6400 × 1024，每格 256 × 256。每行 00 站姿＋01–24 两步步行帧，固定保留供修改对照，不代表美术认可。

行序由离线生成器 `scripts/prepare-gait-assets.py` 的 `HEADINGS` 索引 4–7 和 `HeroFrames.load` 的斜向行加载顺序核对：

| 行 | 方向 | 审核顺序 |
| --- | --- | --- |
| 0 | 右下 ↘ | 05，r1 已认可 |
| 1 | 左下 ↙ | 06，当前 |
| 2 | 左上 ↖ | 07，排队 |
| 3 | 右上 ↗ | 08，排队 |

四条横图与对应行 RGBA 像素相等；原版编号图只重新排版、增加黑底与编号。摘要、来源、当前项及认可范围见 `../review.json`，新稿另存各方向 `revisions/`，不覆盖基线或正式图集。
