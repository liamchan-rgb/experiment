#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT
source_png="../right-idle-r2/00.png"
convert "$source_png" -alpha extract -threshold 0 "$work_dir/source-mask.png"
convert -size 256x256 xc:none -fill white -draw 'point 63,41 point 80,52 point 107,62 point 108,62 point 226,82 point 48,185' "$work_dir/source-specks.png"
convert -size 256x256 xc:black -fill white -draw 'rectangle 105,133 123,151' "$work_dir/near-arm-joint.png"
convert -size 256x256 xc:black -fill white -draw 'rectangle 96,142 112,158' "$work_dir/far-arm-joint.png"
convert -size 256x256 xc:black -fill white -draw 'rectangle 129,174 149,194' "$work_dir/near-leg-joint.png"
convert -size 256x256 xc:black -fill white -draw 'rectangle 95,174 115,194' "$work_dir/far-leg-joint.png"
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
    elif [[ "$layer" == body.torso ]]; then
      # Keep the six isolated alpha specks in the exact static assembly, but
      # omit them from joint diagnostics so they are not mistaken for anatomy.
      convert "$path" "$work_dir/source-specks.png" -compose DstOut -composite "$work_dir/$name-$layer.png"
      path="$work_dir/$name-$layer.png"
    fi
    compose+=("$path" -compose over -composite)
  done

  "${compose[@]}" "$work_dir/$name-full.png"
  convert "$work_dir/$name-full.png" -background '#e8e5dc' -alpha remove -filter point -resize 768x768 -depth 8 "$work_dir/$name.png"
}

compose_case rest +0 +0 none
compose_case near-arm +3 +1 right.near
compose_case far-arm -3 +1 left.far
compose_case near-leg +2 -2 near-leg
compose_case far-leg -2 -2 far-leg

check_joint_coverage() {
  local key="$1" name="$2" region="$3"
  convert "$work_dir/source-mask.png" "$work_dir/$region.png" -compose Multiply -composite "$work_dir/$name-expected.png"
  convert "$work_dir/$name-full.png" -alpha extract -threshold 0 "$work_dir/$name-alpha.png"
  convert "$work_dir/$name-alpha.png" -negate "$work_dir/$name-alpha-inverse.png"
  convert "$work_dir/$name-expected.png" "$work_dir/$name-alpha-inverse.png" -compose Multiply -composite "$work_dir/$name-holes.png"
  convert "$work_dir/$name-holes.png" -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}' > "$work_dir/$name-holes.txt"
  local holes="$(cat "$work_dir/$name-holes.txt")"
  test "$holes" = "0"
  printf '  "%s": %s' "$key" "$holes"
}

{
  printf '{\n'
  check_joint_coverage nearArmJoint near-arm near-arm-joint
  printf ',\n'
  check_joint_coverage farArmJoint far-arm far-arm-joint
  printf ',\n'
  check_joint_coverage nearLegJoint near-leg near-leg-joint
  printf ',\n'
  check_joint_coverage farLegJoint far-leg far-leg-joint
  printf '\n}\n'
} > "$work_dir/joint-coverage.json"

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
  "purpose": "Localized shoulder and hip-root coverage checks under rigid single-limb translations, not animation approval.",
  "canvasPx": [256, 256],
  "testTranslationsPx": {
    "nearArmAndHand": [3, 1],
    "farArmAndHand": [-3, 1],
    "nearLeg": [2, -2],
    "farLeg": [-2, -2]
  },
  "contactSheet": "movement-seams.png",
  "jointDetailSheet": "movement-joints.png",
  "status": "localized-joint-root-windows-passed",
  "jointCoveragePassed": true,
  "wholeSilhouetteSeamsPassed": false,
  "isolatedApprovedSourceSpecksExcludedFromDiagnostic": true,
  "jointCoverageWindowsPx": {
    "nearArm": [105, 133, 123, 151],
    "farArm": [96, 142, 112, 158],
    "nearLeg": [129, 174, 149, 194],
    "farLeg": [95, 174, 115, 194]
  },
  "holesInsideSourceSilhouetteByJointWindow": {
$(cat "$work_dir/joint-coverage.json" | sed '1d;$d')
  },
  "findings": [
    "The four registered joint windows remain covered after the documented rigid translations.",
    "The contact sheet still changes the outer silhouette because whole parts are translated rather than redrawn or posed around a joint."
  ],
  "knownLimit": "A zero-hole result applies only to the four joint windows, not to the whole displaced silhouette. This is a coverage diagnostic, not an animation or artwork approval; limb rotations, redraws, clothing overlap, other poses and directions are not tested."
}
EOF
