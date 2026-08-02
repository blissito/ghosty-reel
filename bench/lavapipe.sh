#!/usr/bin/env bash
# ¿Puede EEVEE renderizar sin GPU?  ->  el número que decide si esto es servicio.
#
# EEVEE es rasterizado y exige contexto Vulkan; las microVMs sobre bare metal no
# tienen GPU. lavapipe (Vulkan por software, de Mesa) es la salida candidata:
# Blender 5.x usa backend Vulkan, así que en teoría entra. NADIE LO HA VERIFICADO
# — de eso se trata esto.
#
# Corre DENTRO del contenedor (bench/Dockerfile). No lo ejecutes suelto en un
# host: instalaría paquetes y dejaría rastro. Ver bench/README.md.
set -uo pipefail

FRAMES="${FRAMES:-200,460,640}"
SCENE="${SCENE:-/work/scene.py}"

hr() { printf '%*s\n' 64 '' | tr ' ' '-'; }

hr; echo "ENTORNO"; hr
blender --version | head -1
echo "VK_ICD_FILENAMES=$VK_ICD_FILENAMES"

hr; echo "¿VULKAN POR SOFTWARE?"; hr
if vulkaninfo --summary 2>/dev/null | grep -iE "driverName|deviceName"; then
  :
else
  echo "!! vulkaninfo no reporta dispositivo."
  echo "   Si Blender tampoco arranca, lavapipe no es viable aquí y el plan B"
  echo "   es Cycles en CPU (ver el final de este script)."
fi

hr; echo "RENDER"; hr
n=$(echo "$FRAMES" | tr ',' '\n' | grep -c .)
LOG=/tmp/bench.log
start=$(date +%s.%N)
# Sin pipe: un `| grep ... || true` se come el codigo de salida y el banco
# reporta "0.00 s/frame" como si fuera un exito cuando Blender ni arranco.
PREVIEW=1 FRAMES="$FRAMES" blender -b -P "$SCENE" > "$LOG" 2>&1
rc=$?
end=$(date +%s.%N)
grep -E "Saved:|Error|error|not supported|fallback" "$LOG" | head -20 || true

# Exito = tantos PNG escritos como frames pedidos. El codigo de salida solo no
# basta: Blender puede salir 0 habiendo fallado el render.
saved=$(grep -c "Saved:" "$LOG" || true)
if [ "$saved" -ne "$n" ]; then
  echo "!! se pidieron $n frames y se guardaron $saved"
  rc=1
fi

hr; echo "RESULTADO"; hr
if [ "$rc" -ne 0 ]; then
  echo "FALLO — el render no se completó. Ultimas lineas:"
  tail -15 "$LOG" | sed 's/^/  /'
  echo
  echo "Plan B: Cycles en CPU, que funciona headless sin nada extra."
  echo "  jq '.render.engine=\"CYCLES\"' scene.json > t && mv t scene.json"
  exit "$rc"
fi

total=$(echo "$end - $start" | bc)
per=$(echo "$total / $n" | bc -l)
printf "%s frames al 40%%, 16 samples: %.1fs total  ->  %.2f s/frame\n" "$n" "$total" "$per"
printf "extrapolado a 1080p/64 samples (~6x): %.1f s/frame\n" "$(echo "$per * 6" | bc -l)"

cat <<'EOF'

Cómo leerlo. Referencia: ~2.2 s/frame a 1080p en EEVEE con GPU (Mac M-series).
Un anuncio de 32s son 960 frames.

  < 3 s/frame    viable tal cual         (~45 min por anuncio)
  3-8 s/frame    viable bajando samples  (o repartiendo frames entre cajas)
  > 15 s/frame   replantear: Cycles CPU, o render en una caja con GPU

El render es stateless y paralelizable por rangos (RANGE=a,b en scene.py), así
que "lento" se compensa con cajas — pero solo hasta cierto punto: cada caja paga
su arranque en frío.
EOF
