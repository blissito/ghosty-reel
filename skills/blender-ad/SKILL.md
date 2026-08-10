---
name: blender-ad
description: Genera anuncios y motion graphics 3D con Blender headless, dirigidos por un JSON, capturando la UI real de una app con Chrome headless y componiendo audio (voz Kokoro + música sintetizada + SFX) con ffmpeg. Úsalo cuando pidan un video 3D, un anuncio de producto, un logo reveal, o cuando HyperFrames (HTML→video, 2D) no alcance porque hace falta profundidad, cámara, materiales o elementos que salgan de la pantalla. NO lo uses para video 2D plano — ahí HyperFrames es mejor y más rápido.
---

# Anuncios 3D con Blender headless

Pipeline completo por CLI: nadie abre Blender, ni un editor de video, ni un DAW.
Todo el stack es libre (Blender GPL, Chromium BSD, Kokoro Apache 2.0, ffmpeg).

**Implementación de referencia completa y funcionando: `/Users/bliss/blender-motion/`.**
Empieza copiándola; no reescribas desde cero.

```bash
cp -r /Users/bliss/blender-motion /ruta/nuevo-video
cd /ruta/nuevo-video && rm -rf out audio/vo
```

## La idea central

**La UI no se modela.** Se captura con Chrome headless en capas separadas y
Blender las usa como texturas emisivas sobre planos.

El corte en capas **es** el efecto. Si el botón que debe despegarse viviera
dentro de la textura de fondo, jamás podría salir de ella. Por eso `capture.sh`
saca la página *sin* el botón, y el botón aparte con alpha.

Lo que la cámara va a acercar se captura a 3-4x (`--force-device-scale-factor`);
el fondo a 1x. A 1x, cualquier acercamiento pixela el texto.

## Mapeo píxel → mundo

El plano de la página mide 16×9 unidades y la cámara se encuadra para que calce
exacto en `z=0`:

```python
cam.data.angle = 2 * math.atan((PLANE_W / 2) / CAM_D)

def px_to_world(px, py):
    return (-PLANE_W/2 + px/RES_X * PLANE_W,
             PLANE_H/2 - py/RES_Y * PLANE_H)
```

Así un rect en píxeles del JSON cae donde debe sin ajustar nada a ojo.

**Usa perspectiva, no ortográfica.** Ortográfica es más simple pero los objetos
que vuelan hacia el espectador no crecen y se pierde todo el 3D. Con perspectiva
encuadrada el mapeo sigue siendo exacto en `z=0`, que es donde vive la UI.

## Gotchas de Blender 5 que cuestan horas

**Las fcurves se mudaron a channelbags** (4.4+). `action.fcurves` ya no existe:

```python
def fcurves(id_data):
    act = id_data.animation_data.action
    if hasattr(act, "fcurves"):
        yield from act.fcurves; return
    slot = id_data.animation_data.action_slot
    for layer in act.layers:
        for strip in layer.strips:
            cb = strip.channelbag(slot)
            if cb: yield from cb.fcurves
```

**El compositor se mudó a un node group** (`scene.compositing_node_group`) y los
parámetros del Glare pasaron de propiedades a sockets de entrada (`Type` es un
`NodeSocketMenu` con valor `"Bloom"`). Y lo que más cuesta: **el render NO entra
por la entrada del grupo** — hay que leerlo con un `CompositorNodeRLayers`
DENTRO. Cablearlo desde `NodeGroupInput` deja el socket en su default y **el
video sale en blanco puro**. `CompositorNodeComposite` ya no existe; el destino
es `NodeGroupOutput`.

**Geometría redondeada de verdad.** Si la malla es un rectángulo recto y el
redondeo vive solo en el alpha, el Solidify extruye esquinas cuadradas por debajo
del recorte: muescas visibles en cuanto el objeto gira. Construye el contorno con
arcos reales y UVs planares (`rounded_rect_mesh`).

