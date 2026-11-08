# Common natural empty-arm motion r6 · candidate

This version uses the retained walk-r2 idle00 natural arms and empty hands. Each complete arm and its hand share one recorded shoulder-pivot rotation, a small authored translation and the existing body bob. The hand is independent of the presence of a weapon or outfit. The repeated gripping-fist artwork is not selected.

Head, torso and both legs keep their original per-pose artwork. The original idle00 pose remains unchanged. This is a separate candidate; it does not overwrite approved motion or inherit approval for the new arm motion.

arm-motion-authoring.json records right/left shoulder pivots, 0–8 angle arrays, relative XY arrays and body bob. Corresponding Forester sleeves use those same transforms. Rebuild with `python3 scripts/export-relaxed-arm-motion.py Art/Templates/P1-Neutral/down/walk-r6-relaxed-arms`; editable ORA/SVG and body-only frames regenerate together.

The earlier r2 ownership correction is retained as history in source/inherited-r2-correction.json. Current full-body and normal-speed evidence is under Art/Review/P1/modular-down-back-carry-v1/. This package is down-only and has no user art approval or production approval.
