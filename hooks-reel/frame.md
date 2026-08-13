# Design spec — "Hooks: el control que no depende del modelo"

## Concepto

Caricatura plana. Todo se dibuja como si fuera un cartoon impreso: figuras
simples con **contorno de tinta grueso**, rellenos de **color sólido** y cero
profundidad falsa. El video anterior usaba luz (blobs radiales, glow, grano);
este usa **tinta y papel de color**.

La idea visual que carga el tema: el modelo es una figura blanda y voluble
(cambia de color, se deforma, a veces obedece y a veces no). El hook es una
figura rígida de tinta: **una compuerta que siempre está ahí**, no se deforma,
no negocia. La rigidez del hook es literalmente la rigidez del dibujo.

## Prohibido

- Gradientes de cualquier tipo (`linear-gradient`, `radial-gradient`, `conic-`).
- `box-shadow` difuso, `filter: blur()`, `text-shadow`, glow, bloom.
- Opacidades intermedias para simular volumen.
- Grano, ruido, texturas fotográficas.

La única sombra permitida es la **sombra dura de caricatura**: un offset sólido
sin difuminado (`box-shadow: 8px 8px 0 var(--ink)`), siempre en tinta.

## Reglas de composición (aprendidas en la revisión del 13 de agosto)

1. **El texto nunca flota suelto sobre el campo.** Las formas del fondo pasan
   por detrás y lo vuelven ilegible — un círculo cyan bajo texto crema mata el
   contraste y el contorno de tinta cruza las letras. Todo remate va dentro de
   un bloque sólido con contorno.
2. **Nada en las esquinas inferiores salvo la marca.** El número de escena en
   la esquina chocaba con las formas del fondo; ahora vive en el kicker
   (`01 · el problema`).
3. **Las formas del fondo se quedan en los márgenes**, mordidas por el borde
   del cuadro. No cruzan la columna de contenido.
4. **Máximo cuatro bloques de contenido por cuadro** además del titular. Si
   hace falta un quinto, es otra escena.
5. **El personaje es Ghosty oficial, no un dibujo inventado.** El asset vive en
   `assets/ghosty.png` (copiado de `~/ghosty-launch/assets/ghosty.png`, 810x936,
   transparente). **Nunca se repinta ni se le pone placa de fondo.** La emoción
   la ponen los adornos de caricatura en tinta que lo rodean — gota de sudor,
   líneas de nervio, signo de interrogación —, no el personaje.
   Ghosty es morado: el bloque sobre el que se monta nunca puede ser morado.
   **Excepción decidida el 13 de agosto: en video Ghosty SÍ lleva boca**, un
   trazo de tinta dibujado encima del PNG (no se repinta el asset) que existe
   sólo para actuar la emoción. Siempre torcida o asimétrica, nunca una sonrisa
   simétrica. En producto Ghosty sigue sin boca; ésta es su versión expresiva
   para video, del mismo modo que la gota de sudor y las líneas de nervio
   tampoco están en el logo.
6. **Los dibujos son dibujos, no emojis.** Contorno irregular hecho a mano,
   asimetría deliberada (ojos de distinto tamaño, boca torcida), y detalles de
   más: gota de sudor, líneas de nervio, ceja levantada. Una carita simétrica
   de círculo perfecto se ve floja.

## Paleta (sólidos planos, sin mezclas)

| Rol | Hex | Uso |
| --- | --- | --- |
| ink | `#141A1F` | contornos, sombras duras, texto sobre claro |
| paper | `#F7F0E4` | texto sobre oscuro, rellenos claros, "papel" |
| mint | `#4ECFAF` | el hook, el control determinista |
| purple | `#9B7FE8` | el modelo, lo probabilístico |
| orange | `#F29130` | tensión, la petición que puede fallar |
| red | `#E0574E` | la falla, lo que se coló |
| cyan | `#4FC7EE` | datos, herramientas, I/O |
| grass | `#7FC95C` | confirmación, lo que sí pasó |
| yellow | `#F5C542` | énfasis, remates, marca |

