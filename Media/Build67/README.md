# Build67 · Rune Slash IPA and art review

[Open the normal-speed full-scene GIF](https://raw.githubusercontent.com/liamchan-rgb/experiment/c6ee157f63a19237cf101382920e7c591152ba73/Art/Review/Battle/spellblade-demo-v1/runeSlash-normal.gif) · [Download the unsigned IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/b046d5f15b62dad77638f48ad108639f14404235/Downloads/MeadowJourney-b67.ipa) · [View the supplied spritesheet](../../Art/Parts/BattleVFX/rune-slash-v1/source-spritesheet.png) · [Frame mapping and timing](../../Art/Parts/BattleVFX/rune-slash-v1/frames/frame-manifest.json)

The app uses the eight exact 256×256 RGBA cells from the supplied 2048×256 sheet. The slash closes in on the target; frame 05 begins at the existing hit receipt at 1.048s, while the ground light remains at the target's feet. Other skills, combat rules and character/weapon art are unchanged. The source was labeled an initial concept crop, so it remains subject to the user's overall-art review.

The GIF is an offline preview rendered from production receipts and artwork, not an App/UIKit, simulator or device capture. It is 235 frames at 20ms per frame (4.7s). Browser loading and frame advancement are recorded in `standalone-gif-browser.json`.

Build 1.6.41 (67), unsigned IPA, 49938573 bytes, SHA-256 `2cfe07cfd90ef1f3b0ae36ee7154763d420a2d96ac37b16dcce1380d67090816`. Device Release archive succeeded in [GitHub Actions run 40914603016](https://github.com/liamchan-rgb/experiment/actions/runs/40914603016). ZIP CRC and classic ZIP 2.0 headers, arm64/iPhoneOS target, iPhone/iPad family, Metal, and the eight Rune Slash catalog assets passed. 162 Swift tests, five logic checks and 13 Mac/Linux export comparisons passed. No App, simulator or physical-device runtime was run; the user handles installation and on-device checks.

Public full-GET and normal-speed GIF playback receipt: `public-downloads.json`.
