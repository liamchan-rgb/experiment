#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

source_png="../right-idle-r2/00.png"
mkdir -p parts
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

part_ids=(
  part-body-leg-left-far
  part-body-arm-left-far
  part-body-hand-left-far
  part-body-leg-right-near
  part-body-torso
  part-head-base
  part-body-arm-right-near
  part-body-hand-right-near
)
part_names=(
  body.leg.left.far
  body.arm.left.far
  body.hand.left.far
  body.leg.right.near
  body.torso
  head.base
  body.arm.right.near
  body.hand.right.near
)
owner_tie_order=(7 6 5 2 1 4 3 0)

# Export the authored SVG regions as candidate shapes, then make a pixel-owner
# partition. The hard ownership masks preserve each source pixel's original RGBA
# once, so antialiased clip edges cannot expose or darken the hidden anatomy.
for i in "${!part_ids[@]}"; do
  inkscape authoring.svg --export-area-page --export-id="${part_ids[$i]}" --export-id-only --export-filename="$work_dir/raw-$i.png" >/dev/null 2>&1
  convert "$work_dir/raw-$i.png" -alpha extract -threshold 0 "$work_dir/core-$i.png"
done

convert "$source_png" -alpha extract -threshold 0 "$work_dir/source-mask.png"
convert -size 256x256 xc:black "$work_dir/claimed.png"
for i in "${!part_ids[@]}"; do
  convert -size 256x256 xc:black "$work_dir/owner-$i.png"
done

for radius in $(seq 0 12); do
  for i in "${!part_ids[@]}"; do
    if [ "$radius" = 0 ]; then
      cp "$work_dir/core-$i.png" "$work_dir/grow-$radius-$i.png"
    else
      convert "$work_dir/core-$i.png" -morphology Dilate "Disk:$radius" "$work_dir/grow-$radius-$i.png"
    fi
  done

  # At ambiguous joint edges, let the limb own its outline before the torso;
  # the final display stack still follows z-order. This keeps moving limb edges
  # from leaving their original outline attached to the stationary torso.
  for i in "${owner_tie_order[@]}"; do
    if [ "$radius" = 0 ]; then
      cp "$work_dir/grow-$radius-$i.png" "$work_dir/shell.png"
    else
      convert "$work_dir/grow-$((radius - 1))-$i.png" -negate "$work_dir/prev-inverse.png"
      convert "$work_dir/grow-$radius-$i.png" "$work_dir/prev-inverse.png" -compose Multiply -composite "$work_dir/shell.png"
    fi
    convert "$work_dir/claimed.png" -negate "$work_dir/unclaimed.png"
    convert "$work_dir/source-mask.png" "$work_dir/shell.png" -compose Multiply -composite "$work_dir/shell-source.png"
    convert "$work_dir/shell-source.png" "$work_dir/unclaimed.png" -compose Multiply -composite "$work_dir/new-owner.png"
    convert "$work_dir/owner-$i.png" "$work_dir/new-owner.png" -evaluate-sequence max "$work_dir/owner-next.png"
    mv "$work_dir/owner-next.png" "$work_dir/owner-$i.png"
    convert "$work_dir/claimed.png" "$work_dir/new-owner.png" -evaluate-sequence max "$work_dir/claimed-next.png"
    mv "$work_dir/claimed-next.png" "$work_dir/claimed.png"
  done
done

# A few isolated source-alpha specks are more than 12 px from every semantic
# mask. Keep them with the fixed torso/root layer rather than losing source pixels.
convert "$work_dir/claimed.png" -negate "$work_dir/unclaimed.png"
convert "$work_dir/source-mask.png" "$work_dir/unclaimed.png" -compose Multiply -composite "$work_dir/residual.png"
convert "$work_dir/residual.png" -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}' > "$work_dir/residual-count.txt"
residual_count="$(cat "$work_dir/residual-count.txt")"
if [ "$residual_count" != 0 ]; then
  convert "$work_dir/owner-4.png" "$work_dir/residual.png" -evaluate-sequence max "$work_dir/owner-next.png"
  mv "$work_dir/owner-next.png" "$work_dir/owner-4.png"
  convert "$work_dir/claimed.png" "$work_dir/residual.png" -evaluate-sequence max "$work_dir/claimed-next.png"
  mv "$work_dir/claimed-next.png" "$work_dir/claimed.png"
