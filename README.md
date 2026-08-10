# Reels generados por completo desde la terminal

Sistema para producir video promocional con Blender headless: guion, voz, música,
efectos, render y mezcla. Nadie abre Blender, ni un editor de video, ni un DAW.
Todo el stack es libre.

## Producciones

| | formato | técnica | render |
|---|---|---|---|
| **EasyBits** (raíz) | 16:9 · 32s | UI real capturada con Chrome, en capas | ~35 min |
| **[harness-reel](./harness-reel)** | 9:16 · 31s | diagrama trazado con Grease Pencil | ~2.7 min |

EasyBits vive en la raíz por histórico: fue la primera y de ahí salió el motor.
Las nuevas producciones van en su propia carpeta.

## El motor

Lo que comparten las dos, y lo que hay que entender antes de tocar nada:

**`scene.json` es la dirección completa.** Ningún número vive hardcodeado en el
script de escena: beats, rects, cámara, coreografía. Cambiar de anuncio es
cambiar el JSON.

**El audio se deriva de la imagen.** `plan.py` lee los beats de `scene.json` y
escribe `audio/plan.json`: los efectos no llevan segundos escritos a mano sino el
beat visual al que responden (`at("button_pop", 3)`). Mover un beat y volver a
correr `plan.py` mueve el sonido con él. `music.py` sintetiza el bed desde cero
—sin modelos, sin catálogo, sin licencia— y saca de ahí su duración y sus ducks.
Detalle en **[AUDIO.md](./AUDIO.md)**.

**El loop de iteración es de segundos, no de minutos.** `PREVIEW=1` saca stills
al 40%, `FRAMES=a,b` va a beats puntuales, `RANGE=a,b` re-renderiza un tramo y
`AUDIO_ONLY=1 ./mix.sh` juzga la pista sin esperar el render. Eso es lo que hace
viable dirigir esto desde un agente.

**Los gotchas están documentados.** [`skills/blender-ad`](./skills/blender-ad)
recoge lo que costó horas descubrir: las fcurves mudadas a channelbags, el
compositor de Blender 5, por qué Grease Pencil se dibuja siempre encima de las
mallas, por qué AgX apaga una paleta plana, el mapeo píxel→mundo en vertical.
Trae `grease-pencil.py`, un ejemplo mínimo que corre solo.

## Dos técnicas, dos usos

**Capturar la UI** (EasyBits). La interfaz no se modela: `capture.sh` la dispara
con Chrome headless **en capas separadas** y Blender las usa como texturas
emisivas. Ese corte en capas *es* el efecto — si el botón viviera dentro de la
textura de fondo, jamás podría despegarse de ella. Lo que la cámara va a acercar
se captura a 3-4x; el fondo a 1x.

**Trazar con Grease Pencil** (harness-reel). Cuando no hay UI que mostrar sino
una idea que explicar, el diagrama se dibuja en el espacio 3D y la cámara entra
entre las capas. El modificador Build hace que el trazo se dibuje solo, y el
texto convertido a Grease Pencil se escribe solo. Render mucho más barato.

En ambos casos, **perspectiva y no ortográfica**: el mapeo sigue siendo exacto en
`z=0` y los objetos que vuelan hacia el espectador sí crecen.

## Correr EasyBits

```bash
./capture.sh                      # UI real -> assets/*.png + layout.json
python3 plan.py                   # beats -> audio/plan.json
python3 music.py audio/bgm.wav    # música sintetizada
blender -b -P scene.py            # render -> out/frames
./mix.sh                          # audio + frames -> out/ad.mp4
```

`blender` = `/Applications/Blender.app/Contents/MacOS/Blender`.

Los seis actos: problema (0–4.5s), producto (4.5–12), el agente (12.9–18.6), la
flota (18.5–24.3), compartir (24.2–29.9), marca (29.9–32). La escena del agente
es la que **explica** —las tools se leen textuales, no como iconos— y las otras
muestran.

## Stack — todo libre

| Pieza | Herramienta | Licencia |
|---|---|---|
| Render 3D | Blender 5.2 | GPL |
| Captura de UI | Chrome headless (intercambiable por Chromium) | BSD |
| Voz | Kokoro-82M vía `hyperframes tts` | Apache 2.0 |
| Música | `music.py`, síntesis propia | nuestra |
| SFX | Pixabay Content License | royalty-free, sin atribución |
| Mezcla y encode | ffmpeg | LGPL/GPL |

Sin cuentas, sin API keys, sin servicios. La única pieza no-OSI son los seis SFX,
sintetizables con el mismo enfoque de `music.py` si hiciera falta pureza estricta.

## Siguiente

- **Benchmark de lavapipe.** EEVEE necesita GPU; las microVMs del KS-5 son CPU
  pura. Vulkan por software (Mesa lavapipe) es lo que decide si esto puede correr
  como servicio. Sin ese número, todo lo demás es especulación.
- Servicio: `POST {screenshot, rect, guion, paleta}` → MP4, en Firecracker, con
  job asíncrono y webhook — el render son minutos, no puede ser síncrono.

---

Hecho por [blissito](https://github.com/blissito) · [fixter.org](https://fixter.org)
