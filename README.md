# Reels generados por completo desde la terminal

Guion, voz, música, efectos, render y mezcla desde la línea de comandos. Nadie
abre Blender, ni un editor de video, ni un DAW. Todo el stack es libre.

Hay **dos motores**: HTML + GSAP (el que se usa por default) y Blender headless.
**Primero GSAP**: en los shorts da mejores resultados (ritmo, texto vivo, cambios de
dirección de cámara con `skills/motion-lab/camera-rig`). Blender, incluido el modo
toon, es experimental: sólo para un objeto que tenga que girar en el espacio de verdad. Comparten guion, voz y mezcla; cambia lo que dibuja
los cuadros. La tabla de cuándo usar cada uno está en
[hooks-reel](./hooks-reel#cuándo-usar-esto-y-cuándo-blender).

<p align="center">
  <img src="harness-reel/docs/preview.gif" width="270" alt="Reel del harness: diagrama trazándose solo, en 9:16">
</p>

<p align="center">
  <em>Trazado con Grease Pencil, voz sintetizada en local, música generada.<br>
  <a href="harness-reel/docs/harness-reel.mp4">Ver con audio (31s)</a></em>
</p>

## Instalar el skill en tu agente

```sh
npx skills add https://blissito.github.io/ghosty-reel
```

Instala `blender-ad`, `motion-anything` y `motion-lab` en Claude Code, Cursor, Codex y el
resto de agentes que leen el formato Agent Skills. El sitio de GitHub Pages sirve `/.well-known/skills/index.json`,
generado desde `skills/` por `scripts/build-well-known.sh` en cada push.

## Cómo funciona (ruta Blender)

Los pasos 1 y 5 son iguales en las dos rutas: el guion manda y la voz fija los
tiempos. Lo que cambia es el medio. Para la ruta HTML, ver
[hooks-reel](./hooks-reel).

**1. Se escribe el guion y se genera la voz.** Kokoro local, sin red. Las
duraciones reales de esos audios son las que fijan todo lo demás.

**2. Esas duraciones se vuelcan a `scene.json`,** que es la dirección completa:
beats, posiciones, cámara. Ningún número vive dentro del script de escena.

**3. El audio se deriva de ahí.** `plan.py` coloca cada efecto en el beat visual
al que responde, no en un segundo escrito a mano. `music.py` sintetiza el bed
desde cero y saca de ahí su duración. Mover un beat realinea todo.

**4. Blender renderiza sin abrirse.** `scene.py` construye la escena, la anima y
saca los frames. `PREVIEW=1` da stills en un segundo para iterar sin esperar.

**5. `mix.sh` mezcla y encodea.** Voz, música y efectos con ffmpeg, pegados a los
frames.

## Las técnicas

### Con Blender

**Capturar la UI.** La interfaz no se modela: Chrome headless la dispara en capas
separadas y Blender las usa como texturas. Ese corte en capas *es* el efecto — si
el botón viviera dentro de la textura de fondo, jamás podría despegarse de ella.

**Trazar con Grease Pencil.** Cuando no hay UI que mostrar sino una idea que
explicar. El diagrama se dibuja en el espacio 3D, la cámara entra entre las capas
y el trazo se dibuja solo. Render mucho más barato.

**Modo caricatura (`"style": "toon"`).** En `scene.json`, `"style": "toon"`
cambia el look al de la marca: emisión plana con el hex exacto (sin luces ni
degradados), contorno de tinta con Line Art (`"outline": "hull"` usa casco
invertido, más barato), sombra dura desplazada en vez del blob radial, y sin
bloom, sin DOF, sin motion blur, view transform Standard. Colores y grosores en
el bloque `"toon"`. El default sigue siendo `"style": "default"` para no romper
reels viejos. Probar sin editar el JSON: `STYLE=toon PREVIEW=1 OUT=/tmp/toon
blender -b -P scene.py`. Para que el contorno se dibuje solo (Line Art + Build):
[`skills/blender-ad/lineart-build.py`](./skills/blender-ad/lineart-build.py).

### Sin Blender

**Componer en HTML.** Para piezas 2D planas —tipografía, diagramas, código en
pantalla, un personaje que actúa— el 3D no aporta y cuesta. La composición es un
documento HTML donde el DOM declara el tiempo con atributos `data-*` y GSAP anima
sobre una línea de tiempo pausada; el renderer la busca cuadro por cuadro. Itera
en segundos y saca 2 minutos en 9:16 en menos de un minuto de render. Lo mueve
[HyperFrames](https://hyperframes.heygen.com).

## Producciones

- **[EasyBits](./EASYBITS.md)** — 16:9, 32s, UI capturada. Blender.
- **[harness-reel](./harness-reel)** — 9:16, 31s, Grease Pencil. Blender.
- **[hooks-reel](./hooks-reel)** — 9:16, 2:10, caricatura plana con personaje y
  código en pantalla. HTML + GSAP.
- **[partitura-reel](./partitura-reel)** — 9:16, 37s, Ghosty Factory. Una partitura mueve la
  animación y el sintetizador; cada objeto toca su nota en el mismo cuadro. HTML + GSAP.
  **La ruta por defecto desde el 24 sep 2026.**
- **HyperFrames 0.8.212 · beats y audio** — 9:16, 33 s. Cinco escenas, una por medida de `beats`/`audio`;
  se ve en [el sitio](https://blissito.github.io/ghosty-reel/#producciones). Música: «Electro Cabello», Kevin MacLeod
  (incompetech.com), CC BY 4.0.
- **[fabrica-reel](./fabrica-reel)**: 9:16, 70 s, con narración. Un pedido real de Ghosty Factory cruza el
  tablero; la voz marca el tiempo y cada efecto cae en la palabra que lo nombra. Estilo oficial de la marca y
  sprites de gpt-image-2. Su README trae las reglas que salieron de los errores.

## HyperFrames 0.8.212 (28-oct-2026)

Probamos lo nuevo con `npx -y hyperframes@0.8.212`, una demo por función.

**Adoptamos**
- `audio --only beats,downbeats,bpm,sections` para medir la música: acertó 112 BPM donde `medir-bgm` dio 75.
- `beats` alimenta a `beat-snap.js`, que se queda para ajustar tiempos a la rejilla; `medir-bgm` sólo rankea por RMS y punch.
- `echo-smear` como estela por default en entradas y salidas rápidas; `smear-dash` queda para el plano heroico.
- `filmed-screen` para demos de producto con UI real, sólo con el parche que agrega `glow`, `grain` y `bg` (es lento).
- `render --format mov --prores-profile 4444` para overlays con alfa.
- `keyframes --shot`, `snapshot --range`, `check --range` y `compare` para revisar un movimiento antes del render.
- `remove-background` para fotos y tomas de personas (no recorta objetos).
- `transcribe --to srt|vtt` sólo para el sidecar de YouTube/TikTok, exportado del JSON ya corregido.

**No adoptamos (o sólo a medias)**
- parakeet: segunda opinión rápida de tiempos; el estándar sigue siendo `-m large-v3 -l es`.
- Mezcla dentro de la composición (`data-fx-chain`, `truepeak`): funciona, pero sin sidechain; la cama se agacha con una curva.
- Shaders WebGPU y motion blur: chocan con la caricatura plana; sólo para piezas que rompen la regla a propósito o fondos de EasyBits.
- `inspect`: alias obsoleto de `check`, no acepta `--range`.

**Bug arreglado:** en ffmpeg 9, `alimiter` trae auto-ganancia (`level=true`) y el short salía a −13.1 LUFS con pico de
+0.1 dBTP. Arreglo: `alimiter=limit=0.84:level=disabled`.

## Stack — todo libre

Blender 5.2 (GPL) · Chrome headless (BSD) · Kokoro-82M (Apache 2.0) · ffmpeg
(LGPL/GPL) · GSAP (licencia estándar, sin costo) · música sintetizada propia o
de Mixkit · SFX de Pixabay.

Sin cuentas, sin API keys, sin servicios. La voz corre local.

## Dónde buscar

| Si quieres… | Ve a |
| --- | --- |
| Entender el pipeline de Blender de punta a punta | [`skills/blender-ad`](./skills/blender-ad) — los gotchas que costaron horas, con un ejemplo que corre solo |
| Copiar una mecánica de motion graphics ya medida (ventana retro, lista inclinada, partículas, malla de barril, cubos isométricos, karaoke por palabra…) | [`skills/motion-lab`](./skills/motion-lab) — 15 recetas HyperFrames + GSAP parametrizadas; galería con previews en [blissito.github.io/ghosty-reel/motion-lab](https://blissito.github.io/ghosty-reel/motion-lab/) |
| Animar texto, entradas o fondos sin escribir el efecto | [`skills/motion-anything`](./skills/motion-anything) — 85 recetas web, 20 de tarjetas y 94 clases CSS (Apache-2.0) |
| Hacer un video 2D con tipografía y personaje | [`hooks-reel`](./hooks-reel) — cómo replicarlo, qué falta generar y por qué |
| Copiar una dirección de arte ya resuelta | [`hooks-reel/frame.md`](./hooks-reel/frame.md) — paleta, tipografía, reglas de composición y motion |
| Que la imagen y la música vayan a la nota, sin alinear a mano | [`partitura-reel`](./partitura-reel) — una partitura, dos salidas (GSAP + sintetizador numpy), verificada cuadro por cuadro |
| Narración + partitura, y las reglas de sonido e imagen que costaron (qué no hacer) | [`fabrica-reel`](./fabrica-reel#lo-que-aprendimos-y-cómo-lo-pagamos) |
| Sincronizar animación con narración | [`hooks-reel/README.md`](./hooks-reel#las-tres-cosas-que-cuesta-descubrir-solo) — medir con `transcribe`, nunca estimar |
| Escribir un guion que el TTS no mastique | [`hooks-reel/SCRIPT.md`](./hooks-reel/SCRIPT.md) — anglicismos escritos fonéticos |

**Nota para agentes:** cada producción trae su propio `README.md` con el estado
real y lo que NO está versionado (audio regenerable, música con licencia que
prohíbe redistribuirla, y las salidas de render). Léelo antes de asumir que el
proyecto corre tal cual sale del clon.

---

Hecho por [blissito](https://github.com/blissito) · [fixter.org](https://fixter.org)
