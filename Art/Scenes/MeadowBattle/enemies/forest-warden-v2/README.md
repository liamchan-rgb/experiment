# Forest warden v2 · pixel-art alert idle candidate

The former running silhouette conflicted with a waiting combatant. This candidate keeps the chestnut, leaf-green and amber design, faces left, lowers the head, and plants all four hooves. It replaces the soft painterly rendering with larger, deliberate pixel clusters so the deer sits more naturally beside the low-detail battle hero. The earlier chroma-key source and this pixel-art edit are retained separately in `source/`.

Run `bash process.sh` from this directory to rebuild the runtime sprite. It thresholds the generated alpha to discard its soft transparent fringe, reduces the complete 1536×1024 canvas on a nearest-neighbour grid, then registers the figure inside the same 384×256 canvas so its visible alpha bounds remain `(13,9)-(344,241)` and the four-hoof ground line stays at `y=240`. It does not crop to alpha or shift individual limbs. The scene keeps its original enemy anchor and shadow caster; contact gradients are aligned to the rebuilt hoof pixels in `MeadowBattlePreviewView.swift`.

This is one static art candidate, not a user-approved enemy design or an idle animation. The earlier sprite and build32 remain in `../forest-warden-v1/`. Scene light, cast shadow and hoof contacts are independent runtime layers; no halo or ground is baked into this sprite.