Regla de uso: **máximo cuatro colores por cuadro** más tinta y papel. Los
fondos son un color sólido de la paleta (no `#0E1317`): cada escena tiene su
color de papel y el corte de escena es un cambio franco de color.

## Tipografía

- **Archivo Black 400** — display. Titulares 110–170px, tracking `-0.03em`.
  Siempre con contorno de tinta o sobre bloque de color sólido.
- **JetBrains Mono 400/700** — código, etiquetas, cifras. Cuerpo 32–42px,
  etiquetas 24–28px.

Los titulares pueden ir dentro de un **bloque de color con sombra dura**, como
rótulo de caricatura. Nunca texto suelto flotando sobre el fondo en escenas de
remate.

## Fondo (`bg-field`, pista 0, 0 → fin)

Reemplaza al campo de blobs del video anterior. Es un **plano de color sólido**
que cambia por escena, con tres o cuatro formas geométricas planas (círculos,
triángulos, arcos gruesos de tinta) desplazándose muy despacio en bucle. Las
formas tienen contorno y no se traslapan con opacidad: se ocultan unas a otras.
Nunca se detiene, pero es tranquilo — el ruido visual va en las escenas.

## Música

**Una pista distinta por escena, cortada en la transición** — no una sola cama
para todo el video. El cambio de música refuerza el cambio de papel y de tema.
Cada pista se recorta al largo exacto de su escena, con fade de entrada de 1.2s
y de salida de 1.2s, normalizada a −20 LUFS, y suena entre 0.11 y 0.13 de
volumen para no pelear con la narración.

En este video la música es **movida** (117–161 BPM); la escena 2, la del
mecanismo, lleva la más rápida.

## Estados de ánimo de Ghosty

Ghosty actúa: cambia de ánimo durante la narración. Cada estado es un grupo SVG
encima del PNG que se prende y apaga con `opacity`, y son excluyentes — al
entrar uno se apagan los adornos del anterior.

| Estado | Vocabulario |
| --- | --- |
| normal | boca torcida, gota de sudor, líneas de nervio, interrogación |
| mareado | boca de zigzag, dos remolinos, cuerpo oscilando en rotación |
| emo | fleco sobre un ojo, boca plana caída, lágrima, cuerpo hundiéndose |

Cada estado se sostiene 4s o más — el chiste necesita tiempo en pantalla — y al
final vuelve al normal antes del remate.

**Sincronización: SIEMPRE con timestamps medidos.**

```bash
npx hyperframes transcribe assets/voice/<escena>.wav --language es --model medium --json
```

Estimar contando caracteres falla, y `silencedetect` falla peor: marca pausas de
respiración dentro de las frases, no los límites entre ellas — así fue como los
estados quedaron 3.3s tarde. Los ítems de una enumeración hablada duran ~1s cada
uno. Cada estado entra 0.1–0.2s **antes** de su palabra; si entra después se lee
como reacción tardía. Recuerda el offset: escena = `wav + data-start del audio`.

La respiración ambiental debe terminar antes de que empiecen los estados: si no,
pelea con ellos por la propiedad `y`.

## Motion (caricatura, no editorial)

- **Squash & stretch** en cada entrada: la figura llega deformada 1.12/0.9 y
  se asienta en 0.18s.
- **Overshoot** obligatorio: `back.out(1.7)` en entradas, no `power3.out`.
- **Pops discretos**: los elementos aparecen en 2–3 pasos visibles, no en un
  fade continuo. Nada de opacidad animada larga.
- Contornos que se dibujan con `svg-path-draw` a velocidad de pluma.
- **Siempre hay transición entre escenas. Nunca corte seco, nunca crossfade.**
  El estándar es un barrido de tres barras sólidas que suben escalonadas
  (0.1s de diferencia), tapan la pantalla mientras cambia el papel, y siguen de
  largo hacia arriba. Vive en `compositions/wipes.html`, en su propia pista
  encima de las escenas. Los colores de las barras anuncian la escena que entra.
- Respiración ambiental: las formas del fondo nunca quietas, ciclo 8–14s.
