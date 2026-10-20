# Blue eye and right-facing profile · battle idle candidate v7

The user rejected v5's crowded features and v6's blocky nose/disconnected mouth. The v6 files and feedback are retained under `revisions/v6/`; that artwork is not used by the current sprite.

v7 uses the face design from the retained generated **whole-character** study. `source-v7/extract.sh` registers that study with one fixed canvas scale and a -4 px feature translation, then selects only the brow, eye, nose and mouth into four transparent layers. The generated body, clothing, hair, ear and neck are not imported. `face.svg` exposes the four raster parts as named editable groups; the generated original, prompt and extraction source are retained. `face.png` is the 256×256 runtime export, with alpha bounds `[138, 106, 152, 129]` in right/bottom-exclusive convention.

The primary self-review uses the [native full registered character](../assembled.png) and [whole-character 3× preview](../review-face-v7.png). The eyebrow and eye occupy the upper face; the nose leads the profile; the mouth sits below it with a visible chin. These are asset recompositions, not runtime screenshots.

This is still one unapproved static candidate. It has no other directions or expressions, and actual battle-scale readability awaits the user's iPad screenshot.
