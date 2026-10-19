#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
layers=(
  body.leg.left.far
  body.arm.left.far
  body.hand.left.far
  body.leg.right.near
  body.torso
  head.base
  body.arm.right.near
  body.hand.right.near
)

compose_frame() {
  local name="$1"
  local compose=(convert -size 256x256 xc:none parts/body.skin.underlay.png -compose over -composite)
  for layer in "${layers[@]}"; do
    local path="parts/$layer.png"
    case "$layer" in
      body.arm.left.far|body.hand.left.far)
        convert -size 256x256 xc:none "$path" -geometry -1+0 -compose over -composite "$work/$name-$layer.png"
        path="$work/$name-$layer.png"
        ;;
      body.leg.left.far)
        convert -size 256x256 xc:none "$path" -geometry -1+0 -compose over -composite "$work/$name-$layer.png"
        path="$work/$name-$layer.png"
        ;;
      body.arm.right.near|body.hand.right.near|body.leg.right.near)
        convert -size 256x256 xc:none "$path" -geometry +1+0 -compose over -composite "$work/$name-$layer.png"
        path="$work/$name-$layer.png"
        ;;
    esac
    compose+=("$path" -compose over -composite)
  done
  "${compose[@]}" "$work/$name-full.png"
}

compose_frame nudge
convert assembled/01.png -background '#e8e5dc' -alpha remove -filter point -resize 768x768 "$work/rest.png"
convert "$work/nudge-full.png" -background '#e8e5dc' -alpha remove -filter point -resize 768x768 "$work/nudge.png"
montage -font DejaVu-Sans -pointsize 20 -background '#e8e5dc' -fill '#26352f' \
  -label 'POSE 01 · STATIC LAYER COMPOSITE' "$work/rest.png" \
  -label 'LIMB ROOT NUDGE · ±1 PX' "$work/nudge.png" \
  -tile 2x1 -geometry 768x768+18+32 movement-test.png

convert frames/01.png -alpha extract -threshold 0 "$work/source-alpha.png"
convert "$work/nudge-full.png" -alpha extract -threshold 0 "$work/nudge-alpha.png"
convert -size 256x256 xc:black "$work/holes-union.png"
for region in 'near-arm 105 133 123 151' 'far-arm 96 142 112 158' 'near-leg 129 174 149 194' 'far-leg 95 174 115 194'; do
  read -r name x1 y1 x2 y2 <<< "$region"
  convert -size 256x256 xc:black -fill white -draw "rectangle $x1,$y1 $x2,$y2" "$work/window.png"
  convert "$work/source-alpha.png" "$work/window.png" -compose Multiply -composite "$work/expected.png"
  convert "$work/nudge-alpha.png" -negate "$work/inverse.png"
  convert "$work/expected.png" "$work/inverse.png" -compose Multiply -composite "$work/holes-$name.png"
  convert "$work/holes-union.png" "$work/holes-$name.png" -evaluate-sequence max "$work/holes-next.png"
  mv "$work/holes-next.png" "$work/holes-union.png"
  convert "$work/holes-$name.png" -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}' > "$work/holes-$name.txt"
done

convert -size 256x256 xc:red "$work/holes-union.png" -compose CopyOpacity -composite "$work/hole-red.png"
cp "$work/holes-union.png" movement-hole-mask.png
convert "$work/nudge-full.png" -background '#e8e5dc' -alpha remove \
  "$work/hole-red.png" -compose over -composite -filter point -resize 1024x1024 movement-holes.png

near_arm="$(cat "$work/holes-near-arm.txt")"
far_arm="$(cat "$work/holes-far-arm.txt")"
near_leg="$(cat "$work/holes-near-leg.txt")"
far_leg="$(cat "$work/holes-far-leg.txt")"
components="$(convert "$work/nudge-alpha.png" -define connected-components:verbose=true -connected-components 8 null: 2>&1 | awk '/srgb\(255,255,255\)|gray\(255\)/ {count++} END {print count + 0}')"
test "$near_arm" = '0'
test "$far_arm" = '0'
test "$near_leg" = '0'
test "$far_leg" = '0'
test "$components" = '1'
cat > movement-validation.json <<EOF
{
  "schemaVersion": "1.0.0",
  "status": "single-pixel-root-nudge-diagnostic",
  "pose": "frames/01.png",
  "underlay": "parts/body.skin.underlay.png",
  "translationsPx": {
    "farArmAndHand": [-1, 0],
    "nearArmAndHand": [1, 0],
    "farLeg": [-1, 0],
    "nearLeg": [1, 0]
  },
  "jointWindowUncoveredPixels": {
    "nearArm": $near_arm,
    "farArm": $far_arm,
    "nearLeg": $near_leg,
    "farLeg": $far_leg
  },
  "connectedSilhouetteComponents": $components,
  "checks": {
    "allFourJointWindowsCovered": $([ "$near_arm" = 0 ] && [ "$far_arm" = 0 ] && [ "$near_leg" = 0 ] && [ "$far_leg" = 0 ] && echo true || echo false),
    "nudgeIsARealAnimationFrame": false,
    "underbodyIsComplete": false
  },
  "limitation": "A one-pixel rigid root nudge checks only local coverage; it is not a natural pose or animation approval."
}
EOF
