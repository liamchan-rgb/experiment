# Forest warden motion v1

This revision follows the accepted forest-warden-v2 design into eight attack poses. Original idle.png is preserved; generated source/drafts and requests are retained in reference/ and provenance.json. This is an internally reviewed motion revision, not a new user approval.

The 4×2 source is sliced mechanically with one shared scale, a fixed hip registration, nearest-neighbor sampling and common binary-alpha export. No per-frame alpha fitting, RGB painting or hidden rescale. The authored recovery frame07 is replaced with exact frame00 to close the motion at idle. World travel is owned by the battle timeline, not baked into these sprites.

`attack.gif` uses8×120ms=960ms, exactly the runtime enemy motion duration. `motion.json` records the original cells, scale/translations, visible bounds and planted-hoof contacts. Runtime silhouette, contact shadow and health/impact effects follow the same source pose. Transparent gutters, full antlers/tail/hooves and native full-body shape are checked in contact-sheet.png. No simulator or device run performed.
