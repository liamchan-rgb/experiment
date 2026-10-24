#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
step_tmp="$(mktemp -d)"
trap 'rm -rf "$step_tmp"' EXIT
# A common pose module: lock head, torso, hands and hip root to the current r3.
# Only the legs below y=180 use the retained small-step study.
magick ../right-idle-r3-head-contour/00.png -crop 256x180+0+0 +repage \
  -gravity north -background none -extent 256x256 "$step_tmp/upper.png"
magick ../right-walk-pose-test-v1/frames/01.png -crop 256x76+0+180 +repage \
  -gravity south -background none -extent 256x256 "$step_tmp/lower.png"
magick "$step_tmp/upper.png" "$step_tmp/lower.png" -compose over -composite -strip 01.png
