# Audio — cómo se generó, y por qué así

Todo el audio de este anuncio se produce en la máquina, sin servicios ni cuentas.
Es el requisito que manda: el objetivo es un pipeline que pueda correr dentro de
un microVM sin credenciales de nadie.

```bash
python3 music.py audio/bgm.wav   # música
./mix.sh                         # voz + SFX + música -> out/ad.mp4
AUDIO_ONLY=1 ./mix.sh            # solo audio/mix.wav, para juzgar la pista
```

## Las tres fuentes

| Pieza | Cómo se hace | Licencia |
|---|---|---|
| Voz | Kokoro-82M local vía `hyperframes tts` | Apache 2.0 (modelo y código) |
| Música | `music.py`, síntesis propia | nuestra, sin dependencias |
| SFX | 6 archivos de Pixabay, vendorizados en `audio/sfx/` | Pixabay Content License |

Solo los SFX vienen de fuera. La Pixabay Content License permite uso comercial,
modificación y redistribución sin atribución — no es OSI, pero no impone ninguna
restricción sobre el pipeline ni sobre el video. Si hiciera falta pureza OSI
estricta, los seis son sintetizables con el mismo enfoque de `music.py`
(`audio/sfx/CREDITS.md` lo detalla).

## Voz

```bash
npx hyperframes tts "Tus agentes generan archivos." -v em_santa -l es -s 0.96 -o audio/vo/vo1.wav
```

Kokoro corre on-device, sin red después de la primera descarga de pesos (~27 MB).
Con `-l es` el fonemizador aplica las reglas correctas y los signos de apertura
(`¿`) se leen bien.

**`em_santa` no aparece en `--list`, pero funciona.** El CLI expone un subconjunto
curado (en español solo lista `ef_dora`), mientras que `tools/call` acepta
cualquier voz del set de Kokoro. Si el CLI dice que una voz no existe, conviene
intentarla igual antes de descartarla.

**Gotcha:** el CLI no trae `kokoro-onnx`. Sin él falla con un mensaje claro pero
no lo instala solo. Hay que crear un venv y apuntarlo:

```bash
uv venv ~/.venvs/kokoro && VIRTUAL_ENV=~/.venvs/kokoro uv pip install kokoro-onnx soundfile
export HYPERFRAMES_PYTHON=~/.venvs/kokoro/bin/python3
```

Las cuatro líneas están en `audio/plan.json` con su texto, así que el guion se
lee sin abrir los WAV.

## Música — `music.py`

**Por qué no un modelo generativo.** MusicGen y Stable Audio Open traen pesos con
licencia no comercial o restringida, que es exactamente lo que rompe la premisa.
Además pesan gigas y quieren GPU — mal encaje para una caja efímera.

**Por qué sintetizar alcanza.** Un bed de anuncio de 14 segundos no necesita un
modelo: es una progresión corta con sub, pad y arpegio. Escribirlo es
determinista (mismo archivo byte a byte en cualquier máquina), tarda ~1.2s en
CPU, no depende de nada y el resultado es nuestro.

La estructura sigue los actos de `scene.json`, no un loop genérico:

| Tiempo | Qué suena | Qué pasa en pantalla |
|---|---|---|
| 0–3.2s | sub + pad, agachados bajo la voz | los títulos del problema |
| 3.2s | entra el arpegio | aparece la UI |
| 4.0s | entran los ticks de aire | el cursor vuela |
| 6–10.3s | todo abierto, el filtro se abre solo | clic, botón, archivos |
| 10.3s | swell | los archivos se apartan |
| 11.8s | acorde final Am sostenido | entra la marca |

Decisiones que importan y no son obvias:

**Am–F–C–G.** Sobrio sin sonar triste, y resuelve sin quedar en jingle.

**Dos osciladores desafinados por nota del pad** (`f` y `f * 1.004`). Ese batido
es la diferencia entre un pad y un sintetizador de juguete.

**El diente de sierra se suma por armónicos**, no se genera como rampa. Una rampa
directa produce aliasing audible en las notas altas del arpegio.

**El filtro del arpegio se abre con el tiempo** (`clip((T-3)/6)`). Sube la energía
percibida sin subir el volumen, que es lo que deja espacio a la voz.

**El bed se agacha solo** bajo las dos primeras líneas (`duck`). Hacerlo en la
síntesis y no en la mezcla significa que el `loudnorm` final no tiene que pelear.

**El estéreo es un `np.roll` de 90 muestras** (~2ms) en el canal derecho. Ancho
sutil por retardo; suficiente para que no suene mono, sin romper la suma a mono.

## Mezcla — `plan.py` → `audio/plan.json` → `mix.sh`

`plan.json` **se genera**, no se edita. `plan.py` lo escribe leyendo los beats de
`scene.json`, así que un efecto no lleva su segundo a mano sino el momento visual
al que responde:

```python
(at("button_pop", 3), "impact-bass-1.mp3", 0.40, "onset", "el botón se despega"),
```

Mover `button_pop` en `scene.json` y volver a correr `plan.py` mueve el impacto
con él. Escribir los segundos a mano garantiza que imagen y audio se separen en
cuanto se retoca la edición — y en un pipeline donde el render tarda media hora,
ese desfase se descubre tarde. `music.py` toma su duración del mismo sitio.

`mix.sh` compila el plan a un grafo de ffmpeg.

Dos detalles del grafo que cuestan si se ignoran:

