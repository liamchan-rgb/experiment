# Approved P1 walking artwork in the demo

The user requested the previously approved eight directions in the demo and a new IPA on 2026-10-21. Left-up uses r6; the other seven directions use r1. `integration.json` records each approved strip's SHA-256 and the emitted runtime resources. Originals remain untouched.

Run `python3 scripts/import-approved-p1-gait.py` after any legacy asset regeneration. Each P1 atlas has nine actual columns: idle, then eight complete walking poses. The 24-tick distance clock samples each pose for three ticks; there are no interpolated or duplicated raster poses. Normal demo playback is 120 ms per pose, 960 ms per two-step cycle. Stepping advances one complete P1 pose. P2/P3 keep their existing 24 poses and footprint data.

`footprints.json` contains boot sole coordinates in the unchanged 256px source canvas and conservative recovery lift. Source landmarks were seeded from boot colors, checked on whole-character overlays, and corrected where the silhouettes overlap. They address the rendered sole pixels; physical-device lighting and contact appearance remain for user review. The foreground and Metal depth caster sample the same pose.

The earlier 24-pose blue-boot layered comparison is preserved as historical artwork. Its demo entry is hidden while it is incompatible with the new P1 sequence. This import does not claim a completed interchangeable wardrobe or animation rig.
