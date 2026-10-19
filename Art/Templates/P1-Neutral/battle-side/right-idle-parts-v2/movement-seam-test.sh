#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT
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

compose_case() {
  local name="$1" dx="$2" dy="$3"
  local move_group="$4"
  local compose=(convert -size 256x256 xc:none parts/body.skin.underlay.png -compose over -composite)
  local moved_arm="body.arm.${move_group}"
  local moved_hand="body.hand.${move_group}"

  for layer in "${layers[@]}"; do
    local path="parts/$layer.png"
    if [[ "$move_group" != none && ( "$layer" == "$moved_arm" || "$layer" == "$moved_hand" ) ]]; then
      convert -size 256x256 xc:none "$path" -geometry "${dx}${dy}" -compose over -composite "$work_dir/$name-$layer.png"
      path="$work_dir/$name-$layer.png"
    elif [[ "$move_group" == near-leg && "$layer" == body.leg.right.near ]]; then
      convert -size 256x256 xc:none "$path" -geometry "${dx}${dy}" -compose over -composite "$work_dir/$name-$layer.png"
      path="$work_dir/$name-$layer.png"
    elif [[ "$move_group" == far-leg && "$layer" == body.leg.left.far ]]; then
      convert -size 256x256 xc:none "$path" -geometry "${dx}${dy}" -compose over -composite "$work_dir/$name-$layer.png"
      path="$work_dir/$name-$layer.png"
    fi
    compose+=("$path" -compose over -composite)
  done

  compose+=(-background '#e8e5dc' -alpha remove -filter point -resize 768x768 -depth 8 "$work_dir/$name.png")
  "${compose[@]}"
}

compose_case rest +0 +0 none
compose_case near-arm +3 +1 right.near
compose_case far-arm -3 +1 left.far
compose_case near-leg +2 -2 near-leg
compose_case far-leg -2 -2 far-leg

for name in rest near-arm far-arm near-leg far-leg; do
  convert "$work_dir/$name.png" -crop 222x270+264+378 +repage -filter point -resize 296x360 -depth 8 "$work_dir/$name-joint.png"
done

montage \
  -font DejaVu-Sans -pointsize 18 -background '#e8e5dc' -fill '#26352f' \
  -label 'REST · underbody below semantic parts' "$work_dir/rest.png" \
  -label 'NEAR ARM +3,+1' "$work_dir/near-arm.png" \
  -label 'FAR ARM -3,+1' "$work_dir/far-arm.png" \
  -label 'NEAR LEG +2,-2' "$work_dir/near-leg.png" \
  -label 'FAR LEG -2,-2' "$work_dir/far-leg.png" \
  -tile 3x2 -geometry 384x384+12+12 movement-seams.png

montage \
  -font DejaVu-Sans -pointsize 18 -background '#e8e5dc' -fill '#26352f' \
  -label 'REST · torso and joints' "$work_dir/rest-joint.png" \
  -label 'NEAR ARM +3,+1' "$work_dir/near-arm-joint.png" \
  -label 'FAR ARM -3,+1' "$work_dir/far-arm-joint.png" \
  -label 'NEAR LEG +2,-2' "$work_dir/near-leg-joint.png" \
  -label 'FAR LEG -2,-2' "$work_dir/far-leg-joint.png" \
  -tile 3x2 -geometry 296x360+12+12 movement-joints.png

cat > movement-seam-test.json <<EOF
{
  "schemaVersion": "1.0.0",
  "purpose": "Rigid single-limb translation checks for underlayer coverage, not animation approval.",
  "canvasPx": [256, 256],
  "testTranslationsPx": {
    "nearArmAndHand": [3, 1],
    "farArmAndHand": [-3, 1],
    "nearLeg": [2, -2],
    "farLeg": [-2, -2]
  },
  "contactSheet": "movement-seams.png",
  "jointDetailSheet": "movement-joints.png",
  "status": "needs-joint-art-revision",
  "seamsPassed": false,
  "findings": [
    "Far-arm displacement leaves an outline at the original shoulder cut.",
    "Leg displacement exposes gaps at the hip and garment edge."
  ],
  "knownLimit": "Rigid shifts are diagnostic; the underbody reaches shoulder and upper-hip roots but does not contain complete limb anatomy, and limb rotations are not tested."
}
EOF
