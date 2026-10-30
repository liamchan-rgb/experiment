#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

BODY="$ROOT/Art/Templates/P1-Neutral/battle-side/right-idle-r2/00.png"
SOURCE="$HERE/source/registered-chromakey.png"
MASK_RIGHT="$ROOT/Art/Templates/P1-Neutral/battle-side/right-idle-parts-v2/parts/body.hand.right.near.png"
MASK_LEFT="$ROOT/Art/Templates/P1-Neutral/battle-side/right-idle-parts-v2/parts/body.hand.left.far.png"

# Rebuild from the retained full-canvas source with pixel-art nearest-neighbor sampling.
# Key the chroma matte only after the exact 256x256 whole-canvas registration step.
magick "$SOURCE" -filter point -resize 256x256\! -alpha on -fuzz 48% -transparent '#ff00ff' \
  -fuzz 10% -transparent '#500850' "$WORK/keyed.png"

# Select only the brown footwear silhouettes, then move both boots up four source pixels.
inkscape "$HERE/source/boot-mask.svg" \
  --export-filename="$WORK/boot-mask.png" --export-width=256 --export-height=256 2>/dev/null
magick "$WORK/boot-mask.png" -alpha off -colorspace gray -alpha copy "$WORK/boot-mask-alpha.png"
magick "$WORK/keyed.png" "$WORK/boot-mask-alpha.png" -compose DstOut -composite "$WORK/no-boots.png"
magick "$WORK/keyed.png" "$WORK/boot-mask-alpha.png" -compose DstIn -composite "$WORK/boots.png"
magick -size 256x256 xc:none "$WORK/boots.png" -geometry +0-4 -compose over -composite "$WORK/boots-registered.png"

# Use only the approved neutral pose's alpha as a shape guide. Clothing fills the complete
# trouser/boot silhouette, including dark outline pixels, while the original body stays untouched.
magick "$BODY" -alpha extract "$WORK/body-alpha.png"
magick "$WORK/body-alpha.png" -alpha off -colorspace gray -alpha copy "$WORK/body-silhouette-alpha.png"
magick -size 256x256 xc:black \
  \( "$WORK/body-alpha.png" -crop 14x9+99+177 +repage \) -geometry +99+177 -compose over -composite \
  \( "$WORK/body-alpha.png" -crop 22x22+108+173 +repage \) -geometry +108+173 -compose over -composite \
  \( "$WORK/body-alpha.png" -crop 28x30+89+184 +repage \) -geometry +89+184 -compose over -composite \
  \( "$WORK/body-alpha.png" -crop 32x41+122+173 +repage \) -geometry +122+173 -compose over -composite \
  "$WORK/leg-underlap-mask.png"
magick -size 256x256 xc:black \
  \( "$WORK/body-alpha.png" -crop 15x16+107+134 +repage \) -geometry +107+134 -compose over -composite \
  "$WORK/shoulder-underlap-mask.png"
magick "$WORK/leg-underlap-mask.png" "$WORK/shoulder-underlap-mask.png" -compose Lighten -composite \
  -alpha off -colorspace gray -alpha copy "$WORK/underlap-mask.png"
inkscape "$HERE/source/fit-repair.svg" \
  --export-filename="$WORK/underlap-art.png" --export-width=256 --export-height=256 2>/dev/null
magick "$WORK/underlap-art.png" "$WORK/underlap-mask.png" \
  -compose DstIn -composite "$WORK/underlap.png"
inkscape "$HERE/source/boot-underlap.svg" \
  --export-filename="$WORK/boot-underlap-art.png" --export-width=256 --export-height=256 2>/dev/null
magick "$WORK/boot-underlap-art.png" "$WORK/body-silhouette-alpha.png" \
  -compose DstIn -composite "$WORK/boot-underlap.png"
magick -size 256x256 xc:black -fill white -draw 'rectangle 0,0 255,213' \
  -alpha off -colorspace gray -alpha copy "$WORK/sole-line-alpha.png"

magick "$WORK/underlap.png" "$WORK/no-boots.png" -compose over -composite \
  "$WORK/boot-underlap.png" -compose over -composite \
  "$WORK/boots-registered.png" -compose over -composite \
  "$WORK/sole-line-alpha.png" \
  -compose DstIn -composite "$WORK/wardrobe-green.png"

# Match the map P1's blue signature palette while retaining the original green
# layer's exact alpha, outlines, trim, boots, and registered coordinates.
magick "$WORK/wardrobe-green.png" -colorspace HSL \
  -channel R -fx 'if(r>0.26 && r<0.42 && g>0.15 && b>0.12, 0.60, r)' +channel \
  -channel G -fx 'if(r>0.59 && r<0.61 && g>0.15, min(1,g*1.60), g)' +channel \
  -channel B -fx 'if(r>0.59 && r<0.61 && g>0.15, min(1,b*1.30), b)' +channel \
  -colorspace sRGB -depth 8 -strip "PNG32:$HERE/wardrobe.png"
