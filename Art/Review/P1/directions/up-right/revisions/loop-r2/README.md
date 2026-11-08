# P1 up-right diagonal loop repair · loop-r2

This revision supersedes the up-right `loop-r1` frame 08 after full-body phase review found that the earlier version switched support feet between 07, 08, and 01. `loop-r2` retains frames 00–07 byte-for-byte from loop-r1 and redraws only frame 08. The loop-r1 frame and its raw generation remain in `drafts/` for comparison. The approved source artwork remains untouched.

Frame 08 was generated as a complete pose and registered as a whole silhouette. It preserves the 256 × 256 cell, 154 px opaque height, and y=224 sole-envelope reference. The left/near boot stays planted at the end of frame 08 (last opaque sole row y=223, x=113–125); the right/rear boot remains in low recovery (approximate bounds x=136–161, y=195–213). This keeps the same support leg across 07→08→01. No extra animation frames were added.

## Review files

- `frames/00.png`–`frames/08.png`: standalone transparent 256 × 256 frames.
- `strip.png`: 00–08 horizontal strip.
- `walk.gif`: frames 01–08 at 120 ms each (960 ms loop).
- `review-2x.png`: numbered 00–08 overview at 2×.
- `registration.json`: unchanged review registration; runtime foot positions must be updated by the parent integrator from the per-foot positions in this frame.
- `provenance.json`: generation attempts, input-reference order, prompts, and raw-output hashes.
- `validation.json`: frame equality, bounds, foot-contact review, and GIF timing checks.
- `generated-08*.png`: retained raw generated results; rejected generations remain separately named.

## Self-review

I reviewed the complete 07→08→01→02 progression at native cell proportions and in the 120 ms GIF. The same screen-left/near boot remains the support foot in 07, 08, and 01; the screen-right/rear boot stays lifted in low recovery through the seam. The raised boot is a few pixels lower than the intended y≈211 target (opaque minimum y=213), but its low lift is continuous and it does not show the pronounced sole or support-leg reversal of loop-r1. The head/hair proxy is about 1 px lower than the mean of source 07 and 01, while the sole line remains fixed. This is technical and visual self-review only, not user art approval.
