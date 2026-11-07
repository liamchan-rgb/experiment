#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
face_source='../../right-idle-v1/face-blue/source-v7'
# Discard the unrelated forehead-edge fragment that entered the v7 broad crop.
magick "$face_source/brow.png" -channel A -fx 'i<147?a:0' +channel brow.png
magick "$face_source/eye.png" -channel A -fx 'i<147?a:0' +channel eye.png
magick -size 256x256 xc:none brow.png -compose over -composite \
  eye.png -compose over -composite "$face_source/nose.png" -compose over -composite \
  "$face_source/mouth.png" -compose over -composite face.png
