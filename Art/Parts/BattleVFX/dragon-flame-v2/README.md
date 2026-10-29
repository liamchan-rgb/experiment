# Dragon Flame V2

This directory preserves the unchanged extracted PNGs and delivery notes from the artist-delivered ZIP as the source of truth. The 1400×1120 RGBA sheet is a fixed 5×4 grid of 20 280×280 frames. Every standalone frame keeps the complete canvas and center anchor; it is not cropped to its alpha bounds. `frame-manifest.json` records each frame hash, alpha bounds, and sheet-cell comparison. The received ZIP SHA-256 is `ceadbb0417568f5511cd3ba081115cee4fa4fb2be91cf416520cc50f6601117e`.

Frames 1–5 gather and form the flame, 6–10 build the dragon crescent, 11–13 carry the peak impact, and 14–20 disperse into embers. The runtime starts the sequence on the committed damage receipt, crossfades the authored poses at 60 Hz, holds the peak frames briefly, and fades the tail. The node-wide skill uses the same anchor independently for each living monster in the selected node.

At impact the scene receives a short red-orange-gold light pulse, the monster body and ground brighten, colored embers arc out under gravity and produce a brief ground-contact spark, and a lethal hit starts the existing monster dissolve from the same receipt. The screen remains dimmed during the cast and lifts through the impact. The Dragon Knight training option uses the existing rule catalog entry and atomic engine receipt.

Run `python3 scripts/verify-dragon-flame-assets.py` to verify the source sheet, 20 standalone RGBA frames, hashes, and all 20 app asset-catalog copies. The normal-speed full-scene review is produced from the 60 Hz receipt export with `scripts/review-dragon-flame-demo.py --dragon-flame-only`; it is an offline art review, not device footage. The review and package identifiers are recorded in `docs/dragon-flame-delivery.md` after the archive is verified.
