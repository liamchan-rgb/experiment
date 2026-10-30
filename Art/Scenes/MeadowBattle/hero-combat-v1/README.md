# Hero combat pose study v1

This data-driven pose study animates the existing registered v9 battle actor layers on the shared 256×256 canvas. It preserves the face, rear hair contour, shoulder/back shading and source art. No art was redrawn. GIF previews are full-character views at 120 ms/frame, assembled by `render-review.py` from the production asset layers.

Clips: `idle`, `attack`, `guard`, `hit`, `victory`, `defeat`. The attack has eight keyed moments: ready, draw back, load, forward step, slash, impact hold, recovery, and settle. The host battlefield applies `rootOffset` to both actor and shadow. `footAnchorPx` and `contacts` follow the body pose matrix. The actor caches transformed silhouettes by clip and 1/24 progress buckets for grounding updates.

The existing Body and Wardrobe source layers contain connected torso, limbs, and legs; these are currently moved as registered layers rather than newly repainted anatomical segments. Separate near hand and sword share the reach offset and wrist arc. This keeps the approved silhouette and clothing intact while allowing the host scene to coordinate foot travel. This is a movement study, not a new approval of the character art or a claim that the underlying body layers form a finished universal rig.

Source: `Sources/Resources/Assets.xcassets/MeadowBattleHero*.imageset/`. Swift pose contract and runtime preview renderer live in `Sources/Game/MeadowBattleActorView.swift`. No simulator or device review was run.
