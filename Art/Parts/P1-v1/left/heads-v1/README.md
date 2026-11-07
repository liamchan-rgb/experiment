# P1-v1 left head resources

Five independent `head-local` packages share the approved left-facing r3 body's 96×96 head coordinates: chestnut, silver and teal hair; blue and amber face features. Every asset maps to idle, walk 01–08, walk-start 01–02 and walk-stop 01–02 (13 poses) by reusing one fixed image. The runtime motion's `headToCanvas` transform moves each image with the shared head.

Each package preserves its imagegen full-body source and exact prompt, plus editable slot PNGs, SVG wrappers, and an ORA layer stack. `layout-proposal.json` records the measured left feature regions for the standard owner. The images contain no skin, ear, neck, head outline, body selection, or dependency on another appearance ID.

Run `python Art/Parts/P1-v1/left/heads-v1/export.py` to deterministically extract and register the five packages from the preserved imagegen sources. Run `python Art/Parts/P1-v1/left/heads-v1/preview.py` to render all six hair × face combinations from the shared r3 motion. Each combination folder under `previews/` contains the 1× and 2× full-body idle, 1× and 4× head crops, a 120 ms walk GIF, all 13 rendered body frames, and the 13-pose head contact sheet.

The package manifests currently cover left direction only. Art approval remains pending. Mechanical image checks do not attest to face anatomy, occlusion, or user acceptance.