fi

for i in "${!part_ids[@]}"; do
  convert "$work_dir/owner-$i.png" -alpha copy "$work_dir/owner-alpha-$i.png"
  convert "$source_png" "$work_dir/owner-alpha-$i.png" -compose DstIn -composite "parts/${part_names[$i]}.png"
done

# Keep the skin core in the shared registered canvas and clip it to the approved
# visible source silhouette; the candidate stays separate from the static composite.
inkscape underbody-authoring.svg --export-area-page --export-id="part-body-skin-underlay" --export-id-only --export-filename="$work_dir/underbody-raw.png" >/dev/null 2>&1
convert "$work_dir/underbody-raw.png" -channel A -threshold 50% +channel "$work_dir/underbody-hard.png"
convert "$source_png" -alpha extract -threshold 0 "$work_dir/source-underbody-mask.png"
convert "$work_dir/source-underbody-mask.png" -alpha copy "$work_dir/source-underbody-alpha.png"
convert "$work_dir/underbody-hard.png" "$work_dir/source-underbody-alpha.png" -compose DstIn -composite parts/body.skin.underlay.png

semantic_parts=()
for name in "${part_names[@]}"; do semantic_parts+=("parts/$name.png"); done
convert "${semantic_parts[@]}" -background none -layers flatten assembled.png
./movement-seam-test.sh
joint_coverage_passed=true # The test exits nonzero unless every local joint window has zero uncovered pixels.
inkscape review.svg --export-area-page --export-filename=review.png >/dev/null 2>&1

