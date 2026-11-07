# Meadow battle hero combat v2

This is a review candidate for the common registered hero rig and battle clips. It replaces the v1 whole-character lean study with separate arm and leg segments driven by one pose library. The approved face, hair, head contour, and shoulder/back artwork remain the original build35 assets.

## Art and rig

The rig uses the shared 256×256 battle-side registration. Fixed masks split the common body and wardrobe layers into a core, near upper arm and forearm, and near/far thigh and shin parts. The near and far shin masks include the complete boot silhouettes: the front boot reaches x=163 in the source art and the rear boot reaches x=88–109. Three-pixel mask overlap closes the joint seams while each neutral body and wardrobe composite reconstructs its source layer. The runtime configuration retains the approved idle layer stack; action clips use a foreground sword order so the blade stays visible while the hand remains on the grip.

Image-generation source material is retained in `source/`. `underlay-inpaint-prompt.txt` records the prompt. `generated-underlay.png` is an unused full-character redraw study and is not part of runtime art. `generated-core-underlay.png` is the core-only generation used as a small concealed joint fill for moving clips; the build script clips it to the registered joint regions. `generated-core-256.png` is a resized preview, and `registered-underlay-holes.png` is a mask-preparation artifact. No generated output replaces or redraws the approved face.

The original v1 research remains under `../hero-combat-v1/`. V1 was returned because whole-body lean and a detached sword/hand transform did not provide a readable attack. V2 adds articulated arm and leg chains, a coupled hand and sword grip, anticipation, step and extension, strike/contact, recovery, guard, hit recoil, idle breathing, and victory/defeat poses. Boot masks were extended to cover the source boot tips after review found static sole fragments.

This rig uses common body and wardrobe segmentation. It does not claim a complete reusable outfit template or appearance-ID-specific rigging. Enemy animation, scene movement, shadows, and hit effects are coordinated by the parent scene work.

## Animation and runtime data

`clips.json` is the source for both the offline GIF renderer and the runtime `MeadowBattleHeroAnimationV2` dataset. The runtime configuration is `hero-v2-configuration.json`, mirrored into `MeadowBattleHeroConfigurationV2`. The actor API is `setPose(clip:progress:)`; the sampled root offset includes support-foot ground correction to y=214, and contacts aggregate planted toe samples to at most one point per boot. The parent scene can use the same sampled clip/progress for the actor silhouette and shadow key.

The complete-character GIFs use the JSON frame timing (120 ms per source frame). Frame `i` samples `progress = i / frameCount` for every clip, including non-looping clips, so the final displayed frame begins one frame interval before the clip duration; the runtime reaches progress 1 at the duration boundary:

| Clip | Duration | Source frames |
| --- | ---: | ---: |
| idle | 2.40 s | 20 |
| attack | 1.20 s | 10 |
| guard | 0.96 s | 8 |
| hit | 0.84 s | 7 |
| victory | 1.08 s | 9 |
| defeat | 1.08 s | 9 |

The GIF encoder coalesces identical adjacent frames, but encoded frame delays preserve each listed total duration. `v2-final-review-sheet.png` was regenerated from the current full-character GIFs after the final boot-mask adjustment.

## Validation record

`final-validation.json` records SHA-256 hashes for every configured runtime layer PNG, the runtime configuration and animation datasets, clip JSON, review sheet, and each GIF. It also records image dimensions, GIF durations, dataset equality, and static-composite comparisons.

The v2 idle composite exactly matches the build35 runtime layer composite, including the head and face. The old runtime composite itself differs from `assembled.png` at 630 visible pixels with a maximum one-channel delta of 1; v2 preserves that same baseline. The original approved head and face therefore add no new static difference.

The Python review renderer and asset/data checks were run. No device or simulator run was performed. This package documents the character art and animation only; full-scene approval remains with the parent review.
