# Forester coverage repair v2 · candidate

The preceding v7 combination was rejected by the user: exposed shoulder/arm pixels, mismatched cuffs and an unsuitable gripping hand were visible. The earlier internal pass did not establish acceptable clothing coverage.

This package supplies real opaque jacket, trouser and leather-boot underlaps within fixed authoring patterns. The neutral body is not erased or clipped. Sleeves use the generated idle sleeve paint, a generated dark cloth underlap and a stored anatomical garment pattern with a one-pixel cloth allowance. Walking sleeves follow the same small shoulder-pivot transforms as the common relaxed arms. Other generated sleeve poses remain provenance and are not selected in final maps.

The jacket, trousers and boots retain the original painted detail above independent cloth/leather underlaps. Neck/collar skin remains visible by design; arms, safety shirt/shorts, bare legs and feet are covered. Patterns are stored in patterns/; original paint is retained in source/original-layers/. No runtime body masks, appearance-ID branches, color guessing or alpha-box fitting are used.

Rebuild: `python3 scripts/export-forester-cover-v2.py Art/Parts/P1-v1/outfit-forester-cover-v2`. Source material squares use fixed uniform registration. The compositor consumes ordinary pose maps.

[Current full-body review](../../../Review/P1/modular-down-back-carry-v1/idle-review-2x.png) · [24×9 compositor audit](../../../Review/P1/modular-down-back-carry-v1/audit.json). Down-only candidate; artApproval remains null.
