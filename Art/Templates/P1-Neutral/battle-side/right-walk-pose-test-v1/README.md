# Right-facing side walk pose test · v1

This is a single unapproved pose study registered to the approved r2 256×256 canvas. Frame `01.png` is a small forward step: the near arm reaches slightly forward, the far arm trails, the near foot is planted, and the far heel lifts.

The generated source had low-alpha color fringe outside the sprite. The build hardens alpha, removes those pixels, downsamples with nearest-neighbor sampling, reduces the palette, and places the result against the approved character bounds. The registered pose has one connected silhouette and no pixels outside the character bounds. The feet remain on the approved sole line at y=214.

The pose is split into eight editable semantic pixel layers, and the static recomposition matches the frame pixel-for-pixel. Fourteen editable skin pixels extend the prior torso/hip-root underlay to cover holes in a ±1 px diagnostic nudge. This confirms only local root coverage; complete hidden anatomy, larger movement, outfit overlap, animation approval, and production rigging remain incomplete. The approved r2 artwork is unchanged.

Run `./build.sh` to reproduce the processed frame, its eight semantic layers, the [pose comparison](review.png), [hand/foot edge details](details.png), [layer contact sheet](parts-review.png), and [one-pixel movement diagnostic](movement-test.png) from the retained generated source.
