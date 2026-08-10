# harness-reel

Reel vertical 9:16 (31s) sobre la anatomía de un agente, para el Taller Sistemas
Agénticos. El diagrama no se captura de ninguna UI: se traza con Grease Pencil,
así que la cámara entra entre las capas en vez de verlas apiladas.

```bash
./build.sh      # voz -> beats -> música -> render -> mezcla -> out/ad.mp4
```

## Arquitectura

**`scene.json` manda.** Los beats están en segundos y salen de las duraciones
reales de la voz. `plan.py` deriva de ahí los SFX y `music.py` los ducks del bed.
Mover un beat y volver a correr `build.sh` realinea todo; ningún tiempo se
escribe a mano dos veces.

**El render son dos pasadas.** EEVEE dibuja los trazos de Grease Pencil siempre
encima de las mallas, sin importar `stroke_depth_order` ni el método de
transparencia. Para que Ghosty vuele por delante hay que separarlo y componer:

```bash
ONLY=ghosty blender -b -P scene.py    # out/ghosty/  (RGBA, fondo transparente)
blender -b -P scene.py                # out/frames/  (base)
```

`mix.sh` las une con `overlay` de ffmpeg.

**`lines.txt` es para el motor de voz, no para pantalla.** Los anglicismos van
fonéticos (`tools` → `tuls`) porque Kokoro les aplica reglas del español. El
texto visible vive en `scene.py`.

**8 muestras, sin sombras ni GI.** El default de EEVEE (64 muestras + sombras +
GI) está pensado para render 3D con luces. Esta escena no tiene una sola luz:
todo es emisión plana, así que ese trabajo se tira. Quitarlo da **3.5×** con una
diferencia de imagen de 0.004/255 — imperceptible. `SPP=64 SLOW=1` lo revierte.

| | s/frame | 930 frames |
|---|---|---|
| 64 spp + sombras + GI | 0.600 | 9.3 min |
| 8 spp sin sombras/GI | 0.173 | 2.7 min |

**`view_transform = 'Standard'`.** AgX desatura la paleta y agrisa el blanco. Si
algo se ve lavado, empieza por ahí.

## Iterar

```bash
PREVIEW=1 blender -b -P scene.py                 # stills al 40% en cada beat
PREVIEW=1 FRAMES=118,470,880 blender -b -P scene.py
RANGE=588,930 blender -b -P scene.py             # re-render de un tramo
AUDIO_ONLY=1 ./mix.sh                            # la pista sin esperar el render
```

Los gotchas del pipeline están en `../skills/blender-ad/SKILL.md`.

---

Hecho por [blissito](https://github.com/blissito) · [fixter.org](https://fixter.org)
