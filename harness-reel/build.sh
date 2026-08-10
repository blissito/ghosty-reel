#!/usr/bin/env bash
# Construye el reel completo. Cada paso es idempotente y se puede correr suelto.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -s audio/vo/vo1.wav ] || [ -n "${VOZ:-}" ]; then
  echo "==> 1/5  voz (Kokoro)"
  : "${HYPERFRAMES_PYTHON:=$HOME/.venvs/kokoro/bin/python3}"
  export HYPERFRAMES_PYTHON
  mkdir -p audio/vo
  i=0
  while IFS= read -r l; do
    case "$l" in \#*|"") continue ;; esac
    i=$((i + 1))
    npx hyperframes tts "$l" -v em_santa -l es -s 0.96 -o "audio/vo/vo$i.wav" </dev/null
  done < lines.txt
  echo "    OJO: si cambian las duraciones, actualiza 'vo' y 'beats' en scene.json"
fi

echo "==> 2/5  beats -> audio/plan.json"
python3 plan.py

echo "==> 3/5  bed musical"
python3 music.py

echo "==> 4/5  render (dos pasadas)"
ONLY=ghosty blender -b -P scene.py >/dev/null    # personaje, fondo transparente
blender -b -P scene.py >/dev/null                # base con el diagrama

echo "==> 5/5  mezcla + encode"
./mix.sh