**Lo que no está en escena tiene que SALIR DEL RENDER, no solo volverse
invisible.** El gotcha más caro de todos. EEVEE compone las superficies BLENDED
en un número limitado de capas por píxel y **descarta el excedente**: los planos
de una escena futura, invisibles a alpha 0 y a ocho segundos de aparecer, se
comen el cupo y tiran la capa de lo que sí debería verse. Se manifiesta como
texto cortado por una línea recta, o parpadeando entre frames.

```python
def only_between(o, a, z):
    for f, hidden in ((1, True), (max(2, int(a) - 1), False), (int(z) + 1, True)):
        o.hide_render = hidden
        o.keyframe_insert("hide_render", frame=f)
    # CONSTANT: un booleano no se interpola
    for fc in fcurves(o):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
```

Aplícalo a **todo** objeto con vida acotada. De paso acelera el render.

**Nada existe antes de su beat, y una fcurve extrapola hacia atrás.** Si la
primera clave de opacidad de un objeto es `1.0` en su nacimiento, el objeto está
visible desde el frame 1. Con escala 0.02 eso son motas blancas repartidas por el
cuadro. Pon siempre una clave a 0 un frame antes.

**Retirarse es fundirse Y alejarse.** Los materiales BLENDED se ordenan por la
distancia del ORIGEN del objeto. Dos planos translúcidos que se solapan en
pantalla casi a la misma Z intercambian orden entre frames y parpadean. Mientras
una escena sale y la siguiente entra coexisten unos frames: si no se separan en
Z, el bug es seguro. Al que sale, aléjalo.

**El canto emisivo sobrevive al fundido de la cara.** Al retirar un objeto con
Solidify, desvanecer la textura deja un contorno flotando. Hay que retraer el
grosor a cero también.

**Emisión pura no recibe sombra.** Una UI emisiva no puede recibir una sombra
real, y sin sombra el objeto que se despega se lee como calcomanía flotante. Se
resuelve con un blob radial oscuro (gradiente esférico + `Mapping` con location
−0.5 para recentrar: `Generated` va 0..1 desde la ESQUINA del bbox).

**Dimensiona contra el ancho VISIBLE a esa profundidad**, no contra 16 unidades.
A `z=2.6` con la cámara a 22.5 el encuadre mide ~12 unidades.

## Audio

Ver `AUDIO.md` de la referencia. Lo esencial:

**Voz — Kokoro local**, Apache 2.0, sin red tras la primera descarga:

```bash
uv venv ~/.venvs/kokoro && VIRTUAL_ENV=~/.venvs/kokoro uv pip install kokoro-onnx soundfile
export HYPERFRAMES_PYTHON=~/.venvs/kokoro/bin/python3
npx hyperframes tts "texto" -v em_santa -l es -s 0.96 -o vo1.wav
```

`em_santa` (español, masculina) **no aparece en `--list`** pero funciona: el CLI
expone un subconjunto curado. Si dice que una voz no existe, inténtala igual.

**Música — sintetízala** (`music.py`). MusicGen y Stable Audio traen pesos con
licencia no comercial, que rompe la premisa OSS. Un bed de 14s es sub + pad +
arpegio: determinista, ~1s en CPU, sin GPU, y es tuyo. Detalles que importan: dos
osciladores desafinados por nota del pad, diente de sierra por suma de armónicos
(una rampa directa aliasea), y el bed agachado bajo la voz desde la síntesis.

**`loudnorm` deja la salida en 192 kHz.** SIEMPRE encadena
`aresample=48000:resampler=soxr` después, y fija `-ar 48000` en el encode. Sin eso
el AAC termina en 96 kHz y cada reproductor remuestrea.

**`amix=normalize=0`.** Por defecto ffmpeg divide entre el número de entradas y la
voz se aplasta cada vez que coincide con un efecto.

