---
mode: autonomous
message: "Los hooks son el único punto del harness donde metes control que no depende de que el modelo obedezca"
audience: "Desarrolladores que construyen con agentes de IA"
aspect: 1080x1920
fps: 30
duration: 120
---

> Dirección de arte: `frame.md` (caricatura plana, sólidos, cero gradientes).
> Style frames aprobados: `styleframes/sf1..sf3.png`.

## Frame bg-field

- status: outline
- src: compositions/bg-field.html
- start: 0 · duration: 110 · track: 0
- beat: Plano de color sólido que cambia por escena (naranja → mint → morado),
  con tres formas geométricas planas con contorno derivando muy despacio en los
  márgenes. Nunca cruzan la columna de contenido. El cambio de color de fondo ES
  el corte de escena: al ras, sin crossfade.

## Frame s1-la-apuesta

- start: 0 · duration: 36 · track: 1 · papel: naranja · voz: 33.6s (`assets/voice/s1-la-apuesta.wav`)
- rules: `discrete-text-sequence`, squash & stretch, `back.out(1.7)`
- beat: El titular entra en bloque de tinta. El post-it de la regla cae torcido
  con rebote. Ghosty entra desde la derecha, ve la nota, y los adornos de tinta
  aparecen en pops discretos: gota, líneas de nervio, interrogación. La cifra
  3% llega de golpe (kinetic slam) y el remate cierra.
- momento clave: Ghosty "lee" la nota — un tilt de 6° hacia el post-it y regreso.

## Frame s2-la-compuerta

- start: 36 · duration: 43 · track: 1 · papel: mint · voz: 40.4s (`assets/voice/s2-la-compuerta.wav`)
- rules: `svg-path-draw` (la flecha se dibuja), `anchored-layout-expand`
- beat: Ghosty y su comando bajan por la flecha hacia la compuerta. El bloque
  PreToolUse se planta con sombra dura y CERO deformación — es la única figura
  del video que no hace squash: la rigidez del dibujo es el argumento. El sello
  "SIEMPRE CORRE" cae rotado. Los dientes entran en cascada de izquierda a
  derecha. El comando choca contra la compuerta y rebota hacia la tarjeta roja.
- momento clave: el rebote. El resto de las cosas del video se deforman; la
  compuerta no.

## Frame s3-la-primitiva

- start: 79 · duration: 31 · track: 1 · papel: morado · voz: 28.3s (`assets/voice/s3-la-primitiva.wav`, tres tomas empalmadas con silencios de 0.55s)
- rules: `stat-bars-and-fills`, `kinetic-beat-slam`
- beat: Las tres tarjetas de framework entran escalonadas 0.12s. Al llegar la
  tercera, las tres etiquetas de color parpadean una vez al unísono y baja el
  bloque "control fuera del modelo". Remate y marca.
- cierre: los dos `[pausa]` del guion son cortes en negro de tinta de ~0.5s.

## Pendientes de producción

1. Sintetizar narración con Kokoro `em_santa` a 0.92 y medir duración real;
   ajustar los `duration` de cada escena a la voz, no al revés.
2. Cama musical sintetizada con ffmpeg, mezclada bajo la voz.
3. `npm run check` antes de renderizar.
4. Subir a Tigris (bucket `wild-bird-2039`, ACL public-read) + `posterWide`
   1200x675 para el correo.
