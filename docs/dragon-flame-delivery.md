# Dragon Flame V2 delivery record

The new source is `Art/Parts/BattleVFX/dragon-flame-v2/`, extracted without cropping from the user-provided `dragon_flame_delivery.zip` (SHA-256 `ceadbb0417568f5511cd3ba081115cee4fa4fb2be91cf416520cc50f6601117e`). Its 5×4 sheet and 20 individual 280×280 RGBA frames are retained, with one fixed center anchor. The app asset catalog copies are pixel-identical to those source frames.

Dragon Flame is available from the Dragon Knight option in the party battle training menu. It uses the existing node-target skill and atomic engine receipt. The new frames begin at the damage contact, with warm scene and floor light, gravity-driven red/orange/gold embers, short ground sparks, and the existing monster dissolve starting on a lethal receipt. The cast dims the scene; the brighter impact light is drawn over it. Support channels from the same receipt remain visible on the Dragon Knight.

The self-check is `python3 scripts/verify-dragon-flame-assets.py`. The macOS package-only workflow also runs `DragonFlameTests` and exports the 60 Hz full-scene review data. The human-readable GIF is sampled at normal wall-clock speed from those frames; GIF timing uses 50 frames per second because its 10 ms duration unit cannot represent 1/60 second. The final archive URL, archive hash, review GIF URL and CI run ID will be added after the build finishes. No simulator or physical device run is part of this delivery; installation and runtime review remain with the user.

Next two battle art tasks are Dragon Scale Ward's round shield and break effect, then Dragon Order's buff feedback.
