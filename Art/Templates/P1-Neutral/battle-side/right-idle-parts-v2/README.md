# P1 battle-side right idle · mask repair and joint preflight v2

This candidate preserves the user-approved r2 neutral pose and near/right hand direction on the registered 256×256 canvas. The source pose remains unchanged. The semantic cut masks are now rebuilt as exclusive pixel owners from the editable regions in [authoring.svg](authoring.svg), so no original silhouette pixels need the old fixed-pose coverage patch.

![Mask repair and joint preflight](review.png)

## Mask repair

The previous eight antialiased masks left 442 source pixels outside the semantic parts, and their translucent edges let the hidden core show through. The build now assigns each source pixel to exactly one of the eight semantic masks: authored regions claim first, nearby gaps are assigned to the closest expanded region out to 12 px, and shoulder/hand ties use a limb-aware ownership order. The six remaining isolated source-alpha specks stay with the torso/root layer. The fixed-pose coverage fill was removed.

The assembled eight-part image now matches the registered r2 source exactly: zero differing RGBA pixels and zero silhouette differences. The ownership export keeps the original source pixels and full-canvas coordinates. This is a structural repair; the semantic placement still needs review under movement.

## Hidden anatomy and movement checks

The editable [underbody-authoring.svg](underbody-authoring.svg) contains a 2,298-pixel connected core with short overlaps behind both shoulders and upper-thigh roots. It remains a separate layer so the reviewed r2 pose stays pixel-identical. It does not yet include complete limb anatomy.

[movement-seam-test.sh](movement-seam-test.sh) makes a static diagnostic sheet for four small rigid translations: near/far arms by 3 px and near/far legs by 2 px. It checks only the anatomical shoulder and hip-root windows against the original silhouette; all four windows now have zero uncovered source pixels. Six isolated alpha specks in the approved source remain in the exact static assembly and are excluded from these movement diagnostics so they are not mistaken for anatomy. [movement-joints.png](movement-joints.png) still shows how whole-part translations alter the outer silhouette. This is a localized coverage check, not an animation test or art approval.

The underbody candidate remains separate from the static composite and is still incomplete. Full limb anatomy, articulated redraws, clothing overlap, other poses/directions and runtime integration are not covered.

Hair, face, clothing, footwear, weapon grip, limb rotation, other poses/directions and runtime integration remain out of scope. Do not use this candidate as a production rig or mark the underbody art approved.

## Rebuild and validation

Run `./build.sh` to export the source-pixel partition, underbody candidate, exact static assembly and review image. Run `./movement-seam-test.sh` to regenerate the rigid-shift diagnostic sheets. The structural checks verify 256×256 full-canvas parts, a complete non-overlapping source-pixel partition, underbody containment and exact static reconstruction of r2. Structural success does not replace the remaining movement and art review.