**`adelay` por pista.** Sin él todas las entradas arrancan en cero y el audio se
despega de la imagen. Es lo que coloca cada golpe en su beat.

**`amix=normalize=0`.** Por defecto ffmpeg divide entre el número de entradas, así
que la voz se aplastaría cada vez que coincide con un efecto. Con `normalize=0`
las ganancias de `plan.json` son las que mandan, y `alimiter` cuida el techo.

Salida normalizada a **−16 LUFS / −1.5 dBTP** (`loudnorm`), que es el estándar de
web y redes. Si el destino fuera broadcast serían −23 LUFS.

**La voz manda, y se consigue bajando lo demás.** Para que la locución domine sin
volverse estridente, los efectos se atenúan (0.20–0.46) y el bed se queda en 0.14;
la voz nunca pasa de 1.0. Subir la voz en vez de bajar el resto empuja al
`alimiter`, y esa compresión es exactamente lo que se oye como aspereza. El bed
además se agacha solo bajo las cuatro líneas desde la síntesis (`duck` en
`music.py`, con piso en 0.25 para que no desaparezca).

Los SFX que falten se saltan con aviso en vez de reventar la corrida — así se
puede mezclar antes de tener todos los assets.

## Sincronía — dos problemas distintos

Cuando el audio "se siente atrás" hay que separar el bug técnico del ajuste
perceptual. Son cosas diferentes y se arreglan por separado.

### 1. El bug: `loudnorm` deja la salida en 192 kHz

Este es el que de verdad rompía. `loudnorm` remuestrea internamente a 192 kHz
para su análisis y **no vuelve a bajar** si no se le pide. El WAV salía a 192 kHz
y el encoder AAC lo llevaba a 96 kHz — un modo raro que obliga a cada reproductor
a remuestrear en tiempo real. Se ve así:

```bash
ffprobe -v error -show_entries stream=sample_rate -of csv=p=0 audio/mix.wav
# 192000   <- mal
```

Fix, y es la práctica estándar de la comunidad: **siempre encadenar un
`aresample` después de `loudnorm`**, y fijar `-ar` en el encode.

```
... loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000:resampler=soxr,aformat=sample_fmts=s16
```

El otro sospechoso clásico es el **priming del AAC**: el encoder nativo de ffmpeg
mete 1024 muestras de silencio al frente (~21 ms), FDK-AAC hasta 2048. En MP4 eso
se declara con una edit list; si el muxer no la escribe, el audio arranca tarde.
Se verifica con `ffprobe -show_entries stream=start_time,initial_padding` — aquí
ambos streams dan `start_time=0`, así que no era el problema, pero es lo primero
que hay que descartar en otro pipeline.

### 2. El culpable de verdad: los archivos traen silencio al frente

Lo que más desalineaba, y lo menos evidente. Un `.mp3` de librería no empieza a
sonar en el byte cero:

```
whoosh-cinematic.mp3   2055 ms de rampa antes del golpe
riser.mp3              2089 ms
chime.mp3               416 ms
click.mp3                48 ms
```

Colocar el whoosh "en el segundo 2.55" lo hacía sonar en el **4.6**. Dos segundos
tarde, en el efecto más audible del anuncio.

El fix es alinear por el punto que el oído reconoce como *el sonido*, no por el
inicio del archivo. `mix.sh` lo mide con ffmpeg + una envolvente suavizada y lo
resta del `at`:

| modo | qué busca | para qué |
|---|---|---|
| `onset` | primer punto con 20% del pico | golpes: clic, impacto, chime |
| `peak` | el máximo de la envolvente | swells: whoosh, riser, que culminan en el corte |

```json
{ "at": 3.05, "file": "whoosh-cinematic.mp3", "align": "peak" }
```

Con esto, `at` significa **el instante en que el sonido debe oírse**, que es como
se piensa el timing, y no cuándo arranca un archivo. Medido sobre el MP4 final,
los seis efectos caen dentro de ±42 ms de su objetivo.

Verificación (vale la pena automatizarla si el pipeline se vuelve servicio):

```bash
ffmpeg -i out/ad.mp4 -vn -ar 48000 -ac 1 /tmp/a.wav
# buscar el máximo de la envolvente en una ventana de ±45ms alrededor de cada cue
```

Ojo al medir: si dos efectos caen a menos de ~200 ms uno del otro, una ventana
ancha encuentra el vecino más fuerte y reporta un error que no existe.

### 3. El ajuste: el sonido va ADELANTE del golpe visual

Aun con sincronía perfecta al frame, un impacto se siente tarde. Dos razones:

El oído tolera muchísimo peor el audio tarde que el audio adelantado —
[ITU-R BT.1359](https://www.itu.int/rec/R-REC-BT.1359) sitúa el umbral en ~125 ms
tarde contra ~45 ms adelantado. El error, si lo hay, conviene que caiga del lado
temprano.

Y el evento visual tiene anticipación: el cursor ya va bajando cuando "toca". La
práctica de sound design en motion graphics es
[colocar la capa transitoria justo antes del pico visual](https://sfxengine.com/blog/animated-sound-effects)
para que el golpe se perciba sincronizado y con más pegada.

Por eso `plan.json` tiene un `lead_ms` global:

```json
{ "lead_ms": 60 }
```

60 ms = 2 frames a 30fps. Se aplica a todas las pistas por igual en `mix.sh`, así
que ajustar la sensación es cambiar un número, no re-tocar catorce timings.
