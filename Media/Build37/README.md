# build37 · Road cadence and playable forest encounter

Version1.6.11 build37. Source: `75c50ee68134b688d3b4d7aa916345b5667e3f49`.

P1 road walking now follows the reviewed120ms authored-pose cadence; moving backdrop shadows follow the complete foot/pose state in the same submitted frame, and idle clears the stale walk phase. P2/P3 source art and speeds remain unchanged. [Four-direction road preview](../../Artifacts/Diagnostics/road-motion-four-directions-offline.gif) uses the production trail network/atlases in an offline composition; it does not establish GPU frame rate or actual iPad smoothness.

Open **林地战斗 → 开始遭遇**, tap the Forest Warden, then select a skill. P1 has12HP and3AP per round; strike costs1AP and deals5 fixed damage, breathe heals4 with2 uses, and protection gives4 shield with2 uses. The18HP Warden acts after **结束回合** with a visible wind-up and4 damage; shield absorbs first. Win/lose, retry, and return to map are implemented. This is a bounded local encounter; it does not use the separate tabletop game's saved inventory or dice rules.

[Parent art review](art-review.json) records the full-body/native and full-scene checks. The rejected rigid v1 is retained. [Hero v2](../../Art/Scenes/MeadowBattle/hero-combat-v2/README.md) uses jointed arm/leg parts, registered head/face/hair, and the same JSON for runtime/review. [Warden motion](../../Art/Scenes/MeadowBattle/enemies/forest-warden-motion-v1/README.md) retains generation sources and8 registered attack poses. Existing user approval of v9 static appearance does not imply new user approval of these motions or completion of the entire wardrobe template.

[Normal-speed full-scene GIF](battle-actions-offline.gif) samples40ms of elapsed time per frame with a shared palette; authored hero and road review GIFs remain120ms per pose. [Full-scene sheet](battle-scene-contact-sheet.png) shows composition, complete silhouettes, weapon reach, planted contacts and separate cast shadows. These are offline artwork renders, **not** UIKit/GPU screenshots. Color treatment/blur and vector HUD feedback are approximate or omitted. Real device operation and screenshots are left to the user; no simulator or physical-device run is performed this round.

Three build-host checks compile actual Foundation encounter/road source and the actual pose sampler with a filesystem asset adapter. The archive uses generic iOS device Release only. Package metadata and a direct `.ipa` URL will be recorded after the archive and checksum verification.
