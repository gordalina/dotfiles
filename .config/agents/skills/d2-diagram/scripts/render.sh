#!/usr/bin/env bash
# House-style D2 render. Usage: ./render.sh [file.d2]  (defaults to the single .d2 in CWD)
# Icons are local (icons/) so this works offline and regenerates identically.
set -euo pipefail
cd "$(dirname "$0")"
SRC="${1:-$(ls *.d2 | head -1)}"
FLAGS=(--layout elk --theme 0 --pad 25 \
  --elk-nodeNodeBetweenLayers 28 --elk-edgeNodeBetweenLayers 20 \
  --elk-padding "[top=24,left=24,bottom=24,right=24]")
d2 "${FLAGS[@]}" "$SRC" "${SRC%.d2}.svg"
d2 "${FLAGS[@]}" "$SRC" "${SRC%.d2}.png"
echo "rendered ${SRC%.d2}.{svg,png}"
