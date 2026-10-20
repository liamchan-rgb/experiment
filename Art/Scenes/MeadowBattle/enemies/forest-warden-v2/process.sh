#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Whole-canvas 1:4 reduction, no alpha fitting or independent limb warping.
# RGB chroma selection removes dark magenta edge pixels as well as the flat key.
magick source/idle-chromakey.png -alpha set -channel A \
  -fx '(r>g*1.15 && b>g*1.15 && r+b>g*3)?0:1' +channel \
  -filter point -resize 384x256\! idle.png