test "$(identify -format '%wx%h' assembled.png)" = "256x256"
for part in parts/*.png; do
  test "$(identify -format '%wx%h' "$part")" = "256x256"
  test "$(convert "$part" -alpha extract -format '%[fx:mean]' info:)" != "0"
done

source_pixel_count="$(convert "$source_png" -alpha extract -threshold 0 -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
owned_pixel_sum=0
for part in "${semantic_parts[@]}"; do
  part_pixels="$(convert "$part" -alpha extract -threshold 0 -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
  owned_pixel_sum=$((owned_pixel_sum + part_pixels))
done
convert "${semantic_parts[@]}" -alpha extract -threshold 0 -evaluate-sequence max "$work_dir/part-union.png"
union_pixel_count="$(convert "$work_dir/part-union.png" -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
test "$source_pixel_count" = "$owned_pixel_sum"
test "$source_pixel_count" = "$union_pixel_count"

source_alpha="$work_dir/source-alpha.png"
output_alpha="$work_dir/output-alpha.png"
convert "$source_png" -alpha extract -threshold 0 "$source_alpha"
convert assembled.png -alpha extract -threshold 0 "$output_alpha"
silhouette_diff="$(compare -metric AE "$source_alpha" "$output_alpha" null: 2>&1 || true)"
static_diff="$(compare -metric AE "$source_png" assembled.png null: 2>&1 || true)"
test "$silhouette_diff" = "0"
test "$static_diff" = "0"

source_solid="$work_dir/source-mask.png"
source_solid_alpha="$work_dir/source-mask-alpha-check.png"
outside_underbody="$work_dir/outside-underbody.png"
convert "$source_png" -alpha extract -threshold 0 "$source_solid"
convert "$source_solid" -alpha copy "$source_solid_alpha"
convert parts/body.skin.underlay.png "$source_solid_alpha" -compose DstOut -composite "$outside_underbody"
outside_count="$(convert "$outside_underbody" -alpha extract -threshold 0 -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
test "$outside_count" = "0"

read -r underbody_w underbody_h underbody_x underbody_y <<< "$(convert parts/body.skin.underlay.png -alpha extract -trim -format '%wx%h%X%Y' info: | tr 'x+' '  ')"
underbody_pixels="$(convert parts/body.skin.underlay.png -alpha extract -threshold 0 -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
underbody_component_output="$(convert parts/body.skin.underlay.png -alpha extract -threshold 0 -define connected-components:verbose=true -connected-components 8 null:)"
underbody_components="$(awk '/srgb\(255,255,255\)/ {count++} END {print count + 0}' <<< "$underbody_component_output")"
test "$underbody_components" = "1"

rm -f coverage-fill.png
cat > validation.json <<EOF
{
  "schemaVersion": "1.2.0",
  "status": "passed-structural-checks-with-artwork-limitations",
  "builtBy": "./build.sh",
  "sourcePose": {
    "path": "$source_png",
    "canvasPx": [256, 256],
    "mode": "RGBA",
    "nonTransparentPixels": 5345,
    "sha256": "9ac9c8141617b9eb31084b7139227fa9cf8ab9ccf6fa7a31a98c661a68923065"
  },
  "canvasPx": [256, 256],
  "semanticPartCount": 8,
  "maskRepair": {
    "method": "Exclusive pixel ownership from registered SVG masks; gaps through 12 px go to the nearest region, with joint ties resolved by the limb-aware ownership order in parts.json.",
    "isolatedResidualPixelsAssignedToTorsoRoot": $residual_count,
    "coverageFillPixels": 0,
    "sourcePixelOwnershipSum": $owned_pixel_sum,
    "unownedSourcePixels": 0,
    "multiplyOwnedSourcePixels": 0,
    "rgbaReconstructionDifferencePixelsVsR2": 0
  },
  "underbodyCandidate": {
    "path": "parts/body.skin.underlay.png",
    "editableSource": "underbody-authoring.svg",
    "canvasPx": [256, 256],
    "mode": "RGBA",
    "nonTransparentPixels": $underbody_pixels,
    "alphaBoundsXYWH": [$underbody_x, $underbody_y, $underbody_w, $underbody_h],
    "connectedForegroundComponents": $underbody_components,
    "includedInStaticAssembly": false,
    "complete": false,
    "movementSeamTestPassed": false,
    "localizedJointRootCoveragePassed": $joint_coverage_passed
  },
  "assembled": {
    "canvasPx": [256, 256],
    "nonTransparentPixels": 5345,
    "alphaSilhouetteDifferencePixelsVsSource": $silhouette_diff,
    "rgbaDifferentPixelsVsSource": $static_diff
  },
  "checks": {
    "allSemanticPartsAre256x256RGBAAndNonempty": true,
    "underbodyIs256x256RGBAAndNonempty": true,
    "underbodyIsOneConnectedCore": true,
    "sourceAndPartsShareTheSameCanvasCoordinates": true,
    "sourcePixelPartitionCoversFullR2Silhouette": true,
    "staticAssemblyExactlyMatchesR2Source": true,
    "underbodyIncludedInStaticAssembly": false,
    "underbodyArtworkApproved": false,
    "movementSeamTestPassed": false,
    "localizedJointRootCoveragePassed": $joint_coverage_passed,
    "hiddenAnatomyComplete": false,
    "runtimeIntegrated": false
  },
  "limitations": [
    "Underbody is still a torso/pelvis study; complete arm, hand, and leg anatomy remains unfinished.",
    "The pixel-owner masks reconstruct the source exactly but still need human review for semantic cut placement.",
    "The four local joint-root windows pass under the documented rigid shifts; this does not validate the shifted full silhouette, redraws, or animation.",
    "This package has not passed outfit swapping, weapon grip, other directions, or runtime tests."
  ]
}
EOF
