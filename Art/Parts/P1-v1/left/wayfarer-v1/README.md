# Left Wayfarer coat upper

This ordinary pose-map outfit contains the five upper garment slots `outfit.torso`, `outfit.sleeve.left`, `outfit.sleeve.right`, `outfit.hem.front`, and `outfit.hem.back`. The shared lower outfit supplies the pants and boots. The original head, arms, hands, legs, and body remain in the common P1-neutral package.

The isolated generated coat art and its two generation prompts are retained in `source/`. `authoring.json` records the fixed full-canvas registration, slot partitions, sleeve pivots, tail scale/sway, compatibility, and all 13 source poses. `export.py` reproducibly builds the 13 RGBA layer sets, editable ORA/SVG files, manifest, and 120 ms review GIFs. Run it from the repository root with:

```sh
python3 Art/Parts/P1-v1/left/wayfarer-v1/export.py
python3 scripts/check-character-part.py Art/Parts/P1-v1/left/wayfarer-v1/asset.json
```

PNG files use storage keys `00`–`12`; manifest bindings map them to idle 0, walk 1–8, walk-start 1–2, and walk-stop 1–2 without key collisions. `review/fullbody-left-wayfarer-13poses-120ms.gif` composites the immutable left r3 body, companion lower outfit, and shared scabbard for visual review. `review/layered-coat-13poses-120ms.gif` shows coat slots alone. `review/storage04-2x.png` is a closer check of the late-swing pose where the rear leg crosses behind the front hem. The review assets are not part of exported character layers.

The source is authored for the supplied left-facing profile and these 13 locomotion poses. Animated poses use registered source garment parts plus per-pose sleeve transforms and short split-tail sway; the generated design is not a general-purpose deformable garment. Final cross-slot draw order remains the compositor's responsibility. The coat's open cuffs preserve the shared hand silhouettes; review full-body composites should be used to check cuff/arm overlap at integration time.
