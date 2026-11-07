# P1 up-right diagonal loop seam repair · loop-r1

This review revision keeps the approved r1 source and redraws only walk frame 08. Frames 00–07 are pixel-for-pixel copies. The replacement 08 is an ImageGen full-pose redraw, uniformly scaled to 154 opaque pixels high and registered as a whole pose to the frame-08/frame-01 head-root proxy. The horizontal whole-pose offset is -4 px; the sole-envelope reference remains y=224. No limbs, shoes, or head were transformed separately.

## Review files

- `frames/00.png`–`frames/08.png`: standalone transparent 256 × 256 frames.
- `strip.png`: 00–08 horizontal strip.
- `walk.gif`: 01–08 only, 120 ms/frame (960 ms loop); no slow preview.
- `review-2x.png`: numbered 00–08 overview at 2×.
- `registration.json`: unchanged source review registration; sole line is not runtime foot metadata.
- `provenance.json`: exact accepted prompt, source-reference order, image hash, and retained unselected attempts.
- `validation.json`: image, registration, unchanged-frame, and GIF checks.
- `generated-08.png`: original ImageGen output; `drafts/`: retained unselected raw generations.

## Seam self-review

The full 07→08→01→02 progression was inspected at native cell proportions and assembled into the normal-speed 120 ms GIF. The warm-hair proxy at 08 now aligns to the mean source 08/01 position within about one pixel horizontally; all four poses retain the 154 px opaque silhouette height and y=224 sole-envelope line. Frame 08 remains a distinct late-swing pose: down-facing views have the forward boot low and contacting, up-facing views carry the lead foot slightly above the contact line before 01 lands. Frame 07→08 maintains the supporting foot and opposing arm rhythm; 01→02 continues weight transfer. The foot bounds/contact notes are recorded in `validation.json`.

This is an internal technical and visual self-review, not user art approval. The generated frame has a small rendering-detail difference from hand-edited approved frames; review the numbered sheet before integration.
