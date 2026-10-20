---
name: toon-object
description: |
  Objeto 3D real (caja de regalo hecha con primitivas) en three.js dentro de la composición HyperFrames, con
  MeshToonMaterial de 2–3 tonos sólidos, contorno grueso por casco invertido, sombra dura plana proyectada y entrada
  con anticipación, squash-stretch y overshoot. Para un beat «héroe» con volumen sin salir del motor HTML.
triggers:
  - "un objeto 3D en caricatura plana"
  - "una caja de regalo que salta y se abre"
  - "3D toon con contorno grueso en el reel"
origin: investigación motion 20 oct 2026 (fixter2025/docs/motion-investigacion-oct20, propuesta 2), 20 oct 2026
---

# toon-object

Caja de regalo sobre un plato: se agacha, salta girando y crece con `back.out`, aterriza aplastándose, la tapa
salta con el moño girando y cae con rebote; a la izquierda, titular fijo y pastilla que se escribe.

## Cuándo usarla
- Un objeto concreto que tiene que verse sólido y girar (la caja, el teléfono, el cubo de la fábrica): 1–3 beats
  héroe por video. Lo demás (texto, pastillas, SVG) sigue en el DOM con GSAP encima del canvas.
- Cuando un SVG isométrico no basta porque el objeto gira más de ~30° o se abre.

## Cuándo NO (contención)
- Gráficas, diagramas y texto: SVG plano (`iso-bars`, `node-tree`) se lee mejor y es más barato.
- Modelos orgánicos o personajes: el casco invertido de primitivas no da; eso es Blender + Line Art.
- Nunca con `OutlinePass`, `UnrealBloomPass`, `MeshStandardMaterial` con envmap ni `requestAnimationFrame`:
  blur, glow, degradado o cuadros no deterministas.

## Cómo aplicarla
1. Copiar `recipe.html`, editar `PARAMS` (textos, `gift`, `place`, `bands`, `outline`, `light`, `timings`).
2. Otro objeto: reemplazar el bloque «el objeto» por tus primitivas con `part(geo, toon(color), padre)`; cada
   `part` trae su casco y su sombra. Animar sólo dentro de `renderAt(t)` como función pura de `t`.
3. Mantener `data-duration` del HTML igual a `timings.total` (el adaptador `three` no infiere duración).
4. Renderizar: `npx hyperframes render . -c preview.html -o preview.mp4`; verificar `start_time` 0 y `blackdetect`.
5. Para pegar `leap`, `land`, `lid` al beat o a la palabra: `../_lib/beat-snap.js` (ver README).

## Parámetros
| clave | tipo | default | qué controla |
|---|---|---|---|
| palette | "fixtergeek" \| "easybits" | fixtergeek | colores (`panel` = plato, `shadow` = sombra, `outline` = tinta del contorno) |
| kicker, title, label | string, string[], string | … | renglón mono, titular fijo, pastilla typewriter ("" = ninguna) |
| gift | {w,h,lidH,lidOver,ribbon} | 1.6, 1.1, 0.32, 0.08, 0.26 | medidas de la caja en unidades de mundo |
| place | {x,z} | {1.75, 0} | dónde se para el objeto |
| startYaw, restYaw | rad | −1.1, 0.6 | giro de entrada y de reposo |
| bands | number[] | [0.42, 0.72, 1.0] | luz de cada banda del toon (2–3 valores) |
| outline | número | 0.0075 | grosor del contorno, constante en pantalla |
| light | {x,y,z} | {−5, 6, 1.2} | dirección de la luz: bandas y sombra |
| timings.anticip / leap / land | s | 0.15 / 0.4 / 1.0 | se agacha, salta, aterriza |
| timings.lid / lidBack | s | 2.0 / 3.1 | la tapa salta / cae con rebote |
| timings.label / total | s | 2.2 / 4.5 | pastilla y duración |

## SFX sugerido
- `leap` (0.4 s): whoosh corto ascendente mientras gira.
- `land` (1.0 s): golpe sordo + crujido de cartón; el rebote de `back.out(1.8)` no lleva otro sonido.
- `lid` (2.0 s): pop; el golpe visible de `back.out(3)` cae a 1/(3+1) = 25 % de 0.5 s → 2.125 s.
- `lidBack` (3.1 s): toc de tapa con dos rebotes chicos (bounce.out) a ~3.35 y ~3.55 s.
- `label`: click + ticks de typewriter cada 0.035 s.

## Trampas
- El contorno usa normales **promediadas por posición** (`smoothNormal`): con las normales de cara de
  `BoxGeometry` el casco se abre en cada arista.
- Grosor = `thickness × −mv.z` en espacio de vista: constante en pantalla aunque el objeto escale o se acerque.
- El `ShaderMaterial` del casco necesita `#include <colorspace_fragment>` o pinta el color en lineal (más oscuro).
- La tinta del contorno no puede ser el `--bg`: en la silueta desaparece. Va un casi-negro (`#030506`).
- `MeshToonMaterial` con luces físicas (r155+): la luz directa va en `Math.PI` para que la banda 1.0 dé el color exacto
  de la paleta. Sin luz ambiente: la banda más baja la pone `bands[0]`.
- Sombra dura = cada pieza re-dibujada con una matriz de proyección plana sobre y=0 (`shadowProj × matrixWorld`),
  color sólido y `depthWrite:false`. Nada de shadow maps: PCF suaviza y Basic sierra.
- Build UMD `three@0.160.0` (último con `build/three.min.js`): pone `window.THREE`, que es donde el adaptador `three`
  de HyperFrames busca el `DefaultLoadingManager`. Si se cambia a ESM, cargar texturas con `__hf.buildReady`.
- El canvas se dibuja desde dos lados: el evento `hf-seek` del adaptador y un tween de reloj en la timeline GSAP;
  los dos llaman `renderAt(t)` puro, así que da igual cuál llegue primero.
- Cuadro 0: titular fijo + caja chica ya visible sobre el plato (es la miniatura); la pastilla entra después.
