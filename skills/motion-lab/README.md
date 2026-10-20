# motion-lab — mecánicas de motion graphics medidas cuadro a cuadro

Quince recetas HyperFrames + GSAP que salieron de replicar, el 17 sep 2026, las escenas de motion
graphics de un video corporativo de TypeSafe AI (laboratorio en `videos/replica-typesafe/`). No son
copias de esas escenas: se midieron posiciones, tamaños, eases y tiempos sobre los cuadros y se
reescribió **la mecánica**, parametrizada, determinista y en las paletas de la casa. Galería con
previews en video: <https://blissito.github.io/ghosty-reel/motion-lab/>.

Cada carpeta trae `SKILL.md` (cuándo usarla, parámetros, SFX sugerido, trampas), `recipe.html`
(la composición con un bloque `PARAMS` al inicio), `preview.html` + `preview.mp4` + `preview.png`.
El contrato de una receta está en `MOLDE.md`. Hoja de contactos: `GALERIA.png`.

| receta | qué hace | de dónde salió |
|---|---|---|
| `window-lower-third` | ventana retro con typewriter, tracking que se cierra, cuerpo que crece, leader line | lower-third de presentación |
| `tilt-list` | lista donde el activo queda horizontal y los demás se inclinan por distancia | lista "disco" de tres puntos |
| `pixel-wipe-sampled` | cortinilla de celdas que muestrean la escena que se va, persisten y se disuelven | transición a diagrama |
| `particle-collapse` | enjambre de puntos que colapsa al contorno de una letra y abre la palabra | anillo → "System One" |
| `barrel-grid` | malla con distorsión de barril, llenado secuencial o paralelo, contador n/N | "el LLM genera secuencialmente" |
| `iso-bars` | cubos isométricos de tres caras con alto y tono por valor | mapa de confianza |
| `hbar-chart` | barras horizontales con grupo en cajita y valores que cuentan | tasa de error por modelo |
| `price-table` | tabla de dos columnas con barras y fila destacada | precios por millón de tokens |
| `scatter-reveal` | dispersión con ejes log, series y marco que se dibuja | inteligencia / costo |
| `node-tree` | nodo central + cajas con cables ortogonales que se dibujan | acrónimo desplegado |
| `hourglass-lines` | curvas que convergen en un glifo y se abren | posibilidades → aplicaciones |
| `radial-rays-counter` | rayos desde el centro + número que cuenta | "38x faster" |
| `word-karaoke-panel` | párrafo que se enciende por palabra en un panel con etiqueta | disclaimer |
| `stacked-boxes` | cajas con `back.out` apiladas sobre guías | "Prod / Not God" |
| `dither-corners` | textura half-tone en esquinas, modos `dots` y `noise` | fondo rosa de las tarjetas |
| `on-twos` | personaje con poses a 12 fps (reloj cuantizado) y cámara/parallax fluidos a 30/60 | investigación motion 20 oct (técnica 5) |
| `squash-hop` | objeto que salta con anticipación, squash & stretch y overshoot; sombra del piso y sombra dura que dicen la altura; `__sfxCues` | investigación motion 20 oct (técnicas 2–4) |
| `smear-dash` | objeto que cruza con smear de 1–2 cuadros, múltiplos y líneas de velocidad en vez de blur; frenón con `back.out` | investigación motion 20 oct (técnica 6) |
| `camera-rig` | cámara virtual por capas: `camera.to({x, y, zoom, rot, yaw})` con parallax real por profundidad, push-in, paneo, whip-pan con smear que transmuta de escena, zoom-punch y dolly-out con corte invisible; 1080×1920 | investigación motion 20 oct (técnicas 8–9, hueco 1 de la auditoría) |
| `toon-object` | escena 3D en three.js: caja de regalo hueca en una mesa, la tapa vuela y sale un robot que saluda; toon de 3 tonos, una silueta de tinta por objeto (redonda, interiores delgados), sombra dura gris, dolly + cambio de ángulo, titular palabra por palabra y CTA que se escribe | investigación motion 20 oct (3D toon en HTML) |

Las captions cinéticas, scrambles y cortinillas de texto ya están en `../motion-anything/`.

