# P1 up-left contact transition repair · contact-r1

This revision addresses the abrupt 01→02 landing. In the source strip, the visible screen-left boot moved from a last visible sole row near y=210 in frame 01 directly to ground in frame 02. Frame 02 is redrawn as a whole pose: its screen-left boot remains in near-contact at y=215 while the screen-right boot stays planted at y=223; frame 03 completes the support transfer. The 8-pixel clearance gives the descent a readable intermediate beat at the normal 120 ms frame interval.

Only the visible pose in frame 02 changed. Frames 00–01 and 03–08 are exact RGBA crops from the loop-r1 source strip, preserving hidden RGB where alpha is zero. The full generated pose was uniformly resized with nearest-neighbor sampling and registered as one image to the source frame-02 warm-hair proxy. No isolated limb or shoe was translated or transformed.

## Review assets

- `frames/00.png`–`frames/08.png`: 256 × 256 transparent review frames.
- `strip.png`: full 9-cell strip with unmodified cells kept as exact crops from the loop-r1 source strip.
- `walk.gif`: frames 01–08 at 120 ms each, 960 ms loop, normal speed only.
- `review-2x.png`: numbered full-body 2× overview.
- `candidate-compare.png`: full-body 01 / revised 02 / 03 comparison.
- `seam-compare.png`: full-body 07→08→01→02→03 comparison.
- `sole-measurements.json`: visible screen-left and screen-right boot sole pixel coordinates and lift from baseline y=223.
- `provenance.json`, `registration.json`, `validation.json`: source, exact prompt, generated raw hash, whole-pose registration, and checks.
- `drafts/`: selected ImageGen raw output, two retained unselected raw generations, the source reference, and exact prompts. Their hashes and unselected reasons are in `provenance.json`.

This is an internal technical and visual self-review. It is not user art approval.
