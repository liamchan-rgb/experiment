#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
bash ../../../Templates/P1-Neutral/battle-side/right-idle-r3-head-contour/build.sh
bash face-blue/build.sh
inkscape hair-chestnut/hair.svg --export-filename=hair-chestnut/hair.png 2>/dev/null
inkscape outfit-forester/shoulder-cleanup.svg --export-filename=outfit-forester/shoulder-cleanup.png 2>/dev/null
magick ../right-idle-v1/outfit-forester/wardrobe.png \
  outfit-forester/shoulder-cleanup.png -compose over -composite outfit-forester/wardrobe.png
magick ../right-idle-v1/weapon-short-sword/weapon.png \
  ../../../Templates/P1-Neutral/battle-side/right-idle-r3-head-contour/00.png -compose over -composite \
  outfit-forester/wardrobe.png -compose over -composite \
  hair-chestnut/hair.png -compose over -composite face-blue/face.png -compose over -composite \
  ../../../Templates/P1-Neutral/battle-side/right-idle-parts-v2/parts/body.hand.right.near.png -compose over -composite \
  ../right-idle-v1/hand-foreground/far.png -compose over -composite assembled.png
magick assembled.png -background '#1f3024' -alpha remove -alpha off -filter point -resize 768x768 review.png