## Reglas de uso
- Todo corre en una sola timeline GSAP pausada registrada en `window.__timelines["main"]`: seek-safe.
- Nada de `requestAnimationFrame`, `Math.random` sin semilla ni CSS con reloj propio. Azar = mulberry32 con `PARAMS.seed`.
- Fotograma 0 completo y fondo `--bg` de la paleta (FixterGeek `#0E1317` / EasyBits `#0b0b0f`), nunca `#000`.
- Un SFX por movimiento, montado con ffmpeg fuera del render; cada `SKILL.md` sugiere cuáles y en qué instante.
- Render: `npx hyperframes render . -c preview.html -o preview.mp4` (el CLI toma un directorio; `-c` elige la composición).

## Ritmo al beat: `_lib/beat-snap.js` (y `_lib/beat_snap.py`)
La palabra decide **qué** entra; el beat decide **cuándo** exacto. `snap()` mueve un inicio al beat (o a la palabra)
más cercano sólo si cae a ≤ `maxShift` (0.12 s); si no, lo deja. Con `impact` alinea el golpe visible, no el inicio
(`back.out(s)` → `1/(s+1)` del tween). Redondea al cuadro (30 fps).

```html
<script src="../_lib/beat-snap.js"></script>   <!-- o copiar el archivo junto a la composición -->
<script>
  const beats = BeatSnap.grid({ bpm: 112, offset: 0.21, subdiv: 2, duration: 30 }); // o BeatSnap.beats(detectados)
  const words = BeatSnap.words(TRANSCRIPT);   // JSON de `npx hyperframes transcribe … --json`
  // 1) un tiempo suelto: entra con la palabra «agente» y se afina a la corchea
  T.leap = BeatSnap.snap(BeatSnap.wordAt(words, "agente"), { beats });
  // 2) toda la timeline ya armada: cada tween se corre al beat; los back.out(s) alinean su golpe
  BeatSnap.snapTimeline(tl, { beats, maxShift: 0.1 });
  // 3) pegar a palabras en vez de beats: { words, to: "word" }  ·  a lo que esté más cerca: { beats, words, to: "both" }
</script>
```
En `plan.py` (SFX derivados de beats): `sys.path.insert(0, "skills/motion-lab/_lib"); from beat_snap import grid, words, word_at, snap`
— mismo contrato (`max_shift`, `impact`, `duration`, `to`), así imagen y sonido se ajustan con la misma regla.

## Trampas aprendidas (valen para cualquier composición)
- El renderizador lee el `data-duration` **estático** del HTML; ponerlo desde JS deja cuadros negros al final.
- `gsap.set` fuera de la timeline no sobrevive al seek del render: todo estado inicial va como `tl.set(…, 0)`.
- Typewriter: revelar por `display`, no por `width:auto` (mide 0 si la fuente no cargó). No medir `offsetWidth` antes de que cargue la fuente.
- `blackdetect` (pix_th 0.10) cuenta `#0E1317` como negro: el cuadro 0 necesita panel, retícula o pistas grises además del título.
- Un `div` gigante rotado se rasteriza con arista: usar `<circle>` en SVG. Dentro de SVG, `svgOrigin`; y `gsap.set` con `svgOrigin` sobre un `<g>` reescribe su `transform` a matriz — guardar x,y aparte.
- `animation-fill-mode: both` rellena hacia atrás durante el delay: todo aparece desde el cuadro 0; usar `forwards`.
- `ffmpeg -ss T` antes de `-i` cae en el keyframe equivocado: extraer cuadros de referencia por número (`select='eq(n,N)'`).
- `dot-grid` y `count-up` de motion-anything usan rAF: no sirven en render (aquí van como `<pattern>` SVG y tween sobre objeto).
- `feTurbulence` tiene la luminancia apretada en 0.5: el umbral del dither se calibra como `0.625 − cobertura/4`.
- No rotar patrones SVG (moiré). Las series de un chart no pueden ser la menta ni el verde de la casa (poco croma); `dataviz/validate_palette.js` da `#199E70 #D95926 #9085E9 #C98500` sobre `#0E1317`.
