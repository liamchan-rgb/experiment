# build33 · actual iPad battle preview

These images come from [iPad test run 39421546572](https://github.com/liamchan-rgb/experiment/actions/runs/39421546572), source `cd86161fd817eda49e3750570060e5b644abcb01`, on iPad Pro 13-inch (M4), iOS 17.5 / Xcode 15.4. Four native checks and two UI checks passed. Artifact `12263897192` contains the exported screenshots; the complete result bundle remains in artifact `12265085671`.

- [Player turn](meadow-layout-player-turn.png) · [small preview](player-turn-preview.png)
- [Monster turn](meadow-layout-monster-turn.png)
- [Exploration](meadow-layout-exploration.png)

`original-attachments/` preserves the three XCTest attachments byte for byte. Their pixels are stored as 2064×2752 with EXIF `LeftBottom` orientation. The images above apply only that orientation to produce upright 2752×2064 landscape PNGs. No actors, lighting, UI or scenery have been retouched. The small preview is resized only for easier viewing. File hashes and orientation-normalized pixel signatures are recorded in `evidence.json`.

Manual review checked the complete hero, sword, antlers, tail, foot contacts, shared ground plane, scene depth and removal of the monster-turn letterbox bands. This is a static art/layout fixture, with independent hair, face, wardrobe and weapon layers. It does not connect battle rules or prove the full wardrobe/animation production contract. These new art candidates have not received user approval. No physical iPad installation was performed.
