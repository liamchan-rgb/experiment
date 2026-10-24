#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Reduce the authored 3:2 canvas on a fixed pixel grid, cut the generated
# translucent backdrop at the alpha edge, then fit the sprite back to the
# original registered silhouette bounds and four-hoof ground line.
magick source/idle-pixel-generation.png -channel A -threshold 50% +channel \
  -filter point -resize 384x256\! "$WORK/pixel.png"
magick "$WORK/pixel.png" -filter point -resize 364x245\! "$WORK/registered.png"
magick -size 384x256 xc:none "$WORK/registered.png" \
  -geometry +3+3 -compose over -composite \
  -depth 8 -strip PNG32:idle.png
