# dragonSoulWard VFX

Supplied archive: `4-dragon_soul_ward_asset_pack.zip` (SHA-256 `ae55fb704d03d16d95a81376e87ab0dd75ea7961b1001d27307e84e61389f8fe`).
Runtime source sheet: `dragon_soul_ward_spritesheet.png`; 20 frames at 256×256 px, 5×4 grid, 12 FPS, one-shot.
Skill ID: `dragonSoulWard`. Existing action motion: existing support / guard; no new body animation is included.
The original ZIP and unpacked delivery are preserved. Runtime sheets and individual frames are copied byte-for-byte.

## Delivery notes

- `dragon_soul_ward_frame_manifest.md`
- `dragon_soul_ward_integration.md`

The app uses the corresponding sheet in `Sources/Resources/Assets.xcassets`; frame slicing and pixel identity are checked by `scripts/verify-skill-vfx-assets.py`.
