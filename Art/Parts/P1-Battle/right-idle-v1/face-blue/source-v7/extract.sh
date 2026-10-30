#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Fixed full-canvas registration from the generated 1254px study. Only face
# feature pixels are selected; body, hair, ear, neck and outfit are never copied.
magick generated.png -filter point -resize 256x256 registered.png

face_brow='i>=141&&i<153&&j>=106&&j<110&&r<0.68&&g<0.56'
face_eye='i>=142&&i<153&&j>=110&&j<118&&((r<0.72&&g<0.68)||(b>r&&b>g)||(g>0.78&&b>0.60))'
face_nose="i>=151&&j>=115&&j<124&&i<=(j<118?154:j<119?155:j<122?157:j<123?155:153)&&!($face_eye)"
face_mouth='i>=143&&i<153&&j>=125&&j<129&&r<0.78&&g<0.58&&b<0.45'
face_edge='a>0.75&&!(r>0.55&&g<0.25&&b<0.25)'
face_tmp="$(mktemp -d)"
trap 'rm -rf "$face_tmp"' EXIT

for face_part in brow eye nose mouth; do
  case "$face_part" in
    brow) face_mask="$face_brow" ;;
    eye) face_mask="$face_eye" ;;
    nose) face_mask="$face_nose" ;;
    mouth) face_mask="$face_mouth" ;;
  esac
  magick registered.png -channel A -fx "(($face_mask)&&($face_edge))?a:0" +channel "$face_tmp/raw.png"
  magick -size 256x256 xc:none "$face_tmp/raw.png" -geometry -4+0 -compose over -composite "$face_part.png"
done

magick -size 256x256 xc:none brow.png -compose over -composite \
  eye.png -compose over -composite nose.png -compose over -composite \
  mouth.png -compose over -composite ../face.png
