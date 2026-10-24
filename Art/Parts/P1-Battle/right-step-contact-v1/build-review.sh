#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
step_tmp="$(mktemp -d)"
trap 'rm -rf "$step_tmp"' EXIT
mkdir -p outfit-forester
# Fixed source registration: 1280px tool canvas -> 256px pose canvas; y +5.
magick reference/generated.png -filter point -resize 256x256 \
  -channel A -threshold 50% +channel -gravity south -background none -extent 256x261 \
  -gravity north -crop 256x256+0+0 +repage -strip "$step_tmp/registered.png"
# Retain all approved jacket, belt, hands and head artwork. No alpha fitting.
magick ../right-idle-v3/outfit-forester/wardrobe.png -crop 256x180+0+0 +repage \
  -gravity north -background none -extent 256x256 "$step_tmp/upper.png"
magick "$step_tmp/registered.png" -crop 256x76+0+180 +repage \
  -gravity south -background none -extent 256x256 "$step_tmp/lower.png"
../../../Templates/P1-Neutral/battle-side/right-step-contact-v1/build.sh
inkscape outfit-forester/coverage-underpaint.svg --export-filename="$step_tmp/coverage.png" 2>/dev/null
magick "$step_tmp/lower.png" ../../../Templates/P1-Neutral/battle-side/right-step-contact-v1/01.png \
  -compose DstIn -composite "$step_tmp/inside-body.png"
magick "$step_tmp/coverage.png" "$step_tmp/inside-body.png" -compose over -composite \
  "$step_tmp/upper.png" -compose over -composite -strip outfit-forester/wardrobe.png
magick ../right-idle-v1/weapon-short-sword/weapon.png \
  ../../../Templates/P1-Neutral/battle-side/right-step-contact-v1/01.png -compose over -composite \
  outfit-forester/wardrobe.png -compose over -composite \
  ../right-idle-v2/hair-chestnut/hair.png -compose over -composite \
  ../right-idle-v2/face-blue/face.png -compose over -composite \
  ../../../Templates/P1-Neutral/battle-side/right-idle-parts-v2/parts/body.hand.right.near.png -compose over -composite \
  ../right-idle-v1/hand-foreground/far.png -compose over -composite -strip assembled.png
magick assembled.png -background '#1f3024' -alpha remove -alpha off -filter point -resize 768x768 -strip review.png
