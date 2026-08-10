#!/usr/bin/env bash
# frames PNG -> MP4. yuv420p + faststart para que se reproduzca en cualquier lado.
set -euo pipefail
cd "$(dirname "$0")"

FPS=$(python3 -c "import json;print(json.load(open('scene.json'))['fps'])")
OUT="out/video.mp4"

command -v ffmpeg >/dev/null || { echo "falta ffmpeg: brew install ffmpeg"; exit 1; }

ffmpeg -y -framerate "$FPS" -pattern_type glob -i 'out/frames/f*.png' \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -movflags +faststart \
  "$OUT" 2>&1 | tail -2

echo "-> $OUT  ($(du -h "$OUT" | cut -f1))"
