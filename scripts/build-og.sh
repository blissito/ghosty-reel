#!/usr/bin/env bash
# Renderiza scripts/og.html a assets/og.png (1200×630) con Chrome headless. Se corre en local
# y el PNG va al repo; el workflow de Pages sólo lo copia.
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1200,630 \
  --virtual-time-budget=6000 --screenshot="$PWD/assets/og.png" "file://$PWD/scripts/og.html" 2>/dev/null
echo "assets/og.png listo"
