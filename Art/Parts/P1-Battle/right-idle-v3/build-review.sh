#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
shade_work="$(mktemp -d)"
trap 'rm -rf "$shade_work"' EXIT
shade_parent='../right-idle-v2'
inkscape outfit-forester/rear-edge-tones.svg --export-filename="$shade_work/edge.png" 2>/dev/null
inkscape outfit-forester/rear-shade.svg --export-filename="$shade_work/factor.png" 2>/dev/null
magick "$shade_parent/outfit-forester/wardrobe.png" -alpha extract "$shade_work/original-alpha.png"
magick "$shade_parent/outfit-forester/wardrobe.png" "$shade_work/edge.png" -compose over -composite \
  -alpha off "$shade_work/factor.png" -compose Multiply -composite "$shade_work/colored.png"
magick "$shade_work/colored.png" "$shade_work/original-alpha.png" -compose CopyOpacity -composite \
  -depth 8 -strip PNG32:outfit-forester/wardrobe.png
magick ../right-idle-v1/weapon-short-sword/weapon.png \
  ../../../Templates/P1-Neutral/battle-side/right-idle-r3-head-contour/00.png -compose over -composite \
  outfit-forester/wardrobe.png -compose over -composite \
  "$shade_parent/hair-chestnut/hair.png" -compose over -composite \
  "$shade_parent/face-blue/face.png" -compose over -composite \
  ../../../Templates/P1-Neutral/battle-side/right-idle-parts-v2/parts/body.hand.right.near.png -compose over -composite \
  ../right-idle-v1/hand-foreground/far.png -compose over -composite -strip assembled.png
magick assembled.png -background '#1f3024' -alpha remove -alpha off -filter point -resize 768x768 -strip review.png
