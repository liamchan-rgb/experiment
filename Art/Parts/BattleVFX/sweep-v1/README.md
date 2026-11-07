# sweep VFX

Supplied archive: `3-sweep_delivery_bundle.zip` (SHA-256 `53d80e0acc7412d76e0daf86221ee79a06b2c7f23cff01e2d944244081040633`).
Runtime source sheet: `sweep_spritesheet.png`; 20 frames at 339×287 px, 5×4 grid, 20 FPS, one-shot.
Skill ID: `sweep`. Existing action motion: existing melee attack; no new body animation is included.
The original ZIP and unpacked delivery are preserved. Runtime sheets and individual frames are copied byte-for-byte.

## Delivery notes

- `sweep_frame_manifest.md`
- `sweep_integration.md`

The app uses the corresponding sheet in `Sources/Resources/Assets.xcassets`; frame slicing and pixel identity are checked by `scripts/verify-skill-vfx-assets.py`.
