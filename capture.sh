#!/usr/bin/env bash
# Captura todas las capas de UI que consume scene.py.
#
# Los elementos que la cámara va a acercar (botón, títulos, tarjetas, cierre) se
# capturan a 3-4x: en el video llegan a ocupar media pantalla y a 1x se pixelan.
# La página va a 1x porque nunca se acerca.
set -euo pipefail
cd "$(dirname "$0")"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UI="file://$PWD/ui.html"
mkdir -p assets

shot () { # $1=query $2=out $3=w $4=h $5=scale
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor="$5" --default-background-color=00000000 \
    --virtual-time-budget=4000 \
    --window-size="$3,$4" --screenshot="assets/$2" "$UI?$1" >/dev/null 2>&1
}

shot "layer=page" page.png   1920 1080 1
shot "layer=btn"  button.png  280   68  4
shot "layer=t1"   t1.png     1500  240  2
shot "layer=t2"   t2.png     1500  130  2
shot "layer=end"  end.png     760  270  2

for i in 0 1 2 3 4 5 6 7; do
  shot "layer=card&i=$i" "card$i.png" 420 132 3
done

for f in assets/*.png; do
  printf '%-22s %s\n' "$(basename "$f")" \
    "$(sips -g pixelWidth -g pixelHeight "$f" | tail -2 | tr -d ' \n' | sed 's/pixel/ /g')"
done
