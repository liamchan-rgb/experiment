# rally VFX

Supplied archive: `2-rally_delivery.zip` (SHA-256 `d95738b6a103c42f9ff32ca873a44b4ef780a059bdc94ec037676588ba791cb3`).
Runtime source sheet: `rally_spritesheet.png`; 20 frames at 256×256 px, 5×4 grid, 12 FPS, one-shot.
Skill ID: `rally`. Existing action motion: existing support / guard; no new body animation is included.
The original ZIP and unpacked delivery are preserved. Runtime sheets and individual frames are copied byte-for-byte.

## Delivery notes

- `README.md`
- `rally_frame_manifest.md`
- `rally_integration.md`

The app uses the corresponding sheet in `Sources/Resources/Assets.xcassets`; frame slicing and pixel identity are checked by `scripts/verify-skill-vfx-assets.py`.
