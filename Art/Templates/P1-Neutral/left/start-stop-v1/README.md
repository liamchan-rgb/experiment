# P1 Neutral Left Start/Stop Pose Sources

Four generated pose sources for optional `walk-start` and `walk-stop` clips. The intended sequences are `idle00 → start01 → start02 → walk01` and `walk08 → stop01 → stop02 → idle00`. Every pose is previewed at 120 ms; no slow preview is included.

`source/*.png` are preserved 1254×1254 image-generation outputs. Rejected first candidates and repair attempts remain under `source/rejected/`. `source/prompts.json` records the prompts, selected repair outputs, and rejected alternatives. `authoring.json` is the merge-ready fixed pose configuration: it records the source SHA-256 per pose, full-canvas registration (scale 0.194, translation [4.72, 6.4]), per-pixel `ownershipOverrides`, eight-slot partitions, head partition for replacement, draw order, joints, actual sole/hand markers, and support.

The fixed visible non-head ownership was exported into `layers/00..03/` and recomposes exactly to each registered source body. `ownership-review.json` records source/layer hashes, alpha checks for every sole marker in its owning leg layer, missing/overlap/recomposition counts, and preview locations. `review/start-transition-120ms.gif` and `review/stop-transition-120ms.gif` show the full-body transitions at normal speed; the contact sheet and slot/boundary atlases support visual review.

The preview temporarily uses the generated start01 head across all four poses. Parent integration replaces each head with the approved r2 shared head and applies that pose's `headToCanvas` transform. Hidden anatomy is not reconstructed; ownership covers visible source pixels only.

主审后续补记：本目录是源图与最初归属快照；完整人物RGBA复原通过不等于语义归属正确。主线程发现手脚描边默认归入躯干，已在[最终r3](../walk-r3-complete-transitions/)中将1676像素归回相应肢体，原源RGBA不改。后续挂载与重导以r3/authoring.json及其source/transition-authoring.json为准。
