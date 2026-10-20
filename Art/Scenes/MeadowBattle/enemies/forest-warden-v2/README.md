# Forest warden v2 · alert idle candidate

The former running silhouette conflicted with a waiting combatant. This revision keeps the chestnut, leaf-green and amber design, faces left, lowers the head, and plants all four hooves. The original generated chroma-key image is retained in `source/idle-chromakey.png`; the exact prompt is beside it.

`process.sh` removes magenta and reduces the **entire** 1536×1024 canvas to 384×256 with nearest-neighbour sampling. There is no alpha-based crop or character-specific body transformation. This deliberately brings the source-pixel density closer to the registered 256×256 hero. Transparency and silhouette are checked before app import.

This is one static art candidate, not a user-approved enemy design or an idle animation. The previous source and build32 remain in `../forest-warden-v1/`. Scene light, cast shadow and hoof contacts are independent runtime layers.
