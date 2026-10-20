# Blue eye and right-facing features · battle idle candidate v4

This revision moves the eye and brow inward, then separately moves the nose and mouth 2 px from the profile edge. A short skin-tone highlight and darker lower pixel make the right-facing nose read as a small projection; the closed mouth is a separate dark line. `face.svg` is the editable integer-pixel source and `face.png` is the transparent 256×256 feature-only export. It contains no ear or hair pixels.

The exact alpha bounding box is `[138, 105, 150, 120]` in `(left, top, right-exclusive, bottom-exclusive)` convention. See the [r2 overlay with separate hair](review-r2-with-hair.png) and [enlarged head detail](review-head-detail.png). A visual review of v4 found the eye, brow, nose and mouth distinct from each other and the profile at both enlarged and 256×256 size. This remains one unapproved static candidate, with no other directions or production compatibility.
