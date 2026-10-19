#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

source_png="../right-idle-r2/00.png"
mkdir -p parts
for pair in \
  'part-body-leg-left-far body.leg.left.far' \
  'part-body-arm-left-far body.arm.left.far' \
  'part-body-hand-left-far body.hand.left.far' \
  'part-body-leg-right-near body.leg.right.near' \
  'part-body-torso body.torso' \
  'part-head-base head.base' \
  'part-body-arm-right-near body.arm.right.near' \
  'part-body-hand-right-near body.hand.right.near'; do
  read -r object_id filename <<<"$pair"
  inkscape authoring.svg --export-area-page --export-id="$object_id" --export-id-only --export-filename="parts/$filename.png" >/dev/null 2>&1
done

# This fixed-pose review layer contains only source pixels not covered by a semantic mask.
# It closes the cut-mask gaps for this one pose; it is not hidden anatomy for runtime movement.
convert parts/*.png -alpha extract -threshold 0 -evaluate-sequence max /tmp/p1-parts-union.png
convert /tmp/p1-parts-union.png -alpha off -negate -threshold 0 /tmp/p1-parts-uncovered.png
convert "$source_png" -alpha extract /tmp/p1-source-alpha.png
convert /tmp/p1-source-alpha.png /tmp/p1-parts-uncovered.png -compose Multiply -composite /tmp/p1-coverage-alpha.png
convert "$source_png" /tmp/p1-coverage-alpha.png -compose CopyOpacity -composite coverage-fill.png

convert coverage-fill.png \
  parts/body.leg.left.far.png \
  parts/body.arm.left.far.png \
  parts/body.hand.left.far.png \
  parts/body.leg.right.near.png \
  parts/body.torso.png \
  parts/head.base.png \
  parts/body.arm.right.near.png \
  parts/body.hand.right.near.png \
  -background none -layers flatten assembled.png

inkscape review.svg --export-area-page --export-filename=review.png >/dev/null 2>&1

test "$(identify -format '%wx%h' assembled.png)" = "256x256"
for part in parts/*.png; do
  test "$(identify -format '%wx%h' "$part")" = "256x256"
  test "$(convert "$part" -alpha extract -format '%[fx:mean]' info:)" != "0"
done

source_alpha="/tmp/p1-parts-source-alpha-$$.png"
output_alpha="/tmp/p1-parts-output-alpha-$$.png"
convert "$source_png" -alpha extract -threshold 0 "$source_alpha"
convert assembled.png -alpha extract -threshold 0 "$output_alpha"
alpha_diff="$(compare -metric AE "$source_alpha" "$output_alpha" null: 2>&1 || true)"
rm -f "$source_alpha" "$output_alpha"
test "$alpha_diff" = "0"
