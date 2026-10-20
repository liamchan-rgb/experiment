# Battle-side idle · v9 rear-plane shading candidate

The user found a remaining black shoulder edge in v8 and requested the depth treatment used in the approved left/right walking artwork. This is the current single-frame art review. Packaging remains paused and the candidate is not imported into the app.

See the [full-character 3× view](review.png) and [native 256×256 composite](assembled.png).

The old diagonal shoulder seam and hard outer strip are replaced by blue transitions. A continuous cooler shadow covers the rear shoulder/back plane and becomes deeper on the trailing sleeve; the foreground sword arm keeps its existing light face. The color multiplier retains the original cloth texture and the outfit's exact alpha. Face, hair, head contour, hands, sword, pose, feet and registration are inherited unchanged from v8.

The depth references are the approved left/right r1 `frames/03.png`. They are used for the near/far value relationship, not copied as clothing or animation. `outfit-forester/rear-edge-tones.svg` and `rear-shade.svg` are the editable color sources; `build-review.sh` reproduces the composite. The retained imagegen study is a shading reference only, and its pixels are not imported.

Mechanical checks in `validation.json` verify that the changes stay in the requested shoulder/rear-sleeve area. They do not constitute user art approval. This remains one unapproved static pose.
