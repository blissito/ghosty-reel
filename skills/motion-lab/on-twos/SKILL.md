---
name: on-twos
description: |
  Personaje u objeto que cambia de pose «a dos» (12 fps, poses escalonadas) mientras la cámara y el
  fondo se mueven fluidos a la fps del render (30/60). El look de animación a mano / stop-motion.
triggers:
  - "que el personaje se mueva a 12 fps y la cámara fluida"
  - "look de animación a mano / stop motion"
  - "animar a dos (on twos)"
  - "robot caminando con el fondo pasando"
origin: técnica 5 de fixter2025/docs/motion-investigacion-oct20/3-tecnicas-de-los-mejores.md, 20 oct 2026
---

# on-twos

Un robot camina en su lugar y saluda; sus poses saltan cada 1/12 s mientras nubes, cerros, postes y piso
pasan con parallax continuo y la cámara hace un dolly suave.

## Cuándo usarla
- Personajes (Ghosty, robots, mascotas) que deben sentirse dibujados, no interpolados por computadora.
- Escenas donde conviven personaje + cámara: el contraste de cadencias es el efecto.

## Cuándo NO (contención)
- UI, texto o charts: a 12 fps se ven trabados, no artesanales. Ésos van continuos.
- Si todo va a 12 fps (cámara incluida) se pierde el truco y parece un video con cuadros caídos.

## Cómo aplicarla
1. Copiar `recipe.html`, cambiar el SVG del personaje y editar `PARAMS`.
2. Todo lo del personaje va en la timeline `ch` (eases normales); la cámara y el fondo van en `tl`.
3. El truco: un tween de reloj en `tl` hace `ch.seek(floor(t·charFps)/charFps)` en su `onUpdate`. Todas las
   partes del personaje cambian de pose en el MISMO cuadro (con `steps(n)` por tween se desfasan).
4. Render: `npx hyperframes render . -c recipe.html -o out.mp4` (`-f 60` para cámara a 60).

## Parámetros
| clave | tipo | default | qué controla |
|---|---|---|---|
| palette | "fixtergeek" \| "easybits" | fixtergeek | variables `--bg --ink --accent --accent2 --muted` |
| charFps | number | 12 | cadencia del personaje (15 = dos exactos a 30 fps) |
| camFps | number | 30 | sólo el texto de la pastilla |
| label | bool | true | pastilla «personaje 12 fps · cámara 30 fps» |
| stepPeriod | s | 0.5 | ciclo de paso completo |
| pan | {far, mid, near} px | 160 / 320 / 900 | recorrido de cada capa (parallax) |
| camZoom | number | 1.06 | dolly de la cámara (`sine.inOut`) |
| wave | {at, times} | 2.4 / 3 | saludo con el brazo derecho, N veces (finito) |
| blinkAt | s | 1.5 | parpadeo |

## SFX sugerido
- Pasos: `tap` suave en cada contacto de pie (cada `stepPeriod/2`, alternando dos samples), alineado al
  cuadro de 12 fps (`floor(t·12)/12`), no al tiempo continuo.
- Saludo: `pop` en `wave.at + 0.25/(2+1)` ≈ +0.08 s (el brazo sube con `back.out(2)`).

## Trampas
- A 30 fps, 12 fps sostiene 3-2-3-2 cuadros (medido sobre el mp4: cambia en los cuadros 2, 4, 7, 9, 12…). Si se
  nota el vaivén, usar `charFps: 15`.
- `ch.seek(0)` sobre una timeline que ya está en 0 no pinta: el cuadro 0 salía con las piernas rectas. Se fuerza
  con `ch.seek(0.001).seek(0)`.
- El zoom de la cámara también escala al personaje: es correcto (es cámara), pero al medir la cadencia recorta
  una zona que no cruce el zoom o compara antes de que arranque.
- La sombra dura es un `<use>` del personaje con `--sh: var(--bg)`: cada forma pinta `fill:var(--sh, color)`,
  así el clon hereda las poses sin duplicar tweens.
