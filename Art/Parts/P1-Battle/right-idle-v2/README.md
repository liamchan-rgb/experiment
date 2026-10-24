# Battle-side idle cleanup · v8 art candidate

The current review is the [v9 rear-plane shading revision](../right-idle-v3/README.md), following the user's remaining shoulder-edge feedback. This v8 source is retained unchanged.

The user requested that packaging pause and marked excess pixels at the forehead and rear shoulder, then asked for a less rounded back of the head. This directory is an isolated single-frame art candidate; it has not been imported into the app or packaged.

The [full-character review](review.png) is a nearest-neighbor 3× view of the [native 256×256 composite](assembled.png). It is the current image for review.

- The brow/eye selection no longer includes the unrelated vertical forehead fragment. The blue eye, nose and mouth keep their v7 positions.
- The rear shoulder's duplicated dark seam and warm fringe are replaced by a continuous blue jacket edge. The remaining outfit pixels and canvas registration are retained.
- The rear hair contour is narrower and straighter, then tapers to the nape. Crown height and the front forelock are unchanged. A separate common neutral-head r3 contour candidate trims the underlying rear skull so reducing hair volume does not expose a skin bulge; the retained r2 original is unchanged.

The same weapon, hands, body pose landmarks, feet and 256×256 registration are used. `build-review.sh` reproduces the composite from the editable SVGs and retained source parts. The generated cleanup study in `reference/` is a shape reference only; its body, face, clothing and background pixels are not imported.

This is one unapproved static pose. User art approval is empty, and the app still uses the earlier v7 fixture. Packaging remains paused pending this review.