**Sesga el audio hacia adelante.** El oído tolera mucho peor el audio tarde que el
adelantado (ITU-R BT.1359: ~125ms vs ~45ms), y el evento visual tiene
anticipación. Un `lead_ms` global de 40-60ms hace que los golpes se sientan
sincronizados.

**Para que la voz domine, baja lo demás**, no subas la voz. Subirla empuja al
limitador y esa compresión es lo que se oye como aspereza.

**Los ducks del bed se DERIVAN del guion, nunca se escriben a mano.** `music.py`
trae una lista `DUCKS` con los tiempos del anuncio para el que se escribió; al
copiar la referencia a otro proyecto esos números sobreviven y el bed se agacha
donde nadie habla, dejando hoyos de 8 dB en mitad del video. Sácalos de las
duraciones reales de la voz:

```python
DUCKS = [(v["at"] - 0.15, v["dur"] + 0.3) for v in _scene["vo"]]
```

**Mide el bed antes de aceptarlo.** El RMS por segundo revela en diez líneas de
numpy lo que oyendo cuesta media hora: dónde está el hoyo, si el gancho abre
flojo, si el final se cae. Grafícalo en la terminal con barras y léelo.

## Texto animado palabra por palabra

Deja que **el navegador mida** dónde cayó cada palabra; no calcules posiciones.
Una capa `?layer=measure` pinta la línea, mide los rects con
`getBoundingClientRect()` y los vuelca a un `<pre>`; `capture.sh` los extrae con
`--dump-dom` a `assets/layout.json`. Calcularlas a mano funciona hasta el primer
cambio de fuente, kerning o `letter-spacing`.

Las palabras cuelgan de un **Empty por línea**: la entrada se anima por palabra
(escalonada, con cabeceo que se endereza), la salida una sola vez sobre el padre.

## Iterar

```bash
PREVIEW=1 blender -b -P scene.py                  # stills al 40%, ~0.5s c/u
PREVIEW=1 FRAMES=460,640 blender -b -P scene.py   # beats puntuales
RANGE=520,960 blender -b -P scene.py              # re-render de un tramo
ONLY=titles,fleet PREVIEW=1 blender -b -P scene.py  # aislar objetos
AUDIO_ONLY=1 ./mix.sh                             # la pista sin esperar el render
```

**Mira los frames que renderizas.** Léelos como imagen y corrige — es lo único que
detecta la sombra descentrada, el anillo que salió disco, o la malla que se
desborda del encuadre.

**Para bugs de composición, bisecciona con `ONLY` y MIDE.** Renderiza el frame
malo con cada grupo de objetos por separado y compara la luminancia de la zona
afectada. Así se encontró que una escena a ocho segundos de distancia cortaba una
palabra del primer acto; a ojo era indistinguible de un problema de z-order.

`RANGE=a,b` importa: arreglar un bug del final de un anuncio de 32s no debería
costar los 960 frames otra vez.

## El audio se deriva de la imagen

`plan.py` lee los beats de `scene.json` y escribe `audio/plan.json`. Los efectos
no llevan segundos escritos a mano sino el beat visual al que responden:

```python
(at("button_pop", 3), "impact-bass-1.mp3", 0.40, "onset", "el botón se despega"),
```

Mover el beat y volver a correr `plan.py` mueve el sonido con él. En un pipeline
donde el render tarda media hora, un desfase por retimeo manual se descubre
demasiado tarde.

## Grease Pencil: diagramas trazados a mano en 3D

Cuando el video es explicativo y el look es de diagrama (estilo Excalidraw), no
captures un diagrama plano para separarlo en capas: **dibújalo con Grease Pencil**.
Los trazos viven en el espacio 3D, así que la cámara puede entrar entre ellos.
Y es barato: 110 frames a 540×960 renderizan en **9 segundos** con EEVEE. Eso
cambia el bucle de iteración por completo frente al render fotorrealista.

