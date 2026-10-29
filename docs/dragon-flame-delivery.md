# Dragon Flame V2 delivery record

The new source is `Art/Parts/BattleVFX/dragon-flame-v2/`, extracted without cropping from the user-provided `dragon_flame_delivery.zip` (SHA-256 `ceadbb0417568f5511cd3ba081115cee4fa4fb2be91cf416520cc50f6601117e`). Its 5×4 sheet and 20 individual 280×280 RGBA frames are retained, with one fixed center anchor. The app asset-catalog copies are pixel-identical to those source frames.

Dragon Flame is available from the Dragon Knight option in the party battle training menu. It uses the existing node-target skill and atomic engine receipt. The new frames begin at the damage contact, with warm scene and floor light, gravity-driven red/orange/gold embers, short ground sparks, and the existing monster dissolve starting on a lethal receipt. The cast dims the scene; the brighter impact light is drawn over it. Support channels from the same receipt remain visible on the Dragon Knight.

**Build 68:** version 1.6.42; device Release archive and unsigned IPA packaging succeeded in [workflow run 40930342876](https://github.com/liamchan-rgb/experiment/actions/runs/40930342876), source `30ce9c83a948caee6789bde183bcd0866a3e1484`. All 164 Swift package tests passed. The source/app frame verifier passed, and the production exporter emitted 270 full-scene samples at 60 Hz with projected dice. The IPA passed outer and inner ZIP CRC checks and contains the arm64 iOS executable and compiled asset catalog. IPA SHA-256: `ab20f5ae7f646ff594ac0d07d986aa86fc0841cc74c31f863b69c62867ecec39` (51210069 bytes).

- Direct IPA: [https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b68.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b68.ipa)
- Normal-speed whole-scene GIF: [https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Art/Review/Battle/dragon-flame-demo-v1/dragon-flame-normal.gif](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Art/Review/Battle/dragon-flame-demo-v1/dragon-flame-normal.gif)
- Seven inspected full-scene keyframes and export records: `Art/Review/Battle/dragon-flame-demo-v1/`

The GIF has 225 frames at 50 FPS and lasts 4.5 seconds; the source combat export remains 60 Hz. GIF uses 10 ms timing units and cannot represent 1/60 second exactly. It is an offline full-scene art review, not UIKit, simulator, or device footage. No simulator or physical-device run was performed; the user handles installation and runtime review. Internal art review is recorded separately and does not represent user approval.

The next two battle-art tasks are Dragon Scale Ward’s larger round shield and break effect, followed by Dragon Order’s buff feedback.
