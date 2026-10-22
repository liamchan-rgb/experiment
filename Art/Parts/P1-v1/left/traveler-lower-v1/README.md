# Left traveler lower outfit

Shared lower outfit for compatible left-facing upper garments. It is a pose-map asset for `p1-chibi-v1` / `p1-standard` / `locomotion-v1`, with slots `outfit.pants.right`, `outfit.pants.left`, `outfit.boot.right`, and `outfit.boot.left`. Materials are charcoal-gray trousers and warm-brown ankle boots.

The independent images cover the complete safety shorts, legs, and feet. Per-pose geometry follows `source/visible-layers/{00..12}/body.leg.{left,right}.png` and each matching `soleMarkers` entry; boots keep the correct raised sole on swing poses. No body, head, torso, hands, or arms are shipped in the slot PNGs.

The shared image-generation source is `source/00-dressed-clean.png`, RGBA 1254×1254 with transparent corners. Prompt history is in `source/prompt-00.txt`; the first RGB checkerboard result is preserved as `source/00-dressed-checker-rejected.png`. This package is reproducibly exported together with the companion Forester shirt package; both directories are a paired submission unit. Run `python3 export.py` from this directory (or the Forester directory) to reproduce both. Editable 13-pose ORA/SVG files and four independent 256×256 transparent slots are included per pose.