Ejemplo mínimo funcionando: `grease-pencil.py` (en esta carpeta). Corre solo.

**API de Blender 5.2 (GPv3).** Crear trazos por código:

```python
gp = bpy.data.grease_pencils.new(name)
ob = bpy.data.objects.new(name, gp); scene.collection.objects.link(ob)
mat = bpy.data.materials.new(name); bpy.data.materials.create_gpencil_data(mat)
mat.grease_pencil.color = (*rgb, 1.0)
gp.materials.append(mat)
lay = gp.layers.new("L")
lay.use_lights = False                 # sin esto los colores salen apagados
d = lay.frames.new(1).drawing
d.add_strokes([len(pts)])              # una entrada por trazo
st = d.strokes[0]
for i, p in enumerate(pts):
    st.points[i].position = p          # (x, y, z) en mundo, local al objeto
    st.points[i].radius = 0.03
    st.points[i].opacity = 1.0
```

**El trazo que se dibuja solo** es el modificador Build. NO uses `frame_start`/
`frame_end`: activa `use_percentage` y keyframea `percentage_factor`, así el
dibujo se ata al beat del JSON igual que todo lo demás.

```python
bd = ob.modifiers.new("build", 'GREASE_PENCIL_BUILD')
bd.use_percentage = True
for f, v in ((a-1, 0.0), (a, 0.0), (b, 1.0)):
    bd.percentage_factor = v
    bd.keyframe_insert("percentage_factor", frame=f)
```

**Build deja el frame 1 vacío.** Si renderizas un still en el frame 1 para revisar
la escena, sale negro puro y parece que nada funcionó. No es eso: aún no dibuja.
Revisa en un frame tardío o bisecciona quitando el modificador.

**`cyclic = True` + Build dibuja una cuerda** atravesando la figura mientras el
trazo está incompleto — el modificador interpola el segmento de cierre desde el
primer frame. Cierra el contorno **repitiendo el primer punto al final** y deja
`cyclic = False`.

**El temblor manuscrito es el modificador Noise.** `factor=0.6`, `noise_scale=0.35`,
`factor_thickness=0.5` da un trazo creíble sin verse sucio. El atributo del semilla
es `seed`, **no** `random_seed`.

**Texto que se escribe solo**: objeto FONT → convertir → Build encima.

```python
cu = bpy.data.curves.new("txt", 'FONT'); cu.body = "harness"
ob = bpy.data.objects.new("t", cu); scene.collection.objects.link(ob)
ob.rotation_euler = (math.pi/2, 0, 0)          # el texto nace en el plano XY
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.object.convert(target='GREASEPENCIL')  # el enum NO lleva guion bajo
```

**El texto convertido usa material de RELLENO, no de trazo.** Pintar solo
`grease_pencil.color` lo deja negro sobre fondo oscuro: invisible. Hay que fijar
también `grease_pencil.fill_color`.

**`Lineart`** (`GREASE_PENCIL_LINEART`) genera trazos desde la geometría de otros
objetos — es el reemplazo moderno de Freestyle y la vía para que un volumen 3D
real se vea dibujado a mano. Sin verificar todavía.

## Formato vertical (9:16)

**`cam.data.angle` aplica a la dimensión MAYOR del render**, que en vertical es la
ALTURA, no el ancho. El mapeo píxel→mundo de más arriba está escrito para 16:9 y
**se rompe en silencio** al pasar a 9:16: los objetos se desbordan del encuadre
sin ningún error. Fija el ajuste explícitamente:

```python
cam.data.sensor_fit = 'HORIZONTAL'
cam.data.angle = 2 * math.atan((PLANE_W / 2) / CAM_D)
```

