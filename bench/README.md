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

---

## Resultado — medido 2026-08-02, box B (SYS-3, Xeon-E 2288G, 8c/16t, 128 GB)

**Veredicto: EEVEE sobre lavapipe NO sirve para producción.**

Lo bueno: la duda técnica se resolvió. **lavapipe levanta** (`llvmpipe (LLVM
15.0.6)`) y Blender 5.2 renderiza sin GPU. Solo hubo que añadir `libxkbcommon0`
y compañía; los `EGL_BAD_MATCH` son ruido, no fallo.

Lo malo, los números:

| Medición | Resultado |
|---|---|
| 40% res, 16 samples | 33s / 357s / 495s para 1 / 6 / 11 frames |
| **1080p, 64 samples** | **~10 min por frame** (8 núcleos) |
| Anuncio de 32s (960 frames) | **~160 horas** |

Referencia: ~2.2 s/frame en el mismo render con GPU. La rasterización por CPU es
~270× más lenta.

**Repartir entre cajas no lo salva.** Harían falta cientos de microVMs corriendo
horas para un solo anuncio, y el KS-5 tiene 8 núcleos en total para toda la flota.

### Notas de método (para no repetir los errores)

**No midas un solo frame.** El arranque de Blender y la construcción de la escena
son coste fijo; con un frame dominan el total y el número sale inflado.

**Pero tampoco asumas linealidad.** Los tres puntos dieron marginales de 65 y
luego 28 s/frame: los frames no cuestan igual entre sí (una escena con más planos
es más cara) y hay efectos de caché. Un único "s/frame" no está bien definido.

**No extrapoles de preview a calidad final.** Estimé "×6" a ojo; el salto real es
6× píxeles y 4× samples. Medir un frame a calidad final directamente eliminó toda
la conjetura — y cambió la conclusión de "malo" a "inviable".

**Un benchmark que falla en silencio es peor que ninguno.** La primera versión
reportó "0.00 s/frame" como éxito cuando Blender ni había arrancado: un
`| grep ... || true` se comía el código de salida. Ahora verifica el código Y
cuenta los PNG escritos.

### Qué queda

Este pipeline es **local o con GPU**. Como servicio en la flota de microVMs, no.
Las opciones reales son una máquina con GPU fuera de la flota, un proveedor de
render por GPU, o aceptar que la generación sea local en la máquina del usuario.
