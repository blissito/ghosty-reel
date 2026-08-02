#!/usr/bin/env bash
# Captura todas las capas de UI que consume scene.py.
#
# Lo que la cámara va a acercar (botón, palabras, paneles, cierre) se captura a
# 2-4x: en el video llega a ocupar media pantalla y a 1x se pixela. La página va
# a 1x porque nunca se acerca.
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

# --- layout de los títulos ---------------------------------------------------
# El navegador MIDE dónde cayó cada palabra y nosotros solo leemos el resultado
# vía --dump-dom. Calcular estas posiciones a mano se desalinea con cualquier
# cambio de fuente, kerning o letter-spacing; medirlas no.
"$CHROME" --headless=new --disable-gpu --virtual-time-budget=5000 \
  --dump-dom "$UI?layer=measure" 2>/dev/null \
  | grep -o 'LAYOUT_JSON:{.*}' | sed 's/^LAYOUT_JSON://' \
  | python3 -c 'import sys,json,html;json.dump(json.loads(html.unescape(sys.stdin.read())),open("assets/layout.json","w"),indent=1,ensure_ascii=False)'

# --- app, botón y cierre -----------------------------------------------------
shot "layer=page" page.png   1920 1080 1
shot "layer=btn"  button.png  280   68  4
shot "layer=end"  end.png     760  270  2

# --- palabras de los títulos del acto 1 --------------------------------------
python3 - <<'PY' | while read -r li i w h; do shot "layer=word&line=$li&i=$i" "w${li}_${i}.png" "$w" "$h" 2; done
import json
lay = json.load(open("assets/layout.json"))
for li, el in enumerate(("t1", "t2")):
    for n, w in enumerate(lay[el]["words"]):
        print(li, n, int(w["w"]) + 10, int(w["h"]) + 10)
PY

# --- títulos de las escenas nuevas (línea completa) --------------------------
shot "layer=line&line=2" t3.png 1500 260 2
shot "layer=line&line=3" t4.png 1500 260 2
shot "layer=line&line=4" t5.png 1500 130 2

# --- tarjetas de archivo -----------------------------------------------------
for i in 0 1 2 3 4 5 6 7; do shot "layer=card&i=$i" "card$i.png" 420 132 3; done

# --- escena 3: el agente -----------------------------------------------------
shot "layer=agent" agent.png 900 240 2
for i in 0 1 2; do shot "layer=tool&i=$i" "tool$i.png" 420 86 3; done

# --- escena 4: la flota ------------------------------------------------------
for i in 0 1 2; do shot "layer=chan&i=$i" "chan$i.png" 400 250 3; done

# --- escena 5: compartir -----------------------------------------------------
shot "layer=share" share.png 760 104 3

printf "%s capas en assets/\n" "$(ls assets/*.png | wc -l | tr -d ' ')"
