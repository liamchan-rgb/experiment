# Battle-side idle · v9 rear-plane shading candidate

The user found a remaining black shoulder edge in v8 and requested the depth treatment used in the approved left/right walking artwork. This is the current single-frame art review. On 2026-10-21 the user withdrew the packaging pause and requested a new IPA. This candidate is now imported into the app without cropping or resampling; see `runtime-import.json`. The user accepted the current static battle presentation and requested the next step; see `approval.json`.

See the [full-character 3× view](review.png) and [native 256×256 composite](assembled.png).

The old diagonal shoulder seam and hard outer strip are replaced by blue transitions. A continuous cooler shadow covers the rear shoulder/back plane and becomes deeper on the trailing sleeve; the foreground sword arm keeps its existing light face. The color multiplier retains the original cloth texture and the outfit's exact alpha. Face, hair, head contour, hands, sword, pose, feet and registration are inherited unchanged from v8.

The depth references are the approved left/right r1 `frames/03.png`. They are used for the near/far value relationship, not copied as clothing or animation. `outfit-forester/rear-edge-tones.svg` and `rear-shade.svg` are the editable color sources; `build-review.sh` reproduces the composite. The retained imagegen study is a shading reference only, and its pixels are not imported.

Mechanical checks in `validation.json` verify that the changes stay in the requested shoulder/rear-sleeve area. They do not constitute user art approval. This remains one static pose. Its current presentation is accepted; new movement poses and the full wardrobe template are reviewed separately.

Device Release archive run [39530852893](https://github.com/liamchan-rgb/experiment/actions/runs/39530852893) succeeded at source `01cb73a` for 1.6.9 build35. The downloaded IPA passed device-platform, arm64, version, CRC and remote-checksum verification. No simulator or physical-device run was performed; see `Media/Build35/package.json` for package provenance.
