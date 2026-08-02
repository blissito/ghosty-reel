# Benchmark: ¿EEVEE sin GPU?

**Este es el número que decide si el pipeline puede ser un servicio.** Todo lo
demás ya funciona; esto no.

EEVEE es un motor de rasterizado y exige contexto Vulkan. Las microVMs sobre bare
metal no tienen GPU. [lavapipe](https://docs.mesa3d.org/drivers/llvmpipe.html)
—el ICD de Vulkan por software de Mesa— es la salida candidata, y Blender 5.x usa
backend Vulkan, así que en teoría entra. **Nadie lo ha verificado.** Sin este
número, cualquier plan de servicio es especulación.

## Correr

```bash
# desde la raíz del repo, en el HOST LINUX destino
docker build -t ghosty-reel-bench -f bench/Dockerfile bench/
docker run --rm -v "$PWD:/work" ghosty-reel-bench
docker rmi ghosty-reel-bench          # y no queda nada
```

**No deja rastro en el host.** Todo —Blender, Mesa, lavapipe— vive dentro de la
imagen; se construye, se corre y se borra. El único requisito previo es un
runtime de contenedores.

No lo corras suelto con `bash bench/lavapipe.sh` en un host: el script asume que
las dependencias ya están y, si las instalaras a mano, quedarían ahí.

## Por qué en contenedor y no en el host pelado

Además de no ensuciar: un contenedor se parece mucho más al entorno real. Medir
en el host —con todos sus núcleos y su RAM— daría un número optimista que luego
no se cumple dentro de una microVM. Si quieres afinar, acota los recursos a los
de tu template:

```bash
docker run --rm --cpus=2 --memory=3g -v "$PWD:/work" ghosty-reel-bench
```

## Cómo leer el resultado

Referencia a batir: **~2.2 s/frame** a 1080p en EEVEE con GPU (Mac M-series). Un
anuncio de 32s son 960 frames.

| s/frame | Veredicto |
|---|---|
| < 3 | Viable tal cual (~45 min por anuncio) |
| 3–8 | Viable bajando samples, o repartiendo frames entre cajas |
| > 15 | Replantear: Cycles en CPU, o mover el render a una caja con GPU |

El render es *stateless* y paralelizable por rangos (`RANGE=a,b` en `scene.py`),
así que "lento" se compensa con cajas — pero solo hasta cierto punto: cada caja
paga su arranque en frío.

## Si lavapipe no levanta

Plan B es **Cycles en CPU**, que funciona headless sin nada extra:

```bash
jq '.render.engine="CYCLES"' scene.json > t && mv t scene.json
```

Es bastante más lento, pero no depende de Vulkan. Merece su propia medición con
este mismo banco antes de descartarlo.
