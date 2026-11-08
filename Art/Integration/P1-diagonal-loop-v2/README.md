# Four diagonal loop seams · demo repair

The user requested an independent agent to repair the four diagonal loop seams and self-review normal-speed animations. Down-right, down-left and up-left use `loop-r1`; up-right uses `loop-r2`. Original approved r1/r6 artwork and approval records remain preserved.

Only pose08 changes in each direction. Poses00–07 retain all original RGBA values, including transparent pixels. Each review GIF has eight frames at 120ms per frame, a 960ms loop. `agent-review.md` records the artist's review; `parent-review.json` records the final whole-character 07→08→01→02 review and selected source hashes. The initial up-right replacement was rejected because it switched support legs; r2 retains the left support foot and right recovery foot through the loop seam.

`footprints.json` updates the individual boot coordinates for all four revised pose08 frames. A common y=224 registration line does not mean individual foot positions are unchanged. The main import script maps the new sole data and sprite to the same source pose.

`Art/Integration/P1-gait-selection.json` is the explicit runtime selection and user task authorization. Run `python3 scripts/import-approved-p1-gait.py` to reproduce both P1 runtime atlases and `hero-gait.json`. The new source pixels are copied exactly; cardinal artwork and P2/P3 assets remain unchanged. Self-review does not mark the new artwork as user-approved or claim physical-device validation.
