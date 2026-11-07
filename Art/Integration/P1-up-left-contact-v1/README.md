# P1 up-left contact transition · build38

The active selection uses `contact-r1` for up-left, based on the previous `loop-r1`. Only cell02 is replaced; all other cells, directions and heroes retain their complete RGBA, including hidden RGB under zero alpha. Original approved r6 and previous loop-r1 remain preserved.

The visible screen-left boot sole progresses y210 → y215 → y223 through poses01 → 02 → 03. The screen-right boot remains on row223 for01–02, then lifts for03. Runtime landmarks use the existing boundary convention (last visible row +1): new02 support `[142,224,0]`, descending foot `[110,216,8]`; the conservative lift projects its ground point near the support baseline. The three distance-clock samples that map to pose02 update together.

[Whole-figure art and normal120ms loop](../../Review/P1/directions/up-left/revisions/contact-r1/README.md), [parent review](../../../Media/Build38/art-review.json), [import record](integration.json) and [landmarks](footprints.json). Internal review follows the user's autonomous correction instruction; it is not new user art approval. Device experience remains for the user to verify.
