#!/bin/bash
# Convert a square PNG into a macOS .icns file.
# Usage: ./make_icns.sh icon.png   ->   produces icon.icns
set -e

SRC="${1:?Usage: ./make_icns.sh <source.png>}"
NAME="${SRC%.*}"
ICONSET="${NAME}.iconset"

rm -rf "$ICONSET"
mkdir -p "$ICONSET"

# Apple expects these sizes (1x and 2x variants).
# -s format png forces real PNG output (otherwise sips keeps the source
# encoding and iconutil rejects the iconset).
for size in 16 32 128 256 512; do
    sips -s format png -z $size $size             "$SRC" --out "$ICONSET/icon_${size}x${size}.png"      >/dev/null
    sips -s format png -z $((size*2)) $((size*2)) "$SRC" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done

iconutil -c icns "$ICONSET" -o "${NAME}.icns"
rm -rf "$ICONSET"
echo "Created ${NAME}.icns"