**Todo lo que no esté en `y = 0` hay que corregirlo por profundidad, incluido el
texto — y sobre todo el texto que está MÁS CERCA que el plano de referencia.** Un
título en `y = -3.2` con la cámara a 16 se magnifica 1.25× y se sale del cuadro
por arriba sin que nada avise. Y si la cámara se mueve durante el video, cada
beat tiene su propio factor de encuadre. Trabaja siempre en coordenadas
APARENTES y deja que una sola función traduzca:

```python
def place(size, loc, cam_d_en_ese_beat):
    y = loc[1]
    k = (cam_d_en_ese_beat / CAM_D) * (CAM_D + y) / CAM_D
    return size * k, (loc[0] * k, y, loc[2] * k)
```

Escribir las posiciones "a ojo" funciona hasta que mueves la cámara; entonces se
rompen todas a la vez y no es obvio por qué.

## Salida de video

El Blender de homebrew **viene sin soporte FFMPEG**: `image_settings.file_format`
no ofrece `'FFMPEG'` y asignarlo revienta. Da igual — el pipeline ya renderiza
secuencia PNG y encodea con el `ffmpeg` del sistema (`encode.sh`). No pierdas
tiempo buscando por qué falta el enum.

Nota: el motor se llama `'BLENDER_EEVEE'`, no `'BLENDER_EEVEE_NEXT'`.

## Guion para vertical: la estructura antes que el render

Un reel no se salva en la edición. Antes de tocar Blender, decide la estructura.
Las cinco que usa la comunidad: Problema-Solución, Mini Hero's Journey,
Before-After-Bridge, **Open Loop** y micro-payoffs apilados.

**Open Loop es la que mejor le sienta a un explicativo técnico**: planteas una
tensión en el segundo cero y no la resuelves hasta el final. Si el tema tiene un
dato contraintuitivo, ya tienes el loop gratis — no lo cuentes como contexto,
suéltalo como pregunta.

Reglas duras:

- **Los primeros 3 segundos deciden todo.** El error típico es abrir explicando
  de dónde sale el dato. Eso es setup. El gancho va primero y el contexto después.
- **70–110 palabras** para 30s, y **un solo mensaje central**. Más ideas no
  informan más: diluyen.
- **Un micro-payoff cada 8-10s.** En un explicativo, cada elemento que aparece es
  uno.
- **Genera la voz ANTES de armar la escena** y saca los beats de sus duraciones
  reales. Escribir los tiempos primero y grabar después garantiza retimear todo.
  Kokoro da ~4 palabras/segundo en español; 85 palabras ≈ 28s de habla, y las
  pausas entre líneas suman 2s más.

## Música: qué cambia en vertical

- **120–150 BPM.** Los cortes rápidos del formato piden tempo.
- **El groove entra en t=0.** El error #1 es tratar el vertical como horizontal
  reformateado: intro ambiental, fade gradual, o una pista que tarda en llegar al
  ritmo. `music.py` trae `ARP_IN = 4.2` — para un reel eso deja el gancho, la
  parte que decide si te quedas, como lo MÁS CALLADO de la pista. Ponlo en 0 y
  acorta el ataque del fade global a ~0.15s.
- **Menor para la tensión, resolución brillante en el CTA.** Am-F-C-G ya lo hace;
  el turno a C-G es el que levanta.
- Sintes punchy leen como moderno y digital, que es lo correcto para motion
  graphics de producto.

## Dónde NO usar esto

Video 2D plano (títulos, captions, slideshows, explainers sin profundidad):
**usa HyperFrames**, es más rápido y el resultado es mejor. Blender entra cuando
hace falta profundidad real, cámara, materiales, o que algo salga de la pantalla.

## Correr en un servidor sin GPU

**EEVEE necesita GPU.** En bare metal sin GPU hay dos caminos: Cycles en CPU
(funciona headless sin nada extra, mucho más lento) o EEVEE sobre **lavapipe**
(Vulkan por software, Mesa) — que mantiene el motor rápido pero **está sin
verificar**. Ese benchmark decide si esto puede ser un servicio; hazlo antes de
prometer nada.
