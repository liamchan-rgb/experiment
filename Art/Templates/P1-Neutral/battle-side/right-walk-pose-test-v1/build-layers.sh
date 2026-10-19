#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

source_png="frames/01.png"
mkdir -p parts assembled
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

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
z_order=(0 1 2 3 4 5 6 7)
tie_order=(7 6 5 2 1 4 3 0)

for i in "${!part_ids[@]}"; do
  inkscape authoring.svg --export-area-page --export-id="${part_ids[$i]}" \
    --export-id-only --export-filename="$work/raw-$i.png" >/dev/null 2>&1
  convert "$work/raw-$i.png" -alpha extract -threshold 0 "$work/core-$i.png"
  convert -size 256x256 xc:black "$work/owner-$i.png"
done

convert "$source_png" -alpha extract -threshold 0 "$work/source-mask.png"
convert -size 256x256 xc:black "$work/claimed.png"

for radius in $(seq 0 12); do
  for i in "${!part_ids[@]}"; do
    if [ "$radius" = 0 ]; then
      cp "$work/core-$i.png" "$work/grow-$radius-$i.png"
    else
      convert "$work/core-$i.png" -morphology Dilate "Disk:$radius" "$work/grow-$radius-$i.png"
    fi
  done

  for i in "${tie_order[@]}"; do
    if [ "$radius" = 0 ]; then
      cp "$work/grow-$radius-$i.png" "$work/shell.png"
    else
      convert "$work/grow-$((radius - 1))-$i.png" -negate "$work/prev-inverse.png"
      convert "$work/grow-$radius-$i.png" "$work/prev-inverse.png" \
        -compose Multiply -composite "$work/shell.png"
    fi
    convert "$work/claimed.png" -negate "$work/unclaimed.png"
    convert "$work/source-mask.png" "$work/shell.png" -compose Multiply -composite "$work/shell-source.png"
    convert "$work/shell-source.png" "$work/unclaimed.png" -compose Multiply -composite "$work/new-owner.png"
    convert "$work/owner-$i.png" "$work/new-owner.png" -evaluate-sequence max "$work/owner-next.png"
    mv "$work/owner-next.png" "$work/owner-$i.png"
    convert "$work/claimed.png" "$work/new-owner.png" -evaluate-sequence max "$work/claimed-next.png"
    mv "$work/claimed-next.png" "$work/claimed.png"
  done
done

convert "$work/claimed.png" -negate "$work/unclaimed.png"
convert "$work/source-mask.png" "$work/unclaimed.png" -compose Multiply -composite "$work/residual.png"
residual="$(convert "$work/residual.png" -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
if [ "$residual" != 0 ]; then
  convert "$work/owner-4.png" "$work/residual.png" -evaluate-sequence max "$work/owner-4-next.png"
  mv "$work/owner-4-next.png" "$work/owner-4.png"
  convert "$work/claimed.png" "$work/residual.png" -evaluate-sequence max "$work/claimed-next.png"
  mv "$work/claimed-next.png" "$work/claimed.png"
fi

for i in "${!part_names[@]}"; do
  convert "$work/owner-$i.png" -alpha copy "$work/owner-alpha-$i.png"
  convert "$source_png" "$work/owner-alpha-$i.png" -compose DstIn -composite "parts/${part_names[$i]}.png"
done

inkscape pose-underlay-authoring.svg --export-area-page --export-id="pose-underlay-patches" \
  --export-id-only --export-filename="$work/underlay-patches.png" >/dev/null 2>&1
convert ../right-idle-parts-v2/parts/body.skin.underlay.png "$work/underlay-patches.png" \
  -compose over -composite parts/body.skin.underlay.png

ordered_parts=()
for i in "${z_order[@]}"; do ordered_parts+=("parts/${part_names[$i]}.png"); done
convert "${ordered_parts[@]}" -background none -layers flatten assembled/01.png
static_diff="$(compare -metric AE "$source_png" assembled/01.png null: 2>&1 || true)"
test "$static_diff" = '0'

source_pixels="$(convert "$work/source-mask.png" -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
owner_sum=0
part_paths=()
for name in "${part_names[@]}"; do
  part="parts/$name.png"
  part_paths+=("$part")
  pixels="$(convert "$part" -alpha extract -threshold 0 -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
  owner_sum=$((owner_sum + pixels))
  convert "$part" -background '#e8e5dc' -alpha remove -crop 90x140+83+78 +repage \
    -filter point -resize 270x420 "$work/${name}.png"
done
convert "${part_paths[@]}" -alpha extract -threshold 0 -evaluate-sequence max "$work/union.png"
union_pixels="$(convert "$work/union.png" -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
test "$source_pixels" = "$owner_sum"
test "$source_pixels" = "$union_pixels"

montage -font DejaVu-Sans -pointsize 16 -background '#e8e5dc' -fill '#26352f' \
  -label 'FAR LEG' "$work/body.leg.left.far.png" \
  -label 'FAR ARM' "$work/body.arm.left.far.png" \
  -label 'FAR HAND' "$work/body.hand.left.far.png" \
  -label 'NEAR LEG' "$work/body.leg.right.near.png" \
  -label 'TORSO' "$work/body.torso.png" \
  -label 'HEAD' "$work/head.base.png" \
  -label 'NEAR ARM' "$work/body.arm.right.near.png" \
  -label 'NEAR HAND' "$work/body.hand.right.near.png" \
  -tile 4x2 -geometry 270x420+8+26 parts-review.png

cat > layers-validation.json <<EOF
{
  "schemaVersion": "1.0.0",
  "status": "static-semantic-recomposition-passed",
  "sourceFrame": "frames/01.png",
  "assembledFrame": "assembled/01.png",
  "canvasPx": [256, 256],
  "partCount": 8,
  "underlay": "parts/body.skin.underlay.png",
  "localizedUnderlayPatchPixels": 14,
  "sourcePixelCount": $source_pixels,
  "sumOfExclusivePartPixels": $owner_sum,
  "unionPartPixels": $union_pixels,
  "unassignedSourcePixelsBeforeRootFallback": $residual,
  "rgbaReconstructionDifferencePixels": $static_diff,
  "ownership": "Exclusive source-pixel assignment from editable authored cores; nearest expanded core through 12 px, limb-aware tie order.",
  "checks": {
    "allParts256x256": true,
    "sourcePixelsPartitionedOnce": true,
    "semanticCompositeMatchesSourceExactly": true,
    "hiddenAnatomyMovementTested": false,
    "poseApproved": false
  },
  "limitations": [
    "Static recomposition confirms layer coverage only; it does not validate movement seams or complete hidden anatomy.",
    "The pose itself remains a single generated art candidate and is not production-approved."
  ]
}
EOF
