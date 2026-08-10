# EasyBits — 16:9, 32s

Anuncio de producto con la UI real capturada. Vive en la raíz del repo porque
fue la primera producción y de ahí salió el motor.

```bash
./capture.sh                      # UI real -> assets/*.png + layout.json
python3 plan.py                   # beats -> audio/plan.json
python3 music.py audio/bgm.wav    # música sintetizada
blender -b -P scene.py            # render -> out/frames  (~35 min)
./mix.sh                          # audio + frames -> out/ad.mp4
```

`blender` = `/Applications/Blender.app/Contents/MacOS/Blender`.

## Los seis actos

| Acto | Segundos | Qué pasa |
|---|---|---|
| Problema | 0–4.5 | Cada palabra entra escalonada; después la línea acelera contra la cámara y la atraviesa. Esa es la transición, no hay corte. |
| Producto | 4.5–12 | Entra la UI real. El cursor 3D vuela y hace clic. El botón se despega de la pantalla, gana grosor, y del impacto salen archivos que se ordenan solos. |
| El agente | 12.9–18.6 | Llama `upload_file()`, `search_documents()`, `create_share_link()` y de cada llamada sale un archivo. Es la escena que **explica**; por eso las tools se leen textuales, no como iconos. |
| La flota | 18.5–24.3 | Tres canales emitiendo archivos que convergen al **mismo** punto. La convergencia es el mensaje. |
| Compartir | 24.2–29.9 | Un link aparece, se sostiene lo suficiente para leerse, y se replica. |
| Marca | 29.9–32 | Todo se aparta y entra el cierre. |

## Las capas de captura

La UI no se modela. `capture.sh` la dispara con Chrome headless en capas
separadas y Blender las usa como texturas emisivas. Lo que la cámara va a
acercar se captura a 3-4x; el fondo a 1x.

| capa | qué es |
|---|---|
| `page.png` | la app **sin** el botón (fondo, 1x) |
| `button.png` | solo el botón, con alpha — por eso puede salir de la pantalla |
| `w0_*.png` | **cada palabra** de los títulos, para animarlas escalonadas |
| `card0..7.png` | tarjetas de archivo, instanciadas 20 veces en 3D |
| `agent/tool*/chan*/share/end.png` | paneles de las escenas 3-6 |

Las posiciones de las palabras **las mide el navegador**: `capture.sh` corre
Chrome con `--dump-dom` sobre una capa que vuelca los rects a
`assets/layout.json`. Calcularlas a mano funciona hasta el primer cambio de
fuente o kerning.

Rendimiento: EEVEE, 1920×1080, 30fps, 960 frames, **~35 min** en un Mac con GPU.
