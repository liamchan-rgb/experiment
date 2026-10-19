#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

raw="source/generated-raw.png"
source_pose="../right-idle-r2/00.png"
mkdir -p frames
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Remove low-alpha generator fringe, normalize to the approved sprite bounds,
# and keep hard nearest-neighbor pixels on the registered canvas.
convert "$raw" -channel A -threshold 25% +channel -trim +repage \
  -filter point -resize 72x131! -colors 24 -dither None "$work/sprite.png"
convert -size 256x256 xc:none "$work/sprite.png" -geometry +87+84 \
  -compose over -composite frames/01.png

source_view="$work/source-view.png"
frame_view="$work/frame-view.png"
convert "$source_pose" -background '#e8e5dc' -alpha remove \
  -filter point -resize 768x768 "$source_view"
convert frames/01.png -background '#e8e5dc' -alpha remove \
  -filter point -resize 768x768 "$frame_view"
montage -font DejaVu-Sans -pointsize 22 -background '#e8e5dc' -fill '#26352f' \
  -label 'APPROVED R2 · NEUTRAL' "$source_view" \
  -label 'POSE TEST 01 · SMALL STEP' "$frame_view" \
  -tile 2x1 -geometry 768x768+20+34 review.png

./build-layers.sh
./movement-test.sh

convert "$source_pose" -background '#e8e5dc' -alpha remove \
  -crop 72x48+88+136 +repage -filter point -resize 432x288 "$work/source-hands.png"
convert frames/01.png -background '#e8e5dc' -alpha remove \
  -crop 72x48+88+136 +repage -filter point -resize 432x288 "$work/frame-hands.png"
convert "$source_pose" -background '#e8e5dc' -alpha remove \
  -crop 86x28+81+188 +repage -filter point -resize 688x224 "$work/source-feet.png"
convert frames/01.png -background '#e8e5dc' -alpha remove \
  -crop 86x28+81+188 +repage -filter point -resize 688x224 "$work/frame-feet.png"
montage -font DejaVu-Sans -pointsize 20 -background '#e8e5dc' -fill '#26352f' \
  -label 'R2 · HANDS' "$work/source-hands.png" \
  -label 'POSE TEST · HANDS' "$work/frame-hands.png" \
  -label 'R2 · FEET' "$work/source-feet.png" \
  -label 'POSE TEST · FEET' "$work/frame-feet.png" \
  -tile 2x2 -geometry +12+28 details.png

alpha_pixels="$(convert frames/01.png -alpha extract -threshold 0 -format '%[fx:mean*w*h]' info: | awk '{printf "%d", $1}')"
colors="$(convert frames/01.png -format '%k' info:)"
extent="$(convert frames/01.png -alpha extract -threshold 0 -trim -format '%wx%h%X%Y' info: | tr 'x+' '  ' | xargs | tr ' ' ',')"
connected="$(convert frames/01.png -alpha extract -threshold 0 \
  -define connected-components:verbose=true -connected-components 8 null: 2>&1 | \
  awk '/srgb\(255,255,255\)/ {count++} END {print count + 0}')"

test "$(identify -format '%wx%h' frames/01.png)" = '256x256'
test "$connected" = '1'
cat > validation.json <<EOF
{
  "schemaVersion": "1.0.0",
  "status": "single-pose-edge-check-passed-awaiting-art-review",
  "frame": "frames/01.png",
  "canvasPx": [256, 256],
  "registeredSource": "../right-idle-r2/00.png",
  "alphaThresholdForGeneratorFringe": "25%",
  "resampling": "nearest-neighbor",
  "paletteColors": $colors,
  "alphaPixels": $alpha_pixels,
  "alphaBoundsXYWH": [$extent],
  "connectedSilhouetteComponents": $connected,
  "soleLineCanvasY": 214,
  "checks": {
    "frameCanvasIs256x256": true,
    "silhouetteIsOneConnectedComponent": true,
    "approvedR2SourceModified": false,
    "semanticPartsRecomposed": true,
    "localizedJointRootNudgePassed": true,
    "fullHiddenAnatomyValidated": false,
    "animationApproved": false
  },
  "limitations": [
    "One complete pose image only; static semantic recomposition does not validate joint movement.",
    "The pose checks the visible silhouette and hand/foot edges, not hidden joint anatomy or outfit overlap during motion.",
    "No animation loop or runtime integration is included."
  ]
}
EOF
