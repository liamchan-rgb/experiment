# Down modular character v8 · coverage and back-carry revision

User feedback rejected v7: clothing failed to cover the body and the gripping hands looked wrong. This revision uses one common relaxed-arm base, complete Forester clothing coverage and an independently mounted sheathed sword behind the body.

- Base: walk-r6-relaxed-arms retains original head/torso/legs and idle00. Natural empty hands follow small continuous shoulder motions; no loadout selects a replacement hand.
- Outfit: outfit-forester-cover-v2 includes shoulder/wrist, shirt/shorts, trouser and boot underlaps. Clothing draws over the complete body. The old order that drew safety shorts over trousers is corrected in this candidate motion.
- Weapon: weapon-short-sword-back-v1 owns weapon.back with carryProfile: back-scabbard. It uses a full-source fixed affine and body bob without a hand socket. Shoulder hilt and opposite-hip scabbard tip identify the back carry.

catalog.json selects ordinary resource packages. motion.json supplies candidate layer order; the compositor has no appearance-specific code. The profile/schema/checker distinguish stowed back weapons from hand grips.

The [actual compositor review](../../../../Review/P1/modular-down-back-carry-v1/) includes 24 appearance/loadout combinations, 216 pose PNGs, normal 8×120ms GIFs, clothing coverage attribution including semitransparent edges, and weapon toggles. Rebuild: `python3 Art/Review/P1/modular-down-back-carry-v1/render-audit.py`.

Current user previews are [idle00 full-body](../../../../Review/P1/modular-down-back-carry-v1/idle-review-2x.png) and the [normal-speed walk GIF](../../../../Review/P1/modular-down-back-carry-v1/walk-120ms.gif). User requires delivery of the normal-speed full-body GIF with future revisions. Other combinations remain internal audit evidence. User approved the presented down-facing full-body appearance and normal-speed walk on 2026-10-22 (see approval.json). Other combinations, directions, start/stop transitions and production integration are outside this approval. No App runtime, simulator/device run or IPA is included.
