# EasyBits — anuncio 3D generado por completo desde CLI

Motion graphics de producto en Blender headless, con voz, música y efectos.
Nadie abre Blender, ni un editor de video, ni un DAW. Todo se genera y se
renderiza desde la terminal, y todo el stack es libre.

## Correr

```bash
./capture.sh                             # UI real -> assets/*.png
python3 music.py audio/bgm.wav           # música sintetizada
blender -b -P scene.py                   # render -> out/frames  (~15 min)
./mix.sh                                 # audio + frames -> out/ad.mp4

PREVIEW=1 blender -b -P scene.py         # stills baratos (~0.5s c/u)
PREVIEW=1 FRAMES=200,325 blender -b -P scene.py
AUDIO_ONLY=1 ./mix.sh                    # solo la pista, sin esperar el render
```

`blender` = `/Applications/Blender.app/Contents/MacOS/Blender`.

## El anuncio

| Acto | Segundos | Qué pasa |
|---|---|---|
| Problema | 0–3.5 | *"Tus agentes generan archivos." / "¿Dónde los guardas?"* Los títulos aceleran contra la cámara y la atraviesan — esa es la transición, no hay corte. |
| Producto | 3.5–11 | Entra la UI real. El cursor 3D vuela y hace clic. El botón se despega de la pantalla, gana grosor, y del impacto salen archivos 3D que se ordenan solos en una malla. |
| Marca | 11–14 | Los archivos se apartan y entra el cierre: logo, *Almacenamiento para agentes*, `easybits.cloud`. |

## Cómo funciona

**La UI no se modela.** `capture.sh` la dispara con Chrome headless en capas
separadas y Blender las usa como texturas emisivas:

| capa | qué es | por qué separada |
|---|---|---|
| `page.png` | la app **sin** el botón | fondo, nunca se acerca → 1x |
| `button.png` | solo el botón, con alpha | es su propio objeto: por eso puede salir de la pantalla → 4x |
| `t1/t2.png` | los títulos | planos 3D que atraviesan la cámara → 2x |
| `card0..7.png` | tarjetas de archivo | se instancian 20 veces en 3D → 3x |
| `end.png` | el cierre de marca | → 2x |

Ese corte en capas **es** el efecto. Si el botón viviera dentro de la textura de
fondo, jamás podría despegarse de ella.

**El mapeo píxel → mundo es exacto.** El plano de la página mide 16×9 unidades y
la cámara se encuadra para que calce justo a `z=0`. Un rect en píxeles de
`scene.json` cae donde debe sin ajustar nada a ojo.

**Perspectiva, no ortográfica.** Ortográfica sería más simple, pero entonces los
objetos que vuelan hacia el espectador no crecerían y todo el 3D se perdería. Con
perspectiva encuadrada, el mapeo sigue siendo exacto en `z=0` — que es donde vive
la UI — y las tarjetas ganan profundidad real.

**`scene.json` es la dirección completa.** `scene.py` no tiene números
hardcodeados: rect del botón, curva del cursor, beats, malla de archivos, cámara.
Cambiar de demo es cambiar el JSON y recapturar.

Para el audio, ver **[AUDIO.md](./AUDIO.md)**.

## Decisiones que cuestan si se ignoran

**Geometría redondeada de verdad.** Si la malla es un rectángulo recto y el
redondeo vive solo en el alpha, el Solidify extruye esquinas cuadradas por debajo
del recorte: se ven como muescas en cuanto el objeto gira. `rounded_rect_mesh`
construye el contorno real con UVs planares.

**La sombra es falsa a propósito.** La página es emisión pura: no recibe luz, así
que no puede recibir una sombra real. Sin el blob radial de `build_shadow` el
botón se lee como calcomanía flotante.

**Nada existe antes de su beat.** Una fcurve extrapola su primer valor hacia
atrás, así que el botón y el cursor aparecían flotando sobre los títulos del
primer acto. Se apagan explícitamente hasta que les toca entrar.

**El canto emisivo sobrevive al fundido de la cara.** Al retirar el botón quedaba
un contorno morado sobre la marca; hay que retraer el grosor del Solidify a cero,
no solo desvanecer la textura.

**La malla de archivos se calcula contra el ancho visible a su profundidad**, no
contra 16 unidades. A `z=2.6` con la cámara a 22.5 el encuadre mide ~12 unidades;
dimensionarla a 16 la desborda.

**El bloom vive en el compositor, y en Blender 5 se mudó otra vez.** El árbol pasó
a ser un node group y los parámetros del Glare pasaron de propiedades a sockets.
Además el render **no** entra por la entrada del grupo: hay que leerlo con un
Render Layers dentro. Cablearlo desde `NodeGroupInput` deja el socket en su valor
por defecto y el video sale en blanco puro.

**Las fcurves se mudaron a channelbags** en Blender 4.4+. El helper `fcurves()`
sirve a ambas APIs para no atar el script a una versión.

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
y son sintetizables con el mismo enfoque de `music.py` si hiciera falta pureza
estricta.

## Rendimiento

EEVEE Next, 1920×1080, 30fps, 14s (420 frames): **~15 min** en un Mac con GPU.
Preview al 40%: ~0.5s por frame — el loop de iteración es de segundos, que es lo
que hace viable dirigir esto desde un agente. La música tarda 1.2s en CPU.

## Siguiente

- **Benchmark de lavapipe.** EEVEE necesita GPU; las microVMs del KS-5 son CPU
  pura. Vulkan por software (Mesa lavapipe) es lo que decide si esto puede correr
  como servicio. Sin ese número, todo lo demás es especulación.
- Escena 2 encadenada desde el cierre.
- Servicio: `POST {screenshot, rect, guion, paleta}` → MP4, en Firecracker, con
  job asíncrono y webhook (el render son minutos, no puede ser síncrono como las
  cajas de voz y render que ya existen).
