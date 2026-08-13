# Reels generados por completo desde la terminal

Guion, voz, música, efectos, render y mezcla desde la línea de comandos. Nadie
abre Blender, ni un editor de video, ni un DAW. Todo el stack es libre.

Hay **dos motores** según lo que haya que contar: Blender headless para 3D, y
HTML + GSAP para 2D plano. Comparten guion, voz y mezcla; cambia lo que dibuja
los cuadros. La tabla de cuándo usar cada uno está en
[hooks-reel](./hooks-reel#cuándo-usar-esto-y-cuándo-blender).

<p align="center">
  <img src="harness-reel/docs/preview.gif" width="270" alt="Reel del harness: diagrama trazándose solo, en 9:16">
</p>

<p align="center">
  <em>Trazado con Grease Pencil, voz sintetizada en local, música generada.<br>
  <a href="harness-reel/docs/harness-reel.mp4">Ver con audio (31s)</a></em>
</p>

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

## Stack — todo libre

Blender 5.2 (GPL) · Chrome headless (BSD) · Kokoro-82M (Apache 2.0) · ffmpeg
(LGPL/GPL) · GSAP (licencia estándar, sin costo) · música sintetizada propia o
de Mixkit · SFX de Pixabay.

Sin cuentas, sin API keys, sin servicios. La voz corre local.

## Dónde buscar

| Si quieres… | Ve a |
| --- | --- |
| Entender el pipeline de Blender de punta a punta | [`skills/blender-ad`](./skills/blender-ad) — los gotchas que costaron horas, con un ejemplo que corre solo |
| Hacer un video 2D con tipografía y personaje | [`hooks-reel`](./hooks-reel) — cómo replicarlo, qué falta generar y por qué |
| Copiar una dirección de arte ya resuelta | [`hooks-reel/frame.md`](./hooks-reel/frame.md) — paleta, tipografía, reglas de composición y motion |
| Sincronizar animación con narración | [`hooks-reel/README.md`](./hooks-reel#las-tres-cosas-que-cuesta-descubrir-solo) — medir con `transcribe`, nunca estimar |
| Escribir un guion que el TTS no mastique | [`hooks-reel/SCRIPT.md`](./hooks-reel/SCRIPT.md) — anglicismos escritos fonéticos |

**Nota para agentes:** cada producción trae su propio `README.md` con el estado
real y lo que NO está versionado (audio regenerable, música con licencia que
prohíbe redistribuirla, y las salidas de render). Léelo antes de asumir que el
proyecto corre tal cual sale del clon.

---

Hecho por [blissito](https://github.com/blissito) · [fixter.org](https://fixter.org)
