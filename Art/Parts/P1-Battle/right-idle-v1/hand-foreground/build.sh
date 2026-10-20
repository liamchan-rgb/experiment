#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Correct semantic ownership in the redundant foreground hand copy only.
# The full approved neutral body and original split remain untouched.
magick ../../../../Templates/P1-Neutral/battle-side/right-idle-parts-v2/parts/body.hand.left.far.png \
  -crop 256x177+0+0 +repage -background none -gravity northwest -extent 256x256 far.png
