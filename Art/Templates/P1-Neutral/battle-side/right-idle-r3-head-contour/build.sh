#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
head_work="$(mktemp -d)"
trap 'rm -rf "$head_work"' EXIT
inkscape head-mask.svg --export-filename="$head_work/mask.png" 2>/dev/null
inkscape head-edge.svg --export-filename="$head_work/edge.png" 2>/dev/null
magick "$head_work/mask.png" -alpha off -colorspace gray -alpha copy "$head_work/alpha.png"
magick ../right-idle-r2/00.png "$head_work/alpha.png" -compose DstIn -composite \
  "$head_work/edge.png" -compose over -composite 00.png
