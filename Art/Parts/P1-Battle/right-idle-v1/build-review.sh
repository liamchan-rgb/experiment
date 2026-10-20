#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
magick weapon-short-sword/weapon.png \
  ../../../Templates/P1-Neutral/battle-side/right-idle-r2/00.png -compose over -composite \
  outfit-forester/wardrobe.png -compose over -composite \
  hair-chestnut/hair.png -compose over -composite face-blue/face.png -compose over -composite \
  ../../../Templates/P1-Neutral/battle-side/right-idle-parts-v2/parts/body.hand.right.near.png -compose over -composite \
  hand-foreground/far.png -compose over -composite assembled.png
magick ../../../Templates/P1-Neutral/battle-side/right-idle-r2/00.png \
  outfit-forester/wardrobe.png -compose over -composite \
  ../../../Templates/P1-Neutral/battle-side/right-idle-parts-v2/parts/body.hand.right.near.png -compose over -composite \
  hand-foreground/far.png -compose over -composite \
  -background '#888888' -alpha remove -filter point -resize 1024x1024 outfit-forester/review-runtime-order.png
